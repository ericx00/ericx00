import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { CARD_LIST, cardOf, describe, RELIC_LIST, ENEMIES, HEROES } from '../src/data.js';

const fnt = readFileSync(new URL('../assets/fonts/forge-sans.fnt', import.meta.url), 'utf8');
const adv = Object.fromEntries([...fnt.matchAll(/char id=(\d+) .*?xadvance=(\d+)/g)].map((m) => [+m[1], +m[2]]));
const width = (s) => [...s].reduce((w, ch) => w + (adv[ch.charCodeAt(0)] ?? 6), 0) - 1;
const wrap = (s, w) => { const out = []; let cur = ''; for (const word of s.split(' ')) { const t = cur ? cur + ' ' + word : word; if (width(t) <= w || !cur) cur = t; else { out.push(cur); cur = word; } } if (cur) out.push(cur); return out; };

test('every card title and rules text fits on the card', () => {
  for (const c of CARD_LIST) for (const up of [false, true]) {
    const card = cardOf({ id: c.id, up });
    assert.ok(width(card.name) <= 76, `${card.name} title is ${width(card.name)} px`);
    const lines = wrap(describe(card), 70);
    assert.ok(lines.length <= 6, `${card.name} needs ${lines.length} lines`);
    for (const l of lines) assert.ok(width(l) <= 74, `${card.name}: "${l}" is too wide`);
  }
});

test('every image and sound the game asks for is in assets/', () => {
  const has = (p) => existsSync(new URL('../assets/' + p, import.meta.url));
  const icons = JSON.parse(readFileSync(new URL('../assets/atlas_icons.json', import.meta.url))).frames;
  const ui = JSON.parse(readFileSync(new URL('../assets/atlas_ui.json', import.meta.url))).frames;
  for (const a of [...CARD_LIST.map((c) => c.art), ...RELIC_LIST.map((r) => r.art)]) {
    if (a.startsWith('k:')) assert.ok(icons[a.slice(2)], a); else assert.ok(has(`items/${a}.png`), a);
  }
  for (const id of [...Object.keys(ENEMIES), ...Object.values(HEROES).map((h) => h.sprite)]) assert.ok(has(`chars/${id}.png`), id);
  const main = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  const sfx = main.match(/const SFX = \[([^\]]+)\]/)[1].match(/'(\w+)'/g).map((s) => s.slice(1, -1));
  for (const s of sfx) assert.ok(has(`sfx/${s}_01.ogg`) && has(`sfx/${s}_02.ogg`), s);
  for (const m of main.matchAll(/A\.play\('(\w+)'/g)) assert.ok(sfx.includes(m[1]), `sound ${m[1]} is played but not loaded`);
  for (const m of main.match(/const MUSIC = \[([^\]]+)\]/)[1].match(/'(\w+)'/g)) assert.ok(has(`music/${m.slice(1, -1)}.ogg`), m);
  for (const m of main.matchAll(/'((?:intent|status|resource|map|action)_\w+)'/g)) if (!sfx.includes(m[1]) && !main.includes(`'${m[1]}', 'battle`) && m[1] !== 'map_embers') assert.ok(icons[m[1]] || ui[m[1]], `icon ${m[1]}`);
});
