"""Retro game SFX recipes. Each recipe takes an RNG so one recipe yields many distinct variants."""
from __future__ import annotations

import random

from .wav import Signal, bitcrush, concat, envelope, finalize, lowpass, mix, note, osc, silence, svf, sweep, tremolo, vibrato


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
    f = r.uniform(500, 720)
    step = r.choice([5 / 4, 4 / 3, 3 / 2])
    a = envelope(osc(sweep(f, f, 0.07), "triangle"), 0.002, 0.02, 0.8, 0.02)
    b = envelope(osc(sweep(f * step, f * step, 0.14), "triangle"), 0.002, 0.04, 0.6, 0.1)
    return concat(a, b)


def cancel(r: random.Random) -> Signal:
    f = r.uniform(400, 620)
    step = r.choice([0.75, 0.667, 0.8, 0.707])
    shape = r.choice(["triangle", "square"])
    a = envelope(osc(sweep(f, f, r.uniform(0.05, 0.08)), shape, duty=0.25), 0.002, 0.02, 0.8, 0.02)
    b = envelope(osc(sweep(f * step, f * step * 0.94, r.uniform(0.11, 0.16)), shape, duty=0.25), 0.002, 0.04, 0.6, 0.1)
    return lowpass(concat(a, b), 5000)


def error(r: random.Random) -> Signal:
    f = r.uniform(170, 230)
    tone = lowpass(mix(osc(sweep(f, f, 0.12), "square", duty=0.5), osc(sweep(f * 1.5, f * 1.5, 0.12), "triangle"), gains=[0.6, 0.5]), 1800)
    buzz = envelope(tone, 0.004, 0.02, 0.8, 0.04)
    return concat(buzz, silence(0.05), buzz)


def pickup(r: random.Random) -> Signal:
    f0 = r.uniform(500, 800)
    sig = osc(sweep(f0, f0 * r.uniform(2, 3), r.uniform(0.08, 0.14), 0.7), "sine")
    return bitcrush(envelope(sig, 0.002, 0.03, 0.7, 0.05), r.choice([5, 6, 8]))


def footstep(r: random.Random) -> Signal:
    dur = r.uniform(0.06, 0.1)
    noise = lowpass(osc(sweep(r.uniform(900, 1600), 300, dur), "noise", rng=r), r.uniform(600, 1100))
    return envelope(noise, 0.001, 0.02, 0.3, dur * 0.7)


# ---------- added in v0.2 ----------
def dash(r):
    d = r.uniform(0.18, 0.28)
    n = osc(sweep(8000, 8000, d), "noise", rng=r)
    return envelope(svf(n, sweep(r.uniform(400, 700), r.uniform(3000, 5000), d, 0.6), q=1.5), 0.01, 0.05, 0.6, d * 0.6)


def whoosh(r):
    d = r.uniform(0.25, 0.4)
    n = osc(sweep(8000, 8000, d), "noise", rng=r)
    up, down = sweep(300, 2400, d / 2, 0.8), sweep(2400, 300, d / 2, 1.4)
    return envelope(svf(n, up + down, q=2.0), d * 0.35, 0.05, 0.8, d * 0.5)


def land(r):
    d = r.uniform(0.1, 0.16)
    thump = osc(sweep(r.uniform(110, 150), 45, d), "sine")
    grit = lowpass(osc(sweep(2500, 600, d), "noise", rng=r), 1400)
    return envelope(mix(thump, grit, gains=[1.0, 0.5]), 0.001, 0.03, 0.4, d * 0.7)


def bounce(r):
    d = r.uniform(0.25, 0.35)
    f0 = r.uniform(180, 260)
    fr = vibrato(sweep(f0, f0 * 2.6, d, 0.5), r.uniform(18, 26), 0.06)
    return envelope(osc(fr, "triangle"), 0.002, 0.06, 0.6, d * 0.5)


