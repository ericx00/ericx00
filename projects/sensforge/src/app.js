import { GAMES, cm360, inches360, edpi, conversionTable, describeCm360, convert, degreesPerCount, roundSens } from './sens.js';
import { createPsa, candidates, choose, isDone, result } from './psa.js';
import { MODES, createSession, applyMouse, step, shoot, summary, project, pixelRadius } from './trainer.js';

const $ = (id) => document.getElementById(id);
const store = {
  get(k, d) { try { const v = localStorage.getItem(`sensforge:${k}`); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(`sensforge:${k}`, JSON.stringify(v)); } catch { /* private mode */ } },
};

// ---------- tabs ----------
document.querySelectorAll('[data-tab]').forEach((btn) => btn.addEventListener('click', () => showTab(btn.dataset.tab)));
function showTab(name) {
  document.querySelectorAll('[data-tab]').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === name)));
  document.querySelectorAll('.tab').forEach((s) => { s.hidden = s.id !== `tab-${name}`; });
  store.set('tab', name);
  if (name !== 'convert') syncTrainerLabels();
}

// ---------- converter ----------
const settings = { game: 'valorant', sens: 0.4, dpi: 800, dpi2: 800, fov: null, mode: 'gridshot', ...store.get('settings', {}) };
// Shareable links: ?game=cs2&sens=1.2&dpi=400
const qs = new URLSearchParams(location.search);
if (GAMES[qs.get('game')]) settings.game = qs.get('game');
if (Number(qs.get('sens')) > 0) settings.sens = Number(qs.get('sens'));
if (Number(qs.get('dpi')) > 0) settings.dpi = settings.dpi2 = Number(qs.get('dpi'));

$('game').innerHTML = Object.entries(GAMES).map(([id, g]) => `<option value="${id}">${g.name}${g.approx ? ' ≈' : ''}</option>`).join('');
$('mode').innerHTML = Object.entries(MODES).map(([id, m]) => `<option value="${id}">${m.label}</option>`).join('');
$('game').value = settings.game; $('sens').value = settings.sens; $('dpi').value = settings.dpi; $('dpi2').value = settings.dpi2;
$('mode').value = settings.mode;
$('fov').value = settings.fov ?? GAMES[settings.game].fov;

function readSettings() {
  const prevGame = settings.game;
  settings.game = $('game').value;
  settings.sens = Number($('sens').value);
  settings.dpi = Number($('dpi').value);
  settings.dpi2 = Number($('dpi2').value);
  settings.mode = $('mode').value;
  if (prevGame !== settings.game) $('fov').value = GAMES[settings.game].fov;
  settings.fov = Number($('fov').value) || GAMES[settings.game].fov;
  store.set('settings', settings);
}

function renderConverter() {
  readSettings();
  const { game, sens, dpi, dpi2 } = settings;
  const tbody = $('table').querySelector('tbody');
  if (!(sens > 0 && dpi > 0 && dpi2 > 0)) {
    ['cm360', 'in360', 'edpi', 'feel'].forEach((id) => { $(id).textContent = '—'; });
    tbody.innerHTML = '';
    return;
  }
  const cm = cm360(sens, dpi, game);
  $('cm360').textContent = cm.toFixed(2);
  $('in360').textContent = inches360(sens, dpi, game).toFixed(2);
  $('edpi').textContent = Math.round(edpi(sens, dpi) * 100) / 100;
  $('feel').textContent = describeCm360(cm);
  tbody.innerHTML = conversionTable(sens, game, dpi, dpi2).filter((r) => r.id !== game).map((r) => `
    <tr><td>${r.name}${r.approx ? ' ≈' : ''}${r.note ? `<div class="muted small">${r.note}</div>` : ''}</td>
    <td><b>${r.sens}</b> <span class="muted small">@ ${dpi2} DPI</span></td>
    <td><button data-copy="${r.sens}">Copy</button></td></tr>`).join('');
  history.replaceState(null, '', `?game=${game}&sens=${sens}&dpi=${dpi}`);
}
$('table').addEventListener('click', async (e) => {
  const v = e.target.dataset?.copy;
  if (!v) return;
  try { await navigator.clipboard.writeText(v); e.target.textContent = 'Copied'; } catch { e.target.textContent = v; }
  setTimeout(() => { e.target.textContent = 'Copy'; }, 1200);
});
['game', 'sens', 'dpi', 'dpi2'].forEach((id) => $(id).addEventListener('input', renderConverter));
renderConverter();

// ---------- trainer ----------
const canvas = $('arena');
const ctx = canvas.getContext('2d');
const overlay = $('overlay');
let session = null;
let activeSens = null; // sens used by the running session (PSA overrides the converter value)
let onFinish = null;
let last = 0;

