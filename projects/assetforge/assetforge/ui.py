"""Pixel UI kit: 9-slice buttons (4 states), panels, bars, checkboxes, slider, cursor."""
from __future__ import annotations

from .png import Canvas, RGBA, hex_to_rgba, shade

THEMES: dict[str, dict[str, str]] = {
    "parchment": {"outline": "#2b1d14", "base": "#c89f6a", "light": "#ecd3a3", "dark": "#8a6239", "accent": "#5b8c5a", "danger": "#b0413e", "text": "#2b1d14"},
    "steel": {"outline": "#101318", "base": "#4a5566", "light": "#7d8ba1", "dark": "#2c333f", "accent": "#3fa7d6", "danger": "#e4572e", "text": "#e8ecf2"},
    "candy": {"outline": "#2d1b3d", "base": "#ff7eb6", "light": "#ffc2dd", "dark": "#c2477f", "accent": "#7bdff2", "danger": "#ff5964", "text": "#2d1b3d"},
}

# 9-slice margins (pixels at 1x) that engines need: Unity sprite border, Godot NinePatchRect, CSS border-image.
NINE_SLICE = {"button": 4, "panel": 6, "bar_frame": 3}


def _theme(name: str) -> dict[str, RGBA]:
    return {k: hex_to_rgba(v) for k, v in THEMES[name].items()}


def _bevel_box(c: Canvas, x: int, y: int, w: int, h: int, base: RGBA, light: RGBA, dark: RGBA, outline: RGBA, inset: bool = False) -> None:
    c.fill_rect(x + 1, y + 1, w - 2, h - 2, base)
    top, bottom = (dark, light) if inset else (light, dark)
    c.fill_rect(x + 1, y + 1, w - 2, 1, top)
    c.fill_rect(x + 1, y + 1, 1, h - 2, top)
    c.fill_rect(x + 1, y + h - 2, w - 2, 1, bottom)
    c.fill_rect(x + w - 2, y + 1, 1, h - 2, bottom)
    # rounded outline: skip the four corner pixels
    c.fill_rect(x + 1, y, w - 2, 1, outline)
    c.fill_rect(x + 1, y + h - 1, w - 2, 1, outline)
    c.fill_rect(x, y + 1, 1, h - 2, outline)
    c.fill_rect(x + w - 1, y + 1, 1, h - 2, outline)


def button(theme: str, state: str = "normal", w: int = 32, h: int = 16) -> Canvas:
    t = _theme(theme)
    c = Canvas(w, h)
    if state == "normal":
        _bevel_box(c, 0, 0, w, h - 1, t["base"], t["light"], t["dark"], t["outline"])
        c.fill_rect(1, h - 1, w - 2, 1, shade(t["outline"], 1.0))  # drop shadow
    elif state == "hover":
        _bevel_box(c, 0, 0, w, h - 1, shade(t["base"], 1.12), shade(t["light"], 1.1), t["base"], t["outline"])
        c.fill_rect(1, h - 1, w - 2, 1, t["outline"])
    elif state == "pressed":
        _bevel_box(c, 0, 1, w, h - 1, t["dark"], t["light"], shade(t["dark"], 0.7), t["outline"], inset=True)
    elif state == "disabled":
        grey = lambda col: (sum(col[:3]) // 3,) * 3 + (255,)  # noqa: E731
        _bevel_box(c, 0, 0, w, h - 1, grey(t["base"]), grey(t["light"]), grey(t["dark"]), grey(t["outline"]))
    else:
        raise ValueError(f"unknown state {state}")
    return c


def panel(theme: str, w: int = 48, h: int = 48) -> Canvas:
    t = _theme(theme)
    c = Canvas(w, h)
    _bevel_box(c, 0, 0, w, h, t["base"], t["light"], t["dark"], t["outline"])
    # inner frame line 3px in: gives the "framed" look while staying 9-slice safe
    c.rect(3, 3, w - 6, h - 6, shade(t["dark"], 0.9))
    for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        c.set(x, y, t["outline"])  # rivets
    return c


def bar(theme: str, fill: float, kind: str = "accent", w: int = 48, h: int = 8) -> Canvas:
    t = _theme(theme)
    c = Canvas(w, h)
    _bevel_box(c, 0, 0, w, h, t["dark"], shade(t["dark"], 0.7), t["dark"], t["outline"], inset=True)
    inner = w - 4
    filled = int(round(inner * max(0.0, min(1.0, fill))))
    if filled:
        col = t[kind]
        c.fill_rect(2, 2, filled, h - 4, col)
        c.fill_rect(2, 2, filled, 1, shade(col, 1.35))
    return c


def checkbox(theme: str, checked: bool) -> Canvas:
    t = _theme(theme)
    c = Canvas(12, 12)
    _bevel_box(c, 0, 0, 12, 12, t["light"], shade(t["light"], 1.2), t["base"], t["outline"], inset=True)
    if checked:
        for x, y in ((3, 6), (4, 7), (5, 8), (6, 7), (7, 6), (8, 5), (9, 4)):
            c.set(x, y, t["accent"])
            c.set(x, y - 1, t["accent"])
    return c


def slider(theme: str, value: float, w: int = 48) -> Canvas:
    t = _theme(theme)
    c = Canvas(w, 10)
    c.fill_rect(2, 4, w - 4, 2, t["outline"])
    kx = 2 + int(round((w - 9) * max(0.0, min(1.0, value))))
    c.fill_rect(2, 4, kx - 2, 2, t["accent"])
    _bevel_box(c, kx, 0, 6, 10, t["base"], t["light"], t["dark"], t["outline"])
    return c


def cursor(theme: str) -> Canvas:
    t = _theme(theme)
    rows = ["X.......", "XX......", "XoX.....", "XooX....", "XoooX...", "XooooX..", "XoooooX.", "XooXXXX.", "XoX.....", "XX......"]
    c = Canvas(8, 10)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "X":
                c.set(x, y, t["outline"])
            elif ch == "o":
                c.set(x, y, t["light"])
    return c
