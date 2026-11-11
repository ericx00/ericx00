"""Chiptune music loops for the Deckbuilder Kit. Each loop is 16 bars and wraps cleanly:
note tails and echo that pass the end are folded back to the start, so there is no gap or click."""
from __future__ import annotations

import math
import random

from .wav import SR, Signal, envelope, lowpass, note, osc, svf, sweep, vibrato

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
MAJ, MIN = (0, 4, 7), (0, 3, 7)
SCALES = {"minor": (0, 2, 3, 5, 7, 8, 10), "major": (0, 2, 4, 5, 7, 9, 11), "phrygian": (0, 1, 3, 5, 7, 8, 10)}


def hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def chord(name: str) -> tuple[int, tuple[int, int, int]]:
    """'Am' -> (root pitch class, intervals)."""
    minor = name.endswith("m")
    return NOTE[name[:-1] if minor else name], (MIN if minor else MAJ)


# name: title, bpm, key root, scale, chords (16 bars), style
TRACKS = {
    "map_embers": dict(title="Embers on the Road", use="map / menu", bpm=96, key="A", scale="minor", style="calm",
                       chords="Am F C G Am F Dm E Am F C G Dm Am E Am".split()),
    "battle_sparks": dict(title="Sparks Fly", use="battle", bpm=140, key="E", scale="minor", style="drive",
                          chords="Em C D Bm Em C D B Em C D Bm C D Em Em".split()),
    "boss_forge_heart": dict(title="The Forge Heart", use="boss", bpm=158, key="D", scale="phrygian", style="heavy",
                             chords="Dm Dm Eb Dm Dm Bb C Dm Dm Dm Eb Dm Bb C A Dm".split()),
    "rest_hearth": dict(title="By the Hearth", use="rest / shop", bpm=84, key="C", scale="major", style="soft",
                        chords="C Am F G C Em F G Am F C G F G C C".split()),
    "title_anvil": dict(title="Anvil Song", use="title / victory", bpm=120, key="G", scale="major", style="bright",
                        chords="G D Em C G D C D Em C G D C D G G".split()),
}

# melody rhythms per bar: (start 16th, length in 16ths, strong beat?)
MOTIFS = {
    "calm": [[(0, 6, 1), (6, 2, 0), (8, 8, 1)], [(0, 4, 1), (4, 4, 0), (8, 4, 1), (12, 4, 0)], [(0, 12, 1), (12, 4, 0)], [(2, 2, 0), (4, 4, 1), (8, 8, 1)]],
    "drive": [[(0, 3, 1), (3, 3, 0), (6, 2, 0), (8, 4, 1), (12, 2, 0), (14, 2, 0)], [(0, 2, 1), (2, 2, 0), (4, 4, 1), (8, 6, 1), (14, 2, 0)],
              [(0, 4, 1), (4, 2, 0), (6, 2, 0), (8, 2, 1), (10, 2, 0), (12, 4, 1)], [(0, 6, 1), (6, 2, 0), (8, 8, 1)]],
    "heavy": [[(0, 2, 1), (2, 2, 0), (4, 2, 1), (6, 2, 0), (8, 4, 1), (12, 4, 1)], [(0, 6, 1), (6, 2, 0), (8, 2, 1), (10, 2, 0), (12, 4, 1)],
              [(0, 3, 1), (3, 3, 0), (6, 2, 1), (8, 3, 1), (11, 3, 0), (14, 2, 0)], [(0, 8, 1), (8, 8, 1)]],
    "soft": [[(0, 8, 1), (8, 4, 1), (12, 4, 0)], [(0, 4, 1), (4, 4, 0), (8, 8, 1)], [(0, 12, 1), (12, 4, 0)], [(0, 6, 1), (6, 2, 0), (8, 4, 1), (12, 4, 0)]],
    "bright": [[(0, 2, 1), (2, 2, 0), (4, 4, 1), (8, 2, 1), (10, 2, 0), (12, 4, 1)], [(0, 6, 1), (6, 2, 0), (8, 8, 1)],
               [(0, 4, 1), (4, 2, 0), (6, 2, 0), (8, 4, 1), (12, 2, 0), (14, 2, 0)], [(0, 3, 1), (3, 3, 0), (6, 2, 0), (8, 8, 1)]],
}
FORM = [0, 1, 0, 2, 0, 1, 3, 2, 0, 1, 0, 2, 3, 1, 0, 3]


