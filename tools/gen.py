"""Generates the pixel-art SVGs used by the profile README.

  python tools/gen.py           -> all assets, sky uses Nairobi time + live weather
  python tools/gen.py --sky     -> only the header (used by the hourly Action)
  python tools/gen.py --at 13   -> force the Nairobi hour (preview day/night)
  python tools/gen.py --weather rain|storm|cloudy|clear|fog

Needs tools/ps2p.woff2 (Press Start 2P, OFL). Everything is plain SVG + CSS
animation, so GitHub renders it as an <img> (no JS runs there, which is why the
day/night switch happens in the Action, on Nairobi time).
"""
import argparse
import base64
import json
import math
import random
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
FONT = base64.b64encode((ROOT / "tools" / "ps2p.woff2").read_bytes()).decode()
EAT = timezone(timedelta(hours=3))  # Nairobi
LAT, LON = -1.2864, 36.8172

# palette (matches the ericx00 itch.io store theme)
BG, PANEL, EDGE = "#0b0d14", "#141826", "#2a3150"
ORANGE, YELLOW, CYAN, GREEN, PINK = "#ff7a2f", "#ffd23f", "#3ee6ff", "#5cff8a", "#ff4fa3"
WHITE, DIM, SHADOW = "#e8ecff", "#8a93b8", "#05060a"

FONT_CSS = (
    "@font-face{font-family:'PS2P';src:url(data:font/woff2;base64,%s) format('woff2');}"
    "text{font-family:'PS2P',monospace;}" % FONT
)


def svg(w, h, body, css="", label=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" shape-rendering="crispEdges" role="img" aria-label="{label}">'
        f"<style>{FONT_CSS}{css}</style>{body}</svg>"
    )


def sprite(rows, px, colors, x=0, y=0):
    out = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colors:
                out.append(f'<rect x="{x + i * px}" y="{y + j * px}" width="{px}" height="{px}" fill="{colors[ch]}"/>')
    return "".join(out)


def outlined(rows, px, fill, line, x=0, y=0):
    filled = {(i, j) for j, r in enumerate(rows) for i, c in enumerate(r) if c == "#"}
    edge = {(i + di, j + dj) for i, j in filled for di in (-1, 0, 1) for dj in (-1, 0, 1)} - filled
    out = [f'<rect x="{x + i * px}" y="{y + j * px}" width="{px}" height="{px}" fill="{line}"/>' for i, j in edge]
    out += [f'<rect x="{x + i * px}" y="{y + j * px}" width="{px}" height="{px}" fill="{fill}"/>' for i, j in filled]
    return "".join(out)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def disc(cx, cy, r, px, color_fn):
    """Pixel disc; color_fn(dx, dy, halfwidth) -> colour or None."""
    out = []
    for j in range(-r, r):
        for i in range(-r, r):
            dx, dy = i + 0.5, j + 0.5
            if dx * dx + dy * dy <= r * r:
                c = color_fn(dx, dy, math.sqrt(max(r * r - dy * dy, 0)))
                if c:
                    out.append(f'<rect x="{cx + i * px}" y="{cy + j * px}" width="{px}" height="{px}" fill="{c}"/>')
    return "".join(out)


