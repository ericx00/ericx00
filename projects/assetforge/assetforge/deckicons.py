"""Card-game icons (16x16): enemy intents, status effects, resources, map nodes and actions.
A separate set from the UI Kit icons, drawn for deckbuilders and turn-based battlers."""
from __future__ import annotations

import math

from .draw import erase_disc, line, polygon, ring, rotate_pts
from .png import Canvas, hex_to_rgba

H = hex_to_rgba
OUT = H("#1a1423")
RED, RED_L, RED_D = H("#e0484f"), H("#ff9aa0"), H("#a3283a")
ORG, ORG_L, ORG_D = H("#f08a2e"), H("#ffc56b"), H("#b5521c")
GOLD, GOLD_L, GOLD_D = H("#f2b33d"), H("#ffe08a"), H("#b5761f")
SILV, SILV_L, SILV_D = H("#c9d1dc"), H("#ffffff"), H("#7d8794")
BLUE, BLUE_L, BLUE_D = H("#3f7ee8"), H("#9cc2ff"), H("#264f9e")
CYAN, CYAN_L, CYAN_D = H("#4fd0e0"), H("#c4f4fa"), H("#2a8a9c")
GREEN, GREEN_L, GREEN_D = H("#4fbf5f"), H("#a6eaae"), H("#2e7a3a")
BROWN, BROWN_L, BROWN_D = H("#8a5a34"), H("#c08a5a"), H("#5a3820")
PURP, PURP_L, PURP_D = H("#9b59d0"), H("#d2a8f5"), H("#623a8a")
WHITE, GREY, DARK = H("#f4f4f4"), H("#8a8f99"), H("#3a3644")
PAPER, PAPER_D = H("#e9d6a6"), H("#c2a56b")


def _new() -> Canvas:
    return Canvas(16, 16)


def _done(c: Canvas) -> Canvas:
    c.outline(OUT)
    return c


def _sword(c, x0, y0, x1, y1, blade=SILV, hi=SILV_L, guard=GOLD_D, grip=BROWN):
    """Blade from the hilt end (x0, y0) to the tip (x1, y1); both diagonal."""
    dx, dy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
    line(c, x0 + 3 * dx, y0 + 3 * dy, x1, y1, blade, 2)
    line(c, x0 + 3 * dx, y0 + 3 * dy - (1 if dy > 0 else 0), x1 - dx, y1 - dy - (1 if dy > 0 else 0), hi, 1)
    line(c, x0 + 2 * dx - 2 * dx, y0 + 2 * dy + 2 * dy, x0 + 2 * dx + 2 * dx, y0 + 2 * dy - 2 * dy, guard, 2)
    line(c, x0, y0, x0 + dx, y0 + dy, grip, 2)


def _shield(c, col=BLUE, rim=SILV_D, hi=BLUE_L, cx=8.0, top=2.5, w=11.0, hgt=12.0):
    l, r = cx - w / 2, cx + w / 2
    polygon(c, [(l, top), (r, top), (r, top + hgt * 0.45), (cx, top + hgt), (l, top + hgt * 0.45)], rim)
    polygon(c, [(l + 1.3, top + 1.3), (r - 1.3, top + 1.3), (r - 1.3, top + hgt * 0.42), (cx, top + hgt - 1.9), (l + 1.3, top + hgt * 0.42)], col)
    c.fill_rect(int(l + 2), int(top + 2), 2, 1, hi); c.set(int(l + 2), int(top + 3), hi)


def _flame(c, cx=8.0, base=14.0, s=1.0, outer=ORG, mid=GOLD, core=GOLD_L):
    polygon(c, [(cx - 4 * s, base - 4 * s), (cx - 2.5 * s, base - 8 * s), (cx - 1 * s, base - 6.5 * s), (cx + 0.5 * s, base - 12 * s), (cx + 3 * s, base - 7.5 * s),
                (cx + 4.2 * s, base - 4 * s), (cx + 2.5 * s, base - 0.5 * s), (cx - 2.5 * s, base - 0.5 * s)], outer)
    polygon(c, [(cx - 2 * s, base - 3.5 * s), (cx - 0.5 * s, base - 5 * s), (cx + 0.5 * s, base - 8 * s), (cx + 2.4 * s, base - 4 * s), (cx + 1.5 * s, base - 1 * s), (cx - 1.5 * s, base - 1 * s)], mid)
    c.fill_rect(int(cx - 1 * s), int(base - 3.2 * s), max(1, int(2 * s)), max(1, int(2 * s)), core)


