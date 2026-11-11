"""Pixel font family for the Deckbuilder Kit.

Two hand-drawn designs (Forge Sans 5x7 with true lowercase, Ember Tiny 3x5 caps) and two
styles derived from Forge Sans by code (Bold = thickened, Display = 2x with smoothed corners).
Each is exported as BMFont (.fnt + PNG) with the stdlib, and as .ttf when fontTools is installed.
"""
from __future__ import annotations

from pathlib import Path

from .font import G as CAPS
from .png import Canvas, RGBA


def _rows(s: str) -> list[str]:
    return s.split("/")


# Lowercase and extra punctuation for Forge Sans. 9 rows: 7 above the baseline + 2 descender rows.
LOWER = {
 "a": "...../...../.###./....#/.####/#...#/.####",
 "b": "#..../#..../####./#...#/#...#/#...#/####.",
 "c": "...../...../.###./#...#/#..../#...#/.###.",
 "d": "....#/....#/.####/#...#/#...#/#...#/.####",
 "e": "...../...../.###./#...#/#####/#..../.###.",
 "f": "..##./.#.../###../.#.../.#.../.#.../.#...",
 "g": "...../...../.####/#...#/#...#/#...#/.####/....#/.###.",
 "h": "#..../#..../####./#...#/#...#/#...#/#...#",
 "i": "..#../...../.##../..#../..#../..#../.###.",
 "j": "...#./...../..##./...#./...#./...#./...#./#..#./.##..",
 "k": "#..../#..../#..#./#.#../##.../#.#../#..#.",
 "l": ".##../..#../..#../..#../..#../..#../.###.",
 "m": "...../...../##.#./#.#.#/#.#.#/#.#.#/#.#.#",
 "n": "...../...../####./#...#/#...#/#...#/#...#",
 "o": "...../...../.###./#...#/#...#/#...#/.###.",
 "p": "...../...../####./#...#/#...#/#...#/####./#..../#....",
 "q": "...../...../.####/#...#/#...#/#...#/.####/....#/....#",
 "r": "...../...../#.##./##..#/#..../#..../#....",
 "s": "...../...../.####/#..../.###./....#/####.",
 "t": ".#.../.#.../###../.#.../.#.../.#..#/..##.",
 "u": "...../...../#...#/#...#/#...#/#...#/.####",
 "v": "...../...../#...#/#...#/#...#/.#.#./..#..",
 "w": "...../...../#...#/#.#.#/#.#.#/#.#.#/.#.#.",
 "x": "...../...../#...#/.#.#./..#../.#.#./#...#",
 "y": "...../...../#...#/#...#/#...#/#...#/.####/....#/.###.",
 "z": "...../...../#####/...#./..#../.#.../#####",
 "[": "..##./..#../..#../..#../..#../..#../..##.",
 "]": ".##../..#../..#../..#../..#../..#../.##..",
 "|": "..#../..#../..#../..#../..#../..#../..#..",
 "~": "...../...../.#.../#.#.#/...#./...../.....",
 "^": "..#../.#.#./#...#/...../...../...../.....",
 "@": ".###./#...#/#.###/#.#.#/#.###/#..../.###.",
 "\\": "#..../.#.../.#.../..#../...#./...#./....#",
 "{": "...#./..#../..#../.#.../..#../..#../...#.",
 "}": ".#.../..#../..#../...#./..#../..#../.#...",
 "`": ".#.../..#../...../...../...../...../.....",
}