# ---------------------------------------------------------------- sprites
KNIGHT_A = [
    "..kkkkkkkk..",
    ".kkkkkkkkkk.",
    "....kkkky...",
    "...ssssss.y.",
    "...sswsws.y.",
    "...ssssss...",
    "..aaaaaaaa..",
    ".aaoaaaaoaa.",
    ".aaoaaaaoaa.",
    "..aaaaaaaa..",
    "..bb....bb..",
    ".bb......bb.",
]
KNIGHT_B = KNIGHT_A[:10] + ["...bb..bb...", "...bb..bb..."]
KCOL = {"k": "#1b1e2e", "y": YELLOW, "s": "#c8cde0", "w": CYAN, "a": "#7d86b0", "o": ORANGE, "b": "#3a3f5c"}
SLIME_A = ["....gggg....", "..gggggggg..", ".gggwggwggg.", ".gggkggkggg.", "gggggggggggg", "gggggggggggg"]
SLIME_B = ["............", "...gggggg...", ".ggggwggwggg", "gggggkggkggg", "gggggggggggg", "gggggggggggg"]
SCOL = {"g": GREEN, "w": WHITE, "k": SHADOW}
COIN = [".yyy.", "yyYyy", "yyYyy", "yyYyy", ".yyy."]
CCOL = {"y": YELLOW, "Y": "#fff3b0"}
CLOUD = ["....wwww......", "..wwwwwwww.ww.", ".wwwwwwwwwwwww", "wwwwwwwwwwwwww", ".ssssssssssss."]
BIRD_A = ["b...b", ".b.b.", "..b.."]
BIRD_B = [".....", "bbbbb", "..b.."]

# ---------------------------------------------------------------- sky state
PHASES = {
    #        sky top    sky bottom  buildings  window-lit-chance  ground
    "night": ("#0b0d14", "#1d1442", "#161236", 0.35, ("#2b2f4a", "#252942")),
    "dawn": ("#2b2a6b", "#ff9a6b", "#2a2350", 0.15, ("#3a3150", "#332b48")),
    "day": ("#3d8bff", "#9fdcff", "#3a4f8f", 0.0, ("#3d6b3a", "#36603a")),
    "dusk": ("#2a1650", "#ff6b4a", "#24183f", 0.25, ("#3a2a44", "#33253d")),
}


def phase_for(hour):
    if 5 <= hour < 7:
        return "dawn"
    if 7 <= hour < 17:
        return "day"
    if 17 <= hour < 19:
        return "dusk"
    return "night"


def moon_phase(now):
    """0 = new, 0.5 = full."""
    ref = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    return ((now - ref).total_seconds() / 86400 / 29.530588853) % 1.0


def moon_name(p):
    names = ["NEW MOON", "WAXING CRESCENT", "FIRST QUARTER", "WAXING GIBBOUS",
             "FULL MOON", "WANING GIBBOUS", "LAST QUARTER", "WANING CRESCENT"]
    return names[int((p * 8) + 0.5) % 8]


def live_weather():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=weather_code,temperature_2m"
        with urllib.request.urlopen(url, timeout=10) as r:
            cur = json.load(r)["current"]
        code, temp = cur["weather_code"], round(cur["temperature_2m"])
    except Exception:
        return "clear", None
    if code >= 95:
        w = "storm"
    elif 51 <= code <= 82:
        w = "rain"
    elif code in (45, 48):
        w = "fog"
    elif code >= 2:
        w = "cloudy"
    else:
        w = "clear"
    return w, temp


