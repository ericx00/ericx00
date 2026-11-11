// Emberdeep rules engine. Pure: no DOM, seeded RNG kept inside the state, so a run
// can be saved as JSON, replayed, and played by a bot in tests.
import {
  HEROES, CARDS, CARD_LIST, cardOf, needsTarget, RELIC_LIST, ENEMIES, ACTS, STEP_POOLS, EVENTS,
  HOT_AT, COLD_AT, BASE_LIMIT, BASE_COOL, BURN_PER_OVER,
} from './data.js';

// ---------- RNG ----------
export function rnd(s) {
  s.rs = (s.rs + 0x6d2b79f5) >>> 0;
  let t = s.rs;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}
const ri = (s, lo, hi) => lo + Math.floor(rnd(s) * (hi - lo + 1));
const pick = (s, arr) => arr[Math.floor(rnd(s) * arr.length)];
function shuffle(s, arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rnd(s) * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}
export function hashSeed(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

const has = (s, id) => s.relics.includes(id);
const emit = (s, e) => { s.ev.push(e); };

// ---------- Run ----------
export function newRun({ hero, seed = 1, diff = 0, daily = null }) {
  const h = HEROES[hero];
  const s = {
    v: 1, hero, seed: seed >>> 0, rs: seed >>> 0, diff, daily,
    hp: h.hp, maxhp: h.hp, gold: 0,
    deck: h.deck.map((id) => ({ id, up: false })),
    relics: [], act: 0, step: 0, phase: 'map', options: [],
    combat: null, reward: null, shop: null, event: null,
    stats: { fights: 0, turns: 0, dealt: 0, taken: 0, overheats: 0 },
    ev: [],
  };
  genOptions(s);
  return s;
}

function genOptions(s) {
  const act = ACTS[s.act];
  s.options = STEP_POOLS[s.step].map((type) => {
    if (type === 'easy' || type === 'fight') return { type: 'fight', enemies: pick(s, act[type === 'easy' ? 'easy' : 'normal']) };
    if (type === 'elite') return { type, enemies: pick(s, act.elite) };
    if (type === 'boss') return { type, enemies: act.boss };
    return { type };
  });
  s.phase = 'map';
}

export function chooseNode(s, i) {
  if (s.phase !== 'map') return false;
  const o = s.options[i];
  if (!o) return false;
  if (o.enemies) startCombat(s, o.enemies, o.type);
  else if (o.type === 'rest') s.phase = 'rest';
  else if (o.type === 'shop') openShop(s);
  else if (o.type === 'event') { s.event = pick(s, EVENTS).id; s.phase = 'event'; }
  return true;
}

function advance(s) {
  s.combat = s.reward = s.shop = s.event = null;
  s.step++;
  if (s.step >= STEP_POOLS.length) {
    s.act++; s.step = 0;
    if (s.act >= ACTS.length) { s.phase = 'win'; emit(s, { t: 'win' }); return; }
    heal(s, Math.round(s.maxhp * 0.4));
  }
  genOptions(s);
}

function heal(s, n) {
  const before = s.hp;
  s.hp = Math.min(s.maxhp, s.hp + n);
  if (s.hp > before) emit(s, { t: 'heal', n: s.hp - before });
}
function gainGold(s, n) {
  if (has(s, 'lucky_coin')) n = Math.round(n * 1.25);
  s.gold += n; emit(s, { t: 'gold', n });
  return n;
}
function upgradable(s) { return s.deck.map((d, i) => (!d.up && CARDS[d.id].up ? i : -1)).filter((i) => i >= 0); }
function upgradeRandom(s, n) {
  const out = [];
  for (let k = 0; k < n; k++) {
    const idx = upgradable(s);
    if (!idx.length) break;
    const i = pick(s, idx); s.deck[i].up = true; out.push(s.deck[i].id);
  }
  return out;
}
export function grantRelic(s, id) {
  if (!id) {
    const pool = RELIC_LIST.filter((r) => !has(s, r.id));
    if (!pool.length) { gainGold(s, 50); return null; }
    id = pick(s, pool).id;
  }
  s.relics.push(id);
  if (id === 'heartstone') { s.maxhp += 10; s.hp += 10; }
  if (id === 'anvil') upgradeRandom(s, 2);
  emit(s, { t: 'relic', id });
  return id;
}

// ---------- Combat ----------
// Per-act tuning (found with the bot in tests/sim.js), then +8% HP / +6% attack per difficulty level.
export const TUNE = { hp: [1.1, 1.3, 1.4], atk: [1.1, 1.25, 1.35] };
const scaleHp = (s, n) => Math.round(n * TUNE.hp[s.act] * (1 + 0.08 * s.diff));
const scaleAtk = (s, n) => Math.round(n * TUNE.atk[s.act] * (1 + 0.06 * s.diff));

function startCombat(s, ids, kind) {
  const enemies = ids.map((id) => {
    const d = ENEMIES[id];
    const hp = scaleHp(s, ri(s, d.hp[0], d.hp[1]));
    return { id, name: d.name, hp, maxhp: hp, block: 0, str: 0, weak: 0, vuln: 0, burn: 0, mi: 0 };
  });
  const c = {
    kind, enemies, draw: shuffle(s, s.deck.map((d) => ({ ...d }))), hand: [], discard: [], exhaust: [],
    heat: 0, limit: BASE_LIMIT + (has(s, 'heat_sink') ? 2 : 0), cool: BASE_COOL + (has(s, 'bellows') ? 1 : 0),
    block: 0, str: 0, weak: 0, vuln: 0, powers: { thorns: has(s, 'thorn_ring') ? 2 : 0, forge: 0, vent: 0, kindle: 0 },
    turn: 0, first: true, valve: has(s, 'safety_valve'), stoke: 0,
  };
  s.combat = c; s.phase = 'combat'; s.stats.fights++;
  emit(s, { t: 'combatStart', kind });
  if (has(s, 'whetstone')) c.str += 1;
  if (has(s, 'buckler')) c.block += 6;
  if (has(s, 'ember_charm')) for (const en of enemies) en.burn += 3;
  if (has(s, 'powder_keg')) for (let i = 0; i < enemies.length; i++) hitEnemy(s, i, 8);
  if (!checkVictory(s)) startTurn(s);
}

export const hotAt = (s) => (has(s, 'tempering_oil') ? HOT_AT - 1 : HOT_AT);
export const coldAt = (s) => (has(s, 'frost_flask') ? COLD_AT + 1 : COLD_AT);
export const alive = (c) => c.enemies.map((e, i) => (e.hp > 0 ? i : -1)).filter((i) => i >= 0);

function drawCards(s, n) {
  const c = s.combat;
  for (let k = 0; k < n; k++) {
    if (c.hand.length >= 10) break;
    if (!c.draw.length) {
      if (!c.discard.length) break;
      c.draw = shuffle(s, c.discard); c.discard = [];
      emit(s, { t: 'shuffle' });
    }
    c.hand.push(c.draw.pop());
    emit(s, { t: 'draw' });
  }
}

function startTurn(s) {
  const c = s.combat;
  c.turn++; s.stats.turns++;
  if (c.turn > 1) c.block = 0;
  if (c.turn > 1) c.heat = Math.max(0, c.heat - c.cool - c.powers.vent);
  if (c.stoke) { c.heat = Math.min(c.limit, c.heat + c.stoke); c.stoke = 0; }
  if (c.powers.forge) c.block += c.powers.forge;
  if (c.powers.kindle) for (const i of alive(c)) c.enemies[i].burn += c.powers.kindle;
  c.first = true;
  drawCards(s, 5 + (c.turn === 1 && has(s, 'scroll_case') ? 2 : 0));
  emit(s, { t: 'turn', n: c.turn });
}

/** Damage one attack hit from the player would do to enemy `en`. */
export function playerHit(s, en, base) {
  const c = s.combat;
  let d = base + c.str;
  if (c.weak > 0) d *= 0.75;
  if (en.vuln > 0) d *= 1.5;
  return Math.max(0, Math.floor(d));
}
/** Damage one hit of an enemy attack would do to the player (before Block). */
export function enemyHit(s, en, base) {
  const c = s.combat;
  let d = scaleAtk(s, base) + en.str;
  if (en.weak > 0) d *= 0.75;
  if (c.vuln > 0) d *= 1.5;
  return Math.max(0, Math.floor(d));
}
/** What an enemy will do next, with attack damage already worked out. */
export function intentOf(s, en) {
  const m = ENEMIES[en.id].moves[en.mi % ENEMIES[en.id].moves.length];
  return { ...m, h: m.h ?? 1, dmg: m.a ? enemyHit(s, en, m.a) : 0 };
}

function hitEnemy(s, i, dmg) {
  const en = s.combat.enemies[i];
  if (!en || en.hp <= 0) return;
  let d = dmg;
  let blocked = 0;
  { blocked = Math.min(en.block, d); en.block -= blocked; d -= blocked; }
  en.hp = Math.max(0, en.hp - d);
  s.stats.dealt += d;
  emit(s, { t: 'hitEnemy', i, n: d, blocked, dead: en.hp <= 0 });
}
function hurtPlayer(s, dmg, { pierce = false, src = 'enemy' } = {}) {
  const c = s.combat;
  let d = dmg, blocked = 0;
  if (!pierce && c) { blocked = Math.min(c.block, d); c.block -= blocked; d -= blocked; }
  s.hp = Math.max(0, s.hp - d);
  s.stats.taken += d;
  emit(s, { t: 'hitPlayer', n: d, blocked, src });
}

function runFx(s, fx, ctx) {
  const c = s.combat;
  for (const f of fx) {
    const [op, a, b] = f;
    const tgt = () => (c.enemies[ctx.target]?.hp > 0 ? ctx.target : alive(c)[0]);
    const each = (fn) => { for (const i of alive(c)) fn(c.enemies[i], i); };
    switch (op) {
      case 'dmg': for (let k = 0; k < (b ?? 1); k++) { const i = tgt(); if (i != null) hitEnemy(s, i, playerHit(s, c.enemies[i], a)); } break;
      case 'aoe': for (let k = 0; k < (b ?? 1); k++) each((en, i) => hitEnemy(s, i, playerHit(s, en, a))); break;
      case 'dmgHeat': { const i = tgt(); if (i != null) hitEnemy(s, i, playerHit(s, c.enemies[i], a * ctx.heat)); break; }
      case 'dmgBlock': { const i = tgt(); if (i != null) hitEnemy(s, i, playerHit(s, c.enemies[i], c.block)); break; }
      case 'dmgBurn': { const i = tgt(); if (i != null) hitEnemy(s, i, playerHit(s, c.enemies[i], a * c.enemies[i].burn)); break; }
      case 'block': c.block += a; emit(s, { t: 'block', n: a }); break;
      case 'draw': drawCards(s, a); break;
      case 'cool': c.heat = Math.max(0, c.heat - a); emit(s, { t: 'cool', n: a }); break;
      case 'vuln': { const i = tgt(); if (i != null) { c.enemies[i].vuln += a; emit(s, { t: 'status', i, k: 'vuln' }); } break; }
      case 'weak': { const i = tgt(); if (i != null) { c.enemies[i].weak += a; emit(s, { t: 'status', i, k: 'weak' }); } break; }
      case 'burn': { const i = tgt(); if (i != null) { c.enemies[i].burn += a; emit(s, { t: 'status', i, k: 'burn' }); } break; }
      case 'aoeburn': each((en, i) => { en.burn += a; emit(s, { t: 'status', i, k: 'burn' }); }); break;
      case 'aoevuln': each((en, i) => { en.vuln += a; emit(s, { t: 'status', i, k: 'vuln' }); }); break;
      case 'aoeweak': each((en, i) => { en.weak += a; emit(s, { t: 'status', i, k: 'weak' }); }); break;
      case 'str': c.str += a; emit(s, { t: 'buff', k: 'str' }); break;
      case 'heal': heal(s, a); break;
      case 'power': c.powers[a] += b; emit(s, { t: 'buff', k: a }); break;
      case 'hot': if (ctx.hot) { emit(s, { t: 'hot' }); runFx(s, a, ctx); } break;
      case 'cold': if (ctx.cold) { emit(s, { t: 'cold' }); runFx(s, a, ctx); } break;
      case 'ifVuln': { const i = tgt(); if (i != null && c.enemies[i].vuln > 0) runFx(s, a, ctx); break; }
      case 'exhaust': break;
    }
  }
}

/** Heat a card would add right now, and the HP an Overheat would cost. */
export function costOf(s, entry) {
  const c = s.combat;
  const card = cardOf(entry);
  const heat = c.first && has(s, 'cold_iron') ? 0 : card.heat;
  const over = Math.max(0, c.heat + heat - c.limit);
  const burn = over > 0 && !c.valve ? over * BURN_PER_OVER : 0;
  return { heat, over, burn, hot: c.heat >= hotAt(s), cold: c.heat <= coldAt(s) };
}

export function playCard(s, hi, target = 0) {
  const c = s.combat;
  if (s.phase !== 'combat' || !c.hand[hi]) return false;
  const entry = c.hand[hi];
  const card = cardOf(entry);
  const cost = costOf(s, entry);
  const ctx = { hot: cost.hot, cold: cost.cold, heat: c.heat, target };
  c.hand.splice(hi, 1);
  c.first = false;
  c.heat += cost.heat;
  emit(s, { t: 'play', id: entry.id, type: card.type, heat: cost.heat });
  if (cost.over > 0) {
    c.heat = c.limit; s.stats.overheats++;
    if (c.valve) { c.valve = false; emit(s, { t: 'valve' }); }
    else hurtPlayer(s, cost.burn, { pierce: true, src: 'overheat' });
    if (s.hp <= 0) return die(s);
  }
  if (has(s, 'silver_ring')) c.block += 1;
  runFx(s, card.fx, ctx);
  if (card.type === 'power') { /* stays in play for the fight */ }
  else if (card.fx.some((f) => f[0] === 'exhaust')) c.exhaust.push(entry);
  else c.discard.push(entry);
  checkVictory(s);
  return true;
}

function die(s) { s.phase = 'over'; emit(s, { t: 'death' }); return true; }

function checkVictory(s) {
  const c = s.combat;
  if (alive(c).length) return false;
  const kind = c.kind;
  emit(s, { t: 'victory', kind });
  if (has(s, 'moss')) heal(s, 5);
  const gold = gainGold(s, kind === 'boss' ? ri(s, 65, 80) : kind === 'elite' ? ri(s, 30, 40) : ri(s, 12, 20));
  const relic = kind !== 'fight' ? grantRelic(s) : null;
  if (kind === 'boss' && s.act === ACTS.length - 1) { s.combat = null; advanceToWin(s); return true; }
  s.reward = { gold, relic, cards: rollCards(s, 3, kind) };
  s.phase = 'reward';
  return true;
}
function advanceToWin(s) { s.step = STEP_POOLS.length - 1; advance(s); }

export function endTurn(s) {
  const c = s.combat;
  if (s.phase !== 'combat') return false;
  c.discard.push(...c.hand); c.hand = [];
  if (c.weak > 0) c.weak--;
  if (c.vuln > 0) c.vuln--;
  emit(s, { t: 'enemyPhase' });
  for (const i of alive(c)) {
    const en = c.enemies[i];
    en.block = 0;
    const m = intentOf(s, en);
    emit(s, { t: 'enemyAct', i, m });
    if (m.b) en.block += m.b;
    if (m.s) en.str += m.s;
    if (m.a) {
      for (let k = 0; k < m.h; k++) {
        hurtPlayer(s, enemyHit(s, en, m.a));
        if (c.powers.thorns && en.hp > 0) hitEnemy(s, i, c.powers.thorns);
        if (s.hp <= 0) return die(s);
      }
    }
    if (m.w) { c.weak += m.w; emit(s, { t: 'debuff', k: 'weak' }); }
    if (m.v) { c.vuln += m.v; emit(s, { t: 'debuff', k: 'vuln' }); }
    if (m.heat) { c.stoke += m.heat; emit(s, { t: 'debuff', k: 'heat' }); }
    en.mi++;
    if (en.hp > 0 && en.burn > 0) { en.hp = Math.max(0, en.hp - en.burn); s.stats.dealt += en.burn; emit(s, { t: 'hitEnemy', i, n: en.burn, blocked: 0, burn: true, dead: en.hp <= 0 }); en.burn--; }
    if (en.weak > 0) en.weak--;
    if (en.vuln > 0) en.vuln--;
  }
  if (!checkVictory(s)) startTurn(s);
  return true;
}

// ---------- Rewards ----------
function rollCards(s, n, kind = 'fight') {
  const w = kind === 'boss' ? [0, 50, 50] : kind === 'elite' ? [45, 40, 15] : [60, 32, 8];
  const out = [];
  let guard = 0;
  while (out.length < n && guard++ < 200) {
    const r = rnd(s) * 100;
    const rar = r < w[0] ? 1 : r < w[0] + w[1] ? 2 : 3;
    const pool = CARD_LIST.filter((cd) => cd.rar === rar && (cd.hero === s.hero || (cd.hero === 'any' && rnd(s) < 0.3)) && !out.some((o) => o.id === cd.id));
    if (!pool.length) continue;
    out.push({ id: pick(s, pool).id, up: rnd(s) < 0.1 * s.act });
  }
  return out;
}

export function pickReward(s, i) {
  if (s.phase !== 'reward') return false;
  if (i >= 0 && s.reward.cards[i]) s.deck.push({ ...s.reward.cards[i] });
  advance(s);
  return true;
}

export function rest(s, action, deckIdx) {
  if (s.phase !== 'rest') return false;
  if (action === 'heal') heal(s, Math.round(s.maxhp * 0.3) + (has(s, 'rations') ? 10 : 0));
  else if (action === 'upgrade') {
    const d = s.deck[deckIdx];
    if (!d || d.up || !CARDS[d.id].up) return false;
    d.up = true; emit(s, { t: 'upgrade', id: d.id });
  } else return false;
  advance(s);
  return true;
}

const PRICE = { 1: 45, 2: 70, 3: 110 };
function openShop(s) {
  const cards = rollCards(s, 3, 'elite').map((entry) => ({ entry, price: PRICE[CARDS[entry.id].rar] + ri(s, -5, 5), sold: false }));
  const pool = RELIC_LIST.filter((r) => !has(s, r.id));
  s.shop = { cards, relic: pool.length ? { id: pick(s, pool).id, price: 130 + ri(s, -10, 10), sold: false } : null, removePrice: 60, removed: false, healPrice: 35, healed: false };
  s.phase = 'shop';
}
export function shopBuy(s, what, i) {
  const sh = s.shop;
  if (s.phase !== 'shop') return false;
  if (what === 'card') {
    const it = sh.cards[i];
    if (!it || it.sold || s.gold < it.price) return false;
    s.gold -= it.price; it.sold = true; s.deck.push({ ...it.entry });
  } else if (what === 'relic') {
    if (!sh.relic || sh.relic.sold || s.gold < sh.relic.price) return false;
    s.gold -= sh.relic.price; sh.relic.sold = true; grantRelic(s, sh.relic.id);
  } else if (what === 'remove') {
    if (sh.removed || s.gold < sh.removePrice || !s.deck[i] || s.deck.length <= 5) return false;
    s.gold -= sh.removePrice; sh.removed = true; s.deck.splice(i, 1);
  } else if (what === 'heal') {
    if (sh.healed || s.gold < sh.healPrice || s.hp >= s.maxhp) return false;
    s.gold -= sh.healPrice; sh.healed = true; heal(s, 15);
  } else return false;
  emit(s, { t: 'buy' });
  return true;
}
export function shopLeave(s) { if (s.phase !== 'shop') return false; advance(s); return true; }

export function eventChoice(s, i) {
  if (s.phase !== 'event') return false;
  const ev = EVENTS.find((x) => x.id === s.event);
  const [op, a] = ev.options[i].fx;
  if (op === 'upgrade') upgradeRandom(s, a);
  else if (op === 'gold') gainGold(s, a);
  else if (op === 'heal') heal(s, a);
  else if (op === 'maxhp') { s.maxhp += a; s.hp += a; }
  else if (op === 'relicHurt') { s.hp = Math.max(1, s.hp - a); grantRelic(s); }
  else if (op === 'remove') {
    const i2 = s.deck.findIndex((d) => CARDS[d.id].rar === 0 && !d.up);
    if (i2 >= 0 && s.deck.length > 5) s.deck.splice(i2, 1);
  }
  advance(s);
  return true;
}

export const serialize = (s) => JSON.stringify({ ...s, ev: [] });
export const deserialize = (str) => { const s = JSON.parse(str); s.ev = []; return s; };
export { needsTarget };