def _drop(c, col, hi, cx=8.0, top=2.0, r=4.2):
    cy = top + 7.6
    c.disc(cx, cy, r, col)
    polygon(c, [(cx, top), (cx + r * 0.92, cy - 1), (cx - r * 0.92, cy - 1)], col)
    c.fill_rect(int(cx - 2), int(cy - 1), 1, 2, hi); c.set(int(cx - 1), int(cy - 2), hi)


def _heart(c, col=RED, hi=RED_L, cx=8.0, cy=6.0, s=1.0):
    c.disc(cx - 3 * s, cy, 3.6 * s, col); c.disc(cx + 3 * s, cy, 3.6 * s, col)
    polygon(c, [(cx - 6.4 * s, cy + 1 * s), (cx + 6.4 * s, cy + 1 * s), (cx, cy + 8 * s)], col)
    c.fill_rect(int(cx - 4 * s), int(cy - 2 * s), 2, 1, hi); c.set(int(cx - 5 * s), int(cy - 1 * s), hi)


def _skull(c, col=WHITE, sh=SILV, eye=OUT, cx=8.0, cy=7.0):
    c.disc(cx, cy, 5.2, col)
    c.fill_rect(int(cx - 3), int(cy + 3), 6, 4, col)
    c.fill_rect(int(cx - 3), int(cy + 6), 6, 1, sh)
    c.fill_rect(int(cx - 3), int(cy - 1), 2, 3, eye); c.fill_rect(int(cx + 1), int(cy - 1), 2, 3, eye)
    c.set(int(cx - 1), int(cy + 3), eye); c.set(int(cx), int(cy + 3), eye)
    c.set(int(cx - 2), int(cy + 5), sh); c.set(int(cx), int(cy + 5), sh); c.set(int(cx + 2), int(cy + 5), sh)


def _card(c, x, y, w=8, h=11, face=PAPER, edge=PAPER_D, pip=None):
    c.fill_rect(x, y, w, h, face)
    c.fill_rect(x, y + h - 1, w, 1, edge); c.fill_rect(x + w - 1, y, 1, h, edge)
    if pip:
        c.fill_rect(x + 2, y + 2, w - 4, 3, pip)


def _stack(c, cards, w=7, h=10):
    """Overlapping cards, each with its own outline so they read as separate."""
    for x, y, face, edge, pip in cards:
        a = Canvas(16, 16); _card(a, x, y, w, h, face=face, edge=edge, pip=pip); a.outline(OUT); c.blit(a, 0, 0)


def _chev(c, cx, y, col, up=True, w=4):
    for i in range(w + 1):
        yy = y + (i if up else -i)
        c.fill_rect(cx - i, yy, 1, 2, col); c.fill_rect(cx + i - 1, yy, 1, 2, col)


def _arrow_up(c, cx, top, col, hgt=9, w=3):
    polygon(c, [(cx, top), (cx + w + 1.5, top + w + 1.5), (cx - w - 1.5, top + w + 1.5)], col)
    c.fill_rect(int(cx - 1), int(top + w), 2, hgt - w, col)


def _bolt(c, col=GOLD, hi=GOLD_L, ox=0, oy=0):
    polygon(c, [(9 + ox, 1 + oy), (4 + ox, 9 + oy), (7.5 + ox, 9 + oy), (6 + ox, 15 + oy), (12 + ox, 6.5 + oy), (8.5 + ox, 6.5 + oy), (10.5 + ox, 1 + oy)], col)
    line(c, 8 + ox, 2 + oy, 6 + ox, 7 + oy, hi)


# ---------- intents ----------
def intent_attack():
    c = _new(); _sword(c, 2, 13, 13, 2, blade=RED_L, hi=WHITE, guard=RED_D, grip=BROWN_D); return _done(c)


def intent_multi():
    c = _new(); _sword(c, 2, 13, 13, 2); _sword(c, 13, 13, 2, 2, blade=SILV, hi=SILV_L); return _done(c)


