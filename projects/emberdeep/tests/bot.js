// A simple greedy bot (one-card lookahead). Used to test that runs are completable
// and to compare hero balance. A human player does much better than this.
import * as L from '../src/logic.js';
import { CARDS } from '../src/data.js';

const clone = (s) => structuredClone(s);
const incoming = (s) => L.alive(s.combat).reduce((t, i) => { const m = L.intentOf(s, s.combat.enemies[i]); return t + m.dmg * m.h; }, 0);
const foeTotal = (c) => c.enemies.reduce((t, e) => t + e.hp + e.block, 0);
const powerSum = (c) => c.powers.thorns * 2 + c.powers.forge * 3 + c.powers.vent * 4 + c.powers.kindle * 5;

function bestPlay(s) {
  const c = s.combat;
  const inc = Math.max(0, incoming(s) - c.block);
  let best = null;
  const targets = L.alive(c);
  for (let hi = 0; hi < c.hand.length; hi++) {
    const cost = L.costOf(s, c.hand[hi]);
    for (const ti of targets) {
      const t = clone(s);
      L.playCard(t, hi, ti);
      if (t.phase === 'over') continue;
      let score;
      if (t.phase !== 'combat') score = 1000;
      else {
        const tc = t.combat;
        const kills = L.alive(c).length - L.alive(tc).length;
        const debuff = tc.enemies.reduce((x, e, i) => x + (e.vuln - c.enemies[i].vuln) * 3 + (e.weak - c.enemies[i].weak) * 3 + (e.burn - c.enemies[i].burn) * 2.5, 0);
        score = (foeTotal(c) - foeTotal(tc)) + kills * 8 + Math.min(tc.block - c.block, inc) * 1.3
          + (tc.hand.length - (c.hand.length - 1)) * 2.5 + (tc.str - c.str) * (6 + 2 * targets.length) + (powerSum(tc) - powerSum(c)) * (c.turn <= 3 ? 1.5 : 0.5)
          + debuff + (t.hp - s.hp) * (t.hp < s.hp ? 3 : 1) + Math.max(0, c.heat + cost.heat - tc.heat - cost.heat) * 0.8;
        if (cost.over > 0) score -= 4;
      }
      if (score > 0.5 && (!best || score > best.score)) best = { hi, ti, score };
      if (!L.needsTarget(CARDS[c.hand[hi].id])) break;
    }
  }
  return best;
}

export function playRun({ hero, seed, diff = 0, maxSteps = 20000 }) {
  const s = L.newRun({ hero, seed, diff });
  let steps = 0;
  while (s.phase !== 'over' && s.phase !== 'win' && steps++ < maxSteps) {
    s.ev.length = 0;
    if (s.phase === 'map') {
      const o = s.options; const hpf = s.hp / s.maxhp;
      const want = hpf < 0.45 ? ['rest', 'shop', 'event', 'fight', 'elite', 'boss'] : hpf > 0.7 ? ['elite', 'event', 'rest', 'fight', 'shop', 'boss'] : ['event', 'rest', 'fight', 'shop', 'elite', 'boss'];
      let i = -1;
      for (const w of want) { i = o.findIndex((x) => x.type === w); if (i >= 0) break; }
      L.chooseNode(s, i);
    } else if (s.phase === 'combat') {
      const p = bestPlay(s);
      if (p) L.playCard(s, p.hi, p.ti); else L.endTurn(s);
    } else if (s.phase === 'reward') {
      const cs = s.reward.cards.map((e, i) => ({ i, r: CARDS[e.id].rar + (e.up ? 0.5 : 0) })).sort((a, b) => b.r - a.r);
      L.pickReward(s, s.deck.length >= 24 ? -1 : cs[0].i);
    } else if (s.phase === 'rest') {
      const up = s.deck.map((d, i) => ({ i, d })).filter((x) => !x.d.up && CARDS[x.d.id].up).sort((a, b) => CARDS[b.d.id].rar - CARDS[a.d.id].rar);
      if (s.hp / s.maxhp < 0.65 || !up.length) L.rest(s, 'heal'); else L.rest(s, 'upgrade', up[0].i);
    } else if (s.phase === 'shop') {
      if (s.shop.relic && !s.shop.relic.sold && s.gold >= s.shop.relic.price) L.shopBuy(s, 'relic');
      else if (!s.shop.healed && s.hp / s.maxhp < 0.6 && s.gold >= s.shop.healPrice) L.shopBuy(s, 'heal');
      else { const k = s.shop.cards.findIndex((x) => !x.sold && s.gold >= x.price && CARDS[x.entry.id].rar >= 2); if (k >= 0) L.shopBuy(s, 'card', k); else L.shopLeave(s); }
    } else if (s.phase === 'event') {
      L.eventChoice(s, s.event === 'chest' && s.hp < 25 ? 1 : 0);
    }
  }
  return s;
}
