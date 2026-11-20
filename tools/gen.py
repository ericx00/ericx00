"""Generates the pixel-art SVGs used by the profile README.

Run:  python tools/gen.py  (needs tools/ps2p.woff2, the Press Start 2P font, OFL)
Everything is plain SVG + CSS animation, so GitHub renders it as an <img>.
"""
import base64
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
FONT = base64.b64encode((ROOT / "tools" / "ps2p.woff2").read_bytes()).decode()

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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'shape-rendering="crispEdges" role="img" aria-label="{label}">'
        f"<style>{FONT_CSS}{css}</style>{body}</svg>"
    )


def sprite(rows, px, colors, x=0, y=0):
    """rows: list of strings; each char maps to a colour in `colors` ('.' = transparent)."""
    out = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colors:
                out.append(f'<rect x="{x + i * px}" y="{y + j * px}" width="{px}" height="{px}" fill="{colors[ch]}"/>')
    return "".join(out)


def outlined(rows, px, fill, line, x=0, y=0):
    """Draws a 1-pixel outline around every filled ('#') pixel, then the fill."""
    filled = {(i, j) for j, r in enumerate(rows) for i, c in enumerate(r) if c == "#"}
    edge = {(i + di, j + dj) for i, j in filled for di in (-1, 0, 1) for dj in (-1, 0, 1)} - filled
    out = [f'<rect x="{x + i * px}" y="{y + j * px}" width="{px}" height="{px}" fill="{line}"/>' for i, j in edge]
    out += [f'<rect x="{x + i * px}" y="{y + j * px}" width="{px}" height="{px}" fill="{fill}"/>' for i, j in filled]
    return "".join(out)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- sprites
KNIGHT_A = [  # knight in a graduation cap, frame A
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

SLIME_A = [
    "....gggg....",
    "..gggggggg..",
    ".gggwggwggg.",
    ".gggkggkggg.",
    "gggggggggggg",
    "gggggggggggg",
]
SLIME_B = [
    "............",
    "...gggggg...",
    ".ggggwggwggg",
    "gggggkggkggg",
    "gggggggggggg",
    "gggggggggggg",
]
SCOL = {"g": GREEN, "w": WHITE, "k": SHADOW}

COIN = [".yyy.", "yyYyy", "yyYyy", "yyYyy", ".yyy."]
CCOL = {"y": YELLOW, "Y": "#fff3b0"}


# ---------------------------------------------------------------- header
def header():
    W, H = 960, 330
    rnd = random.Random(7)
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    b.append(
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="#1d1442"/></linearGradient></defs>'
    )
    css = [
        "@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}",
        ".st{animation:tw 3s steps(3) infinite}",
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}",
        ".blink{animation:blink 1s steps(1) infinite}",
        "@keyframes walk{from{transform:translateX(-80px)}to{transform:translateX(1040px)}}",
        ".walker{animation:walk 14s linear infinite}",
        ".chaser{animation:walk 14s linear infinite;animation-delay:-1.1s}",
        "@keyframes fa{0%,49%{opacity:1}50%,100%{opacity:0}}",
        "@keyframes fb{0%,49%{opacity:0}50%,100%{opacity:1}}",
        ".fa{animation:fa .4s steps(1) infinite}.fb{animation:fb .4s steps(1) infinite}",
        "@keyframes win{0%,100%{fill:#ffd23f}50%{fill:#2a2550}}",
        ".win{animation:win 6s steps(2) infinite}",
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}",
        ".coin{animation:bob 1.2s steps(2) infinite}",
        "@keyframes role{0%{opacity:0}2%,18%{opacity:1}20%,100%{opacity:0}}",
        ".role{opacity:0;animation:role 15s steps(1) infinite}",
    ]
    # stars
    for _ in range(70):
        x, y, s = rnd.randrange(W), rnd.randrange(0, 210), rnd.choice((2, 2, 3, 4))
        b.append(
            f'<rect class="st" style="animation-delay:-{rnd.random() * 3:.2f}s" x="{x}" y="{y}" '
            f'width="{s}" height="{s}" fill="{rnd.choice((WHITE, WHITE, CYAN, YELLOW))}"/>'
        )
    # pixel moon
    moon = ["..mmmm..", ".mmmmmm.", "mmmmmmdm", "mmmdmmmm", "mmmmmmmm", "mmmmmdmm", ".mmmmmm.", "..mmmm.."]
    b.append(sprite(moon, 6, {"m": "#fff3c4", "d": "#e6d48f"}, 850, 26))
    # skyline
    x = 0
    while x < W:
        bw, bh = rnd.randrange(30, 70), rnd.randrange(30, 95)
        top = 290 - bh
        b.append(f'<rect x="{x}" y="{top}" width="{bw}" height="{bh}" fill="#161236"/>')
        for wx in range(x + 6, x + bw - 6, 10):
            for wy in range(top + 8, 282, 12):
                if rnd.random() < 0.35:
                    cls = ' class="win"' if rnd.random() < 0.3 else ""
                    d = f' style="animation-delay:-{rnd.random() * 6:.1f}s"' if cls else ""
                    b.append(f'<rect{cls}{d} x="{wx}" y="{wy}" width="4" height="4" fill="{YELLOW}" opacity=".8"/>')
        x += bw + rnd.randrange(0, 8)
    # ground tiles
    for gx in range(0, W, 16):
        b.append(f'<rect x="{gx}" y="290" width="16" height="40" fill="{"#2b2f4a" if gx // 16 % 2 else "#252942"}"/>')
        b.append(f'<rect x="{gx}" y="290" width="16" height="4" fill="{ORANGE}"/>')
    # coins
    for i, cx in enumerate((160, 200, 240, 700, 740, 780)):
        b.append(f'<g class="coin" style="animation-delay:-{i * 0.2:.1f}s">{sprite(COIN, 3, CCOL, cx, 248)}</g>')
    # title
    t = "ERICK MUTETI"
    b.append(f'<text x="484" y="114" font-size="46" text-anchor="middle" fill="{SHADOW}">{t}</text>')
    b.append(f'<text x="480" y="110" font-size="46" text-anchor="middle" fill="{ORANGE}">{t}</text>')
    b.append(f'<text x="480" y="146" font-size="12" text-anchor="middle" fill="{DIM}">PLAYER 1 · @ERICX00 · KENYA</text>')
    roles = [
        ("FULL-STACK ENGINEER", CYAN),
        ("BUG BOUNTY HUNTER", PINK),
        ("PIXEL ASSET FORGER", ORANGE),
        ("CHESS STREAMER", GREEN),
        ("BSc MATHS + CS GRADUATE", YELLOW),
    ]
    for i, (r, c) in enumerate(roles):
        b.append(
            f'<text class="role" style="animation-delay:{i * 3}s" x="480" y="186" font-size="18" '
            f'text-anchor="middle" fill="{c}">&gt; {esc(r)}_</text>'
        )
    b.append(f'<text class="blink" x="480" y="226" font-size="12" text-anchor="middle" fill="{YELLOW}">PRESS START</text>')
    # walker: slime chasing the graduate knight
    kn = (
        f'<g class="fa">{sprite(KNIGHT_A, 4, KCOL, 0, 242)}</g>'
        f'<g class="fb">{sprite(KNIGHT_B, 4, KCOL, 0, 242)}</g>'
    )
    sl = (
        f'<g class="fa">{sprite(SLIME_A, 4, SCOL, -70, 266)}</g>'
        f'<g class="fb">{sprite(SLIME_B, 4, SCOL, -70, 266)}</g>'
    )
    b.append(f'<g class="walker">{kn}</g><g class="chaser">{sl}</g>')
    b.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{EDGE}" stroke-width="2"/>')
    return svg(W, H, "".join(b), "".join(css), "Erick Muteti - pixel game header")


