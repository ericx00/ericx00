"""Eight designed monster types x 3 colour variants, each with idle(4) move(6) attack(4) hurt(2) death(5)."""
from __future__ import annotations

import math

from .characters import ANIMS, F, GROUND, OUT, WHITE, dissolve, flash, humanoid, humanoid_anim, ramp, shift, skull, goblin_head, sword, dagger
from .draw import line, polygon, ring
from .png import CLEAR, Canvas, hex_to_rgba, shade


def _ellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        t = (y + 0.5 - cy) / ry
        if abs(t) > 1:
            continue
        half = rx * math.sqrt(1 - t * t)
        x0, x1 = int(round(cx - half)), int(round(cx + half))
        c.fill_rect(x0, y, x1 - x0, 1, col)


def _alpha(c: Canvas, a: int) -> Canvas:
    out = Canvas(c.w, c.h)
    for y in range(c.h):
        out.px[y] = [(p[0], p[1], p[2], min(p[3], a)) if p[3] else p for p in c.px[y]]
    return out


def _death(frames_alive: list[Canvas], last: Canvas) -> list[Canvas]:
    return [flash(frames_alive[0]), frames_alive[1], last, dissolve(last, 0.35, 3), dissolve(last, 0.7, 4)]


# ------------------------------------------------------------------ slime
def slime_frame(pal, w, h, dx=0, dy=0, mouth=False):
    c = Canvas(F, F)
    cx, base = 16 + dx, GROUND + dy
    cy = base - h / 2
    _ellipse(c, cx, cy, w / 2, h / 2, pal[2])
    _ellipse(c, cx, cy - 1, w / 2 - 1, h / 2 - 1, pal[1])
    c.fill_rect(int(cx - w / 2) + 1, base - 1, int(w) - 1, 1, pal[2])        # flat-ish base
    _ellipse(c, cx - w / 5, cy - h / 5, max(1, w / 7), max(1, h / 8), pal[0])  # gloss
    c.set(int(cx - w / 5) - 1, int(cy - h / 5) - 1, WHITE)
    ey = int(cy) + 1
    for ex in (int(cx + w / 8), int(cx + w / 3)):
        c.fill_rect(ex, ey - 1, 1, 2, OUT)
    if mouth:
        c.fill_rect(int(cx + w / 8), ey + 2, 3, 1, OUT)
    c.outline(OUT)
    return c


def slime(pal):
    idle = [slime_frame(pal, w, h) for w, h in ((14, 10), (15, 9), (14, 10), (13, 11))]
    move = [slime_frame(pal, w, h, 0, dy) for w, h, dy in ((17, 8, 0), (12, 12, -2), (11, 13, -6), (12, 12, -5), (13, 11, -2), (17, 8, 0))]
    atk = [slime_frame(pal, 18, 7), slime_frame(pal, 11, 14, 3, -3, True), slime_frame(pal, 14, 10, 4, 0, True), slime_frame(pal, 14, 10, 1, 0)]
    hurt = [flash(slime_frame(pal, 16, 9, -2)), slime_frame(pal, 15, 9, -1)]
    puddle = slime_frame(pal, 22, 4)
    death = [flash(slime_frame(pal, 16, 9)), slime_frame(pal, 19, 6), puddle, dissolve(puddle, 0.35, 5), dissolve(puddle, 0.7, 6)]
    return dict(idle=idle, move=move, attack=atk, hurt=hurt, death=death)


