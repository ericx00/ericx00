import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { wilsonLowerBound, tierList } from '../src/stats.js';
import { optimizeBuild, itemValue } from '../src/optimizer.js';
import { diffPatches, diffToMarkdown } from '../src/diff.js';
import { loadGames, compareVersions, validatePatch } from '../src/data.js';
import { buildSite } from '../src/site.js';

const dataDir = join(dirname(fileURLToPath(import.meta.url)), '..', 'data');

test('wilson bound punishes tiny samples', () => {
  assert.equal(wilsonLowerBound(0, 0), 0);
  assert.ok(wilsonLowerBound(3, 3) < wilsonLowerBound(5400, 10000));
  const lb = wilsonLowerBound(50, 100);
  assert.ok(lb > 0.4 && lb < 0.5);
});

test('tier list filters low samples and assigns all tiers', () => {
  const heroes = Array.from({ length: 20 }, (_, i) => ({ id: `h${i}`, name: `H${i}`, wins: 400 + i * 10, games: 1000 }));
  heroes.push({ id: 'lucky', name: 'Lucky', wins: 9, games: 10 });
  const list = tierList(heroes, { minGames: 50 });
  assert.equal(list.length, 20);
  assert.equal(list[0].id, 'h19');
  assert.equal(list[0].tier, 'S');
  assert.equal(list.at(-1).tier, 'D');
  assert.deepEqual([...new Set(list.map((h) => h.tier))], ['S', 'A', 'B', 'C', 'D']);
});

function bruteForce({ items, weights, budget, slots, caps = {} }) {
  let best = 0;
  const n = items.length;
  for (let mask = 0; mask < 1 << n; mask++) {
    const pick = items.filter((_, i) => mask & (1 << i));
    if (pick.length > slots) continue;
    if (pick.reduce((s, i) => s + i.cost, 0) > budget) continue;
    const cats = {};
    let ok = true;
    for (const i of pick) { cats[i.category] = (cats[i.category] ?? 0) + 1; if (caps[i.category] != null && cats[i.category] > caps[i.category]) ok = false; }
    if (!ok) continue;
    best = Math.max(best, pick.reduce((s, i) => s + itemValue(i, weights), 0));
  }
  return Math.round(best * 100) / 100;
}

test('optimizer matches brute force on random pools', () => {
  let seed = 7;
  const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2 ** 31) / 2 ** 31);
  for (let trial = 0; trial < 200; trial++) {
    const items = Array.from({ length: 12 }, (_, i) => ({
      id: `i${i}`, name: `I${i}`, cost: 500 + Math.floor(rnd() * 3000), category: ['a', 'b', 'boots'][i % 3],
      stats: { atk: Math.floor(rnd() * 60), hp: Math.floor(rnd() * 400) },
    }));
    const p = { items, weights: { atk: 1, hp: 0.1 }, budget: 6000 + Math.floor(rnd() * 6000), slots: 4, caps: { boots: 1 } };
    assert.equal(optimizeBuild(p).value, bruteForce(p), `trial ${trial}`);
  }
});

test('optimizer honours require/exclude and impossible constraints', () => {
  const items = [
    { id: 'big', name: 'Big', cost: 3000, category: 'w', stats: { atk: 100 } },
    { id: 'mid', name: 'Mid', cost: 1500, category: 'w', stats: { atk: 60 } },
    { id: 'meh', name: 'Meh', cost: 1500, category: 'w', stats: { atk: 10 } },
  ];
  const base = { items, weights: { atk: 1 }, budget: 3000, slots: 2 };
  assert.deepEqual(optimizeBuild(base).items.map((i) => i.id), ['big']); // 100 > 60 + 10
  assert.deepEqual(optimizeBuild({ ...base, exclude: ['big'] }).items.map((i) => i.id).sort(), ['meh', 'mid']);
  assert.deepEqual(optimizeBuild({ ...base, require: ['meh'] }).items.map((i) => i.id).sort(), ['meh', 'mid']);
  assert.equal(optimizeBuild({ ...base, budget: 100, require: ['big'] }), null);
  assert.throws(() => optimizeBuild({ ...base, require: ['nope'] }));
});

test('diff classifies buffs, nerfs, cost changes, adds and removals', () => {
  const a = { version: '1.0', heroes: [{ id: 'x', name: 'X', stats: { attack: 10, cooldown: 8 } }], items: [{ id: 'old', name: 'Old', cost: 100, stats: {} }] };
  const b = { version: '1.1', heroes: [{ id: 'x', name: 'X', stats: { attack: 10, cooldown: 6 } }], items: [{ id: 'new', name: 'New', cost: 50, stats: {} }] };
  const d = diffPatches(a, b);
  assert.equal(d.heroes.changed[0].verdict, 'buff', 'lower cooldown is a buff');
  assert.equal(d.items.added[0].id, 'new');
  assert.equal(d.items.removed[0].id, 'old');
  assert.match(diffToMarkdown(d, 'Game'), /cooldown: 8 → 6 \(-25%\)/);
});

test('versions sort numerically and bad data is rejected', () => {
  assert.deepEqual(['1.10', '1.9', '1.2.1'].sort(compareVersions), ['1.2.1', '1.9', '1.10']);
  assert.throws(() => validatePatch({ version: '1', heroes: [{ id: 'a', name: 'A', role: 'r', wins: 5, games: 2 }] }), /wins\/games/);
});

test('sample data builds a full site', () => {
  const games = loadGames(dataDir);
  const out = mkdtempSync(join(tmpdir(), 'patchmeta-'));
  const { pages } = buildSite(games, out, { now: new Date('2026-11-05') });
  assert.equal(pages, 6);
  const tier = readFileSync(join(out, 'ironvale-arena/1.5/index.html'), 'utf8');
  assert.match(tier, /application\/ld\+json/);
  assert.match(tier, /<link rel="canonical"/);
  assert.ok(existsSync(join(out, 'ironvale-arena/1.5/changes.md')));
  assert.match(readFileSync(join(out, 'sitemap.xml'), 'utf8'), /ironvale-arena\/1.5\/builds.html/);
  for (const b of ['builds.html']) assert.match(readFileSync(join(out, 'ironvale-arena/1.5', b), 'utf8'), /Marksman/);
});
