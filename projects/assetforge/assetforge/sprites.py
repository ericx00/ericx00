"""Procedural pixel sprites: mirrored ships and creatures, plus hand-tuned item icons and animations."""
from __future__ import annotations

import colorsys
import math
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


# =====================================================================================
# v0.2: animated creatures, item sets, effects, tileset, scene mock-up
# =====================================================================================
from . import icons as _ic  # noqa: E402
from .draw import line, polygon, ring  # noqa: E402
from .png import CLEAR  # noqa: E402

OUTLINE = hex_to_rgba("#1a1423")


def recolor(c: Canvas, mapping: dict[RGBA, RGBA]) -> Canvas:
    out = Canvas(c.w, c.h)
    for y in range(c.h):
        out.px[y] = [mapping.get(p, p) for p in c.px[y]]
    return out


def shift(c: Canvas, dx: int, dy: int) -> Canvas:
    out = Canvas(c.w, c.h)
    out.blit(c, dx, dy)
    return out


def hurt_frame(c: Canvas) -> Canvas:
    """White flash used when a creature takes damage (outline kept)."""
    out = Canvas(c.w, c.h)
    for y in range(c.h):
        out.px[y] = [p if (not p[3] or p == OUTLINE) else (255, 255, 255, 255) for p in c.px[y]]
    return out


def creature_anim(seed: int, pal: str) -> dict[str, list[Canvas]]:
    """idle (2 frames: rest + 1px squash-bob) and hurt (1 frame), 16x16."""
    base = Canvas(16, 16)
    base.blit(creature(seed, pal, 14), 1, 1)
    bob = Canvas(16, 16)
    # squash: drop the top half by 1px, keep the feet planted
    top_rows = base.px[:8]
    for y in range(16):
        bob.px[y] = base.px[y][:] if y >= 8 else (top_rows[y - 1][:] if y >= 1 else [CLEAR] * 16)
    return {"idle": [base, bob], "hurt": [hurt_frame(base)]}


RAMPS = {
    "steel": (_ic.SILV_L, _ic.SILV, _ic.SILV_D), "wood": (_ic.BROWN_L, _ic.BROWN, _ic.BROWN_D),
    "gold": (_ic.GOLD_L, _ic.GOLD, _ic.GOLD_D), "crystal": (hex_to_rgba("#d6fbff"), hex_to_rgba("#6fe3f2"), hex_to_rgba("#2a8fb0")),
    "ruby": (_ic.RED_L, _ic.RED, _ic.RED_D), "emerald": (_ic.GREEN_L, _ic.GREEN, _ic.GREEN_D),
    "sapphire": (_ic.BLUE_L, _ic.BLUE, _ic.BLUE_D), "amethyst": (_ic.PURP_L, _ic.PURP, hex_to_rgba("#5e2d8a")),
    "copper": (hex_to_rgba("#f2b48a"), hex_to_rgba("#c46a3b"), hex_to_rgba("#7a3a1e")),
    "silver": (_ic.SILV_L, _ic.SILV, _ic.SILV_D), "diamond": (hex_to_rgba("#ffffff"), hex_to_rgba("#dfe9f5"), hex_to_rgba("#9fb3cc")),
}


def _swap(c: Canvas, src: str, dst: str) -> Canvas:
    return recolor(c, dict(zip(RAMPS[src], RAMPS[dst])))


def _item_canvas() -> Canvas:
    return Canvas(16, 16)


def chest(open_: bool = False) -> Canvas:
    c = _item_canvas()
    wood, wood_l, wood_d, gold = _ic.BROWN, _ic.BROWN_L, _ic.BROWN_D, _ic.GOLD
    c.fill_rect(1, 7, 14, 8, wood); c.fill_rect(1, 7, 14, 1, wood_l); c.fill_rect(1, 14, 14, 1, wood_d)
    if open_:
        c.fill_rect(2, 3, 12, 3, wood_d); c.fill_rect(2, 6, 12, 1, hex_to_rgba("#2a1a10"))
        c.fill_rect(5, 5, 6, 2, _ic.GOLD_L)
    else:
        c.fill_rect(1, 3, 14, 4, wood); c.fill_rect(1, 3, 14, 1, wood_l)
    for x in (3, 12):
        c.fill_rect(x, 3 if not open_ else 7, 1, 12 - (0 if not open_ else 4), gold)
    c.fill_rect(7, 7, 2, 3, gold)
    c.outline(OUTLINE)
    return c


def scroll() -> Canvas:
    c = _item_canvas()
    c.fill_rect(3, 3, 10, 10, _ic.PAPER)
    for y in (3, 12):
        c.fill_rect(2, y, 12, 2, _ic.PAPER_D)
    for y in (6, 8, 10):
        c.fill_rect(5, y, 6, 1, _ic.BROWN)
    c.outline(OUTLINE)
    return c