function syncTrainerLabels() {
  readSettings();
  $('using').textContent = `${GAMES[settings.game].name} · sens ${settings.sens} · ${settings.dpi} DPI · ${cm360(settings.sens, settings.dpi, settings.game).toFixed(1)} cm/360`;
  $('mode-desc').textContent = MODES[settings.mode].desc;
}
['mode', 'fov'].forEach((id) => $(id).addEventListener('input', syncTrainerLabels));

function showOverlay(html) { overlay.innerHTML = html; overlay.hidden = false; }
showOverlay('<div><h2>Aim trainer</h2><p>Uses your real sensitivity: mouse counts × yaw × sens = degrees, just like in-game.</p><p>Press <b>Start</b>, then click here.</p></div>');

function begin({ mode = settings.mode, sens = settings.sens, label = '', finish = null } = {}) {
  readSettings();
  activeSens = sens;
  onFinish = finish;
  session = null;
  showOverlay(`<div><h2>${label || MODES[mode].label}</h2><p>Sens ${roundSens(sens)} (${GAMES[settings.game].name})</p><p><b>Click to lock the mouse and start.</b> Esc to quit.</p></div>`);
  overlay.dataset.pending = mode;
  showTab('train');
}

overlay.addEventListener('click', async () => {
  const mode = overlay.dataset.pending;
  if (!mode) return;
  try { await canvas.requestPointerLock({ unadjustedMovement: true }); } // raw input where supported
  catch { try { await canvas.requestPointerLock(); } catch { /* ignore */ } }
});

document.addEventListener('pointerlockchange', () => {
  if (document.pointerLockElement === canvas && overlay.dataset.pending) {
    session = createSession(overlay.dataset.pending, { now: performance.now() });
    delete overlay.dataset.pending;
    overlay.hidden = true;
    last = performance.now();
    requestAnimationFrame(frame);
  } else if (!document.pointerLockElement && session && !session.ended) {
    session = null;
    showOverlay('<div><h2>Paused</h2><p>Session discarded. Press Start to go again.</p></div>');
  }
});

canvas.addEventListener('mousemove', (e) => {
  if (!session || document.pointerLockElement !== canvas) return;
  applyMouse(session.cam, e.movementX, e.movementY, degreesPerCount(activeSens, settings.game));
});
canvas.addEventListener('mousedown', (e) => {
  if (!session || document.pointerLockElement !== canvas || e.button !== 0) return;
  const hit = shoot(session, performance.now());
  flash = hit ? { t: performance.now(), hit: true } : { t: performance.now(), hit: false };
});
let flash = null;

function frame(now) {
  if (!session) return;
  step(session, now, now - last);
  last = now;
  draw(now);
  if (session.ended) return finish();
  requestAnimationFrame(frame);
}

