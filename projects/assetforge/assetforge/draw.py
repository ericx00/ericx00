"""Drawing helpers on top of Canvas: lines, polygons, rings, 9-slice scaling."""
from __future__ import annotations

import math

from .png import CLEAR, RGBA, Canvas


def line(c: Canvas, x0: int, y0: int, x1: int, y1: int, col: RGBA, width: int = 1) -> None:
    """Bresenham line with a square brush of `width` pixels."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    off = (width - 1) // 2
    while True:
        c.fill_rect(x0 - off, y0 - off, width, width, col)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def polygon(c: Canvas, pts: list[tuple[float, float]], col: RGBA) -> None:
    """Fill a polygon (even-odd rule, sampled at pixel centres)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(max(0, int(min(ys))), min(c.h, int(math.ceil(max(ys))) + 1)):
        cy = y + 0.5
        for x in range(max(0, int(min(xs))), min(c.w, int(math.ceil(max(xs))) + 1)):
            cx = x + 0.5
            inside = False
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > cy) != (yj > cy) and cx < (xj - xi) * (cy - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside:
                c.set(x, y, col)


def ring(c: Canvas, cx: float, cy: float, r_out: float, r_in: float, col: RGBA, a0: float = 0, a1: float = 360) -> None:
    """Ring (or arc of a ring) between two radii; angles in degrees, 0 = right, counter-clockwise."""
    for y in range(int(cy - r_out - 1), int(cy + r_out + 2)):
        for x in range(int(cx - r_out - 1), int(cx + r_out + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d2 = dx * dx + dy * dy
            if r_in * r_in <= d2 <= r_out * r_out:
                ang = math.degrees(math.atan2(-dy, dx)) % 360
                if (a0 <= ang <= a1) if a0 <= a1 else (ang >= a0 or ang <= a1):
                    c.set(x, y, col)


def erase_disc(c: Canvas, cx: float, cy: float, r: float) -> None:
    c.disc(cx, cy, r, CLEAR)


def margins(m) -> tuple[int, int, int, int]:
    """Normalise a 9-slice border: int (all sides) or (left, top, right, bottom)."""
    return (m, m, m, m) if isinstance(m, int) else tuple(m)  # type: ignore[return-value]


def nine_slice(src: Canvas, w: int, h: int, m) -> Canvas:
    """Stretch `src` to w x h keeping its borders intact (what engines do with 9-slice sprites).
    `m` is an int or (left, top, right, bottom)."""
    l, t, r, b = margins(m)
    if w < l + r or h < t + b:
        raise ValueError("target smaller than the fixed borders")
    out = Canvas(w, h)
    sw, sh = src.w, src.h

    def src_coord(v: int, size: int, ssize: int, lo: int, hi: int) -> int:
        if v < lo:
            return v
        if v >= size - hi:
            return ssize - (size - v)
        inner = ssize - lo - hi
        return lo + ((v - lo) * inner) // max(1, size - lo - hi)

    for y in range(h):
        sy = src_coord(y, h, sh, t, b)
        for x in range(w):
            out.px[y][x] = src.px[sy][src_coord(x, w, sw, l, r)]
    return out


def rotate_pts(pts: list[tuple[float, float]], deg: float, cx: float, cy: float) -> list[tuple[float, float]]:
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]
