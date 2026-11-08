// Build optimizer: pick the item set that maximises a weighted stat score
// under a gold budget, a slot limit and per-category caps.
//
// It's an exact search (branch and bound). Item pools in a single patch are small
// (tens to low hundreds), so exact answers are cheap and beat greedy heuristics,
// which miss combos like "two mid items > one big item".

export function itemValue(item, weights) {
  let v = 0;
  for (const [stat, w] of Object.entries(weights)) v += (item.stats?.[stat] ?? 0) * w;
  return v;
}

/**
 * @param {object} p
 * @param {Array} p.items       [{ id, name, cost, category, stats: { attack: 40, ... } }]
 * @param {object} p.weights    { attack: 1, crit: 2.5, ... }  (from a role profile)
 * @param {number} p.budget     gold
 * @param {number} p.slots      max items
 * @param {object} [p.caps]     max items per category, e.g. { boots: 1 }
 * @param {string[]} [p.require] item ids that must be included
 * @param {string[]} [p.exclude] item ids that cannot be used
 * @returns {{ items, value, cost }}
 */
export function optimizeBuild({ items, weights, budget, slots, caps = {}, require = [], exclude = [] }) {
  const ex = new Set(exclude);
  const req = items.filter((i) => require.includes(i.id));
  if (req.length !== new Set(require).size) throw new Error('A required item is not in the item pool.');

  const baseCost = req.reduce((s, i) => s + i.cost, 0);
  const baseCats = {};
  for (const i of req) baseCats[i.category] = (baseCats[i.category] ?? 0) + 1;
  if (baseCost > budget || req.length > slots) return null;
  for (const [cat, n] of Object.entries(baseCats)) if (caps[cat] != null && n > caps[cat]) return null;

  const pool = items
    .filter((i) => !ex.has(i.id) && !require.includes(i.id))
    .map((i) => ({ ...i, value: itemValue(i, weights) }))
    .filter((i) => i.value > 0)
    .sort((a, b) => b.value / b.cost - a.value / a.cost);

  let best = { picks: [], value: -Infinity };
  const picks = [];
  const cats = { ...baseCats };

  // Optimistic bound = min of two valid upper bounds on what the remaining items can add:
  //  (a) fractional knapsack on gold alone (ignores slots), and
  //  (b) the `slotsLeft` most valuable remaining items (ignores gold).
  // A greedy "by ratio, stop at slot limit" bound is NOT valid: with few slots an
  // expensive high-value item can beat several cheap efficient ones.
  const bound = (start, gold, slotsLeft) => {
    let frac = 0;
    for (let k = start, g = gold; k < pool.length && g > 0; k++) {
      const it = pool[k];
      if (it.cost <= g) { frac += it.value; g -= it.cost; }
      else { frac += it.value * (g / it.cost); break; }
    }
    let top = 0;
    if (slotsLeft < pool.length - start) {
      const vals = [];
      for (let k = start; k < pool.length; k++) vals.push(pool[k].value);
      vals.sort((a, b) => b - a);
      for (let k = 0; k < slotsLeft; k++) top += vals[k];
    } else {
      top = Infinity;
    }
    return Math.min(frac, top);
  };

  const dfs = (idx, gold, slotsLeft, value) => {
    if (value > best.value) best = { picks: [...picks], value };
    if (idx >= pool.length || slotsLeft === 0) return;
    if (value + bound(idx, gold, slotsLeft) <= best.value) return;
    const it = pool[idx];
    const capOk = caps[it.category] == null || (cats[it.category] ?? 0) < caps[it.category];
    if (it.cost <= gold && capOk) {
      picks.push(it);
      cats[it.category] = (cats[it.category] ?? 0) + 1;
      dfs(idx + 1, gold - it.cost, slotsLeft - 1, value + it.value);
      cats[it.category]--;
      picks.pop();
    }
    dfs(idx + 1, gold, slotsLeft, value);
  };

  dfs(0, budget - baseCost, slots - req.length, req.reduce((s, i) => s + itemValue(i, weights), 0));
  const chosen = [...req, ...best.picks];
  return {
    items: chosen.map(({ value, ...rest }) => rest),
    value: Math.round(best.value * 100) / 100,
    cost: chosen.reduce((s, i) => s + i.cost, 0),
  };
}

/** Sum of stats for a build, for display. */
export function buildStats(items) {
  const out = {};
  for (const i of items) for (const [k, v] of Object.entries(i.stats ?? {})) out[k] = (out[k] ?? 0) + v;
  return out;
}
