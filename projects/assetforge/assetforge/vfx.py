"""Pixel VFX: animated effects drawn from an intensity field.

Each effect paints soft shapes (discs, rings, lines) into a float grid for every frame. The grid is
then cut into four colour bands, so the same animation can be exported in any palette and always
has clean pixel edges with a bright core and a dark rim."""
from __future__ import annotations

import math
import random

from .png import Canvas, hex_to_rgba

SIZE = 48
C = SIZE / 2
H = hex_to_rgba

PALETTES = {  # rim, body, light, core
    "fire": ("#a3283a", "#f0642e", "#ffc23d", "#fff6d0"),
    "ice": ("#264f9e", "#3fa0e8", "#8fe3f5", "#f2feff"),
    "poison": ("#1f5a2c", "#4fbf5f", "#b6f06a", "#f6ffd6"),
    "arcane": ("#4a2a80", "#9b59d0", "#e59bf5", "#fff0ff"),
    "holy": ("#b5761f", "#f2c23d", "#ffeb99", "#ffffff"),
    "shadow": ("#17131d", "#3d3550", "#7a6f96", "#d9d2ec"),
}
LEVELS = (0.22, 0.48, 0.8, 1.15)
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


class Field:
    def __init__(self, size: int = SIZE):
        self.n = size
        self.v = [[0.0] * size for _ in range(size)]

    def _box(self, cx, cy, r):
        n = self.n
        return max(0, int(cx - r - 1)), min(n, int(cx + r + 2)), max(0, int(cy - r - 1)), min(n, int(cy + r + 2))

    def disc(self, cx, cy, r, amp=1.0, soft=0.45, sx=1.0, sy=1.0):
        """Filled blob. sx/sy squash it into an ellipse."""
        if r <= 0.2 or amp <= 0:
            return
        x0, x1, y0, y1 = self._box(cx, cy, r * max(sx, sy) * (1 + soft))
        inner = 1 - soft
        for y in range(y0, y1):
            dy = (y + 0.5 - cy) / sy
            row = self.v[y]
            for x in range(x0, x1):
                dx = (x + 0.5 - cx) / sx
                d = math.sqrt(dx * dx + dy * dy) / r
                if d < inner:
                    row[x] += amp
                elif d < 1 + soft:
                    row[x] += amp * (1 - (d - inner) / (2 * soft))

    def ring(self, cx, cy, r, width, amp=1.0, sx=1.0, sy=1.0, a0=None, a1=None):
        """Ring or arc (angles in degrees, 0 = right, clockwise on screen)."""
        if r <= 0 or amp <= 0 or width <= 0:
            return
        x0, x1, y0, y1 = self._box(cx, cy, (r + width) * max(sx, sy))
        for y in range(y0, y1):
            dy = (y + 0.5 - cy) / sy
            row = self.v[y]
            for x in range(x0, x1):
                dx = (x + 0.5 - cx) / sx
                d = abs(math.sqrt(dx * dx + dy * dy) - r) / width
                if d >= 1:
                    continue
                if a0 is not None:
                    ang = math.degrees(math.atan2(dy, dx)) % 360
                    lo, hi = a0 % 360, a1 % 360
                    if not ((lo <= ang <= hi) if lo <= hi else (ang >= lo or ang <= hi)):
                        continue
                row[x] += amp * (1 - d * d)

    def line(self, xa, ya, xb, yb, width, amp=1.0):
        if width <= 0.05 or amp <= 0:
            return
        r = width
        x0, x1 = max(0, int(min(xa, xb) - r - 1)), min(self.n, int(max(xa, xb) + r + 2))
        y0, y1 = max(0, int(min(ya, yb) - r - 1)), min(self.n, int(max(ya, yb) + r + 2))
        vx, vy = xb - xa, yb - ya
        ln2 = vx * vx + vy * vy or 1e-6
        for y in range(y0, y1):
            row = self.v[y]
            for x in range(x0, x1):
                px, py = x + 0.5 - xa, y + 0.5 - ya
                t = max(0.0, min(1.0, (px * vx + py * vy) / ln2))
                d = math.hypot(px - t * vx, py - t * vy) / width
                if d < 1:
                    row[x] += amp * (1 - d * d)

    def cut(self, cx, cy, r, sx=1.0, sy=1.0):
        """Remove a disc (used to carve crescents)."""
        x0, x1, y0, y1 = self._box(cx, cy, r * max(sx, sy))
        for y in range(y0, y1):
            dy = (y + 0.5 - cy) / sy
            for x in range(x0, x1):
                dx = (x + 0.5 - cx) / sx
                if dx * dx + dy * dy < r * r:
                    self.v[y][x] = 0.0

    def to_canvas(self, palette: str, dither: bool = False) -> Canvas:
        cols = [H(c) for c in PALETTES[palette]]
        c = Canvas(self.n, self.n)
        for y in range(self.n):
            for x in range(self.n):
                v = self.v[y][x]
                if dither:
                    v += (BAYER[y % 4][x % 4] / 16 - 0.5) * 0.22
                if v < LEVELS[0]:
                    continue
                c.px[y][x] = cols[3] if v >= LEVELS[3] else cols[2] if v >= LEVELS[2] else cols[1] if v >= LEVELS[1] else cols[0]
        return c