TINY = {
 "A": ".#./#.#/###/#.#/#.#", "B": "##./#.#/##./#.#/##.", "C": ".##/#../#../#../.##", "D": "##./#.#/#.#/#.#/##.",
 "E": "###/#../##./#../###", "F": "###/#../##./#../#..", "G": ".##/#../#.#/#.#/.##", "H": "#.#/#.#/###/#.#/#.#",
 "I": "###/.#./.#./.#./###", "J": "..#/..#/..#/#.#/.#.", "K": "#.#/#.#/##./#.#/#.#", "L": "#../#../#../#../###",
 "M": "#.#/###/#.#/#.#/#.#", "N": "##./#.#/#.#/#.#/#.#", "O": ".#./#.#/#.#/#.#/.#.", "P": "##./#.#/##./#../#..",
 "Q": ".#./#.#/#.#/###/.##", "R": "##./#.#/##./#.#/#.#", "S": ".##/#../.#./..#/##.", "T": "###/.#./.#./.#./.#.",
 "U": "#.#/#.#/#.#/#.#/###", "V": "#.#/#.#/#.#/#.#/.#.", "W": "#.#/#.#/#.#/###/#.#", "X": "#.#/#.#/.#./#.#/#.#",
 "Y": "#.#/#.#/.#./.#./.#.", "Z": "###/..#/.#./#../###",
 "0": "###/#.#/#.#/#.#/###", "1": ".#./##./.#./.#./###", "2": "##./..#/.#./#../###", "3": "##./..#/.#./..#/##.",
 "4": "#.#/#.#/###/..#/..#", "5": "###/#../##./..#/##.", "6": ".##/#../###/#.#/###", "7": "###/..#/.#./.#./.#.",
 "8": "###/#.#/###/#.#/###", "9": "###/#.#/###/..#/##.",
 " ": ".../.../.../.../...", ".": ".../.../.../.../.#.", ",": ".../.../.../.#./#..", "!": ".#./.#./.#./.../.#.",
 "?": "##./..#/.#./.../.#.", ":": ".../.#./.../.#./...", ";": ".../.#./.../.#./#..", "-": ".../.../###/.../...",
 "+": ".../.#./###/.#./...", "/": "..#/..#/.#./#../#..", "'": ".#./.#./.../.../...", '"': "#.#/#.#/.../.../...",
 "(": ".#./#../#../#../.#.", ")": ".#./..#/..#/..#/.#.", "%": "#.#/..#/.#./#../#.#", "=": ".../###/.../###/...",
 "_": ".../.../.../.../###", "#": "#.#/###/#.#/###/#.#", "*": ".../#.#/.#./#.#/...", "<": "..#/.#./#../.#./..#",
 ">": "#../.#./..#/.#./#..", "$": ".##/##./.#./.##/##.", "&": ".#./#.#/.#./#.#/.##",
}


def _grid(rows: list[str], h: int) -> list[str]:
    w = len(rows[0])
    return rows + ["." * w] * (h - len(rows))


def _sans() -> dict[str, list[str]]:
    g = {ch: _grid(list(rows), 9) for ch, rows in CAPS.items()}
    g.update({ch: _grid(_rows(s), 9) for ch, s in LOWER.items()})
    return g


BOLD_FIX = {  # letters whose counters close up when thickened are redrawn wider
 "M": "##...##/###.###/#######/##.#.##/##...##/##...##/##...##",
 "W": "##...##/##...##/##...##/##.#.##/#######/###.###/##...##",
 "m": "......./......./######./##.#.##/##.#.##/##.#.##/##.#.##",
 "w": "......./......./##...##/##.#.##/##.#.##/#######/.##.##.",
}


def _bold(g: dict[str, list[str]]) -> dict[str, list[str]]:
    out = {}
    for ch, rows in g.items():
        if ch in BOLD_FIX:
            out[ch] = _grid(_rows(BOLD_FIX[ch]), len(rows))
            continue
        out[ch] = ["".join("#" if (x < len(r) and r[x] == "#") or (x > 0 and r[x - 1] == "#") else "." for x in range(len(r) + 1)) for r in rows]
    return out


