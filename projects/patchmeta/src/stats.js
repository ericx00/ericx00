// Tier lists that don't lie with small samples.

/**
 * Wilson score lower bound for a binomial proportion. A champion with 3/3 wins
 * should not outrank one with 5,400/10,000.
 */
export function wilsonLowerBound(wins, games, z = 1.96) {
  if (games <= 0) return 0;
  const p = wins / games;
  const z2 = z * z;
  const denom = 1 + z2 / games;
  const centre = p + z2 / (2 * games);
  const margin = z * Math.sqrt((p * (1 - p) + z2 / (4 * games)) / games);
  return (centre - margin) / denom;
}

/**
 * Score an entity. Win rate is the main signal (pessimistic bound); pick rate is a
 * small bonus because popular-and-winning is the "meta" readers want.
 */
export function metaScore({ wins, games }, totalGames, { pickWeight = 0.15 } = {}) {
  const wr = wilsonLowerBound(wins, games);
  const pick = totalGames > 0 ? games / totalGames : 0;
  return wr + pickWeight * Math.sqrt(pick);
}

export const TIERS = ['S', 'A', 'B', 'C', 'D'];
// Share of entities in each tier, best first.
const CUTS = [0.1, 0.3, 0.6, 0.85, 1];

/** Returns entities sorted best-first with { score, winRate, pickRate, tier }. */
export function tierList(entities, { minGames = 50, pickWeight } = {}) {
  const eligible = entities.filter((e) => e.games >= minGames);
  const totalGames = eligible.reduce((s, e) => s + e.games, 0);
  const scored = eligible
    .map((e) => ({
      ...e,
      winRate: e.wins / e.games,
      pickRate: totalGames ? e.games / totalGames : 0,
      score: metaScore(e, totalGames, { pickWeight }),
    }))
    .sort((a, b) => b.score - a.score);
  const n = scored.length;
  return scored.map((e, i) => {
    const pct = (i + 1) / n;
    const tier = TIERS[CUTS.findIndex((c) => pct <= c + 1e-9)];
    return { ...e, tier };
  });
}

export function groupByTier(list) {
  return Object.fromEntries(TIERS.map((t) => [t, list.filter((e) => e.tier === t)]));
}
