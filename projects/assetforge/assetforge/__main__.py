"""python -m assetforge build [--out dist] [--no-zip] [--sfx-variants 4] [--creatures 24]
python -m assetforge sfx <recipe> <seed> <out.wav>       one-off sound
python -m assetforge creature <seed> <palette> <out.png> one-off sprite (8x)"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .pack import build_all
from .sfx import RECIPES, render
from .sprites import PALETTES, creature
from .wav import write_wav


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="assetforge", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", default="dist")
    b.add_argument("--no-zip", action="store_true")
    b.add_argument("--sfx-variants", type=int, default=5)
    b.add_argument("--creatures", type=int, default=40)
    s = sub.add_parser("sfx")
    s.add_argument("recipe", choices=sorted(RECIPES))
    s.add_argument("seed", type=int)
    s.add_argument("out")
    st = sub.add_parser("starter")
    st.add_argument("--out", default="dist")
    d = sub.add_parser("deck", help="Deckbuilder Kit + free starter")
    d.add_argument("--out", default="dist")
    d.add_argument("--variants", type=int, default=4)
    c = sub.add_parser("creature")
    c.add_argument("seed", type=int)
    c.add_argument("palette", choices=sorted(PALETTES))
    c.add_argument("out")
    a = ap.parse_args(argv)

    if a.cmd == "build":
        t = time.time()
        packs = build_all(Path(a.out), not a.no_zip, a.sfx_variants, a.creatures)
        for p in packs:
            n = sum(1 for f in p.rglob("*") if f.is_file())
            print(f"{p.name}: {n} files")
        print(f"done in {time.time() - t:.1f}s -> {a.out}")
    elif a.cmd == "starter":
        from .pack import build_starter
        root = build_starter(Path(a.out))
        print(f"{root.name}: {sum(1 for f in root.rglob('*') if f.is_file())} files")
    elif a.cmd == "deck":
        from .deckpack import build as build_deck
        t = time.time()
        for p in build_deck(Path(a.out), a.variants):
            print(f"{p.name}: {sum(1 for f in p.rglob('*') if f.is_file())} files")
        print(f"done in {time.time() - t:.1f}s -> {a.out}")
    elif a.cmd == "sfx":
        print(write_wav(a.out, render(a.recipe, a.seed)))
    elif a.cmd == "creature":
        print(creature(a.seed, a.palette).scaled(8).save(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
