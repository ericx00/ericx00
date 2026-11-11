"""Card & Forge SFX: sounds for card games and turn-based battles.
New recipes (not variations of the Retro SFX pack): paper and card handling, coins, anvil and
steam, weapon and shield hits, status effects, turn cues and stings. All synthesised."""
from __future__ import annotations

import math
import random

from .wav import SR, Signal, concat, envelope, finalize, lowpass, mix, n_samples, note, osc, silence, svf, sweep, tremolo, vibrato


def _decay(sig: Signal, tau: float, attack: float = 0.001) -> Signal:
    a = max(1, int(attack * SR))
    return [v * min(1.0, i / a) * math.exp(-i / (tau * SR)) for i, v in enumerate(sig)]


def _root(r: random.Random, opts) -> float:
    """A base pitch from `opts`. Each variation gets its own pitch slot (about half a semitone apart)
    plus a little random drift, so two variations can never land on the same pitch by chance."""
    slot = ((getattr(r, "variant", 1) - 1) % 4 - 1.5) * 0.5
    return r.choice(opts) * 2 ** ((slot + r.uniform(-0.12, 0.12)) / 12)


def _noise(r: random.Random, dur: float, pitch: float = 20000) -> Signal:
    return osc([pitch] * n_samples(dur), "noise", rng=r)


def _metal(r: random.Random, f0: float, dur: float, partials=(1.0, 2.76, 5.4, 8.93, 11.3), tau: float = 0.25, spread: float = 0.01) -> Signal:
    """Inharmonic partials with separate decays: bells, anvils, coins, glass."""
    n = n_samples(dur)
    out = [0.0] * n
    for k, p in enumerate(partials):
        f = f0 * p * (1 + r.uniform(-spread, spread))
        if f > SR / 2.2:
            continue
        g = 1.0 / (1 + k * 0.7)
        t = tau / (1 + k * 0.55)
        ph = r.uniform(0, 6.28)
        w = 2 * math.pi * f / SR
        for i in range(n):
            out[i] += g * math.sin(w * i + ph) * math.exp(-i / (t * SR))
    return out


def _echo(sig: Signal, delay: float = 0.09, fb: float = 0.35, wet: float = 0.4, tail: float = 0.3) -> Signal:
    d = max(1, int(delay * SR))
    out = list(sig) + [0.0] * int(tail * SR)
    buf = [0.0] * len(out)
    for i in range(len(out)):
        dry = out[i]
        echo = buf[i - d] if i >= d else 0.0
        buf[i] = dry + echo * fb
        out[i] = dry + echo * wet
    return out


def _at(base: Signal, sig: Signal, t: float, gain: float = 1.0) -> Signal:
    s = int(t * SR)
    if len(base) < s + len(sig):
        base = base + [0.0] * (s + len(sig) - len(base))
    for i, v in enumerate(sig):
        base[s + i] += v * gain
    return base


def _swish(r, dur, f0, f1, q=1.2, mode="band") -> Signal:
    n = _noise(r, dur)
    return svf(n, sweep(f0, f1, dur, 0.7), q=q, mode=mode)


def _tones(freqs, d, shape="square", duty=0.25, gap=0.0) -> Signal:
    parts = []
    for f in freqs:
        parts.append(note(f, d, shape, duty=duty, release=d * 0.5))
        if gap:
            parts.append(silence(gap))
    return concat(*parts)


# ---------- cards ----------
def card_draw(r):
    d = r.uniform(0.09, 0.14)
    return envelope(_swish(r, d, r.uniform(1800, 2600), r.uniform(5000, 7500), q=0.9), 0.01, 0.03, 0.6, d * 0.5)


def card_play(r):
    d = r.uniform(0.07, 0.1)
    sw = envelope(_swish(r, d, r.uniform(5000, 7000), r.uniform(1500, 2200)), 0.004, 0.02, 0.6, d * 0.5)
    thud = _decay(osc(sweep(r.uniform(150, 190), 70, 0.09), "sine"), 0.03)
    tick = _decay(lowpass(_noise(r, 0.03), 3500), 0.008)
    return _at(_at(sw, thud, d * 0.8, 0.9), tick, d * 0.8, 0.6)