# ---------------------------------------------------------------- header
def header(now, weather, temp):
    W, H = 960, 340
    hour = now.hour
    phase = phase_for(hour)
    top, bottom, bld, lit, ground = PHASES[phase]
    rnd = random.Random(7)
    b = [
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
    ]
    css = [
        "@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}.st{animation:tw 3s steps(3) infinite}",
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1s steps(1) infinite}",
        "@keyframes walk{from{transform:translateX(-80px)}to{transform:translateX(1040px)}}",
        ".walker{animation:walk 14s linear infinite}.chaser{animation:walk 14s linear infinite;animation-delay:-1.1s}",
        "@keyframes fa{0%,49%{opacity:1}50%,100%{opacity:0}}@keyframes fb{0%,49%{opacity:0}50%,100%{opacity:1}}",
        ".fa{animation:fa .4s steps(1) infinite}.fb{animation:fb .4s steps(1) infinite}",
        "@keyframes win{0%,100%{fill:#ffd23f}50%{fill:#2a2550}}.win{animation:win 6s steps(2) infinite}",
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}.coin{animation:bob 1.2s steps(2) infinite}",
        "@keyframes role{0%{opacity:0}2%,18%{opacity:1}20%,100%{opacity:0}}.role{opacity:0;animation:role 15s steps(1) infinite}",
        "@keyframes drift{from{transform:translateX(-200px)}to{transform:translateX(1100px)}}.cloud{animation:drift linear infinite}",
        "@keyframes fly{from{transform:translate(-60px,0)}50%{transform:translate(500px,-20px)}to{transform:translate(1060px,0)}}",
        ".birds{animation:fly 22s linear infinite}",
        "@keyframes rain{from{transform:translateY(-40px)}to{transform:translateY(360px)}}.drop{animation:rain .7s linear infinite}",
        "@keyframes flash{0%,93%,97%,100%{opacity:0}94%,96%{opacity:.7}}.flash{animation:flash 7s steps(1) infinite}",
        "@keyframes shoot{0%,88%{transform:translate(0,0);opacity:0}89%{opacity:1}96%{transform:translate(-260px,130px);opacity:0}100%{opacity:0}}",
        ".shoot{animation:shoot 9s linear infinite}",
        "@keyframes ff{0%,100%{opacity:.1;transform:translate(0,0)}50%{opacity:1;transform:translate(6px,-8px)}}.ff{animation:ff 3s steps(6) infinite}",
    ]
    # stars (night strong, dawn/dusk faint)
    if phase != "day":
        n = 70 if phase == "night" else 18
        for _ in range(n):
            x, y, s = rnd.randrange(W), rnd.randrange(0, 200), rnd.choice((2, 2, 3, 4))
            b.append(
                f'<rect class="st" style="animation-delay:-{rnd.random() * 3:.2f}s" x="{x}" y="{y}" '
                f'width="{s}" height="{s}" fill="{rnd.choice((WHITE, WHITE, CYAN, YELLOW))}"/>'
            )
    # sun moves across the sky with the hour; moon shows the real phase
    if phase == "night":
        p = moon_phase(now)

        def mcol(dx, dy, w):
            litp = dx > w * math.cos(2 * math.pi * p) if p < 0.5 else dx < w * math.cos(2 * math.pi * (p - 0.5))
            return ("#fff3c4" if (int(dx + dy) % 5) else "#e6d48f") if litp else "#2a2d4a"

        b.append(disc(880, 64, 7, 6, mcol))
        b.append(
            '<g class="shoot"><rect x="760" y="40" width="4" height="4" fill="#fff"/>'
            '<rect x="764" y="36" width="4" height="4" fill="#fff" opacity=".6"/>'
            '<rect x="768" y="32" width="4" height="4" fill="#fff" opacity=".3"/></g>'
        )
    else:
        t = min(max((hour + now.minute / 60 - 5.5) / 13.5, 0), 1)  # 5:30 -> 19:00
        sx, sy = 60 + t * 840, 236 - math.sin(t * math.pi) * 212
        sun = "#ffe066" if phase == "day" else "#ff9a3c"
        b.append(disc(int(sx), int(sy), 6, 6, lambda dx, dy, w: "#fff3b0" if dx * dx + dy * dy < 9 else sun))
    # clouds
    nclouds = {"clear": 2 if phase == "day" else 1, "cloudy": 6, "fog": 5, "rain": 7, "storm": 8}[weather]
    ccol = {"day": ("#ffffff", "#cfe6ff"), "dawn": ("#ffc2a8", "#d98c8c"), "dusk": ("#c98aa8", "#7a4a7a"), "night": ("#3a3d62", "#2a2d4a")}[phase]
    if weather in ("rain", "storm"):
        ccol = ("#6b7290", "#4a5070")
    for i in range(nclouds):
        y, dur, px = rnd.randrange(8, 120), rnd.randrange(40, 80), rnd.choice((5, 6, 7))
        b.append(
            f'<g class="cloud" style="animation-duration:{dur}s;animation-delay:-{rnd.randrange(dur)}s">'
            f'{sprite(CLOUD, px, {"w": ccol[0], "s": ccol[1]}, 0, y)}</g>'
        )
    # birds by day, fireflies by night
    if phase in ("day", "dawn") and weather not in ("rain", "storm"):
        flock = "".join(
            f'<g class="fa">{sprite(BIRD_A, 3, {"b": "#1b2a55"}, dx, dy)}</g><g class="fb">{sprite(BIRD_B, 3, {"b": "#1b2a55"}, dx, dy)}</g>'
            for dx, dy in ((0, 60), (22, 50), (44, 64))
        )
        b.append(f'<g class="birds">{flock}</g>')
    # skyline
    x = 0
    while x < W:
        bw, bh = rnd.randrange(30, 70), rnd.randrange(30, 95)
        top_y = 290 - bh
        b.append(f'<rect x="{x}" y="{top_y}" width="{bw}" height="{bh}" fill="{bld}"/>')
        for wx in range(x + 6, x + bw - 6, 10):
            for wy in range(top_y + 8, 282, 12):
                r = rnd.random()
                if r < lit:
                    cls = ' class="win"' if rnd.random() < 0.3 else ""
                    d = f' style="animation-delay:-{rnd.random() * 6:.1f}s"' if cls else ""
                    b.append(f'<rect{cls}{d} x="{wx}" y="{wy}" width="4" height="4" fill="{YELLOW}" opacity=".8"/>')
                elif phase == "day" and r < 0.3:
                    b.append(f'<rect x="{wx}" y="{wy}" width="4" height="4" fill="#9fdcff" opacity=".7"/>')
        x += bw + rnd.randrange(0, 8)
    if phase == "night":
        for _ in range(10):
            b.append(
                f'<rect class="ff" style="animation-delay:-{rnd.random() * 3:.1f}s" x="{rnd.randrange(W)}" '
                f'y="{rnd.randrange(230, 285)}" width="3" height="3" fill="#d8ff6b"/>'
            )
    # ground
    for gx in range(0, W, 16):
        b.append(f'<rect x="{gx}" y="290" width="16" height="50" fill="{ground[gx // 16 % 2]}"/>')
        b.append(f'<rect x="{gx}" y="290" width="16" height="4" fill="{GREEN if phase == "day" else ORANGE}"/>')
    for i, cx in enumerate((160, 200, 240, 700, 740, 780)):
        b.append(f'<g class="coin" style="animation-delay:-{i * 0.2:.1f}s">{sprite(COIN, 3, CCOL, cx, 250)}</g>')
    # weather particles
    if weather in ("rain", "storm"):
        for _ in range(90):
            b.append(
                f'<rect class="drop" style="animation-delay:-{rnd.random() * 0.7:.2f}s;animation-duration:{0.5 + rnd.random() * 0.4:.2f}s" '
                f'x="{rnd.randrange(W)}" y="{rnd.randrange(-40, 300)}" width="2" height="10" fill="#9fc4ff" opacity=".7"/>'
            )
    if weather == "storm":
        b.append(f'<rect class="flash" width="{W}" height="{H}" fill="#ffffff"/>')
    if weather == "fog":
        for fy in (200, 240, 270):
            b.append(f'<rect x="0" y="{fy}" width="{W}" height="18" fill="#d9dcef" opacity=".25"/>')
    # text panel (readable on any sky)
    b.append(f'<rect x="150" y="62" width="660" height="184" fill="{BG}" opacity=".62"/>')
    b.append(f'<rect x="150" y="62" width="660" height="184" fill="none" stroke="{ORANGE}" stroke-width="3" opacity=".8"/>')
    t = "ERICK MUTETI"
    b.append(f'<text x="484" y="124" font-size="46" text-anchor="middle" fill="{SHADOW}">{t}</text>')
    b.append(f'<text x="480" y="120" font-size="46" text-anchor="middle" fill="{ORANGE}">{t}</text>')
    roles = [("FULL-STACK ENGINEER", CYAN), ("BUG BOUNTY HUNTER", PINK), ("SECURITY RESEARCHER", ORANGE),
             ("PYTHON AUTOMATOR", GREEN), ("MATHS + CS GRADUATE", YELLOW)]
    for i, (r, c) in enumerate(roles):
        b.append(
            f'<text class="role" style="animation-delay:{i * 3}s" x="480" y="170" font-size="20" '
            f'text-anchor="middle" fill="{c}">&gt; {esc(r)}_</text>'
        )
    icon = {"clear": "CLEAR", "cloudy": "CLOUDY", "fog": "FOGGY", "rain": "RAINY", "storm": "STORMY"}[weather]
    extra = f" · {temp}C" if temp is not None else ""
    status = f"NAIROBI {now:%H}:00 · {phase.upper()} · {icon}{extra}"
    b.append(f'<text x="480" y="206" font-size="13" text-anchor="middle" fill="{WHITE}">{status}</text>')
    if phase == "night":
        b.append(f'<text x="480" y="230" font-size="11" text-anchor="middle" fill="{DIM}">{moon_name(moon_phase(now))}</text>')
    else:
        b.append(f'<text class="blink" x="480" y="232" font-size="12" text-anchor="middle" fill="{YELLOW}">PRESS START</text>')
    kn = f'<g class="fa">{sprite(KNIGHT_A, 4, KCOL, 0, 242)}</g><g class="fb">{sprite(KNIGHT_B, 4, KCOL, 0, 242)}</g>'
    sl = f'<g class="fa">{sprite(SLIME_A, 4, SCOL, -70, 266)}</g><g class="fb">{sprite(SLIME_B, 4, SCOL, -70, 266)}</g>'
    b.append(f'<g class="walker">{kn}</g><g class="chaser">{sl}</g>')
    b.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{EDGE}" stroke-width="2"/>')
    return svg(W, H, "".join(b), "".join(css), f"Erick Muteti - live pixel sky over Nairobi: {status}")