class Loop:
    def __init__(self, seconds: float):
        self.n = int(seconds * SR)
        self.buf = [0.0] * self.n

    def add(self, sig: Signal, t: float, gain: float = 1.0) -> None:
        s = int(t * SR) % self.n
        n, buf = self.n, self.buf
        for i, v in enumerate(sig):
            buf[(s + i) % n] += v * gain

    def echo(self, delay: float, fb: float, wet: float) -> None:
        d = int(delay * SR)
        src = self.buf[:]
        for rep in range(1, 4):
            g = wet * fb ** (rep - 1)
            for i in range(self.n):
                self.buf[(i + d * rep) % self.n] += src[i] * g


_cache: dict = {}


def _note(m: float, dur: float, shape: str, duty: float = 0.5, vib: bool = False, attack: float = 0.004) -> Signal:
    key = (round(m, 2), round(dur, 4), shape, duty, vib, attack)
    if key not in _cache:
        f = hz(m)
        if vib:
            fr = vibrato([f] * max(1, int(dur * SR)), 5.5, 0.006)
            _cache[key] = envelope(osc(fr, shape, duty=duty), attack, 0.04, 0.75, min(0.12, dur * 0.4))
        else:
            _cache[key] = note(f, dur, shape, duty=duty, attack=attack, release=min(0.1, dur * 0.4))
    return _cache[key]


def _drum(kind: str) -> Signal:
    if kind not in _cache:
        r = random.Random(kind)
        if kind == "kick":
            s = [v * math.exp(-i / (0.07 * SR)) for i, v in enumerate(osc(sweep(150, 42, 0.22, 0.4), "sine"))]
        elif kind == "snare":
            nz = svf(osc([20000] * int(0.16 * SR), "noise", rng=r), 2200, q=0.8)
            tone = osc(sweep(240, 170, 0.16), "triangle")
            s = [(a + 0.5 * b) * math.exp(-i / (0.045 * SR)) for i, (a, b) in enumerate(zip(nz, tone))]
        elif kind == "hat":
            nz = svf(osc([20000] * int(0.05 * SR), "noise", rng=r), 8000, q=0.9, mode="high")
            s = [v * math.exp(-i / (0.012 * SR)) for i, v in enumerate(nz)]
        else:  # tom
            s = [v * math.exp(-i / (0.09 * SR)) for i, v in enumerate(osc(sweep(190, 90, 0.25, 0.5), "triangle"))]
        _cache[kind] = s
    return _cache[kind]


def _melody(rng: random.Random, t: dict) -> list[tuple[float, float, int]]:
    """(start in 16ths, length in 16ths, midi). Strong beats land on chord tones; weak beats move by scale step."""
    key = NOTE[t["key"]]
    scale = [key + s for s in SCALES[t["scale"]]]
    pitches = sorted({p + 12 * o for p in scale for o in (5, 6)})
    centre = 60 + key + (12 if key < 5 else 0)
    prev = centre + 7
    out = []
    bars: dict[int, list] = {}
    for bar, name in enumerate(t["chords"]):
        root, iv = chord(name)
        tones = sorted({root + i + 12 * o for i in iv for o in (5, 6)})
        src = bar - 8 if bar >= 8 and bar < 14 else None          # second half repeats the first, with a new ending
        if src is not None and t["chords"][src] == name:
            notes = bars[src]
        else:
            notes = []
            for (st, ln, strong) in MOTIFS[t["style"]][FORM[bar]]:
                if strong:
                    cands = sorted(tones, key=lambda p: abs(p - prev) + (6 if p == prev else 0) + abs(p - centre - 5) * 0.25)[:2]
                    p = rng.choice(cands)
                else:
                    i = min(range(len(pitches)), key=lambda k: abs(pitches[k] - prev))
                    i = max(0, min(len(pitches) - 1, i + rng.choice([-1, 1, 1, -1, 2])))
                    p = pitches[i]
                notes.append((st, ln, p)); prev = p
            if bar == 15:
                notes = [(0, 12, 60 + key + (12 if key < 5 else 0))]
        bars[bar] = notes
        prev = notes[-1][2]
        out += [(bar * 16 + st, ln, p) for st, ln, p in notes]
    return out