# ---------------------------------------------------------------- achievement
def achievement():
    W, H = 860, 130
    rnd = random.Random(3)
    css = (
        "@keyframes drop{0%{transform:translateY(-140px)}12%{transform:translateY(8px)}16%,100%{transform:translateY(0)}}"
        ".toast{animation:drop 6s steps(8) infinite}"
        "@keyframes shine{0%,30%{transform:translateX(-200px)}60%,100%{transform:translateX(1000px)}}"
        ".shine{animation:shine 6s linear infinite}"
        "@keyframes fall{0%{transform:translateY(-20px);opacity:0}10%{opacity:1}100%{transform:translateY(150px);opacity:0}}"
        ".cf{animation:fall 3s linear infinite}"
    )
    trophy = [
        "yyyyyyyyyy",
        "Yyyyyyyyyy",
        "yYyyyyyyyY",
        ".yyyyyyyy.",
        "..yyyyyy..",
        "...yyyy...",
        "....yy....",
        "....yy....",
        "..oooooo..",
        "..oooooo..",
    ]
    cap = ["....kk....", "..kkkkkk..", "kkkkkkkkkk", "..kkkkkkyy", "..kkkkkk.y", "........y."]
    b = []
    for _ in range(26):
        x = rnd.randrange(10, W - 10)
        b.append(
            f'<rect class="cf" style="animation-delay:-{rnd.random() * 3:.2f}s" x="{x}" y="0" width="5" height="5" '
            f'fill="{rnd.choice((ORANGE, YELLOW, CYAN, PINK, GREEN))}"/>'
        )
    t = [f'<g class="toast"><clipPath id="c"><rect x="20" y="16" width="{W - 40}" height="98"/></clipPath>']
    t.append(f'<rect x="20" y="16" width="{W - 40}" height="98" fill="{PANEL}" stroke="{ORANGE}" stroke-width="4"/>')
    t.append(f'<rect x="28" y="24" width="98" height="82" fill="#1d2236"/>')
    t.append(sprite(trophy, 6, {"y": YELLOW, "Y": "#fff3b0", "o": ORANGE}, 47, 40))
    t.append(sprite(cap, 4, {"k": SHADOW, "y": YELLOW}, 57, 26))
    t.append(f'<text x="146" y="48" font-size="12" fill="{YELLOW}">ACHIEVEMENT UNLOCKED!</text>')
    t.append(f'<text x="146" y="76" font-size="15" fill="{WHITE}">GRADUATED: BSc MATHEMATICS</text>')
    t.append(f'<text x="146" y="98" font-size="15" fill="{WHITE}">&amp; COMPUTER SCIENCE</text>')
    t.append(f'<text x="826" y="48" font-size="10" text-anchor="end" fill="{GREEN}">+1000 XP</text>')
    t.append(f'<text x="826" y="98" font-size="10" text-anchor="end" fill="{DIM}">MASENO UNIVERSITY</text>')
    t.append(
        '<g clip-path="url(#c)"><rect class="shine" x="0" y="16" width="40" height="98" fill="#ffffff" opacity=".10" '
        'transform="skewX(-20)"/></g></g>'
    )
    return svg(W, H, "".join(b) + "".join(t), css, "Achievement unlocked: graduated BSc Mathematics and Computer Science, Maseno University")


