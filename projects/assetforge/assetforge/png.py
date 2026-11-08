"""Minimal RGBA PNG writer/reader and a pixel canvas."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

RGBA = tuple[int, int, int, int]
CLEAR: RGBA = (0, 0, 0, 0)


def hex_to_rgba(h: str, a: int = 255) -> RGBA:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def shade(c: RGBA, f: float) -> RGBA:
    """f < 1 darkens, f > 1 lightens (towards white)."""
    r, g, b, a = c
    if f <= 1:
        return (int(r * f), int(g * f), int(b * f), a)
    t = min(f - 1, 1)
    return (int(r + (255 - r) * t), int(g + (255 - g) * t), int(b + (255 - b) * t), a)


class Canvas:
    def __init__(self, w: int, h: int, fill: RGBA = CLEAR):
        if w <= 0 or h <= 0:
            raise ValueError("canvas size must be positive")
        self.w, self.h = w, h
        self.px: list[list[RGBA]] = [[fill] * w for _ in range(h)]

    def get(self, x: int, y: int) -> RGBA:
        return self.px[y][x]

    def set(self, x: int, y: int, c: RGBA) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def fill_rect(self, x: int, y: int, w: int, h: int, c: RGBA) -> None:
        for yy in range(max(0, y), min(self.h, y + h)):
            row = self.px[yy]
            for xx in range(max(0, x), min(self.w, x + w)):
                row[xx] = c

    def rect(self, x: int, y: int, w: int, h: int, c: RGBA) -> None:
        self.fill_rect(x, y, w, 1, c)
        self.fill_rect(x, y + h - 1, w, 1, c)
        self.fill_rect(x, y, 1, h, c)
        self.fill_rect(x + w - 1, y, 1, h, c)

    def disc(self, cx: float, cy: float, r: float, c: RGBA) -> None:
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def outline(self, c: RGBA) -> None:
        """Add a 1px outline around every opaque pixel (classic sprite look)."""
        src = [row[:] for row in self.px]
        for y in range(self.h):
            for x in range(self.w):
                if src[y][x][3]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and src[ny][nx][3] and src[ny][nx] != c:
                        self.px[y][x] = c
                        break

    def blit(self, other: "Canvas", ox: int, oy: int) -> None:
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y][x]
                if c[3]:
                    self.set(ox + x, oy + y, c)

    def scaled(self, k: int) -> "Canvas":
        out = Canvas(self.w * k, self.h * k)
        for y in range(self.h):
            row = [c for c in self.px[y] for _ in range(k)]
            for i in range(k):
                out.px[y * k + i] = row[:]
        return out

    def opaque_count(self) -> int:
        return sum(1 for row in self.px for c in row if c[3])

    def to_png(self) -> bytes:
        raw = b"".join(b"\x00" + bytes(v for c in row for v in c) for row in self.px)

        def chunk(tag: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(self.to_png())
        return p


def read_png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    return struct.unpack(">II", data[16:24])


def decode_png(data: bytes) -> Canvas:
    """Decode PNGs written by this module (RGBA8, filter 0). Used by tests."""
    w, h = read_png_size(data)
    pos, idat = 8, b""
    while pos < len(data):
        (n,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        if tag == b"IDAT":
            idat += data[pos + 8:pos + 8 + n]
        pos += 12 + n
    raw = zlib.decompress(idat)
    c = Canvas(w, h)
    stride = w * 4 + 1
    for y in range(h):
        row = raw[y * stride + 1:(y + 1) * stride]
        c.px[y] = [tuple(row[i:i + 4]) for i in range(0, len(row), 4)]  # type: ignore[misc]
    return c