def card_flip(r):
    a = envelope(_swish(r, 0.05, 3000, 6500), 0.003, 0.01, 0.6, 0.03)
    b = _decay(svf(_noise(r, 0.05), r.uniform(1800, 2600), q=2.0), 0.012)
    return _at(a, b, r.uniform(0.06, 0.08), 1.0)


def card_shuffle(r):
    out: Signal = []
    t = 0.0
    n = r.randint(11, 16)
    for k in range(n):
        tick = _decay(svf(_noise(r, 0.03), r.uniform(2200, 4200), q=1.6), r.uniform(0.006, 0.012))
        out = _at(out, tick, t, r.uniform(0.5, 1.0))
        t += r.uniform(0.018, 0.034) * (1.25 - 0.4 * k / n)
    return _at(out, envelope(_swish(r, 0.12, 2500, 5000), 0.02, 0.03, 0.5, 0.06), t, 0.6)


def card_deal(r):
    out: Signal = []
    for k in range(r.randint(3, 5)):
        out = _at(out, card_draw(r), k * r.uniform(0.07, 0.09), 1.0)
    return out


def card_slide(r):
    d = r.uniform(0.18, 0.26)
    return envelope(lowpass(_swish(r, d, r.uniform(900, 1300), r.uniform(1600, 2400), q=0.7), 5000), 0.03, 0.05, 0.7, d * 0.45)


def card_discard(r):
    d = r.uniform(0.1, 0.14)
    sw = envelope(_swish(r, d, r.uniform(4500, 6000), r.uniform(1200, 1700)), 0.005, 0.03, 0.5, d * 0.5)
    return _at(sw, _decay(lowpass(_noise(r, 0.04), 1800), 0.012), d * 0.9, 0.7)


def card_exhaust(r):
    d = r.uniform(0.45, 0.6)
    hiss = envelope(svf(_noise(r, d), sweep(7000, 2500, d), q=0.8, mode="high"), 0.01, 0.1, 0.4, d * 0.6)
    crack: Signal = []
    for _ in range(r.randint(5, 9)):
        crack = _at(crack, _decay(_noise(r, 0.01), 0.002), r.uniform(0, d * 0.8), r.uniform(0.4, 1.0))
    return mix(hiss, crack, gains=[0.8, 0.7])


def card_upgrade(r):
    clang = _metal(r, r.uniform(520, 640), 0.7, tau=0.22)
    hit = _decay(lowpass(_noise(r, 0.04), 4000), 0.01)
    root = _root(r, [784, 880, 988])
    shimmer = concat(*(_decay(osc([root * k] * n_samples(0.09), "triangle"), 0.06) for k in (1, 5 / 4, 3 / 2, 2)))
    return _at(mix(clang, hit, gains=[0.8, 0.6]), shimmer, 0.12, 0.5)


def card_hover(r):
    f = r.uniform(1500, 2100)
    return _decay(osc([f] * n_samples(0.04), "triangle"), 0.012)


def card_select(r):
    f = _root(r, [660, 740, 784])
    return concat(_decay(osc([f] * n_samples(0.04), "square", duty=0.25), 0.02), _decay(osc([f * 1.5] * n_samples(0.07), "square", duty=0.25), 0.03))


def card_invalid(r):
    f = r.uniform(150, 190)
    return concat(note(f, 0.06, "square", duty=0.5, release=0.02), silence(0.025), note(f * 0.84, 0.1, "square", duty=0.5, release=0.05))


# ---------- economy ----------
def coin_drop(r):
    f = r.uniform(2300, 3100)
    out: Signal = []
    t, gap, g = 0.0, r.uniform(0.07, 0.1), 1.0
    for _ in range(r.randint(3, 5)):
        out = _at(out, _metal(r, f * r.uniform(0.98, 1.02), 0.2, partials=(1, 1.6, 2.45), tau=0.05), t, g)
        t += gap; gap *= 0.62; g *= 0.7
    return out


def coins_pile(r):
    out: Signal = []
    for _ in range(r.randint(7, 11)):
        out = _at(out, _metal(r, r.uniform(2000, 3600), 0.15, partials=(1, 1.6, 2.45), tau=0.035), r.uniform(0, 0.32), r.uniform(0.4, 1.0))
    return out


def purchase(r):
    reg = _at(coins_pile(r), _metal(r, r.uniform(1500, 1800), 0.5, partials=(1, 2.0, 3.01), tau=0.18), 0.3, 1.0)
    return reg


