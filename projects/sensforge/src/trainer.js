// Aim-trainer core: a yaw/pitch camera, perspective projection and angular hit tests.
// Because mouse counts are turned into degrees with your game's yaw x sensitivity,
// a flick here takes the same hand movement as the same flick in-game.

const D2R = Math.PI / 180;
export const wrapDeg = (a) => ((((a + 180) % 360) + 360) % 360) - 180;

export function createCamera() {
  return { yaw: 0, pitch: 0 };
}

/** Apply raw mouse counts. dx > 0 turns right, dy > 0 looks down (like games). */
export function applyMouse(cam, dx, dy, degPerCount) {
  cam.yaw = wrapDeg(cam.yaw + dx * degPerCount);
  cam.pitch = Math.max(-89, Math.min(89, cam.pitch - dy * degPerCount));
  return cam;
}

export function dirFromAngles(yawDeg, pitchDeg) {
  const y = yawDeg * D2R;
  const p = pitchDeg * D2R;
  return [Math.cos(p) * Math.sin(y), Math.sin(p), Math.cos(p) * Math.cos(y)];
}

/** Angle in degrees between the crosshair and a world direction (yaw, pitch). */
export function angularDistance(cam, yaw, pitch) {
  const a = dirFromAngles(cam.yaw, cam.pitch);
  const b = dirFromAngles(yaw, pitch);
  const dot = Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]));
  return Math.acos(dot) / D2R;
}

/** Project a world direction to screen pixels. Returns null if behind the camera. hfov is horizontal FOV in degrees. */
export function project(cam, yaw, pitch, hfov, width, height) {
  let [x, y, z] = dirFromAngles(yaw, pitch);
  // rotate by -camera yaw around Y
  const cy = Math.cos(-cam.yaw * D2R), sy = Math.sin(-cam.yaw * D2R);
  [x, z] = [x * cy + z * sy, -x * sy + z * cy];
  // rotate around X so the camera's pitch maps to the screen centre
  const cp = Math.cos(cam.pitch * D2R), sp = Math.sin(cam.pitch * D2R);
  [y, z] = [y * cp - z * sp, y * sp + z * cp];
  if (z <= 1e-6) return null;
  const f = width / 2 / Math.tan((hfov * D2R) / 2);
  return { x: width / 2 + (x / z) * f, y: height / 2 - (y / z) * f, depth: z };
}

/** Pixel radius of a target with angular radius `angDeg` at the centre of the screen. */
export function pixelRadius(angDeg, hfov, width) {
  const f = width / 2 / Math.tan((hfov * D2R) / 2);
  return Math.tan(angDeg * D2R) * f;
}

/** Deterministic PRNG so sessions are reproducible in tests. */
export function rng(seed = Date.now()) {
  let s = seed >>> 0 || 1;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32);
}

export const MODES = {
  gridshot: { label: 'Gridshot', duration: 30, targets: 3, radius: 2, spread: [-16, 16, -8, 10], desc: 'Three targets at once. Speed + accuracy.' },
  microflick: { label: 'Micro-flick', duration: 30, targets: 1, radius: 0.8, spread: [-6, 6, -4, 4], desc: 'Small targets near the crosshair. Precision.' },
  wideflick: { label: 'Wide flick', duration: 30, targets: 1, radius: 1.4, spread: [-60, 60, -12, 12], desc: 'Large flicks. Tests your cm/360.' },
  tracking: { label: 'Tracking', duration: 30, targets: 1, radius: 1.5, spread: [-25, 25, -5, 8], moving: true, desc: 'Keep the crosshair on a strafing target.' },
};

/** Session state machine; the UI only feeds it mouse/clicks/time and draws it. */
export function createSession(modeKey, { seed, now = 0 } = {}) {
  const mode = MODES[modeKey];
  if (!mode) throw new Error(`Unknown mode ${modeKey}`);
  const s = {
    modeKey, mode, rand: rng(seed), cam: createCamera(), targets: [], startedAt: now, lastHitAt: now,
    shots: 0, hits: 0, reactions: [], onTargetMs: 0, totalMs: 0, ended: false, nextId: 1,
  };
  for (let i = 0; i < mode.targets; i++) spawn(s, now);
  return s;
}

function spawn(s, now) {
  const [y0, y1, p0, p1] = s.mode.spread;
  for (let attempt = 0; attempt < 30; attempt++) {
    const yaw = y0 + s.rand() * (y1 - y0);
    const pitch = p0 + s.rand() * (p1 - p0);
    const clear = s.targets.every((t) => Math.hypot(wrapDeg(t.yaw - yaw), t.pitch - pitch) > s.mode.radius * 3)
      && angularDistance(s.cam, yaw, pitch) > s.mode.radius * 2;
    if (clear || attempt === 29) {
      const t = { id: s.nextId++, yaw, pitch, bornAt: now, vel: s.mode.moving ? (s.rand() < 0.5 ? -1 : 1) * (12 + s.rand() * 10) : 0 };
      s.targets.push(t);
      return t;
    }
  }
  return null;
}

/** Advance time (ms). Moves tracking targets, accumulates time-on-target, ends the session. */
export function step(s, now, dtMs) {
  if (s.ended) return s;
  const [y0, y1] = s.mode.spread;
  for (const t of s.targets) {
    if (!t.vel) continue;
    t.yaw += (t.vel * dtMs) / 1000;
    if (t.yaw < y0 || t.yaw > y1) { t.vel = -t.vel; t.yaw = Math.max(y0, Math.min(y1, t.yaw)); }
    if (s.rand() < dtMs / 1500) t.vel = -t.vel; // random strafe changes
  }
  if (s.mode.moving) {
    s.totalMs += dtMs;
    if (s.targets.some((t) => angularDistance(s.cam, t.yaw, t.pitch) <= s.mode.radius)) s.onTargetMs += dtMs;
  }
  if (now - s.startedAt >= s.mode.duration * 1000) s.ended = true;
  return s;
}

/** Fire at the crosshair. Returns the hit target or null. */
export function shoot(s, now) {
  if (s.ended || s.mode.moving) return null;
  s.shots++;
  const hit = s.targets.find((t) => angularDistance(s.cam, t.yaw, t.pitch) <= s.mode.radius);
  if (!hit) return null;
  s.hits++;
  s.reactions.push(now - Math.max(hit.bornAt, s.lastHitAt));
  s.lastHitAt = now;
  s.targets = s.targets.filter((t) => t !== hit);
  spawn(s, now);
  return hit;
}

export function summary(s) {
  if (s.mode.moving) {
    const pct = s.totalMs ? s.onTargetMs / s.totalMs : 0;
    return { mode: s.modeKey, accuracy: pct, score: Math.round(pct * 10000), hits: null, shots: null, avgReactionMs: null };
  }
  const accuracy = s.shots ? s.hits / s.shots : 0;
  const avg = s.reactions.length ? s.reactions.reduce((a, b) => a + b, 0) / s.reactions.length : null;
  // Kills dominate; accuracy scales them so spraying clicks doesn't pay.
  const score = Math.round(s.hits * 100 * (0.5 + 0.5 * accuracy ** 2));
  return { mode: s.modeKey, accuracy, score, hits: s.hits, shots: s.shots, avgReactionMs: avg };
}
