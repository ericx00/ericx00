import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tierList, groupByTier, TIERS } from './stats.js';
import { optimizeBuild, buildStats } from './optimizer.js';
import { diffPatches, diffToMarkdown } from './diff.js';

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pct = (x) => `${(x * 100).toFixed(1)}%`;

const CSS = `:root{--bg:#0f1117;--panel:#181b24;--text:#e8e9ee;--muted:#9aa0b0;--line:#2a2f3d;--accent:#7c5cff;
--S:#ff5c7a;--A:#ff9f43;--B:#feca57;--C:#48dbfb;--D:#8395a7}
@media (prefers-color-scheme: light){:root{--bg:#f6f7fb;--panel:#fff;--text:#1b1e27;--muted:#5d6475;--line:#e3e6ee}}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--text)}
main{max-width:920px;margin:0 auto;padding:24px 16px 64px}a{color:var(--accent)}
nav{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;margin-bottom:8px}h1{line-height:1.2;margin:.3em 0}
.muted{color:var(--muted)}.tier{display:grid;grid-template-columns:56px 1fr;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:10px 0;background:var(--panel)}
.tier>b{display:grid;place-items:center;font-size:24px;color:#111}.chips{display:flex;flex-wrap:wrap;gap:8px;padding:10px}
.chip{border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:14px}.chip small{color:var(--muted);display:block}
table{width:100%;border-collapse:collapse;font-size:14px;margin:12px 0}td,th{padding:8px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--muted);font-weight:600}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin:16px 0}
.buff{color:#2ecc71}.nerf{color:#ff6b6b}.adjusted{color:#feca57}.cta{display:inline-block;background:var(--accent);color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:600}
@media (max-width:600px){.hide-sm{display:none}}`;

function page({ title, description, canonical, body, jsonLd, nav }) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(description)}">
${canonical ? `<link rel="canonical" href="${esc(canonical)}">` : ''}
<meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}"><meta property="og:type" content="article">
${jsonLd ? `<script type="application/ld+json">${JSON.stringify(jsonLd).replace(/</g, '\\u003c')}</script>` : ''}
<style>${CSS}</style></head><body><main>${nav ?? ''}${body}</main></body></html>`;
}

function article(title, description, url, date) {
  return { '@context': 'https://schema.org', '@type': 'Article', headline: title, description, datePublished: date, dateModified: date, mainEntityOfPage: url };
}

export function computePatch(game, patch, prev) {
  const tiers = tierList(patch.heroes, { minGames: game.minGames ?? 50 });
  const builds = Object.entries(game.roles).map(([role, r]) => {
    const res = optimizeBuild({ items: patch.items, weights: r.weights, ...game.build });
    return { role, label: r.label, ...res, totals: buildStats(res?.items ?? []) };
  });
  const diff = prev ? diffPatches(prev, patch) : null;
  return { tiers, builds, diff };
}

export function buildSite(games, outDir, { now = new Date() } = {}) {
  rmSync(outDir, { recursive: true, force: true });
  mkdirSync(outDir, { recursive: true });
  const urls = [];
  const write = (rel, html, siteUrl) => {
    const full = join(outDir, rel);
    mkdirSync(join(full, '..'), { recursive: true });
    writeFileSync(full, html);
    if (siteUrl && rel.endsWith('.html')) urls.push(`${siteUrl.replace(/\/$/, '')}/${rel.replace(/index\.html$/, '')}`);
  };

  const indexLinks = [];
  for (const game of games) {
    const site = game.siteUrl ?? '';
    game.patches.forEach((patch, k) => {
      const prev = game.patches[k - 1];
      const latest = k === game.patches.length - 1;
      const { tiers, builds, diff } = computePatch(game, patch, prev);
      const base = `${game.slug}/${patch.version}`;
      const nav = `<nav><a href="../../index.html">All games</a><a href="index.html">Tier list</a><a href="builds.html">Best builds</a>${diff ? '<a href="changes.html">Patch changes</a>' : ''}</nav>`;
      const grouped = groupByTier(tiers);

      // Tier list
      const tTitle = `${game.name} tier list — patch ${patch.version} (${new Date(patch.date).toLocaleString('en', { month: 'long', year: 'numeric' })})`;
      const tDesc = `Every ${game.name} hero ranked for patch ${patch.version}, from ${tiers.reduce((s, h) => s + h.games, 0).toLocaleString('en')} games. Win rates adjusted for sample size.`;
      const tierHtml = TIERS.map((t) => `<div class="tier"><b style="background:var(--${t})">${t}</b><div class="chips">${
        grouped[t].map((h) => `<span class="chip">${esc(h.name)}<small>${pct(h.winRate)} WR · ${pct(h.pickRate)} PR</small></span>`).join('') || '<span class="muted">—</span>'
      }</div></div>`).join('');
      const table = `<table><tr><th>#</th><th>Hero</th><th>Tier</th><th>Win rate</th><th class="hide-sm">Pick rate</th><th class="hide-sm">Games</th></tr>${
        tiers.map((h, i) => `<tr><td>${i + 1}</td><td>${esc(h.name)}</td><td>${h.tier}</td><td>${pct(h.winRate)}</td><td class="hide-sm">${pct(h.pickRate)}</td><td class="hide-sm">${h.games.toLocaleString('en')}</td></tr>`).join('')}</table>`;
      write(`${base}/index.html`, page({
        title: tTitle, description: tDesc, canonical: site && `${site}/${base}/`, nav,
        jsonLd: article(tTitle, tDesc, `${site}/${base}/`, patch.date),
        body: `<h1>${esc(tTitle)}</h1><p class="muted">Updated ${esc(patch.date)}. Ranking uses the Wilson lower bound of win rate, so tiny samples can't top the list.</p>${tierHtml}${table}