# ------------------------------------------------------------------ bat
def bat_frame(pal, flap, dy=0, dive=0, fangs=False, folded=False):
    c = Canvas(F, F)
    cx, cy = 16, 15 + dy
    tip = (-7, -3, 2, -1)[flap % 4]
    for side in (-1, 1):
        if folded:
            polygon(c, [(cx + side * 2, cy - 2), (cx + side * 5, cy + 3), (cx + side * 2, cy + 4)], pal[2])
            continue
        pts = [(cx + side * 2, cy - 2), (cx + side * 7, cy + tip - 2), (cx + side * 13, cy + tip),
               (cx + side * 10, cy + tip + 3), (cx + side * 8, cy + tip + 2), (cx + side * 6, cy + tip + 5), (cx + side * 4, cy + 3)]
        polygon(c, pts, pal[2] if side < 0 else pal[1])
        line(c, cx + side * 2, cy - 2, cx + side * 12, cy + tip, shade(pal[2], 0.8))
    c.disc(cx, cy + dive, 3.6, pal[1])
    c.disc(cx - 0.5, cy - 1 + dive, 1.4, pal[0])
    polygon(c, [(cx - 3, cy - 3 + dive), (cx - 2, cy - 7 + dive), (cx - 1, cy - 3 + dive)], pal[1])   # ears
    polygon(c, [(cx + 1, cy - 3 + dive), (cx + 2, cy - 7 + dive), (cx + 3, cy - 3 + dive)], pal[1])
    c.set(cx - 1, cy + dive, hex_to_rgba("#ff4040")); c.set(cx + 1, cy + dive, hex_to_rgba("#ff4040"))
    if fangs:
        c.set(cx - 1, cy + 3 + dive, WHITE); c.set(cx + 1, cy + 3 + dive, WHITE)
    c.outline(OUT)
    return c


def bat(pal):
    idle = [bat_frame(pal, i, (0, -1, 0, 1)[i]) for i in range(4)]
    move = [shift(bat_frame(pal, i, (0, -1, -1, 0, 1, 1)[i]), 1, 0) for i in range(6)]
    atk = [bat_frame(pal, 0, -2), bat_frame(pal, 1, 2, 1, True), bat_frame(pal, 2, 4, 1, True), bat_frame(pal, 3, 1)]
    hurt = [flash(bat_frame(pal, 1, 0)), shift(bat_frame(pal, 2, 0), -2, 0)]
    fallen = bat_frame(pal, 0, 12, folded=True)
    death = [flash(bat_frame(pal, 1)), bat_frame(pal, 0, 6, folded=True), fallen, dissolve(fallen, 0.35, 7), dissolve(fallen, 0.7, 8)]
    return dict(idle=idle, move=move, attack=atk, hurt=hurt, death=death)


# ------------------------------------------------------------------ ghost
def ghost_frame(pal, phase, dy=0, mouth=0, alpha=210):
    c = Canvas(F, F)
    cx, top = 16, 6 + dy
    c.disc(cx, top + 6, 6.5, pal[1])
    body = [(cx - 6.5, top + 6), (cx + 6.5, top + 6), (cx + 6, top + 16)]
    waves = [(cx + 6, top + 16)]
    for k in range(6):
        x = cx + 6 - (k + 1) * 2.2
        y = top + 16 + (2 if (k + phase) % 2 else -1) + (k * 0.4)
        waves.append((x, y))
    polygon(c, body[:2] + waves + [(cx - 7, top + 13)], pal[1])
    c.disc(cx - 2, top + 4, 2.2, pal[0])
    c.fill_rect(cx + 1, top + 4, 2, 3, OUT); c.fill_rect(cx + 4, top + 4, 2, 3, OUT)
    if mouth:
        _ellipse(c, cx + 3.5, top + 10, 1.5 + mouth / 2, 1 + mouth, OUT)
    c.outline(OUT)
    return _alpha(c, alpha)


def ghost(pal):
    idle = [ghost_frame(pal, i, (0, -1, -1, 0)[i]) for i in range(4)]
    move = [shift(ghost_frame(pal, i, (0, -1, -2, -1, 0, 1)[i]), (0, 1, 1, 2, 1, 0)[i], 0) for i in range(6)]
    atk = [ghost_frame(pal, 0, -1, 1), shift(ghost_frame(pal, 1, 0, 2), 2, 0), shift(ghost_frame(pal, 2, 0, 3), 3, 0), ghost_frame(pal, 3, 0, 1)]
    hurt = [flash(ghost_frame(pal, 0)), shift(ghost_frame(pal, 1), -2, 0)]
    death = [flash(ghost_frame(pal, 0)), ghost_frame(pal, 1, -2, 2, 170), ghost_frame(pal, 2, -4, 3, 120),
             dissolve(ghost_frame(pal, 3, -6, 2, 80), 0.4, 9), dissolve(ghost_frame(pal, 0, -8, 1, 50), 0.7, 10)]
    return dict(idle=idle, move=move, attack=atk, hurt=hurt, death=death)