# ---------------------------------------------------------------- achievement (phone-friendly size)
def achievement():
    W, H = 640, 190
    rnd = random.Random(3)
    css = (
        "@keyframes drop{0%{transform:translateY(-200px)}75%{transform:translateY(8px)}100%{transform:translateY(0)}}"
        ".toast{animation:drop 1.2s steps(8) both}"
        "@keyframes shine{0%,30%{transform:translateX(-200px)}60%,100%{transform:translateX(900px)}}"
        ".shine{animation:shine 6s linear infinite}"
        "@keyframes fall{0%{transform:translateY(-20px);opacity:0}10%{opacity:1}100%{transform:translateY(210px);opacity:0}}"
        ".cf{animation:fall 3s linear infinite}"
    )
    trophy = ["yyyyyyyyyy", "Yyyyyyyyyy", "yYyyyyyyyY", ".yyyyyyyy.", "..yyyyyy..", "...yyyy...",
              "....yy....", "....yy....", "..oooooo..", "..oooooo.."]
    cap = ["....kk....", "..kkkkkk..", "kkkkkkkkkk", "..kkkkkkyy", "..kkkkkk.y", "........y."]
    b = []
    for _ in range(26):
        b.append(
            f'<rect class="cf" style="animation-delay:-{rnd.random() * 3:.2f}s" x="{rnd.randrange(10, W - 10)}" y="0" '
            f'width="6" height="6" fill="{rnd.choice((ORANGE, YELLOW, CYAN, PINK, GREEN))}"/>'
        )
    t = [f'<g class="toast"><clipPath id="c"><rect x="12" y="14" width="{W - 24}" height="162"/></clipPath>']
    t.append(f'<rect x="12" y="14" width="{W - 24}" height="162" fill="{PANEL}" stroke="{ORANGE}" stroke-width="5"/>')
    t.append(f'<rect x="26" y="28" width="120" height="134" fill="#1d2236"/>')
    t.append(sprite(trophy, 8, {"y": YELLOW, "Y": "#fff3b0", "o": ORANGE}, 46, 66))
    t.append(sprite(cap, 6, {"k": SHADOW, "y": YELLOW}, 56, 34))
    t.append(f'<text x="166" y="54" font-size="15" fill="{YELLOW}">ACHIEVEMENT</text>')
    t.append(f'<text x="166" y="76" font-size="15" fill="{YELLOW}">UNLOCKED!</text>')
    t.append(f'<text x="166" y="110" font-size="17" fill="{WHITE}">GRADUATED: BSc</text>')
    t.append(f'<text x="166" y="134" font-size="13" fill="{WHITE}">MATHS &amp; COMPUTER SCIENCE</text>')
    t.append(f'<text x="166" y="158" font-size="11" fill="{DIM}">MASENO UNIVERSITY</text>')
    t.append(f'<text x="612" y="54" font-size="12" text-anchor="end" fill="{GREEN}">+1000 XP</text>')
    t.append(
        '<g clip-path="url(#c)"><rect class="shine" x="0" y="14" width="50" height="162" fill="#ffffff" opacity=".10" '
        'transform="skewX(-20)"/></g></g>'
    )
    return svg(W, H, "".join(b) + "".join(t), css, "Achievement unlocked: graduated BSc Mathematics and Computer Science, Maseno University")


