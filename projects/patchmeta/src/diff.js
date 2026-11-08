// Patch diff: turn two patch data files into a list of buffs/nerfs.
// This is what lets you publish "Patch X.Y changes, explained" minutes after notes drop.

/** Stats where a lower number is better for the player. */
export const LOWER_IS_BETTER = new Set(['cost', 'cooldown', 'cast_time', 'mana_cost', 'reload']);

function classify(stat, before, after) {
  if (before === after) return null;
  const up = after > before;
  const good = LOWER_IS_BETTER.has(stat) ? !up : up;
  return good ? 'buff' : 'nerf';
}

function diffStats(a = {}, b = {}) {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  const changes = [];
  for (const k of [...keys].sort()) {
    const before = a[k] ?? 0;
    const after = b[k] ?? 0;
    const kind = classify(k, before, after);
    if (kind) changes.push({ stat: k, before, after, kind, pct: before ? (after - before) / Math.abs(before) : null });
  }
  return changes;
}

function verdict(changes) {
  const b = changes.filter((c) => c.kind === 'buff').length;
  const n = changes.filter((c) => c.kind === 'nerf').length;
  if (b && n) return 'adjusted';
  return b ? 'buff' : 'nerf';
}

/** Compare a collection keyed by id. Each entry has `stats` and optionally `cost`. */
export function diffCollection(before = [], after = []) {
  const A = new Map(before.map((x) => [x.id, x]));
  const B = new Map(after.map((x) => [x.id, x]));
  const out = { added: [], removed: [], changed: [] };
  for (const [id, b] of B) {
    const a = A.get(id);
    if (!a) { out.added.push(b); continue; }
    const changes = diffStats({ ...a.stats, ...(a.cost != null ? { cost: a.cost } : {}) },
      { ...b.stats, ...(b.cost != null ? { cost: b.cost } : {}) });
    if (changes.length) out.changed.push({ id, name: b.name, changes, verdict: verdict(changes) });
  }
  for (const [id, a] of A) if (!B.has(id)) out.removed.push(a);
  return out;
}

export function diffPatches(oldPatch, newPatch) {
  return {
    from: oldPatch.version,
    to: newPatch.version,
    heroes: diffCollection(oldPatch.heroes, newPatch.heroes),
    items: diffCollection(oldPatch.items, newPatch.items),
  };
}

const fmt = (n) => (Number.isInteger(n) ? String(n) : n.toFixed(2));

/** Markdown summary: paste into Reddit / a newsletter / a video script. */
export function diffToMarkdown(d, gameName) {
  const lines = [`# ${gameName} patch ${d.to}: every change explained`, ''];
  for (const [label, coll] of [['Heroes', d.heroes], ['Items', d.items]]) {
    if (!coll.changed.length && !coll.added.length && !coll.removed.length) continue;
    lines.push(`## ${label}`, '');
    for (const c of coll.changed) {
      const tag = { buff: '🟢 Buff', nerf: '🔴 Nerf', adjusted: '🟡 Adjusted' }[c.verdict];
      lines.push(`### ${c.name} (${tag})`);
      for (const ch of c.changes) {
        const pct = ch.pct != null ? ` (${ch.pct > 0 ? '+' : ''}${Math.round(ch.pct * 100)}%)` : '';
        lines.push(`- ${ch.stat.replace(/_/g, ' ')}: ${fmt(ch.before)} → ${fmt(ch.after)}${pct}`);
      }
      lines.push('');
    }
    for (const a of coll.added) lines.push(`- ✨ New: **${a.name}**`);
    for (const r of coll.removed) lines.push(`- 🗑️ Removed: **${r.name}**`);
    if (coll.added.length || coll.removed.length) lines.push('');
  }
  return lines.join('\n');
}