def intent_heavy():
    c = _new()
    line(c, 3, 13, 10, 6, BROWN, 2)
    polygon(c, rotate_pts([(6, 1.5), (14, 1.5), (14, 7.5), (6, 7.5)], 45, 10, 4.5), SILV_D)
    polygon(c, rotate_pts([(7, 2.5), (13, 2.5), (13, 4.5), (7, 4.5)], 45, 10, 4.5), SILV)
    return _done(c)


def intent_defend():
    c = _new(); _shield(c); return _done(c)


def intent_buff():
    c = _new(); _chev(c, 8, 2, GREEN_L); _chev(c, 8, 6, GREEN); _chev(c, 8, 10, GREEN_D); return _done(c)


def intent_debuff():
    c = _new(); _chev(c, 8, 13, PURP_L, up=False); _chev(c, 8, 9, PURP, up=False); _chev(c, 8, 5, PURP_D, up=False); return _done(c)


def intent_special():
    c = _new()
    pts = []
    for i in range(16):
        r = 7 if i % 2 == 0 else 3.4
        a = math.radians(i * 22.5)
        pts.append((8 + r * math.cos(a), 8 + r * math.sin(a)))
    polygon(c, pts, PURP); c.disc(8, 8, 2.6, PURP_L); c.fill_rect(7, 7, 2, 2, WHITE)
    return _done(c)


def intent_unknown():
    c = _new()
    c.disc(8, 8, 6.5, DARK); c.disc(8, 8, 5.4, GREY)
    c.fill_rect(6, 4, 4, 2, WHITE); c.fill_rect(9, 5, 2, 3, WHITE); c.fill_rect(7, 8, 2, 2, WHITE); c.fill_rect(7, 11, 2, 2, WHITE)
    return _done(c)


def intent_sleep():
    c = _new()
    for x, y, s, col in ((2, 8, 6, BLUE_L), (8, 2, 5, CYAN_L)):
        c.fill_rect(x, y, s, 1, col); c.fill_rect(x, y + s - 1, s, 1, col)
        line(c, x + s - 1, y, x, y + s - 1, col)
    return _done(c)


def intent_flee():
    c = _new()
    polygon(c, [(1, 8), (7, 2.5), (7, 6), (14, 6), (14, 10), (7, 10), (7, 13.5)], GOLD)
    c.fill_rect(7, 7, 6, 1, GOLD_L)
    return _done(c)


def intent_summon():
    c = _new()
    ring(c, 8, 8, 6.8, 5, PURP); ring(c, 8, 8, 4, 3, PURP_D)
    c.fill_rect(7, 4, 2, 8, PURP_L); c.fill_rect(4, 7, 8, 2, PURP_L)
    return _done(c)


def intent_stoke():
    c = _new(); _flame(c, 6.5, 15, 1.0); _arrow_up(c, 13, 2, RED, hgt=8, w=1); return _done(c)


# ---------- status ----------
def strength():
    c = _new()
    c.fill_rect(3, 5, 10, 8, ORG); c.fill_rect(3, 5, 10, 2, ORG_L)
    for x in (5, 8, 11):
        c.fill_rect(x, 5, 1, 4, ORG_D)
    c.fill_rect(1, 8, 3, 4, ORG); c.fill_rect(3, 12, 10, 1, ORG_D); c.fill_rect(5, 13, 6, 2, ORG_D)
    return _done(c)


def weak():
    c = _new()
    line(c, 2, 13, 3, 12, BROWN, 2); line(c, 2, 9, 6, 13, GOLD_D, 2)
    line(c, 5, 10, 8, 7, SILV, 2); line(c, 5, 9, 7, 7, SILV_L, 1)
    polygon(c, [(10.5, 6), (14, 2), (14, 4.5), (12, 7.5)], SILV_D)
    c.set(9, 8, PURP_L); c.set(11, 9, PURP_L); c.set(13, 8, PURP)
    return _done(c)


def vulnerable():
    c = _new(); _shield(c, col=RED, rim=SILV_D, hi=RED_L)
    line(c, 9, 3, 7, 6, OUT); line(c, 7, 6, 9, 8, OUT); line(c, 9, 8, 8, 12, OUT)
    return _done(c)