# ------------------------------------------------------------------ mushroom
def mushroom_frame(pal, step=0, squash=0, spores=0, cap_off=0):
    c = Canvas(F, F)
    stem = ramp("#efe3c8")
    base = GROUND
    cy = base - 11 + squash - cap_off
    # cap first (a dome: an ellipse with its lower half cut away) ...
    cap = Canvas(F, F)
    _ellipse(cap, 16, cy, 10 + squash, 6, pal[2])
    _ellipse(cap, 16, cy - 1, 9 + squash, 5, pal[1])
    cap.fill_rect(0, cy + 1, F, F - cy - 1, CLEAR)
    cap.fill_rect(6 - squash, cy, 20 + 2 * squash, 1, pal[2])
    for sx, sy, r in ((11, -3, 1.6), (17, -4, 1.3), (21, -2, 1.1)):
        cap.disc(sx, cy + sy, r, pal[0])
    # ... then the stem body with its face, tucked under the cap
    lx = (0, 1, 0, -1)[step % 4]
    top = base - 11 + squash + 1
    c.fill_rect(12 + lx, base - 2, 3, 2, stem[2]); c.fill_rect(17 - lx, base - 2, 3, 2, stem[2])     # feet
    c.fill_rect(12, top, 8, base - 2 - top, stem[1])
    c.fill_rect(18, top, 2, base - 2 - top, stem[2])
    c.fill_rect(12, top, 8, 1, shade(stem[1], 0.8))                                                   # cap shadow
    c.fill_rect(16, top + 2, 1, 2, OUT); c.fill_rect(18, top + 2, 1, 2, OUT)                          # eyes
    c.blit(cap, 0, 0)
    for k in range(spores):
        a = k * 1.3
        c.set(int(16 + math.cos(a) * (8 + k)), int(cy - 2 + math.sin(a) * (4 + k)), (*pal[0][:3], 255))
    c.outline(OUT)
    return c


def mushroom(pal):
    idle = [mushroom_frame(pal, 0, s) for s in (0, 1, 0, 0)]
    move = [shift(mushroom_frame(pal, i), 0, -(i % 2)) for i in range(6)]
    atk = [mushroom_frame(pal, 0, 2), mushroom_frame(pal, 0, 0, 4), mushroom_frame(pal, 0, 0, 8), mushroom_frame(pal, 0, 0, 3)]
    hurt = [flash(mushroom_frame(pal, 0, 1)), shift(mushroom_frame(pal), -2, 0)]
    fallen = mushroom_frame(pal, 0, 3, 0, -5)
    death = [flash(mushroom_frame(pal)), mushroom_frame(pal, 0, 2), fallen, dissolve(fallen, 0.35, 11), dissolve(fallen, 0.7, 12)]
    return dict(idle=idle, move=move, attack=atk, hurt=hurt, death=death)


# ------------------------------------------------------------------ floating eye
def eye_frame(pal, look=0, lid=0, dy=0, beam=0, tent=0, r=7):
    c = Canvas(F, F)
    cx, cy = 15, 13 + dy
    for k, x in enumerate((cx - 4, cx - 1, cx + 2, cx + 5)):     # tentacles
        sway = (1 if (k + tent) % 2 else -1)
        line(c, x, cy + r - 1, x + sway, cy + r + 4, shade(pal[2], 0.9), 1)
        line(c, x + sway, cy + r + 4, x, cy + r + 7, shade(pal[2], 0.9), 1)
    c.disc(cx, cy, r, hex_to_rgba("#f2ece4"))
    c.disc(cx - 2, cy - 2, r / 2.6, WHITE)
    line(c, cx - r + 1, cy + 2, cx - 3, cy + 1, hex_to_rgba("#d76b6b"))
    line(c, cx - 2, cy + r - 2, cx - 1, cy + 3, hex_to_rgba("#d76b6b"))
    ix = cx + 2 + look
    c.disc(ix, cy, 3.3, pal[1] if not beam else pal[0])
    c.disc(ix + 0.5, cy, 1.4, OUT)
    c.set(ix - 1, cy - 2, WHITE)
    if lid:
        c.fill_rect(cx - r, cy - r, 2 * r + 1, int(lid * r * 2 / 3), pal[2])
        for y in range(cy - r, cy - r + int(lid * r * 2 / 3)):
            for x in range(cx - r, cx + r + 1):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 > r * r:
                    c.set(x, y, CLEAR)
    if beam:
        line(c, ix + 3, cy, F - 1, cy, (*pal[0][:3], 230), beam)
    c.outline(OUT)
    return c


