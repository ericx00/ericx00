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


def _blep(t: float, dt: float) -> float:
    """PolyBLEP correction: removes the aliasing a naive square/saw makes at each jump."""
    if t < dt:
        t /= dt
        return t + t - t * t - 1.0
    if t > 1.0 - dt:
        t = (t - 1.0) / dt
        return t * t + t + t + 1.0
    return 0.0


def osc(freqs: list[float], shape: str = "sine", duty: float = 0.5, rng: random.Random | None = None) -> Signal:
    """Band-limited oscillators (square and saw use PolyBLEP, so high sweeps don't alias)."""
    rng = rng or random.Random(0)
    out, phase = [], 0.0
    held, hold_left = 0.0, 0
    for f in freqs:
        dt = min(0.49, max(f, 1e-6) / SR)
        phase = (phase + f / SR) % 1.0
        if shape == "sine":
            v = math.sin(2 * math.pi * phase)
        elif shape == "square":
            v = (1.0 if phase < duty else -1.0) + _blep(phase, dt) - _blep((phase - duty) % 1.0, dt)
        elif shape == "saw":
            v = 2 * phase - 1 - _blep(phase, dt)
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


def svf(sig: Signal, cutoffs: list[float] | float, q: float = 0.7, mode: str = "band") -> Signal:
    """State-variable filter with a per-sample cutoff (sweeps for whooshes, wah, resonance)."""
    n = len(sig)
    cs = cutoffs if isinstance(cutoffs, list) else [cutoffs] * n
    low = band = 0.0
    damp = 1.0 / max(q, 0.05)
    out = []
    for i, v in enumerate(sig):
        fc = min(cs[min(i, len(cs) - 1)], SR / 6)
        f = 2 * math.sin(math.pi * fc / SR)
        low += f * band
        high = v - low - damp * band
        band += f * high
        out.append(band if mode == "band" else low if mode == "low" else high)
    return out


def vibrato(freqs: list[float], rate: float, depth: float) -> list[float]:
    return [f * (1 + depth * math.sin(2 * math.pi * rate * i / SR)) for i, f in enumerate(freqs)]


def tremolo(sig: Signal, rate: float, depth: float) -> Signal:
    return [v * (1 - depth * (0.5 + 0.5 * math.sin(2 * math.pi * rate * i / SR))) for i, v in enumerate(sig)]


def note(freq: float, seconds: float, shape: str = "square", duty: float = 0.5, attack: float = 0.003, release: float | None = None) -> Signal:
    rel = seconds * 0.4 if release is None else release
    return envelope(osc(sweep(freq, freq, seconds), shape, duty=duty), attack, 0.03, 0.75, rel)


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


def short_term_db(sig: Signal, window: float = 0.05) -> float:
    """Loudest 50 ms RMS window in dBFS: a simple proxy for how loud a short SFX sounds."""
    n = max(1, int(window * SR))
    if len(sig) <= n:
        rms = math.sqrt(sum(v * v for v in sig) / max(1, len(sig)))
    else:
        sq = [v * v for v in sig]
        acc = sum(sq[:n]); best = acc
        for i in range(n, len(sq)):
            acc += sq[i] - sq[i - n]
            best = max(best, acc)
        rms = math.sqrt(best / n)
    return 20 * math.log10(rms + 1e-12)


def finalize(sig: Signal, peak: float = 0.89, target_db: float | None = None) -> Signal:
    """DC removal -> click-free edge fades -> level. With target_db, sounds are matched by
    loudness (short-term RMS), never exceeding the peak ceiling (about -1 dBFS)."""
    if not sig:
        return sig
    mean = sum(sig) / len(sig)
    faded = fade_edges([v - mean for v in sig])
    m = max(abs(v) for v in faded) or 1.0
    gain = peak / m
    if target_db is not None:
        gain = min(gain, 10 ** ((target_db - short_term_db(faded)) / 20))
    return [v * gain for v in faded]


Recipe = Callable[[random.Random], Signal]
