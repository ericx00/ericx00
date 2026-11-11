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
from assetforge.sfx import CATEGORY_OF, RECIPES, TARGET_DB, render
from assetforge.wav import SR, envelope, normalize, osc, short_term_db, sweep, write_wav


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


class SpriteSetTests(unittest.TestCase):
    def test_tiles_items_effects(self):
        tl = sprites.tiles()
        for k in ("ground_tl", "ground_t", "ground_tr", "ground_l", "ground_c", "ground_r", "ground_bl", "ground_b", "ground_br", "ground_single"):
            self.assertIn(k, tl)
        for k, c in tl.items():
            self.assertEqual((c.w, c.h), (16, 16), k)
            self.assertGreater(c.opaque_count(), 10, k)
        # grass tops connect: the top rows of neighbouring top tiles match at the seam
        a, b = tl["ground_t"], tl["ground_t"]
        self.assertEqual([a.px[y][15] for y in range(4)], [b.px[y][15] for y in range(4)])
        its = sprites.items()
        self.assertGreaterEqual(len(its), 40)
        self.assertEqual(len({c.to_png() for c in its.values()}), len(its), "every item is distinct")
        for name, (f, fps) in sprites.EFFECTS.items():
            frames = f()
            self.assertGreaterEqual(len(frames), 4, name)
            self.assertEqual(len({(fr.w, fr.h) for fr in frames}), 1, f"{name} frames share one size")

    def test_creature_animation(self):
        a = sprites.creature_anim(5, "moss")
        self.assertEqual(len(a["idle"]), 2)
        self.assertNotEqual(a["idle"][0].to_png(), a["idle"][1].to_png())
        hurt = a["hurt"][0]
        self.assertIn((255, 255, 255, 255), [p for row in hurt.px for p in row])

    def test_scene(self):
        sc = sprites.scene()
        self.assertEqual((sc.w, sc.h), (320, 180))


class CharacterTests(unittest.TestCase):
    def test_every_character_has_the_full_animation_set(self):
        from assetforge.characters import ANIMS, F, hero, HEROES
        from assetforge.monsters import MONSTERS
        chars = {f"hero_{n}": hero(n) for n in HEROES}
        chars.update({n: f() for n, f in MONSTERS.items()})
        self.assertEqual(len(chars), 27)
        for name, anim in chars.items():
            for a, n in ANIMS.items():
                frames = anim[a]
                self.assertEqual(len(frames), n, f"{name}.{a}")
                for f in frames:
                    self.assertEqual((f.w, f.h), (F, F), f"{name}.{a} size")
                    self.assertGreater(f.opaque_count(), 15, f"{name}.{a} blank frame")
            for a in ("idle", "move", "attack"):
                self.assertGreater(len({f.to_png() for f in anim[a]}), 1, f"{name}.{a} has no motion")
            self.assertIn((255, 255, 255, 255), [p for row in anim["hurt"][0].px for p in row], f"{name} hurt flash")
            self.assertLess(anim["death"][-1].opaque_count(), anim["death"][2].opaque_count(), f"{name} death dissolves")

    def test_variants_differ_and_types_are_distinct(self):
        from assetforge.monsters import MONSTERS
        idles = {n: f()["idle"][0].to_png() for n, f in MONSTERS.items()}
        self.assertEqual(len(set(idles.values())), len(idles), "every variant looks different")
        self.assertEqual(len({n.split("_")[0] for n in MONSTERS}), 8)

    def test_biomes_share_tile_names_and_scenes_render(self):
        names = None
        for b in sprites.BIOMES:
            tl = sprites.biome_tiles(b)
            core = {k for k in tl if not k.startswith("decor_")}
            names = names or core
            self.assertEqual(core, names, f"{b} has the same structural tiles")
            sc = sprites.level_scene(b, 0)
            self.assertEqual((sc.w, sc.h), (320, 180))
        self.assertNotEqual(sprites.biome_tiles("dungeon")["ground_t"].to_png(), sprites.biome_tiles("snow")["ground_t"].to_png())
        # the biome swap must not leak: grassland tiles are unchanged afterwards
        self.assertEqual(sprites.tiles()["ground_t"].to_png(), sprites.biome_tiles("grassland")["ground_t"].to_png())