def render(name: str) -> Signal:
    t = TRACKS[name]
    rng = random.Random("music:" + name)
    s16 = 60.0 / t["bpm"] / 4
    bars = len(t["chords"])
    style = t["style"]
    lead, back = Loop(bars * 16 * s16), Loop(bars * 16 * s16)
    lead_shape = {"calm": ("triangle", 0.5), "soft": ("triangle", 0.5), "drive": ("square", 0.25), "heavy": ("square", 0.25), "bright": ("square", 0.5)}[style]
    for st, ln, p in _melody(rng, t):
        lead.add(_note(p, ln * s16 * 0.95, lead_shape[0], lead_shape[1], vib=ln >= 4), st * s16, 0.55)
    lead.echo(s16 * 3, 0.4, 0.22)
    for bar, cname in enumerate(t["chords"]):
        root, iv = chord(cname)
        b0 = bar * 16
        bass = 36 + root if root >= 4 else 48 + root
        tones = [60 + root + i for i in iv]
        if style in ("calm", "soft"):
            for st, ln in ((0, 8), (8, 6), (14, 2)) if style == "calm" else ((0, 6), (6, 6), (12, 4)):
                back.add(_note(bass + (7 if st == 14 else 0), ln * s16 * 0.95, "triangle"), (b0 + st) * s16, 0.6)
            pat = [0, 1, 2, 1, 0, 1, 2, 1] if style == "calm" else [0, 2, 1, 2, 0, 2, 1, 2]
            for k, idx in enumerate(pat):
                back.add(_note(tones[idx] + (12 if k % 4 == 2 else 0), s16 * 1.8, "square", 0.125), (b0 + k * 2) * s16, 0.16)
            if style == "calm":
                for st in (4, 12):
                    back.add(_drum("hat"), (b0 + st) * s16, 0.12)
        else:
            for k in range(8):
                oct_ = 12 if (style == "drive" and k % 2 == 1) or (style == "bright" and k in (3, 7)) else 0
                if style == "heavy":
                    back.add(_note(bass + (12 if k in (3, 6) else 0), s16 * 1.7, "saw"), (b0 + k * 2) * s16, 0.3)
                else:
                    back.add(_note(bass + oct_, s16 * 1.7, "triangle"), (b0 + k * 2) * s16, 0.6)
            for k in range(16):
                idx = (k * (2 if style == "heavy" else 1)) % 3
                back.add(_note(tones[idx] + (12 if k % 4 == 3 else 0), s16 * 0.9, "square", 0.125), (b0 + k) * s16, 0.11 if style != "bright" else 0.13)
            kicks = {"drive": (0, 6, 8, 14), "heavy": (0, 4, 8, 10, 12), "bright": (0, 8, 10)}[style]
            for st in kicks:
                back.add(_drum("kick"), (b0 + st) * s16, 0.8)
            for st in (4, 12):
                back.add(_drum("snare"), (b0 + st) * s16, 0.5)
            for st in range(0, 16, 2):
                back.add(_drum("hat"), (b0 + st) * s16, 0.16 if st % 4 else 0.1)
            if bar % 8 == 7:
                for k, st in enumerate((12, 13, 14, 15)):
                    back.add(_drum("tom" if k < 3 else "snare"), (b0 + st) * s16, 0.45)
    out = [a + b for a, b in zip(lead.buf, back.buf)]
    m = max(abs(v) for v in out) or 1.0
    rms = math.sqrt(sum(v * v for v in out) / len(out))
    gain = min(0.89 / m, 10 ** (-17 / 20) / rms)          # match loops by RMS (-17 dBFS), never clipping
    return [v * gain for v in out]