# ---------------------------------------------------------------- player card (stacked, phone-friendly)
PORTRAIT = [
    "....hhhhhhhh....", "...hhhhhhhhhh...", "..hhhhhhhhhhhh..", "..hhhffffffhhh..",
    ".hhhffffffffhhh.", ".hhfffeffefffhh.", ".chffggffggffhc.", ".chfffffffffhhc.",
    ".chhffffmfffhhc.", "..hhhffffffhhh..", "..hhhhhffhhhhh..", ".hhhhhhhhhhhhhh.",
    "hhhhoohhhhoohhhh", "hhhhhhhkkhhhhhhh", "hhhhhhkkkkhhhhhh", "hhhhhhhhhhhhhhhh",
]
PCOL = {"h": "#2b3355", "f": "#8a5a3c", "e": "#1b120c", "g": CYAN, "m": "#5a3626", "c": ORANGE, "o": ORANGE, "k": CYAN}


def player():
    W, H = 640, 740
    css = (
        "@keyframes fill{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        ".bar{transform-origin:0 0;transform-box:fill-box;animation:fill 1.6s steps(12) both}"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1.2s steps(1) infinite}"
        "@keyframes glow{0%,100%{opacity:.35}50%{opacity:1}}.glow{animation:glow 2s steps(4) infinite}"
    )
    b = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    b.append(f'<rect x="6" y="6" width="{W - 12}" height="{H - 12}" fill="{PANEL}" stroke="{EDGE}" stroke-width="4"/>')
    b.append(f'<text x="26" y="44" font-size="16" fill="{ORANGE}">CHARACTER SHEET</text>')
    b.append(f'<text class="blink" x="614" y="44" font-size="12" text-anchor="end" fill="{GREEN}">ONLINE</text>')
    # portrait
    b.append(f'<rect x="26" y="64" width="208" height="208" fill="#1d2236" stroke="{ORANGE}" stroke-width="4"/>')
    b.append(f'<rect class="glow" x="30" y="68" width="200" height="200" fill="none" stroke="{CYAN}" stroke-width="2"/>')
    b.append(sprite(PORTRAIT, 12, PCOL, 34, 72))
    b.append(f'<text x="130" y="300" font-size="16" text-anchor="middle" fill="{WHITE}">ERICX00</text>')
    b.append(f'<text x="26" y="328" font-size="12" fill="{YELLOW}">HP</text>')
    b.append(f'<rect x="60" y="314" width="174" height="16" fill="{SHADOW}" stroke="{EDGE}" stroke-width="2"/>')
    b.append(f'<rect class="glow" x="64" y="318" width="166" height="8" fill="{GREEN}"/>')
    info = [("CLASS", "FULL-STACK DEV", CYAN), ("SUBCLASS", "BUG HUNTER", PINK), ("GUILD", "MASENO UNI", YELLOW),
            ("RANK", "MATHS+CS GRAD", WHITE), ("TRAINING", "ALX SE PROGRAM", GREEN), ("BASE", "NAIROBI, KENYA", ORANGE)]
    for i, (k, v, c) in enumerate(info):
        y = 82 + i * 42
        b.append(f'<text x="256" y="{y}" font-size="11" fill="{DIM}">{k}</text>')
        b.append(f'<text x="256" y="{y + 20}" font-size="15" fill="{c}">{esc(v)}</text>')
    skills = [("PYTHON", 9, CYAN), ("JS / TS / NODE", 8, YELLOW), ("C / C++", 7, PINK), ("PHP · LARAVEL", 7, "#a78bfa"),
              ("APPSEC · BURP", 9, ORANGE), ("JAVA · RUST", 6, GREEN), ("LINUX · BASH", 8, WHITE)]
    b.append(f'<text x="26" y="378" font-size="14" fill="{ORANGE}">SKILL TREE</text>')
    for i, (name, lv, c) in enumerate(skills):
        y = 396 + i * 36
        b.append(f'<text x="26" y="{y + 14}" font-size="12" fill="{WHITE}">{esc(name)}</text>')
        b.append(f'<text x="614" y="{y + 14}" font-size="12" text-anchor="end" fill="{c}">LV{lv}</text>')
        b.append(f'<rect x="262" y="{y}" width="290" height="18" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>')
        segs = "".join(f'<rect x="{265 + s * 28.6:.1f}" y="{y + 3}" width="25" height="12" fill="{c}"/>' for s in range(lv))
        b.append(f'<g class="bar" style="animation-delay:{i * 0.15:.2f}s">{segs}</g>')
    stats = [("27", "PUBLIC REPOS"), ("8", "LANGUAGES"), ("ALX", "ALUMNI"), ("1", "DEGREE")]
    for i, (n, l) in enumerate(stats):
        x = 26 + i * 152
        b.append(f'<rect x="{x}" y="{H - 80}" width="138" height="56" fill="#1d2236" stroke="{EDGE}" stroke-width="2"/>')
        b.append(f'<text x="{x + 69}" y="{H - 50}" font-size="20" text-anchor="middle" fill="{ORANGE}">{n}</text>')
        b.append(f'<text x="{x + 69}" y="{H - 32}" font-size="10" text-anchor="middle" fill="{DIM}">{l}</text>')
    return svg(W, H, "".join(b), css, "Character sheet for ericx00")