ease = lambda t: 1 - (1 - t) ** 2
fade = lambda t, p=1.0: max(0.0, 1 - t) ** p
TAU = 2 * math.pi


def _parts(seed: str, n: int):
    r = random.Random(seed)
    return [(r.uniform(0, TAU), r.uniform(0.45, 1.0), r.uniform(0, 1), r.uniform(-1, 1)) for _ in range(n)]


# ---------- effects: fn(field, t) with t in [0, 1) ----------
def explosion(f, t):
    f.disc(C, C, 4 + 15 * ease(t), 1.7 * fade(t, 1.3), 0.5)
    f.ring(C, C, 5 + 17 * ease(t), 2.6, 1.1 * fade(t, 0.7))
    for a, s, _, _ in _parts("explosion", 11):
        d = 6 + 17 * s * ease(t)
        f.disc(C + math.cos(a) * d, C + math.sin(a) * d, 3.2 * fade(t) + 0.6, 1.1 * fade(t, 0.6), 0.5)


def explosion_small(f, t):
    f.disc(C, C, 3 + 8 * ease(t), 1.6 * fade(t, 1.2), 0.5)
    for a, s, _, _ in _parts("pop", 7):
        d = 4 + 11 * s * ease(t)
        f.disc(C + math.cos(a) * d, C + math.sin(a) * d, 2.2 * fade(t) + 0.4, 1.0 * fade(t, 0.6))


def hit_spark(f, t):
    f.disc(C, C, 5 * fade(t, 0.6), 1.6 * fade(t), 0.5)
    for k in range(6):
        a = k * TAU / 6 + 0.3
        r0, r1 = 3 + 12 * ease(t), 8 + 14 * ease(t)
        f.line(C + math.cos(a) * r0, C + math.sin(a) * r0, C + math.cos(a) * r1, C + math.sin(a) * r1, 1.6 * fade(t) + 0.5, 1.3 * fade(t, 0.5))


def hit_star(f, t):
    s = math.sin((0.14 + 0.78 * t) * math.pi)
    for a in (0, math.pi / 2):
        L = 17 * s
        f.line(C - math.cos(a) * L, C - math.sin(a) * L, C + math.cos(a) * L, C + math.sin(a) * L, 1.8 * s + 0.6, 1.5 * s)
    for a in (math.pi / 4, 3 * math.pi / 4):
        L = 9 * s
        f.line(C - math.cos(a) * L, C - math.sin(a) * L, C + math.cos(a) * L, C + math.sin(a) * L, 1.4 * s + 0.4, 1.2 * s)
    f.disc(C, C, 4 * s, 1.4 * s)


def slash(f, t):
    sweep = 150 * ease(min(1, t * 1.6))
    a0 = 205
    f.ring(C, C + 6, 17, 3.2 * fade(t, 0.8) + 0.8, 1.6 * fade(t, 0.9), a0=a0, a1=a0 + sweep)
    f.cut(C + 3, C + 12, 15.5)


def slash_cross(f, t):
    for k, (xa, ya, xb, yb) in enumerate(((8, 8, 40, 40), (40, 8, 8, 40))):
        tt = max(0.0, min(1.0, (t - k * 0.22) / 0.78))
        if tt <= 0:
            continue
        p = ease(min(1, tt * 2))
        f.line(xa, ya, xa + (xb - xa) * p, ya + (yb - ya) * p, 2.4 * fade(tt, 0.8) + 0.5, 1.6 * fade(tt, 0.7))


