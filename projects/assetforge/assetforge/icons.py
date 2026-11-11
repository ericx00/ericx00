"""36 original 16x16 pixel icons, built from shapes and given a 1px outline."""
from __future__ import annotations

from .draw import erase_disc, line, polygon, ring, rotate_pts
from .font import draw_text
from .png import Canvas, hex_to_rgba

H = hex_to_rgba
OUT = H("#1a1423")
RED, RED_L, RED_D = H("#e0484f"), H("#ff9aa0"), H("#a3283a")
GOLD, GOLD_L, GOLD_D = H("#f2b33d"), H("#ffe08a"), H("#b5761f")
SILV, SILV_L, SILV_D = H("#c9d1dc"), H("#ffffff"), H("#7d8794")
BLUE, BLUE_L, BLUE_D = H("#3f7ee8"), H("#9cc2ff"), H("#264f9e")
GREEN, GREEN_L, GREEN_D = H("#4fbf5f"), H("#a6eaae"), H("#2e7a3a")
BROWN, BROWN_L, BROWN_D = H("#8a5a34"), H("#c08a5a"), H("#5a3820")
PURP, PURP_L = H("#9b59d0"), H("#d2a8f5")
WHITE, GREY = H("#f4f4f4"), H("#8a8f99")
PAPER, PAPER_D = H("#e9d6a6"), H("#c2a56b")


def _new() -> Canvas:
    return Canvas(16, 16)


def _done(c: Canvas) -> Canvas:
    c.outline(OUT)
    return c


def heart(full=True):
    c = _new()
    col = RED if full else H("#4a4e5c")
    c.disc(5, 6, 3.6, col); c.disc(11, 6, 3.6, col)
    polygon(c, [(1.6, 7), (14.4, 7), (8, 14)], col)
    if full:
        c.fill_rect(4, 4, 2, 1, RED_L); c.set(3, 5, RED_L)
    else:
        c.fill_rect(4, 4, 2, 1, H("#6b7080")); c.set(3, 5, H("#6b7080"))
    return _done(c)


def star():
    c = _new()
    pts = []
    import math
    for i in range(10):
        r = 7 if i % 2 == 0 else 3
        a = math.radians(-90 + i * 36)
        pts.append((8 + r * math.cos(a), 8.5 + r * math.sin(a)))
    polygon(c, pts, GOLD)
    polygon(c, [(8, 2.5), (9.2, 6.5), (8, 7.5), (6.8, 6.5)], GOLD_L)
    return _done(c)


def coin():
    c = _new()
    c.disc(8, 8, 6.5, GOLD_D); c.disc(8, 8, 5.5, GOLD); ring(c, 8, 8, 4.4, 3.4, GOLD_D)
    c.fill_rect(7, 5, 2, 6, GOLD_D); c.fill_rect(5, 4, 2, 1, GOLD_L); c.set(4, 5, GOLD_L)
    return _done(c)


def gem():
    c = _new()
    polygon(c, [(3, 6), (6, 2.5), (10, 2.5), (13, 6), (8, 14)], BLUE)
    polygon(c, [(3, 6), (13, 6), (8, 14)], BLUE_D)
    polygon(c, [(6, 2.5), (10, 2.5), (9, 6), (7, 6)], BLUE_L)
    polygon(c, [(6, 6), (10, 6), (8, 12)], BLUE)
    return _done(c)


def sword():
    c = _new()
    line(c, 4, 11, 12, 3, SILV, 2); line(c, 5, 11, 12, 4, SILV_D, 1); line(c, 4, 10, 11, 3, SILV_L, 1)
    line(c, 3, 8, 7, 12, GOLD_D, 2)
    line(c, 2, 13, 4, 11, BROWN, 2)
    c.fill_rect(1, 13, 2, 2, GOLD)
    return _done(c)


def shield():
    c = _new()
    pts = [(2.5, 2.5), (13.5, 2.5), (13.5, 8), (8, 14.5), (2.5, 8)]
    polygon(c, pts, SILV_D)
    polygon(c, [(3.8, 3.8), (12.2, 3.8), (12.2, 7.6), (8, 12.6), (3.8, 7.6)], BLUE)
    c.fill_rect(7, 4, 2, 8, GOLD); c.fill_rect(4, 6, 8, 2, GOLD)
    return _done(c)


def potion(col=RED, hi=RED_L):
    c = _new()
    c.fill_rect(6, 1, 4, 2, BROWN); c.fill_rect(6, 3, 4, 3, SILV_L)
    c.disc(8, 10, 5, SILV_L); c.disc(8, 10.5, 4, col)
    c.fill_rect(5, 8, 2, 2, hi); c.fill_rect(6, 3, 1, 3, WHITE)
    return _done(c)


