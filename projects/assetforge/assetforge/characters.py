"""Designed, animated characters (32x32 frames, side view facing right).

Humanoids use a tiny pose rig: back limbs, torso, head and front limbs are placed per frame,
so walk cycles, swings and falls are real motion rather than shifted copies.
Every character exports the same animation set: idle(4) move(6) attack(4) hurt(2) death(5).
"""
from __future__ import annotations

import math
import random

from .draw import line, polygon, ring
from .png import CLEAR, Canvas, RGBA, hex_to_rgba, shade

OUT = hex_to_rgba("#1a1423")
WHITE = (255, 255, 255, 255)
F = 32            # frame size
GROUND = 30       # feet rest on this row
ANIMS = {"idle": 4, "move": 6, "attack": 4, "hurt": 2, "death": 5}


def ramp(h: str) -> tuple[RGBA, RGBA, RGBA]:
    c = hex_to_rgba(h)
    return shade(c, 1.35), c, shade(c, 0.68)


# ------------------------------------------------------------------ helpers
def _pt(x0: float, y0: float, ang: float, length: float) -> tuple[int, int]:
    """Point at `length` from (x0,y0); angle 0 = straight down, positive swings toward the facing side (+x)."""
    a = math.radians(ang)
    return round(x0 + math.sin(a) * length), round(y0 + math.cos(a) * length)


def flash(c: Canvas) -> Canvas:
    out = Canvas(c.w, c.h)
    for y in range(c.h):
        out.px[y] = [p if (not p[3] or p == OUT) else WHITE for p in c.px[y]]
    return out


def dissolve(c: Canvas, amount: float, seed: int) -> Canvas:
    rng = random.Random(seed)
    out = Canvas(c.w, c.h)
    for y in range(c.h):
        out.px[y] = [CLEAR if (p[3] and rng.random() < amount) else p for p in c.px[y]]
    return out


def lie_down(c: Canvas) -> Canvas:
    """Rotate a standing frame 90° (head toward -x) and rest it on the ground line."""
    rot = Canvas(F, F)
    for y in range(F):
        for x in range(F):
            p = c.px[y][x]
            if p[3]:
                rot.set(y, F - 1 - x, p)  # 90° counter-clockwise
    ys = [y for y in range(F) for x in range(F) if rot.px[y][x][3]]
    xs = [x for y in range(F) for x in range(F) if rot.px[y][x][3]]
    if not ys:
        return rot
    out = Canvas(F, F)
    dx = (F - (max(xs) - min(xs) + 1)) // 2 - min(xs)
    out.blit(rot, dx, GROUND - max(ys))
    return out


def shift(c: Canvas, dx: int, dy: int) -> Canvas:
    out = Canvas(c.w, c.h)
    out.blit(c, dx, dy)
    return out