class UiTests(unittest.TestCase):
    def test_every_theme_has_the_full_component_set(self):
        names = None
        for theme in ui.THEMES:
            comps = ui.components(theme)
            self.assertGreaterEqual(len(comps), 60, theme)
            names = names or set(comps)
            self.assertEqual(set(comps), names, "all themes ship the same elements")
            pngs = {s: comps[f"button_m_{s}"][0].to_png() for s in ("normal", "hover", "pressed", "disabled")}
            self.assertEqual(len(set(pngs.values())), 4, theme)
            for name, (img, m) in comps.items():
                self.assertGreater(img.opaque_count(), 0, f"{theme}/{name} is blank")
        with self.assertRaises(ValueError):
            ui.button("steel", "wiggle")

    def test_bars_fill(self):
        empty, full = ui.bar("steel", 0), ui.bar("steel", 1)
        red = hex_to_rgba(ui.BAR_COLOURS["health"])
        self.assertNotIn(red, [p for row in empty.px for p in row])
        self.assertIn(red, [p for row in full.px for p in row])

    def test_nine_slice_borders_are_uniform(self):
        """Stretching must not distort edges: the middle rows/cols of a 9-slice image repeat."""
        p = ui.panel("steel", 48, 48)
        m = ui.NINE_SLICE["panel"]
        self.assertEqual(len({tuple(p.px[y]) for y in range(m, 48 - m)}), 1)
        b = ui.button("candy", "normal", 32, 16)
        m = ui.NINE_SLICE["button"]
        self.assertEqual(len({tuple(b.px[y][x] for y in range(16)) for x in range(m, 32 - m)}), 1)
        d = ui.dialog("neon")
        l, t, r, bt = ui.NINE_SLICE["dialog"]
        self.assertEqual(len({tuple(d.px[y]) for y in range(t, d.h - bt)}), 1, "title strip sits inside the fixed top border")

    def test_nine_slice_stretch_keeps_corners(self):
        from assetforge.draw import nine_slice
        src = ui.dialog("steel")
        big = nine_slice(src, 200, 150, ui.NINE_SLICE["dialog"])
        self.assertEqual((big.w, big.h), (200, 150))
        for y in range(14):
            self.assertEqual(big.px[y][:6], src.px[y][:6])
        with self.assertRaises(ValueError):
            nine_slice(src, 5, 5, 6)

    def test_mockup_and_text_button(self):
        m = ui.mockup("parchment")
        self.assertEqual((m.w, m.h), (320, 180))
        tb = ui.text_button("steel", "A VERY LONG LABEL")
        from assetforge.font import text_width
        self.assertGreaterEqual(tb.w, text_width("A VERY LONG LABEL") + 14)


class IconFontTests(unittest.TestCase):
    def test_icons(self):
        from assetforge.icons import ICONS
        self.assertGreaterEqual(len(ICONS), 40)
        seen = set()
        for name, f in ICONS.items():
            c = f()
            self.assertEqual((c.w, c.h), (16, 16), name)
            self.assertGreater(c.opaque_count(), 30, name)
            seen.add(c.to_png())
        self.assertEqual(len(seen), len(ICONS), "no two icons are identical")

    def test_font(self):
        from assetforge import font
        for ch, rows in font.G.items():
            self.assertEqual(len(rows), 7, ch)
            self.assertTrue(all(len(r) == 5 for r in rows), ch)
        self.assertEqual(font.text_width("AB"), 11)
        sheet, pos = font.atlas()
        fnt = font.bmfont("f.png", (sheet.w, sheet.h), pos)
        self.assertIn('char id=65 ', fnt)   # A
        self.assertIn('char id=97 ', fnt)   # a -> mapped
        self.assertEqual(fnt.count("\nchar id="), len(pos) + sum(ch.isalpha() for ch in pos))


