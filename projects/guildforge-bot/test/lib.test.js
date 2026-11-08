import { test } from 'node:test';
import assert from 'node:assert/strict';
import { expectedScore, updateRatings } from '../src/lib/elo.js';
import { pickWinners, parseDuration } from '../src/lib/giveaway.js';
import { PLANS, resolvePlan, isActiveEntitlement } from '../src/lib/plans.js';

test('elo is zero-sum-ish and favours upsets', () => {
  assert.equal(expectedScore(1000, 1000), 0.5);
  const even = updateRatings({ rating: 1000, games: 50 }, { rating: 1000, games: 50 });
  assert.equal(even.winner, 1008);
  assert.equal(even.loser, 992);
  const upset = updateRatings({ rating: 900, games: 50 }, { rating: 1100, games: 50 });
  assert.ok(upset.winner - 900 > 8);
});

test('pickWinners returns distinct winners from the pool', () => {
  const w = pickWinners(['a', 'b', 'c', 'c', 'd'], 3);
  assert.equal(w.length, 3);
  assert.equal(new Set(w).size, 3);
  assert.deepEqual(pickWinners(['a'], 5), ['a']);
  assert.deepEqual(pickWinners([], 2), []);
});

test('parseDuration', () => {
  assert.equal(parseDuration('30m'), 1_800_000);
  assert.equal(parseDuration('1h30m'), 5_400_000);
  assert.equal(parseDuration('1 d'), 86_400_000);
  assert.equal(parseDuration('soon'), null);
  assert.equal(parseDuration('0m'), null);
});

test('plan resolution: entitlements, overrides and expiry', () => {
  const now = 1_000_000;
  const sku = 'sku1';
  const active = { skuId: sku, guildId: 'g1', endsTimestamp: now + 1 };
  assert.ok(isActiveEntitlement(active, { skuId: sku, guildId: 'g1', now }));
  assert.ok(!isActiveEntitlement(active, { skuId: sku, guildId: 'g2', now }));
  assert.ok(!isActiveEntitlement({ ...active, endsTimestamp: now }, { skuId: sku, guildId: 'g1', now }));
  assert.equal(resolvePlan({ guildId: 'g1', entitlements: [active], skuId: sku, now }), PLANS.premium);
  assert.equal(resolvePlan({ guildId: 'g1', entitlements: new Map([['x', active]]), skuId: sku, now }), PLANS.premium);
  assert.equal(resolvePlan({ guildId: 'g1', entitlements: [], skuId: sku, now }), PLANS.free);
  assert.equal(resolvePlan({ guildId: 'g1', override: { premium: true, until: null }, now }), PLANS.premium);
  assert.equal(resolvePlan({ guildId: 'g1', override: { premium: true, until: now - 1 }, now }), PLANS.free);
});