def key():
    c = _new()
    ring(c, 5, 6, 3.8, 1.6, GOLD)
    c.fill_rect(8, 5, 7, 2, GOLD); c.fill_rect(11, 7, 2, 3, GOLD); c.fill_rect(13, 7, 2, 2, GOLD)
    c.set(3, 4, GOLD_L); c.set(4, 3, GOLD_L)
    return _done(c)


def lock(open_=False):
    c = _new()
    if open_:
        ring(c, 5, 6, 4, 2, SILV, 0, 180); c.fill_rect(1, 6, 2, 2, SILV)
    else:
        ring(c, 8, 6, 4, 2, SILV, 0, 180); c.fill_rect(4, 6, 2, 2, SILV); c.fill_rect(10, 6, 2, 2, SILV)
    c.fill_rect(3, 7, 10, 8, GOLD); c.fill_rect(3, 7, 10, 1, GOLD_L)
    c.fill_rect(7, 10, 2, 3, BROWN_D)
    return _done(c)


def gear():
    c = _new()
    for k in range(8):
        polygon(c, rotate_pts([(7, 0.5), (9, 0.5), (9, 4), (7, 4)], k * 45, 8, 8), SILV_D)
    c.disc(8, 8, 5.2, SILV_D); c.disc(8, 8, 4.2, SILV); erase_disc(c, 8, 8, 1.8)
    return _done(c)


def home():
    c = _new()
    polygon(c, [(1, 8), (8, 1.5), (15, 8)], RED)
    c.fill_rect(3, 8, 10, 7, PAPER); c.fill_rect(7, 10, 3, 5, BROWN); c.fill_rect(4, 9, 2, 2, BLUE_L)
    return _done(c)


def play():
    c = _new(); polygon(c, [(4, 2), (13.5, 8), (4, 14)], GREEN); polygon(c, [(5, 4), (7, 5.2), (5, 6.5)], GREEN_L); return _done(c)


def pause():
    c = _new(); c.fill_rect(3, 2, 4, 12, SILV); c.fill_rect(9, 2, 4, 12, SILV); return _done(c)


def stop():
    c = _new(); c.fill_rect(3, 3, 10, 10, RED); c.fill_rect(4, 4, 3, 1, RED_L); return _done(c)


def _speaker(c):
    polygon(c, [(1.5, 6), (4.5, 6), (8.5, 2), (8.5, 14), (4.5, 10), (1.5, 10)], SILV)


def sound(on=True):
    c = _new(); _speaker(c)
    if on:
        ring(c, 8, 8, 4.4, 3.2, SILV, 300, 60); ring(c, 8, 8, 7, 5.8, SILV, 305, 55)
    else:
        line(c, 11, 6, 14, 9, RED, 1); line(c, 14, 6, 11, 9, RED, 1); line(c, 11, 7, 13, 9, RED, 1); line(c, 13, 6, 11, 8, RED, 1)
    return _done(c)


def music():
    c = _new()
    c.disc(4.5, 12, 2.4, PURP); c.disc(11.5, 10.5, 2.4, PURP)
    c.fill_rect(6, 3, 1, 9, PURP); c.fill_rect(13, 2, 1, 9, PURP); polygon(c, [(6, 2.5), (14, 1), (14, 4), (6, 5.5)], PURP)
    c.set(4, 11, PURP_L)
    return _done(c)


def arrow(direction="right"):
    c = _new()
    pts = [(2, 6), (8, 6), (8, 2), (14.5, 8), (8, 14), (8, 10), (2, 10)]
    ang = {"right": 0, "down": 90, "left": 180, "up": 270}[direction]
    polygon(c, rotate_pts(pts, ang, 8, 8), SILV)
    return _done(c)


def check():
    c = _new(); line(c, 3, 8, 6, 11, GREEN, 3); line(c, 6, 11, 12, 4, GREEN, 3); return _done(c)


def cross():
    c = _new(); line(c, 4, 4, 11, 11, RED, 3); line(c, 11, 4, 4, 11, RED, 3); return _done(c)


def plus():
    c = _new(); c.fill_rect(6, 2, 4, 12, GREEN); c.fill_rect(2, 6, 12, 4, GREEN); return _done(c)


def minus():
    c = _new(); c.fill_rect(2, 6, 12, 4, RED); return _done(c)


def _badge(col, ch):
    c = _new(); c.disc(8, 8, 7, col); draw_text(c, 6, 4, ch, WHITE); return _done(c)


def info():
    return _badge(BLUE, "I")


def question():
    return _badge(PURP, "?")