function draw(now) {
  const W = canvas.width, H = canvas.height, fov = settings.fov, cam = session.cam;
  ctx.fillStyle = '#0a0c10'; ctx.fillRect(0, 0, W, H);
  // Reference grid every 15° so turns are visible.
  ctx.strokeStyle = 'rgba(255,255,255,0.07)'; ctx.lineWidth = 1;
  for (let yaw = -180; yaw < 180; yaw += 15) {
    const a = project(cam, yaw, -30, fov, W, H), b = project(cam, yaw, 30, fov, W, H);
    if (a && b) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
  }
  for (let pitch = -30; pitch <= 30; pitch += 15) {
    ctx.beginPath(); let started = false;
    for (let yaw = -180; yaw <= 180; yaw += 3) {
      const p = project(cam, yaw, pitch, fov, W, H);
      if (!p) { started = false; continue; }
      if (!started) { ctx.moveTo(p.x, p.y); started = true; } else ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
  }
  // Targets
  for (const t of session.targets) {
    const p = project(cam, t.yaw, t.pitch, fov, W, H);
    if (!p) continue;
    const r = pixelRadius(session.mode.radius, fov, W) / p.depth;
    const g = ctx.createRadialGradient(p.x - r / 3, p.y - r / 3, r / 5, p.x, p.y, r);
    g.addColorStop(0, '#ff8fa3'); g.addColorStop(1, '#ff4d6d');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.fill();
  }
  // Crosshair
  const cx = W / 2, cy = H / 2;
  ctx.strokeStyle = flash && now - flash.t < 90 ? (flash.hit ? '#4dff9a' : '#ffd24d') : '#4dd2ff';
  ctx.lineWidth = 2; ctx.beginPath();
  ctx.moveTo(cx - 10, cy); ctx.lineTo(cx - 3, cy); ctx.moveTo(cx + 3, cy); ctx.lineTo(cx + 10, cy);
  ctx.moveTo(cx, cy - 10); ctx.lineTo(cx, cy - 3); ctx.moveTo(cx, cy + 3); ctx.lineTo(cx, cy + 10); ctx.stroke();
  // HUD
  const left = Math.max(0, session.mode.duration - (now - session.startedAt) / 1000);
  const s = summary(session);
  ctx.fillStyle = '#e9ebf1'; ctx.font = '600 22px system-ui'; ctx.textAlign = 'left';
  ctx.fillText(`${left.toFixed(1)}s`, 20, 36);
  ctx.textAlign = 'right';
  ctx.fillText(session.mode.moving ? `${Math.round(s.accuracy * 100)}% on target` : `${s.hits} hits · ${Math.round(s.accuracy * 100)}%`, W - 20, 36);
}

function finish() {
  document.exitPointerLock?.();
  const s = summary(session);
  const rec = { ...s, sens: roundSens(activeSens), game: settings.game, at: Date.now() };
  const hist = store.get('history', []);
  hist.push(rec);
  store.set('history', hist.slice(-200));
  renderHistory();
  const done = onFinish;
  session = null;
  onFinish = null;
  const detail = s.hits == null ? `${Math.round(s.accuracy * 100)}% time on target`
    : `${s.hits} hits · ${Math.round(s.accuracy * 100)}% accuracy${s.avgReactionMs ? ` · ${Math.round(s.avgReactionMs)} ms/kill` : ''}`;
  showOverlay(`<div><h2>${MODES[s.mode].label} complete</h2><div class="big">${s.score.toLocaleString()}</div><p>${detail}</p>${done ? '<p>Head back to <b>Sens finder</b> to choose.</p>' : ''}</div>`);
  if (done) done(rec);
}

function renderHistory() {
  const hist = store.get('history', []);
  const best = {};
  for (const r of hist) {
    const key = `${r.mode}|${r.game}|${r.sens}`;
    if (!best[key] || r.score > best[key].score) best[key] = r;
  }
  const rows = Object.values(best).sort((a, b) => a.mode.localeCompare(b.mode) || b.score - a.score).slice(0, 30);
  $('history').querySelector('tbody').innerHTML = rows.length ? rows.map((r) => `<tr><td>${MODES[r.mode]?.label ?? r.mode}</td>
    <td>${r.sens} <span class="muted small">${GAMES[r.game]?.name ?? ''}</span></td><td>${r.score.toLocaleString()}</td>
    <td>${Math.round(r.accuracy * 100)}%</td><td>${r.avgReactionMs ? `${Math.round(r.avgReactionMs)} ms` : '—'}</td></tr>`).join('')
    : '<tr><td colspan="5" class="muted">No sessions yet.</td></tr>';
}
renderHistory();

$('start').addEventListener('click', () => begin());

// ---------- PSA sens finder ----------
let psa = store.get('psa', null);
function resetPsa() { readSettings(); psa = createPsa(settings.sens); store.set('psa', psa); renderPsa(); }
function renderPsa() {
  if (!psa) return resetPsa();
  const done = isDone(psa);
  const { a, b } = candidates(psa);
  $('psa-round').innerHTML = done ? '<b>Done!</b>' : `Round <b>${psa.round + 1}</b> of ${psa.rounds}: A = <b>${roundSens(a)}</b>, B = <b>${roundSens(b)}</b>`;
  ['try-a', 'try-b', 'pick-a', 'pick-b'].forEach((id) => { $(id).disabled = done; });
  $('try-a').textContent = `Try A (${roundSens(a)})`;
  $('try-b').textContent = `Try B (${roundSens(b)})`;
  if (done) {
    const r = result(psa);
    const others = Object.keys(GAMES).filter((g) => g !== settings.game).slice(0, 4)
      .map((g) => `${GAMES[g].name}: <b>${roundSens(convert(r, settings.game, g, settings.dpi))}</b>`).join('<br>');
    $('psa-result').innerHTML = `<div class="stats"><div><b>${roundSens(r)}</b><span>your ${GAMES[settings.game].name} sens · ${cm360(r, settings.dpi, settings.game).toFixed(1)} cm/360</span></div></div>
      <button class="primary" id="psa-apply">Use this sensitivity</button><p class="small">${others}</p>`;
    $('psa-apply').onclick = () => { $('sens').value = roundSens(r); renderConverter(); showTab('convert'); };
  } else {
    $('psa-result').innerHTML = '';
  }
}
$('try-a').onclick = () => begin({ mode: 'wideflick', sens: candidates(psa).a, label: 'PSA · option A', finish: () => {} });
$('try-b').onclick = () => begin({ mode: 'wideflick', sens: candidates(psa).b, label: 'PSA · option B', finish: () => {} });
$('pick-a').onclick = () => { psa = choose(psa, 'a'); store.set('psa', psa); renderPsa(); };
$('pick-b').onclick = () => { psa = choose(psa, 'b'); store.set('psa', psa); renderPsa(); };
$('psa-reset').onclick = resetPsa;
renderPsa();

syncTrainerLabels();
showTab(store.get('tab', 'convert'));