def slash_heavy(f, t):
    sweep = 200 * ease(min(1, t * 1.5))
    f.ring(C, C, 19, 4.5 * fade(t, 0.8) + 1, 1.7 * fade(t, 0.8), a0=250 - sweep / 2, a1=250 + sweep / 2)
    f.cut(C, C + 7, 18)
    for a, s, _, _ in _parts("heavy", 5):
        d = 18 + 5 * t
        ang = math.radians(200 + 110 * s)
        f.disc(C + math.cos(ang) * d, C + math.sin(ang) * d, 1.6 * fade(t), fade(t))


def pierce(f, t):
    p = ease(min(1, t * 2.2))
    f.line(4, C, 4 + 40 * p, C, 2.2 * fade(t, 0.8) + 0.5, 1.6 * fade(t, 0.6))
    f.disc(4 + 40 * p, C, 4.5 * fade(t, 0.7), 1.5 * fade(t))
    f.ring(4 + 40 * p, C, 3 + 9 * t, 1.6, 0.9 * fade(t), sx=0.5)


def magic_burst(f, t):
    f.ring(C, C, 3 + 17 * ease(t), 2.4, 1.4 * fade(t, 0.8))
    f.ring(C, C, 1 + 10 * ease(t), 1.6, 1.0 * fade(t, 1.2))
    f.disc(C, C, 6 * fade(t, 2), 1.6 * fade(t, 2))
    for k in range(8):
        a = k * TAU / 8 + t * 1.5
        d = 5 + 16 * ease(t)
        f.disc(C + math.cos(a) * d, C + math.sin(a) * d, 2.0 * fade(t) + 0.5, 1.3 * fade(t, 0.7))


def shockwave(f, t):
    f.ring(C, C + 10, 4 + 18 * ease(t), 2.6 * fade(t, 0.6) + 0.6, 1.5 * fade(t, 0.8), sy=0.38)
    f.ring(C, C + 10, 2 + 11 * ease(t), 1.6, 0.9 * fade(t, 1.4), sy=0.38)
    f.disc(C, C + 8, 7 * fade(t, 2.5), 1.5 * fade(t, 2), sy=0.6)


def nova(f, t):
    s = math.sin(min(1, (0.07 + 0.9 * t) * 1.0) * math.pi) ** 0.8
    for k in range(8):
        a = k * TAU / 8
        L = (21 if k % 2 == 0 else 13) * s
        f.line(C, C, C + math.cos(a) * L, C + math.sin(a) * L, 1.7 * s + 0.4, 1.2 * s)
    f.disc(C, C, 6.5 * s, 1.5 * s)
    f.ring(C, C, 20 * ease(t), 1.4, 0.8 * fade(t))


def smoke_puff(f, t):
    for a, s, ph, dr in _parts("smoke", 8):
        x = C + math.cos(a) * (3 + 15 * s * ease(t)) + dr * 5 * t
        y = C + 8 + math.sin(a) * 7 * s - 16 * t * (0.4 + ph * 0.7)
        f.disc(x, y, (3.2 + 3 * ph) * (0.8 + 0.5 * ease(t)) * fade(t, 0.5) + 0.5, 0.75 * fade(t, 0.8), 0.45)


def dust_land(f, t):
    for side in (-1, 1):
        for k in range(4):
            x = C + side * (3 + (5 + k * 4.5) * ease(t))
            y = C + 15 - (3 + k * 2.2) * math.sin(t * math.pi) - k * 0.8
            f.disc(x, y, (6 - k * 0.9) * fade(t, 0.6) + 0.5, 0.7 * fade(t, 0.6), 0.5)


def flame_loop(f, t):
    for k in range(7):
        ph = (t + k / 7) % 1
        sway = math.sin((t * TAU) + k * 1.7) * (1.5 + 2.5 * ph)
        f.disc(C + sway, C + 15 - 27 * ph, 7.5 * (1 - ph) ** 0.8 + 0.6, 1.25 * (1 - ph * 0.55), 0.55)
    f.disc(C, C + 14, 7, 1.0, 0.5, sy=0.7)