<div class="card"><b>Want the full matchup sheets?</b><p class="muted">Counters, item timings and per-rank stats for every hero, updated each patch.</p><a class="cta" href="#">Get Pro guides</a></div>`,
      }), site);

      // Builds
      const bTitle = `Best ${game.name} builds for patch ${patch.version}`;
      const bDesc = `Optimal ${builds.map((b) => b.label).join(', ')} builds for ${game.name} ${patch.version}, computed under a ${game.build.budget.toLocaleString('en')} gold budget.`;
      const bBody = builds.map((b) => `<div class="card"><h2>${esc(b.label)}</h2>${b.items ? `<ol>${b.items.map((i) => `<li>${esc(i.name)} <span class="muted">(${i.cost.toLocaleString('en')}g)</span></li>`).join('')}</ol>
<p class="muted">Total ${b.cost.toLocaleString('en')}g · ${Object.entries(b.totals).map(([k, v]) => `${k.replace(/_/g, ' ')} ${v}`).join(' · ')}</p>` : '<p>No valid build under these limits.</p>'}</div>`).join('');
      write(`${base}/builds.html`, page({ title: bTitle, description: bDesc, canonical: site && `${site}/${base}/builds.html`, nav,
        jsonLd: article(bTitle, bDesc, `${site}/${base}/builds.html`, patch.date), body: `<h1>${esc(bTitle)}</h1>${bBody}` }), site);

      // Changes
      if (diff) {
        const md = diffToMarkdown(diff, game.name);
        writeFileSync(join(outDir, base, 'changes.md'), md);
        const cTitle = `${game.name} patch ${patch.version}: every change explained`;
        const cDesc = `All buffs, nerfs and item changes from ${game.name} ${diff.from} to ${diff.to}, with before/after numbers.`;
        const sec = (label, c) => (c.changed.length || c.added.length || c.removed.length) ? `<h2>${label}</h2>${c.changed.map((x) => `<div class="card"><b>${esc(x.name)}</b> <span class="${x.verdict}">${x.verdict}</span><ul>${
          x.changes.map((ch) => `<li class="${ch.kind}">${esc(ch.stat.replace(/_/g, ' '))}: ${ch.before} → ${ch.after}</li>`).join('')}</ul></div>`).join('')}${
          c.added.map((a) => `<p>✨ New: <b>${esc(a.name)}</b></p>`).join('')}${c.removed.map((r) => `<p>🗑️ Removed: <b>${esc(r.name)}</b></p>`).join('')}` : '';
        write(`${base}/changes.html`, page({ title: cTitle, description: cDesc, canonical: site && `${site}/${base}/changes.html`, nav,
          jsonLd: article(cTitle, cDesc, `${site}/${base}/changes.html`, patch.date),
          body: `<h1>${esc(cTitle)}</h1><p class="muted">${esc(diff.from)} → ${esc(diff.to)}</p>${sec('Heroes', diff.heroes)}${sec('Items', diff.items)}` }), site);
      }
      if (latest) indexLinks.push({ game, patch, base, hasDiff: !!diff });
    });
  }

  const home = indexLinks.map(({ game, patch, base, hasDiff }) => `<div class="card"><h2>${esc(game.name)} <span class="muted">patch ${esc(patch.version)}</span></h2>
<p><a href="${base}/index.html">Tier list</a> · <a href="${base}/builds.html">Best builds</a>${hasDiff ? ` · <a href="${base}/changes.html">What changed</a>` : ''}</p></div>`).join('');
  write('index.html', page({ title: 'Patch-day meta guides', description: 'Tier lists, builds and patch breakdowns, updated the day each patch lands.', body: `<h1>Patch-day meta guides</h1>${home}` }), games[0]?.siteUrl);

  const lastmod = now.toISOString().slice(0, 10);
  writeFileSync(join(outDir, 'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${
    urls.map((u) => `  <url><loc>${esc(u)}</loc><lastmod>${lastmod}</lastmod></url>`).join('\n')}\n</urlset>\n`);
  const sitemapUrl = games[0]?.siteUrl ? `${games[0].siteUrl.replace(/\/$/, '')}/sitemap.xml` : 'sitemap.xml';
  writeFileSync(join(outDir, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${sitemapUrl}\n`);
  return { pages: urls.length };
}
