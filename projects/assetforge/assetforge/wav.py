"""Tiny synthesiser: oscillators, envelopes, sweeps, filters -> 16-bit mono WAV."""
from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path
from typing import Callable

SR = 44100
Signal = list[float]


def n_samples(seconds: float) -> int:
    return max(1, int(seconds * SR))


def sweep(f0: float, f1: float, seconds: float, curve: float = 1.0) -> list[float]:
    """Per-sample frequency moving from f0 to f1 (curve > 1 = slow start, < 1 = fast start)."""
    n = n_samples(seconds)
    return [f0 + (f1 - f0) * ((i / max(1, n - 1)) ** curve) for i in range(n)]


def osc(freqs: list[float], shape: str = "sine", duty: float = 0.5, rng: random.Random | None = None) -> Signal:
    rng = rng or random.Random(0)
    out, phase = [], 0.0
    held, hold_left = 0.0, 0
    for f in freqs:
        phase = (phase + f / SR) % 1.0
        if shape == "sine":
            v = math.sin(2 * math.pi * phase)
        elif shape == "square":
            v = 1.0 if phase < duty else -1.0
        elif shape == "saw":
            v = 2 * phase - 1
        elif shape == "triangle":
            v = 4 * abs(phase - 0.5) - 1
        elif shape == "noise":
            # sample-and-hold noise: frequency controls the "pitch" of the noise
            if hold_left <= 0:
                held = rng.uniform(-1, 1)
                hold_left = max(1, int(SR / max(f, 1)))
            hold_left -= 1
            v = held
        else:
            raise ValueError(f"unknown shape {shape}")
        out.append(v)
    return out


def envelope(sig: Signal, attack: float = 0.005, decay: float = 0.05, sustain: float = 0.7, release: float = 0.1) -> Signal:
    n = len(sig)
    a, d, r = int(attack * SR), int(decay * SR), int(release * SR)
    out = []
    for i, v in enumerate(sig):
        if i < a:
            g = i / max(1, a)
        elif i < a + d:
            g = 1 - (1 - sustain) * (i - a) / max(1, d)
        else:
            g = sustain
        if i >= n - r:
            g *= max(0.0, (n - i) / max(1, r))
        out.append(v * g)
    return out


def lowpass(sig: Signal, cutoff: float) -> Signal:
    rc = 1 / (2 * math.pi * cutoff)
    alpha = (1 / SR) / (rc + 1 / SR)
    out, y = [], 0.0
    for v in sig:
        y += alpha * (v - y)
        out.append(y)
    return out


def mix(*sigs: Signal, gains: list[float] | None = None) -> Signal:
    n = max(len(s) for s in sigs)
    gains = gains or [1.0] * len(sigs)
    return [sum(s[i] * g for s, g in zip(sigs, gains) if i < len(s)) for i in range(n)]


def concat(*sigs: Signal) -> Signal:
    return [v for s in sigs for v in s]


def silence(seconds: float) -> Signal:
    return [0.0] * n_samples(seconds)


def bitcrush(sig: Signal, bits: int = 6) -> Signal:
    q = 2 ** (bits - 1)
    return [round(v * q) / q for v in sig]


def normalize(sig: Signal, peak: float = 0.89) -> Signal:
    """Peak-normalise to about -1 dBFS; also removes DC offset."""
    if not sig:
        return sig
    mean = sum(sig) / len(sig)
    sig = [v - mean for v in sig]
    m = max(abs(v) for v in sig) or 1.0
    return [v * peak / m for v in sig]


def fade_edges(sig: Signal, ms: float = 3) -> Signal:
    """Short fades so the files never click at start/end."""
    k = min(len(sig) // 2, int(SR * ms / 1000))
    out = sig[:]
    for i in range(k):
        g = i / k
        out[i] *= g
        out[-1 - i] *= g
    return out


def write_wav(path: str | Path, sig: Signal) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in sig)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(frames)
    return p


def finalize(sig: Signal, peak: float = 0.89) -> Signal:
    """DC removal -> click-free edge fades -> peak scaling (in that order so very short
    sounds still reach full level and the first/last samples stay at exactly zero)."""
    if not sig:
        return sig
    mean = sum(sig) / len(sig)
    faded = fade_edges([v - mean for v in sig])
    m = max(abs(v) for v in faded) or 1.0
    return [v * peak / m for v in faded]


Recipe = Callable[[random.Random], Signal]
