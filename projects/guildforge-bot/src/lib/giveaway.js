import { randomInt } from 'node:crypto';

/** Pick `count` distinct winners with a partial Fisher-Yates shuffle (crypto RNG). */
export function pickWinners(entrants, count, rand = randomInt) {
  const pool = [...new Set(entrants)];
  const n = Math.min(count, pool.length);
  for (let i = 0; i < n; i++) {
    const j = i + rand(pool.length - i);
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, n);
}

/** Parse durations like "30m", "2h", "1d", "1h30m". Returns milliseconds or null. */
export function parseDuration(text) {
  const units = { s: 1e3, m: 60e3, h: 3600e3, d: 86400e3, w: 604800e3 };
  const clean = String(text).trim().toLowerCase().replace(/\s+/g, '');
  if (!/^(\d+[smhdw])+$/.test(clean)) return null;
  let total = 0;
  for (const [, n, u] of clean.matchAll(/(\d+)([smhdw])/g)) total += Number(n) * units[u];
  return total > 0 ? total : null;
}
