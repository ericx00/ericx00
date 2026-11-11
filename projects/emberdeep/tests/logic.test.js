import test from 'node:test';
import assert from 'node:assert/strict';
import * as L from '../src/logic.js';
import { HEROES, CARDS, CARD_LIST, cardOf, describe, RELIC_LIST, ENEMIES, ACTS, EVENTS, BURN_PER_OVER } from '../src/data.js';
import { playRun } from './bot.js';

const fight = (hero = 'knight', hand = null) => {
  const s = L.newRun({ hero, seed: 7 });
  L.chooseNode(s, 0);
  if (hand) s.combat.hand = hand.map((id) => (typeof id === 'string' ? { id, up: false } : id));
  return s;
};

test('content is consistent', () => {
  assert.equal(new Set(CARD_LIST.map((c) => c.id)).size, CARD_LIST.length);
  for (const h of Object.values(HEROES)) for (const id of h.deck) assert.ok(CARDS[id], id);
  for (const c of CARD_LIST) {
    assert.ok(describe(c).length > 3, c.id);
    assert.ok(c.up, `${c.id} has an upgrade`);
    assert.ok(describe(cardOf({ id: c.id, up: true })) !== describe(c) || cardOf({ id: c.id, up: true }).heat < c.heat, `${c.id} upgrade changes something`);
  }
  for (const a of ACTS) for (const g of [...a.easy, ...a.normal, ...a.elite, a.boss]) for (const id of g) assert.ok(ENEMIES[id], id);
  const used = new Set(ACTS.flatMap((a) => [...a.easy, ...a.normal, ...a.elite, a.boss].flat()));
  assert.equal(used.size, 24, 'all 24 monsters appear');
  for (const hero of Object.keys(HEROES)) assert.ok(CARD_LIST.filter((c) => c.hero === hero).length >= 20);
  assert.ok(RELIC_LIST.length >= 18 && EVENTS.length >= 4);
});

test('same seed gives the same run', () => {
  const a = playRun({ hero: 'mage', seed: 42 }), b = playRun({ hero: 'mage', seed: 42 });
  assert.deepEqual({ ...a, ev: [] }, { ...b, ev: [] });
  const c = playRun({ hero: 'mage', seed: 43 });
  assert.notDeepEqual(a.stats, c.stats);
});

test('heat, overheat, cooling', () => {
  const s = fight('knight', ['heavy_blow', 'heavy_blow', 'heavy_blow', 'strike']);
  const c = s.combat; c.enemies.forEach((e) => { e.hp = e.maxhp = 500; });
  L.playCard(s, 0, 0); L.playCard(s, 0, 0);
  assert.equal(c.heat, 6);
  const hp = s.hp;
  assert.deepEqual(L.costOf(s, c.hand[0]).over, 1);
  L.playCard(s, 0, 0);
  assert.equal(c.heat, c.limit);
  assert.equal(s.hp, hp - 1 * BURN_PER_OVER);
  L.endTurn(s);
  if (s.phase === 'combat') assert.equal(c.heat, c.limit - c.cool);
});

test('HOT and COLD bonuses use heat before the card is played', () => {
  let s = fight('knight', ['tempered_blade']);
  s.combat.enemies[0].hp = 100; s.combat.heat = 4;
  L.playCard(s, 0, 0);
  assert.equal(s.combat.enemies[0].hp, 95);
  s = fight('knight', ['tempered_blade']);
  s.combat.enemies[0].hp = 100; s.combat.heat = 5;
  L.playCard(s, 0, 0);
  assert.equal(s.combat.enemies[0].hp, 90);
  s = fight('ranger', ['snipe']);
  s.combat.enemies[0].hp = 100; s.combat.heat = 2;
  L.playCard(s, 0, 0);
  assert.equal(s.combat.enemies[0].hp, 82);
});

test('block, vulnerable, weak, strength, burn', () => {
  const s = fight('knight', ['bash', 'strike', 'guard']);
  const c = s.combat; const e = c.enemies[0]; e.hp = 100; e.block = 3;
  L.playCard(s, 0, 0);               // 8 dmg - 3 block, then Vulnerable 1
  assert.equal(e.hp, 95); assert.equal(e.vuln, 1);
  c.str = 2;
  L.playCard(s, 0, 0);               // (6+2)*1.5 = 12
  assert.equal(e.hp, 83);
  c.weak = 1; c.hand.push({ id: 'strike', up: false });
  L.playCard(s, 1, 0);               // floor((6+2)*.75*1.5) = 9
  assert.equal(e.hp, 74);
  L.playCard(s, 0);
  assert.equal(c.block, 5);
  e.burn = 4; const before = e.hp;
  L.endTurn(s);
  assert.equal(e.hp, before - 4); assert.equal(e.burn, 3); assert.equal(e.vuln, 0);
});

test('a run can be saved and resumed without changing the outcome', () => {
  const s = L.newRun({ hero: 'ranger', seed: 99 });
  L.chooseNode(s, 0); L.playCard(s, 0, 0);
  const t = L.deserialize(L.serialize(s));
  L.endTurn(s); L.endTurn(t);
  assert.deepEqual({ ...s, ev: [] }, { ...t, ev: [] });
});

test('relics do what they say', () => {
  const s = L.newRun({ hero: 'knight', seed: 3 });
  for (const id of ['heat_sink', 'bellows', 'buckler', 'whetstone', 'thorn_ring', 'heartstone', 'cold_iron']) L.grantRelic(s, id);
  assert.equal(s.maxhp, HEROES.knight.hp + 10);
  L.chooseNode(s, 0);
  const c = s.combat;
  assert.equal(c.limit, 10); assert.equal(c.cool, 5); assert.equal(c.block, 6); assert.equal(c.str, 1); assert.equal(c.powers.thorns, 2);
  assert.equal(L.costOf(s, { id: 'heavy_blow', up: false }).heat, 0);
  c.hand = [{ id: 'guard', up: false }, { id: 'guard', up: false }];
  L.playCard(s, 0); assert.equal(c.heat, 0);
  L.playCard(s, 0); assert.equal(c.heat, 1);
});

test('bot runs always finish; every hero can win and can lose', () => {
  for (const hero of Object.keys(HEROES)) {
    let wins = 0, losses = 0;
    for (let i = 0; i < 60; i++) {
      const s = playRun({ hero, seed: 500 + i });
      assert.ok(s.phase === 'win' || s.phase === 'over', `${hero} seed ${500 + i} ended in ${s.phase}`);
      assert.ok(s.hp >= 0 && s.hp <= s.maxhp);
      if (s.phase === 'win') wins++; else losses++;
    }
    assert.ok(wins > 0 && losses > 0, `${hero}: ${wins} wins, ${losses} losses`);
  }
});