def gem_pickup(r):
    f = _root(r, [1568, 1760, 1976])
    a = _metal(r, f, 0.4, partials=(1, 2.0, 3.0, 4.2), tau=0.12)
    return _echo(_at(a, _metal(r, f * 1.5, 0.35, partials=(1, 2.0, 3.0), tau=0.1), 0.07, 0.8), 0.07, 0.3, 0.35, 0.2)


# ---------- forge ----------
def anvil_hit(r):
    f = r.uniform(420, 560)
    return mix(_metal(r, f, 0.9, tau=0.3), _decay(lowpass(_noise(r, 0.05), 5000), 0.012), _decay(osc(sweep(140, 60, 0.1), "sine"), 0.04), gains=[0.9, 0.7, 0.6])


def hammer_tap(r):
    f = r.uniform(900, 1300)
    return mix(_metal(r, f, 0.25, partials=(1, 2.3, 4.1), tau=0.06), _decay(lowpass(_noise(r, 0.03), 3000), 0.008), gains=[0.8, 0.7])


def steam_hiss(r):
    d = r.uniform(0.5, 0.8)
    return envelope(svf(_noise(r, d), sweep(r.uniform(5000, 7000), r.uniform(2500, 3500), d), q=0.6, mode="high"), 0.02, 0.15, 0.5, d * 0.6)


def quench(r):
    d = r.uniform(0.7, 1.0)
    hiss = envelope(svf(_noise(r, d), sweep(9000, 1800, d, 0.5), q=0.7, mode="band"), 0.005, 0.2, 0.35, d * 0.7)
    bub = tremolo(envelope(osc(sweep(300, 180, d * 0.6), "sine"), 0.02, 0.1, 0.4, 0.2), r.uniform(18, 26), 0.9)
    return mix(hiss, bub, gains=[1.0, 0.3])


def overheat(r):
    f = r.uniform(620, 720)
    alarm = concat(*(note(f * k, 0.09, "saw", release=0.03) for k in (1, 1.26, 1, 1.26)))
    return mix(alarm, envelope(svf(_noise(r, 0.5), sweep(3000, 8000, 0.5), q=0.8, mode="high"), 0.05, 0.1, 0.6, 0.2), gains=[0.7, 0.6])


def ember_crackle(r):
    d = r.uniform(0.6, 0.9)
    out: Signal = [0.0] * n_samples(d)
    for _ in range(r.randint(14, 22)):
        out = _at(out, _decay(svf(_noise(r, 0.012), r.uniform(1500, 5000), q=1.5), 0.003), r.uniform(0, d - 0.02), r.uniform(0.3, 1.0))
    bed = envelope(lowpass(_noise(r, d), 500), 0.1, 0.1, 0.6, 0.3)
    return mix(out, bed, gains=[1.0, 0.25])


def fire_whoosh(r):
    d = r.uniform(0.4, 0.6)
    n = svf(_noise(r, d), sweep(r.uniform(300, 500), r.uniform(2200, 3200), d, 0.6), q=1.4)
    return tremolo(envelope(n, 0.08, 0.1, 0.8, d * 0.45), r.uniform(22, 30), 0.35)


def bellows(r):
    d = r.uniform(0.45, 0.6)
    a = envelope(svf(_noise(r, d), sweep(400, 1100, d), q=0.9), 0.15, 0.1, 0.8, 0.15)
    b = envelope(svf(_noise(r, d * 0.8), sweep(1000, 350, d * 0.8), q=0.9), 0.1, 0.1, 0.7, 0.2)
    return concat(a, silence(0.05), b)


# ---------- combat ----------
def slash(r):
    d = r.uniform(0.12, 0.18)
    return envelope(svf(_noise(r, d), sweep(r.uniform(2500, 3500), r.uniform(8000, 10000), d, 0.5), q=2.2), 0.02, 0.03, 0.7, d * 0.5)


def heavy_slash(r):
    d = r.uniform(0.22, 0.3)
    sw = envelope(svf(_noise(r, d), sweep(900, 6500, d, 0.6), q=1.8), 0.05, 0.04, 0.8, d * 0.4)
    return _at(sw, mix(_decay(osc(sweep(170, 55, 0.18), "sine"), 0.07), _decay(lowpass(_noise(r, 0.08), 2200), 0.025), gains=[0.9, 0.8]), d * 0.75, 1.0)