def fire_pillar(f, t):
    grow = ease(min(1, t * 2.5)) * fade(max(0, (t - 0.7) / 0.3), 1)
    for k in range(9):
        ph = (t * 2.2 + k / 9) % 1
        sway = math.sin(t * TAU * 2 + k * 2.1) * 2.2
        f.disc(C + sway, C + 20 - 40 * ph * grow, (6.5 - 3.5 * ph) * grow + 0.4, 1.3 * grow * (1 - ph * 0.4), 0.5)
    f.ring(C, C + 19, 6 + 9 * ease(t), 1.8, 1.0 * fade(t, 0.6), sy=0.35)


def sparkle_loop(f, t):
    for a, s, ph, dr in _parts("sparkle", 7):
        tt = (t + ph) % 1
        b = math.sin(tt * math.pi) ** 2
        x, y = C + math.cos(a) * 16 * s, C + math.sin(a) * 16 * s
        L = 4.5 * b
        f.line(x - L, y, x + L, y, 0.9 + 0.5 * b, 1.4 * b)
        f.line(x, y - L, x, y + L, 0.9 + 0.5 * b, 1.4 * b)


def twinkle(f, t):
    s = math.sin((0.12 + 0.8 * t) * math.pi)
    L = 15 * s
    f.line(C - L, C, C + L, C, 1.2 + s, 1.5 * s)
    f.line(C, C - L, C, C + L, 1.2 + s, 1.5 * s)
    f.disc(C, C, 3.5 * s, 1.4 * s)
    f.ring(C, C, 6 + 10 * t, 1.2, 0.7 * fade(t))


def heal(f, t):
    for a, s, ph, dr in _parts("heal", 6):
        tt = (t * 1.0 + ph * 0.35)
        if tt > 1:
            continue
        x = C + dr * 13
        y = C + 16 - 30 * ease(tt)
        b = math.sin(tt * math.pi)
        L = 3.4 * b * (0.7 + 0.5 * s)
        f.line(x - L, y, x + L, y, 1.3, 1.4 * b)
        f.line(x, y - L, x, y + L, 1.3, 1.4 * b)
    f.ring(C, C + 16, 5 + 10 * ease(t), 1.6, 0.9 * fade(t), sy=0.35)


def buff_up(f, t):
    for k in range(4):
        ph = (t + k / 4) % 1
        x = C + (k - 1.5) * 9
        y = C + 17 - 32 * ph
        b = math.sin(ph * math.pi)
        f.line(x, y + 5, x, y - 2, 1.3, 1.3 * b)
        f.line(x - 3.5, y + 1.5, x, y - 3, 1.2, 1.3 * b)
        f.line(x + 3.5, y + 1.5, x, y - 3, 1.2, 1.3 * b)


def debuff_down(f, t):
    for k in range(4):
        ph = (t + k / 4) % 1
        x = C + (k - 1.5) * 9
        y = C - 15 + 32 * ph
        b = math.sin(ph * math.pi)
        f.line(x, y - 5, x, y + 2, 1.3, 1.3 * b)
        f.line(x - 3.5, y - 1.5, x, y + 3, 1.2, 1.3 * b)
        f.line(x + 3.5, y - 1.5, x, y + 3, 1.2, 1.3 * b)


def lightning(f, t):
    r = random.Random("bolt" + str(int(t * 3)))
    b = 1.0 if t < 0.5 else fade((t - 0.5) / 0.5)
    reach = min(1.0, t * 5)
    x, y = C + r.uniform(-4, 4), 2.0
    segs = 6
    for k in range(segs):
        if k / segs > reach:
            break
        nx, ny = C + r.uniform(-9, 9) * (1 - (k + 1) / segs * 0.6), 2 + (k + 1) * 41 / segs
        f.line(x, y, nx, ny, 1.5 + 0.8 * b, 1.6 * b)
        x, y = nx, ny
    if reach >= 1:
        f.disc(x, 43, 6 * b, 1.5 * b, sy=0.6)
        f.ring(x, 43, 4 + 10 * t, 1.5, 0.9 * b, sy=0.35)


def orb_loop(f, t):
    pulse = 1 + 0.12 * math.sin(t * TAU)
    f.disc(C + 4, C, 6.5 * pulse, 1.5, 0.5)
    for k in range(5):
        ph = (t + k / 5) % 1
        f.disc(C + 2 - 20 * ph, C + math.sin(ph * 9 + k) * 2.5, 4.2 * (1 - ph) + 0.4, 0.95 * (1 - ph), 0.6)