def frail():
    c = _new(); _shield(c, col=GREY, rim=DARK, hi=SILV)
    for y in range(16):
        for x in range(16):
            if x + y > 17 and c.px[y][x][3]:
                c.px[y][x] = (0, 0, 0, 0)
    c.set(9, 7, SILV_D); c.set(11, 6, SILV_D)
    return _done(c)


def burn():
    c = _new(); _flame(c); return _done(c)


def poison():
    c = _new(); _drop(c, GREEN, GREEN_L)
    c.fill_rect(6, 9, 1, 2, OUT); c.fill_rect(9, 9, 1, 2, OUT); c.fill_rect(7, 12, 2, 1, GREEN_D)
    return _done(c)


def bleed():
    c = _new(); _drop(c, RED, RED_L, cx=6.5, top=1.5, r=3.6); _drop(c, RED_D, RED, cx=12, top=7, r=2.2); return _done(c)


def frost():
    c = _new()
    for k in range(3):
        a = math.radians(k * 60)
        x, y = 6.5 * math.cos(a), 6.5 * math.sin(a)
        line(c, round(8 - x), round(8 - y), round(8 + x), round(8 + y), CYAN_L)
    for k in range(6):
        a = math.radians(k * 60)
        px, py = 8 + 4.5 * math.cos(a), 8 + 4.5 * math.sin(a)
        for d in (-50, 50):
            b = a + math.radians(d)
            line(c, round(px), round(py), round(px + 2 * math.cos(b)), round(py + 2 * math.sin(b)), CYAN)
    c.fill_rect(7, 7, 2, 2, WHITE)
    return _done(c)


def shock():
    c = _new(); _bolt(c); return _done(c)


def stun():
    c = _new()
    def st(cx, cy, r, col):
        polygon(c, [(cx, cy - r), (cx + r * 0.3, cy - r * 0.3), (cx + r, cy), (cx + r * 0.3, cy + r * 0.3), (cx, cy + r), (cx - r * 0.3, cy + r * 0.3), (cx - r, cy), (cx - r * 0.3, cy - r * 0.3)], col)
    st(6, 6.5, 5.5, GOLD); st(12, 11.5, 3.5, GOLD_L); st(12.5, 3.5, 2.5, WHITE); c.fill_rect(5, 6, 2, 1, GOLD_L)
    return _done(c)


def thorns():
    c = _new()
    for k in range(8):
        polygon(c, rotate_pts([(6.8, 4.5), (8, 0.5), (9.2, 4.5)], k * 45, 8, 8), GREEN_L)
    c.disc(8, 8, 4.4, GREEN_D); c.disc(8, 8, 3.2, GREEN); c.fill_rect(6, 6, 2, 1, GREEN_L)
    return _done(c)


def regen():
    c = _new(); _heart(c, GREEN, GREEN_L, cy=6.5)
    c.fill_rect(7, 5, 2, 6, WHITE); c.fill_rect(5, 7, 6, 2, WHITE)
    return _done(c)


def block():
    c = _new(); _shield(c, col=BLUE, rim=SILV, hi=BLUE_L); c.fill_rect(7, 5, 2, 6, SILV_L); c.fill_rect(5, 7, 6, 2, SILV_L); return _done(c)


def dodge():
    c = _new()
    for y, x0, x1, col in ((4, 2, 11, CYAN_L), (8, 4, 14, WHITE), (12, 2, 9, CYAN)):
        c.fill_rect(x0, y, x1 - x0, 2, col); c.fill_rect(x1, y, 1, 1, col)
    return _done(c)


def focus():
    c = _new()
    polygon(c, [(1, 8), (5, 4), (11, 4), (15, 8), (11, 12), (5, 12)], WHITE)
    c.disc(8, 8, 3.2, BLUE); c.disc(8, 8, 1.5, OUT); c.set(6, 6, BLUE_L)
    return _done(c)


def blind():
    c = _new()
    polygon(c, [(1, 8), (5, 4), (11, 4), (15, 8), (11, 12), (5, 12)], GREY)
    c.disc(8, 8, 3.2, DARK)
    line(c, 2, 13, 13, 2, RED, 2)
    return _done(c)


def curse():
    c = _new(); _skull(c, PURP_L, PURP, OUT); return _done(c)