def stab(r):
    a = envelope(svf(_noise(r, 0.05), sweep(6000, 9000, 0.05), q=2.5), 0.003, 0.01, 0.6, 0.03)
    return _at(a, _decay(svf(_noise(r, 0.06), r.uniform(900, 1300), q=1.2), 0.018), 0.04, 1.0)


def blunt_hit(r):
    return mix(_decay(osc(sweep(r.uniform(200, 260), 50, 0.2), "sine"), 0.06), _decay(lowpass(_noise(r, 0.1), r.uniform(1200, 1800)), 0.03), gains=[1.0, 0.8])


def arrow_shot(r):
    twang = _decay(osc(vibrato(sweep(r.uniform(260, 320), 180, 0.14), 40, 0.04), "triangle"), 0.045)
    fl = envelope(svf(_noise(r, 0.16), sweep(4000, 7500, 0.16), q=1.5), 0.02, 0.03, 0.6, 0.1)
    return _at(twang, fl, 0.02, 0.7)


def arrow_hit(r):
    return mix(_decay(svf(_noise(r, 0.05), r.uniform(1500, 2100), q=1.4), 0.014), _decay(osc(vibrato([r.uniform(140, 180)] * n_samples(0.16), 55, 0.08), "triangle"), 0.05), gains=[1.0, 0.6])


def shield_up(r):
    f = r.uniform(700, 860)
    return mix(_metal(r, f, 0.35, partials=(1, 1.5, 2.9, 4.2), tau=0.09), _decay(osc(sweep(260, 420, 0.12), "triangle"), 0.06), gains=[0.8, 0.6])


def shield_hit(r):
    return mix(_metal(r, r.uniform(300, 380), 0.4, partials=(1, 2.2, 3.7, 6.1), tau=0.08), _decay(lowpass(_noise(r, 0.06), 2500), 0.018), gains=[0.8, 0.9])


def shield_break(r):
    out = mix(_metal(r, r.uniform(240, 300), 0.5, partials=(1, 2.2, 3.7, 6.1, 9.2), tau=0.07), _decay(lowpass(_noise(r, 0.2), 5000), 0.05), gains=[0.8, 1.0])
    for _ in range(r.randint(5, 8)):
        out = _at(out, _metal(r, r.uniform(1800, 4200), 0.12, partials=(1, 2.6), tau=0.025), r.uniform(0.06, 0.4), r.uniform(0.2, 0.6))
    return out


def enemy_hurt(r):
    f = r.uniform(170, 240)
    return envelope(osc(vibrato(sweep(f * 1.6, f * 0.7, 0.16), 28, 0.08), "saw"), 0.005, 0.04, 0.6, 0.08)


def enemy_growl(r):
    f = r.uniform(62, 90)
    d = r.uniform(0.5, 0.7)
    g = lowpass(osc(vibrato(sweep(f, f * 0.75, d), r.uniform(22, 34), 0.12), "saw"), 900)
    return tremolo(envelope(g, 0.08, 0.1, 0.8, d * 0.4), r.uniform(26, 38), 0.5)


def enemy_die(r):
    f = r.uniform(300, 420)
    d = r.uniform(0.4, 0.55)
    a = envelope(osc(vibrato(sweep(f, f * 0.25, d, 0.7), 18, 0.06), "square", duty=0.3), 0.005, 0.08, 0.6, d * 0.5)
    return mix(a, envelope(lowpass(_noise(r, d), 1800), 0.01, 0.1, 0.3, d * 0.6), gains=[0.8, 0.5])


def boss_roar(r):
    d = r.uniform(1.0, 1.3)
    f = r.uniform(48, 62)
    g = lowpass(mix(osc(vibrato(sweep(f * 1.4, f, d, 0.4), 17, 0.1), "saw"), osc(sweep(f * 2.03, f * 1.4, d), "square", duty=0.4), gains=[1.0, 0.5]), 1100)
    n = envelope(svf(_noise(r, d), sweep(500, 1600, d), q=0.8), 0.1, 0.2, 0.5, d * 0.5)
    return _echo(mix(tremolo(envelope(g, 0.1, 0.15, 0.85, d * 0.45), 31, 0.45), n, gains=[1.0, 0.35]), 0.12, 0.3, 0.3, 0.4)


