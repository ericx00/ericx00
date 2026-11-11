// Emberdeep: screens, input and animation. All rules live in logic.js.
import * as L from './logic.js';
import { HEROES, CARDS, cardOf, describe, needsTarget, RELICS, ENEMIES, ACTS, STEP_POOLS, EVENTS, KEYWORDS, BURN_PER_OVER } from './data.js';
import { W, H, img, atlas, loadAll, text, textWidth, wrap, para, spr, slice, sprite, strip } from './gfx.js';
import * as A from './audio.js';

const STORE_URL = 'https://whop.com/erick-muteti/';
const VERSION = '1.0';
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
ctx.imageSmoothingEnabled = false;

const SFX = ['card_draw', 'card_play', 'card_shuffle', 'card_hover', 'card_select', 'card_invalid', 'card_upgrade', 'card_exhaust', 'coin_drop', 'purchase',
  'steam_hiss', 'overheat', 'fire_whoosh', 'slash', 'heavy_slash', 'blunt_hit', 'arrow_shot', 'arrow_hit', 'shield_up', 'shield_hit', 'enemy_hurt', 'enemy_growl',
  'enemy_die', 'boss_roar', 'buff', 'debuff', 'strength_up', 'burn_tick', 'heal_soft', 'curse', 'turn_start', 'turn_end', 'enemy_turn', 'map_step', 'door_open',
  'chest_open', 'relic_get', 'rest_campfire', 'victory_fanfare', 'defeat_sting', 'boss_intro', 'level_complete', 'ui_tick', 'ui_press', 'ui_confirm', 'ui_back', 'anvil_hit'];
const MUSIC = ['title_anvil', 'map_embers', 'battle_sparks', 'boss_forge_heart', 'rest_hearth'];

