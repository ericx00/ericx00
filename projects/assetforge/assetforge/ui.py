"""Pixel UI kit: 5 themes x ~60 components, 9-slice ready, plus composed mock-up screens."""
from __future__ import annotations

from .draw import line, nine_slice, polygon
from .font import draw_text, text_width
from .png import CLEAR, Canvas, RGBA, hex_to_rgba, shade

THEMES: dict[str, dict[str, str]] = {
    "parchment": {"outline": "#2b1d14", "base": "#c89f6a", "light": "#ecd3a3", "dark": "#8a6239", "accent": "#5b8c5a", "danger": "#b0413e", "text": "#2b1d14", "bg": "#3b2a1e"},
    "steel": {"outline": "#101318", "base": "#4a5566", "light": "#7d8ba1", "dark": "#2c333f", "accent": "#3fa7d6", "danger": "#e4572e", "text": "#e8ecf2", "bg": "#161a22"},
    "candy": {"outline": "#2d1b3d", "base": "#ff7eb6", "light": "#ffc2dd", "dark": "#c2477f", "accent": "#7bdff2", "danger": "#ff5964", "text": "#2d1b3d", "bg": "#3d2552"},
    "emerald": {"outline": "#0d1a14", "base": "#2f5d46", "light": "#4f8f6a", "dark": "#1c3a2b", "accent": "#e3b341", "danger": "#c8453d", "text": "#f1ead2", "bg": "#0f2018"},
    "neon": {"outline": "#05060c", "base": "#1b1f3a", "light": "#33407a", "dark": "#10132a", "accent": "#26e0ff", "danger": "#ff3d81", "text": "#e8f6ff", "bg": "#07081a"},
}
BAR_COLOURS = {"health": "#d83a46", "mana": "#3f7ee8", "stamina": "#4fbf5f", "xp": "#f2b33d"}
BUTTON_SIZES = {"s": (32, 14), "m": (48, 16), "l": (64, 20)}

# 9-slice border (pixels at 1x) for stretchable elements; others are fixed-size sprites.
NINE_SLICE = {"button": 4, "panel": 6, "dialog": (6, 14, 6, 6), "tooltip": 4, "tab": 3, "slot": 4, "bar_frame": 3, "input": 3,
              "dropdown": 3, "banner": 6, "scroll_track": 2, "slider_track": 2}


def theme(name: str) -> dict[str, RGBA]:
    return {k: hex_to_rgba(v) for k, v in THEMES[name].items()}


def _grey(col: RGBA) -> RGBA:
    v = (col[0] * 30 + col[1] * 59 + col[2] * 11) // 100
    return (v, v, v, col[3])


def bevel(c: Canvas, x: int, y: int, w: int, h: int, base: RGBA, light: RGBA, dark: RGBA, outline: RGBA, inset: bool = False) -> None:
    c.fill_rect(x + 1, y + 1, w - 2, h - 2, base)
    top, bottom = (dark, light) if inset else (light, dark)
    c.fill_rect(x + 1, y + 1, w - 2, 1, top)
    c.fill_rect(x + 1, y + 1, 1, h - 2, top)
    c.fill_rect(x + 1, y + h - 2, w - 2, 1, bottom)
    c.fill_rect(x + w - 2, y + 1, 1, h - 2, bottom)
    c.fill_rect(x + 1, y, w - 2, 1, outline)
    c.fill_rect(x + 1, y + h - 1, w - 2, 1, outline)
    c.fill_rect(x, y + 1, 1, h - 2, outline)
    c.fill_rect(x + w - 1, y + 1, 1, h - 2, outline)