def shoot(r):
    d = r.uniform(0.12, 0.2)
    zap = osc(sweep(r.uniform(900, 1300), r.uniform(150, 250), d, 0.4), "square", duty=0.5)
    crack = lowpass(osc(sweep(6000, 2000, 0.04), "noise", rng=r), 4000)
    return envelope(mix(zap, crack, gains=[0.8, 0.6]), 0.001, 0.03, 0.5, d * 0.6)


def shield_block(r):
    d = r.uniform(0.25, 0.4)
    base = r.uniform(520, 760)
    ring = mix(*(osc(sweep(base * k, base * k, d), "sine") for k in (1.0, 2.76, 5.4)), gains=[1.0, 0.6, 0.35])
    tick = osc(sweep(7000, 3000, 0.015), "noise", rng=r)
    return mix(envelope(ring, 0.001, 0.05, 0.3, d * 0.8), envelope(tick, 0.0005, 0.005, 0.2, 0.008), gains=[1.0, 0.7])


def death(r):
    d = r.uniform(0.6, 0.9)
    f0 = r.uniform(500, 700)
    fr = vibrato(sweep(f0, f0 * 0.18, d, 0.7), 9, 0.04)
    return envelope(lowpass(osc(fr, "square", duty=0.5), 3000), 0.003, 0.1, 0.8, d * 0.4)


def charge_up(r):
    d = r.uniform(0.6, 0.9)
    sig = osc(sweep(r.uniform(120, 180), r.uniform(900, 1300), d, 1.3), "saw")
    return envelope(tremolo(lowpass(sig, 3500), r.uniform(14, 22), 0.5), d * 0.6, 0.05, 0.9, 0.06)


def spell(r):
    root = r.choice([659, 698, 784, 880])
    notes = [root * k for k in r.choice([(1, 1.26, 1.5, 2), (1, 1.19, 1.5, 1.78), (2, 1.5, 1.26, 1)])]
    arp = concat(*(note(f, 0.06, "triangle") for f in notes))
    shimmer = envelope(svf(osc(sweep(9000, 9000, len(arp) / 44100 + 0.2), "noise", rng=r), 6000, q=4.0), 0.02, 0.1, 0.5, 0.2)
    return mix(arp, shimmer, gains=[0.9, 0.35])


def heal(r):
    root = r.choice([392, 440, 494])
    d = r.uniform(0.5, 0.7)
    chord = mix(*(osc(sweep(root * k, root * k * 1.06, d), "sine") for k in (1, 1.25, 1.5, 2)), gains=[1, 0.8, 0.7, 0.4])
    return envelope(tremolo(chord, 6, 0.25), d * 0.3, 0.1, 0.8, d * 0.5)


def teleport(r):
    d = r.uniform(0.35, 0.5)
    fr = vibrato(sweep(r.uniform(300, 500), r.uniform(1800, 2600), d, 0.8), r.uniform(28, 40), 0.15)
    return envelope(osc(fr, "triangle"), 0.01, 0.05, 0.8, d * 0.4)


def menu_open(r):
    f, k, sh = r.uniform(480, 720), r.choice([1.5, 1.335, 1.26, 2.0]), r.choice(["triangle", "sine"])
    return concat(note(f, r.uniform(0.035, 0.055), sh), note(f * k, r.uniform(0.07, 0.1), sh))


def menu_close(r):
    f, k, sh = r.uniform(720, 1050), r.choice([1.5, 1.335, 1.26, 2.0]), r.choice(["triangle", "sine"])
    return concat(note(f, r.uniform(0.035, 0.055), sh), note(f / k, r.uniform(0.07, 0.1), sh))


def text_blip(r):
    f = r.uniform(400, 900)
    return envelope(osc(sweep(f, f, 0.035), "square", duty=0.25), 0.001, 0.01, 0.6, 0.012)


def notification(r):
    f = r.uniform(700, 1150)
    k = r.choice([1.335, 1.26, 1.5, 1.19, 0.75])
    sh = r.choice(["sine", "triangle"])
    gap = r.uniform(0.0, 0.05)
    a = envelope(osc(sweep(f, f, r.uniform(0.08, 0.13)), sh), 0.002, 0.03, 0.5, 0.07)
    b = envelope(osc(sweep(f * k, f * k, r.uniform(0.16, 0.26)), sh), 0.002, 0.05, 0.5, 0.15)
    return concat(a, silence(gap), b)