def floating_eye(pal):
    idle = [eye_frame(pal, l, lid, d, 0, i) for i, (l, lid, d) in enumerate(((0, 0, 0), (1, 0, -1), (0, 1.5, -1), (0, 0, 0)))]
    move = [shift(eye_frame(pal, 1, 0, (0, -1, -1, 0, 1, 1)[i], 0, i), 1, 0) for i in range(6)]
    atk = [eye_frame(pal, 1, 0.5, 0), eye_frame(pal, 1, 0, 0, 1), eye_frame(pal, 1, 0, 0, 2), eye_frame(pal, 0, 0, 0)]
    hurt = [flash(eye_frame(pal, -1, 1)), shift(eye_frame(pal, -1, 0.5), -2, 0)]
    fallen = shift(eye_frame(pal, 0, 3, 0, 0, 0, 5), 0, 10)
    death = [flash(eye_frame(pal)), eye_frame(pal, -1, 2, 3), fallen, dissolve(fallen, 0.35, 13), dissolve(fallen, 0.7, 14)]
    return dict(idle=idle, move=move, attack=atk, hurt=hurt, death=death)


# ------------------------------------------------------------------ golem
def golem_frame(pal, glow, step=0, arm=0, dy=0, crumble=0):
    c = Canvas(F, F)
    st = pal
    base = GROUND
    lx = (0, 1, 0, -1)[step % 4]
    c.fill_rect(9 + lx, base - 6, 5, 6, st[2]); c.fill_rect(18 - lx, base - 6, 5, 6, st[1])           # legs
    by = base - 17 + dy
    c.fill_rect(8, by, 16, 12, st[1]); c.fill_rect(8, by, 16, 2, st[0]); c.fill_rect(21, by + 2, 3, 10, st[2])  # torso
    line(c, 11, by + 3, 13, by + 7, st[2]); line(c, 19, by + 8, 21, by + 5, st[2])                      # cracks
    c.disc(16, by + 6, 2.2, glow[1]); c.set(15, by + 5, glow[0])                                         # core
    c.fill_rect(12, by - 5, 8, 6, st[1]); c.fill_rect(12, by - 5, 8, 1, st[0])                           # head
    c.fill_rect(16, by - 3, 2, 1, glow[0]); c.fill_rect(13, by - 3, 2, 1, glow[1])                       # eyes
    ay = by + 1 + arm
    c.fill_rect(4, by + 1, 4, 9, st[2])                                                                  # back arm
    c.fill_rect(24, ay - (arm < 0) * 0, 5, 10, st[1]); c.fill_rect(24, ay + 8, 5, 2, st[2])              # front arm
    if crumble:
        out = Canvas(F, F)
        for y in range(F):
            for x in range(F):
                p = c.px[y][x]
                if p[3]:
                    out.set(x + ((x // 4) % 3 - 1) * crumble, min(base, y + crumble * ((x * 7 + y) % 3)), p)
        c = out
    c.outline(OUT)
    return c


def golem(pal, glow):
    idle = [golem_frame(pal, glow, 0, 0, d) for d in (0, 0, 1, 1)]
    move = [golem_frame(pal, glow, i, 0, (0, 1, 0, 0, 1, 0)[i]) for i in range(6)]
    atk = [golem_frame(pal, glow, 0, -9), golem_frame(pal, glow, 0, -11, -1), golem_frame(pal, glow, 0, 3, 1), golem_frame(pal, glow, 0, 1)]
    for p in ((22, GROUND - 1), (27, GROUND - 2), (30, GROUND - 1)):                  # slam dust
        atk[2].set(*p, hex_to_rgba("#d8c8a8"))
    hurt = [flash(golem_frame(pal, glow)), shift(golem_frame(pal, glow), -1, 0)]
    rubble = golem_frame(pal, glow, 0, 0, 2, 3)
    death = [flash(golem_frame(pal, glow)), golem_frame(pal, glow, 0, 0, 1, 1), rubble, dissolve(rubble, 0.35, 15), dissolve(rubble, 0.7, 16)]
    return dict(idle=idle, move=move, attack=atk, hurt=hurt, death=death)


# ------------------------------------------------------------------ humanoid monsters
def _ribs(bone):
    def draw(c, hip_x, hip_y, sh_y):
        c.fill_rect(hip_x - 3, sh_y, 7, hip_y - sh_y, CLEAR)
        c.fill_rect(hip_x - 1, sh_y, 2, hip_y - sh_y + 1, bone[1])                    # spine
        for y in range(sh_y + 1, hip_y - 1, 2):
            c.fill_rect(hip_x - 3, y, 7, 1, bone[1])
    return draw


def skeleton(bone, eye):
    spec = dict(skin=bone, cloth=bone, cloth2=ramp("#5a3820"), metal=bone, legs=bone, boots=bone, sleeves=False,
                head=skull(bone), weapon=sword(ramp("#a89f8e"), ramp("#6b5a45")), detail=_ribs(bone), eye=eye)
    return humanoid_anim(spec, "melee")


def goblin(skin, cloth):
    spec = dict(skin=skin, cloth=cloth, cloth2=ramp("#3b2a1e"), metal=ramp("#c9d1dc"), legs=ramp("#4a3b2e"),
                head=goblin_head(skin), weapon=dagger(), torso=6, sleeves=False)
    return humanoid_anim(spec, "melee")


# ------------------------------------------------------------------ catalogue
R = ramp
MONSTERS = {
    "slime_green": lambda: slime(R("#5fcf5a")), "slime_blue": lambda: slime(R("#4aa8ff")), "slime_magma": lambda: slime(R("#ff6a2a")),
    "bat_purple": lambda: bat(R("#6c4f9e")), "bat_brown": lambda: bat(R("#8a5a3a")), "bat_crimson": lambda: bat(R("#a8283f")),
    "ghost_pale": lambda: ghost(R("#e8eef7")), "ghost_spectral": lambda: ghost(R("#8fd0ff")), "ghost_ember": lambda: ghost(R("#ff9b6b")),
    "mushroom_red": lambda: mushroom(R("#e0484f")), "mushroom_blue": lambda: mushroom(R("#3f7ee8")), "mushroom_gold": lambda: mushroom(R("#f2b33d")),
    "eye_crimson": lambda: floating_eye(R("#d83a46")), "eye_venom": lambda: floating_eye(R("#4fbf5f")), "eye_void": lambda: floating_eye(R("#9b59d0")),
    "golem_stone": lambda: golem(R("#8a8f99"), R("#7bdff2")), "golem_moss": lambda: golem(R("#5f7d55"), R("#c4f27b")), "golem_lava": lambda: golem(R("#4a3a3a"), R("#ff7a2a")),
    "skeleton_bone": lambda: skeleton(R("#e8e2cf"), hex_to_rgba("#ff5a5a")), "skeleton_cursed": lambda: skeleton(R("#b8d6a8"), hex_to_rgba("#7dff6b")),
    "skeleton_gilded": lambda: skeleton(R("#f2d27a"), hex_to_rgba("#7bdff2")),
    "goblin_forest": lambda: goblin(R("#6fbf4a"), R("#7a5a3a")), "goblin_cave": lambda: goblin(R("#8a9a8a"), R("#4a4a5a")), "goblin_fire": lambda: goblin(R("#d8603a"), R("#3a2a2a")),
}
