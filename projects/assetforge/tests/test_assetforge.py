import json
import math
import random
import tempfile
import unittest
import wave
import zipfile
from pathlib import Path

from assetforge import sprites, ui
from assetforge.pack import build_all
from assetforge.png import Canvas, decode_png, hex_to_rgba, read_png_size
from assetforge.sfx import RECIPES, render
from assetforge.wav import SR, envelope, normalize, osc, sweep, write_wav


class PngTests(unittest.TestCase):
    def test_roundtrip(self):
        c = Canvas(5, 3)
        c.set(1, 2, (10, 20, 30, 255))
        c.fill_rect(3, 0, 5, 1, hex_to_rgba("#abc"))
        back = decode_png(c.to_png())
        self.assertEqual(read_png_size(c.to_png()), (5, 3))
        self.assertEqual(back.get(1, 2), (10, 20, 30, 255))
        self.assertEqual(back.get(4, 0), (0xAA, 0xBB, 0xCC, 255))
        self.assertEqual(back.get(0, 0)[3], 0)

    def test_scale_and_outline(self):
        c = Canvas(3, 3)
        c.set(1, 1, (255, 0, 0, 255))
        c.outline((0, 0, 0, 255))
        self.assertEqual(c.opaque_count(), 5)  # centre + 4 neighbours
        s = c.scaled(4)
        self.assertEqual((s.w, s.h), (12, 12))
        self.assertEqual(s.get(5, 5), (255, 0, 0, 255))
        with self.assertRaises(ValueError):
            Canvas(0, 1)


class SpriteTests(unittest.TestCase):
    def test_creatures_symmetric_deterministic_and_solid(self):
        for seed in range(30):
            a = sprites.creature(seed, "moss")
            self.assertEqual(a.to_png(), sprites.creature(seed, "moss").to_png(), "deterministic")
            for y in range(a.h):
                for x in range(a.w // 2):
                    self.assertEqual(a.get(x, y)[3] > 0, a.get(a.w - 1 - x, y)[3] > 0, f"seed {seed} symmetric")
            self.assertGreater(a.opaque_count(), 30)
        self.assertNotEqual(sprites.creature(1).to_png(), sprites.creature(2).to_png())

    def test_items(self):
        frames = sprites.coin_frames()
        self.assertEqual(len(frames), 6)
        self.assertGreater(frames[0].opaque_count(), frames[3].opaque_count(), "edge-on frame is thinner")
        self.assertGreater(sprites.heart(1).opaque_count(), 40)
        sheet = sprites.sheet(frames, 3, pad=1)
        self.assertEqual((sheet.w, sheet.h), (3 * 13 + 1, 2 * 13 + 1))


class UiTests(unittest.TestCase):
    def test_states_differ_and_bars_fill(self):
        for theme in ui.THEMES:
            pngs = {s: ui.button(theme, s).to_png() for s in ("normal", "hover", "pressed", "disabled")}
            self.assertEqual(len(set(pngs.values())), 4, theme)
            empty, full = ui.bar(theme, 0), ui.bar(theme, 1)
            accent = hex_to_rgba(ui.THEMES[theme]["accent"])
            self.assertNotIn(accent, [p for row in empty.px for p in row])
            self.assertIn(accent, [p for row in full.px for p in row])
        with self.assertRaises(ValueError):
            ui.button("steel", "wiggle")

    def test_nine_slice_borders_are_uniform(self):
        """Stretching the centre must not distort edges: the middle rows/cols of a 9-slice image repeat."""
        p = ui.panel("steel", 48, 48)
        m = ui.NINE_SLICE["panel"]
        mid_rows = [tuple(p.px[y]) for y in range(m, 48 - m)]
        self.assertEqual(len(set(mid_rows)), 1)
        b = ui.button("candy", "normal", 32, 16)
        m = ui.NINE_SLICE["button"]
        cols = {tuple(b.px[y][x] for y in range(16)) for x in range(m, 32 - m)}
        self.assertEqual(len(cols), 1)


class AudioTests(unittest.TestCase):
    def test_every_recipe_renders_clean_audio(self):
        for name in RECIPES:
            for seed in (1, 2):
                sig = render(name, seed)
                self.assertTrue(0.02 < len(sig) / SR < 2.0, name)
                peak = max(abs(v) for v in sig)
                self.assertTrue(0.8 < peak <= 0.9, f"{name} peak {peak}")
                self.assertTrue(all(math.isfinite(v) for v in sig), name)
                self.assertLess(abs(sig[0]), 1e-3, f"{name} starts at silence (no click)")
                self.assertLess(abs(sig[-1]), 1e-3, f"{name} ends at silence (no click)")
            self.assertEqual(render(name, 3), render(name, 3), "deterministic")
            self.assertNotEqual(render(name, 1), render(name, 2), "variants differ")

    def test_primitives(self):
        s = osc(sweep(441, 441, 0.1), "sine")
        crossings = sum(1 for a, b in zip(s, s[1:]) if a < 0 <= b)
        self.assertAlmostEqual(crossings, 44, delta=1)
        self.assertEqual(max(abs(v) for v in normalize([0.1, -0.2, 0.05])), 0.89)
        env = envelope([1.0] * SR, attack=0.1, release=0.1)
        self.assertLess(env[0], 0.01)
        self.assertAlmostEqual(env[SR // 2], 0.7, places=2)
        with self.assertRaises(ValueError):
            osc([440], "kazoo", rng=random.Random(1))

    def test_wav_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = write_wav(Path(d) / "x.wav", render("coin", 1))
            with wave.open(str(p)) as w:
                self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, SR))
                self.assertGreater(w.getnframes(), 1000)


class PackTests(unittest.TestCase):
    def test_build_all(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "dist"
            packs = build_all(out, zip_packs=True, sfx_variants=1, creatures=4)
            self.assertEqual([p.name for p in packs], ["assetforge-retro-sfx", "assetforge-pixel-sprites", "assetforge-pixel-ui"])
            for p in packs:
                self.assertTrue((p / "LICENSE.txt").exists())
                self.assertTrue((p / "preview.html").exists())
                with zipfile.ZipFile(p.with_suffix(".zip")) as z:
                    self.assertTrue(any(n.endswith("LICENSE.txt") for n in z.namelist()))
            self.assertEqual(len(list((out / "assetforge-retro-sfx" / "wav").glob("*.wav"))), len(RECIPES))
            meta = json.loads((out / "assetforge-pixel-ui" / "metadata.json").read_text())
            self.assertEqual(meta["nine_slice_1x"]["button"], 4)
            big = (out / "assetforge-pixel-ui" / "steel" / "4x" / "button_normal.png").read_bytes()
            self.assertEqual(read_png_size(big), (128, 64))


if __name__ == "__main__":
    unittest.main()