# ---------------------------------------------------------------- player card
PORTRAIT = [  # hooded hacker with headset, 16x16
    "....hhhhhhhh....",
    "...hhhhhhhhhh...",
    "..hhhhhhhhhhhh..",
    "..hhhffffffhhh..",
    ".hhhffffffffhhh.",
    ".hhfffeffefffhh.",
    ".chffggffggffhc.",
    ".chfffffffffhhc.",
    ".chhffffmfffhhc.",
    "..hhhffffffhhh..",
    "..hhhhhffhhhhh..",
    ".hhhhhhhhhhhhhh.",
    "hhhhoohhhhoohhhh",
    "hhhhhhhkkhhhhhhh",
    "hhhhhhkkkkhhhhhh",
    "hhhhhhhhhhhhhhhh",
]
PCOL = {"h": "#2b3355", "f": "#8a5a3c", "e": "#1b120c", "g": CYAN, "m": "#5a3626", "c": ORANGE, "o": ORANGE, "k": "#3ee6ff"}


def player():
    W, H = 960, 380
    css = (
        "@keyframes fill{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        ".bar{transform-origin:0 0;transform-box:fill-box;animation:fill 1.6s steps(12) both}"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        ".blink{animation:blink 1.2s steps(1) infinite}"
        "@keyframes glow{0%,100%{opacity:.35}50%{opacity:1}}"
        ".glow{animation:glow 2s steps(4) infinite}"
    )
    b = [f'<rect width="{W}" height="{H}" fill="{BG}"/>']
    b.append(f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" fill="{PANEL}" stroke="{EDGE}" stroke-width="4"/>')
    b.append(f'<text x="30" y="44" font-size="14" fill="{ORANGE}">CHARACTER SHEET</text>')
    b.append(f'<text class="blink" x="930" y="44" font-size="10" text-anchor="end" fill="{GREEN}">● ONLINE</text>')
    # portrait frame
    b.append(f'<rect x="30" y="64" width="208" height="208" fill="#1d2236" stroke="{ORANGE}" stroke-width="4"/>')
    b.append(f'<rect class="glow" x="34" y="68" width="200" height="200" fill="none" stroke="{CYAN}" stroke-width="2"/>')
    b.append(sprite(PORTRAIT, 12, PCOL, 38, 72))
    b.append(f'<text x="134" y="298" font-size="12" text-anchor="middle" fill="{WHITE}">ERICX00</text>')
    b.append(f'<text x="134" y="320" font-size="9" text-anchor="middle" fill="{DIM}">RANK: GRADUATE</text>')
    b.append(f'<text x="40" y="346" font-size="8" fill="{YELLOW}">HP</text>')
    b.append(f'<rect x="64" y="336" width="164" height="12" fill="{SHADOW}" stroke="{EDGE}" stroke-width="2"/>')
    b.append(f'<rect class="glow" x="67" y="339" width="158" height="6" fill="{GREEN}"/>')
    # info column
    info = [
        ("CLASS", "FULL-STACK ENGINEER", CYAN),
        ("SUBCLASS", "BUG BOUNTY HUNTER", PINK),
        ("GUILD", "MASENO UNI · MATHS + CS", YELLOW),
        ("TRAINING", "ALX SOFTWARE ENGINEERING", WHITE),
        ("SIDE QUEST", "CHESSTROPOLIS ON YOUTUBE", GREEN),
        ("SHOP", "ASSETFORGE ON ITCH.IO", ORANGE),
    ]
    for i, (k, v, c) in enumerate(info):
        y = 84 + i * 40
        b.append(f'<text x="262" y="{y}" font-size="9" fill="{DIM}">{k}</text>')
        b.append(f'<text x="262" y="{y + 18}" font-size="11" fill="{c}">{esc(v)}</text>')
    # skills
    skills = [
        ("PYTHON", 9, CYAN),
        ("JS / TS / NODE", 8, YELLOW),
        ("C / C++", 7, PINK),
        ("PHP · LARAVEL", 7, "#a78bfa"),
        ("APPSEC · BURP", 9, ORANGE),
        ("PIXEL ART · SFX", 8, GREEN),
        ("CHESS", 8, WHITE),
    ]
    b.append(f'<text x="622" y="84" font-size="10" fill="{DIM}">SKILL TREE</text>')
    for i, (name, lv, c) in enumerate(skills):
        y = 104 + i * 34
        b.append(f'<text x="622" y="{y + 9}" font-size="9" fill="{WHITE}">{esc(name)}</text>')
        b.append(f'<text x="930" y="{y + 9}" font-size="9" text-anchor="end" fill="{c}">LV{lv}</text>')
        b.append(f'<rect x="622" y="{y + 15}" width="308" height="12" fill="#0b0d14" stroke="{EDGE}" stroke-width="2"/>')
        segs = "".join(
            f'<rect x="{625 + s * 30.4:.1f}" y="{y + 18}" width="27" height="6" fill="{c}"/>' for s in range(lv)
        )
        b.append(f'<g class="bar" style="animation-delay:{i * 0.15:.2f}s">{segs}</g>')
    # stat strip
    stats = [("27", "PUBLIC REPOS"), ("20", "ITCH RELEASES"), ("2", "PLAYABLE GAMES"), ("1", "DEGREE UNLOCKED")]
    for i, (n, l) in enumerate(stats):
        x = 262 + i * 168
        b.append(f'<text x="{x}" y="342" font-size="16" fill="{ORANGE}">{n}</text>')
        b.append(f'<text x="{x}" y="358" font-size="7" fill="{DIM}">{l}</text>')
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
    # 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? - white to move
    fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR"
    S, M = 44, 26
    W = H = S * 8 + M * 2
    css = "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1s steps(1) infinite}"
    defs = "".join(
        f'<g id="{c}{k}">{outlined(rows, 4, "#f4f1e8" if c == "w" else ORANGE, SHADOW, 0, 0)}</g>'
        for k, rows in PIECES.items() for c in "wb"
    )
    b = [f'<defs>{defs}</defs><rect width="{W}" height="{H + 30}" fill="{BG}"/>']
    b.append(f'<rect x="{M - 6}" y="{M - 6}" width="{S * 8 + 12}" height="{S * 8 + 12}" fill="{ORANGE}"/>')
    for r, row in enumerate(fen.split("/")):
        f = 0
        for ch in row:
            if ch.isdigit():
                for _ in range(int(ch)):
                    b.append(f'<rect x="{M + f * S}" y="{M + r * S}" width="{S}" height="{S}" fill="{"#3b4470" if (r + f) % 2 == 0 else "#232a4a"}"/>')
                    f += 1
                continue
            b.append(f'<rect x="{M + f * S}" y="{M + r * S}" width="{S}" height="{S}" fill="{"#3b4470" if (r + f) % 2 == 0 else "#232a4a"}"/>')
            white = ch.isupper()
            b.append(f'<use href="#{"w" if white else "b"}{ch.lower()}" x="{M + f * S + 2}" y="{M + r * S + 2}"/>')
            f += 1
    for i, ch in enumerate("abcdefgh"):
        b.append(f'<text x="{M + i * S + S / 2}" y="{M + S * 8 + 20}" font-size="8" text-anchor="middle" fill="{DIM}">{ch}</text>')
        b.append(f'<text x="{M - 14}" y="{M + i * S + S / 2 + 4}" font-size="8" text-anchor="middle" fill="{DIM}">{8 - i}</text>')
    b.append(f'<text class="blink" x="{W / 2}" y="{H + 18}" font-size="10" text-anchor="middle" fill="{YELLOW}">WHITE TO MOVE · MATE IN 1</text>')
    return svg(W, H + 30, "".join(b), css, "Chess puzzle: white to move, mate in one")


if __name__ == "__main__":
    for name, fn in (("header", header), ("achievement", achievement), ("player", player), ("chess", chess)):
        (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print("wrote", name, (OUT / f"{name}.svg").stat().st_size // 1024, "KB")
