import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

export function compareVersions(a, b) {
  const pa = String(a).split('.').map(Number);
  const pb = String(b).split('.').map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const d = (pa[i] ?? 0) - (pb[i] ?? 0);
    if (d) return d;
  }
  return 0;
}

const readJson = (p) => JSON.parse(readFileSync(p, 'utf8'));

export function validatePatch(p, file = 'patch') {
  const errs = [];
  if (!p.version) errs.push('missing version');
  for (const h of p.heroes ?? []) {
    if (!h.id || !h.name || !h.role) errs.push(`hero missing id/name/role: ${JSON.stringify(h).slice(0, 60)}`);
    if (!(h.games >= 0) || !(h.wins >= 0) || h.wins > h.games) errs.push(`hero ${h.id}: wins/games invalid`);
  }
  for (const i of p.items ?? []) {
    if (!i.id || !i.name || !(i.cost >= 0) || !i.category) errs.push(`item missing id/name/cost/category: ${i.id ?? '?'}`);
  }
  const ids = (p.heroes ?? []).map((h) => h.id).concat((p.items ?? []).map((i) => i.id));
  const dup = ids.find((id, k) => ids.indexOf(id) !== k);
  if (dup) errs.push(`duplicate id: ${dup}`);
  if (errs.length) throw new Error(`${file}: ${errs.join('; ')}`);
  return p;
}

/** Load every game under dataDir: [{ ...game.json, patches: [oldest..newest] }] */
export function loadGames(dataDir) {
  return readdirSync(dataDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && existsSync(join(dataDir, d.name, 'game.json')))
    .map((d) => {
      const dir = join(dataDir, d.name);
      const game = readJson(join(dir, 'game.json'));
      const pdir = join(dir, 'patches');
      const patches = readdirSync(pdir).filter((f) => f.endsWith('.json'))
        .map((f) => validatePatch(readJson(join(pdir, f)), f))
        .sort((a, b) => compareVersions(a.version, b.version));
      return { ...game, slug: game.slug ?? d.name, patches };
    });
}
