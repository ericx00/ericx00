"""Build sellable packs: folders + zips + preview pages + license + engine metadata."""
from __future__ import annotations

import html
import json
import shutil
import zipfile
from pathlib import Path

from . import __version__, sprites, ui
from .png import Canvas
from .sfx import RECIPES, render
from .wav import SR, write_wav

LICENSE = """{title} — license (v{version})

You may use these assets in unlimited commercial and non-commercial games and
apps, modified or unmodified. Credit is appreciated but not required.

You may NOT resell, redistribute or share the assets themselves (individually or as
a pack, modified or not), or use them in another asset pack, template or NFT.
"""

SCALES = (1, 4)


def _save_scaled(c: Canvas, base: Path, name: str) -> list[str]:
    out = []
    for k in SCALES:
        p = base / f"{k}x" / f"{name}.png"
        (c if k == 1 else c.scaled(k)).save(p)
        out.append(str(p.relative_to(base.parent)))
    return out


def _preview(title: str, body: str) -> str:
    return f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>body{{font-family:system-ui;background:#16161d;color:#eee;margin:0;padding:16px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;align-items:start}}
figure{{margin:0;background:#22222c;border-radius:8px;padding:10px;text-align:center}}
img{{image-rendering:pixelated;max-width:100%}}audio{{width:100%}}figcaption{{font-size:12px;color:#aaa;margin-top:6px}}</style>
<h1>{html.escape(title)}</h1>{body}"""


def _zip(folder: Path) -> Path:
    z = folder.with_suffix(".zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(folder.parent))
    return z


def _ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def _encode(src: Path, dst: Path, codec: str) -> bool:
    """WAV -> OGG/MP3 with ffmpeg when it's installed (optional; WAV is always shipped)."""
    import subprocess
    exe = _ffmpeg()
    if not exe:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    args = {"ogg": ["-c:a", "libvorbis", "-q:a", "5"], "mp3": ["-c:a", "libmp3lame", "-b:a", "160k"]}[codec]
    r = subprocess.run([exe, "-loglevel", "error", "-y", "-i", str(src), *args, str(dst)], capture_output=True)
    return r.returncode == 0


def build_sfx(out: Path, variants: int = 5) -> Path:
    from .sfx import CATEGORIES
    from .wav import short_term_db
    root = out / "assetforge-retro-sfx"
    rows = ["file,category,sound,variant,seconds,loudness_dbfs"]
    sections = []
    reel: list[float] = []
    count = 0
    has_ogg = _ffmpeg() is not None
    for cat, names in CATEGORIES.items():
        figs = []
        for name in names:
            for v in range(1, variants + 1):
                sig = render(name, v)
                rel = f"wav/{cat}/{name}_{v:02d}.wav"
                write_wav(root / rel, sig)
                if has_ogg:
                    _encode(root / rel, root / f"ogg/{cat}/{name}_{v:02d}.ogg", "ogg")
                rows.append(f"{rel},{cat},{name},{v},{len(sig) / SR:.3f},{short_term_db(sig):.1f}")
                figs.append(f'<figure><audio controls preload="none" src="{rel}"></audio><figcaption>{name}_{v:02d}</figcaption></figure>')
                count += 1
                if v == 1:
                    reel += sig + [0.0] * int(0.35 * SR)
        sections.append(f'<h2>{cat} ({len(names) * variants})</h2><div class="g">{"".join(figs)}</div>')
    write_wav(root / "preview-reel.wav", reel)
    if has_ogg:
        _encode(root / "preview-reel.wav", root / "preview-reel.mp3", "mp3")
    (root / "sounds.csv").write_text("\n".join(rows) + "\n")
    fmt = "WAV + OGG" if has_ogg else "WAV"
    title = f"Retro SFX: {count} sounds in {len(CATEGORIES)} categories"
    (root / "README.txt").write_text(
        f"{title}\n\nFormats: {fmt}. WAV is 16-bit mono {SR} Hz; OGG is Vorbis q5 (smaller, loops cleanly in most engines).\n"
        "Levels: matched by loudness within each category (UI sits about 5 dB under gameplay), peaks at or below -1 dBFS,\n"
        "no clicks at start or end. sounds.csv lists every file with its length and loudness.\n"
        "preview-reel.wav/.mp3 plays one variant of every sound type.\n")
    (root / "preview.html").write_text(_preview(title, f'<p>{fmt}. <a href="preview-reel.wav">Preview reel</a> plays one of each.</p>{"".join(sections)}'))
    (root / "LICENSE.txt").write_text(LICENSE.format(title=title, version=__version__))
    return root


def _gifs(root: Path, chars: dict, anims: dict) -> None:
    """Animated previews (needs ffmpeg; skipped quietly without it)."""
    import subprocess
    import tempfile
    exe = _ffmpeg()
    if not exe:
        return
    groups = {"heroes": [n for n in chars if n.startswith("hero_")],
              "monsters": [n for n in chars if not n.startswith("hero_") and n.endswith(("green", "purple", "pale", "red", "crimson", "stone", "bone", "forest"))]}
    order = ["idle", "move", "attack", "hurt", "death"]
    for gname, names in groups.items():
        frames = []
        for a in order:                       # play each animation twice (death once) for every character side by side
            n = anims[a]
            for rep in range(1 if a == "death" else 2):
                for i in range(n):
                    canvas = Canvas(len(names) * 34, 34, (44, 46, 58, 255))
                    for k, name in enumerate(names):
                        canvas.blit(chars[name][a][i], k * 34 + 1, 1)
                    frames.append(canvas.scaled(4))
        with tempfile.TemporaryDirectory() as td:
            for i, f in enumerate(frames):
                f.save(Path(td) / f"f{i:04d}.png")
            subprocess.run([exe, "-loglevel", "error", "-y", "-framerate", "8", "-i", str(Path(td) / "f%04d.png"),
                            "-vf", "split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none", "-loop", "0",
                            str(root / "previews" / f"{gname}.gif")], check=False)


def build_sprites(out: Path, creatures: int = 40) -> Path:
    root = out / "assetforge-pixel-sprites"
    pals = list(sprites.PALETTES)
    meta: dict[str, object] = {"scales": list(UI_SCALES), "tile_size": 16, "animations": {}, "creatures": [], "items": [], "tiles": []}
    anims = meta["animations"]

    # creatures: idle (2 frames) + hurt, as single PNGs and one sheet (row per creature)
    crit = {}
    for i in range(creatures):
        a = sprites.creature_anim(i, pals[i % len(pals)])
        crit[f"creature_{i + 1:02d}"] = a
        for k, frames in a.items():
            for j, f in enumerate(frames):
                for sc in UI_SCALES:
                    (f if sc == 1 else f.scaled(sc)).save(root / "creatures" / f"{sc}x" / f"creature_{i + 1:02d}_{k}_{j}.png")
    sheet = Canvas(3 * 16, creatures * 16)
    for r, (name, a) in enumerate(crit.items()):
        for j, f in enumerate(a["idle"] + a["hurt"]):
            sheet.blit(f, j * 16, r * 16)
    for sc in UI_SCALES:
        (sheet if sc == 1 else sheet.scaled(sc)).save(root / "creatures" / f"creatures_sheet_{sc}x.png")
    meta["creatures"] = list(crit)
    anims["creature_idle"] = {"sheet": "creatures/creatures_sheet_1x.png", "frame_w": 16, "frame_h": 16, "columns": [0, 1], "row": "one per creature", "fps": 3}
    anims["creature_hurt"] = {"sheet": "creatures/creatures_sheet_1x.png", "frame_w": 16, "frame_h": 16, "columns": [2], "fps": 1}

    # items
    its = sprites.items()
    _save_set(its, root / "items")
    isheet, irects = _pack_atlas(its, 128)
    isheet.save(root / "items" / "atlas_items.png")
    (root / "items" / "atlas_items.json").write_text(json.dumps({"image": "atlas_items.png", "frames": {k: dict(zip("xywh", v)) for k, v in irects.items()}}, indent=1))
    meta["items"] = list(its)

    # effects + coin spin: horizontal strips
    fx = {k: (f(), fps) for k, (f, fps) in sprites.EFFECTS.items()}
    fx["coin_spin"] = (sprites.coin_frames(), 10)
    for k, (frames, fps) in fx.items():
        fw, fh = frames[0].w, frames[0].h
        strip = Canvas(fw * len(frames), fh)
        for j, f in enumerate(frames):
            strip.blit(f, j * fw, 0)
        for sc in UI_SCALES:
            (strip if sc == 1 else strip.scaled(sc)).save(root / "effects" / f"{sc}x" / f"{k}_strip.png")
        anims[k] = {"strip": f"effects/1x/{k}_strip.png", "frames": len(frames), "frame_w": fw, "frame_h": fh, "fps": fps, "loop": k in ("coin_spin", "sparkle")}

    # tilesets: one per biome (same tile names in each) + JSON names + a Tiled .tsx
    tile_count = 0
    for biome in sprites.BIOMES:
        tl = sprites.biome_tiles(biome)
        tile_count = len(tl)
        cols = 8
        rows_n = (len(tl) + cols - 1) // cols
        tsheet = Canvas(cols * 16, rows_n * 16)
        index = {}
        for i, (k, c) in enumerate(tl.items()):
            tsheet.blit(c, (i % cols) * 16, (i // cols) * 16)
            index[k] = i
        tdir = root / "tiles" / biome
        _save_set(tl, tdir)
        for sc in UI_SCALES:
            (tsheet if sc == 1 else tsheet.scaled(sc)).save(tdir / f"tileset_{biome}_{sc}x.png")
        (tdir / f"tileset_{biome}.json").write_text(json.dumps({"image": f"tileset_{biome}_1x.png", "tile": 16, "columns": cols, "index": index,
            "animated": {"water_top": ["water_top_0", "water_top_1"], "torch": ["torch_0", "torch_1"]}}, indent=1))
        props = "".join(f'<tile id="{i}"><properties><property name="name" value="{k}"/></properties></tile>' for k, i in index.items())
        (tdir / f"tileset_{biome}.tsx").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="1.10" name="assetforge-{biome}" tilewidth="16" tileheight="16" tilecount="{len(tl)}" columns="{cols}">'
            f'<image source="tileset_{biome}_1x.png" width="{tsheet.w}" height="{tsheet.h}"/>{props}</tileset>\n')
        _contact_sheet(tl, 9, (60, 70, 90, 255)).scaled(4).save(root / "previews" / f"tiles-{biome}.png")
        sprites.level_scene(biome, 1).scaled(4).save(root / "previews" / f"level-{biome}.png")
    meta["biomes"] = list(sprites.BIOMES)
    meta["tiles"] = list(sprites.biome_tiles("grassland"))

    # designed characters: 3 heroes + 24 monsters, every one with idle/move/attack/hurt/death
    from .characters import ANIMS, F as FR, hero, HEROES
    from .monsters import MONSTERS
    FPS = {"idle": 6, "move": 10, "attack": 12, "hurt": 10, "death": 8}
    chars = {f"hero_{n}": hero(n) for n in HEROES}
    chars.update({n: MONSTERS[n]() for n in MONSTERS})
    width = max(ANIMS.values())
    for name, anim in chars.items():
        sheet = Canvas(width * FR, len(ANIMS) * FR)
        for r, a in enumerate(ANIMS):
            for i, f in enumerate(anim[a]):
                sheet.blit(f, i * FR, r * FR)
        cdir = root / "characters" / ("heroes" if name.startswith("hero_") else "monsters")
        for sc in UI_SCALES:
            (sheet if sc == 1 else sheet.scaled(sc)).save(cdir / f"{sc}x" / f"{name}.png")
    meta["characters"] = {"frame": FR, "layout": "one row per animation, frames left to right",
                          "animations": {a: {"row": r, "frames": n, "fps": FPS[a], "loop": a in ("idle", "move")} for r, (a, n) in enumerate(ANIMS.items())},
                          "heroes": [n for n in chars if n.startswith("hero_")], "monsters": [n for n in chars if not n.startswith("hero_")]}

    # previews: stills + animated GIFs (itch.io shows GIFs as moving screenshots)
    sprites.scene().scaled(4).save(root / "previews" / "level-mockup.png")
    _contact_sheet({k: v for k, v in its.items()}, 12, (44, 46, 58, 255)).scaled(4).save(root / "previews" / "items.png")
    cprev = Canvas(10 * 20, ((creatures + 9) // 10) * 20, (44, 46, 58, 255))
    for i, a in enumerate(crit.values()):
        cprev.blit(a["idle"][0], (i % 10) * 20 + 2, (i // 10) * 20 + 2)
    cprev.scaled(4).save(root / "previews" / "bonus-critters.png")
    fxprev = {f"{k}_{j}": f for k, (frames, _) in fx.items() for j, f in enumerate(frames)}
    _contact_sheet(fxprev, 8, (44, 46, 58, 255)).scaled(3).save(root / "previews" / "effects.png")
    roster = Canvas(9 * 36, 3 * 36, (44, 46, 58, 255))
    for i, (n, a) in enumerate(chars.items()):
        roster.blit(a["idle"][0], (i % 9) * 36 + 2, (i // 9) * 36 + 2)
    roster.scaled(4).save(root / "previews" / "characters.png")
    _gifs(root, chars, ANIMS)

    n_frames = sum(len(f) for f, _ in fx.values())
    n_monster_types = len({n.split("_")[0] for n in MONSTERS})
    title = (f"Pixel Sprites: 3 heroes + {len(MONSTERS)} monsters (5 animations each), {len(its)} items, {len(fx)} effects, "
             f"{len(sprites.BIOMES)} tileset themes")
    (root / "metadata.json").write_text(json.dumps(meta, indent=1))
    (root / "README.txt").write_text(
        f"{title}\n\nPixel art at 1x/2x/4x. Import with nearest-neighbour filtering.\n\n"
        f"characters/: 3 heroes (knight, mage, ranger) and {len(MONSTERS)} monsters ({n_monster_types} types x 3 colour variants:\n"
        "  slime, bat, ghost, mushroom, floating eye, golem, skeleton, goblin). 32x32 frames, facing right (flip for left).\n"
        "  Each sheet: one row per animation: idle(4) move(6) attack(4) hurt(2) death(5). Frame rates in metadata.json.\n"
        f"items/: {len(its)} items in material tiers + food, chests, misc; atlas json.\n"
        f"effects/: {len(fx)} animations ({n_frames} frames) as horizontal strips.\n"
        f"tiles/<biome>/: {', '.join(sprites.BIOMES)} tilesets ({tile_count} tiles each, same names in every biome so levels re-skin instantly).\n"
        "  tileset_<biome>.tsx opens in Tiled. Ground: ground_tl/t/tr/l/c/r/bl/b/br, single block, thin ledges. Animated: water_top_0/1, torch_0/1.\n"
        f"creatures/: {creatures} bonus mini-critters (procedural, idle + hurt).\n"
        "previews/: level mock-ups per biome and animated GIFs, all built only from this pack.\n")
    body = (''.join(f'<h2>{b.title()} level</h2><img src="previews/level-{b}.png" alt="">' for b in sprites.BIOMES)
            + '<h2>Characters (animated)</h2><img src="previews/heroes.gif" alt=""><img src="previews/monsters.gif" alt="">'
            '<h2>Roster</h2><img src="previews/characters.png" alt=""><h2>Items</h2><img src="previews/items.png" alt="">'
            '<h2>Effects</h2><img src="previews/effects.png" alt="">'
            + ''.join(f'<h2>{b.title()} tiles</h2><img src="previews/tiles-{b}.png" alt="">' for b in sprites.BIOMES))
    (root / "preview.html").write_text(_preview(title, body))
    (root / "LICENSE.txt").write_text(LICENSE.format(title=title, version=__version__))
    return root


def _pack_atlas(items: dict[str, Canvas], max_w: int = 256, pad: int = 2) -> tuple[Canvas, dict[str, tuple[int, int, int, int]]]:
    """Shelf-pack sprites into one sheet (2px padding stops filtering bleed)."""
    order = sorted(items, key=lambda k: (-items[k].h, k))
    x = y = shelf = 0
    rects: dict[str, tuple[int, int, int, int]] = {}
    width = max(max_w, max(c.w for c in items.values()) + 2 * pad)
    for k in order:
        c = items[k]
        if x + c.w + pad > width:
            x, y, shelf = 0, y + shelf + pad, 0
        rects[k] = (x + pad, y + pad, c.w, c.h)
        x += c.w + pad
        shelf = max(shelf, c.h)
    sheet = Canvas(width, y + shelf + 2 * pad)
    for k, (rx, ry, _, _) in rects.items():
        sheet.blit(items[k], rx, ry)
    return sheet, rects


UI_SCALES = (1, 2, 4)


def _save_set(items: dict[str, Canvas], base: Path) -> None:
    for k in UI_SCALES:
        for name, c in items.items():
            (c if k == 1 else c.scaled(k)).save(base / f"{k}x" / f"{name}.png")


def _contact_sheet(items: dict[str, Canvas], cols: int, bg) -> Canvas:
    cw = max(c.w for c in items.values()) + 8
    ch = max(c.h for c in items.values()) + 8
    rows = (len(items) + cols - 1) // cols
    sheet = Canvas(cols * cw, rows * ch, bg)
    for i, c in enumerate(items.values()):
        sheet.blit(c, (i % cols) * cw + (cw - c.w) // 2, (i // cols) * ch + (ch - c.h) // 2)
    return sheet


CSS_DEMO = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pixel UI Kit: CSS 9-slice demo</title>
<style>
body{margin:0;padding:24px;background:#161a22;color:#e8ecf2;font-family:system-ui;image-rendering:pixelated}
.panel{border:24px solid transparent;border-image:url(../themes/steel/4x/panel_framed.png) 24 fill stretch;padding:8px;max-width:520px}
.btn{display:inline-block;border:16px solid transparent;border-image:url(../themes/steel/4x/button_m_normal.png) 16 fill stretch;padding:0 12px;color:#e8ecf2;font-weight:700;cursor:pointer;margin:8px 8px 0 0}
.btn:hover{border-image-source:url(../themes/steel/4x/button_m_hover.png)}
.btn:active{border-image-source:url(../themes/steel/4x/button_m_pressed.png)}
</style>
<h1>CSS 9-slice demo</h1>
<p>Each element stretches to any size while its pixel border stays crisp. Slice value = the 1x border &times; scale (panel 6&times;4 = 24, button 4&times;4 = 16).</p>
<div class="panel"><h2>Any size panel</h2><p>Resize the window: the frame keeps its corners.</p>
<span class="btn">PLAY</span><span class="btn">OPTIONS</span><span class="btn">A MUCH LONGER BUTTON</span></div>
"""


def build_ui(out: Path) -> Path:
    from . import font, icons
    from .draw import margins
    root = out / "assetforge-pixel-ui"
    meta: dict[str, object] = {"scales": list(UI_SCALES), "themes": list(ui.THEMES), "elements": {}, "icons": list(icons.ICONS),
                               "font": {"name": "Forge 5x7", "glyph_w": font.GW, "glyph_h": font.GH, "advance": font.ADVANCE}}
    figs = []
    total = 0
    for theme in ui.THEMES:
        comps = ui.components(theme)
        imgs = {k: c for k, (c, _) in comps.items()}
        _save_set(imgs, root / "themes" / theme)
        sheet, rects = _pack_atlas(imgs)
        sheet.save(root / "themes" / theme / f"atlas_{theme}.png")
        frames = {k: {"x": x, "y": y, "w": w, "h": h, "nine_slice": list(margins(comps[k][1])) if comps[k][1] is not None else None}
                  for k, (x, y, w, h) in rects.items()}
        (root / "themes" / theme / f"atlas_{theme}.json").write_text(json.dumps({"image": f"atlas_{theme}.png", "scale": 1, "frames": frames}, indent=1))
        if theme == list(ui.THEMES)[0]:
            meta["elements"] = {k: {"w": c.w, "h": c.h, "nine_slice": list(margins(m)) if m is not None else None} for k, (c, m) in comps.items()}
        ui.mockup(theme).scaled(4).save(root / "previews" / f"{theme}-mockup.png")
        _contact_sheet(imgs, 8, ui.theme(theme)["bg"]).scaled(3).save(root / "previews" / f"{theme}-all-elements.png")
        figs.append(f'<figure><img src="previews/{theme}-mockup.png" alt=""><figcaption>{theme}: mock-up made only from kit parts</figcaption></figure>')
        figs.append(f'<figure><img src="previews/{theme}-all-elements.png" alt=""><figcaption>{theme}: all {len(imgs)} elements</figcaption></figure>')
        total += len(imgs)

    icon_imgs = {k: f() for k, f in icons.ICONS.items()}
    _save_set(icon_imgs, root / "icons")
    isheet, irects = _pack_atlas(icon_imgs, 160)
    isheet.save(root / "icons" / "atlas_icons.png")
    (root / "icons" / "atlas_icons.json").write_text(json.dumps({"image": "atlas_icons.png", "scale": 1,
        "frames": {k: {"x": x, "y": y, "w": w, "h": h} for k, (x, y, w, h) in irects.items()}}, indent=1))
    _contact_sheet(icon_imgs, 11, (40, 42, 52, 255)).scaled(4).save(root / "previews" / "icons.png")

    fsheet, pos = font.atlas()
    for k in (1, 4):
        name = f"forge-5x7{'' if k == 1 else '@4x'}"
        (fsheet if k == 1 else fsheet.scaled(k)).save(root / "font" / f"{name}.png")
        fnt = font.bmfont(f"{name}.png", (fsheet.w * k, fsheet.h * k), {ch: (x * k, y * k) for ch, (x, y) in pos.items()})
        if k != 1:  # scale metrics
            fnt = fnt.replace(f"size={font.GH}", f"size={font.GH * k}").replace(f"lineHeight={font.LINE} base={font.GH}", f"lineHeight={font.LINE * k} base={font.GH * k}")
            fnt = fnt.replace(f"width={font.GW} height={font.GH}", f"width={font.GW * k} height={font.GH * k}").replace(f"xadvance={font.ADVANCE}", f"xadvance={font.ADVANCE * k}")
        (root / "font" / f"{name}.fnt").write_text(fnt)
    sample = Canvas(330, 40, (24, 26, 34, 255))
    font.draw_text(sample, 6, 6, "THE QUICK BROWN FOX JUMPS 0123456789", (240, 240, 240, 255))
    font.draw_text(sample, 6, 20, "OVER THE LAZY DOG! (+50%) <ENTER> $9.99?", (242, 179, 61, 255))
    sample.scaled(3).save(root / "previews" / "font.png")

    (root / "css-demo").mkdir(parents=True, exist_ok=True)
    (root / "css-demo" / "index.html").write_text(CSS_DEMO)
    (root / "metadata.json").write_text(json.dumps(meta, indent=1))
    (root / "HOW-TO-USE.txt").write_text(
        "PIXEL UI KIT: HOW TO USE\n\n"
        f"Contents: {len(ui.THEMES)} themes x {total // len(ui.THEMES)} elements, {len(icon_imgs)} icons, the Forge 5x7 bitmap font.\n"
        "Each theme: individual PNGs at 1x/2x/4x, plus atlas_<theme>.png + atlas_<theme>.json (rects + 9-slice borders).\n\n"
        "IMPORT: use nearest-neighbour / point filtering and no compression, or the pixels go blurry.\n\n"
        "9-SLICE borders at 1x are [left, top, right, bottom] in metadata.json and each atlas json (multiply by your scale):\n"
        + "".join(f"  {k}: {list(margins(v))}\n" for k, v in ui.NINE_SLICE.items())
        + "\nUNITY: Sprite Mode Multiple or single sprites; Sprite Editor -> Border = the values above; Image Type = Sliced.\n"
        "GODOT: NinePatchRect (or StyleBoxTexture) -> Patch Margin = the values above; Texture Filter = Nearest.\n"
        "GAMEMAKER: Sprite -> Nine Slice -> enable, set the borders.\n"
        "CSS: border-image-slice = border x scale. See css-demo/index.html.\n\n"
        "FONT: font/forge-5x7.fnt (+ .png) is AngelCode BMFont text format: Unity (via TextMesh Pro importers or BMFont packages),\n"
        "Godot (import .fnt as FontFile), Phaser (bitmapFont), LibGDX, Love2D. Uppercase glyphs; lowercase maps to capitals.\n\n"
        "Bars: bar_frame + bar_fill_<kind> are separate so you can scale the fill to any value. bar_health_* are ready-made examples.\n"
    )
    title = f"Pixel UI Kit: {len(ui.THEMES)} themes, {total} elements, {len(icon_imgs)} icons, bitmap font"
    body = (f'<p>{title}.</p><h2>Themes</h2><div class="g" style="grid-template-columns:repeat(auto-fill,minmax(420px,1fr))">{"".join(figs)}</div>'
            '<h2>Icons</h2><img src="previews/icons.png" alt=""><h2>Font</h2><img src="previews/font.png" alt="">')
    (root / "preview.html").write_text(_preview(title, body))
    (root / "LICENSE.txt").write_text(LICENSE.format(title=title, version=__version__))
    return root


STARTER_SFX = ["ui_click", "ui_hover", "confirm", "cancel", "error", "menu_open", "menu_close", "text_blip", "notification",
               "coin", "pickup", "powerup", "heal", "jump", "land", "hit", "explosion", "laser", "shoot", "level_up"]


def build_starter(out: Path) -> Path:
    """Free sample: 20 SFX, the parchment UI theme (no icons/font), 8 creatures and 10 items."""
    from .sfx import CATEGORY_OF
    root = out / "assetforge-starter-free"
    for name in STARTER_SFX:
        write_wav(root / "sfx" / CATEGORY_OF[name] / f"{name}_01.wav", render(name, 1))
    comps = ui.components("parchment")
    for k, (c, _) in comps.items():
        c.save(root / "ui-parchment" / "1x" / f"{k}.png"); c.scaled(4).save(root / "ui-parchment" / "4x" / f"{k}.png")
    pals = list(sprites.PALETTES)
    for i in range(8):
        a = sprites.creature_anim(i, pals[i % len(pals)])
        for kind, frames in a.items():
            for j, f in enumerate(frames):
                f.scaled(4).save(root / "sprites" / "creatures" / f"creature_{i + 1:02d}_{kind}_{j}.png")
    from .characters import ANIMS, F as FR, hero
    from .monsters import MONSTERS
    for name, anim in (("hero_knight", hero("knight")), ("slime_green", MONSTERS["slime_green"]())):
        sheet = Canvas(max(ANIMS.values()) * FR, len(ANIMS) * FR)
        for r, a in enumerate(ANIMS):
            for i, f in enumerate(anim[a]):
                sheet.blit(f, i * FR, r * FR)
        sheet.save(root / "sprites" / "characters" / f"{name}_1x.png"); sheet.scaled(4).save(root / "sprites" / "characters" / f"{name}_4x.png")
    for k in ["sword_steel", "shield_sapphire", "gem_ruby", "potion_ruby", "potion_sapphire", "key_gold", "coin_gold", "chest_closed", "apple", "heart"]:
        sprites.items()[k].scaled(4).save(root / "sprites" / "items" / f"{k}.png")
    ui.mockup("parchment").scaled(4).save(root / "preview-ui.png")
    (root / "README.txt").write_text(
        "AssetForge Starter (free)\n\n20 retro sound effects, the Parchment UI theme (65 elements), the knight hero and the green slime\n"
        "(32x32, idle/move/attack/hurt/death, one row per animation), 8 mini-critters and 10 items.\n"
        "Free for commercial and non-commercial games. Credit appreciated, not required. Don't resell or redistribute the files.\n\n"
        "The full packs:\n  Retro SFX Pack: 155 sounds, WAV + OGG\n  Pixel Sprites Pack: 3 heroes + 24 monsters (5 animations each), 46 items, 7 effects, 3 tileset themes\n"
        "  Pixel UI Kit: 5 themes, 43 icons, pixel font, atlases\n$8 each or $18 for all 3: https://whop.com/erick-muteti/ (also on itch.io)\n")
    (root / "LICENSE.txt").write_text(LICENSE.format(title="AssetForge Starter (free)", version=__version__).replace(
        "You may NOT resell", "This sample is free. You may NOT resell"))
    _zip(root)
    return root


def build_all(out: Path, zip_packs: bool = True, sfx_variants: int = 5, creatures: int = 40) -> list[Path]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    packs = [build_sfx(out, sfx_variants), build_sprites(out, creatures), build_ui(out)]
    if zip_packs:
        for p in packs:
            _zip(p)
    return packs