def warning():
    c = _new(); polygon(c, [(8, 1), (15, 14.5), (1, 14.5)], GOLD); draw_text(c, 6, 6, "!", OUT); return _done(c)


def trophy():
    c = _new()
    ring(c, 3.5, 5.5, 3, 1.6, GOLD_D); ring(c, 12.5, 5.5, 3, 1.6, GOLD_D)
    polygon(c, [(3.5, 1.5), (12.5, 1.5), (11.5, 7), (8, 10), (4.5, 7)], GOLD)
    c.fill_rect(7, 9, 2, 3, GOLD_D); c.fill_rect(4, 12, 8, 3, BROWN); c.fill_rect(5, 2, 1, 4, GOLD_L)
    return _done(c)


def bag():
    c = _new()
    c.disc(8, 10, 5.5, BROWN); polygon(c, [(5, 2), (11, 2), (9.5, 5), (6.5, 5)], BROWN)
    c.fill_rect(5, 5, 6, 1, GOLD); c.fill_rect(5, 8, 2, 2, BROWN_L)
    return _done(c)


def user():
    c = _new(); c.disc(8, 5, 3.4, SILV); c.disc(8, 16, 6.5, BLUE); return _done(c)


def chat():
    c = _new()
    c.fill_rect(1, 2, 14, 9, WHITE); polygon(c, [(4, 10), (8, 10), (4, 14)], WHITE)
    for x in (4, 7, 10):
        c.fill_rect(x, 6, 2, 2, GREY)
    return _done(c)


def clock():
    c = _new(); c.disc(8, 8, 7, SILV_D); c.disc(8, 8, 6, WHITE)
    c.fill_rect(7, 3, 2, 6, OUT); c.fill_rect(7, 7, 5, 2, OUT); return _done(c)


def search():
    c = _new(); ring(c, 6.5, 6.5, 5, 3, SILV); c.disc(6.5, 6.5, 3, BLUE_L); line(c, 10, 10, 14, 14, BROWN, 3); return _done(c)


def menu():
    c = _new()
    for y in (3, 7, 11):
        c.fill_rect(2, y, 12, 2, SILV)
    return _done(c)


def refresh():
    c = _new(); ring(c, 8, 8, 6.5, 4.3, GREEN, 60, 350); polygon(c, [(9, 0.5), (15, 3.5), (10, 7)], GREEN); return _done(c)


def map_():
    c = _new()
    polygon(c, [(1, 3), (5.5, 1.5), (10.5, 3), (15, 1.5), (15, 13), (10.5, 14.5), (5.5, 13), (1, 14.5)], PAPER)
    c.fill_rect(5, 2, 1, 12, PAPER_D); c.fill_rect(10, 3, 1, 12, PAPER_D)
    line(c, 3, 11, 7, 7, RED, 1); line(c, 11, 6, 13, 8, RED, 1); line(c, 13, 6, 11, 8, RED, 1)
    return _done(c)


def skull():
    c = _new()
    c.disc(8, 7, 6, WHITE); c.fill_rect(5, 11, 6, 4, WHITE)
    c.disc(5.5, 7.5, 1.8, OUT); c.disc(10.5, 7.5, 1.8, OUT); c.fill_rect(7, 10, 2, 2, OUT); c.fill_rect(6, 13, 1, 2, GREY); c.fill_rect(9, 13, 1, 2, GREY)
    return _done(c)


def flag():
    c = _new(); c.fill_rect(3, 1, 2, 15, BROWN); polygon(c, [(5, 2), (14, 4.5), (5, 8)], RED); return _done(c)


ICONS = {
    "heart": lambda: heart(True), "heart_empty": lambda: heart(False), "star": star, "coin": coin, "gem": gem,
    "sword": sword, "shield": shield, "potion_red": lambda: potion(RED, RED_L), "potion_blue": lambda: potion(BLUE, BLUE_L),
    "potion_green": lambda: potion(GREEN, GREEN_L), "key": key, "lock": lambda: lock(False), "unlock": lambda: lock(True),
    "gear": gear, "home": home, "play": play, "pause": pause, "stop": stop, "sound_on": lambda: sound(True),
    "sound_off": lambda: sound(False), "music": music, "arrow_right": lambda: arrow("right"), "arrow_left": lambda: arrow("left"),
    "arrow_up": lambda: arrow("up"), "arrow_down": lambda: arrow("down"), "check": check, "cross": cross, "plus": plus,
    "minus": minus, "info": info, "question": question, "warning": warning, "trophy": trophy, "bag": bag, "user": user,
    "chat": chat, "clock": clock, "search": search, "menu": menu, "refresh": refresh, "map": map_, "skull": skull, "flag": flag,
}