def ring_item(material: str = "gold", gem_col: RGBA | None = None) -> Canvas:
    c = _item_canvas()
    l, m, d = RAMPS[material]
    ring(c, 8, 10, 5, 3, m); ring(c, 8, 10, 5, 4.2, d, 180, 360); c.set(5, 7, l)
    gc = gem_col or _ic.RED
    c.disc(8, 4.5, 2.6, gc); c.set(7, 3, (255, 255, 255, 255))
    c.outline(OUTLINE)
    return c


def apple() -> Canvas:
    c = _item_canvas()
    c.disc(6, 9, 4.5, _ic.RED); c.disc(10, 9, 4.5, _ic.RED); c.fill_rect(5, 6, 2, 2, _ic.RED_L)
    c.fill_rect(8, 2, 1, 4, _ic.BROWN); polygon(c, [(9, 3), (13, 2), (11, 5)], _ic.GREEN)
    c.outline(OUTLINE)
    return c


def meat() -> Canvas:
    c = _item_canvas()
    c.disc(7, 8, 5.5, hex_to_rgba("#b5523b")); c.disc(6, 7, 3, hex_to_rgba("#d97a5c"))
    line(c, 11, 11, 14, 14, _ic.SILV_L, 2); c.disc(14, 14, 1.6, _ic.SILV_L)
    c.outline(OUTLINE)
    return c


def bread() -> Canvas:
    c = _item_canvas()
    c.disc(8, 9, 6, hex_to_rgba("#c98a3e")); c.fill_rect(2, 9, 13, 5, hex_to_rgba("#c98a3e"))
    for x in (5, 8, 11):
        line(c, x, 6, x - 1, 9, hex_to_rgba("#f2c27a"))
    c.outline(OUTLINE)
    return c


def bomb() -> Canvas:
    c = _item_canvas()
    c.disc(7, 10, 5.5, hex_to_rgba("#2c2f3a")); c.fill_rect(4, 7, 2, 2, hex_to_rgba("#5a6070"))
    c.fill_rect(9, 3, 3, 3, _ic.SILV_D); line(c, 11, 3, 13, 1, _ic.BROWN_L)
    c.set(14, 1, _ic.GOLD_L); c.set(13, 0, _ic.GOLD)
    c.outline(OUTLINE)
    return c


def items() -> dict[str, Canvas]:
    out: dict[str, Canvas] = {}
    sword = _ic.sword()
    for m in ("steel", "wood", "gold", "crystal", "ruby"):
        out[f"sword_{m}"] = sword if m == "steel" else _swap(sword, "steel", m)
    sh = _ic.shield()
    for m in ("sapphire", "ruby", "emerald", "amethyst"):
        out[f"shield_{m}"] = sh if m == "sapphire" else _swap(sh, "sapphire", m)
    gem = _ic.gem()
    for m in ("sapphire", "ruby", "emerald", "amethyst", "gold", "diamond"):
        out[f"gem_{m}"] = gem if m == "sapphire" else _swap(gem, "sapphire", m)
    pot = _ic.potion(_ic.RED, _ic.RED_L)
    for m in ("ruby", "sapphire", "emerald", "amethyst", "gold", "diamond"):
        out[f"potion_{m}"] = pot if m == "ruby" else recolor(pot, {_ic.RED: RAMPS[m][1], _ic.RED_L: RAMPS[m][0]})
    key = _ic.key()
    for m in ("gold", "silver", "copper", "crystal"):
        out[f"key_{m}"] = key if m == "gold" else _swap(key, "gold", m)
    cn = _ic.coin()
    for m in ("gold", "silver", "copper"):
        out[f"coin_{m}"] = cn if m == "gold" else _swap(cn, "gold", m)
    for m, g in (("gold", _ic.RED), ("silver", _ic.BLUE), ("gold", _ic.GREEN)):
        out[f"ring_{m}_{'ruby' if g == _ic.RED else 'sapphire' if g == _ic.BLUE else 'emerald'}"] = ring_item(m, g)
    out.update({"chest_closed": chest(False), "chest_open": chest(True), "scroll": scroll(), "apple": apple(), "meat": meat(),
                "bread": bread(), "bomb": bomb(), "heart": _ic.heart(True), "heart_empty": _ic.heart(False), "star": _ic.star(),
                "trophy": _ic.trophy(), "bag": _ic.bag(), "map": _ic.map_(), "skull": _ic.skull(), "flag": _ic.flag()})
    return out


# ---------------- effects (animated) ----------------
WHITE = (255, 255, 255, 255)
YEL, ORA, RED, SMOKE, SMOKE_D = (hex_to_rgba(h) for h in ("#ffe66b", "#ff9b3d", "#e0484f", "#9aa0ab", "#6b7180"))


def _blob(c: Canvas, cx: float, cy: float, r: float, col: RGBA, rng: random.Random, lumps: int = 6) -> None:
    c.disc(cx, cy, r, col)
    for _ in range(lumps):
        a = rng.random() * 6.283
        import math
        c.disc(cx + math.cos(a) * r * 0.7, cy + math.sin(a) * r * 0.7, r * rng.uniform(0.35, 0.55), col)


def _holes(c: Canvas, rng: random.Random, amount: float) -> None:
    for y in range(c.h):
        for x in range(c.w):
            if c.px[y][x][3] and rng.random() < amount:
                c.px[y][x] = CLEAR


