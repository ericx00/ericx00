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


def build_sfx(out: Path, variants: int = 4) -> Path:
    root = out / "assetforge-retro-sfx"
    figs = []
    count = 0
    for name in RECIPES:
        for v in range(1, variants + 1):
            rel = f"wav/{name}_{v:02d}.wav"
            write_wav(root / rel, render(name, v))
            figs.append(f'<figure><audio controls preload="none" src="{rel}"></audio><figcaption>{name}_{v:02d}</figcaption></figure>')
            count += 1
    title = f"Retro SFX — {count} sounds"
    (root / "preview.html").write_text(_preview(title, f'<p>16-bit mono WAV, {SR} Hz, peak-normalised, click-free edges.</p><div class="g">{"".join(figs)}</div>'))
    (root / "LICENSE.txt").write_text(LICENSE.format(title=title, version=__version__))
    return root


def build_sprites(out: Path, creatures: int = 24) -> Path:
    root = out / "assetforge-pixel-sprites"
    meta: dict[str, object] = {"scales": list(SCALES), "animations": {}}
    figs = []
    pals = list(sprites.PALETTES)
    crit = [sprites.creature(i, pals[i % len(pals)]) for i in range(creatures)]
    for i, c in enumerate(crit):
        files = _save_scaled(c, root / "creatures", f"creature_{i + 1:02d}")
        figs.append(f'<figure><img src="{files[-1]}" alt=""><figcaption>creature_{i + 1:02d}</figcaption></figure>')
    _save_scaled(sprites.sheet(crit, 8), root / "sheets", "creatures_sheet")

    frames = sprites.coin_frames()
    _save_scaled(sprites.sheet(frames, len(frames), pad=0), root / "sheets", "coin_spin")
    meta["animations"]["coin_spin"] = {"frames": len(frames), "frame_w": frames[0].w, "frame_h": frames[0].h, "fps": 10}  # type: ignore[index]
    for i, f in enumerate(frames):
        _save_scaled(f, root / "items", f"coin_{i}")

    for name, c in {"heart_full": sprites.heart(1), "heart_half": sprites.heart(0.5), "heart_empty": sprites.heart(0)}.items():
        files = _save_scaled(c, root / "items", name)
        figs.append(f'<figure><img src="{files[-1]}" alt=""><figcaption>{name}</figcaption></figure>')
    for i in range(6):
        files = _save_scaled(sprites.potion(i), root / "items", f"potion_{i + 1}")
        figs.append(f'<figure><img src="{files[-1]}" alt=""><figcaption>potion_{i + 1}</figcaption></figure>')

    (root / "metadata.json").write_text(json.dumps(meta, indent=2))
    title = f"Pixel Sprites — {creatures} creatures + items"
    (root / "preview.html").write_text(_preview(title, f'<div class="g">{"".join(figs)}</div><h2>Coin animation</h2><img src="sheets/4x/coin_spin.png" alt="">'))
    (root / "LICENSE.txt").write_text(LICENSE.format(title=title, version=__version__))
    return root


def build_ui(out: Path) -> Path:
    root = out / "assetforge-pixel-ui"
    meta: dict[str, object] = {"nine_slice_1x": ui.NINE_SLICE, "scales": list(SCALES), "themes": list(ui.THEMES)}
    figs = []
    for theme in ui.THEMES:
        items: dict[str, Canvas] = {}
        for state in ("normal", "hover", "pressed", "disabled"):
            items[f"button_{state}"] = ui.button(theme, state)
        items["panel"] = ui.panel(theme)
        for kind in ("accent", "danger"):
            for pct in (0, 25, 50, 75, 100):
                items[f"bar_{kind}_{pct}"] = ui.bar(theme, pct / 100, kind)
        items["checkbox_off"] = ui.checkbox(theme, False)
        items["checkbox_on"] = ui.checkbox(theme, True)
        items["slider_50"] = ui.slider(theme, 0.5)
        items["cursor"] = ui.cursor(theme)
        for name, c in items.items():
            files = _save_scaled(c, root / theme, name)
            if not name.startswith("bar_") or name.endswith("_75"):
                figs.append(f'<figure><img src="{files[-1]}" alt=""><figcaption>{theme}/{name}</figcaption></figure>')
    (root / "metadata.json").write_text(json.dumps(meta, indent=2))
    (root / "HOW-TO-9-SLICE.txt").write_text(
        "Buttons, panels and bar frames are 9-slice ready. Borders at 1x (multiply by your scale):\n"
        + "".join(f"  {k}: {v}px on every side\n" for k, v in ui.NINE_SLICE.items())
        + "\nUnity: Sprite Editor -> Border.  Godot: NinePatchRect patch margins.  CSS: border-image-slice.\n"
        + "Import with point/nearest filtering and no compression to keep pixels crisp.\n"
    )
    title = f"Pixel UI Kit — {len(ui.THEMES)} themes"
    (root / "preview.html").write_text(_preview(title, f'<div class="g">{"".join(figs)}</div>'))
    (root / "LICENSE.txt").write_text(LICENSE.format(title=title, version=__version__))
    return root


def build_all(out: Path, zip_packs: bool = True, sfx_variants: int = 4, creatures: int = 24) -> list[Path]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    packs = [build_sfx(out, sfx_variants), build_sprites(out, creatures), build_ui(out)]
    if zip_packs:
        for p in packs:
            _zip(p)
    return packs