def button(name: str, state: str = "normal", w: int = 48, h: int = 16) -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    if state == "normal":
        bevel(c, 0, 0, w, h - 1, t["base"], t["light"], t["dark"], t["outline"])
        c.fill_rect(1, h - 1, w - 2, 1, t["outline"])
    elif state == "hover":
        bevel(c, 0, 0, w, h - 1, shade(t["base"], 1.15), shade(t["light"], 1.15), t["base"], t["outline"])
        c.fill_rect(1, h - 1, w - 2, 1, t["outline"])
    elif state == "pressed":
        bevel(c, 0, 1, w, h - 1, t["dark"], t["base"], shade(t["dark"], 0.7), t["outline"], inset=True)
    elif state == "disabled":
        bevel(c, 0, 0, w, h - 1, _grey(t["base"]), _grey(t["light"]), _grey(t["dark"]), _grey(t["outline"]))
        c.fill_rect(1, h - 1, w - 2, 1, _grey(t["outline"]))
    else:
        raise ValueError(f"unknown state {state}")
    return c


def panel(name: str, w: int = 48, h: int = 48, style: str = "framed") -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    if style == "inset":
        bevel(c, 0, 0, w, h, t["dark"], shade(t["dark"], 0.7), t["base"], t["outline"], inset=True)
        return c
    bevel(c, 0, 0, w, h, t["base"], t["light"], t["dark"], t["outline"])
    if style == "framed":
        c.rect(3, 3, w - 6, h - 6, shade(t["dark"], 0.9))
        for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
            c.set(x, y, t["outline"])
    return c


def dialog(name: str, w: int = 96, h: int = 64) -> Canvas:
    """Panel with a title strip (stretch it: the 6px border keeps the strip intact horizontally)."""
    t = theme(name)
    c = panel(name, w, h, "plain")
    c.fill_rect(2, 2, w - 4, 10, t["dark"])
    c.fill_rect(2, 12, w - 4, 1, t["outline"])
    c.fill_rect(2, 2, w - 4, 1, shade(t["dark"], 1.3))
    return c


def tooltip(name: str, w: int = 40, h: int = 20) -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    bevel(c, 0, 0, w, h - 4, t["light"], shade(t["light"], 1.2), t["base"], t["outline"])
    polygon(c, [(w / 2 - 4, h - 5), (w / 2 + 4, h - 5), (w / 2, h - 1)], t["outline"])
    polygon(c, [(w / 2 - 2.5, h - 5.5), (w / 2 + 2.5, h - 5.5), (w / 2, h - 2.5)], t["light"])
    return c


def banner(name: str, w: int = 64, h: int = 16) -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    for side in (0, 1):  # ribbon tails
        x0 = 0 if side == 0 else w - 8
        pts = [(x0, 4), (x0 + 8, 4), (x0 + 8, h), (x0, h)]
        polygon(c, pts, t["outline"])
        notch = [(x0, h), (x0 + 3, h - 6), (x0, 4)] if side == 0 else [(x0 + 8, h), (x0 + 5, h - 6), (x0 + 8, 4)]
        polygon(c, [(x0 + 1, 5), (x0 + 7, 5), (x0 + 7, h - 1), (x0 + 1, h - 1)], t["dark"])
        polygon(c, notch, CLEAR)
    bevel(c, 4, 0, w - 8, h - 3, t["accent"], shade(t["accent"], 1.3), shade(t["accent"], 0.7), t["outline"])
    return c


def tab(name: str, active: bool, w: int = 32, h: int = 14) -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    body = t["base"] if active else t["dark"]
    yy = 0 if active else 2
    c.fill_rect(1, yy, w - 2, 1, t["outline"])
    c.fill_rect(0, yy + 1, 1, h - yy - 1, t["outline"])
    c.fill_rect(w - 1, yy + 1, 1, h - yy - 1, t["outline"])
    c.fill_rect(1, yy + 1, w - 2, h - yy - 1, body)
    c.fill_rect(1, yy + 1, w - 2, 1, shade(body, 1.3))
    if not active:
        c.fill_rect(0, h - 1, w, 1, t["outline"])
    return c