// ---------- persistence (works without it too: itch embeds can block storage) ----------
const store = {
  get(k, d) { try { const v = localStorage.getItem('emberdeep.' + k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('emberdeep.' + k, JSON.stringify(v)); } catch { /* ignore */ } },
  del(k) { try { localStorage.removeItem('emberdeep.' + k); } catch { /* ignore */ } },
};
const meta = store.get('meta', { wins: {}, best: 0, runs: 0, seenHelp: false, sfx: true, music: true });
A.settings.sfx = meta.sfx; A.settings.music = meta.music;
const saveMeta = () => store.set('meta', meta);

const G = {
  screen: 'loading', run: null, cv: null, view: null, queue: [], qt: 0, t: 0, sel: -1, floaters: [], fx: [], shake: 0, flash: 0,
  overlay: null, picker: null, page: 0, hero: 'knight', diff: 0, heroAnim: { name: 'idle', t: 0 }, handHidden: false, dealT: 9, progress: 0, banner: null,
};
let regions = [], mouse = { x: -1, y: -1, down: false }, hot = null, lastHot = null, tip = null;

// ---------- input ----------
function toLogical(e) {
  const r = canvas.getBoundingClientRect();
  return { x: (e.clientX - r.left) * W / r.width, y: (e.clientY - r.top) * H / r.height };
}
canvas.addEventListener('pointermove', (e) => { Object.assign(mouse, toLogical(e)); });
canvas.addEventListener('pointerleave', () => { mouse.x = mouse.y = -1; });
canvas.addEventListener('pointerdown', (e) => {
  Object.assign(mouse, toLogical(e));
  A.unlock(SFX, MUSIC);
  const r = topRegion();
  if (r && r.onClick) r.onClick();
  e.preventDefault();
});
window.addEventListener('keydown', (e) => {
  A.unlock(SFX, MUSIC);
  if (G.overlay || G.picker) { if (e.key === 'Escape') { G.overlay = G.picker = null; A.play('ui_back'); } return; }
  if (G.screen !== 'combat' || busy()) return;
  const c = G.run.combat;
  if (e.key >= '1' && e.key <= '9') { const i = +e.key - 1; if (c.hand[i]) clickCard(i); }
  else if (e.key === 'e' || e.key === 'E') doEndTurn();
  else if (e.key === 'Enter' || e.key === ' ') { if (G.sel >= 0) tryPlay(G.sel, L.alive(c)[0]); e.preventDefault(); }
  else if (e.key === 'Escape') G.sel = -1;
});
const topRegion = () => { for (let i = regions.length - 1; i >= 0; i--) { const r = regions[i]; if (mouse.x >= r.x && mouse.x < r.x + r.w && mouse.y >= r.y && mouse.y < r.y + r.h) return r; } return null; };
function region(x, y, w, h, opts = {}) { regions.push({ x, y, w, h, ...opts }); }
const over = (id) => hot === id;

function button(id, x, y, w, h, label, onClick, { color = 'ember', disabled = false, tipText = null, font: fk = 'bold' } = {}) {
  const state = disabled ? 'disabled' : over(id) ? (mouse.down ? 'pressed' : 'hover') : 'normal';
  slice(ctx, `button_${color}_${state}`, x, y, w, h);
  text(ctx, label, x + w / 2, y + Math.floor((h - 12) / 2) + 1, { font: fk, align: 'center', color: disabled ? '#8a8f99' : '#ffffff', shadow: '#1a1423' });
  region(x, y, w, h, { id, tip: tipText, onClick: disabled ? () => A.play('card_invalid') : () => { A.play('ui_press'); onClick(); } });
}

// ---------- flow ----------
const busy = () => G.queue.length > 0;
function pump() { if (G.run) { G.queue.push(...G.run.ev); G.run.ev.length = 0; if (G.run.combat) G.cv = G.run.combat; } }
function save() { if (G.run && G.run.phase !== 'over' && G.run.phase !== 'win') store.set('run', L.serialize(G.run)); else store.del('run'); }
function syncView() {
  const s = G.run; if (!s) return;
  const c = G.cv;
  const old = G.view;
  G.view = { hp: s.hp, block: c ? c.block : 0, e: c ? c.enemies.map((en, i) => ({ hp: en.hp, block: en.block, anim: old?.e?.[i]?.anim ?? null, deathT: old?.e?.[i]?.deathT ?? (en.hp > 0 ? -1 : 9), hurt: 0, x: 0 })) : [] };
}
function startRun(hero, diff, daily = null) {
  const seed = daily ? L.hashSeed('daily:' + daily + ':' + hero) : (Math.random() * 2 ** 32) >>> 0;
  G.run = L.newRun({ hero, seed, diff, daily });
  G.cv = null; G.queue = []; G.sel = -1; meta.runs++; saveMeta();
  syncView(); setScreen('map'); save();
}
function setScreen(s) {
  G.screen = s; G.sel = -1; G.page = 0;
  const boss = G.run?.combat?.kind === 'boss';
  A.music(s === 'title' ? 'title_anvil' : s === 'combat' ? (boss ? 'boss_forge_heart' : 'battle_sparks') : s === 'rest' ? 'rest_hearth' : s === 'over' ? null : 'map_embers');
}
function act(fn) {           // run a logic call, then let its events play out
  const ok = fn();
  pump();
  if (!busy()) afterQueue();
  return ok;
}
function afterQueue() {
  syncView();
  const s = G.run; if (!s) return;
  G.handHidden = false;
  if (s.phase !== G.screen) {
    if (s.phase === 'win') { meta.wins[s.hero] = (meta.wins[s.hero] ?? 0) + 1; meta.best = Math.max(meta.best, s.diff + 1); saveMeta(); }
    if (s.phase === 'combat') { G.heroAnim = { name: 'idle', t: 0 }; if (!meta.seenHelp) { G.overlay = 'help'; meta.seenHelp = true; saveMeta(); } }
    setScreen(s.phase);
  }
  save();
}

const ACT_NAME = () => ACTS[Math.min(G.run.act, ACTS.length - 1)].name;
const enemyScale = (en) => ENEMIES[en.id].scale + 1;
function enemyPos(c, i) {
  const n = c.enemies.length, sc = enemyScale(c.enemies[i]), w = 32 * sc;
  const centres = n === 1 ? [470] : n === 2 ? [400, 530] : [350, 455, 560];
  return { x: centres[i] - w / 2, y: 200 - w, w, sc, cx: centres[i] };
}
const floater = (x, y, str, color = '#ffffff', big = false) => G.floaters.push({ x, y, str: String(str), color, t: 0, big });
const HERO_X = 62, HERO_CX = 110;

function applyEvent(ev) {
  const c = G.cv, v = G.view;
  switch (ev.t) {
    case 'combatStart': syncView(); G.dealT = 0; if (ev.kind === 'boss') { A.play('boss_intro'); A.play('boss_roar', { vol: 0.7 }); G.banner = { str: 'BOSS', t: 0 }; } else if (ev.kind === 'elite') { A.play('enemy_growl'); G.banner = { str: 'ELITE', t: 0 }; } else A.play('door_open', { vol: 0.6 }); break;
    case 'turn': syncView(); G.handHidden = false; G.dealT = 0; A.play('turn_start'); if (ev.n > 1) G.banner = { str: 'YOUR TURN', t: 0.5 }; break;
    case 'draw': A.play('card_draw', { vol: 0.5 }); break;
    case 'shuffle': A.play('card_shuffle'); break;
    case 'play': {
      const hero = G.run.hero;
      if (ev.type === 'attack') { G.heroAnim = { name: 'attack', t: 0 }; A.play(hero === 'mage' ? 'fire_whoosh' : hero === 'ranger' ? 'arrow_shot' : ev.heat >= 3 ? 'heavy_slash' : 'slash'); }
      else if (ev.type === 'power') A.play('buff'); else A.play('card_play');
      break;
    }
    case 'hitEnemy': {
      const e = v.e[ev.i]; if (!e) break;
      const p = enemyPos(c, ev.i);
      e.hp = Math.max(0, e.hp - ev.n); e.block = Math.max(0, e.block - ev.blocked);
      if (ev.n > 0) { floater(p.cx, p.y + p.w * 0.35, ev.n, ev.burn ? '#ffc56b' : '#ffffff', true); e.hurt = 0.25; G.fx.push({ key: ev.burn ? 'explosion_strip' : 'hit_spark_strip', x: p.cx, y: p.y + p.w * 0.6, t: 0, sc: ev.burn ? 2 : 3 }); A.play(ev.burn ? 'burn_tick' : G.run.hero === 'ranger' ? 'arrow_hit' : 'blunt_hit'); }
      else { floater(p.cx, p.y + p.w * 0.35, 'BLOCK', '#9cc2ff'); A.play('shield_hit'); }
      if (ev.dead) { e.deathT = 0; A.play('enemy_die'); }
      break;
    }
    case 'hitPlayer':
      v.hp = Math.max(0, v.hp - ev.n); v.block = Math.max(0, v.block - ev.blocked);
      if (ev.n > 0) { floater(HERO_CX, 120, '-' + ev.n, ev.src === 'overheat' ? '#f0642e' : '#ff9aa0', true); G.heroAnim = { name: 'hurt', t: 0 }; G.shake = 0.25; G.flash = ev.src === 'overheat' ? 0.3 : 0.12; A.play(ev.src === 'overheat' ? 'overheat' : 'enemy_hurt'); }
      else { floater(HERO_CX, 120, 'BLOCK', '#9cc2ff'); A.play('shield_hit'); }
      break;
    case 'block': v.block += ev.n; floater(HERO_CX, 130, '+' + ev.n, '#9cc2ff'); A.play('shield_up', { vol: 0.7 }); break;
    case 'cool': floater(60, 240, '-' + ev.n + ' HEAT', '#7fe3f0'); A.play('steam_hiss', { vol: 0.6 }); break;
    case 'heal': v.hp = Math.min(G.run.maxhp, v.hp + ev.n); floater(HERO_CX, 120, '+' + ev.n, '#a6eaae', true); A.play('heal_soft'); break;
    case 'gold': A.play('coin_drop'); break;
    case 'relic': A.play('relic_get'); break;
    case 'status': A.play('debuff', { vol: 0.6 }); break;
    case 'buff': floater(HERO_CX, 110, ev.k === 'str' ? 'STRENGTH' : 'POWER', '#ffc56b'); A.play('strength_up', { vol: 0.7 }); break;
    case 'hot': floater(HERO_CX, 96, 'HOT!', '#f0642e', true); break;
    case 'cold': floater(HERO_CX, 96, 'COLD!', '#7fe3f0', true); break;
    case 'valve': floater(HERO_CX, 110, 'SAFETY VALVE', '#7fe3f0'); A.play('steam_hiss'); break;
    case 'enemyPhase': G.handHidden = true; G.sel = -1; A.play('enemy_turn'); G.banner = { str: 'ENEMY TURN', t: 0.5 }; break;
    case 'enemyAct': {
      const e = v.e[ev.i]; if (!e) break;
      e.block = ev.m.b ?? 0;
      e.anim = { name: ev.m.a ? 'attack' : 'move', t: 0 };
      const p = enemyPos(c, ev.i);
      if (ev.m.b) floater(p.cx, p.y + 20, '+' + ev.m.b + ' BLOCK', '#9cc2ff');
      if (ev.m.s) floater(p.cx, p.y + 8, '+' + ev.m.s + ' STRENGTH', '#ffc56b');
      if (!ev.m.a) A.play(ev.m.b ? 'shield_up' : 'enemy_growl', { vol: 0.6 });
      break;
    }
    case 'debuff': floater(HERO_CX, 108, ev.k === 'weak' ? 'WEAK' : ev.k === 'vuln' ? 'VULNERABLE' : 'STOKED', ev.k === 'heat' ? '#f0642e' : '#d2a8f5'); A.play('curse', { vol: 0.5 }); break;
    case 'victory': A.play(ev.kind === 'boss' ? 'victory_fanfare' : 'level_complete'); G.heroAnim = { name: 'idle', t: 0 }; break;
    case 'death': G.heroAnim = { name: 'death', t: 0 }; A.play('defeat_sting'); break;
    case 'win': A.play('victory_fanfare'); break;
    case 'upgrade': A.play('card_upgrade'); break;
    case 'buy': A.play('purchase'); break;
  }
}
const DELAY = { play: 0.16, hitEnemy: 0.2, hitPlayer: 0.3, enemyAct: 0.42, enemyPhase: 0.55, draw: 0.05, turn: 0.15, block: 0.1, victory: 0.9, death: 1.6, combatStart: 0.5, heal: 0.15, hot: 0.1, cold: 0.1, cool: 0.1, status: 0.06, buff: 0.12, debuff: 0.15 };

// ---------- card rendering ----------
const cardCache = new Map();
const RAR = ['common', 'common', 'uncommon', 'rare'];
function drawArt(g, art, cx, cy, scale = 2) {
  if (art.startsWith('k:')) { const f = atlas.icons.frames[art.slice(2)]; g.drawImage(atlas.icons.img, f.x, f.y, f.w, f.h, cx - 8 * scale, cy - 8 * scale, 16 * scale, 16 * scale); }
  else g.drawImage(img['item_' + art], cx - 8 * scale, cy - 8 * scale, 16 * scale, 16 * scale);
}
function cardCanvas(entry) {
  const key = entry.id + (entry.up ? '+' : '');
  if (cardCache.has(key)) return cardCache.get(key);
  const card = cardOf(entry);
  const cv = document.createElement('canvas'); cv.width = 88; cv.height = 124;
  const g = cv.getContext('2d'); g.imageSmoothingEnabled = false;
  g.drawImage(img['bg_' + card.type], 6, 20);
  drawArt(g, card.art, 44, 39, 2);
  g.drawImage(img[`frame_${card.type}_${RAR[card.rar]}`], 0, 0);
  text(g, card.name, 44, 8, { align: 'center', color: entry.up ? '#a6eaae' : '#ffffff', shadow: '#1a1423' });
  const lines = wrap(describe(card), 70);
  const lh = lines.length > 5 ? 8 : 9;
  let y = 70 + Math.max(1, Math.floor((48 - lines.length * lh) / 2)) + 1;
  for (const ln of lines) { text(g, ln, 44, y, { align: 'center', color: '#e8e2f0' }); y += lh; }
  g.drawImage(img.gem, 1, 14);
  text(g, card.heat, 10, 19, { font: 'bold', align: 'center', color: '#ffffff', shadow: '#1a1423' });
  cardCache.set(key, cv);
  return cv;
}
function drawCard(entry, x, y, { glow = null, dim = false, scale = 1 } = {}) {
  x = Math.round(x); y = Math.round(y);
  if (glow) ctx.drawImage(img['glow_' + glow], x - 3, y - 3);
  ctx.drawImage(cardCanvas(entry), x, y, 88 * scale, 124 * scale);
  if (dim) { ctx.fillStyle = 'rgba(21,17,27,0.55)'; ctx.fillRect(x + 1, y + 1, 86, 122); }
}
function keywordTips(card) {
  const d = describe(card);
  const out = [];
  for (const k of ['HOT', 'COLD', 'Block', 'Vulnerable', 'Weak', 'Burn', 'Strength', 'Exhaust']) if (d.includes(k)) out.push(k);
  return out.slice(0, 3);
}

// ---------- backdrops ----------
const backdrops = {};
function backdrop(biome) {
  if (backdrops[biome]) return backdrops[biome];
  const cv = document.createElement('canvas'); cv.width = W; cv.height = 232;
  const g = cv.getContext('2d');
  let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const hill = (base, amp, col, step) => { g.fillStyle = col; for (let x = 0; x < W; x += step) { const h = base + Math.round(Math.sin(x / 61 + base) * amp + Math.sin(x / 23 + amp) * amp * 0.4); g.fillRect(x, h, step, 232 - h); } };
  if (biome === 'grassland') {
    ['#3b6fb5', '#4c86c9', '#66a0d8', '#8cbde6', '#b4d8f0'].forEach((col, i) => { g.fillStyle = col; g.fillRect(0, i * 34, W, 40); });
    g.fillStyle = '#f4f4f4'; for (let i = 0; i < 6; i++) { const x = rnd() * W, y = 20 + rnd() * 60; g.fillRect(x, y, 40 + rnd() * 30, 6); g.fillRect(x + 8, y - 5, 24, 5); }
    hill(120, 14, '#4d8a6a', 4); hill(150, 10, '#3f7a52', 4); hill(176, 5, '#2f6a40', 2);
    g.fillStyle = '#3f9a4c'; g.fillRect(0, 198, W, 34); g.fillStyle = '#6fcf6a'; g.fillRect(0, 198, W, 2); g.fillStyle = '#2e7a3a';
    for (let i = 0; i < 160; i++) g.fillRect(Math.floor(rnd() * W), 202 + Math.floor(rnd() * 28), 2, 1);
  } else if (biome === 'dungeon') {
    for (let y = 0; y < 198; y += 12) for (let x = -12; x < W; x += 24) { const ox = (y / 12) % 2 ? 12 : 0; g.fillStyle = rnd() < 0.18 ? '#2f273d' : '#2a2336'; g.fillRect(x + ox, y, 24, 12); g.fillStyle = '#1d1826'; g.fillRect(x + ox, y, 24, 1); g.fillRect(x + ox, y, 1, 12); }
    g.fillStyle = '#3a3348'; g.fillRect(0, 196, W, 3); g.fillStyle = '#241f2e'; g.fillRect(0, 199, W, 33); g.fillStyle = '#2c2638';
    for (let i = 0; i < 140; i++) g.fillRect(Math.floor(rnd() * W), 202 + Math.floor(rnd() * 28), 3, 1);
  } else {
    ['#141a33', '#1b2444', '#243156', '#30406b'].forEach((col, i) => { g.fillStyle = col; g.fillRect(0, i * 44, W, 50); });
    g.fillStyle = '#e6e9ef'; for (let i = 0; i < 70; i++) g.fillRect(Math.floor(rnd() * W), Math.floor(rnd() * 120), 1, 1);
    hill(96, 26, '#3d4a73', 6); hill(134, 16, '#55648f', 4);
    g.fillStyle = '#f0642e'; g.fillRect(300, 150, 40, 48); g.fillStyle = '#ffd27a'; g.fillRect(308, 160, 24, 38); g.fillStyle = '#2a2336'; g.fillRect(292, 140, 56, 12); g.fillRect(292, 140, 10, 58); g.fillRect(338, 140, 10, 58);
    g.fillStyle = '#dfe7f2'; g.fillRect(0, 198, W, 34); g.fillStyle = '#ffffff'; g.fillRect(0, 198, W, 2); g.fillStyle = '#b9c6da';
    for (let i = 0; i < 120; i++) g.fillRect(Math.floor(rnd() * W), 203 + Math.floor(rnd() * 27), 3, 1);
  }
  return (backdrops[biome] = cv);
}

// ---------- shared UI ----------
function topBar() {
  const s = G.run;
  slice(ctx, 'panel_flat', -2, -3, W + 4, 24);
  spr(ctx, 'icons', 'action_heal', 6, 3);
  text(ctx, `${Math.max(0, Math.round(G.view?.hp ?? s.hp))}/${s.maxhp}`, 26, 7, { color: '#ff9aa0' });
  spr(ctx, 'icons', 'resource_gold', 76, 3);
  text(ctx, s.gold, 96, 7, { color: '#ffe08a' });
  s.relics.forEach((id, i) => {
    const x = 132 + i * 19;
    ctx.drawImage(img['item_' + RELICS[id].art], x, 3);
    region(x, 2, 18, 18, { id: 'relic' + i, tip: `${RELICS[id].name}: ${RELICS[id].text}` });
  });
  const label = `${ACT_NAME()} ${s.act + 1}-${Math.min(s.step + 1, STEP_POOLS.length)}` + (s.diff ? `  Lv ${s.diff}` : '') + (s.daily ? '  DAILY' : '');
  text(ctx, label, W - 78, 7, { align: 'right', color: '#b9b0c9' });
  iconButton('deckbtn', W - 72, 2, 'resource_deck', () => { G.overlay = 'deck'; G.page = 0; }, `Deck (${s.deck.length} cards)`);
  iconButton('helpbtn', W - 54, 2, 'intent_unknown', () => { G.overlay = 'help'; }, 'How to play');
  iconButton('sndbtn', W - 36, 2, A.settings.sfx ? 'status_shock' : 'status_blind', () => { A.settings.sfx = meta.sfx = !A.settings.sfx; saveMeta(); }, 'Sound effects on/off');
  iconButton('musbtn', W - 18, 2, A.settings.music ? 'action_turn' : 'action_remove', () => { A.settings.music = meta.music = !A.settings.music; saveMeta(); A.refresh(); }, 'Music on/off');
}
function iconButton(id, x, y, icon, onClick, tipText) {
  if (over(id)) { ctx.fillStyle = 'rgba(255,224,138,0.18)'; ctx.fillRect(x - 1, y, 18, 18); }
  spr(ctx, 'icons', icon, x, y + 1);
  region(x - 1, y, 18, 18, { id, tip: tipText, onClick: () => { A.play('ui_tick'); onClick(); } });
}
function dimScreen(a = 0.72) { ctx.fillStyle = `rgba(13,10,18,${a})`; ctx.fillRect(0, 0, W, H); region(0, 0, W, H, { id: 'dim' }); }
function title(str, y, color = '#ffd27a') { text(ctx, str, W / 2, y, { font: 'display', align: 'center', color, shadow: '#1a1423' }); }
function drawTip() {
  if (!tip) return;
  const lines = wrap(tip, 190);
  const w = Math.max(...lines.map((l) => textWidth(l))) + 12, h = lines.length * 10 + 9;
  const x = Math.max(2, Math.min(W - w - 2, mouse.x + 10)), y = mouse.y + 14 + h > H ? mouse.y - h - 6 : mouse.y + 14;
  slice(ctx, 'tooltip', x, y, w, h);
  lines.forEach((l, i) => text(ctx, l, x + 6, y + 5 + i * 10));
}
function bar(x, y, w, frac, fill, label) {
  slice(ctx, 'bar_frame', x, y, w, 9);
  const f = atlas.ui.frames['bar_fill_' + fill];
  const fw = Math.max(0, Math.round((w - 4) * Math.min(1, frac)));
  if (fw > 0) ctx.drawImage(atlas.ui.img, f.x, f.y, 4, f.h, x + 2, y + 2, fw, 5);
  if (label != null) text(ctx, label, x + w / 2, y + 12, { font: 'tiny', align: 'center', shadow: '#1a1423' });
}

// ---------- screens ----------
function drawLoading() {
  ctx.fillStyle = '#15111b'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#3d3550'; ctx.fillRect(220, 176, 200, 8); ctx.fillStyle = '#f0642e'; ctx.fillRect(220, 176, 200 * G.progress, 8);
}

function drawTitle() {
  ctx.drawImage(backdrop('dungeon'), 0, 0); ctx.fillStyle = '#15111b'; ctx.fillRect(0, 232, W, H - 232);
  ctx.fillStyle = 'rgba(13,10,18,0.45)'; ctx.fillRect(0, 0, W, H);
  text(ctx, 'EMBERDEEP', W / 2 + 2, 22, { font: 'display', align: 'center', color: '#7a1f1a' });
  text(ctx, 'EMBERDEEP', W / 2, 20, { font: 'display', align: 'center', color: '#ffd27a', shadow: '#f0642e' });
  text(ctx, 'A deckbuilder where every card heats the forge', W / 2, 44, { align: 'center', color: '#e8e2f0', shadow: '#1a1423' });
  const names = Object.keys(HEROES);
  names.forEach((h, i) => {
    const x = 80 + i * 166, y = 64, sel = G.hero === h, id = 'hero' + h;
    slice(ctx, sel ? 'panel_iron' : 'panel_stone', x, y, 148, 150);
    if (sel) ctx.drawImage(img.glow_playable, 0, 0, 3, 3, x - 2, y - 2, 152, 2);
    sprite(ctx, HEROES[h].sprite, sel ? 'move' : 'idle', Math.floor(G.t * (sel ? 8 : 4)) % (sel ? 6 : 4), x + 26, y + 6, 3);
    text(ctx, HEROES[h].name, x + 74, y + 100, { font: 'bold', align: 'center', color: sel ? '#ffd27a' : '#f1ead8', shadow: '#1a1423' });
    para(ctx, HEROES[h].blurb, x + 8, y + 114, 132, { align: 'center', color: '#b9b0c9' });
    text(ctx, `HP ${HEROES[h].hp}   WINS ${meta.wins[h] ?? 0}`, x + 74, y + 138, { font: 'tiny', align: 'center', color: '#8a8f99' });
    region(x, y, 148, 150, { id, onClick: () => { G.hero = h; A.play('card_select'); } });
  });
  // difficulty
  const maxDiff = Math.min(5, meta.best);
  G.diff = Math.min(G.diff, maxDiff);
  text(ctx, 'Difficulty', 200, 228, { color: '#b9b0c9' });
  for (let d = 0; d <= 5; d++) {
    const x = 262 + d * 24, locked = d > maxDiff, id = 'diff' + d;
    slice(ctx, d === G.diff ? 'button_gold_normal' : locked ? 'button_steel_disabled' : over(id) ? 'button_steel_hover' : 'button_steel_normal', x, 222, 22, 18);
    text(ctx, d, x + 11, 226, { font: 'bold', align: 'center', color: locked ? '#5b6170' : '#ffffff', shadow: '#1a1423' });
    region(x, 222, 22, 18, { id, tip: locked ? 'Win a run on the level below to unlock.' : d === 0 ? 'Standard.' : `Enemies: +${d * 8}% HP, +${d * 6}% damage.`, onClick: () => { if (!locked) { G.diff = d; A.play('ui_tick'); } else A.play('card_invalid'); } });
  }
  const saved = store.get('run', null);
  const bw = 120;
  button('newrun', saved ? 136 : 196, 250, bw, 24, 'NEW RUN', () => startRun(G.hero, G.diff));
  const day = new Date().toISOString().slice(0, 10);
  button('daily', saved ? 260 : 324, 250, bw, 24, 'DAILY RUN', () => startRun(G.hero, G.diff, day), { color: 'steel', tipText: `Same seed for everyone today (${day}). Compare runs with friends.` });
  if (saved) button('cont', 384, 250, bw, 24, 'CONTINUE', () => { try { G.run = L.deserialize(saved); G.cv = G.run.combat; G.queue = []; syncView(); setScreen(G.run.phase); } catch { store.del('run'); } }, { color: 'green' });
  button('how', 250, 282, 140, 20, 'HOW TO PLAY', () => { G.overlay = 'help'; }, { color: 'steel', font: 'sans' });
  text(ctx, 'Art, UI, fonts, sounds and music: Forge Deckbuilder Kit + Pixel Sprites.', W / 2, 316, { align: 'center', color: '#8a8f99' });
  const lw = textWidth('Get the asset packs (free starter included)');
  text(ctx, 'Get the asset packs (free starter included)', W / 2, 328, { align: 'center', color: over('store') ? '#ffe08a' : '#7fe3f0' });
  region(W / 2 - lw / 2 - 4, 325, lw + 8, 12, { id: 'store', onClick: () => window.open(STORE_URL, '_blank', 'noopener') });
  text(ctx, 'v' + VERSION, W - 6, 348, { font: 'tiny', align: 'right', color: '#5b6170' });
}

const NODE = {
  fight: ['map_fight', 'Fight', (o) => o.enemies.map((id) => ENEMIES[id].name).join(', ')],
  elite: ['map_elite', 'Elite', (o) => `${o.enemies.map((id) => ENEMIES[id].name).join(', ')}. Tough, but drops a relic.`],
  boss: ['map_boss', 'Boss', (o) => `${ENEMIES[o.enemies[0]].name} guards the way.`],
  rest: ['map_rest', 'Campfire', () => 'Heal 30% of your HP, or upgrade a card.'],
  shop: ['map_shop', 'Merchant', () => 'Buy cards and relics, heal, or remove a card.'],
  event: ['map_event', 'Unknown', () => 'Something is waiting here.'],
};
function drawMap() {
  const s = G.run, actDef = ACTS[s.act];
  ctx.drawImage(backdrop(actDef.biome), 0, 0); ctx.fillStyle = '#15111b'; ctx.fillRect(0, 232, W, H - 232);
  ctx.fillStyle = 'rgba(13,10,18,0.6)'; ctx.fillRect(0, 0, W, H);
  topBar();
  title(`Act ${s.act + 1}: ${actDef.name}`, 34);
  const n = STEP_POOLS.length, x0 = W / 2 - (n - 1) * 20;
  for (let i = 0; i < n; i++) {
    const x = x0 + i * 40 - 14;
    if (i < n - 1) { ctx.fillStyle = i < s.step ? '#8791a0' : '#3d3550'; ctx.fillRect(x + 28, 79, 12, 2); }
    spr(ctx, 'ui', i < s.step ? 'node_done' : i === s.step ? 'node_current' : 'node_normal', x, 66);
    if (i === n - 1) spr(ctx, 'icons', 'map_boss', x + 6, 72); else if (i === s.step) spr(ctx, 'icons', 'map_start', x + 6, 72);
  }
  text(ctx, 'Choose your path', W / 2, 104, { align: 'center', color: '#b9b0c9' });
  const k = s.options.length, pw = 170, gap = 16, px0 = W / 2 - (k * pw + (k - 1) * gap) / 2;
  s.options.forEach((o, i) => {
    const [icon, name, desc] = NODE[o.type];
    const x = px0 + i * (pw + gap), y = 124, id = 'opt' + i, h = over(id);
    slice(ctx, h ? 'panel_iron' : 'panel_stone', x, y - (h ? 2 : 0), pw, 150);
    spr(ctx, 'ui', h ? 'node_hover' : 'node_normal', x + pw / 2 - 14, y + 12 - (h ? 2 : 0));
    spr(ctx, 'icons', icon, x + pw / 2 - 8, y + 18 - (h ? 2 : 0));
    text(ctx, name, x + pw / 2, y + 48, { font: 'bold', align: 'center', color: o.type === 'elite' || o.type === 'boss' ? '#ff9aa0' : '#ffd27a', shadow: '#1a1423' });
    para(ctx, desc(o), x + 10, y + 64, pw - 20, { align: 'center', color: '#e8e2f0' });
    if (o.enemies) o.enemies.forEach((id2, j) => sprite(ctx, id2, 'idle', Math.floor(G.t * 4 + j) % 4, x + pw / 2 - o.enemies.length * 20 + j * 40 - 12, y + 80, o.type === 'boss' ? 2 : 2, { flip: true }));
    region(x, y, pw, 150, { id, onClick: () => { A.play('map_step'); if (o.type === 'rest') A.play('rest_campfire', { vol: 0.6 }); if (o.type === 'event') A.play('chest_open', { vol: 0.6 }); act(() => L.chooseNode(s, i)); } });
  });
  text(ctx, `Deck ${s.deck.length} cards`, W / 2, 292, { align: 'center', color: '#8a8f99' });
}

function clickCard(i) {
  const c = G.run.combat;
  if (busy() || !c.hand[i]) return;
  const card = cardOf(c.hand[i]);
  if (G.sel === i) { if (!needsTarget(card) || L.alive(c).length === 1) tryPlay(i, L.alive(c)[0]); return; }
  G.sel = i; A.play('card_select', { vol: 0.6 });
}
function tryPlay(i, target) {
  const s = G.run, c = s.combat;
  if (busy() || !c.hand[i]) return;
  const cost = L.costOf(s, c.hand[i]);
  if (cost.burn >= s.hp) { A.play('card_invalid'); floater(HERO_CX, 100, 'OVERHEAT WOULD KILL YOU', '#ff9aa0'); return; }
  G.sel = -1;
  act(() => L.playCard(s, i, target ?? 0));
}
function doEndTurn() { if (!busy() && G.run.phase === 'combat') { A.play('turn_end'); G.sel = -1; act(() => L.endTurn(G.run)); } }

function intentText(m) {
  const parts = [];
  if (m.a) parts.push(`Attacks for ${m.dmg}${m.h > 1 ? ' x' + m.h : ''}`);
  if (m.b) parts.push(`gains ${m.b} Block`);
  if (m.s) parts.push(`gains ${m.s} Strength`);
  if (m.w) parts.push(`applies ${m.w} Weak`);
  if (m.v) parts.push(`applies ${m.v} Vulnerable`);
  if (m.heat) parts.push(`stokes you: +${m.heat} Heat`);
  const t = parts.join(', ');
  return t.charAt(0).toUpperCase() + t.slice(1) + '.';
}
const intentIcon = (m) => (m.a ? (m.h > 1 ? 'intent_multi_attack' : m.dmg >= 18 ? 'intent_heavy_attack' : 'intent_attack') : m.b ? 'intent_defend' : m.s ? 'intent_buff' : m.heat ? 'intent_stoke' : 'intent_debuff');

function drawCombat() {
  const s = G.run, c = G.cv, v = G.view;
  if (!c || !v) return;
  const live = s.phase === 'combat' && s.combat === c;
  ctx.save();
  if (G.shake > 0) ctx.translate(Math.round((Math.random() - 0.5) * 6 * G.shake / 0.25), Math.round((Math.random() - 0.5) * 4 * G.shake / 0.25));
  ctx.drawImage(backdrop(ACTS[Math.min(s.act, 2)].biome), 0, 0);
  ctx.fillStyle = '#15111b'; ctx.fillRect(0, 232, W, H - 232);
  // hero
  const ha = G.heroAnim, hs = HEROES[s.hero].sprite;
  const hf = ha.name === 'idle' ? Math.floor(G.t * 5) % 4 : ha.name === 'attack' ? Math.floor(ha.t * 14) : ha.name === 'hurt' ? Math.floor(ha.t * 8) : Math.min(4, Math.floor(ha.t * 6));
  sprite(ctx, hs, ha.name, hf, HERO_X + (ha.name === 'attack' ? Math.sin(Math.min(1, ha.t / 0.28) * Math.PI) * 26 : 0), 104, 3);
  bar(HERO_X + 8, 206, 88, v.hp / s.maxhp, 'hp', `${Math.max(0, Math.round(v.hp))}/${s.maxhp}`);
  if (v.block > 0) { spr(ctx, 'icons', 'status_block', HERO_X - 12, 201); text(ctx, v.block, HERO_X - 4, 206, { font: 'bold', align: 'center', color: '#ffffff', shadow: '#1a1423' }); }
  let sx = HERO_X + 8;
  const pst = [['status_strength', c.str, 'Strength: each attack hit deals that much more.'], ['status_weak', c.weak, KEYWORDS.Weak], ['status_vulnerable', c.vuln, KEYWORDS.Vulnerable],
    ['status_thorns', c.powers.thorns, 'Thorns: attackers take this much damage.'], ['status_barrier', c.powers.forge, 'Gain this much Block at the start of each turn.'],
    ['status_cold', c.powers.vent, 'Cool this much more each turn.'], ['status_burn', c.powers.kindle, 'Each turn, apply this much Burn to all enemies.']];
  for (const [icon, n, tp] of pst) if (n > 0) { spr(ctx, 'icons', icon, sx, 224); text(ctx, n, sx + 15, 233, { font: 'tiny', color: '#ffe08a', shadow: '#1a1423' }); region(sx, 224, 20, 16, { id: 'pst' + icon, tip: tp }); sx += 24; }
  // enemies
  let hoverEnemy = -1;
  c.enemies.forEach((en, i) => {
    const e = v.e[i]; if (!e) return;
    const p = enemyPos(c, i);
    const dead = en.hp <= 0 && e.hp <= 0;
    if (dead && e.deathT > 0.7) return;
    const an = e.deathT >= 0 && dead ? { name: 'death', f: Math.min(4, Math.floor(e.deathT * 8)) } : e.anim ? { name: e.anim.name, f: Math.floor(e.anim.t * 12) } : e.hurt > 0 ? { name: 'hurt', f: 0 } : { name: 'idle', f: Math.floor(G.t * 4 + i * 1.3) % 4 };
    const lunge = e.anim?.name === 'attack' ? -Math.sin(Math.min(1, e.anim.t / 0.3) * Math.PI) * 30 : 0;
    const id = 'enemy' + i;
    if (!dead && live && G.sel >= 0 && needsTarget(cardOf(c.hand[G.sel])) && over(id)) { ctx.fillStyle = 'rgba(255,224,138,0.16)'; ctx.fillRect(p.x, p.y, p.w, p.w); }
    sprite(ctx, en.id, an.name, an.f, p.x + lunge, p.y, p.sc, { flip: true, alpha: dead ? Math.max(0, 1 - e.deathT / 0.7) : 1 });
    if (dead) return;
    bar(p.cx - 32, 206, 64, e.hp / en.maxhp, 'enemy', `${Math.max(0, Math.round(e.hp))}/${en.maxhp}`);
    if (e.block > 0) { spr(ctx, 'icons', 'status_block', p.cx - 50, 201); text(ctx, e.block, p.cx - 42, 206, { font: 'bold', align: 'center', color: '#ffffff', shadow: '#1a1423' }); }
    let ex = p.cx - 30;
    for (const [icon, n] of [['status_vulnerable', en.vuln], ['status_weak', en.weak], ['status_burn', en.burn], ['status_strength', en.str]]) if (n > 0) { spr(ctx, 'icons', icon, ex, 224); text(ctx, n, ex + 15, 233, { font: 'tiny', color: '#ffe08a', shadow: '#1a1423' }); ex += 24; }
    if (live && !G.handHidden) {
      const m = L.intentOf(s, en);
      const by = Math.max(24, p.y + (p.sc >= 5 ? 8 : -4) - 22 + Math.round(Math.sin(G.t * 2 + i) * 1.5));
      spr(ctx, 'ui', 'intent_bubble', p.cx - 15, by);
      spr(ctx, 'icons', intentIcon(m), p.cx - (m.a ? 13 : 8), by + 2);
      if (m.a) text(ctx, m.h > 1 ? `${m.dmg}x${m.h}` : m.dmg, p.cx + 14, by + (m.h > 1 ? 13 : 6), { font: m.h > 1 ? 'tiny' : 'bold', align: 'right', color: '#a3283a' });
      region(p.x, Math.min(by, p.y), p.w, 232 - Math.min(by, p.y), { id, tip: `${en.name}. ${intentText(m)}`, onClick: () => { if (G.sel >= 0) tryPlay(G.sel, i); } });
      if (over(id)) hoverEnemy = i;
    }
  });
  // effects and floating numbers
  for (const f of G.fx) strip(ctx, f.key, f.t * 18, f.x, f.y, f.sc);
  ctx.restore();
  topBar();
  // heat gauge
  const hotAt = L.hotAt(s), coldAt = L.coldAt(s);
  const selCost = live && G.sel >= 0 && c.hand[G.sel] ? L.costOf(s, c.hand[G.sel]) : null;
  const hovCard = live && hot && hot.startsWith('card') ? +hot.slice(4) : -1;
  const preview = selCost ?? (hovCard >= 0 && c.hand[hovCard] ? L.costOf(s, c.hand[hovCard]) : null);
  text(ctx, 'HEAT', 12, 240, { font: 'bold', color: '#ffd27a', shadow: '#1a1423' });
  const state = c.heat >= hotAt ? ['HOT', '#f0642e'] : c.heat <= coldAt ? ['COLD', '#7fe3f0'] : ['WARM', '#f2b33d'];
  text(ctx, state[0], 52, 240, { font: 'bold', color: state[1], shadow: '#1a1423' });
  for (let i = 0; i < c.limit; i++) {
    const filled = i < c.heat, adding = preview && !filled && i < c.heat + preview.heat;
    const name = filled ? (i < coldAt ? 'gauge_cold' : i < hotAt ? 'gauge_warm' : 'gauge_hot') : adding && Math.floor(G.t * 6) % 2 ? 'gauge_over' : 'gauge_empty';
    spr(ctx, 'ui', name, 12 + i * 9, 252);
  }
  text(ctx, `${c.heat}/${c.limit}`, 14 + c.limit * 9, 255, { font: 'tiny', shadow: '#1a1423' });
  text(ctx, `Cools ${c.cool + c.powers.vent} each turn`, 12, 268, { font: 'tiny', color: '#8a8f99' });
  if (preview && preview.burn > 0) text(ctx, `OVERHEAT: -${preview.burn} HP`, 12, 278, { font: 'tiny', color: Math.floor(G.t * 6) % 2 ? '#ff9aa0' : '#f0642e', shadow: '#1a1423' });
  region(8, 236, 118, 46, { id: 'heat', tip: `${KEYWORDS.Heat} ${KEYWORDS.Overheat} HOT at ${hotAt}+, COLD at ${coldAt} or less.` });
  // piles
  spr(ctx, 'icons', 'resource_draw_pile', 12, 322, 2); text(ctx, c.draw.length, 48, 336, { font: 'bold', shadow: '#1a1423' });
  region(10, 320, 54, 36, { id: 'drawp', tip: `Draw pile: ${c.draw.length}. Exhausted: ${c.exhaust.length}.` });
  spr(ctx, 'icons', 'resource_discard_pile', 596, 322, 2); text(ctx, c.discard.length, 590, 336, { font: 'bold', align: 'right', shadow: '#1a1423' });
  region(566, 320, 66, 36, { id: 'discp', tip: `Discard pile: ${c.discard.length}.` });
  if (live) button('endturn', 546, 244, 84, 22, 'END TURN', doEndTurn, { disabled: busy(), tipText: 'End your turn (E). Unplayed cards are discarded.' });
  // hand
  if (live && !G.handHidden) {
    const n = c.hand.length, room = 400, step = n > 1 ? Math.min(92, (room - 88) / (n - 1)) : 0, x0 = 134 + (room - (88 + step * (n - 1))) / 2;
    const order = [...c.hand.keys()].sort((a, b) => (a === G.sel || a === hovCard ? 1 : 0) - (b === G.sel || b === hovCard ? 1 : 0));
    for (const i of order) {
      const cost = L.costOf(s, c.hand[i]);
      const lift = i === G.sel ? 26 : i === hovCard ? 14 : 0;
      const deal = Math.max(0, 1 - (G.dealT - i * 0.05) / 0.18);
      const x = x0 + i * step - deal * (x0 + i * step - 20), y = 236 - lift + deal * 80;
      const card = cardOf(c.hand[i]);
      const hasHot = describe(card).includes('HOT:') && cost.hot, hasCold = describe(card).includes('COLD:') && cost.cold;
      drawCard(c.hand[i], x, y, { glow: i === G.sel ? 'selected' : cost.burn > 0 ? 'danger' : hasHot ? 'hot' : hasCold ? 'cold' : i === hovCard ? 'playable' : null });
      if (i <= 8) text(ctx, i + 1, x + 82, y + 114, { font: 'tiny', align: 'right', color: '#5b6170' });
    }
    // regions in visual order so the raised card wins
    for (const i of order) {
      const lift = i === G.sel ? 26 : i === hovCard ? 14 : 0;
      const wv = i === n - 1 || i === G.sel || i === hovCard ? 88 : Math.max(20, step);
      region(x0 + i * step, 236 - lift, wv, 124 + lift, { id: 'card' + i, onClick: () => clickCard(i) });
    }
    const focus = G.sel >= 0 ? G.sel : hovCard;
    if (focus >= 0 && c.hand[focus]) {
      const card = cardOf(c.hand[focus]);
      const tips = keywordTips(card);
      if (tips.length) {
        const txt = tips.map((k) => `${k}: ${KEYWORDS[k]}`);
        const lines = txt.flatMap((t) => wrap(t, 196));
        const hh = lines.length * 10 + 9;
        slice(ctx, 'tooltip', 220, 222 - hh - 20, 208, hh);
        lines.forEach((l, k) => text(ctx, l, 226, 222 - hh - 15 + k * 10, { color: '#e8e2f0' }));
      }
      if (G.sel >= 0) text(ctx, needsTarget(card) && L.alive(c).length > 1 ? 'Click an enemy to play it' : 'Click the card again (or Enter) to play it', W / 2, 212, { align: 'center', color: '#ffe08a', shadow: '#1a1423' });
    }
    if (G.sel >= 0 && hoverEnemy >= 0 && needsTarget(cardOf(c.hand[G.sel]))) {
      const p = enemyPos(c, hoverEnemy);
      spr(ctx, 'ui', 'target_arrow', p.cx - 8, p.y - 4 + Math.round(Math.sin(G.t * 8) * 2));
    }
    region(126, 22, 414, 180, { id: 'field', onClick: () => { if (G.sel >= 0) { const card = cardOf(c.hand[G.sel]); if (!needsTarget(card) || L.alive(c).length === 1) tryPlay(G.sel, L.alive(c)[0]); } } });
    regions.unshift(regions.pop());        // battlefield catch-all sits under everything else
  }
  if (G.banner && G.banner.t < 1.2) {
    const a = Math.min(1, G.banner.t * 6, (1.2 - G.banner.t) * 4);
    ctx.globalAlpha = Math.max(0, a); slice(ctx, 'ribbon_neutral', W / 2 - 80, 110, 160, 20); text(ctx, G.banner.str, W / 2, 114, { font: 'bold', align: 'center', color: '#ffffff', shadow: '#1a1423' }); ctx.globalAlpha = 1;
  }
}

function drawReward() {
  drawCombat(); dimScreen();
  const s = G.run, r = s.reward;
  slice(ctx, 'ribbon_victory', W / 2 - 90, 28, 180, 20); text(ctx, 'VICTORY', W / 2, 32, { font: 'bold', align: 'center', color: '#ffffff', shadow: '#7a4a12' });
  spr(ctx, 'icons', 'resource_gold', W / 2 - 40, 56); text(ctx, `+${r.gold} gold`, W / 2 - 20, 60, { color: '#ffe08a' });
  if (r.relic) { ctx.drawImage(img['item_' + RELICS[r.relic].art], W / 2 - 150, 76); text(ctx, `Relic: ${RELICS[r.relic].name}. ${RELICS[r.relic].text}`, W / 2 - 130, 80, { color: '#7fe3f0' }); }
  text(ctx, 'Add a card to your deck', W / 2, 100, { align: 'center', color: '#b9b0c9' });
  r.cards.forEach((entry, i) => {
    const x = W / 2 - 150 + i * 106, id = 'rw' + i, h = over(id);
    drawCard(entry, x, 116 - (h ? 6 : 0), { glow: h ? 'selected' : null });
    region(x, 110, 88, 130, { id, onClick: () => { A.play('card_select'); act(() => L.pickReward(s, i)); } });
  });
  button('skip', W / 2 - 50, 256, 100, 22, 'SKIP', () => act(() => L.pickReward(s, -1)), { color: 'steel' });
  rewardTips(r.cards);
}
function rewardTips(entries) {
  const i = hot && hot.startsWith('rw') ? +hot.slice(2) : hot && hot.startsWith('shopc') ? +hot.slice(5) : -1;
  if (i < 0 || !entries[i]) return;
  const tips = keywordTips(cardOf(entries[i]));
  if (!tips.length) return;
  const lines = tips.map((k) => `${k}: ${KEYWORDS[k]}`).flatMap((t) => wrap(t, 300));
  slice(ctx, 'tooltip', W / 2 - 156, 286, 312, lines.length * 10 + 9);
  lines.forEach((l, k) => text(ctx, l, W / 2 - 150, 291 + k * 10, { color: '#e8e2f0' }));
}

function drawRest() {
  const s = G.run;
  ctx.drawImage(backdrop(ACTS[s.act].biome), 0, 0); ctx.fillStyle = '#15111b'; ctx.fillRect(0, 232, W, H - 232); ctx.fillStyle = 'rgba(13,10,18,0.55)'; ctx.fillRect(0, 0, W, H);
  topBar(); title('Campfire', 40);
  sprite(ctx, HEROES[s.hero].sprite, 'idle', Math.floor(G.t * 3) % 4, W / 2 - 110, 70, 3);
  spr(ctx, 'icons', 'map_rest', W / 2 + 10, 110, 4);
  const healN = Math.round(s.maxhp * 0.3) + (s.relics.includes('rations') ? 10 : 0);
  button('rheal', W / 2 - 170, 200, 160, 26, `REST (+${Math.min(healN, s.maxhp - s.hp)} HP)`, () => act(() => L.rest(s, 'heal')), { color: 'green' });
  const ups = s.deck.map((d, i) => i).filter((i) => !s.deck[i].up);
  button('rup', W / 2 + 10, 200, 160, 26, 'UPGRADE A CARD', () => { G.picker = { title: 'Choose a card to upgrade', filter: (d) => !d.up, preview: true, onPick: (i) => { G.picker = null; act(() => L.rest(s, 'upgrade', i)); } }; G.page = 0; }, { color: 'gold', disabled: !ups.length });
  text(ctx, 'Upgraded cards are stronger for the rest of the run.', W / 2, 240, { align: 'center', color: '#8a8f99' });
}

function drawShop() {
  const s = G.run, sh = s.shop;
  ctx.fillStyle = '#1c1826'; ctx.fillRect(0, 0, W, H);
  topBar(); title('Merchant', 30);
  sh.cards.forEach((it, i) => {
    const x = 60 + i * 100, id = 'shopc' + i, can = !it.sold && s.gold >= it.price;
    if (it.sold) { slice(ctx, 'panel_flat', x, 60, 88, 124); text(ctx, 'SOLD', x + 44, 116, { font: 'bold', align: 'center', color: '#5b6170' }); }
    else { drawCard(it.entry, x, 60 - (over(id) ? 4 : 0), { glow: over(id) && can ? 'selected' : null, dim: !can }); spr(ctx, 'icons', 'resource_gold', x + 20, 190); text(ctx, it.price, x + 40, 194, { color: can ? '#ffe08a' : '#a3283a' }); }
    region(x, 56, 88, 150, { id, onClick: () => { if (!act(() => L.shopBuy(s, 'card', i))) A.play('card_invalid'); } });
  });
  if (sh.relic) {
    const x = 380, can = !sh.relic.sold && s.gold >= sh.relic.price, r = RELICS[sh.relic.id];
    slice(ctx, over('shopr') && can ? 'panel_iron' : 'panel_stone', x, 60, 200, 60);
    if (sh.relic.sold) text(ctx, 'SOLD', x + 100, 84, { font: 'bold', align: 'center', color: '#5b6170' });
    else { ctx.drawImage(img['item_' + r.art], x + 8, 68, 32, 32); text(ctx, r.name, x + 48, 68, { font: 'bold', color: '#7fe3f0', shadow: '#1a1423' }); para(ctx, r.text, x + 48, 82, 146, { color: '#e8e2f0' }); spr(ctx, 'icons', 'resource_gold', x + 140, 100); text(ctx, sh.relic.price, x + 160, 104, { color: can ? '#ffe08a' : '#a3283a' }); }
    region(x, 60, 200, 60, { id: 'shopr', onClick: () => { if (!act(() => L.shopBuy(s, 'relic'))) A.play('card_invalid'); } });
  }
  button('shoprem', 380, 132, 200, 24, sh.removed ? 'CARD REMOVED' : `REMOVE A CARD (${sh.removePrice})`, () => { G.picker = { title: 'Choose a card to remove', filter: () => true, onPick: (i) => { G.picker = null; act(() => L.shopBuy(s, 'remove', i)); } }; G.page = 0; }, { color: 'steel', disabled: sh.removed || s.gold < sh.removePrice || s.deck.length <= 5, tipText: 'A smaller deck draws its best cards more often.' });
  button('shopheal', 380, 162, 200, 24, sh.healed ? 'HEALED' : `HEAL 15 HP (${sh.healPrice})`, () => act(() => L.shopBuy(s, 'heal')), { color: 'green', disabled: sh.healed || s.gold < sh.healPrice || s.hp >= s.maxhp });
  button('shopleave', W / 2 - 60, 232, 120, 24, 'LEAVE', () => act(() => L.shopLeave(s)));
  rewardTips(sh.cards.map((x) => x.entry));
}

function drawEvent() {
  const s = G.run, ev = EVENTS.find((x) => x.id === s.event);
  ctx.drawImage(backdrop(ACTS[s.act].biome), 0, 0); ctx.fillStyle = '#15111b'; ctx.fillRect(0, 232, W, H - 232); ctx.fillStyle = 'rgba(13,10,18,0.6)'; ctx.fillRect(0, 0, W, H);
  topBar();
  slice(ctx, 'panel_stone', W / 2 - 190, 60, 380, 200);
  title(ev.title, 76);
  para(ctx, ev.text, W / 2 - 170, 110, 340, { align: 'center', color: '#e8e2f0' });
  ev.options.forEach((o, i) => button('ev' + i, W / 2 - 160, 160 + i * 34, 320, 26, o.label, () => act(() => L.eventChoice(s, i)), { color: i ? 'steel' : 'ember', font: 'sans' }));
}

function drawEnd(win) {
  const s = G.run;
  if (G.cv && !win) drawCombat(); else { ctx.drawImage(backdrop('snow'), 0, 0); ctx.fillStyle = '#15111b'; ctx.fillRect(0, 232, W, H - 232); }
  dimScreen(0.78);
  slice(ctx, win ? 'ribbon_victory' : 'ribbon_defeat', W / 2 - 110, 50, 220, 20);
  text(ctx, win ? 'THE FORGE HEART IS QUIET' : 'YOU BURNED OUT', W / 2, 54, { font: 'bold', align: 'center', color: '#ffffff', shadow: '#1a1423' });
  sprite(ctx, HEROES[s.hero].sprite, win ? 'idle' : 'death', win ? Math.floor(G.t * 4) % 4 : 4, W / 2 - 48, 78, 3);
  const lines = [`${HEROES[s.hero].name}, difficulty ${s.diff}${s.daily ? `, daily ${s.daily}` : ''}`, win ? 'All three acts cleared.' : `Fell in ${ACTS[Math.min(s.act, 2)].name}, step ${s.step + 1}.`,
    `${s.stats.fights} fights, ${s.stats.turns} turns, ${s.stats.dealt} damage dealt, ${s.stats.overheats} overheats.`, `Deck: ${s.deck.length} cards. Relics: ${s.relics.length}.`];
  lines.forEach((l, i) => text(ctx, l, W / 2, 184 + i * 12, { align: 'center', color: i ? '#b9b0c9' : '#ffd27a' }));
  if (win && s.diff < 5) text(ctx, `Difficulty ${s.diff + 1} unlocked.`, W / 2, 236, { align: 'center', color: '#a6eaae' });
  button('again', W / 2 - 130, 256, 120, 24, 'PLAY AGAIN', () => startRun(s.hero, s.diff, s.daily ? null : null));
  button('menu', W / 2 + 10, 256, 120, 24, 'MAIN MENU', () => { G.run = null; G.cv = null; setScreen('title'); }, { color: 'steel' });
  const msg = 'Like the look? Every sprite, sound and font is in the Forge asset packs.';
  text(ctx, msg, W / 2, 300, { align: 'center', color: over('store2') ? '#ffe08a' : '#7fe3f0' });
  region(W / 2 - textWidth(msg) / 2, 296, textWidth(msg), 14, { id: 'store2', onClick: () => window.open(STORE_URL, '_blank', 'noopener') });
}

function drawDeckOverlay(pick) {
  dimScreen(0.86);
  const s = G.run;
  const idx = s.deck.map((d, i) => i).filter((i) => !pick || pick.filter(s.deck[i]));
  const per = 12, pages = Math.max(1, Math.ceil(idx.length / per));
  G.page = Math.min(G.page, pages - 1);
  title(pick ? pick.title : `Your deck (${s.deck.length})`, 10);
  idx.slice(G.page * per, G.page * per + per).forEach((di, k) => {
    const x = 46 + (k % 6) * 92, y = 44 + Math.floor(k / 6) * 132, id = 'dk' + di, h = over(id);
    const entry = pick?.preview && h ? { ...s.deck[di], up: true } : s.deck[di];
    drawCard(entry, x, y, { glow: h && pick ? 'selected' : null });
    region(x, y, 88, 124, { id, onClick: pick ? () => { A.play('card_select'); pick.onPick(di); } : null });
  });
  if (pick?.preview) text(ctx, 'Hover a card to see its upgraded version.', W / 2, 314, { align: 'center', color: '#a6eaae' });
  if (pages > 1) {
    button('pgp', 200, 328, 60, 20, 'PREV', () => { G.page = Math.max(0, G.page - 1); }, { color: 'steel', disabled: G.page === 0 });
    text(ctx, `${G.page + 1}/${pages}`, W / 2, 334, { align: 'center' });
    button('pgn', 380, 328, 60, 20, 'NEXT', () => { G.page = Math.min(pages - 1, G.page + 1); }, { color: 'steel', disabled: G.page >= pages - 1 });
  }
  button('dkclose', W - 86, 328, 76, 20, pick ? 'CANCEL' : 'CLOSE', () => { G.overlay = null; G.picker = null; }, { color: 'steel' });
}

const HELP = [
  ['Heat, not energy', `Every card adds its Heat (the number in the red gem). Play as many cards as you like. You cool ${4} Heat at the start of each turn, and Heat carries over between turns.`],
  ['Overheat', `Going over your Heat limit burns you for ${BURN_PER_OVER} HP per point. Sometimes that is worth it.`],
  ['HOT and COLD', 'Some cards get a bonus when your Heat is high (HOT) or low (COLD). The card glows orange or blue when the bonus is active.'],
  ['Enemies show their plan', 'The bubble above an enemy says what it does next. Block lasts until your next turn.'],
  ['Controls', 'Click a card to pick it, click an enemy to play it. Keys: 1-9 pick, Enter plays, E ends the turn. Touch works too.'],
];
function drawHelp() {
  dimScreen(0.88);
  slice(ctx, 'panel_stone', 70, 20, 500, 320);
  title('How to play', 32);
  let y = 62;
  for (const [h, body] of HELP) {
    text(ctx, h, 92, y, { font: 'bold', color: '#ffd27a', shadow: '#1a1423' });
    y += 13 + para(ctx, body, 92, y + 13, 456, { color: '#e8e2f0' }) + 8;
  }
  button('helpok', W / 2 - 50, 306, 100, 22, 'GOT IT', () => { G.overlay = null; });
}

// ---------- main loop ----------
function update(dt) {
  G.t += dt;
  if (G.queue.length) {
    G.qt -= dt;
    while (G.queue.length && G.qt <= 0) { const ev = G.queue.shift(); applyEvent(ev); G.qt += DELAY[ev.t] ?? 0; }
    if (!G.queue.length) { G.qt = 0; afterQueue(); }
  }
  G.dealT += dt; G.shake = Math.max(0, G.shake - dt); G.flash = Math.max(0, G.flash - dt);
  if (G.banner) G.banner.t += dt;
  const ha = G.heroAnim; ha.t += dt;
  if ((ha.name === 'attack' && ha.t > 0.3) || (ha.name === 'hurt' && ha.t > 0.25)) G.heroAnim = { name: 'idle', t: 0 };
  if (G.view) for (const e of G.view.e) { if (e.anim) { e.anim.t += dt; if (e.anim.t > 0.34) e.anim = null; } if (e.hurt > 0) e.hurt -= dt; if (e.deathT >= 0) e.deathT += dt; }
  for (const f of G.floaters) f.t += dt;
  G.floaters = G.floaters.filter((f) => f.t < 0.9);
  for (const f of G.fx) f.t += dt;
  G.fx = G.fx.filter((f) => f.t < 0.5);
}

function render() {
  regions = [];
  ctx.fillStyle = '#15111b'; ctx.fillRect(0, 0, W, H);
  const sc = G.screen;
  if (sc === 'loading') drawLoading();
  else if (sc === 'title') drawTitle();
  else if (sc === 'map') drawMap();
  else if (sc === 'combat') drawCombat();
  else if (sc === 'reward') drawReward();
  else if (sc === 'rest') drawRest();
  else if (sc === 'shop') drawShop();
  else if (sc === 'event') drawEvent();
  else if (sc === 'over') drawEnd(false);
  else if (sc === 'win') drawEnd(true);
  for (const f of G.floaters) {
    ctx.globalAlpha = Math.max(0, Math.min(1, (0.9 - f.t) * 3));
    text(ctx, f.str, f.x, f.y - f.t * 34, { font: f.big ? 'bold' : 'tiny', align: 'center', color: f.color, shadow: '#1a1423' });
    ctx.globalAlpha = 1;
  }
  if (G.flash > 0) { ctx.fillStyle = `rgba(240,100,46,${Math.min(0.35, G.flash)})`; ctx.fillRect(0, 0, W, H); }
  if (G.picker) drawDeckOverlay(G.picker); else if (G.overlay === 'deck') drawDeckOverlay(null); else if (G.overlay === 'help') drawHelp();
  const r = topRegion();
  hot = r?.id ?? null; tip = r?.tip ?? null;
  if (hot !== lastHot) { if (hot && hot.startsWith('card')) A.play('card_hover', { vol: 0.35 }); lastHot = hot; }
  canvas.style.cursor = r?.onClick ? 'pointer' : 'default';
  drawTip();
}

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  update(dt); render();
  requestAnimationFrame(frame);
}
canvas.addEventListener('pointerdown', () => { mouse.down = true; }, true);
window.addEventListener('pointerup', () => { mouse.down = false; });