# ---------- status ----------
def buff(r):
    root = _root(r, [392, 440, 494])
    return _echo(concat(*(_decay(osc([root * k] * n_samples(0.07), "triangle"), 0.07) for k in (1, 5 / 4, 3 / 2, 2, 5 / 2))), 0.08, 0.3, 0.3, 0.2)


def debuff(r):
    root = _root(r, [330, 370, 392])
    return concat(*(envelope(osc(vibrato([root * k] * n_samples(0.09), 14, 0.03), "saw"), 0.004, 0.03, 0.6, 0.05) for k in (1, 15 / 16, 5 / 6, 2 / 3)))


def strength_up(r):
    f = r.uniform(110, 140)
    return mix(envelope(osc(sweep(f, f * 2.4, 0.3, 1.6), "saw"), 0.01, 0.05, 0.8, 0.08), _at([0.0], _decay(lowpass(_noise(r, 0.08), 3000), 0.025), 0.27, 1.0), gains=[0.8, 0.8])


def burn_tick(r):
    d = r.uniform(0.2, 0.28)
    out = envelope(svf(_noise(r, d), sweep(1200, 4200, d), q=1.3), 0.02, 0.05, 0.6, d * 0.5)
    for _ in range(r.randint(2, 4)):
        out = _at(out, _decay(_noise(r, 0.008), 0.002), r.uniform(0, d), 0.8)
    return out


def poison_bubble(r):
    out: Signal = []
    t = 0.0
    for _ in range(r.randint(3, 5)):
        f = r.uniform(280, 520)
        out = _at(out, _decay(osc(sweep(f, f * r.uniform(1.6, 2.2), 0.07, 2.0), "sine"), 0.03), t, r.uniform(0.6, 1.0))
        t += r.uniform(0.05, 0.1)
    return out


def freeze(r):
    f = r.uniform(2400, 3200)
    out = _metal(r, f, 0.5, partials=(1, 1.48, 2.21, 3.3), tau=0.12)
    for k in range(r.randint(4, 6)):
        out = _at(out, _metal(r, f * r.uniform(1.1, 2.0), 0.1, partials=(1, 1.5), tau=0.02), 0.03 + k * r.uniform(0.02, 0.04), 0.5)
    return _echo(out, 0.06, 0.35, 0.3, 0.25)