def orb_impact(f, t):
    f.disc(C, C, 4 + 9 * ease(t), 1.6 * fade(t, 1.4))
    f.ring(C, C, 4 + 15 * ease(t), 2.2 * fade(t, 0.5) + 0.5, 1.2 * fade(t, 0.8))
    for k in range(5):
        a = math.pi + (k - 2) * 0.45
        d = 5 + 15 * ease(t)
        f.disc(C + math.cos(a) * d, C + math.sin(a) * d, 2.3 * fade(t), 1.1 * fade(t, 0.6))


def beam(f, t):
    b = math.sin(min(1, (0.07 + 0.93 * t) * 1.15) * math.pi) ** 0.6
    f.line(3, C, 45, C, 7.5 * b + 0.3, 1.7 * b)
    f.line(3, C, 45, C, 3 * b + 0.2, 1.0 * b)
    f.disc(6, C, 8.5 * b, 1.3 * b)
    for k in range(4):
        ph = (t * 2 + k / 4) % 1
        f.disc(6 + 38 * ph, C + math.sin(ph * 12 + k) * 9, 1.8 * b, 1.2 * b)


def shield(f, t):
    b = math.sin(min(1, (0.07 + 0.93 * t) * 1.1) * math.pi) ** 0.7
    f.ring(C, C, 17, 2.2, 1.35 * b)
    f.ring(C, C, 17, 3.4, 0.9 * b, a0=200 + t * 200, a1=250 + t * 200)
    f.ring(C, C, 12 + 9 * t, 1.2, 0.6 * fade(t))


def portal_loop(f, t):
    f.ring(C, C, 16, 2.6, 1.2, sx=0.72)
    f.disc(C, C, 13, 0.36, 0.3, sx=0.72)
    for k in range(3):
        a0 = (t * 360 + k * 120) % 360
        f.ring(C, C, 16, 3.4, 0.9, sx=0.72, a0=a0, a1=a0 + 50)
        a1 = (-t * 360 + k * 120 + 40) % 360
        f.ring(C, C, 9, 1.6, 0.9, sx=0.72, a0=a1, a1=a1 + 70)
    f.disc(C, C, 3 + math.sin(t * TAU) * 0.8, 1.3, sx=0.72)


def charge(f, t):
    for a, s, ph, dr in _parts("charge", 12):
        tt = (t * 1.6 + ph) % 1
        d = 21 * (1 - ease(tt)) + 2
        f.disc(C + math.cos(a + tt) * d, C + math.sin(a + tt) * d, 1.3 + 1.2 * tt, 1.2 * (0.5 + 0.5 * tt))
    f.disc(C, C, 2 + 7 * t, 0.8 + 0.9 * t, 0.5)
    f.ring(C, C, 20 * (1 - (t * 2 % 1)), 1.3, 0.8 * t)


def pickup(f, t):
    f.ring(C, C, 3 + 13 * ease(t), 2.0 * fade(t, 0.5) + 0.4, 1.3 * fade(t, 0.8))
    for k in range(6):
        a = k * TAU / 6 - math.pi / 2
        d = 5 + 14 * ease(t)
        x, y = C + math.cos(a) * d, C + math.sin(a) * d - 5 * t
        L = 2.6 * fade(t)
        f.line(x - L, y, x + L, y, 1.0, 1.3 * fade(t, 0.6))
        f.line(x, y - L, x, y + L, 1.0, 1.3 * fade(t, 0.6))


def splash(f, t):
    for a, s, ph, dr in _parts("splash", 9):
        vx, vy = dr * 15, -(17 + 14 * s)
        x = C + vx * t
        y = C + 15 + vy * t + 46 * t * t
        f.disc(x, y, 2.4 * fade(t, 0.4) + 0.4, 1.2 * fade(t, 0.5))
    f.ring(C, C + 16, 3 + 13 * ease(t), 1.6, 1.0 * fade(t), sy=0.3)
    f.disc(C, C + 13 - 9 * math.sin(t * math.pi), 3.8 * fade(t), 1.3 * fade(t), sx=0.7)