def level_up(r):
    root = r.uniform(440, 700)
    seq = r.choice([[1, 1.26, 1.5, 2], [1, 1.12, 1.26, 1.5, 2], [1, 1.5, 1.26, 2], [1, 1.19, 1.5, 2]])
    step, duty = r.uniform(0.055, 0.085), r.choice([0.25, 0.125, 0.5])
    body = concat(*(note(root * k, step, "square", duty=duty) for k in seq[:-1]))
    return concat(body, note(root * seq[-1], r.uniform(0.25, 0.4), "square", duty=duty, release=0.2))


def game_over(r):
    root = r.uniform(300, 420)
    seq = r.choice([[1.5, 1.19, 1, 0.75], [1.5, 1.335, 1.19, 1], [1.19, 1.12, 1, 0.75], [2, 1.5, 1.19, 1]])
    beat, shape = r.uniform(0.15, 0.22), r.choice(["square", "triangle"])
    return lowpass(concat(*(note(root * k, beat if i < 3 else beat * 2.8, shape, duty=0.5, release=beat * 0.6 if i < 3 else 0.4) for i, k in enumerate(seq))), 2500)


def victory(r):
    root = r.uniform(460, 680)
    beat = r.uniform(0.075, 0.105)
    seq = r.choice([
        [(1, 1), (1, 1), (1, 1), (1.26, 2.2), (1.12, 2.2), (1.5, 5)],
        [(1, 1), (1.26, 1), (1.5, 1), (2, 3), (1.5, 1.5), (2, 5)],
        [(1.5, 1), (1.5, 1), (1.68, 1), (2, 2.2), (1.68, 2.2), (2, 5)],
    ])
    seq = [(k, d * beat) for k, d in seq]
    lead = concat(*(note(root * k, d, "square", duty=0.25, release=d * 0.3) for k, d in seq))
    bass = concat(*(note(root * k / 2, d, "triangle", release=d * 0.3) for k, d in seq))
    return mix(lead, bass, gains=[0.8, 0.6])


CATEGORIES: dict[str, list[str]] = {
    "ui": ["ui_click", "ui_hover", "confirm", "cancel", "error", "menu_open", "menu_close", "text_blip", "notification"],
    "pickups": ["coin", "pickup", "powerup", "heal"],
    "movement": ["jump", "land", "bounce", "dash", "whoosh", "footstep"],
    "combat": ["hit", "explosion", "laser", "shoot", "shield_block", "death", "charge_up"],
    "magic": ["spell", "teleport"],
    "jingles": ["level_up", "game_over", "victory"],
}
# Target loudness (loudest 50 ms, dBFS): UI sits under gameplay; impacts and jingles lead.
TARGET_DB = {"ui": -17.0, "pickups": -13.0, "movement": -14.0, "combat": -12.0, "magic": -13.0, "jingles": -14.0}

RECIPES = {
    "coin": coin, "jump": jump, "laser": laser, "explosion": explosion, "hit": hit, "powerup": powerup,
    "ui_click": ui_click, "ui_hover": ui_hover, "confirm": confirm, "cancel": cancel, "error": error,
    "pickup": pickup, "footstep": footstep,
    "dash": dash, "whoosh": whoosh, "land": land, "bounce": bounce, "shoot": shoot, "shield_block": shield_block,
    "death": death, "charge_up": charge_up, "spell": spell, "heal": heal, "teleport": teleport,
    "menu_open": menu_open, "menu_close": menu_close, "text_blip": text_blip, "notification": notification,
    "level_up": level_up, "game_over": game_over, "victory": victory,
}
CATEGORY_OF = {name: cat for cat, names in CATEGORIES.items() for name in names}


def render(name: str, seed: int) -> Signal:
    return finalize(RECIPES[name](random.Random(f"{name}:{seed}")), target_db=TARGET_DB[CATEGORY_OF[name]])