def slot(name: str, state: str = "normal", size: int = 20) -> Canvas:
    t = theme(name)
    c = Canvas(size, size)
    bevel(c, 0, 0, size, size, shade(t["dark"], 0.85), shade(t["dark"], 0.6), t["base"], t["outline"], inset=True)
    if state == "hover":
        c.rect(1, 1, size - 2, size - 2, t["light"])
    elif state == "selected":
        c.rect(1, 1, size - 2, size - 2, t["accent"])
        c.rect(2, 2, size - 4, size - 4, shade(t["accent"], 0.7))
    elif state == "disabled":
        for i in range(2, size - 2):
            c.set(i, i, t["outline"])
    return c


def bar_frame(name: str, w: int = 48, h: int = 8) -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    bevel(c, 0, 0, w, h, shade(t["dark"], 0.6), shade(t["dark"], 0.45), t["dark"], t["outline"], inset=True)
    return c


def bar_fill(kind: str, w: int = 44, h: int = 4) -> Canvas:
    col = hex_to_rgba(BAR_COLOURS[kind])
    c = Canvas(w, h, col)
    c.fill_rect(0, 0, w, 1, shade(col, 1.4))
    c.fill_rect(0, h - 1, w, 1, shade(col, 0.75))
    return c


def bar(name: str, fill: float, kind: str = "health", w: int = 48, h: int = 8) -> Canvas:
    c = bar_frame(name, w, h)
    inner = w - 4
    n = int(round(inner * max(0.0, min(1.0, fill))))
    if n:
        c.blit(bar_fill(kind, n, h - 4), 2, 2)
    return c


def checkbox(name: str, checked: bool, hover: bool = False) -> Canvas:
    t = theme(name)
    c = Canvas(12, 12)
    face = shade(t["light"], 1.15) if hover else t["light"]
    bevel(c, 0, 0, 12, 12, face, shade(face, 1.2), t["base"], t["outline"], inset=True)
    if checked:
        for x, y in ((3, 6), (4, 7), (5, 8), (6, 7), (7, 6), (8, 5), (9, 4)):
            c.set(x, y, t["accent"]); c.set(x, y - 1, t["accent"])
    return c


def radio(name: str, on: bool, hover: bool = False) -> Canvas:
    t = theme(name)
    c = Canvas(12, 12)
    c.disc(6, 6, 6, t["outline"])
    c.disc(6, 6, 5, shade(t["light"], 1.15) if hover else t["light"])
    c.disc(6, 6.6, 4.2, shade(t["light"], 0.9))
    if on:
        c.disc(6, 6, 2.6, t["accent"])
    return c


def toggle(name: str, on: bool) -> Canvas:
    t = theme(name)
    c = Canvas(22, 12)
    track = t["accent"] if on else t["dark"]
    c.disc(6, 6, 6, t["outline"]); c.disc(16, 6, 6, t["outline"]); c.fill_rect(6, 0, 10, 12, t["outline"])
    c.disc(6, 6, 5, track); c.disc(16, 6, 5, track); c.fill_rect(6, 1, 10, 10, track)
    kx = 16 if on else 6
    c.disc(kx, 6, 4, t["outline"]); c.disc(kx, 6, 3.2, t["light"]); c.set(kx - 1, 4, shade(t["light"], 1.4))
    return c


def slider_track(name: str, w: int = 48, filled: bool = False) -> Canvas:
    t = theme(name)
    c = Canvas(w, 6)
    col = t["accent"] if filled else shade(t["dark"], 0.7)
    bevel(c, 0, 0, w, 6, col, shade(col, 1.3), shade(col, 0.7), t["outline"])
    return c


def slider_knob(name: str) -> Canvas:
    t = theme(name)
    c = Canvas(7, 12)
    bevel(c, 0, 0, 7, 12, t["base"], t["light"], t["dark"], t["outline"])
    c.fill_rect(3, 3, 1, 6, t["dark"])
    return c