def levelup(f, t):
    b = math.sin(min(1, (0.07 + 0.93 * t) * 1.08) * math.pi) ** 0.5
    f.line(C, 46, C, 46 - 44 * ease(min(1, t * 2)), 5.5 * b + 0.3, 1.1 * b)
    f.line(C, 46, C, 46 - 44 * ease(min(1, t * 2)), 2.4 * b, 0.8 * b)
    f.ring(C, 43, 5 + 13 * ease(t), 2.0, 1.2 * fade(t, 0.7), sy=0.32)
    for a, s, ph, dr in _parts("levelup", 8):
        tt = (t * 1.3 + ph * 0.5)
        if tt < 1:
            f.disc(C + dr * 15, 44 - 40 * tt, 1.5 + s, 1.2 * math.sin(tt * math.pi))


def bubbles_loop(f, t):
    for a, s, ph, dr in _parts("bubbles", 7):
        tt = (t + ph) % 1
        x = C + dr * 14 + math.sin(tt * 7 + a) * 2
        y = C + 18 - 34 * tt
        r = 2 + 3.2 * s
        if tt < 0.85:
            f.ring(x, y, r, 1.1, 1.2 * min(1, tt * 6))
            f.disc(x - r * 0.35, y - r * 0.35, 0.9, 1.3)
        else:
            f.ring(x, y, r + (tt - 0.85) * 26, 0.9, 1.1 * fade((tt - 0.85) / 0.15))


def freeze(f, t):
    g = ease(min(1, t * 1.6))
    b = 1.0 if t < 0.75 else fade((t - 0.75) / 0.25)
    for k in range(6):
        a = k * TAU / 6 + math.pi / 6
        L = (17 if k % 2 == 0 else 12) * g
        ex, ey = C + math.cos(a) * L, C + math.sin(a) * L
        f.line(C, C, ex, ey, 2.0, 1.25 * b)
        for sgn in (-1, 1):
            bx, by = C + math.cos(a) * L * 0.6, C + math.sin(a) * L * 0.6
            f.line(bx, by, bx + math.cos(a + sgn * 0.9) * 5 * g, by + math.sin(a + sgn * 0.9) * 5 * g, 1.1, 1.1 * b)
    f.disc(C, C, 4.5 * g, 1.4 * b)


def whirl_loop(f, t):
    for k in range(7):
        y = C + 17 - k * 5.2
        w = 4 + k * 2.1
        a = (t * 360 * 2 + k * 70) % 360
        f.ring(C + math.sin(t * TAU + k * 0.6) * 1.8, y, w, 1.5, 1.15, sy=0.36, a0=a, a1=a + 200)


def muzzle(f, t):
    b = fade(t, 0.8)
    f.disc(8, C, 6 * b + 1, 1.6 * b)
    polyL = 30 * b
    f.line(8, C, 8 + polyL, C, 3.4 * b + 0.3, 1.5 * b)
    for sgn in (-1, 1):
        f.line(8, C, 8 + polyL * 0.55, C + sgn * polyL * 0.42, 2.0 * b + 0.2, 1.2 * b)


def aura_loop(f, t):
    f.ring(C, C + 15, 14, 2.0, 1.1 + 0.15 * math.sin(t * TAU), sy=0.32)
    for a, s, ph, dr in _parts("aura", 10):
        tt = (t + ph) % 1
        x = C + math.cos(a) * 13
        f.line(x, C + 15 - 26 * tt, x, C + 15 - 26 * tt - 4 * s, 1.0, 1.2 * math.sin(tt * math.pi))


def meteor(f, t):
    p = min(1.0, t / 0.55)
    x, y = 6 + 22 * p, 2 + 34 * p
    if t < 0.55:
        f.disc(x, y, 4.5, 1.6)
        for k in range(1, 6):
            f.disc(x - k * 3.2, y - k * 5, 3.6 - k * 0.5, 1.1 - k * 0.15, 0.6)
    else:
        tt = (t - 0.55) / 0.45
        f.disc(28, 38, 4 + 11 * ease(tt), 1.7 * fade(tt, 1.2), sy=0.75)
        f.ring(28, 40, 4 + 16 * ease(tt), 2.2, 1.2 * fade(tt, 0.8), sy=0.36)
        for a, s, _, dr in _parts("meteor", 7):
            f.disc(28 + dr * 17 * ease(tt), 38 - (9 + 12 * s) * math.sin(tt * math.pi), 2.2 * fade(tt), fade(tt, 0.6))


