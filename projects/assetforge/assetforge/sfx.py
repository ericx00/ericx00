"""Retro game SFX recipes. Each recipe takes an RNG so one recipe yields many distinct variants."""
from __future__ import annotations

import random

from .wav import Signal, bitcrush, concat, envelope, finalize, lowpass, mix, osc, silence, sweep


def coin(r: random.Random) -> Signal:
    base = r.choice([988, 1046, 1175, 1318])
    step = r.choice([4 / 3, 3 / 2, 5 / 4])
    shape = r.choice(["square", "triangle"])
    a = envelope(osc(sweep(base, base, 0.06), shape, duty=0.25), 0.002, 0.02, 0.8, 0.01)
    b = envelope(osc(sweep(base * step, base * step, r.uniform(0.18, 0.3)), shape, duty=0.25), 0.002, 0.05, 0.6, 0.15)
    return concat(a, b)


def jump(r: random.Random) -> Signal:
    f0 = r.uniform(180, 300)
    sig = osc(sweep(f0, f0 * r.uniform(2.2, 3.5), r.uniform(0.18, 0.28), 0.6), "square", duty=r.choice([0.25, 0.5]))
    return envelope(sig, 0.003, 0.08, 0.5, 0.08)


def laser(r: random.Random) -> Signal:
    f0 = r.uniform(1400, 2400)
    sig = osc(sweep(f0, r.uniform(120, 300), r.uniform(0.15, 0.3), 0.5), r.choice(["saw", "square"]), duty=0.3)
    return envelope(sig, 0.001, 0.05, 0.6, 0.1)


def explosion(r: random.Random) -> Signal:
    dur = r.uniform(0.6, 1.1)
    noise = osc(sweep(r.uniform(2500, 4000), 60, dur, 0.4), "noise", rng=r)
    noise = lowpass(noise, r.uniform(1200, 2400))
    boom = osc(sweep(90, 35, dur * 0.6), "sine")
    return envelope(mix(noise, boom, gains=[1.0, 0.8]), 0.002, 0.15, 0.4, dur * 0.6)


def hit(r: random.Random) -> Signal:
    dur = r.uniform(0.1, 0.18)
    noise = lowpass(osc(sweep(3000, 800, dur), "noise", rng=r), 2500)
    thump = osc(sweep(r.uniform(180, 260), 60, dur), "square", duty=0.5)
    return envelope(mix(noise, thump, gains=[0.8, 0.6]), 0.001, 0.04, 0.3, dur * 0.6)


def powerup(r: random.Random) -> Signal:
    root = r.choice([262, 294, 330, 349])
    scale = r.choice([[1, 5 / 4, 3 / 2, 2], [1, 9 / 8, 5 / 4, 3 / 2, 2], [1, 6 / 5, 3 / 2, 2, 12 / 5]])
    note = r.uniform(0.05, 0.08)
    shape = r.choice(["square", "triangle"])
    return concat(*(envelope(osc(sweep(root * k * 2, root * k * 2, note), shape, duty=0.25), 0.002, 0.02, 0.8, 0.02) for k in scale))


def ui_click(r: random.Random) -> Signal:
    f = r.uniform(1800, 3200)
    return envelope(osc(sweep(f, f * 0.6, 0.03), r.choice(["sine", "triangle"])), 0.0005, 0.01, 0.3, 0.015)


def ui_hover(r: random.Random) -> Signal:
    f = r.uniform(600, 900)
    return envelope(osc(sweep(f, f * 1.15, 0.05), "sine"), 0.004, 0.02, 0.4, 0.03)


def confirm(r: random.Random) -> Signal:
    f = r.choice([523, 587, 659, 698])
    step = r.choice([5 / 4, 4 / 3, 3 / 2])
    a = envelope(osc(sweep(f, f, 0.07), "triangle"), 0.002, 0.02, 0.8, 0.02)
    b = envelope(osc(sweep(f * step, f * step, 0.14), "triangle"), 0.002, 0.04, 0.6, 0.1)
    return concat(a, b)


def cancel(r: random.Random) -> Signal:
    f = r.choice([440, 494, 523])
    a = envelope(osc(sweep(f, f, 0.07), "triangle"), 0.002, 0.02, 0.8, 0.02)
    b = envelope(osc(sweep(f * 0.75, f * 0.7, 0.14), "triangle"), 0.002, 0.04, 0.6, 0.1)
    return concat(a, b)


def error(r: random.Random) -> Signal:
    f = r.uniform(140, 200)
    buzz = envelope(osc(sweep(f, f, 0.12), "square", duty=0.5), 0.002, 0.02, 0.8, 0.03)
    return concat(buzz, silence(0.04), buzz)


def pickup(r: random.Random) -> Signal:
    f0 = r.uniform(500, 800)
    sig = osc(sweep(f0, f0 * r.uniform(2, 3), r.uniform(0.08, 0.14), 0.7), "sine")
    return bitcrush(envelope(sig, 0.002, 0.03, 0.7, 0.05), r.choice([5, 6, 8]))


def footstep(r: random.Random) -> Signal:
    dur = r.uniform(0.06, 0.1)
    noise = lowpass(osc(sweep(r.uniform(900, 1600), 300, dur), "noise", rng=r), r.uniform(600, 1100))
    return envelope(noise, 0.001, 0.02, 0.3, dur * 0.7)


RECIPES = {
    "coin": coin, "jump": jump, "laser": laser, "explosion": explosion, "hit": hit, "powerup": powerup,
    "ui_click": ui_click, "ui_hover": ui_hover, "confirm": confirm, "cancel": cancel, "error": error,
    "pickup": pickup, "footstep": footstep,
}


def render(name: str, seed: int) -> Signal:
    return finalize(RECIPES[name](random.Random(f"{name}:{seed}")))