def haste():
    c = _new()
    for ox in (0, 6):
        polygon(c, [(2 + ox, 3), (8 + ox, 8), (2 + ox, 13)], GOLD if ox else GOLD_D)
    return _done(c)


def slow():
    c = _new()
    c.fill_rect(3, 1, 10, 2, BROWN); c.fill_rect(3, 13, 10, 2, BROWN)
    polygon(c, [(4, 3), (12, 3), (8, 8)], CYAN_L); polygon(c, [(8, 8), (12, 13), (4, 13)], CYAN_L)
    polygon(c, [(6, 5), (10, 5), (8, 7.5)], GOLD); polygon(c, [(8, 11), (11, 13), (5, 13)], GOLD)
    return _done(c)


def heat():
    c = _new()
    c.fill_rect(7, 1, 3, 10, SILV_L); c.disc(8.5, 12, 3.4, SILV_L)
    c.disc(8.5, 12, 2.3, RED); c.fill_rect(8, 4, 1, 8, RED)
    for y in (3, 5, 7):
        c.fill_rect(11, y, 2, 1, ORG)
    return _done(c)


def cold():
    c = _new()
    c.fill_rect(7, 1, 3, 10, SILV_L); c.disc(8.5, 12, 3.4, SILV_L)
    c.disc(8.5, 12, 2.3, BLUE); c.fill_rect(8, 9, 1, 3, BLUE)
    for y in (3, 5, 7):
        c.fill_rect(11, y, 2, 1, CYAN)
    return _done(c)


def barrier():
    c = _new()
    pts = [(8 + 6.8 * math.cos(math.radians(a)), 8 + 6.8 * math.sin(math.radians(a))) for a in range(30, 390, 60)]
    polygon(c, pts, CYAN_D)
    polygon(c, [(8 + 5.3 * math.cos(math.radians(a)), 8 + 5.3 * math.sin(math.radians(a))) for a in range(30, 390, 60)], CYAN)
    line(c, 5, 6, 7, 4, CYAN_L); c.fill_rect(5, 7, 1, 2, CYAN_L)
    return _done(c)


def mark():
    c = _new()
    ring(c, 8, 8, 6.4, 4.8, RED)
    c.fill_rect(7, 0, 2, 5, RED); c.fill_rect(7, 11, 2, 5, RED); c.fill_rect(0, 7, 5, 2, RED); c.fill_rect(11, 7, 5, 2, RED)
    c.fill_rect(7, 7, 2, 2, WHITE)
    return _done(c)


# ---------- resources ----------
def energy():
    c = _new(); c.disc(8, 8, 6.8, BLUE_D); c.disc(8, 8, 5.6, BLUE); ring(c, 8, 8, 5.6, 4.6, BLUE_L, 100, 190)
    polygon(c, [(9, 3), (5.5, 8.5), (8, 8.5), (7, 13), (11, 7), (8.5, 7), (10.5, 3)], WHITE)
    return _done(c)


def ember():
    c = _new(); c.disc(8, 8, 6.8, RED_D); c.disc(8, 8, 5.6, DARK)
    _flame(c, 8, 13, 0.8); ring(c, 8, 8, 5.6, 4.8, ORG_D, 100, 190)
    return _done(c)


def gold():
    c = _new()
    for x, y in ((5, 11), (11, 11), (8, 6)):
        c.disc(x, y, 3.6, GOLD_D); c.disc(x, y - 0.6, 3, GOLD); c.set(x - 2, y - 2, GOLD_L); c.set(x - 1, y - 3, GOLD_L)
    return _done(c)


def gem():
    c = _new()
    polygon(c, [(2.5, 6), (5.5, 2.5), (10.5, 2.5), (13.5, 6), (8, 14)], PURP)
    polygon(c, [(2.5, 6), (13.5, 6), (8, 14)], PURP_D)
    polygon(c, [(5.5, 2.5), (10.5, 2.5), (9.5, 6), (6.5, 6)], PURP_L)
    polygon(c, [(6.5, 6), (9.5, 6), (8, 12)], PURP)
    return _done(c)


def card():
    c = _new(); _card(c, 4, 2, 9, 12, pip=RED); c.fill_rect(6, 9, 5, 1, PAPER_D); c.fill_rect(6, 11, 4, 1, PAPER_D); return _done(c)