def slider(name: str, value: float, w: int = 48) -> Canvas:
    c = Canvas(w, 12)
    c.blit(slider_track(name, w), 0, 3)
    kx = int(round((w - 7) * max(0.0, min(1.0, value))))
    if kx > 2:
        c.blit(slider_track(name, kx + 3, True), 0, 3)
    c.blit(slider_knob(name), kx, 0)
    return c


def scroll_track(name: str, h: int = 48) -> Canvas:
    t = theme(name)
    c = Canvas(8, h)
    bevel(c, 0, 0, 8, h, shade(t["dark"], 0.7), shade(t["dark"], 0.5), t["dark"], t["outline"], inset=True)
    return c


def scroll_thumb(name: str, h: int = 16) -> Canvas:
    t = theme(name)
    c = Canvas(8, h)
    bevel(c, 0, 0, 8, h, t["base"], t["light"], t["dark"], t["outline"])
    for y in (h // 2 - 2, h // 2, h // 2 + 2):
        c.fill_rect(2, y, 4, 1, t["dark"])
    return c


def scroll_arrow(name: str, up: bool) -> Canvas:
    t = theme(name)
    c = Canvas(8, 8)
    bevel(c, 0, 0, 8, 8, t["base"], t["light"], t["dark"], t["outline"])
    pts = [(2, 5), (6, 5), (4, 2.5)] if up else [(2, 3), (6, 3), (4, 5.5)]
    polygon(c, pts, t["outline"])
    return c


def text_input(name: str, focused: bool, w: int = 64, h: int = 14) -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    bevel(c, 0, 0, w, h, shade(t["light"], 1.25), shade(t["light"], 1.4), t["light"], t["outline"], inset=True)
    if focused:
        c.rect(0, 0, w, h, t["accent"])
        c.fill_rect(4, 3, 1, h - 6, t["outline"])  # caret
    return c


def dropdown(name: str, w: int = 64, h: int = 14) -> Canvas:
    t = theme(name)
    c = Canvas(w, h)
    bevel(c, 0, 0, w, h, t["base"], t["light"], t["dark"], t["outline"])
    c.fill_rect(w - 13, 2, 1, h - 4, t["dark"])
    polygon(c, [(w - 10, 5), (w - 4, 5), (w - 7, 9)], t["outline"])
    return c


def close_button(name: str, hover: bool = False) -> Canvas:
    t = theme(name)
    c = Canvas(11, 11)
    face = shade(t["danger"], 1.2) if hover else t["danger"]
    bevel(c, 0, 0, 11, 11, face, shade(face, 1.3), shade(face, 0.7), t["outline"])
    line(c, 3, 3, 7, 7, t["outline"]); line(c, 7, 3, 3, 7, t["outline"])
    return c


def divider(name: str, w: int = 48) -> Canvas:
    t = theme(name)
    c = Canvas(w, 3)
    c.fill_rect(2, 0, w - 4, 1, t["outline"]); c.fill_rect(2, 1, w - 4, 1, t["light"])
    c.fill_rect(0, 1, 2, 1, t["outline"]); c.fill_rect(w - 2, 1, 2, 1, t["outline"])
    return c


def _cursor(rows: list[str], t: dict[str, RGBA]) -> Canvas:
    c = Canvas(len(rows[0]), len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "X":
                c.set(x, y, t["outline"])
            elif ch == "o":
                c.set(x, y, t["light"])
            elif ch == "a":
                c.set(x, y, t["accent"])
    return c


def cursor(name: str, kind: str = "pointer") -> Canvas:
    t = theme(name)
    shapes = {
        "pointer": ["X.......", "XX......", "XoX.....", "XooX....", "XoooX...", "XooooX..", "XoooooX.", "XooXXXX.", "XoX.....", "XX......"],
        "hand": ["...XX.....", "..XooX....", "..XooX....", "..XooXXX..", "..XooXooXX", "XXXooXooXoX", "XooXoooooX", ".XooooooooX", "..XoooooooX", "...XooooooX", "....XXXXXX."],
        "crosshair": [".....X.....", ".....a.....", ".....a.....", ".....X.....", "...........", "Xaa.....aaX", "...........", ".....X.....", ".....a.....", ".....a.....", ".....X....."],
    }
    rows = shapes[kind]
    w = max(len(r) for r in rows)
    return _cursor([r.ljust(w, ".") for r in rows], t)


def components(name: str) -> dict[str, tuple[Canvas, int | None]]:
    """Every element of one theme: name -> (image, 9-slice border or None)."""
    out: dict[str, tuple[Canvas, int | None]] = {}
    for size, (w, h) in BUTTON_SIZES.items():
        for st in ("normal", "hover", "pressed", "disabled"):
            out[f"button_{size}_{st}"] = (button(name, st, w, h), NINE_SLICE["button"])
    for st in ("normal", "hover", "pressed", "disabled"):
        out[f"button_icon_{st}"] = (button(name, st, 16, 16), NINE_SLICE["button"])
    out["panel_framed"] = (panel(name, 48, 48, "framed"), NINE_SLICE["panel"])
    out["panel_plain"] = (panel(name, 48, 48, "plain"), NINE_SLICE["panel"])
    out["panel_inset"] = (panel(name, 48, 48, "inset"), NINE_SLICE["panel"])
    out["dialog"] = (dialog(name), NINE_SLICE["dialog"])
    out["tooltip"] = (tooltip(name), None)
    out["banner"] = (banner(name), NINE_SLICE["banner"])
    out["tab_active"] = (tab(name, True), NINE_SLICE["tab"])
    out["tab_inactive"] = (tab(name, False), NINE_SLICE["tab"])
    for st in ("normal", "hover", "selected", "disabled"):
        out[f"slot_{st}"] = (slot(name, st), NINE_SLICE["slot"])
    out["bar_frame"] = (bar_frame(name), NINE_SLICE["bar_frame"])
    for kind in BAR_COLOURS:
        out[f"bar_fill_{kind}"] = (bar_fill(kind), None)
    for pct in (0, 25, 50, 75, 100):
        out[f"bar_health_{pct}"] = (bar(name, pct / 100, "health"), None)
    out["slider_track"] = (slider_track(name), NINE_SLICE["slider_track"])
    out["slider_track_filled"] = (slider_track(name, 48, True), NINE_SLICE["slider_track"])
    out["slider_knob"] = (slider_knob(name), None)
    out["slider_example_50"] = (slider(name, 0.5), None)
    for on in (False, True):
        tag = "on" if on else "off"
        out[f"checkbox_{tag}"] = (checkbox(name, on), None)
        out[f"checkbox_{tag}_hover"] = (checkbox(name, on, True), None)
        out[f"radio_{tag}"] = (radio(name, on), None)
        out[f"radio_{tag}_hover"] = (radio(name, on, True), None)
        out[f"toggle_{tag}"] = (toggle(name, on), None)
    out["scroll_track"] = (scroll_track(name), NINE_SLICE["scroll_track"])
    out["scroll_thumb"] = (scroll_thumb(name), None)
    out["scroll_arrow_up"] = (scroll_arrow(name, True), None)
    out["scroll_arrow_down"] = (scroll_arrow(name, False), None)
    out["input"] = (text_input(name, False), NINE_SLICE["input"])
    out["input_focused"] = (text_input(name, True), NINE_SLICE["input"])
    out["dropdown"] = (dropdown(name), None)
    out["close"] = (close_button(name), None)
    out["close_hover"] = (close_button(name, True), None)
    out["divider"] = (divider(name), None)
    for kind in ("pointer", "hand", "crosshair"):
        out[f"cursor_{kind}"] = (cursor(name, kind), None)
    return out


def text_button(name: str, label: str, state: str = "normal", size: str = "m", min_w: int = 0) -> Canvas:
    t = theme(name)
    bw, bh = BUTTON_SIZES[size]
    w = max(bw, min_w, text_width(label) + 14)
    c = nine_slice(button(name, state, bw, bh), w, bh, NINE_SLICE["button"])
    dy = 1 if state == "pressed" else 0
    col = t["text"] if state != "disabled" else _grey(t["text"])
    draw_text(c, (w - text_width(label)) // 2, (bh - 1 - 7) // 2 + dy, label, col)
    return c


def mockup(name: str) -> Canvas:
    """A 320x180 'options screen' composed only from kit parts: the store image buyers judge."""
    from .icons import ICONS
    t = theme(name)
    W, Hh = 320, 180
    c = Canvas(W, Hh, t["bg"])
    for y in range(Hh):  # dithered vertical gradient
        for x in range(W):
            if (x + y) % 2 == 0 and y > Hh * 0.55:
                c.set(x, y, shade(t["bg"], 1.35))
            elif (x * 7 + y * 3) % 97 == 0 and y < Hh * 0.5:
                c.set(x, y, shade(t["bg"], 1.9))
    ink = t["text"]
    # HUD
    hud = nine_slice(panel(name, 48, 48, "plain"), 104, 40, 6)
    c.blit(hud, 6, 6)
    c.blit(ICONS["heart"](), 10, 9); c.blit(bar(name, 0.75, "health", 70, 8), 30, 13)
    c.blit(ICONS["potion_blue"](), 10, 25); c.blit(bar(name, 0.45, "mana", 70, 8), 30, 29)
    c.blit(ICONS["coin"](), W - 70, 8)
    draw_text(c, W - 50, 13, "1250", hex_to_rgba("#ffe08a"), shadow=t["outline"])
    # Dialog
    dw, dh, dx, dy = 168, 120, 76, 34
    c.blit(nine_slice(dialog(name), dw, dh, NINE_SLICE["dialog"]), dx, dy)
    title_ink = hex_to_rgba("#ffffff") if sum(t["dark"][:3]) < 400 else t["outline"]
    draw_text(c, dx + (dw - text_width("OPTIONS")) // 2, dy + 4, "OPTIONS", title_ink)
    c.blit(close_button(name), dx + dw - 14, dy + 2)
    body_ink = ink if sum(t["base"][:3]) < 400 else t["outline"]
    rows = [("MUSIC", slider(name, 0.7, 70)), ("SOUND", slider(name, 0.4, 70))]
    yy = dy + 20
    for label, widget in rows:
        draw_text(c, dx + 10, yy + 3, label, body_ink); c.blit(widget, dx + 86, yy); yy += 16
    draw_text(c, dx + 10, yy + 3, "FULLSCREEN", body_ink); c.blit(checkbox(name, True), dx + 86, yy + 1); yy += 16
    draw_text(c, dx + 10, yy + 3, "VSYNC", body_ink); c.blit(toggle(name, True), dx + 86, yy + 1); yy += 16
    c.blit(divider(name, dw - 20), dx + 10, yy + 2)
    c.blit(text_button(name, "BACK", "normal", "m", 60), dx + 14, dy + dh - 24)
    c.blit(text_button(name, "APPLY", "hover", "m", 60), dx + dw - 74, dy + dh - 24)
    # Inventory bar
    items = ["sword", "shield", "potion_red", "key", "gem", "map", "bag", None]
    sx = (W - len(items) * 22) // 2
    for i, it in enumerate(items):
        st = "selected" if i == 0 else "normal"
        c.blit(slot(name, st), sx + i * 22, Hh - 26)
        if it:
            c.blit(ICONS[it](), sx + i * 22 + 2, Hh - 24)
    c.blit(cursor(name, "pointer"), dx + dw - 50, dy + dh - 14)
    return c
