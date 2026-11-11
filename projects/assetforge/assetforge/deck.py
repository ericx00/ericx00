"""Deckbuilder Kit: card frames, card backs and the battle UI parts a card game needs.
Card size is 88x124 px at 1x (title plate, 76x40 art window, type tab, 76x48 text box)."""
from __future__ import annotations

from .deckicons import GROUPS, _flame
from .draw import polygon, ring
from .pixfonts import fonts
from .png import Canvas, hex_to_rgba, shade

H = hex_to_rgba
OUT = H("#1a1423")
CLEAR = (0, 0, 0, 0)
CW, CH = 88, 124
ART = (6, 20, 76, 40)     # x, y, w, h of the art window
TEXT = (6, 70, 76, 48)    # text box
TITLE = (5, 5, 78, 13)

TYPES = {  # background, plate, light
    "attack": ("#4a1a26", "#a3283a", "#f0707a"),
    "skill": ("#1b2c52", "#2f5fb5", "#7fb0ff"),
    "power": ("#35204f", "#7a44b0", "#c99af5"),
    "item": ("#1c3d28", "#2e7a3a", "#7fdc8e"),
    "curse": ("#202329", "#454a55", "#9aa0ad"),
}
RARITIES = {  # dark, mid, light
    "common": ("#4a5160", "#8791a0", "#d5dbe4"),
    "uncommon": ("#195867", "#2fa3b8", "#9aeaf5"),
    "rare": ("#7a4a12", "#d99a2b", "#ffe9a0"),
    "legendary": ("#7a1f1a", "#f0642e", "#ffd27a"),
}
PANEL, PANEL_L, PANEL_D = H("#262130"), H("#3d3550"), H("#191520")

_F = None


def F():
    global _F
    if _F is None:
        _F = fonts()
    return _F


def _round(c: Canvas, x: int, y: int, w: int, h: int, col, r: int = 2) -> None:
    c.fill_rect(x, y, w, h, col)
    for i in range(r):
        n = r - i
        for (xx, yy) in ((x, y + i), (x + w - n, y + i), (x, y + h - 1 - i), (x + w - n, y + h - 1 - i)):
            c.fill_rect(xx, yy, n, 1, CLEAR)


def _bevel(c: Canvas, x: int, y: int, w: int, h: int, mid, light, dark, r: int = 1) -> None:
    """Outlined box with a light top/left edge and a dark bottom/right edge."""
    _round(c, x, y, w, h, OUT, r + 1)
    _round(c, x + 1, y + 1, w - 2, h - 2, mid, r)
    c.fill_rect(x + 2, y + 1, w - 4, 1, light); c.fill_rect(x + 1, y + 2, 1, h - 4, light)
    c.fill_rect(x + 2, y + h - 2, w - 4, 1, dark); c.fill_rect(x + w - 2, y + 2, 1, h - 4, dark)