# ------------------------------------------------------------------ humanoid rig
def humanoid(spec: dict, pose: dict) -> Canvas:
    """Draw one frame. pose keys: by (bob), lean, fl/bl (leg dx, lift), fa/ba (arm angles), wa (weapon extra angle), crouch."""
    c = Canvas(F, F)
    by, lean = pose.get("by", 0), pose.get("lean", 0)
    crouch = pose.get("crouch", 0)
    hip_x, hip_y = 15 + lean, GROUND - 7 + by + crouch
    sh_y = hip_y - spec.get("torso", 7)
    skin, cloth, cloth2, metal = spec["skin"], spec["cloth"], spec["cloth2"], spec["metal"]
    legc, bootc = spec.get("legs", ramp("#3a3f52")), spec.get("boots", ramp("#5a3820"))

    def leg(dx: int, lift: int, back: bool):
        col = legc[2] if back else legc[1]
        fx, fy = hip_x + dx, GROUND - lift
        kx, ky = (hip_x + fx) // 2 + (1 if lift else 0), (hip_y + fy) // 2
        line(c, hip_x, hip_y, kx, ky, col, 2)
        line(c, kx, ky, fx, fy - 1, col, 2)
        b = bootc[2] if back else bootc[1]
        c.fill_rect(fx - 1, fy - 1, 4, 2, b)

    def arm(ang: float, back: bool):
        col = (cloth[2] if back else cloth[1]) if spec.get("sleeves", True) else (skin[2] if back else skin[1])
        sx = hip_x + (0 if back else 1)
        ex, ey = _pt(sx, sh_y + 1, ang, 6)
        line(c, sx, sh_y + 1, ex, ey, col, 2)
        c.disc(ex + 0.5, ey + 0.5, 1.3, skin[2] if back else skin[1])
        return ex, ey

    # back layer
    if not spec.get("robe"):
        leg(*pose.get("bl", (-1, 0)), back=True)
    if spec.get("back_item"):
        spec["back_item"](c, hip_x, sh_y, metal)
    arm(pose.get("ba", -10), back=True)
    # torso
    if spec.get("robe"):
        polygon(c, [(hip_x - 3, sh_y), (hip_x + 4, sh_y), (hip_x + 6 + lean // 2, GROUND - 1), (hip_x - 5, GROUND - 1)], cloth[1])
        polygon(c, [(hip_x + 1, sh_y + 1), (hip_x + 4, sh_y), (hip_x + 6 + lean // 2, GROUND - 1), (hip_x + 2, GROUND - 1)], cloth[2])
        c.fill_rect(hip_x - 4, hip_y - 1, 9, 1, cloth2[1])
        for dx, (lx, lift) in ((0, pose.get("fl", (1, 0))),):  # boots peek out under the robe
            c.fill_rect(hip_x + lx - 1, GROUND - 1 - lift, 4, 2, bootc[1])
    else:
        c.fill_rect(hip_x - 3, sh_y, 7, hip_y - sh_y + 1, cloth[1])
        c.fill_rect(hip_x - 3, sh_y, 7, 1, cloth[0])
        c.fill_rect(hip_x + 2, sh_y + 1, 2, hip_y - sh_y, cloth[2])
        c.fill_rect(hip_x - 3, hip_y - 1, 7, 1, cloth2[1])              # belt
        c.set(hip_x + 1, hip_y - 1, metal[0])                           # buckle
    if spec.get("detail"):
        spec["detail"](c, hip_x, hip_y, sh_y)
    # head
    hx, hy = hip_x - 2, sh_y - 7
    c.fill_rect(hx, hy, 6, 6, skin[1])
    c.fill_rect(hx, hy + 5, 6, 1, skin[2])
    c.set(hx + 4, hy + 2, OUT)                                          # eye (facing right)
    if spec.get("eye"):
        c.set(hx + 4, hy + 2, spec["eye"])
    spec["head"](c, hx, hy)
    # front layer
    if not spec.get("robe"):
        leg(*pose.get("fl", (1, 0)), back=False)
    hand = arm(pose.get("fa", 10), back=False)
    if spec.get("weapon"):
        spec["weapon"](c, hand, pose.get("fa", 10) + pose.get("wa", 0), pose)
    c.outline(OUT)
    if spec.get("glow") and pose.get("glow"):
        spec["glow"](c, hand, pose)
    return c


# ------------------------------------------------------------------ weapons and gear
def sword(blade=ramp("#c9d1dc"), guard=ramp("#f2b33d")):
    """Blade direction = arm angle + 110° (+ pose 'wa' to aim the swing): 0 down, 90 forward, 180 up."""
    def draw(c, hand, ang, pose):
        hx, hy = hand
        d = ang + 110
        bx, by = _pt(hx, hy, d, 10)
        line(c, hx, hy, bx, by, blade[1], 2)
        line(c, hx, hy, bx, by, blade[0], 1)
        g0, g1 = _pt(hx, hy, d + 90, 2), _pt(hx, hy, d - 90, 2)
        line(c, g0[0], g0[1], g1[0], g1[1], guard[1], 1)
    return draw


def staff(wood=ramp("#8a5a34"), orb=ramp("#7bdff2")):
    def draw(c, hand, ang, pose):
        hx, hy = hand
        line(c, hx, hy + 6, hx, hy - 9, wood[1], 1)
        c.disc(hx + 0.5, hy - 10.5, 2.2, orb[1])
        c.set(hx, hy - 11, orb[0])
    return draw


def staff_glow(orb=ramp("#7bdff2")):
    def draw(c, hand, pose):
        hx, hy = hand
        r = pose.get("glow", 0)
        ring(c, hx + 0.5, hy - 10.5, 2.2 + r, 1.2 + r, (*orb[0][:3], 200))
        if r > 2:
            for k in range(6):
                px, py = _pt(hx + 0.5, hy - 10.5, k * 60 + r * 20, r + 3)
                c.set(px, py, orb[0])
    return draw


def bow(wood=ramp("#a8723f"), string=(230, 230, 230, 255)):
    def draw(c, hand, ang, pose):
        hx, hy = hand
        ring(c, hx - 1.5, hy + 0.5, 6.5, 5.5, wood[1], 290, 70)
        draw_pull = pose.get("pull", 0)
        sx = hx - 4 - draw_pull
        line(c, hx + 1, hy - 6, sx, hy, string, 1)
        line(c, sx, hy, hx + 1, hy + 6, string, 1)
        if pose.get("arrow"):
            line(c, sx, hy, hx + 5, hy, ramp("#c9d1dc")[0], 1)
    return draw


def dagger(blade=ramp("#c9d1dc")):
    def draw(c, hand, ang, pose):
        hx, hy = hand
        bx, by = _pt(hx, hy, ang + 180 - 70, 5)
        line(c, hx, hy, bx, by, blade[1], 1)
    return draw


def shield_on_back(face=ramp("#3f7ee8"), rim=ramp("#c9d1dc")):
    def draw(c, hip_x, sh_y, metal):
        c.fill_rect(hip_x - 6, sh_y, 4, 7, rim[1])
        c.fill_rect(hip_x - 5, sh_y + 1, 2, 5, face[1])
    return draw


# ------------------------------------------------------------------ heads
def knight_helm(steel=ramp("#9aa4b5"), plume=ramp("#e0484f")):
    def draw(c, x, y):
        c.fill_rect(x - 1, y - 1, 8, 5, steel[1])
        c.fill_rect(x - 1, y - 1, 8, 1, steel[0])
        c.fill_rect(x + 3, y + 2, 4, 1, OUT)               # visor slit
        c.fill_rect(x - 1, y + 3, 2, 3, steel[2])          # cheek guard
        polygon(c, [(x, y - 1), (x + 3, y - 4), (x + 5, y - 2), (x + 2, y)], plume[1])
        c.set(x + 2, y - 3, plume[0])
    return draw


def wizard_hat(felt=ramp("#6b46c1"), band=ramp("#f2b33d")):
    def draw(c, x, y):
        polygon(c, [(x - 2, y + 1), (x + 8, y + 1), (x + 3, y - 8), (x + 1, y - 6)], felt[1])
        polygon(c, [(x + 3, y - 8), (x + 8, y + 1), (x + 5, y + 1)], felt[2])
        c.fill_rect(x - 2, y + 1, 10, 1, felt[2])
        c.fill_rect(x - 1, y, 8, 1, band[1])
        c.fill_rect(x - 1, y + 3, 1, 4, hex_to_rgba("#d9d9e3"))     # beard side
        polygon(c, [(x + 1, y + 5), (x + 6, y + 5), (x + 3, y + 10)], hex_to_rgba("#d9d9e3"))
    return draw


def hood(cloth=ramp("#3f8f4f")):
    def draw(c, x, y):
        polygon(c, [(x - 1, y + 6), (x - 1, y), (x + 2, y - 2), (x + 6, y - 1), (x + 7, y + 2), (x + 3, y + 1), (x + 1, y + 6)], cloth[1])
        polygon(c, [(x - 1, y + 6), (x - 2, y + 2), (x + 1, y)], cloth[2])
        c.fill_rect(x + 3, y + 1, 3, 1, OUT)                         # shadow under hood brim
        c.set(x + 4, y + 2, hex_to_rgba("#f2e6c9"))                  # glint of eye
    return draw


def skull(bone=ramp("#e8e2cf")):
    def draw(c, x, y):
        c.fill_rect(x, y, 6, 6, bone[1])
        c.fill_rect(x + 3, y + 2, 2, 2, OUT)                         # eye socket
        c.set(x + 4, y + 2, hex_to_rgba("#ff5a5a"))
        c.fill_rect(x + 2, y + 5, 4, 1, bone[2])
        c.set(x + 3, y + 5, OUT); c.set(x + 5, y + 5, OUT)            # teeth gaps
    return draw


def goblin_head(skin=ramp("#6fbf4a")):
    def draw(c, x, y):
        polygon(c, [(x, y + 1), (x - 5, y), (x - 1, y + 4)], skin[1])             # long ear, swept back
        c.set(x - 3, y + 1, skin[2])
        c.fill_rect(x + 5, y + 3, 2, 1, skin[2])                                  # nose
        c.fill_rect(x + 3, y + 4, 3, 1, OUT)                                      # grin
        c.set(x + 4, y + 4, WHITE)
    return draw


# ------------------------------------------------------------------ animation sets
def humanoid_anim(spec: dict, kind: str = "melee") -> dict[str, list[Canvas]]:
    idle = [humanoid(spec, {"by": b, "fa": 10 + s, "ba": -10 - s}) for b, s in ((0, 0), (0, 2), (1, 4), (1, 2))]
    legs = [(4, 0), (2, 2), (-1, 3), (-3, 1), (-1, 0), (2, 0)]
    arms = [-35, -15, 15, 40, 20, -10]
    bobs = [0, -1, -1, 0, -1, -1]
    move = [humanoid(spec, {"by": bobs[i], "fl": legs[i], "bl": legs[(i + 3) % 6], "fa": arms[(i + 3) % 6], "ba": arms[i]}) for i in range(6)]
    if kind == "melee":
        # wind-up (blade up and back), strike (blade level, forward), follow-through (blade low), recover
        atk = [humanoid(spec, p) for p in ({"fa": 160, "wa": -70, "lean": -1, "ba": -30},
                                          {"fa": 75, "wa": -95, "lean": 2, "fl": (3, 0), "ba": -40},
                                          {"fa": 35, "wa": -95, "lean": 1, "fl": (3, 0)},
                                          {"fa": 15, "lean": 0})]
    elif kind == "caster":
        atk = [humanoid(spec, p) for p in ({"fa": 150, "glow": 1}, {"fa": 120, "glow": 2, "lean": 1}, {"fa": 95, "glow": 4, "lean": 2}, {"fa": 40, "glow": 0})]
    else:  # archer
        atk = [humanoid(spec, p) for p in ({"fa": 90, "ba": 90, "pull": 1, "arrow": 1}, {"fa": 90, "ba": 80, "pull": 3, "arrow": 1},
                                          {"fa": 90, "ba": 60, "pull": 0}, {"fa": 30, "ba": -10})]
    hit = humanoid(spec, {"lean": -2, "fa": -20, "ba": -40})
    hurt = [flash(hit), humanoid(spec, {"lean": -1, "fa": -10})]
    kneel = humanoid(spec, {"crouch": 3, "fl": (2, 0), "bl": (-2, 0), "fa": -30, "ba": -40, "lean": -1})
    down = lie_down(humanoid(spec, {"fa": 30, "ba": -20}))
    death = [flash(hit), kneel, down, dissolve(down, 0.35, 1), dissolve(down, 0.7, 2)]
    return {"idle": idle, "move": move, "attack": atk, "hurt": hurt, "death": death}


HEROES = {
    "knight": dict(skin=ramp("#f2c49b"), cloth=ramp("#2f5fb3"), cloth2=ramp("#5a3820"), metal=ramp("#f2b33d"),
                   legs=ramp("#7d8798"), head=knight_helm(), weapon=sword(), back_item=shield_on_back()),
    "mage": dict(skin=ramp("#f2c49b"), cloth=ramp("#6b46c1"), cloth2=ramp("#f2b33d"), metal=ramp("#f2b33d"), robe=True,
                 head=wizard_hat(), weapon=staff(), glow=staff_glow()),
    "ranger": dict(skin=ramp("#c98e65"), cloth=ramp("#4b7a3a"), cloth2=ramp("#5a3820"), metal=ramp("#c9d1dc"),
                   legs=ramp("#5a4632"), head=hood(), weapon=bow()),
}
HERO_KIND = {"knight": "melee", "mage": "caster", "ranger": "archer"}


def hero(name: str) -> dict[str, list[Canvas]]:
    return humanoid_anim(HEROES[name], HERO_KIND[name])
