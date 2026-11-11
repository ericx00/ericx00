import math
import random
import unittest

from assetforge import cardsfx, deck, deckicons, music, pixfonts
from assetforge.wav import SR, short_term_db


class DeckKit(unittest.TestCase):
    def test_icons_are_distinct_and_drawn(self):
        icons = deckicons.all_icons()
        self.assertGreaterEqual(len(icons), 69)
        seen = {}
        for name, c in icons.items():
            self.assertEqual((c.w, c.h), (16, 16), name)
            self.assertGreater(c.opaque_count(), 40, name)
            key = tuple(map(tuple, c.px))
            if key in seen:
                self.assertEqual({name, seen[key]}, {"intent_multi_attack", "map_fight"})  # the one intended reuse
            seen[key] = name

    def test_frames_have_a_clear_art_window(self):
        cards = deck.all_cards()
        self.assertEqual(len(cards["frames"]), len(deck.TYPES) * len(deck.RARITIES))
        x, y, w, h = deck.ART
        for name, c in cards["frames"].items():
            self.assertEqual((c.w, c.h), (deck.CW, deck.CH), name)
            self.assertEqual(c.px[y + 2][x + 2][3], 0, name)
            self.assertEqual(c.px[y + h // 2][x - 1][3], 255, name)
        self.assertNotEqual(cards["frames"]["attack_common"].px, cards["frames_no_label"]["attack_common"].px)

    def test_ui_parts_fit_their_nine_slice_borders(self):
        for name, (c, m) in deck.ui_parts().items():
            if m is not None:
                l, t, r, b = (m, m, m, m) if isinstance(m, int) else m
                self.assertGreater(c.w, l + r, name); self.assertGreater(c.h, t + b, name)

    def test_fonts_cover_printable_ascii(self):
        fs = pixfonts.fonts()
        for key in ("sans", "bold", "display"):
            missing = [chr(i) for i in range(32, 127) if chr(i) not in fs[key].glyphs]
            self.assertEqual(missing, [], key)
        tiny = fs["tiny"]
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            self.assertIn(ch, tiny.glyphs)
        self.assertEqual(tiny.get("a"), tiny.get("A"))
        for f in fs.values():
            shapes = [tuple(rows) for ch, (rows, w) in f.glyphs.items() if ch.isalnum()]
            self.assertEqual(len(shapes), len(set(shapes)), f"{f.name}: two letters look the same")
            _, fnt = f.bmfont("x.png")
            self.assertIn(f"char id={ord('A')} ", fnt)

    def test_sfx_levels_and_variation(self):
        self.assertGreaterEqual(len(cardsfx.RECIPES), 67)
        for name in cardsfx.RECIPES:
            a, b = cardsfx.render(name, 1), cardsfx.render(name, 2)
            self.assertLessEqual(max(abs(v) for v in a), 0.9, name)
            self.assertLessEqual(short_term_db(a), cardsfx.TARGET_DB[cardsfx.CATEGORY_OF[name]] + 0.2, name)
            self.assertGreater(short_term_db(a), -24, name)
            self.assertLess(len(a) / SR, 2.5, name)
            vs = [a, b, cardsfx.render(name, 3), cardsfx.render(name, 4)]
            for i in range(4):
                for j in range(i + 1, 4):
                    n = min(len(vs[i]), len(vs[j]))
                    diff = sum(abs(x - y) for x, y in zip(vs[i][:n], vs[j][:n])) / n
                    self.assertGreater(diff, 0.002, f"{name}: variations {i + 1} and {j + 1} are (nearly) identical")
        self.assertEqual(cardsfx.render("slash", 3), cardsfx.render("slash", 3))

    def test_music_notes_stay_in_key_and_loops_join(self):
        for name, t in music.TRACKS.items():
            self.assertEqual(len(t["chords"]), 16)
            key = music.NOTE[t["key"]]
            allowed = {(key + s) % 12 for s in music.SCALES[t["scale"]]}
            for c in t["chords"]:
                root, iv = music.chord(c)
                allowed |= {(root + i) % 12 for i in iv}
            for _, _, p in music._melody(random.Random("music:" + name), t):
                self.assertIn(p % 12, allowed, name)
        sig = music.render("boss_forge_heart")
        rms = math.sqrt(sum(v * v for v in sig) / len(sig))
        self.assertAlmostEqual(20 * math.log10(rms), -17, delta=1.5)
        self.assertLess(abs(sig[0] - sig[-1]), 0.1)


if __name__ == "__main__":
    unittest.main()