def draw_pile():
    c = _new()
    _card(c, 2, 5, 9, 10, face=BLUE_D, edge=OUT); _card(c, 4, 3, 9, 10, face=BLUE_D, edge=OUT); _card(c, 6, 1, 9, 10, face=BLUE, edge=BLUE_D)
    c.fill_rect(8, 3, 5, 6, BLUE_L); c.fill_rect(9, 4, 3, 4, BLUE)
    return _done(c)


def discard_pile():
    c = _new()
    _stack(c, [(1, 4, PAPER_D, BROWN, None), (4, 2, PAPER, PAPER_D, None)], w=8, h=10)
    a = _new(); polygon(a, [(9, 10), (15, 10), (12, 15)], RED); a.fill_rect(11, 6, 2, 4, RED); a.outline(OUT); c.blit(a, 0, 0)
    return c


def exhaust_pile():
    c = _new()
    _card(c, 3, 2, 9, 12, face=DARK, edge=OUT)
    polygon(c, [(3, 14), (12, 14), (12, 9), (10, 11), (8, 8.5), (6, 11), (3, 9)], GREY)
    c.set(6, 5, ORG); c.set(9, 4, ORG_L); c.set(8, 6, RED)
    return _done(c)


def deck():
    c = _new()
    _stack(c, [(1, 4, PAPER, PAPER_D, RED), (5, 2, PAPER, PAPER_D, BLUE), (9, 4, PAPER, PAPER_D, GOLD)], w=6, h=10)
    return c


def hand():
    c = _new()
    for pts, col in ((rotate_pts([(2, 4), (8, 4), (8, 13), (2, 13)], -20, 6, 13), PAPER_D), (rotate_pts([(8, 4), (14, 4), (14, 13), (8, 13)], 20, 10, 13), PAPER_D)):
        a = _new(); polygon(a, pts, col); a.outline(OUT); c.blit(a, 0, 0)
    _stack(c, [(5, 2, PAPER, PAPER_D, RED)], w=6, h=11)
    return c


def relic():
    c = _new()
    ring(c, 8, 5, 4.6, 3.4, GOLD_D, 0, 180); c.fill_rect(3, 5, 1, 3, GOLD_D); c.fill_rect(12, 5, 1, 3, GOLD_D)
    polygon(c, [(8, 6), (12, 10), (8, 15), (4, 10)], GOLD); polygon(c, [(8, 8), (10, 10), (8, 13), (6, 10)], CYAN); c.set(7, 9, CYAN_L)
    return _done(c)


def potion():
    c = _new()
    c.fill_rect(6, 1, 4, 2, BROWN); c.fill_rect(6, 3, 4, 3, SILV_L)
    polygon(c, [(6, 6), (10, 6), (14, 14), (2, 14)], SILV_L); polygon(c, [(5, 10), (11, 10), (13, 13.5), (3, 13.5)], GREEN)
    c.set(6, 12, GREEN_L); c.set(9, 11, GREEN_L)
    return _done(c)


def key():
    c = _new()
    ring(c, 5, 5, 3.8, 1.8, SILV); line(c, 7, 7, 13, 13, SILV, 2); c.fill_rect(11, 13, 2, 2, SILV); c.fill_rect(9, 11, 2, 2, SILV_D)
    c.set(3, 3, SILV_L)
    return _done(c)


# ---------- map ----------
def node_fight():
    return intent_multi()


def node_elite():
    c = _new(); _skull(c, WHITE, SILV, RED, cy=8)
    polygon(c, [(1, 1), (4.5, 3), (4, 7), (2, 5)], RED_D); polygon(c, [(15, 1), (11.5, 3), (12, 7), (14, 5)], RED_D)
    return _done(c)


def node_boss():
    c = _new()
    polygon(c, [(2, 12), (2, 4), (5.5, 8), (8, 2.5), (10.5, 8), (14, 4), (14, 12)], GOLD)
    c.fill_rect(2, 12, 12, 2, GOLD_D); c.fill_rect(7, 10, 2, 2, RED); c.fill_rect(4, 10, 1, 1, CYAN); c.fill_rect(11, 10, 1, 1, CYAN)
    c.set(3, 6, GOLD_L); c.set(8, 4, GOLD_L)
    return _done(c)


