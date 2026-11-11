// Sound: Web Audio with decoded OGG buffers, two variations per sound, one looping music track.
let ctx = null, sfxGain, musGain;
const buffers = {};
let current = null, wanted = null;
export const settings = { sfx: true, music: true };

function ensure() {
  if (ctx) return true;
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return false;
  ctx = new AC();
  sfxGain = ctx.createGain(); sfxGain.gain.value = 0.9; sfxGain.connect(ctx.destination);
  musGain = ctx.createGain(); musGain.gain.value = 0.32; musGain.connect(ctx.destination);
  return true;
}

async function load(key, url) {
  try {
    const data = await (await fetch(url)).arrayBuffer();
    buffers[key] = await new Promise((res, rej) => ctx.decodeAudioData(data, res, rej));
  } catch { /* a missing sound must never break the game */ }
}

/** Call from the first click/tap (browsers block audio before that). */
export async function unlock(sfxNames, musicNames) {
  if (!ensure()) return;
  if (ctx.state === 'suspended') ctx.resume();
  if (unlock.done) return;
  unlock.done = true;
  await Promise.all([
    ...sfxNames.flatMap((n) => [1, 2].map((v) => load(`${n}_${v}`, `assets/sfx/${n}_0${v}.ogg`))),
  ]);
  for (const m of musicNames) load('m:' + m, `assets/music/${m}.ogg`).then(() => { if (wanted === m) music(m, true); });
}

export function play(name, { vol = 1, rate = 1 } = {}) {
  if (!ctx || !settings.sfx) return;
  const b = buffers[`${name}_${1 + Math.floor(Math.random() * 2)}`] ?? buffers[`${name}_1`];
  if (!b) return;
  const s = ctx.createBufferSource(); s.buffer = b; s.playbackRate.value = rate * (0.97 + Math.random() * 0.06);
  const g = ctx.createGain(); g.gain.value = vol;
  s.connect(g); g.connect(sfxGain); s.start();
}

export function music(name, force = false) {
  wanted = name;
  if (!ctx) return;
  if (!settings.music || !name) { if (current) { current.src.stop(); current = null; } return; }
  if (current && current.name === name && !force) return;
  const b = buffers['m:' + name];
  if (!b) return;
  if (current) { try { current.src.stop(); } catch { /* already stopped */ } }
  const src = ctx.createBufferSource(); src.buffer = b; src.loop = true; src.connect(musGain); src.start();
  current = { name, src };
}

export function refresh() { music(wanted, true); }
