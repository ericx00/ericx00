// Drawing helpers: asset loading, bitmap fonts, 9-slice, sprite sheets. Logical screen is 640x360.
export const W = 640, H = 360;
export const img = {};
export const atlas = {};
export const font = {};

const loadImg = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('missing ' + src)); i.src = src; });
const loadText = (src) => fetch(src).then((r) => { if (!r.ok) throw new Error('missing ' + src); return r.text(); });

function parseFnt(txt) {
  const f = { chars: {}, line: 9, base: 7 };
  for (const ln of txt.split('\n')) {
    const kv = Object.fromEntries([...ln.matchAll(/(\w+)=(-?\d+)/g)].map((m) => [m[1], +m[2]]));
    if (ln.startsWith('common')) { f.line = kv.lineHeight; f.base = kv.base; }
    if (ln.startsWith('char ')) f.chars[kv.id] = kv;
  }
  return f;
}

export async function loadAll(list, onProgress) {
  let done = 0;
  const tick = () => onProgress && onProgress(++done / total);
  const jobs = [];
  for (const [key, src] of Object.entries(list.images)) jobs.push(loadImg(src).then((i) => { img[key] = i; tick(); }));
  for (const [key, base] of Object.entries(list.atlases)) {
    jobs.push(Promise.all([loadImg(base + '.png'), loadText(base + '.json')]).then(([i, j]) => { atlas[key] = { img: i, frames: JSON.parse(j).frames }; tick(); }));
  }
  for (const [key, base] of Object.entries(list.fonts)) {
    jobs.push(Promise.all([loadImg(base + '.png'), loadText(base + '.fnt')]).then(([i, t]) => { font[key] = { img: i, ...parseFnt(t), tint: {} }; tick(); }));
  }
  const total = jobs.length;
  await Promise.all(jobs);
}

function tinted(f, color) {
  if (!f.tint[color]) {
    const c = document.createElement('canvas'); c.width = f.img.width; c.height = f.img.height;
    const x = c.getContext('2d');
    x.drawImage(f.img, 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = color; x.fillRect(0, 0, c.width, c.height);
    f.tint[color] = c;
  }
  return f.tint[color];
}

export function textWidth(str, fk = 'sans') {
  const f = font[fk]; let w = 0;
  for (const ch of String(str)) w += (f.chars[ch.charCodeAt(0)] ?? f.chars[63]).xadvance;
  return Math.max(0, w - 1);
}

/** Draw text. opts: font, color, shadow (colour or null), align ('left' | 'center' | 'right'). */
export function text(ctx, str, x, y, { font: fk = 'sans', color = '#f1ead8', shadow = null, align = 'left' } = {}) {
  str = String(str);
  const f = font[fk];
  if (align !== 'left') x -= align === 'center' ? Math.round(textWidth(str, fk) / 2) : textWidth(str, fk);
  x = Math.round(x); y = Math.round(y);
  const pass = (im, ox, oy) => {
    let cx = x + ox;
    for (const ch of str) {
      const g = f.chars[ch.charCodeAt(0)] ?? f.chars[63];
      if (ch !== ' ') ctx.drawImage(im, g.x, g.y, g.width, g.height, cx, y + oy, g.width, g.height);
      cx += g.xadvance;
    }
  };
  if (shadow) pass(tinted(f, shadow), 1, 1);
  pass(tinted(f, color), 0, 0);
}

export function wrap(str, width, fk = 'sans') {
  const lines = []; let cur = '';
  for (const word of String(str).split(' ')) {
    const t = cur ? cur + ' ' + word : word;
    if (textWidth(t, fk) <= width || !cur) cur = t; else { lines.push(cur); cur = word; }
  }
  if (cur) lines.push(cur);
  return lines;
}

export function para(ctx, str, x, y, width, opts = {}) {
  const fk = opts.font ?? 'sans';
  const lh = opts.lineHeight ?? font[fk].line;
  const lines = wrap(str, width, fk);
  lines.forEach((ln, i) => text(ctx, ln, opts.align === 'center' ? x + width / 2 : x, y + i * lh, opts));
  return lines.length * lh;
}

/** Draw an atlas frame by name (optionally scaled). */
export function spr(ctx, key, name, x, y, scale = 1) {
  const a = atlas[key], f = a.frames[name];
  if (!f) return;
  ctx.drawImage(a.img, f.x, f.y, f.w, f.h, Math.round(x), Math.round(y), f.w * scale, f.h * scale);
}

/** 9-slice a UI atlas frame to w x h. */
export function slice(ctx, name, x, y, w, h) {
  const a = atlas.ui, f = a.frames[name];
  const [l, t, r, b] = f.nine_slice ?? [0, 0, 0, 0];
  x = Math.round(x); y = Math.round(y);
  const sx = [f.x, f.x + l, f.x + f.w - r], sw = [l, f.w - l - r, r];
  const sy = [f.y, f.y + t, f.y + f.h - b], sh = [t, f.h - t - b, b];
  const dx = [x, x + l, x + w - r], dw = [l, w - l - r, r];
  const dy = [y, y + t, y + h - b], dh = [t, h - t - b, b];
  for (let j = 0; j < 3; j++) for (let i = 0; i < 3; i++) {
    if (sw[i] > 0 && sh[j] > 0 && dw[i] > 0 && dh[j] > 0) ctx.drawImage(a.img, sx[i], sy[j], sw[i], sh[j], dx[i], dy[j], dw[i], dh[j]);
  }
}

export const ANIMS = { idle: [0, 4], move: [1, 6], attack: [2, 4], hurt: [3, 2], death: [4, 5] };
/** One frame of a 32x32 character sheet. flip mirrors horizontally; flash draws it white. */
export function sprite(ctx, key, anim, frame, x, y, scale = 3, { flip = false, alpha = 1 } = {}) {
  const [row, n] = ANIMS[anim];
  const fr = Math.min(n - 1, Math.max(0, frame));
  const s = 32 * scale;
  ctx.save();
  ctx.globalAlpha = alpha;
  if (flip) { ctx.translate(Math.round(x) + s, Math.round(y)); ctx.scale(-1, 1); ctx.drawImage(img[key], fr * 32, row * 32, 32, 32, 0, 0, s, s); }
  else ctx.drawImage(img[key], fr * 32, row * 32, 32, 32, Math.round(x), Math.round(y), s, s);
  ctx.restore();
}

export function strip(ctx, key, frame, x, y, scale = 2) {
  const im = img[key]; const n = im.width / im.height; const s = im.height;
  if (frame >= n) return false;
  ctx.drawImage(im, Math.floor(frame) * s, 0, s, s, Math.round(x - s * scale / 2), Math.round(y - s * scale / 2), s * scale, s * scale);
  return true;
}