function fit() {
  const s = Math.min(window.innerWidth / W, window.innerHeight / H);
  const k = s >= 1 ? Math.floor(s * 2) / 2 : s;      // whole or half steps keep pixels even
  canvas.style.width = Math.round(W * k) + 'px'; canvas.style.height = Math.round(H * k) + 'px';
}
window.addEventListener('resize', fit); fit();

const list = { images: { gem: 'assets/cards/gem.png', back: 'assets/cards/back.png' }, atlases: { icons: 'assets/atlas_icons', ui: 'assets/atlas_ui' },
  fonts: { sans: 'assets/fonts/forge-sans', bold: 'assets/fonts/forge-sans-bold', display: 'assets/fonts/forge-display', tiny: 'assets/fonts/ember-tiny' } };
for (const t of ['attack', 'skill', 'power']) { list.images['bg_' + t] = `assets/cards/bg_${t}.png`; for (const r of ['common', 'uncommon', 'rare']) list.images[`frame_${t}_${r}`] = `assets/cards/${t}_${r}.png`; }
for (const g of ['playable', 'selected', 'hot', 'cold', 'danger']) list.images['glow_' + g] = `assets/cards/glow_${g}.png`;
for (const h of Object.values(HEROES)) list.images[h.sprite] = `assets/chars/${h.sprite}.png`;
for (const id of Object.keys(ENEMIES)) list.images[id] = `assets/chars/${id}.png`;
const items = new Set([...Object.values(CARDS).map((c) => c.art), ...Object.values(RELICS).map((r) => r.art)].filter((a) => !a.startsWith('k:')));
for (const a of items) list.images['item_' + a] = `assets/items/${a}.png`;
for (const f of ['hit_spark_strip', 'explosion_strip']) list.images[f] = `assets/fx/${f}.png`;

requestAnimationFrame(frame);
loadAll(list, (p) => { G.progress = p; }).then(() => { setScreen('title'); window.__emberdeep = { G, L, act, startRun }; }).catch((e) => { document.body.insertAdjacentHTML('beforeend', `<p style="color:#ff9aa0;font-family:monospace">Could not load the game: ${e.message}</p>`); });
