const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const O = require('../overlays/lib.js');
const { panelSvg, DEFAULT_PANELS, ICONS } = require('../scripts/panels.js');
const { fieldsFor, buildWidget } = require('../scripts/streamelements.js');
const themes = require('../themes.json');

test('params parse with encoding and plus-as-space', () => {
  assert.deepEqual(O.parseParams('?theme=neon&title=Live+now%21&flag'), { theme: 'neon', title: 'Live now!', flag: '' });
  assert.deepEqual(O.parseParams(''), {});
});

test('theme resolution, colour overrides and fallback', () => {
  const t = O.resolveTheme(themes, { theme: 'sunset', accent: '00ff00', accent2: 'not-a-colour' });
  assert.equal(t.accent, '#00ff00');
  assert.equal(t.accent2, themes.sunset.accent2);
  assert.equal(O.resolveTheme(themes, { theme: 'nope' }).label, themes.neon.label);
  assert.equal(themes.neon.accent, '#b14cff', 'base theme not mutated');
});

test('countdown: minutes, until (rolls to tomorrow), formatting', () => {
  const now = new Date(2026, 10, 8, 20, 0, 0);
  assert.equal(O.countdownTarget({ minutes: '10' }, now) - now.getTime(), 600000);
  assert.equal(O.countdownTarget({}, now) - now.getTime(), 300000);
  assert.equal(O.countdownTarget({ until: '20:30' }, now) - now.getTime(), 1800000);
  assert.equal(O.countdownTarget({ until: '19:00' }, now) - now.getTime(), 23 * 3600000);
  assert.equal(O.formatCountdown(65000), '01:05');
  assert.equal(O.formatCountdown(3725000), '1:02:05');
  assert.equal(O.formatCountdown(-5), '00:00');
});

test('socials parse', () => {
  assert.deepEqual(O.parseSocials('twitch:me, X:me2,site.com'), [
    { platform: 'twitch', handle: 'me' }, { platform: 'x', handle: 'me2' }, { platform: 'link', handle: 'site.com' }]);
});

test('alerts: templates, gifts, tips, months and HTML escaping', () => {
  assert.equal(O.formatAlert('follower', { name: 'Ann' }).message, 'Ann just followed!');
  assert.equal(O.formatAlert('subscriber', { name: 'Bo', amount: 6 }).message, 'Bo subscribed for 6 months!');
  assert.equal(O.formatAlert('subscriber', { name: 'Bo', amount: 1 }).message, 'Bo subscribed!');
  const gift = O.formatAlert('subscriber', { name: 'Cy', gifted: true, sender: 'Di' });
  assert.equal(gift.kind, 'gift');
  assert.equal(gift.message, 'Di gifted a sub to Cy!');
  assert.equal(O.formatAlert('tip', { name: 'E', amount: 5 }, null, { currency: '€' }).message, 'E tipped €5.00!');
  const evil = O.formatAlert('tip', { name: '<img src=x onerror=alert(1)>', amount: 1, message: '<script>' });
  assert.ok(!evil.message.includes('<img'));
  assert.equal(evil.userMessage, '&lt;script&gt;');
  assert.equal(O.formatAlert('unknown', {}), null);
});

test('alert queue never overlaps', () => {
  const shown = [];
  let pending = null;
  const q = new O.AlertQueue((a, done) => { shown.push(a); pending = done; });
  q.push(1); q.push(2); q.push(3);
  assert.deepEqual(shown, [1]);
  pending(); assert.deepEqual(shown, [1, 2]);
  pending(); pending(); assert.deepEqual(shown, [1, 2, 3]);
});

test('panels: valid-looking SVG for every icon, label escaped', () => {
  for (const name of DEFAULT_PANELS) assert.ok(ICONS[name], name);
  const svg = panelSvg({ label: 'Q&A <live>', icon: 'about', theme: themes.neon });
  assert.match(svg, /^<svg[^>]+width="320" height="100"/);
  assert.match(svg, /Q&amp;A &lt;LIVE&gt;/);
});

test('StreamElements widget bundles lib and theme defaults', () => {
  const f = fieldsFor(themes.forest);
  assert.equal(f.accentColor.value, themes.forest.accent);
  assert.equal(f.enable_raid.value, 'yes');
  assert.ok(f.giftText && !f.enable_gift);
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'ok-'));
  buildWidget(themes.forest, out);
  const js = fs.readFileSync(path.join(out, 'widget.js'), 'utf8');
  assert.ok(js.includes('function formatAlert') && !js.includes('@@LIB@@'));
  const css = fs.readFileSync(path.join(out, 'widget.css'), 'utf8');
  assert.ok(css.includes('.alert-icon') && css.includes('{{accentColor}}'));
  // Every {{placeholder}} in the CSS must exist as a field.
  for (const [, k] of css.matchAll(/\{\{(\w+)\}\}/g)) assert.ok(f[k], `missing field ${k}`);
});

test('widget handles a StreamElements event end to end', () => {
  // Minimal DOM + window shim, then run the bundled widget.js.
  const els = {};
  const el = () => ({ textContent: '', innerHTML: '', classList: { add() {}, remove() {} } });
  const listeners = {};
  const window = { addEventListener: (n, fn) => { listeners[n] = fn; } };
  const document = { getElementById: (id) => (els[id] ??= el()) };
  const out = fs.mkdtempSync(path.join(os.tmpdir(), 'ok-'));
  buildWidget(themes.neon, out);
  const code = fs.readFileSync(path.join(out, 'widget.js'), 'utf8');
  new Function('window', 'document', 'setTimeout', 'Audio', 'module', code)(window, document, () => {}, function () {}, undefined);
  listeners.onWidgetLoad({ detail: { fieldData: { cheerText: '{name} threw {amount} bits', minBits: 100 } } });
  listeners.onEventReceived({ detail: { listener: 'cheer-latest', event: { name: 'Zed', amount: 50 } } });
  assert.equal(els.amsg?.innerHTML ?? '', '', 'below minBits is ignored');
  listeners.onEventReceived({ detail: { listener: 'cheer-latest', event: { name: 'Zed', amount: 500 } } });
  assert.equal(els.amsg.innerHTML, 'Zed threw 500 bits');
});