def node_rest():
    c = _new()
    _flame(c, 8, 12, 0.85)
    line(c, 2, 14, 13, 11, BROWN, 2); line(c, 13, 14, 2, 11, BROWN_D, 2)
    return _done(c)


def node_shop():
    c = _new()
    polygon(c, [(4, 6), (12, 6), (14, 14), (2, 14)], BROWN); polygon(c, [(5, 3), (11, 3), (12, 6), (4, 6)], BROWN_L)
    c.fill_rect(5, 5, 6, 1, BROWN_D); c.disc(8, 10, 2.6, GOLD); c.fill_rect(8, 9, 1, 3, GOLD_D)
    return _done(c)


def node_event():
    c = _new()
    c.fill_rect(3, 2, 10, 12, PAPER); c.fill_rect(2, 1, 12, 2, PAPER_D); c.fill_rect(2, 13, 12, 2, PAPER_D)
    c.fill_rect(6, 4, 4, 1, PURP); c.fill_rect(9, 5, 2, 2, PURP); c.fill_rect(7, 7, 2, 2, PURP); c.fill_rect(7, 10, 2, 2, PURP)
    return _done(c)


def node_treasure():
    c = _new()
    c.fill_rect(2, 6, 12, 8, BROWN); polygon(c, [(2, 6), (4, 3), (12, 3), (14, 6)], BROWN_L)
    c.fill_rect(2, 6, 12, 1, GOLD_D); c.fill_rect(2, 13, 12, 1, BROWN_D)
    c.fill_rect(7, 5, 2, 4, GOLD); c.set(7, 7, OUT); c.fill_rect(3, 8, 1, 4, GOLD_D); c.fill_rect(12, 8, 1, 4, GOLD_D)
    return _done(c)


def node_start():
    c = _new()
    c.fill_rect(3, 1, 2, 14, SILV_D); polygon(c, [(5, 2), (14, 4.5), (5, 8)], GREEN); c.fill_rect(5, 3, 3, 1, GREEN_L)
    c.fill_rect(1, 14, 6, 1, DARK)
    return _done(c)


def node_locked():
    c = _new()
    ring(c, 8, 6, 4, 2.2, SILV, 0, 180); c.fill_rect(4, 6, 2, 2, SILV); c.fill_rect(10, 6, 2, 2, SILV)
    c.fill_rect(3, 7, 10, 8, DARK); c.fill_rect(3, 7, 10, 1, GREY); c.fill_rect(7, 10, 2, 3, OUT)
    return _done(c)


def node_forge():
    c = _new()
    c.fill_rect(2, 6, 11, 3, SILV); c.fill_rect(2, 6, 11, 1, SILV_L); polygon(c, [(13, 6), (15.5, 6), (13, 9)], SILV_D)
    c.fill_rect(5, 9, 5, 3, SILV_D); c.fill_rect(3, 12, 9, 2, SILV_D); c.fill_rect(3, 12, 9, 1, SILV)
    c.set(6, 3, ORG_L); c.set(9, 2, GOLD_L); c.set(11, 4, ORG)
    return _done(c)


# ---------- actions ----------
def upgrade():
    c = _new()
    line(c, 3, 13, 9, 7, BROWN, 2)
    polygon(c, rotate_pts([(6, 2), (13, 2), (13, 7), (6, 7)], 45, 9.5, 4.5), SILV)
    c.fill_rect(12, 10, 1, 3, GOLD_L); c.fill_rect(11, 11, 3, 1, GOLD_L); c.set(14, 14, GOLD); c.set(10, 14, GOLD)
    return _done(c)


def remove():
    c = _new(); _card(c, 4, 2, 9, 12, face=GREY, edge=DARK)
    line(c, 3, 3, 13, 13, RED, 2); line(c, 13, 3, 3, 13, RED, 2)
    return _done(c)


def transform():
    c = _new()
    ring(c, 8, 8, 6.4, 4.6, CYAN, 20, 170); ring(c, 8, 8, 6.4, 4.6, PURP, 200, 350)
    polygon(c, [(11, 1.5), (15.5, 4), (11, 7)], CYAN); polygon(c, [(5, 9), (0.5, 12), (5, 14.5)], PURP)
    return _done(c)