# ---------------------------------------------------------------- chess puzzle
PIECES = {
    "p": ["..........", "....##....", "...####...", "...####...", "....##....", "...####...", "..######..", "..######..", ".########.", ".........."],
    "r": ["..........", ".##.##.##.", ".########.", "..######..", "..######..", "..######..", "..######..", ".########.", ".########.", ".........."],
    "n": ["..........", "....##....", "...####...", "..######..", ".#######..", ".##.####..", "....####..", "...#####..", "..######..", ".########."],
    "b": ["....#.....", "...###....", "..##.##...", "..###.#...", "..#####...", "...###....", "..#####...", ".#######..", ".#######..", ".........."],
    "q": ["#...##...#", ".#..##..#.", ".########.", "..######..", "...####...", "...####...", "..######..", ".########.", ".########.", ".........."],
    "k": ["....##....", "...####...", "....##....", ".########.", ".########.", "..######..", "...####...", "..######..", ".########.", ".########."],
}


def chess():
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR"  # 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6??
    S, M = 44, 26
    W = H = S * 8 + M * 2
    css = "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1s steps(1) infinite}"
    defs = "".join(
        f'<g id="{c}{k}">{outlined(rows, 4, "#f4f1e8" if c == "w" else ORANGE, SHADOW, 0, 0)}</g>'
        for k, rows in PIECES.items() for c in "wb"
    )
    b = [f'<defs>{defs}</defs><rect width="{W}" height="{H + 34}" fill="{BG}"/>']
    b.append(f'<rect x="{M - 6}" y="{M - 6}" width="{S * 8 + 12}" height="{S * 8 + 12}" fill="{ORANGE}"/>')
    for r, row in enumerate(fen.split("/")):
        f = 0
        for ch in row:
            n = int(ch) if ch.isdigit() else 1
            for _ in range(n):
                b.append(f'<rect x="{M + f * S}" y="{M + r * S}" width="{S}" height="{S}" fill="{"#3b4470" if (r + f) % 2 == 0 else "#232a4a"}"/>')
                if not ch.isdigit():
                    b.append(f'<use href="#{"w" if ch.isupper() else "b"}{ch.lower()}" xlink:href="#{"w" if ch.isupper() else "b"}{ch.lower()}" x="{M + f * S + 2}" y="{M + r * S + 2}"/>')
                f += 1
    for i, ch in enumerate("abcdefgh"):
        b.append(f'<text x="{M + i * S + S / 2}" y="{M + S * 8 + 20}" font-size="9" text-anchor="middle" fill="{DIM}">{ch}</text>')
        b.append(f'<text x="{M - 14}" y="{M + i * S + S / 2 + 4}" font-size="9" text-anchor="middle" fill="{DIM}">{8 - i}</text>')
    b.append(f'<text class="blink" x="{W / 2}" y="{H + 22}" font-size="12" text-anchor="middle" fill="{YELLOW}">WHITE TO MOVE · MATE IN 1</text>')
    return svg(W, H + 34, "".join(b), css, "Chess puzzle: white to move, mate in one")


