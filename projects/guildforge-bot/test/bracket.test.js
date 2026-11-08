import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createBracket, seedOrder, reportResult, pendingMatches, championOf, renderBracket, nextPowerOfTwo } from '../src/lib/bracket.js';

const players = (n) => Array.from({ length: n }, (_, i) => ({ id: `p${i + 1}`, name: `Player ${i + 1}` }));

test('seed order keeps top seeds apart', () => {
  assert.deepEqual(seedOrder(4), [1, 4, 2, 3]);
  assert.deepEqual(seedOrder(8), [1, 8, 4, 5, 2, 7, 3, 6]);
  assert.equal(nextPowerOfTwo(5), 8);
});

test('byes advance automatically and top seeds get them', () => {
  const b = createBracket(players(5));
  assert.equal(b.size, 8);
  assert.equal(b.rounds, 3);
  // seeds 1..3 get byes against nonexistent seeds 6..8
  const r2 = b.matches.filter((m) => m.round === 2);
  const advanced = r2.flatMap((m) => [m.p1, m.p2]).filter(Boolean).sort();
  assert.deepEqual(advanced, ['p1', 'p2', 'p3']);
  // playable now: 4 vs 5 (round 1) and 2 vs 3 (both had byes)
  assert.equal(pendingMatches(b).length, 2);
});

test('playing a full bracket crowns a champion', () => {
  const b = createBracket(players(6));
  let guard = 0;
  while (!championOf(b) && guard++ < 20) {
    const m = pendingMatches(b)[0];
    // lower seed number always wins
    const win = Number(m.p1.slice(1)) < Number(m.p2.slice(1)) ? m.p1 : m.p2;
    reportResult(b, win);
  }
  assert.equal(championOf(b), 'p1');
  assert.match(renderBracket(b), /Champion: Player 1/);
});

test('rejects bad input', () => {
  assert.throws(() => createBracket(players(1)));
  assert.throws(() => createBracket([{ id: 'a', name: 'A' }, { id: 'a', name: 'A' }]));
  const b = createBracket(players(2));
  assert.throws(() => reportResult(b, 'nobody'));
  reportResult(b, 'p2');
  assert.throws(() => reportResult(b, 'p2'), /no match/);
});
