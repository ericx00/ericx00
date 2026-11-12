"""One sound per VFX animation, timed to the visual (same synth as the other packs, new recipes)."""
from __future__ import annotations

import random

from . import cardsfx as K
from .cardsfx import _at, _decay, _echo, _metal, _noise, _root, _swish, _tones
from .wav import Signal, concat, envelope, finalize, lowpass, mix, n_samples, osc, silence, svf, sweep, tremolo, vibrato


def explosion(r):
    d = r.uniform(0.7, 1.0)
    n = lowpass(_noise(r, d), r.uniform(1400, 2200))
    return mix(envelope(n, 0.002, 0.15, 0.4, d * 0.6), _decay(osc(sweep(r.uniform(100, 130), 36, d * 0.7), "sine"), 0.22), gains=[1.0, 0.9])


def pop(r):
    f = _root(r, [300, 360])
    return mix(_decay(osc(sweep(f * 2, f * 0.6, 0.12), "sine"), 0.04), _decay(lowpass(_noise(r, 0.1), 3000), 0.03), gains=[0.9, 0.7])


def hit(r):
    return mix(_decay(svf(_noise(r, 0.07), r.uniform(1800, 2600), q=1.2), 0.02), _decay(osc(sweep(r.uniform(200, 260), 80, 0.09), "triangle"), 0.03), gains=[1.0, 0.8])


def hit_heavy(r):
    return _at(K.blunt_hit(r), _metal(r, r.uniform(1500, 1900), 0.2, partials=(1, 2.4, 3.9), tau=0.05), 0.0, 0.5)


def slash_double(r):
    return _at(K.slash(r), K.slash(r), r.uniform(0.1, 0.13), 1.0)


def pierce(r):
    return _at(envelope(_swish(r, 0.09, 3000, 9000, q=2.0), 0.005, 0.02, 0.7, 0.04), _decay(svf(_noise(r, 0.05), r.uniform(1300, 1700), q=1.4), 0.015), 0.07, 1.0)


def magic_burst(r):
    root = _root(r, [392, 440, 523])
    ring = _metal(r, root * 2, 0.6, partials=(1, 1.5, 2.0, 3.0), tau=0.18)
    sw = envelope(_swish(r, 0.3, 600, 4500, q=1.5), 0.02, 0.05, 0.6, 0.15)
    return _echo(mix(ring, sw, gains=[0.8, 0.6]), 0.08, 0.35, 0.35, 0.3)


def shockwave(r):
    d = r.uniform(0.45, 0.6)
    return mix(_decay(osc(sweep(r.uniform(140, 170), 40, d), "sine"), 0.16), envelope(svf(_noise(r, d), sweep(2500, 300, d, 0.6), q=0.9), 0.005, 0.1, 0.4, d * 0.6), gains=[1.0, 0.7])


def nova(r):
    root = _root(r, [659, 784])
    hit_ = _metal(r, root, 0.7, partials=(1, 2.0, 3.0, 4.0, 5.0), tau=0.2)
    return _echo(mix(hit_, envelope(_swish(r, 0.25, 2000, 9000, q=1.2), 0.01, 0.05, 0.5, 0.15), gains=[0.9, 0.5]), 0.1, 0.4, 0.4, 0.35)


def puff(r):
    d = r.uniform(0.25, 0.35)
    return envelope(lowpass(_swish(r, d, 900, 300, q=0.8), 1800), 0.02, 0.06, 0.5, d * 0.6)


def land(r):
    return mix(_decay(osc(sweep(r.uniform(120, 150), 55, 0.12), "sine"), 0.04), envelope(lowpass(_noise(r, 0.22), 1100), 0.005, 0.05, 0.4, 0.14), gains=[0.9, 0.8])


def fire_loop(r):
    return K.ember_crackle(r)


def fire_pillar(r):
    return _at(K.fire_whoosh(r), K.ember_crackle(r), 0.15, 0.6)


def sparkle(r):
    root = _root(r, [1568, 1760, 2093])
    out: Signal = []
    for k in range(5):
        out = _at(out, _metal(r, root * r.choice([1, 1.25, 1.5, 2]), 0.25, partials=(1, 2.0), tau=0.07), k * r.uniform(0.07, 0.1), r.uniform(0.5, 1.0))
    return out


def twinkle(r):
    root = _root(r, [1319, 1568])
    return _echo(_at(_metal(r, root, 0.35, partials=(1, 2.0, 3.0), tau=0.1), _metal(r, root * 1.5, 0.3, partials=(1, 2.0), tau=0.08), 0.06, 0.8), 0.07, 0.3, 0.3, 0.2)


def lightning(r):
    crack = _decay(_noise(r, 0.05), 0.012)
    d = r.uniform(0.5, 0.7)
    rumble = envelope(lowpass(_noise(r, d), r.uniform(500, 800)), 0.005, 0.15, 0.4, d * 0.6)
    return _at(_at(crack, K.shock(r), 0.01, 0.8), rumble, 0.04, 0.9)


def orb_cast(r):
    f = _root(r, [330, 392])
    d = 0.35
    return tremolo(envelope(osc(vibrato(sweep(f, f * 1.8, d, 1.4), 9, 0.02), "triangle"), 0.03, 0.05, 0.8, 0.1), r.uniform(16, 22), 0.4)


def orb_impact(r):
    f = _root(r, [220, 262])
    return mix(_decay(osc(sweep(f * 2, f * 0.5, 0.2), "square", duty=0.3), 0.07), _decay(lowpass(_noise(r, 0.15), 2800), 0.04), gains=[0.8, 0.8])