# ---------------------------------------------------------------- footer
def footer():
    W, H = 640, 150
    css = (
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1s steps(1) infinite}"
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}.coin{animation:bob 1.2s steps(2) infinite}"
    )
    b = [f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<rect x="4" y="4" width="{W - 8}" height="{H - 8}" fill="none" stroke="{ORANGE}" stroke-width="4"/>',
         f'<text x="324" y="62" font-size="30" text-anchor="middle" fill="{SHADOW}">GAME ON</text>',
         f'<text x="320" y="58" font-size="30" text-anchor="middle" fill="{ORANGE}">GAME ON</text>',
         f'<text x="320" y="92" font-size="12" text-anchor="middle" fill="{WHITE}">THANKS FOR PLAYING, TRAVELLER</text>',
         f'<text class="blink" x="320" y="124" font-size="12" text-anchor="middle" fill="{YELLOW}">INSERT COIN TO CONTINUE</text>']
    for i, cx in enumerate((40, 70, 556, 586)):
        b.append(f'<g class="coin" style="animation-delay:-{i * 0.3:.1f}s">{sprite(COIN, 4, CCOL, cx, 60)}</g>')
    return svg(W, H, "".join(b), css, "Game on - thanks for playing")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sky", action="store_true", help="only regenerate the header")
    ap.add_argument("--at", type=int, help="force Nairobi hour 0-23")
    ap.add_argument("--weather", choices=["clear", "cloudy", "fog", "rain", "storm"])
    ap.add_argument("--out", default="header", help="header file name (for previews)")
    a = ap.parse_args()
    now = datetime.now(EAT)
    if a.at is not None:
        now = now.replace(hour=a.at, minute=0)
    weather, temp = (a.weather, None) if a.weather else live_weather()
    jobs = [(a.out, lambda: header(now, weather, temp))]
    if not a.sky:
        jobs += [("achievement", achievement), ("player", player), ("chess", chess), ("footer", footer)]
    for name, fn in jobs:
        (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8", newline="\n")
        print("wrote", name, (OUT / f"{name}.svg").stat().st_size // 1024, "KB")
    print(f"sky: {now:%H:%M} EAT, {phase_for(now.hour)}, {weather}, {temp}")
