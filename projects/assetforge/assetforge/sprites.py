"""Procedural pixel sprites: mirrored ships and creatures, plus hand-tuned item icons and animations."""
from __future__ import annotations

import colorsys
import random

from .png import Canvas, RGBA, hex_to_rgba, shade

PALETTES: dict[str, list[str]] = {
    # Each palette: outline, then dark -> light ramps for two hues, then accent.
    "dusk": ["#1a1423", "#3d2c5e", "#6a4c93", "#a77bca", "#c13e5b", "#f0766b", "#ffd28a"],
    "lagoon": ["#0e1a24", "#16425b", "#2f6690", "#3a7ca5", "#81c3d7", "#d9dcd6", "#f4d35e"],
    "ember": ["#1c0f0a", "#5e1f12", "#a33b20", "#e06d34", "#f3a648", "#fbe29f", "#7dd6c0"],
    "moss": ["#141a12", "#2d4a2b", "#4f7942", "#8cb369", "#f4e285", "#f4a259", "#bc4b51"],
}


def palette(name: str) -> list[RGBA]:
    return [hex_to_rgba(h) for h in PALETTES[name]]


def _mirrored_mask(r: random.Random, w: int, h: int, fill: float, body_bias: float) -> list[list[bool]]:
    """Left half random, mirrored to the right. Bias fills the centre so shapes stay solid."""
    half = (w + 1) // 2
    mask = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(half):
            centre = 1 - abs(x - (half - 1)) / half
            vert = 1 - abs(y - h / 2) / (h / 2)
            p = fill * (0.4 + body_bias * centre + 0.4 * vert)
            on = r.random() < p
            mask[y][x] = on
            mask[y][w - 1 - x] = on
    return mask


def _largest_component(mask: list[list[bool]]) -> list[list[bool]]:
    h, w = len(mask), len(mask[0])
    seen = [[False] * w for _ in range(h)]
    best: list[tuple[int, int]] = []
    for sy in range(h):
        for sx in range(w):
            if not mask[sy][sx] or seen[sy][sx]:
                continue
            comp, stack = [], [(sx, sy)]
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(comp) > len(best):
                best = comp
    out = [[False] * w for _ in range(h)]
    for x, y in best:
        out[y][x] = True
    return out


def creature(seed: int, pal: str = "dusk", size: int = 14) -> Canvas:
    """A symmetric creature/ship. Only the largest connected blob is kept (no floating pixels)."""
    r = random.Random(f"creature:{seed}")
    cols = palette(pal)
    for _ in range(20):
        mask = _largest_component(_mirrored_mask(r, size - 2, size - 2, r.uniform(0.45, 0.6), 0.6))
        if sum(map(sum, mask)) >= (size - 2) ** 2 * 0.25:
            break
    body = cols[r.choice([1, 2, 4])]
    c = Canvas(size, size)
    for y, row in enumerate(mask):
        for x, on in enumerate(row):
            if on:
                # vertical gradient: lighter on top, darker at the bottom
                t = y / max(1, len(mask) - 1)
                c.set(x + 1, y + 1, shade(body, 1.25 - 0.5 * t))
    # eyes: a mirrored pair on an opaque row in the upper half
    opaque_rows = [y for y in range(1, size // 2 + 1) if any(c.get(x, y)[3] for x in range(size))]
    if opaque_rows:
        ey = r.choice(opaque_rows)
        xs = [x for x in range(1, size // 2) if c.get(x, ey)[3]]
        if xs:
            ex = r.choice(xs)
            eye = cols[6]
            c.set(ex, ey, eye)
            c.set(size - 1 - ex, ey, eye)
    c.outline(cols[0])
    return c


def coin_frames(pal: str = "ember", size: int = 12) -> list[Canvas]:
    """A spinning coin: 6 frames, width shrinks/grows like a 3D rotation."""
    cols = palette(pal)
    gold, light, dark = cols[4], cols[5], cols[2]
    frames = []
    for wscale in (1.0, 0.75, 0.4, 0.15, 0.4, 0.75):
        c = Canvas(size, size)
        cx, cy, rad = size / 2, size / 2, size / 2 - 1
        for y in range(size):
            for x in range(size):
                dx = (x + 0.5 - cx) / max(wscale, 0.12)
                dy = y + 0.5 - cy
                d2 = dx * dx + dy * dy
                if d2 <= rad * rad:
                    edge = d2 > (rad - 1.6) ** 2
                    c.set(x, y, dark if edge else (light if dx < -rad / 4 and dy < 0 else gold))
        c.outline(cols[0])
        frames.append(c)
    return frames


def heart(full: float = 1.0, pal: str = "dusk") -> Canvas:
    rows = ["..XX.XX..", ".XXXXXXX.", "XXXXXXXXX", "XXXXXXXXX", ".XXXXXXX.", "..XXXXX..", "...XXX...", "....X...."]
    cols = palette(pal)
    red, hi, empty = cols[4], cols[5], shade(cols[1], 0.9)
    c = Canvas(11, 10)
    cutoff = 1 + int(round(9 * full))  # columns lit from the left
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "X":
                lit = x + 1 < cutoff
                col = (hi if (y == 1 and x in (2, 3)) else red) if lit else empty
                c.set(x + 1, y + 1, col)
    c.outline(cols[0])
    return c


def potion(seed: int, pal: str = "lagoon") -> Canvas:
    r = random.Random(f"potion:{seed}")
    cols = palette(pal)
    liquid = hex_to_rgba("#%02x%02x%02x" % tuple(int(v * 255) for v in colorsys.hsv_to_rgb(r.random(), 0.7, 0.9)))
    glass = cols[5]
    c = Canvas(12, 14)
    c.fill_rect(5, 1, 2, 1, cols[3])        # cork
    c.fill_rect(5, 2, 2, 3, glass)           # neck
    c.disc(6, 9, 4.5, glass)                 # bulb
    level = r.uniform(7, 9)
    for y in range(c.h):
        for x in range(c.w):
            if c.get(x, y)[3] and y >= level and y > 4:
                c.set(x, y, shade(liquid, 1.2 if x < 5 else 1.0))
    c.set(4, 7, (255, 255, 255, 255))        # glint
    c.outline(cols[0])
    return c


def sheet(sprites: list[Canvas], cols: int, pad: int = 1) -> Canvas:
    cw = max(s.w for s in sprites) + pad
    ch = max(s.h for s in sprites) + pad
    rows = (len(sprites) + cols - 1) // cols
    out = Canvas(cols * cw + pad, rows * ch + pad)
    for i, s in enumerate(sprites):
        out.blit(s, pad + (i % cols) * cw, pad + (i // cols) * ch)
    return out