def rune_circle(f, t):
    b = math.sin(min(1, (0.07 + 0.93 * t) * 1.05) * math.pi) ** 0.5
    f.ring(C, C, 19, 1.5, 1.25 * b)
    f.ring(C, C, 13, 1.1, 1.0 * b)
    for k in range(6):
        a = k * TAU / 6 + t * 1.2
        f.line(C + math.cos(a) * 13, C + math.sin(a) * 13, C + math.cos(a + TAU / 3) * 13, C + math.sin(a + TAU / 3) * 13, 0.9, 0.95 * b)
    for k in range(8):
        a = k * TAU / 8 - t * 0.8
        f.disc(C + math.cos(a) * 16, C + math.sin(a) * 16, 1.3, 1.2 * b)
    f.disc(C, C, 3 * b, 1.3 * b)


# name: (function, frames, loops, fps, dither, matching sound)
EFFECTS: dict[str, tuple] = {
    "explosion": (explosion, 12, False, 16, False, "explosion"),
    "explosion_small": (explosion_small, 8, False, 16, False, "pop"),
    "hit_spark": (hit_spark, 6, False, 18, False, "hit"),
    "hit_star": (hit_star, 7, False, 18, False, "hit_heavy"),
    "slash": (slash, 7, False, 18, False, "slash"),
    "slash_cross": (slash_cross, 9, False, 18, False, "slash_double"),
    "slash_heavy": (slash_heavy, 8, False, 16, False, "slash_heavy"),
    "pierce": (pierce, 7, False, 18, False, "pierce"),
    "magic_burst": (magic_burst, 10, False, 16, False, "magic_burst"),
    "shockwave": (shockwave, 9, False, 16, False, "shockwave"),
    "nova": (nova, 10, False, 16, False, "nova"),
    "smoke_puff": (smoke_puff, 10, False, 12, False, "puff"),
    "dust_land": (dust_land, 8, False, 14, False, "land"),
    "flame_loop": (flame_loop, 8, True, 12, False, "fire_loop"),
    "fire_pillar": (fire_pillar, 12, False, 14, False, "fire_pillar"),
    "sparkle_loop": (sparkle_loop, 8, True, 10, False, "sparkle"),
    "twinkle": (twinkle, 7, False, 14, False, "twinkle"),
    "heal": (heal, 12, False, 14, False, "heal"),
    "buff_up": (buff_up, 8, True, 12, False, "buff"),
    "debuff_down": (debuff_down, 8, True, 12, False, "debuff"),
    "lightning": (lightning, 8, False, 16, False, "lightning"),
    "orb_loop": (orb_loop, 6, True, 12, False, "orb_cast"),
    "orb_impact": (orb_impact, 7, False, 16, False, "orb_impact"),
    "beam": (beam, 9, False, 16, False, "beam"),
    "shield": (shield, 9, False, 14, False, "shield"),
    "portal_loop": (portal_loop, 10, True, 12, False, "portal"),
    "charge": (charge, 10, False, 14, False, "charge"),
    "pickup": (pickup, 8, False, 16, False, "pickup"),
    "splash": (splash, 9, False, 16, False, "splash"),
    "levelup": (levelup, 14, False, 14, False, "levelup"),
    "bubbles_loop": (bubbles_loop, 10, True, 10, False, "bubbles"),
    "freeze": (freeze, 10, False, 14, False, "freeze"),
    "whirl_loop": (whirl_loop, 8, True, 14, False, "whirl"),
    "muzzle": (muzzle, 5, False, 20, False, "shot"),
    "aura_loop": (aura_loop, 8, True, 12, False, "aura"),
    "meteor": (meteor, 12, False, 14, False, "meteor"),
    "rune_circle": (rune_circle, 12, False, 12, False, "rune"),
}


def fields(name: str) -> list[Field]:
    fn, n, loops, _, _, _ = EFFECTS[name]
    out = []
    for i in range(n):
        f = Field()
        fn(f, i / n if loops else i / (n - 1) * 0.999 if n > 1 else 0)
        out.append(f)
    return out


def frames(name: str, palette: str, fs: list[Field] | None = None) -> list[Canvas]:
    dither = EFFECTS[name][4]
    return [f.to_canvas(palette, dither) for f in (fs or fields(name))]


def strip(frs: list[Canvas]) -> Canvas:
    c = Canvas(SIZE * len(frs), SIZE)
    for i, f in enumerate(frs):
        c.blit(f, i * SIZE, 0)
    return c