def _epx(rows: list[str]) -> list[str]:
    """Scale2x/EPX: doubles a glyph and rounds its diagonal steps."""
    h, w = len(rows), len(rows[0])
    P = lambda x, y: rows[y][x] if 0 <= x < w and 0 <= y < h else "."
    out = [["."] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        for x in range(w):
            p, a, b, c, d = P(x, y), P(x, y - 1), P(x + 1, y), P(x - 1, y), P(x, y + 1)
            e = [p, p, p, p]
            if c == a and c != d and a != b: e[0] = a
            if a == b and a != c and b != d: e[1] = b
            if d == c and d != b and c != a: e[2] = c
            if b == d and b != a and d != c: e[3] = d
            out[y * 2][x * 2], out[y * 2][x * 2 + 1], out[y * 2 + 1][x * 2], out[y * 2 + 1][x * 2 + 1] = e
    return ["".join(r) for r in out]


def _trim(rows: list[str]) -> tuple[list[str], int]:
    """Cut empty columns on both sides (for proportional spacing). Returns rows and width."""
    w = len(rows[0])
    cols = [x for x in range(w) if any(r[x] == "#" for r in rows)]
    if not cols:
        return rows, 0
    lo, hi = cols[0], cols[-1]
    return [r[lo:hi + 1] for r in rows], hi - lo + 1


class PixFont:
    def __init__(self, name: str, file: str, glyphs: dict[str, list[str]], ascent: int, gap: int = 1, space: int = 3,
                 caps_only: bool = False, mono: bool = False, note: str = ""):
        self.name, self.file, self.ascent, self.gap, self.caps_only, self.note = name, file, ascent, gap, caps_only, note
        self.height = len(next(iter(glyphs.values())))
        self.glyphs: dict[str, tuple[list[str], int]] = {}
        cell = max(len(r[0]) for r in glyphs.values())
        for ch, rows in glyphs.items():
            if ch == " ":
                self.glyphs[ch] = ([""] * self.height, space)
            elif mono:
                self.glyphs[ch] = (rows, cell)
            else:
                self.glyphs[ch] = _trim(rows)
        self.line = self.height + 2

    def get(self, ch: str) -> tuple[list[str], int]:
        if ch not in self.glyphs and self.caps_only:
            ch = ch.upper()
        return self.glyphs.get(ch) or self.glyphs["?"]

    def width(self, text: str) -> int:
        return max(0, sum(self.get(ch)[1] + self.gap for ch in text) - self.gap)

    def draw(self, c: Canvas, x: int, y: int, text: str, col: RGBA, shadow: RGBA | None = None) -> int:
        for pass_ in ((1, shadow), (0, col)) if shadow else ((0, col),):
            off, colr = pass_
            cx = x
            for ch in text:
                rows, w = self.get(ch)
                for gy, row in enumerate(rows):
                    for gx, v in enumerate(row):
                        if v == "#":
                            c.set(cx + gx + off, y + gy + off, colr)
                cx += w + self.gap
        return self.width(text)

    def chars(self) -> list[str]:
        cs = sorted(self.glyphs)
        if self.caps_only:
            cs = sorted(set(cs) | {ch.lower() for ch in cs if ch.isalpha()})
        return cs

    def atlas(self, cols: int = 16, pad: int = 1) -> tuple[Canvas, dict[str, tuple[int, int, int]]]:
        keys = sorted(self.glyphs)
        cw = max(w for _, w in self.glyphs.values()) + pad
        chh = self.height + pad
        c = Canvas(cols * cw, ((len(keys) + cols - 1) // cols) * chh)
        pos = {}
        for i, ch in enumerate(keys):
            x, y = (i % cols) * cw, (i // cols) * chh
            rows, w = self.glyphs[ch]
            for gy, row in enumerate(rows):
                for gx, v in enumerate(row):
                    if v == "#":
                        c.set(x + gx, y + gy, (255, 255, 255, 255))
            pos[ch] = (x, y, w)
        return c, pos

    def bmfont(self, png_name: str, scale: int = 1) -> tuple[Canvas, str]:
        c, pos = self.atlas()
        if scale > 1:
            c = c.scaled(scale)
        k = scale
        lines = [
            f'info face="{self.name}" size={self.ascent * k} bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=1,1',
            f"common lineHeight={self.line * k} base={self.ascent * k} scaleW={c.w} scaleH={c.h} pages=1 packed=0",
            f'page id=0 file="{png_name}"',
        ]
        rows = []
        for ch in self.chars():
            src = ch if ch in pos else ch.upper()
            x, y, w = pos[src]
            rows.append(f"char id={ord(ch)} x={x * k} y={y * k} width={max(w, 1) * k} height={self.height * k} xoffset=0 yoffset=0 xadvance={(w + self.gap) * k} page=0 chnl=15")
        lines.append(f"chars count={len(rows)}")
        return c, "\n".join(lines + rows) + "\n"

    def ttf(self, path: Path, px: int, upm: int, version: str = "1.0") -> bool:
        """Write a TrueType font: every pixel run becomes a rectangle. Needs fontTools (build-time only)."""
        try:
            from fontTools.fontBuilder import FontBuilder
            from fontTools.pens.ttGlyphPen import TTGlyphPen
        except ImportError:
            return False
        names = {".notdef": None}
        cmap, glyphs, metrics = {}, {}, {}
        pen = TTGlyphPen(None)
        pen.moveTo((px // 2, 0)); pen.lineTo((px // 2, self.ascent * px)); pen.lineTo((px * 3, self.ascent * px)); pen.lineTo((px * 3, 0)); pen.closePath()
        glyphs[".notdef"] = pen.glyph(); metrics[".notdef"] = (px * 4, px // 2)
        for ch, (rows, w) in sorted(self.glyphs.items()):
            gname = f"uni{ord(ch):04X}"
            pen = TTGlyphPen(None)
            for gy, row in enumerate(rows):
                x = 0
                while x < len(row):
                    if row[x] == "#":
                        x1 = x
                        while x1 < len(row) and row[x1] == "#":
                            x1 += 1
                        top, bot = (self.ascent - gy) * px, (self.ascent - gy - 1) * px
                        pen.moveTo((x * px, bot)); pen.lineTo((x * px, top)); pen.lineTo((x1 * px, top)); pen.lineTo((x1 * px, bot)); pen.closePath()
                        x = x1
                    else:
                        x += 1
            glyphs[gname] = pen.glyph(); metrics[gname] = ((w + self.gap) * px, 0)
            cmap[ord(ch)] = gname
            if self.caps_only and ch.isalpha():
                cmap[ord(ch.lower())] = gname
        order = list(glyphs)
        fb = FontBuilder(upm, isTTF=True)
        fb.setupGlyphOrder(order)
        fb.setupCharacterMap(cmap)
        fb.setupGlyf(glyphs)
        fb.setupHorizontalMetrics(metrics)
        desc = (self.height - self.ascent) * px
        fb.setupHorizontalHeader(ascent=self.ascent * px + px, descent=-desc - px)
        fb.setupNameTable({"familyName": self.name, "styleName": "Regular", "uniqueFontIdentifier": f"Forge:{self.name}:{version}",
                           "fullName": self.name, "psName": self.name.replace(" ", ""), "version": f"Version {version}",
                           "manufacturer": "Forge", "designer": "Forge (Erick Muteti)", "licenseDescription": "See LICENSE.txt in the pack."})
        fb.setupOS2(sTypoAscender=self.ascent * px + px, sTypoDescender=-desc - px, sTypoLineGap=0, usWinAscent=self.ascent * px + px, usWinDescent=desc + px,
                    sxHeight=5 * px, sCapHeight=self.ascent * px)
        fb.setupPost()
        path.parent.mkdir(parents=True, exist_ok=True)
        fb.save(str(path))
        return True


def fonts() -> dict[str, PixFont]:
    sans = _sans()
    disp = {ch: _epx(rows) for ch, rows in sans.items()}
    for ch in "DBPREFLKHMNU":           # keep the stem square: a rounded D reads as an O
        rows = disp[ch]
        for y in range(len(rows)):
            if sans[ch][y // 2][0] == "#" and rows[y][0] != "#":
                rows[y] = "#" + rows[y][1:]
    tiny = {ch: _rows(s) for ch, s in TINY.items()}
    return {
        "sans": PixFont("Forge Sans", "forge-sans", sans, ascent=7, note="5x7 body font with true lowercase. Crisp at 8, 16, 24, 32 px."),
        "bold": PixFont("Forge Sans Bold", "forge-sans-bold", _bold(sans), ascent=7, note="Thickened Forge Sans for titles and numbers. Crisp at 8, 16, 24, 32 px."),
        "display": PixFont("Forge Display", "forge-display", disp, ascent=14, gap=2, space=6, note="Forge Sans doubled with smoothed corners, for logos and headings. Crisp at 16, 32, 48 px."),
        "tiny": PixFont("Ember Tiny", "ember-tiny", tiny, ascent=5, space=2, caps_only=True, mono=False, note="3x5 capitals and digits for labels, damage numbers and tiny HUDs (lowercase shows as capitals). Crisp at 6, 12, 18 px."),
    }


# (pixel size in font units, units per em): em = 8 px for the 7-px fonts, 16 for Display, 6 for Tiny.
TTF_UNITS = {"sans": (128, 1024), "bold": (128, 1024), "display": (64, 1024), "tiny": (160, 960)}