def duplicate():
    c = _new(); _card(c, 2, 2, 8, 10, face=PAPER_D, edge=BROWN); _card(c, 6, 5, 8, 10, pip=BLUE); return _done(c)


def end_turn():
    c = _new()
    c.fill_rect(3, 1, 10, 2, GOLD_D); c.fill_rect(3, 13, 10, 2, GOLD_D)
    polygon(c, [(4, 3), (12, 3), (8, 8)], SILV_L); polygon(c, [(8, 8), (12, 13), (4, 13)], SILV_L)
    polygon(c, [(8, 10.5), (11, 13), (5, 13)], ORG); c.fill_rect(7, 6, 2, 4, ORG)
    return _done(c)


def heal():
    c = _new(); c.disc(8, 8, 6.8, WHITE); c.fill_rect(6, 3, 4, 10, RED); c.fill_rect(3, 6, 10, 4, RED); c.fill_rect(6, 3, 1, 3, RED_L); return _done(c)


def max_hp():
    c = _new(); _heart(c, RED, RED_L, cx=7, cy=7.5, s=0.85); _arrow_up(c, 13, 1, GREEN_L, hgt=7, w=1); return _done(c)


def dice():
    c = _new()
    c.fill_rect(2, 2, 12, 12, WHITE); c.fill_rect(2, 13, 12, 1, SILV); c.fill_rect(13, 2, 1, 12, SILV)
    for x, y in ((4, 4), (10, 4), (7, 7), (4, 10), (10, 10)):
        c.fill_rect(x, y, 2, 2, OUT)
    return _done(c)


def target():
    c = _new()
    ring(c, 8, 8, 6.8, 5.6, WHITE); ring(c, 8, 8, 3.6, 2.6, RED); c.fill_rect(7, 7, 2, 2, RED)
    return _done(c)


def swap():
    c = _new()
    c.fill_rect(3, 4, 9, 2, CYAN); polygon(c, [(11, 1.5), (15, 5), (11, 8.5)], CYAN)
    c.fill_rect(4, 10, 9, 2, ORG); polygon(c, [(5, 7.5), (1, 11), (5, 14.5)], ORG)
    return _done(c)


def turn():
    c = _new()
    ring(c, 8, 8, 6.6, 4.8, GOLD, 40, 320); polygon(c, [(10, 0.5), (15.5, 3.5), (10.5, 7)], GOLD)
    c.fill_rect(7, 5, 2, 4, WHITE); c.fill_rect(7, 8, 4, 2, WHITE)
    return _done(c)


GROUPS: dict[str, dict] = {
    "intent": {"attack": intent_attack, "multi_attack": intent_multi, "heavy_attack": intent_heavy, "defend": intent_defend, "buff": intent_buff,
               "debuff": intent_debuff, "special": intent_special, "unknown": intent_unknown, "sleep": intent_sleep, "flee": intent_flee,
               "summon": intent_summon, "stoke": intent_stoke},
    "status": {"strength": strength, "weak": weak, "vulnerable": vulnerable, "frail": frail, "burn": burn, "poison": poison, "bleed": bleed,
               "frost": frost, "shock": shock, "stun": stun, "thorns": thorns, "regen": regen, "block": block, "dodge": dodge, "focus": focus,
               "blind": blind, "curse": curse, "haste": haste, "slow": slow, "heat": heat, "cold": cold, "barrier": barrier, "mark": mark},
    "resource": {"energy": energy, "ember": ember, "gold": gold, "gem": gem, "card": card, "draw_pile": draw_pile, "discard_pile": discard_pile,
                 "exhaust_pile": exhaust_pile, "deck": deck, "hand": hand, "relic": relic, "potion": potion, "key": key},
    "map": {"fight": node_fight, "elite": node_elite, "boss": node_boss, "rest": node_rest, "shop": node_shop, "event": node_event,
            "treasure": node_treasure, "start": node_start, "locked": node_locked, "forge": node_forge},
    "action": {"upgrade": upgrade, "remove": remove, "transform": transform, "duplicate": duplicate, "end_turn": end_turn, "heal": heal,
               "max_hp": max_hp, "dice": dice, "target": target, "swap": swap, "turn": turn},
}


def all_icons() -> dict[str, Canvas]:
    return {f"{g}_{name}": fn() for g, items in GROUPS.items() for name, fn in items.items()}