class AudioTests(unittest.TestCase):
    def test_every_recipe_renders_clean_audio(self):
        for name in RECIPES:
            for seed in (1, 2):
                sig = render(name, seed)
                self.assertTrue(0.02 < len(sig) / SR < 2.0, name)
                peak = max(abs(v) for v in sig)
                self.assertLessEqual(peak, 0.8901, f"{name} peak {peak} above the -1 dBFS ceiling")
                target = TARGET_DB[CATEGORY_OF[name]]
                loud = short_term_db(sig)
                self.assertLessEqual(abs(loud - target), 1.0, f"{name}: {loud:.1f} dB vs category target {target}")
                self.assertTrue(all(math.isfinite(v) for v in sig), name)
                self.assertLess(abs(sig[0]), 1e-3, f"{name} starts at silence (no click)")
                self.assertLess(abs(sig[-1]), 1e-3, f"{name} ends at silence (no click)")
            self.assertEqual(render(name, 3), render(name, 3), "deterministic")
            self.assertNotEqual(render(name, 1), render(name, 2), "variants differ")

    def test_square_is_band_limited(self):
        """A 3 kHz PolyBLEP square must not fold energy back below its fundamental (aliasing)."""
        import cmath
        sig = osc(sweep(3000, 3000, 0.05), "square")
        def mag(f):
            return abs(sum(v * cmath.exp(-2j * math.pi * f * i / SR) for i, v in enumerate(sig)))
        self.assertGreater(mag(3000), 20 * mag(1700))

    def test_every_recipe_has_a_category(self):
        self.assertEqual(set(RECIPES), set(CATEGORY_OF))
        self.assertGreaterEqual(len(RECIPES), 30)

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
            self.assertEqual(len(list((out / "assetforge-retro-sfx" / "wav").glob("*/*.wav"))), len(RECIPES))
            self.assertTrue((out / "assetforge-retro-sfx" / "sounds.csv").exists())
            sp = out / "assetforge-pixel-sprites"
            meta = json.loads((sp / "metadata.json").read_text())
            self.assertEqual(len(meta["creatures"]), 4)
            self.assertIn("explosion", meta["animations"])
            for b in ("grassland", "dungeon", "snow"):
                self.assertTrue((sp / "tiles" / b / f"tileset_{b}.tsx").read_text().startswith("<?xml"))
            self.assertEqual(len(meta["characters"]["heroes"]) + len(meta["characters"]["monsters"]), 27)
            self.assertTrue((sp / "characters" / "monsters" / "4x" / "slime_green.png").exists())
            strip = read_png_size((sp / "effects" / "1x" / "explosion_strip.png").read_bytes())
            self.assertEqual(strip, (32 * meta["animations"]["explosion"]["frames"], 32))
            ui_root = out / "assetforge-pixel-ui"
            meta = json.loads((ui_root / "metadata.json").read_text())
            self.assertEqual(meta["elements"]["button_m_normal"]["nine_slice"], [4, 4, 4, 4])
            self.assertEqual(meta["elements"]["dialog"]["nine_slice"], [6, 14, 6, 6])
            big = (ui_root / "themes" / "steel" / "4x" / "button_m_normal.png").read_bytes()
            self.assertEqual(read_png_size(big), (192, 64))
            atlas = json.loads((ui_root / "themes" / "neon" / "atlas_neon.json").read_text())
            sheet = decode_png((ui_root / "themes" / "neon" / "atlas_neon.png").read_bytes())
            rects = [(f["x"], f["y"], f["w"], f["h"]) for f in atlas["frames"].values()]
            for i, a in enumerate(rects):
                self.assertLessEqual(a[0] + a[2], sheet.w); self.assertLessEqual(a[1] + a[3], sheet.h)
                for b in rects[i + 1:]:
                    overlap = a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
                    self.assertFalse(overlap, "atlas rects must not overlap")
            self.assertTrue((ui_root / "font" / "forge-5x7.fnt").exists())
            self.assertTrue((ui_root / "css-demo" / "index.html").exists())
            self.assertEqual(len(list((ui_root / "previews").glob("*-mockup.png"))), len(ui.THEMES))


if __name__ == "__main__":
    unittest.main()