def explosion(seed: int = 1) -> list[Canvas]:
    frames = []
    radii = [3, 7, 10, 12, 13, 13, 12]
    for i, r in enumerate(radii):
        rng = random.Random(f"boom:{seed}")  # same lump layout every frame = coherent motion
        c = Canvas(32, 32)
        if i <= 1:
            _blob(c, 16, 16, r, YEL if i else WHITE, rng)
            if i == 1:
                c.disc(16, 16, r * 0.5, WHITE)
        elif i <= 3:
            _blob(c, 16, 16, r, RED, rng); _blob(c, 16, 16, r * 0.75, ORA, random.Random(f"b2:{seed}")); c.disc(16, 16, r * 0.4, YEL)
        else:
            _blob(c, 16, 15 - (i - 4), r, SMOKE_D, rng); _blob(c, 15, 14 - (i - 4), r * 0.7, SMOKE, random.Random(f"b3:{seed}"))
            if i == 4:
                c.disc(16, 16, 3, ORA)
            _holes(c, random.Random(f"h:{seed}:{i}"), (i - 3) * 0.18)
        if i < 6:
            c.outline(OUTLINE) if i >= 2 else None
        frames.append(c)
    return frames


def hit_spark() -> list[Canvas]:
    frames = []
    for i, (ln, w) in enumerate([(2, 2), (5, 2), (7, 1), (7, 1)]):
        c = Canvas(16, 16)
        if i < 3:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                line(c, 8, 8, 8 + dx * ln, 8 + dy * ln, YEL, w)
            for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                line(c, 8, 8, 8 + dx * (ln // 2), 8 + dy * (ln // 2), ORA, 1)
            c.fill_rect(7, 7, 2, 2, WHITE)
        else:
            for x, y in ((1, 8), (15, 8), (8, 1), (8, 15), (3, 3), (13, 13)):
                c.set(x, y, YEL)
        frames.append(c)
    return frames


def smoke_puff(seed: int = 3) -> list[Canvas]:
    frames = []
    for i, r in enumerate([2, 3.5, 5, 6, 6.5, 6.5]):
        c = Canvas(16, 16)
        rng = random.Random(f"puff:{seed}")
        _blob(c, 8, 9 - i * 0.6, r, SMOKE, rng, 4); c.disc(7, 8 - i * 0.6, r * 0.45, hex_to_rgba("#c9ced6"))
        _holes(c, random.Random(f"ph:{i}"), max(0, (i - 2) * 0.22))
        frames.append(c)
    return frames


def sparkle() -> list[Canvas]:
    frames = []
    for s in (1, 2, 4, 6, 3):
        c = Canvas(16, 16)
        line(c, 8 - s, 8, 8 + s, 8, YEL); line(c, 8, 8 - s, 8, 8 + s, YEL)
        if s >= 2:
            c.fill_rect(7, 7, 3, 3, WHITE)
        if s >= 4:
            for p in ((5, 5), (11, 5), (5, 11), (11, 11)):
                c.set(*p, YEL)
        frames.append(c)
    return frames


def magic_burst() -> list[Canvas]:
    frames = []
    purp, purp_l = _ic.PURP, _ic.PURP_L
    for i, r in enumerate([3, 6, 9, 11, 13, 14]):
        c = Canvas(32, 32)
        thick = max(1, 4 - i // 2)
        ring(c, 16, 16, r, r - thick, purp if i > 1 else purp_l)
        if i < 4:
            ring(c, 16, 16, r * 0.6, r * 0.6 - 1, purp_l)
        rng = random.Random(f"mb:{i}")
        for _ in range(6 + i * 2):
            import math
            a = rng.random() * 6.283
            d = r + rng.uniform(-2, 3)
            c.set(int(16 + math.cos(a) * d), int(16 + math.sin(a) * d), WHITE if rng.random() < 0.4 else purp_l)
        frames.append(c)
    return frames


def dust() -> list[Canvas]:
    frames = []
    for i in range(4):
        c = Canvas(16, 16)
        for side in (-1, 1):
            cx = 8 + side * (2 + i * 2)
            r = 2.6 - i * 0.5
            if r > 0.6:
                c.disc(cx, 12 - i * 0.5, r, hex_to_rgba("#d8c8a8"))
        frames.append(c)
    return frames


EFFECTS = {"explosion": (explosion, 12), "hit_spark": (hit_spark, 16), "smoke_puff": (smoke_puff, 10),
           "sparkle": (sparkle, 10), "magic_burst": (magic_burst, 12), "dust": (dust, 12)}


# ---------------- tileset (16x16) ----------------
GRASS, GRASS_L, GRASS_D = hex_to_rgba("#5fb446"), hex_to_rgba("#9be06b"), hex_to_rgba("#3b7d34")
DIRT, DIRT_L, DIRT_D = hex_to_rgba("#8a5a3a"), hex_to_rgba("#a8724a"), hex_to_rgba("#5e3a24")
STONE, STONE_L, STONE_D = hex_to_rgba("#7d8494"), hex_to_rgba("#a3aab8"), hex_to_rgba("#525868")
WATER, WATER_L = hex_to_rgba("#3a86d6"), hex_to_rgba("#8fd0ff")
T = 16


def _dirt(seed: str) -> Canvas:
    rng = random.Random(seed)
    c = Canvas(T, T, DIRT)
    for _ in range(14):
        x, y = rng.randrange(T), rng.randrange(T)
        c.set(x, y, DIRT_D if rng.random() < 0.6 else DIRT_L)
    for _ in range(2):  # pebbles
        x, y = rng.randrange(2, 13), rng.randrange(6, 13)
        c.fill_rect(x, y, 2, 1, STONE); c.set(x, y + 1, STONE_D)
    return c


def _terrain(top: bool, bottom: bool, left: bool, right: bool, seed: str) -> Canvas:
    c = _dirt(seed)
    if top:
        rng = random.Random("grass")  # same edge on every tile so tops connect seamlessly
        for x in range(T):
            depth = 3 + (1 if rng.random() < 0.45 else 0)
            c.fill_rect(x, 0, 1, depth, GRASS)
            c.set(x, depth, GRASS_D)
        c.fill_rect(0, 0, T, 1, GRASS_L)
        c.fill_rect(0, 0, T, 0, OUTLINE)
    if left:
        c.fill_rect(0, 0, 1, T, OUTLINE); c.fill_rect(1, 1 if top else 0, 1, T, DIRT_L if not top else DIRT_L)
        if top:
            c.fill_rect(1, 0, 1, 4, GRASS_L)
    if right:
        c.fill_rect(T - 1, 0, 1, T, OUTLINE); c.fill_rect(T - 2, 0, 1, T, DIRT_D)
        if top:
            c.fill_rect(T - 2, 0, 1, 4, GRASS_D)
    if bottom:
        c.fill_rect(0, T - 1, T, 1, OUTLINE); c.fill_rect(0, T - 2, T, 1, DIRT_D)
    if top:
        c.fill_rect(0 if not left else 1, 0, T - (1 if left else 0) - (1 if right else 0), 1, GRASS_L)
    if top and left:
        c.set(0, 0, CLEAR); c.set(1, 0, OUTLINE); c.set(0, 1, OUTLINE)
    if top and right:
        c.set(T - 1, 0, CLEAR); c.set(T - 2, 0, OUTLINE); c.set(T - 1, 1, OUTLINE)
    if bottom and left:
        c.set(0, T - 1, CLEAR)
    if bottom and right:
        c.set(T - 1, T - 1, CLEAR)
    return c


def _bricks(seed: str, cracked: bool = False) -> Canvas:
    rng = random.Random(seed)
    c = Canvas(T, T, STONE_D)
    for row in range(4):
        y = row * 4
        off = 0 if row % 2 == 0 else 4
        for bx in range(-8, T, 8):
            x0 = bx + off
            shadeval = rng.uniform(0.92, 1.1)
            col = shade(STONE, shadeval)
            c.fill_rect(max(0, x0), y, min(7, T - max(0, x0)) - (max(0, x0) - x0), 3, col)
            c.fill_rect(max(0, x0), y, min(7, T - max(0, x0)) - (max(0, x0) - x0), 1, STONE_L)
    if cracked:
        line(c, 4, 1, 7, 6, OUTLINE); line(c, 7, 6, 6, 10, OUTLINE); line(c, 7, 6, 11, 8, OUTLINE)
    return c


def _platform(part: str) -> Canvas:
    c = Canvas(T, T)
    wood, wl, wd = _ic.BROWN_L, hex_to_rgba("#d9a46e"), _ic.BROWN
    x0 = 1 if part == "left" else 0
    x1 = T - 1 if part == "right" else T
    c.fill_rect(x0, 0, x1 - x0, 6, wood); c.fill_rect(x0, 0, x1 - x0, 1, wl); c.fill_rect(x0, 5, x1 - x0, 1, wd)
    c.set(x0 + 3, 2, _ic.SILV_D); c.set(x1 - 4, 2, _ic.SILV_D)
    if part != "mid":
        bx = 3 if part == "left" else T - 5
        c.fill_rect(bx, 6, 2, 4, wd)
    c.outline(OUTLINE)
    return c


def _crate() -> Canvas:
    c = Canvas(T, T, _ic.BROWN_L)
    c.rect(0, 0, T, T, OUTLINE); c.rect(1, 1, T - 2, T - 2, _ic.BROWN)
    line(c, 2, 2, 13, 13, _ic.BROWN, 2)
    for y in (5, 10):
        c.fill_rect(2, y, T - 4, 1, hex_to_rgba("#d9a46e"))
    return c


def _ladder() -> Canvas:
    c = Canvas(T, T)
    for x in (3, 11):
        c.fill_rect(x, 0, 2, T, _ic.BROWN_L); c.fill_rect(x + 1, 0, 1, T, _ic.BROWN)
    for y in (2, 7, 12):
        c.fill_rect(5, y, 6, 2, _ic.BROWN_L); c.fill_rect(5, y + 1, 6, 1, _ic.BROWN)
    return c


def _spikes() -> Canvas:
    c = Canvas(T, T)
    c.fill_rect(0, 12, T, 4, STONE_D); c.fill_rect(0, 12, T, 1, STONE)
    for x0 in (0, 5, 10):  # three wide spikes, lit on the left, shaded on the right
        polygon(c, [(x0 + 0.5, 12.5), (x0 + 5.5, 12.5), (x0 + 3, 3)], _ic.SILV_D)
        polygon(c, [(x0 + 0.5, 12.5), (x0 + 3, 12.5), (x0 + 3, 3)], _ic.SILV)
        line(c, x0 + 2, 7, x0 + 2, 11, _ic.SILV_L)
    c.fill_rect(0, T - 1, T, 1, OUTLINE)
    return c


def _door(half: str) -> Canvas:
    c = Canvas(T, T)
    wood, wd = _ic.BROWN, _ic.BROWN_D
    if half == "top":
        c.disc(8, 8, 7.5, STONE_D); c.fill_rect(0, 8, T, 8, STONE_D)
        c.disc(8, 9, 6, wood); c.fill_rect(2, 9, 12, 7, wood)
        for x in (5, 8, 11):
            c.fill_rect(x, 4, 1, 12, wd)
    else:
        c.fill_rect(0, 0, T, T, STONE_D); c.fill_rect(2, 0, 12, T, wood)
        for x in (5, 8, 11):
            c.fill_rect(x, 0, 1, T, wd)
        c.fill_rect(10, 6, 2, 2, _ic.GOLD)
    c.outline(OUTLINE)
    return c


def _water(top: bool, frame: int = 0) -> Canvas:
    c = Canvas(T, T, (WATER[0], WATER[1], WATER[2], 215))
    if top:
        for x in range(T):
            if (x + frame * 3) % 8 < 4:
                c.set(x, 0, WATER_L)
            c.set(x, 1, (WATER_L[0], WATER_L[1], WATER_L[2], 160))
    rng = random.Random(f"water:{top}:{frame}")
    for _ in range(3):
        c.fill_rect(rng.randrange(1, 13), rng.randrange(4, 15), 2, 1, (WATER_L[0], WATER_L[1], WATER_L[2], 140))
    return c


def _torch(frame: int) -> Canvas:
    c = Canvas(T, T)
    c.fill_rect(7, 7, 2, 8, _ic.BROWN)
    flame = [(8, 2.5 + frame), (11, 6), (8, 8), (5, 6)] if frame == 0 else [(7, 3), (11, 6), (8, 8), (5, 6.5)]
    polygon(c, flame, ORA); c.disc(8, 6, 1.6, YEL)
    c.outline(OUTLINE)
    return c


def _decor(kind: str) -> Canvas:
    c = Canvas(T, T)
    if kind == "grass":
        for x, h in ((4, 5), (6, 7), (8, 4), (10, 6), (12, 4)):
            line(c, x, 15, x + (1 if x % 4 == 0 else -1), 15 - h, GRASS)
    elif kind.startswith("flower"):
        col = _ic.RED if kind == "flower_red" else _ic.GOLD
        line(c, 8, 15, 8, 8, GRASS_D); c.fill_rect(9, 11, 2, 1, GRASS)
        for dx, dy in ((0, -2), (2, 0), (0, 2), (-2, 0)):
            c.disc(8 + dx, 7 + dy, 1.4, col)
        c.set(8, 7, YEL)
    elif kind == "bush":
        for cx, cy, r in ((5, 11, 4), (10, 10, 5), (8, 8, 4)):
            c.disc(cx, cy, r, GRASS)
        c.fill_rect(1, 15, 14, 1, GRASS_D); c.set(6, 7, GRASS_L); c.set(10, 7, GRASS_L)
    elif kind == "mushroom":
        c.fill_rect(6, 9, 4, 7, hex_to_rgba("#efe3c8")); c.fill_rect(9, 10, 1, 6, hex_to_rgba("#cbbd9e"))
        polygon(c, [(1.5, 10), (14.5, 10), (13, 6), (10, 3.5), (6, 3.5), (3, 6)], _ic.RED)
        c.fill_rect(2, 9, 12, 1, _ic.RED_D)
        for x, y in ((5, 6), (10, 5), (8, 8)):
            c.fill_rect(x, y, 2, 1, WHITE)
    elif kind == "sign":
        c.fill_rect(7, 9, 2, 7, _ic.BROWN); c.fill_rect(2, 3, 12, 7, _ic.BROWN_L)
        for y in (5, 7):
            c.fill_rect(4, y, 8, 1, _ic.BROWN_D)
    c.outline(OUTLINE)
    return c


def tiles() -> dict[str, Canvas]:
    out: dict[str, Canvas] = {}
    names = {(True, False, True, False): "tl", (True, False, False, False): "t", (True, False, False, True): "tr",
             (False, False, True, False): "l", (False, False, False, False): "c", (False, False, False, True): "r",
             (False, True, True, False): "bl", (False, True, False, False): "b", (False, True, False, True): "br",
             (True, True, True, True): "single", (True, True, False, False): "t_thin", (True, True, True, False): "t_thin_l",
             (True, True, False, True): "t_thin_r"}
    for (tp, bt, lf, rt), n in names.items():
        out[f"ground_{n}"] = _terrain(tp, bt, lf, rt, f"dirt:{n}")
    out["ground_c_alt"] = _dirt("dirt:alt")
    for p in ("left", "mid", "right"):
        out[f"platform_{p}"] = _platform(p)
    out["bricks"] = _bricks("b1"); out["bricks_alt"] = _bricks("b2"); out["bricks_cracked"] = _bricks("b3", True)
    out["crate"] = _crate(); out["ladder"] = _ladder(); out["spikes"] = _spikes()
    out["door_top"] = _door("top"); out["door_bottom"] = _door("bottom")
    out["water_top_0"] = _water(True, 0); out["water_top_1"] = _water(True, 1); out["water"] = _water(False)
    out["torch_0"] = _torch(0); out["torch_1"] = _torch(1)
    for k in ("grass", "flower_red", "flower_yellow", "bush", "mushroom", "sign"):
        out[f"decor_{k}"] = _decor(k)
    return out


def scene(hero: bool = True) -> Canvas:
    """320x180 level mock-up assembled only from this pack's tiles, creatures, items and effects.
    hero=False leaves the hero out (for animating it on top, e.g. promo videos)."""
    W, H = 320, 180
    sky_top, sky_bot = hex_to_rgba("#5ab4f0"), hex_to_rgba("#bfe8ff")
    c = Canvas(W, H)
    for y in range(H):
        t = y / H
        col = tuple(int(sky_top[i] + (sky_bot[i] - sky_top[i]) * t) for i in range(3)) + (255,)
        c.fill_rect(0, y, W, 1, col)  # type: ignore[arg-type]
    for cx, cy in ((60, 30), (200, 22), (280, 45)):  # clouds
        for dx, r in ((-10, 7), (0, 10), (11, 7)):
            c.disc(cx + dx, cy, r, WHITE)
        c.fill_rect(cx - 17, cy, 35, 7, WHITE)
    for x in range(0, W, 3):  # distant hills
        h = 30 + int(10 * __import__("math").sin(x / 23))
        c.fill_rect(x, H - 32 - h, 3, h, hex_to_rgba("#8fd38a"))
    tl = tiles()
    gy = H - 32
    for x in range(0, 13 * T, T):
        n = "ground_tl" if x == 0 else ("ground_tr" if x == 12 * T else "ground_t")
        c.blit(tl[n], x, gy); c.blit(tl["ground_bl" if x == 0 else "ground_br" if x == 12 * T else "ground_b"], x, gy + T)
    for x in range(13 * T, 17 * T, T):  # water pool
        c.blit(tl["water_top_0"], x, gy + 4); c.blit(tl["water"], x, gy + 4 + T)
    for x in range(17 * T, W, T):
        n = "ground_tl" if x == 17 * T else "ground_t"
        c.blit(tl[n], x, gy); c.blit(tl["ground_bl" if x == 17 * T else "ground_b"], x, gy + T)
    for i, p in enumerate(("left", "mid", "mid", "right")):  # floating platform
        c.blit(tl[f"platform_{p}"], 120 + i * T, 78)
    for y in range(gy - 4 * T, gy, T):  # brick tower + door
        for x in (34 * 0 + 240, 256):
            c.blit(tl["bricks" if (y // T) % 2 else "bricks_alt"], x, y)
    c.blit(tl["bricks_cracked"], 240, gy - 4 * T)
    c.blit(tl["door_top"], 272, gy - 2 * T); c.blit(tl["door_bottom"], 272, gy - T)
    c.blit(tl["torch_0"], 288, gy - 2 * T)
    c.blit(tl["ladder"], 104, 78); c.blit(tl["ladder"], 104, 94); c.blit(tl["ladder"], 104, 110); c.blit(tl["ladder"], 104, 126)
    c.blit(tl["crate"], 40, gy - T); c.blit(tl["crate"], 56, gy - T); c.blit(tl["crate"], 48, gy - 2 * T)
    c.blit(tl["spikes"], 176, gy - T); c.blit(tl["spikes"], 192, gy - T)
    for x, k in ((8, "decor_grass"), (24, "decor_flower_red"), (88, "decor_bush"), (150, "decor_mushroom"), (300, "decor_flower_yellow"), (220, "decor_sign")):
        c.blit(tl[k], x, gy - T)
    it = items()
    c.blit(it["chest_closed"], 150, 62)
    c.blit(it["sword_gold"], 136, 62)
    for i, x in enumerate((128, 144, 160)):
        c.blit(it["coin_gold"], x, 40 + (i % 2) * 4)
    c.blit(it["potion_ruby"], 230, gy - T)
    if hero:
        c.blit(creature_anim(7, "lagoon")["idle"][0], 70, gy - T)
    foe1 = creature_anim(3, "ember")["hurt"][0]; c.blit(foe1, 210, gy - T)
    foe2 = creature_anim(11, "dusk")["idle"][0]; c.blit(foe2, 172, 62)
    c.blit(explosion()[3], 118, 30)
    c.blit(sparkle()[3], 160, 34)
    c.blit(hit_spark()[1], 202, gy - T - 2)
    c.blit(dust()[1], 70, gy - 13)
    return c


# =====================================================================================
# v0.3: biome themes (grassland, dungeon, snow) and showcase levels with the new characters
# =====================================================================================
_H = hex_to_rgba
BIOMES = {
    "grassland": dict(grass=("#5fb446", "#9be06b", "#3b7d34"), dirt=("#8a5a3a", "#a8724a", "#5e3a24"),
                      stone=("#7d8494", "#a3aab8", "#525868"), water=("#3a86d6", "#8fd0ff"), water_alpha=215,
                      sky=("#5ab4f0", "#bfe8ff"), hills="#8fd38a"),
    "dungeon": dict(grass=("#6b6f7d", "#9095a3", "#45495a"), dirt=("#3a3346", "#4c4459", "#262030"),
                    stone=("#5a5468", "#7a7390", "#3a3448"), water=("#ff6a2a", "#ffd36b"), water_alpha=255,
                    sky=("#120e1a", "#2a2236"), hills="#1e1828"),
    "snow": dict(grass=("#eef6ff", "#ffffff", "#b8cde6"), dirt=("#5a6a86", "#71829f", "#3d4a63"),
                 stone=("#8fa3bf", "#bcd0e8", "#5f7290"), water=("#8fd8ff", "#e8fbff"), water_alpha=200,
                 sky=("#6f8fc4", "#d8e8f8"), hills="#c6d8ee"),
}


def _decor_biome(kind: str) -> Canvas:
    c = Canvas(T, T)
    if kind == "chain":
        for y in range(0, 14, 3):
            ring(c, 8, y + 1.5, 1.6, 0.6, _ic.SILV_D)
        c.disc(8, 14, 2, _ic.SILV)
    elif kind == "bones":
        line(c, 3, 14, 12, 12, _H("#e8e2cf"), 2); c.disc(3, 14, 1.4, _H("#e8e2cf")); c.disc(12, 12, 1.4, _H("#e8e2cf"))
        c.disc(9, 10, 3, _H("#e8e2cf")); c.fill_rect(9, 9, 2, 2, OUTLINE)
    elif kind == "barrel":
        c.fill_rect(4, 3, 8, 12, _ic.BROWN_L); c.fill_rect(10, 3, 2, 12, _ic.BROWN)
        for y in (5, 11):
            c.fill_rect(4, y, 8, 1, _ic.SILV_D)
    elif kind == "cobweb":
        for a in range(0, 90, 18):
            x, y = 15 * math.cos(math.radians(a)), 15 * math.sin(math.radians(a))
            line(c, 0, 0, int(x), int(y), (220, 220, 230, 200))
        for r in (5, 9, 13):
            ring(c, 0, 0, r, r - 0.8, (220, 220, 230, 170), 270, 360)
        return c
    elif kind == "pine":
        for i, (w, y) in enumerate(((3, 2), (5, 5), (7, 8), (8, 11))):
            polygon(c, [(8 - w, y + 3), (8 + w, y + 3), (8, y - 1)], _H("#2f6b4f") if i % 2 else _H("#3b7d5c"))
            c.fill_rect(8 - w + 1, y + 2, w, 1, _H("#ffffff"))
        c.fill_rect(7, 14, 2, 2, _ic.BROWN)
    elif kind == "snowman":
        c.disc(8, 12, 3.6, _H("#ffffff")); c.disc(8, 6.5, 2.7, _H("#ffffff"))
        c.set(9, 6, OUTLINE); c.set(7, 6, OUTLINE); c.fill_rect(10, 7, 2, 1, _H("#ff9b3d"))
        c.fill_rect(5, 9, 6, 1, _H("#e0484f"))
    elif kind == "icicles":
        for x, h in ((2, 6), (6, 9), 
                     (10, 5), (13, 8)):
            polygon(c, [(x - 1.5, 0), (x + 1.5, 0), (x, h)], _H("#cfefff"))
        c.fill_rect(0, 0, T, 1, _H("#ffffff"))
    elif kind == "rock":
        c.disc(8, 12, 5, STONE); c.disc(7, 11, 3, STONE_L); c.fill_rect(3, 15, 10, 1, STONE_D)
    c.outline(OUTLINE)
    return c


BIOME_DECOR = {"grassland": ["grass", "flower_red", "flower_yellow", "bush", "mushroom", "sign"],
               "dungeon": ["chain", "bones", "barrel", "cobweb", "sign", "mushroom"],
               "snow": ["pine", "snowman", "icicles", "rock", "sign", "bush"]}


def biome_tiles(biome: str = "grassland") -> dict[str, Canvas]:
    """The full tileset recoloured and re-decorated for a biome (same tile names in every biome)."""
    g = globals()
    keep = {k: g[k] for k in ("GRASS", "GRASS_L", "GRASS_D", "DIRT", "DIRT_L", "DIRT_D", "STONE", "STONE_L", "STONE_D", "WATER", "WATER_L")}
    b = BIOMES[biome]
    try:
        g["GRASS"], g["GRASS_L"], g["GRASS_D"] = (_H(x) for x in b["grass"])
        g["DIRT"], g["DIRT_L"], g["DIRT_D"] = (_H(x) for x in b["dirt"])
        g["STONE"], g["STONE_L"], g["STONE_D"] = (_H(x) for x in b["stone"])
        g["WATER"], g["WATER_L"] = (_H(x) for x in b["water"])
        out = tiles()
        if b["water_alpha"] == 255:  # lava: opaque, glowing
            for k in ("water_top_0", "water_top_1", "water"):
                out[k] = recolor(out[k], {})
                out[k].px = [[(p[0], p[1], p[2], 255) if p[3] else p for p in row] for row in out[k].px]
        for k in list(out):
            if k.startswith("decor_"):
                del out[k]
        for d in BIOME_DECOR[biome]:
            out[f"decor_{d}"] = _decor(d) if d in ("grass", "flower_red", "flower_yellow", "bush", "mushroom", "sign") else _decor_biome(d)
        return out
    finally:
        g.update(keep)


def level_scene(biome: str = "grassland", frame: int = 0) -> Canvas:
    """320x180 showcase level: biome tiles + the designed heroes and monsters (frame picks animation frames)."""
    from .characters import hero
    from .monsters import MONSTERS
    W, Hh = 320, 180
    b = BIOMES[biome]
    tl = biome_tiles(biome)
    c = Canvas(W, Hh)
    top, bot = _H(b["sky"][0]), _H(b["sky"][1])
    for y in range(Hh):
        t = y / Hh
        c.fill_rect(0, y, W, 1, tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))
    if biome == "dungeon":
        for y in range(0, Hh - 32, 16):          # back wall of bricks
            for x in range(0, W, 16):
                c.blit(recolor(tl["bricks" if (x // 16 + y // 16) % 3 else "bricks_alt"], {}), x, y)
        for y in range(0, Hh - 32):
            c.px[y] = [(p[0] * 9 // 20, p[1] * 9 // 20, p[2] * 9 // 20, 255) for p in c.px[y]]   # darken the wall so the action pops
    else:
        for x in range(0, W, 3):
            h = 30 + int(10 * math.sin(x / 23 + (1 if biome == "snow" else 0)))
            c.fill_rect(x, Hh - 32 - h, 3, h, _H(b["hills"]))
        if biome == "snow":
            rng = random.Random(4)
            for _ in range(70):
                c.set(rng.randrange(W), rng.randrange(Hh - 40), (255, 255, 255, 255))
    gy = Hh - 32
    for x in range(0, 13 * T, T):
        c.blit(tl["ground_tl" if x == 0 else "ground_t"], x, gy); c.blit(tl["ground_bl" if x == 0 else "ground_b"], x, gy + T)
    for x in range(13 * T, 16 * T, T):
        c.blit(tl["water_top_%d" % (frame % 2)], x, gy + 4); c.blit(tl["water"], x, gy + 4 + T)
    for x in range(16 * T, W, T):
        c.blit(tl["ground_tl" if x == 16 * T else "ground_t"], x, gy); c.blit(tl["ground_bl" if x == 16 * T else "ground_b"], x, gy + T)
    for i, p in enumerate(("left", "mid", "mid", "right")):
        c.blit(tl[f"platform_{p}"], 120 + i * T, 82)
    hanging = {"cobweb": (304, 0), "chain": (24, 0), "icicles": (136, 88)}
    for k, x in zip(BIOME_DECOR[biome][:4], (8, 92, 176, 300)):
        c.blit(tl[f"decor_{k}"], *(hanging.get(k, (x, gy - T))))
    c.blit(tl["torch_%d" % (frame % 2)], 288, gy - 2 * T) if biome == "dungeon" else None
    it = items()
    c.blit(it["chest_closed"], 156, 66)
    for i, x in enumerate((128, 140)):
        c.blit(it["coin_gold"], x, 64 - i * 3)
    f = frame
    knight, mage, ranger = hero("knight"), hero("mage"), hero("ranger")
    foes = {"grassland": ("slime_green", "mushroom_red", "bat_purple"), "dungeon": ("skeleton_bone", "eye_void", "ghost_spectral"),
            "snow": ("golem_stone", "slime_blue", "ghost_pale")}[biome]
    m1, m2, m3 = (MONSTERS[n]() for n in foes)
    c.blit(knight["attack"][1], 40, gy - 31)
    c.blit(ranger["attack"][1], 160, 82 - 31)
    c.blit(mage["attack"][2], 230, gy - 31)
    c.blit(m1["attack"][1], 66, gy - 31)
    c.blit(m2["idle"][f % 4], 200, gy - 31)
    c.blit(m3["move"][f % 6], 96, 30)
    c.blit(hit_spark()[1], 64, gy - 22)
    c.blit(magic_burst()[2], 252, gy - 30)
    return c