def shock(r):
    d = r.uniform(0.22, 0.3)
    z = osc([r.uniform(90, 130)] * n_samples(d), "saw")
    z = [v * (1 if (i // int(SR / r.uniform(45, 70))) % 2 == 0 else 0.15) for i, v in enumerate(z)]
    return mix(envelope(svf(z, sweep(3000, 900, d), q=2.0, mode="high"), 0.002, 0.04, 0.7, d * 0.4), envelope(svf(_noise(r, d), 5200, q=2.0), 0.002, 0.05, 0.4, d * 0.5), gains=[0.9, 0.5])


def heal_soft(r):
    root = _root(r, [523, 587, 659])
    out: Signal = []
    for k, m in enumerate((1, 3 / 2, 2, 5 / 2)):
        out = _at(out, _decay(osc(vibrato([root * m] * n_samples(0.4), 5, 0.004), "sine"), 0.16, attack=0.02), k * 0.08, 0.8)
    return _echo(out, 0.11, 0.35, 0.35, 0.35)


def curse(r):
    f = r.uniform(140, 180)
    d = 0.6
    a = envelope(osc(vibrato(sweep(f * 2, f, d, 0.5), 9, 0.05), "square", duty=0.2), 0.03, 0.1, 0.6, 0.3)
    b = envelope(osc(sweep(f * 2 * 1.06, f * 1.06, d, 0.5), "square", duty=0.2), 0.03, 0.1, 0.6, 0.3)
    return _echo(mix(a, b, gains=[0.6, 0.6]), 0.13, 0.4, 0.35, 0.35)


def block_gain(r):
    f = r.uniform(520, 620)
    return mix(_decay(osc(sweep(f * 0.5, f, 0.09), "triangle"), 0.06), _metal(r, f * 2, 0.2, partials=(1, 2.4), tau=0.05), gains=[0.9, 0.5])


# ---------- flow ----------
def turn_start(r):
    root = _root(r, [523, 587])
    return _echo(_tones([root, root * 3 / 2], 0.09, "square", 0.25), 0.09, 0.25, 0.25, 0.15)


def turn_end(r):
    root = _root(r, [392, 440])
    return mix(_tones([root * 3 / 2, root], 0.08, "triangle"), _decay(lowpass(_noise(r, 0.03), 2500), 0.01), gains=[0.9, 0.5])


def enemy_turn(r):
    root = _root(r, [196, 220])
    return _tones([root, root * 6 / 5, root], 0.08, "saw")


def map_step(r):
    return concat(*(mix(_decay(lowpass(_noise(r, 0.05), r.uniform(900, 1400)), 0.014), _decay(osc(sweep(120, 70, 0.05), "sine"), 0.02), gains=[0.9, 0.6]) + silence(0.07) for _ in range(2)))


def door_open(r):
    d = r.uniform(0.5, 0.7)
    f = r.uniform(110, 150)
    creak = envelope(svf(osc(vibrato(sweep(f, f * 1.9, d, 1.5), 7, 0.06), "saw"), sweep(900, 2200, d), q=3.0), 0.08, 0.1, 0.7, 0.15)
    return _at(creak, mix(_decay(osc(sweep(110, 55, 0.2), "sine"), 0.07), _decay(lowpass(_noise(r, 0.08), 1200), 0.03), gains=[1.0, 0.7]), d, 1.0)


def chest_open(r):
    latch = _metal(r, r.uniform(1400, 1800), 0.12, partials=(1, 2.3), tau=0.03)
    creak = envelope(svf(osc(sweep(140, 260, 0.25, 1.4), "saw"), sweep(800, 1800, 0.25), q=3.0), 0.04, 0.05, 0.6, 0.1)
    root = _root(r, [659, 784])
    spark = concat(*(_decay(osc([root * k] * n_samples(0.07), "triangle"), 0.05) for k in (1, 5 / 4, 3 / 2, 2)))
    return _echo(_at(_at(latch, creak, 0.08, 0.6), spark, 0.33, 0.7), 0.08, 0.3, 0.3, 0.2)


def relic_get(r):
    root = _root(r, [523, 587, 659])
    out: Signal = []
    for k, m in enumerate((1, 5 / 4, 3 / 2, 2, 5 / 2, 3)):
        out = _at(out, _metal(r, root * m, 0.5, partials=(1, 2.0, 3.0), tau=0.16), k * 0.065, 0.8)
    return _echo(out, 0.1, 0.4, 0.4, 0.4)


def rest_campfire(r):
    return _at(ember_crackle(r), heal_soft(r), 0.2, 0.6)


def victory_fanfare(r):
    root = _root(r, [262, 294, 330])
    seq = [(1, 0.12), (1, 0.12), (1, 0.12), (4 / 3, 0.36), (5 / 4, 0.12), (3 / 2, 0.12), (2, 0.6)]
    lead = concat(*(note(root * 2 * k, d, "square", duty=0.25, release=d * 0.35) for k, d in seq))
    harm = concat(*(note(root * 2 * k * 5 / 4 if k < 2 else root * 2 * k * 3 / 4, d, "square", duty=0.125, release=d * 0.35) for k, d in seq))
    bass = concat(*(note(root * k / 2, d, "triangle", release=d * 0.3) for k, d in seq))
    return _echo(mix(lead, harm, bass, gains=[0.7, 0.35, 0.6]), 0.12, 0.3, 0.3, 0.4)


def defeat_sting(r):
    root = _root(r, [220, 247])
    seq = [(1, 0.22), (15 / 16, 0.22), (5 / 6, 0.22), (2 / 3, 0.8)]
    lead = concat(*(envelope(osc(vibrato([root * k] * n_samples(d), 6, 0.01), "square", duty=0.3), 0.01, 0.05, 0.7, d * 0.5) for k, d in seq))
    bass = concat(*(note(root * k / 2, d, "triangle", release=d * 0.4) for k, d in seq))
    return _echo(mix(lead, bass, gains=[0.7, 0.7]), 0.15, 0.4, 0.35, 0.5)


def boss_intro(r):
    root = _root(r, [73.4, 82.4])
    hit = mix(_decay(osc(sweep(root * 2, root, 0.9, 0.3), "saw"), 0.4), _decay(osc([root * 1.5] * n_samples(0.9), "square", duty=0.3), 0.35), _decay(lowpass(_noise(r, 0.3), 900), 0.08), gains=[0.9, 0.5, 0.8])
    out = _at(lowpass(hit, 1800), lowpass(hit, 1500), 0.45, 0.8)
    return _echo(_at(out, _tones([root * 4, root * 4 * 6 / 5, root * 4 * 3 / 2], 0.14, "square", 0.25), 0.9, 0.6), 0.16, 0.4, 0.35, 0.5)


def level_complete(r):
    root = _root(r, [392, 440])
    return _echo(_tones([root, root * 5 / 4, root * 3 / 2, root * 2, root * 3 / 2, root * 2], 0.085, "square", 0.25), 0.1, 0.3, 0.3, 0.3)


# ---------- ui ----------
def ui_tick(r):
    return _decay(svf(_noise(r, 0.02), r.uniform(2800, 3800), q=2.5), 0.005)


def ui_press(r):
    f = r.uniform(420, 520)
    return mix(_decay(osc(sweep(f, f * 0.7, 0.05), "triangle"), 0.02), _decay(lowpass(_noise(r, 0.02), 3000), 0.006), gains=[1.0, 0.6])


def ui_open(r):
    f = r.uniform(300, 360)
    return envelope(osc(sweep(f, f * 2, 0.12, 0.6), "triangle"), 0.01, 0.03, 0.7, 0.05)


def ui_close(r):
    f = r.uniform(600, 720)
    return envelope(osc(sweep(f, f * 0.5, 0.11, 0.6), "triangle"), 0.01, 0.03, 0.7, 0.05)


def ui_tab(r):
    f = _root(r, [880, 988])
    return concat(_decay(osc([f] * n_samples(0.03), "triangle"), 0.015), _decay(osc([f * 4 / 3] * n_samples(0.05), "triangle"), 0.02))


def ui_confirm(r):
    root = _root(r, [523, 587, 659])
    return _tones([root, root * 3 / 2, root * 2], 0.06, "triangle")


def ui_back(r):
    root = _root(r, [523, 587])
    return _tones([root, root * 3 / 4], 0.07, "triangle")


def ui_error(r):
    f = r.uniform(120, 150)
    return concat(note(f, 0.07, "saw", release=0.02), silence(0.03), note(f, 0.1, "saw", release=0.05))


CATEGORIES: dict[str, list[str]] = {
    "cards": ["card_draw", "card_play", "card_flip", "card_shuffle", "card_deal", "card_slide", "card_discard", "card_exhaust", "card_upgrade", "card_hover", "card_select", "card_invalid"],
    "economy": ["coin_drop", "coins_pile", "purchase", "gem_pickup"],
    "forge": ["anvil_hit", "hammer_tap", "steam_hiss", "quench", "overheat", "ember_crackle", "fire_whoosh", "bellows"],
    "combat": ["slash", "heavy_slash", "stab", "blunt_hit", "arrow_shot", "arrow_hit", "shield_up", "shield_hit", "shield_break", "enemy_hurt", "enemy_growl", "enemy_die", "boss_roar"],
    "status": ["buff", "debuff", "strength_up", "burn_tick", "poison_bubble", "freeze", "shock", "heal_soft", "curse", "block_gain"],
    "flow": ["turn_start", "turn_end", "enemy_turn", "map_step", "door_open", "chest_open", "relic_get", "rest_campfire", "victory_fanfare", "defeat_sting", "boss_intro", "level_complete"],
    "ui": ["ui_tick", "ui_press", "ui_open", "ui_close", "ui_tab", "ui_confirm", "ui_back", "ui_error"],
}
TARGET_DB = {"cards": -16.0, "economy": -14.0, "forge": -13.0, "combat": -12.0, "status": -13.5, "flow": -13.5, "ui": -18.0}
RECIPES = {name: globals()[name] for names in CATEGORIES.values() for name in names}
CATEGORY_OF = {name: cat for cat, names in CATEGORIES.items() for name in names}


def render(name: str, seed: int) -> Signal:
    r = random.Random(f"deck:{name}:{seed}")
    r.variant = seed
    return finalize(RECIPES[name](r), target_db=TARGET_DB[CATEGORY_OF[name]])