def frame(kind: str = "attack", rarity: str = "common", label: bool = True) -> Canvas:
    bg, plate, light = (H(v) for v in TYPES[kind])
    md, mm, ml = (H(v) for v in RARITIES[rarity])
    c = Canvas(CW, CH)
    _round(c, 0, 0, CW, CH, OUT, 3)
    _round(c, 1, 1, CW - 2, CH - 2, mm, 2)
    c.fill_rect(3, 1, CW - 6, 1, ml); c.fill_rect(1, 3, 1, CH - 6, ml)
    c.fill_rect(3, CH - 2, CW - 6, 1, md); c.fill_rect(CW - 2, 3, 1, CH - 6, md)
    c.fill_rect(2, 2, CW - 4, 1, mm); c.fill_rect(3, 3, CW - 6, CH - 6, OUT)
    c.fill_rect(4, 4, CW - 8, CH - 8, bg)
    # subtle vertical shading of the card body
    for y in range(4, CH - 4):
        if y % 2 == 0 and y > CH * 0.55:
            c.fill_rect(4, y, CW - 8, 1, shade(bg, 0.9))
    # title plate
    x, y, w, h = TITLE
    c.fill_rect(x - 1, y - 1, w + 2, h + 2, OUT)
    c.fill_rect(x, y, w, h, plate); c.fill_rect(x, y, w, 1, light); c.fill_rect(x, y + h - 2, w, 2, shade(plate, 0.72))
    c.set(x, y, plate); c.set(x + w - 1, y, plate)
    # art window (transparent, so your art goes underneath)
    x, y, w, h = ART
    c.fill_rect(x - 1, y - 1, w + 2, h + 2, OUT)
    c.fill_rect(x, y, w, h, CLEAR)
    # text box
    x, y, w, h = TEXT
    c.fill_rect(x - 1, y - 1, w + 2, h + 2, OUT)
    c.fill_rect(x, y, w, h, PANEL); c.rect(x, y, w, h, PANEL_L)
    c.fill_rect(x + 1, y + h - 1, w - 2, 1, PANEL_D); c.fill_rect(x + w - 1, y + 1, 1, h - 2, PANEL_D)
    # type tab across the bottom edge of the art
    tw = 38
    tx, ty = (CW - tw) // 2, ART[1] + ART[3] - 4
    _bevel(c, tx, ty, tw, 11, mm, ml, md)
    if label:
        f = F()["tiny"]
        txt = kind.upper()
        f.draw(c, tx + (tw - f.width(txt)) // 2 + 1, ty + 3, txt, OUT)
    # rarity studs
    if rarity in ("rare", "legendary"):
        for sx, sy in ((2, 2), (CW - 5, 2), (2, CH - 5), (CW - 5, CH - 5)):
            c.fill_rect(sx, sy, 3, 3, OUT); c.set(sx + 1, sy + 1, ml)
    if rarity == "legendary":
        for sx in (CW // 2 - 14, CW // 2 + 11):
            polygon(c, [(sx + 1.5, ART[1] - 3.5), (sx + 4, ART[1] - 1), (sx + 1.5, ART[1] + 1.5), (sx - 1, ART[1] - 1)], ml)
    return c


def art_bg(kind: str) -> Canvas:
    """A backdrop to put behind card art: dark centre glow in the type colour."""
    bg, plate, light = (H(v) for v in TYPES[kind])
    w, h = ART[2], ART[3]
    c = Canvas(w, h, shade(bg, 0.55))
    for r, f in ((26, 0.75), (19, 1.0), (12, 1.3)):
        for yy in range(h):
            for xx in range(w):
                if ((xx - w / 2) / 1.6) ** 2 + (yy - h / 2) ** 2 <= r * r / 2.2 and (xx + yy) % 2 == 0 or ((xx - w / 2) / 1.6) ** 2 + (yy - h / 2) ** 2 <= (r - 4) ** 2 / 2.2:
                    c.px[yy][xx] = shade(bg, f)
    return c


BACKS = {"ember": ("#3a1418", "#a3283a", "#f08a2e"), "frost": ("#14263a", "#2f5fb5", "#7fe3f0"), "arcane": ("#24163a", "#7a44b0", "#d2a8f5"),
         "forest": ("#142a1c", "#2e7a3a", "#a6eaae"), "bone": ("#23262b", "#5b6170", "#e6e9ef"), "royal": ("#2a2010", "#b5761f", "#ffe08a")}
BACK_EMBLEM = {"ember": ("status", "burn"), "frost": ("status", "frost"), "arcane": ("intent", "special"), "forest": ("status", "thorns"),
               "bone": ("status", "curse"), "royal": ("map", "boss")}


def back(name: str) -> Canvas:
    bg, mid, light = (H(v) for v in BACKS[name])
    c = Canvas(CW, CH)
    _round(c, 0, 0, CW, CH, OUT, 3)
    _round(c, 1, 1, CW - 2, CH - 2, mid, 2)
    c.fill_rect(3, 1, CW - 6, 1, light); c.fill_rect(1, 3, 1, CH - 6, light)
    c.fill_rect(3, 3, CW - 6, CH - 6, OUT); c.fill_rect(4, 4, CW - 8, CH - 8, bg)
    lat = shade(bg, 1.45)
    for y in range(6, CH - 6):
        for x in range(6, CW - 6):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                c.px[y][x] = lat
    c.rect(6, 6, CW - 12, CH - 12, mid); c.rect(8, 8, CW - 16, CH - 16, shade(mid, 0.6))
    cx, cy = CW // 2, CH // 2
    polygon(c, [(cx, cy - 34), (cx + 26, cy), (cx, cy + 34), (cx - 26, cy)], OUT)
    polygon(c, [(cx, cy - 32), (cx + 24.5, cy), (cx, cy + 32), (cx - 24.5, cy)], mid)
    polygon(c, [(cx, cy - 29), (cx + 22, cy), (cx, cy + 29), (cx - 22, cy)], shade(bg, 0.7))
    g, n = BACK_EMBLEM[name]
    icon = GROUPS[g][n]().scaled(2)
    c.blit(icon, cx - 16, cy - 16)
    for sx, sy in ((10, 10), (CW - 13, 10), (10, CH - 13), (CW - 13, CH - 13)):
        c.fill_rect(sx, sy, 3, 3, light); c.set(sx + 1, sy + 1, WHITE)
    return c


WHITE = H("#ffffff")
GEMS = {"heat": ("#a3283a", "#f0642e", "#ffd27a"), "energy": ("#264f9e", "#3f7ee8", "#c4dcff"), "gold": ("#7a4a12", "#f2b33d", "#fff0b0"),
        "nature": ("#1f5a2c", "#4fbf5f", "#c9f5cf"), "void": ("#3a2459", "#9b59d0", "#e6ccff"), "steel": ("#4a5160", "#9aa4b3", "#ffffff")}


def gem(name: str) -> Canvas:
    d, m, l = (H(v) for v in GEMS[name])
    c = Canvas(17, 17)
    c.disc(8.5, 8.5, 8.4, OUT); c.disc(8.5, 8.5, 7.3, d); c.disc(8.5, 8.5, 6.2, m)
    ring(c, 8.5, 8.5, 6.2, 5.0, l, 100, 200)
    c.fill_rect(4, 4, 2, 1, WHITE)
    return c


def glow(col: str, w: int = CW, h: int = CH) -> Canvas:
    """Outline to draw behind a card: 3 px, fading outwards."""
    base = H(col)
    c = Canvas(w + 6, h + 6)
    for i, a in enumerate((70, 140, 255)):
        _round(c, i, i, w + 6 - 2 * i, h + 6 - 2 * i, (base[0], base[1], base[2], a), 4 - i)
    _round(c, 3, 3, w, h, CLEAR, 3)
    return c


def mini(kind: str) -> Canvas:
    bg, plate, light = (H(v) for v in TYPES[kind])
    c = Canvas(22, 30)
    _round(c, 0, 0, 22, 30, OUT, 2); _round(c, 1, 1, 20, 28, plate, 1)
    c.fill_rect(3, 3, 16, 10, shade(bg, 0.7)); c.fill_rect(3, 15, 16, 2, light); c.fill_rect(3, 19, 16, 1, bg); c.fill_rect(3, 22, 12, 1, bg); c.fill_rect(3, 25, 14, 1, bg)
    c.fill_rect(2, 1, 18, 1, light)
    return c


def _btn(base: str, state: str, w: int = 48, h: int = 18) -> Canvas:
    m = H(base)
    f = {"normal": 1.0, "hover": 1.18, "pressed": 0.82, "disabled": 1.0}[state]
    if state == "disabled":
        g = (m[0] * 30 + m[1] * 59 + m[2] * 11) // 100
        m = (g, g, g, 255)
        m = shade(m, 0.7)
    m = shade(m, f)
    c = Canvas(w, h)
    press = 1 if state == "pressed" else 0
    _round(c, 0, press, w, h - press, OUT, 2)
    _round(c, 1, 1 + press, w - 2, h - 2 - press, shade(m, 0.6), 1)       # lip
    _round(c, 1, 1 + press, w - 2, h - 5 + press, m, 1)                    # face
    c.fill_rect(3, 1 + press, w - 6, 1, shade(m, 1.4)); c.fill_rect(1, 3 + press, 1, h - 9 + press, shade(m, 1.2))
    return c


def _panel(mid, light, dark, w: int = 32, h: int = 32, inner: bool = True) -> Canvas:
    c = Canvas(w, h)
    _bevel(c, 0, 0, w, h, mid, light, dark, 2)
    if inner:
        c.rect(3, 3, w - 6, h - 6, dark); c.fill_rect(4, h - 4, w - 8, 1, light); c.fill_rect(w - 4, 4, 1, h - 8, light)
    return c


def _bubble() -> Canvas:
    c = Canvas(30, 26)
    _bevel(c, 0, 0, 30, 21, H("#f1ead8"), WHITE, H("#c2b89c"), 2)
    polygon(c, [(11, 19), (19, 19), (15, 26)], OUT); polygon(c, [(12.5, 19), (17.5, 19), (15, 24)], H("#f1ead8"))
    return c


def _bar_frame(w: int = 64, h: int = 9) -> Canvas:
    c = Canvas(w, h)
    _round(c, 0, 0, w, h, OUT, 2); c.fill_rect(1, 1, w - 2, h - 2, H("#5b6170")); c.fill_rect(2, 2, w - 4, h - 4, H("#17131d"))
    c.fill_rect(2, 1, w - 4, 1, H("#9aa0ad"))
    return c


def _bar_fill(col: str, w: int = 60, h: int = 5) -> Canvas:
    m = H(col)
    c = Canvas(w, h, m)
    c.fill_rect(0, 0, w, 1, shade(m, 1.45)); c.fill_rect(0, h - 1, w, 1, shade(m, 0.65))
    return c


def _seg(col: str | None) -> Canvas:
    """One cell of the heat/energy gauge (8x12)."""
    c = Canvas(8, 12)
    _round(c, 0, 0, 8, 12, OUT, 1)
    if col is None:
        c.fill_rect(1, 1, 6, 10, H("#17131d")); c.fill_rect(1, 1, 6, 1, H("#2a2433"))
    else:
        m = H(col)
        c.fill_rect(1, 1, 6, 10, m); c.fill_rect(1, 1, 6, 2, shade(m, 1.45)); c.fill_rect(1, 9, 6, 2, shade(m, 0.65)); c.set(2, 3, WHITE)
    return c


def _badge(state: str) -> Canvas:
    cols = {"normal": ("#3d3550", "#5a4f78"), "hover": ("#b5761f", "#ffe08a"), "current": ("#a3283a", "#ff9aa0"), "done": ("#23262b", "#454a55"), "locked": ("#191520", "#2a2433")}[state]
    c = Canvas(28, 28)
    c.disc(14, 14, 13.8, OUT); c.disc(14, 14, 12.8, H(cols[1])); c.disc(14, 14, 10.4, OUT); c.disc(14, 14, 9.4, H(cols[0]))
    ring(c, 14, 14, 9.4, 8.2, shade(H(cols[0]), 1.35), 100, 200)
    return c


def _orb(col: str | None) -> Canvas:
    c = Canvas(24, 24)
    c.disc(12, 12, 11.6, OUT); c.disc(12, 12, 10.4, H("#8791a0")); c.disc(12, 12, 8.8, OUT)
    if col is None:
        c.disc(12, 12, 8, H("#17131d"))
    else:
        d, m, l = (H(v) for v in GEMS[col])
        c.disc(12, 12, 8, d); c.disc(12, 11.4, 6.8, m); ring(c, 12, 12, 6.8, 5.4, l, 100, 200); c.fill_rect(7, 7, 2, 1, WHITE)
    return c


def _arrow_head() -> Canvas:
    c = Canvas(16, 16)
    polygon(c, [(8, 1), (15, 13), (8, 10), (1, 13)], H("#ffd27a"))
    polygon(c, [(8, 4), (11.5, 10.5), (8, 9), (4.5, 10.5)], H("#f0642e"))
    c.outline(OUT)
    return c


def _dot() -> Canvas:
    c = Canvas(8, 8)
    c.disc(4, 4, 2.6, H("#ffd27a")); c.outline(OUT)
    return c


def _ribbon(col: str) -> Canvas:
    m = H(col)
    c = Canvas(64, 20)
    polygon(c, [(0, 5), (10, 5), (10, 19), (0, 19), (4, 12)], shade(m, 0.6)); polygon(c, [(64, 5), (54, 5), (54, 19), (64, 19), (60, 12)], shade(m, 0.6))
    c.fill_rect(6, 1, 52, 15, m); c.fill_rect(6, 1, 52, 1, shade(m, 1.4)); c.fill_rect(6, 14, 52, 2, shade(m, 0.75))
    c.outline(OUT)
    return c


# name -> (canvas, nine-slice margins or None)
def ui_parts() -> dict[str, tuple[Canvas, object]]:
    out: dict[str, tuple[Canvas, object]] = {}
    for base, col in (("ember", "#d9532b"), ("steel", "#5b6b85"), ("gold", "#d99a2b"), ("green", "#3a9a4c")):
        for st in ("normal", "hover", "pressed", "disabled"):
            out[f"button_{base}_{st}"] = (_btn(col, st), (4, 4, 4, 6))
    out["panel_stone"] = (_panel(H("#2c2638"), H("#463d5c"), H("#191520")), 6)
    out["panel_iron"] = (_panel(H("#3a4254"), H("#6b7892"), H("#232836")), 6)
    out["panel_parchment"] = (_panel(H("#e2cf9c"), H("#f6ebc8"), H("#b3995e")), 6)
    out["panel_flat"] = (_panel(H("#211c2b"), H("#322a41"), H("#15111b"), inner=False), 4)
    out["tooltip"] = (_panel(H("#15111b"), H("#463d5c"), H("#0d0a12"), 24, 24, inner=False), 4)
    out["intent_bubble"] = (_bubble(), None)
    out["bar_frame"] = (_bar_frame(), (3, 3, 3, 3))
    for n, col in (("hp", "#e0484f"), ("block", "#3f7ee8"), ("enemy", "#f08a2e"), ("poison", "#4fbf5f"), ("xp", "#9b59d0")):
        out[f"bar_fill_{n}"] = (_bar_fill(col), None)
    for n, col in (("empty", None), ("cold", "#4fd0e0"), ("warm", "#f2b33d"), ("hot", "#f0642e"), ("over", "#e0484f"), ("energy", "#3f7ee8")):
        out[f"gauge_{n}"] = (_seg(col), None)
    for st in ("normal", "hover", "current", "done", "locked"):
        out[f"node_{st}"] = (_badge(st), None)
    for n in (None, "energy", "heat", "nature", "void", "gold"):
        out[f"orb_{n or 'empty'}"] = (_orb(n), None)
    out["target_arrow"] = (_arrow_head(), None)
    out["target_dot"] = (_dot(), None)
    for n, col in (("victory", "#d99a2b"), ("defeat", "#7a2030"), ("neutral", "#5b6b85")):
        out[f"ribbon_{n}"] = (_ribbon(col), (12, 2, 12, 5))
    return out


def all_cards() -> dict[str, dict[str, Canvas]]:
    return {
        "frames": {f"{k}_{r}": frame(k, r, True) for k in TYPES for r in RARITIES},
        "frames_no_label": {f"{k}_{r}": frame(k, r, False) for k in TYPES for r in RARITIES},
        "art_backgrounds": {k: art_bg(k) for k in TYPES},
        "backs": {n: back(n) for n in BACKS},
        "gems": {n: gem(n) for n in GEMS},
        "glows": {n: glow(col) for n, col in (("playable", "#ffe08a"), ("selected", "#ffffff"), ("hot", "#f0642e"), ("cold", "#4fd0e0"), ("danger", "#e0484f"))},
        "mini": {k: mini(k) for k in TYPES},
    }


def wrap(font, text: str, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split(" "):
        t = (cur + " " + word).strip()
        if font.width(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = word
    if cur:
        lines.append(cur)
    return lines


def sample_card(kind: str, rarity: str, title: str, text: str, art: Canvas | None, cost: int | None, gem_name: str = "heat") -> Canvas:
    """A finished card, to show how the layers go together (also used for the previews)."""
    f = F()
    c = Canvas(CW, CH)
    c.blit(art_bg(kind), ART[0], ART[1])
    if art:
        c.blit(art, ART[0] + (ART[2] - art.w) // 2, ART[1] + (ART[3] - art.h) // 2 - 1)
    c.blit(frame(kind, rarity), 0, 0)
    f["sans"].draw(c, TITLE[0] + (TITLE[2] - f["sans"].width(title)) // 2, TITLE[1] + 3, title, WHITE, shadow=OUT)
    lines = wrap(f["sans"], text, TEXT[2] - 6)
    y = TEXT[1] + (TEXT[3] - len(lines) * 9) // 2 + 1
    for ln in lines:
        f["sans"].draw(c, TEXT[0] + (TEXT[2] - f["sans"].width(ln)) // 2, y, ln, H("#e8e2f0"))
        y += 9
    if cost is not None:
        c.blit(gem(gem_name), 1, 14)
        s = str(cost)
        f["bold"].draw(c, 1 + (17 - f["bold"].width(s)) // 2 + 1, 14 + 5, s, WHITE, shadow=OUT)
    return c
