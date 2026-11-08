import { test } from 'node:test';
import assert from 'node:assert/strict';
import { GAMES, cm360, convert, sensForCm360, conversionTable, roundSens, edpi, degreesPerCount } from '../src/sens.js';
import { createPsa, candidates, choose, isDone, result } from '../src/psa.js';
import {
  createCamera, applyMouse, project, angularDistance, wrapDeg, createSession, shoot, step, summary, pixelRadius,
} from '../src/trainer.js';

const close = (a, b, eps = 1e-6) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`);

test('known reference values', () => {
  // CS2 3.09 @ 400 DPI ≈ 33.6 cm/360 (widely cited pro setting)
  close(cm360(3.09, 400, 'cs2'), 33.63, 0.01);
  // Valorant <-> CS2 ratio = 0.07 / 0.022 ≈ 3.18
  close(convert(1, 'valorant', 'cs2'), 3.1818, 1e-4);
  // CS2 -> OW2 ratio ≈ 3.333
  close(convert(1, 'cs2', 'ow2'), 3.3333, 1e-4);
  // CS2 <-> Apex is 1:1
  close(convert(2.5, 'cs2', 'apex'), 2.5);
});

test('conversion preserves cm/360, including DPI changes', () => {
  for (const from of Object.keys(GAMES)) for (const to of Object.keys(GAMES)) {
    const s = convert(1.7, from, to, 800, 1600);
    close(cm360(1.7, 800, from), cm360(s, 1600, to), 1e-9);
  }
  close(cm360(sensForCm360(40, 800, 'valorant'), 800, 'valorant'), 40);
  assert.equal(edpi(0.4, 800), 320);
  close(degreesPerCount(2, 'cs2'), 0.044);
  assert.throws(() => cm360(0, 800, 'cs2'));
  assert.throws(() => convert(1, 'cs2', 'nope'));
});

test('rounding and table', () => {
  assert.equal(roundSens(0.314159), 0.3142);
  assert.equal(roundSens(3.18181), 3.182);
  assert.equal(roundSens(10.4567), 10.46);
  const t = conversionTable(0.4, 'valorant', 800);
  assert.equal(t.find((r) => r.id === 'cs2').sens, 1.273);
  assert.ok(t.find((r) => r.id === 'fortnite').approx);
});

test('PSA narrows toward the preferred side', () => {
  let s = createPsa(2, { rounds: 7 });
  assert.deepEqual(candidates(s), { a: 1, b: 3 });
  // A player whose ideal is 2.4 always picks the candidate closer to it.
  while (!isDone(s)) { const { a, b } = candidates(s); s = choose(s, Math.abs(a - 2.4) < Math.abs(b - 2.4) ? 'a' : 'b'); }
  assert.ok(Math.abs(result(s) - 2.4) < 0.05, `got ${result(s)}`);
  assert.throws(() => choose(s, 'a'));
});

test('camera and projection agree', () => {
  const cam = createCamera();
  // 1000 counts at 0.022*2 deg/count = 44° right
  applyMouse(cam, 1000, 0, 0.044);
  close(cam.yaw, 44);
  applyMouse(cam, 0, 100000, 0.044);
  assert.equal(cam.pitch, -89, 'pitch clamps');
  assert.equal(wrapDeg(190), -170);

  const c = { yaw: 30, pitch: 10 };
  const centre = project(c, 30, 10, 103, 1920, 1080);
  close(centre.x, 960, 1e-6); close(centre.y, 540, 1e-6);
  const right = project(c, 40, 10, 103, 1920, 1080);
  assert.ok(right.x > 960 && Math.abs(right.y - 540) < 30, 'target to the right draws right');
  const up = project(c, 30, 20, 103, 1920, 1080);
  assert.ok(up.y < 540 && Math.abs(up.x - 960) < 1e-6, 'target above draws above');
  assert.equal(project(c, 210, 10, 103, 1920, 1080), null, 'behind camera');
  // the edge of the horizontal FOV lands on the screen edge
  close(project({ yaw: 0, pitch: 0 }, 51.5, 0, 103, 1920, 1080).x, 1920, 1e-6);
  close(angularDistance(c, 30, 15), 5, 1e-9);
  assert.ok(pixelRadius(1, 103, 1920) > 10);
});

test('gridshot session: hits, misses, scoring, end', () => {
  const s = createSession('gridshot', { seed: 42, now: 0 });
  assert.equal(s.targets.length, 3);
  const t = s.targets[0];
  s.cam.yaw = t.yaw; s.cam.pitch = t.pitch;
  assert.equal(shoot(s, 400), t);
  assert.equal(s.targets.length, 3, 'respawns');
  s.cam.yaw = 170; // aim at nothing
  assert.equal(shoot(s, 500), null);
  const sum = summary(s);
  assert.equal(sum.hits, 1); assert.equal(sum.shots, 2); assert.equal(sum.accuracy, 0.5);
  assert.equal(sum.avgReactionMs, 400);
  step(s, 30000, 16);
  assert.ok(s.ended);
  assert.equal(shoot(s, 30001), null);
});

test('tracking measures time on target', () => {
  const s = createSession('tracking', { seed: 1, now: 0 });
  const t = s.targets[0];
  s.cam.yaw = t.yaw; s.cam.pitch = t.pitch;
  step(s, 10, 10); // on target this tick (target moves after check? it moves first, but only ~0.2°)
  s.cam.yaw = wrapDeg(t.yaw + 90);
  step(s, 20, 10);
  const sum = summary(s);
  close(sum.accuracy, 0.5);
});
