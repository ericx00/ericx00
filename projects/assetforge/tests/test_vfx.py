import unittest

from assetforge import vfx, vfxsfx
from assetforge.vfxpack import FREE_EFFECTS, FREE_PALETTES
from assetforge.wav import SR, short_term_db


BUILD_UPS = {"charge"}  # end at full strength on purpose: they lead into another effect


class Vfx(unittest.TestCase):
    def test_every_effect_animates_and_stays_in_frame(self):
        self.assertGreaterEqual(len(vfx.EFFECTS), 37)
        seen = set()
        for name, (fn, n, loops, fps, dither, sound) in vfx.EFFECTS.items():
            frs = vfx.frames(name, "fire")
            self.assertEqual(len(frs), n, name)
            counts = [f.opaque_count() for f in frs]
            self.assertGreater(max(counts), 60, f"{name} is too faint")
            self.assertGreaterEqual(sum(1 for c in counts if c > 0), n - 2, f"{name} has empty frames")
            distinct = {tuple(map(tuple, f.px)) for f in frs}
            self.assertGreaterEqual(len(distinct), n - 1, f"{name} repeats frames")
            for f in frs:
                edge = sum(1 for i in range(vfx.SIZE) if f.px[0][i][3] or f.px[-1][i][3] or f.px[i][0][3] or f.px[i][-1][3])
                self.assertLess(edge, 30, f"{name} is cut off by the frame edge")
            if not loops and name not in BUILD_UPS:
                self.assertLess(counts[-1], max(counts) * 0.6, f"{name} should fade out at the end")
            key = tuple(tuple(map(tuple, f.px)) for f in frs)
            self.assertNotIn(key, seen, name); seen.add(key)
            self.assertIn(sound, vfxsfx.RECIPES, name)

    def test_palettes_recolour_the_same_shapes(self):
        fs = vfx.fields("explosion")
        a, b = vfx.frames("explosion", "fire", fs), vfx.frames("explosion", "ice", fs)
        for fa, fb in zip(a, b):
            self.assertEqual([[bool(p[3]) for p in row] for row in fa.px], [[bool(p[3]) for p in row] for row in fb.px])
        self.assertNotEqual(a[3].px, b[3].px)

    def test_sounds(self):
        for name in vfxsfx.RECIPES:
            vs = [vfxsfx.render(name, v) for v in (1, 2, 3)]
            for s in vs:
                self.assertLessEqual(max(abs(x) for x in s), 0.9, name)
                self.assertGreater(short_term_db(s), -22, name)
                self.assertLess(len(s) / SR, 2.6, name)
            for i in range(3):
                for j in range(i + 1, 3):
                    n = min(len(vs[i]), len(vs[j]))
                    self.assertGreater(sum(abs(x - y) for x, y in zip(vs[i][:n], vs[j][:n])) / n, 0.002, f"{name}: variations {i + 1} and {j + 1} match")

    def test_free_selection_exists(self):
        for e in FREE_EFFECTS:
            self.assertIn(e, vfx.EFFECTS)
        for p in FREE_PALETTES:
            self.assertIn(p, vfx.PALETTES)


if __name__ == "__main__":
    unittest.main()
