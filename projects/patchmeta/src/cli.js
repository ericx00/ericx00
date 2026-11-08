#!/usr/bin/env node
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, resolve, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadGames } from './data.js';
import { buildSite, computePatch } from './site.js';
import { diffPatches, diffToMarkdown } from './diff.js';
import { optimizeBuild, buildStats } from './optimizer.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = process.env.PATCHMETA_DATA ?? join(root, 'data');
const outDir = process.env.PATCHMETA_OUT ?? join(root, 'dist');
const [cmd, ...args] = process.argv.slice(2);

const findGame = (slug) => {
  const games = loadGames(dataDir);
  const g = slug ? games.find((x) => x.slug === slug) : games[0];
  if (!g) throw new Error(`Unknown game "${slug}". Available: ${games.map((x) => x.slug).join(', ')}`);
  return g;
};

switch (cmd) {
  case 'build': {
    const t = Date.now();
    const { pages } = buildSite(loadGames(dataDir), outDir);
    console.log(`Built ${pages} pages into ${outDir} in ${Date.now() - t}ms`);
    break;
  }
  case 'diff': {
    // patchmeta diff [game] -> markdown for the latest two patches
    const g = findGame(args[0]);
    if (g.patches.length < 2) throw new Error('Need at least two patches to diff.');
    const [a, b] = g.patches.slice(-2);
    console.log(diffToMarkdown(diffPatches(a, b), g.name));
    break;
  }
  case 'tiers': {
    const g = findGame(args[0]);
    const { tiers } = computePatch(g, g.patches.at(-1));
    for (const h of tiers) console.log(`${h.tier}  ${h.name.padEnd(12)} ${(h.winRate * 100).toFixed(1)}% WR  ${h.games} games`);
    break;
  }
  case 'optimize': {
    // patchmeta optimize <game> <role> [--require a,b] [--exclude c] [--budget n]
    const g = findGame(args[0]);
    const role = g.roles[args[1]];
    if (!role) throw new Error(`Unknown role. Roles: ${Object.keys(g.roles).join(', ')}`);
    const flag = (n) => { const k = args.indexOf(`--${n}`); return k >= 0 ? args[k + 1] : undefined; };
    const res = optimizeBuild({
      items: g.patches.at(-1).items, weights: role.weights, ...g.build,
      budget: Number(flag('budget') ?? g.build.budget),
      require: flag('require')?.split(',') ?? [], exclude: flag('exclude')?.split(',') ?? [],
    });
    if (!res) { console.log('No build satisfies those constraints.'); break; }
    for (const i of res.items) console.log(`- ${i.name} (${i.cost}g)`);
    console.log(`Total ${res.cost}g, score ${res.value}`, buildStats(res.items));
    break;
  }
  case 'serve': {
    const port = Number(args[0] ?? 4173);
    const types = { '.html': 'text/html; charset=utf-8', '.xml': 'application/xml', '.txt': 'text/plain', '.md': 'text/markdown' };
    createServer((req, res) => {
      let p = join(outDir, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (!p.startsWith(outDir)) { res.writeHead(403).end(); return; }
      if (existsSync(p) && statSync(p).isDirectory()) p = join(p, 'index.html');
      if (!existsSync(p)) { res.writeHead(404).end('Not found'); return; }
      res.writeHead(200, { 'content-type': types[extname(p)] ?? 'application/octet-stream' }).end(readFileSync(p));
    }).listen(port, () => console.log(`Serving ${outDir} at http://localhost:${port}`));
    break;
  }
  default:
    console.log(`patchmeta <command>
  build                         generate the static site into dist/
  tiers [game]                  print the tier list for the latest patch
  diff [game]                   markdown of every change in the latest patch
  optimize <game> <role> [--require ids] [--exclude ids] [--budget gold]
  serve [port]                  preview dist/ locally`);
}