def beam(r):
    f = _root(r, [196, 220])
    d = r.uniform(0.5, 0.6)
    a = lowpass(mix(osc([f] * n_samples(d), "saw"), osc([f * 1.505] * n_samples(d), "saw"), gains=[0.6, 0.5]), 2600)
    return mix(tremolo(envelope(a, 0.04, 0.05, 0.85, 0.15), r.uniform(28, 36), 0.35), envelope(svf(_noise(r, d), 5200, q=1.5), 0.03, 0.05, 0.5, 0.2), gains=[0.9, 0.4])


def portal(r):
    f = _root(r, [110, 131])
    d = 0.9
    a = osc(vibrato(sweep(f, f * 1.5, d, 0.7), 5.5, 0.05), "triangle")
    b = osc(vibrato(sweep(f * 2.01, f * 3.02, d, 0.7), 5.5, 0.05), "sine")
    return _echo(tremolo(envelope(mix(a, b, gains=[0.8, 0.5]), 0.15, 0.1, 0.8, 0.3), 7, 0.4), 0.13, 0.4, 0.35, 0.3)


def charge(r):
    f = _root(r, [147, 165])
    d = r.uniform(0.6, 0.75)
    return mix(envelope(osc(sweep(f, f * 4, d, 1.8), "saw"), 0.05, 0.05, 0.9, 0.04), envelope(svf(_noise(r, d), sweep(500, 6000, d, 1.6), q=1.6), 0.1, 0.05, 0.8, 0.04), gains=[0.6, 0.5])


def pickup(r):
    root = _root(r, [784, 880, 988])
    return _tones([root, root * 1.5], 0.07, "square", 0.25)


def splash(r):
    d = r.uniform(0.35, 0.45)
    out = envelope(svf(_noise(r, d), sweep(1500, 4500, d, 0.5), q=0.8), 0.004, 0.08, 0.4, d * 0.6)
    for _ in range(r.randint(3, 5)):
        f = r.uniform(500, 1100)
        out = _at(out, _decay(osc(sweep(f, f * 1.8, 0.05, 2.0), "sine"), 0.02), r.uniform(0.1, d), 0.6)
    return out


def levelup(r):
    root = _root(r, [392, 440])
    return _echo(_tones([root, root * 5 / 4, root * 3 / 2, root * 2, root * 5 / 2, root * 3], 0.075, "square", 0.25), 0.1, 0.35, 0.35, 0.35)


def whirl(r):
    d = r.uniform(0.7, 0.9)
    return tremolo(envelope(svf(_noise(r, d), sweep(500, 1500, d), q=2.0), 0.15, 0.1, 0.8, 0.25), r.uniform(9, 13), 0.6)


def shot(r):
    return mix(_decay(lowpass(_noise(r, 0.12), r.uniform(3500, 5000)), 0.03), _decay(osc(sweep(r.uniform(260, 320), 70, 0.1), "square", duty=0.5), 0.03), gains=[1.0, 0.7])


def aura(r):
    f = _root(r, [262, 294])
    d = 0.9
    a = mix(osc(vibrato([f] * n_samples(d), 4, 0.01), "sine"), osc([f * 1.5] * n_samples(d), "sine"), osc([f * 2] * n_samples(d), "triangle"), gains=[0.6, 0.4, 0.25])
    return tremolo(envelope(a, 0.2, 0.1, 0.8, 0.35), 6, 0.3)


def meteor(r):
    fall = envelope(svf(_noise(r, 0.45), sweep(4500, 700, 0.45, 0.8), q=1.6), 0.1, 0.05, 0.9, 0.02)
    return _at(fall, explosion(r), 0.42, 1.0)


def rune(r):
    root = _root(r, [196, 220])
    out: Signal = []
    for k, m in enumerate((1, 6 / 5, 3 / 2, 2)):
        out = _at(out, _metal(r, root * 2 * m, 0.7, partials=(1, 2.0, 3.0), tau=0.25), k * 0.11, 0.8)
    return _echo(out, 0.14, 0.45, 0.4, 0.4)


RECIPES = {
    "explosion": explosion, "pop": pop, "hit": hit, "hit_heavy": hit_heavy, "slash": K.slash, "slash_double": slash_double, "slash_heavy": K.heavy_slash,
    "pierce": pierce, "magic_burst": magic_burst, "shockwave": shockwave, "nova": nova, "puff": puff, "land": land, "fire_loop": fire_loop,
    "fire_pillar": fire_pillar, "sparkle": sparkle, "twinkle": twinkle, "heal": K.heal_soft, "buff": K.buff, "debuff": K.debuff, "lightning": lightning,
    "orb_cast": orb_cast, "orb_impact": orb_impact, "beam": beam, "shield": K.shield_up, "portal": portal, "charge": charge, "pickup": pickup,
    "splash": splash, "levelup": levelup, "bubbles": K.poison_bubble, "freeze": K.freeze, "whirl": whirl, "shot": shot, "aura": aura, "meteor": meteor, "rune": rune,
}
# Sounds whose recipe also appears in the Card & Forge SFX set (rendered here with different seeds).
SHARED = sorted(n for n, f in RECIPES.items() if f.__module__ == K.__name__)


def render(name: str, seed: int) -> Signal:
    r = random.Random(f"vfx:{name}:{seed}")
    r.variant = seed
    return finalize(RECIPES[name](r), target_db=-13.0)
