"""Build the Deckbuilder Kit (paid) and the Deckbuilder Starter (free)."""
from __future__ import annotations

import json
from pathlib import Path

from . import __version__, cardsfx, deck, deckicons, music, pixfonts
from .draw import margins, nine_slice
from .pack import LICENSE, _contact_sheet, _encode, _pack_atlas, _preview, _zip
from .png import Canvas, hex_to_rgba
from .wav import SR, write_wav

H = hex_to_rgba
SCALES = (1, 2, 4)
STORE = "https://whop.com/erick-muteti/"

FREE_ICONS = ["intent_attack", "intent_defend", "intent_buff", "intent_debuff", "intent_unknown", "status_strength", "status_weak", "status_vulnerable",
              "status_burn", "status_poison", "status_block", "status_heat", "resource_energy", "resource_gold", "resource_card", "resource_draw_pile",
              "resource_discard_pile", "resource_relic", "map_fight", "map_elite", "map_boss", "map_rest", "map_shop", "action_end_turn"]
FREE_SFX = ["card_draw", "card_play", "card_flip", "card_shuffle", "card_discard", "card_select", "card_invalid", "coin_drop", "purchase", "anvil_hit",
            "steam_hiss", "slash", "blunt_hit", "shield_up", "shield_hit", "enemy_hurt", "enemy_die", "buff", "debuff", "burn_tick", "heal_soft",
            "block_gain", "turn_start", "turn_end", "chest_open", "relic_get", "victory_fanfare", "defeat_sting", "ui_tick", "ui_press", "ui_confirm", "ui_back"]
FREE_UI = ["button_ember_normal", "button_ember_hover", "button_ember_pressed", "button_ember_disabled", "panel_stone", "tooltip", "intent_bubble", "bar_frame",
           "bar_fill_hp", "bar_fill_block", "gauge_empty", "gauge_cold", "gauge_warm", "gauge_hot", "node_normal", "node_hover", "node_current", "node_done",
           "orb_empty", "orb_energy", "target_arrow", "target_dot"]
FREE_FONTS = ["sans", "tiny"]
FREE_MUSIC = ["map_embers"]


def _save(imgs: dict[str, Canvas], base: Path) -> None:
    for name, c in imgs.items():
        for k in SCALES:
            (c if k == 1 else c.scaled(k)).save(base / f"{k}x" / f"{name}.png")


def _atlas(imgs: dict[str, Canvas], base: Path, name: str, extra: dict | None = None, max_w: int = 256) -> None:
    sheet, rects = _pack_atlas(imgs, max_w)
    sheet.save(base / f"{name}.png")
    frames = {k: {"x": x, "y": y, "w": w, "h": h, **((extra or {}).get(k, {}))} for k, (x, y, w, h) in rects.items()}
    (base / f"{name}.json").write_text(json.dumps({"image": f"{name}.png", "scale": 1, "frames": frames}, indent=1))


def _fonts(root: Path, keys: list[str]) -> tuple[list[str], bool]:
    fs = pixfonts.fonts()
    made_ttf = True
    for k in keys:
        f = fs[k]
        for sc in (1, 2):
            png = f"{f.file}{'' if sc == 1 else '@2x'}.png"
            c, fnt = f.bmfont(png, sc)
            c.save(root / "fonts" / "bmfont" / png)
            (root / "fonts" / "bmfont" / png.replace(".png", ".fnt")).write_text(fnt)
        px, upm = pixfonts.TTF_UNITS[k]
        made_ttf &= f.ttf(root / "fonts" / "ttf" / f"{f.file}.ttf", px, upm, __version__)
    return [fs[k].name for k in keys], made_ttf


def font_sheet(keys: list[str]) -> Canvas:
    fs = pixfonts.fonts()
    c = Canvas(420, 34 * len(keys) + 6 + (16 if "display" in keys else 0), H("#1c1826"))
    y = 6
    for k in keys:
        f = fs[k]
        f.draw(c, 6, y, f.name, H("#ffd27a")); y += f.line + 1
        f.draw(c, 6, y, "The quick brown fox jumps over the lazy dog 0123456789", H("#f1ead8")); y += f.line
        f.draw(c, 6, y, "Deal 12 damage. Gain 8 Block! (+50%) HOT: Draw 2?", H("#9cc2ff")); y += f.line + 6
    return c


def _sfx(root: Path, names: list[str], variants: int) -> tuple[int, float, int]:
    n, secs, ogg = 0, 0.0, 0
    for name in names:
        cat = cardsfx.CATEGORY_OF[name]
        for v in range(1, variants + 1):
            sig = cardsfx.render(name, v)
            wav = write_wav(root / "sfx" / "wav" / cat / f"{name}_{v:02d}.wav", sig)
            ogg += _encode(wav, root / "sfx" / "ogg" / cat / f"{name}_{v:02d}.ogg", "ogg")
            n += 1; secs += len(sig) / SR
    return n, secs, ogg


def _music(root: Path, names: list[str]) -> list[dict]:
    info = []
    for name in names:
        sig = music.render(name)
        wav = write_wav(root / "music" / "wav" / f"{name}.wav", sig)
        _encode(wav, root / "music" / "ogg" / f"{name}.ogg", "ogg")
        t = music.TRACKS[name]
        info.append({"file": name, "title": t["title"], "use": t["use"], "bpm": t["bpm"], "bars": len(t["chords"]), "seconds": round(len(sig) / SR, 2), "loops": True})
    (root / "music" / "tracks.json").write_text(json.dumps(info, indent=1))
    return info


def _sample_cards() -> list[Canvas]:
    from .sprites import items
    it = items()
    art = lambda n: it[n].scaled(2)
    specs = [("attack", "common", "Strike", "Deal 6 damage.", art("sword_steel"), 1), ("skill", "uncommon", "Bulwark", "Gain 7 Block. COLD: Gain 4 Block.", art("shield_amethyst"), 1),
             ("power", "rare", "Berserk", "Gain 2 Strength.", art("skull"), 2), ("attack", "legendary", "Whirlwind", "Deal 6 damage to ALL enemies 3 times.", art("sword_crystal"), 3),
             ("item", "common", "Bandage", "Heal 4. Exhaust.", art("potion_emerald"), 1)]
    return [deck.sample_card(*s) for s in specs]


def battle_mockup() -> Canvas:
    """640x360 battle screen assembled only from kit parts (+ characters from the Pixel Sprites pack)."""
    from .characters import hero
    from .monsters import MONSTERS
    fs = pixfonts.fonts()
    parts = {k: v[0] for k, v in deck.ui_parts().items()}
    icons = deckicons.all_icons()
    W, Hh = 640, 360
    c = Canvas(W, Hh, H("#15111b"))
    for y in range(Hh):                                   # backdrop: brick wall fading down to a stone floor
        for x in range(W):
            if y < 196:
                brick = ((x + (12 if (y // 12) % 2 else 0)) % 24 == 0) or y % 12 == 0
                c.px[y][x] = H("#1d1826") if brick else H("#2a2336") if (x // 24 + y // 12) % 5 else H("#2f273d")
            else:
                c.px[y][x] = H("#3a3348") if y < 199 else H("#241f2e") if (x + y * 3) % 17 else H("#2c2638")
    for tx in (90, 320, 550):                             # torches
        deckicons._flame(c, tx, 92, 1.4)
        c.fill_rect(tx - 2, 92, 4, 14, H("#5a3820"))
    c.blit(hero("knight")["idle"][0].scaled(4), 96, 72)
    foes = [("skeleton_bone", 372, 3, "intent_attack", "9", 22, 30), ("ghost_spectral", 462, 3, "intent_debuff", "", 24, 28), ("bat_purple", 548, 3, "intent_multi_attack", "5x2", 12, 19)]
    for name, x, k, intent, val, hp, mhp in foes:
        fr = MONSTERS[name]()["idle"][0].scaled(k)
        # mirror so enemies face the hero
        for row in fr.px:
            row.reverse()
        c.blit(fr, x, 196 - 32 * k + 4)
        c.blit(parts["intent_bubble"], x + 33, 62); c.blit(icons[intent], x + 36, 64)
        fs["tiny"].draw(c, x + 54 - fs["tiny"].width(val) // 2 - 4, 70, val, H("#1a1423")) if val and len(val) < 3 else None
        bar = nine_slice(parts["bar_frame"], 64, 9, 3)
        c.blit(bar, x + 16, 204); c.fill_rect(x + 18, 206, int(60 * hp / mhp), 5, H("#f08a2e")); c.fill_rect(x + 18, 206, int(60 * hp / mhp), 1, H("#ffc56b"))
        t = f"{hp}/{mhp}"
        fs["tiny"].draw(c, x + 48 - fs["tiny"].width(t) // 2, 216, t, H("#f1ead8"), shadow=H("#1a1423"))
    c.blit(icons["status_vulnerable"], 392, 224); c.blit(icons["status_burn"], 482, 224); fs["tiny"].draw(c, 500, 232, "3", H("#ffd27a"), shadow=H("#1a1423"))
    # hero bars
    bar = nine_slice(parts["bar_frame"], 104, 9, 3)
    c.blit(bar, 108, 204); c.fill_rect(110, 206, 72, 5, H("#e0484f")); c.fill_rect(110, 206, 72, 1, H("#ff9aa0"))
    fs["tiny"].draw(c, 150, 216, "52/72", H("#f1ead8"), shadow=H("#1a1423"))
    c.blit(icons["status_block"], 88, 199); fs["bold"].draw(c, 76, 204, "8", H("#9cc2ff"), shadow=H("#1a1423"))
    # top bar
    top = nine_slice(parts["panel_flat"], 640, 22, 4); c.blit(top, 0, -2)
    c.blit(icons["action_heal"], 8, 2); fs["sans"].draw(c, 28, 6, "52/72", H("#ff9aa0"))
    c.blit(icons["resource_gold"], 78, 2); fs["sans"].draw(c, 98, 6, "134", H("#ffe08a"))
    for i, n in enumerate(("resource_relic", "status_thorns", "resource_potion")):
        c.blit(icons[n], 150 + i * 20, 2)
    fs["sans"].draw(c, 640 - 8 - fs["sans"].width("Undercrypt 2-4"), 6, "Undercrypt 2-4", H("#b9b0c9"))
    # heat gauge
    fs["bold"].draw(c, 14, 240, "HEAT", H("#ffd27a"), shadow=H("#1a1423"))
    for i in range(8):
        seg = "gauge_cold" if i < 2 else "gauge_warm" if i < 5 else "gauge_hot"
        c.blit(parts[seg if i < 6 else "gauge_empty"], 14 + i * 9, 252)
    fs["tiny"].draw(c, 92, 256, "6/8", H("#f1ead8"), shadow=H("#1a1423"))
    c.blit(icons["status_heat"], 110, 250)
    # piles and end turn
    c.blit(icons["resource_draw_pile"].scaled(2), 12, 320); fs["bold"].draw(c, 48, 334, "11", H("#f1ead8"), shadow=H("#1a1423"))
    c.blit(icons["resource_discard_pile"].scaled(2), 596, 320); fs["bold"].draw(c, 580, 334, "4", H("#f1ead8"), shadow=H("#1a1423"))
    btn = nine_slice(parts["button_ember_normal"], 84, 22, (4, 4, 4, 6)); c.blit(btn, 544, 244)
    fs["bold"].draw(c, 544 + (84 - fs["bold"].width("END TURN")) // 2, 250, "END TURN", H("#ffffff"), shadow=H("#7a1f1a"))
    # hand
    cards = _sample_cards()
    x0 = (W - (len(cards) * 92 - 4)) // 2
    for i, card in enumerate(cards):
        y = 236 - (14 if i == 1 else 0)
        if i == 1:
            c.blit(deck.glow("#ffe08a"), x0 + i * 92 - 3, y - 3)
        c.blit(card, x0 + i * 92, y)
    return c


README = """# {title}

Everything a card battler needs in one consistent pixel style: card frames, card-game icons, battle UI,
pixel fonts, sound effects and music loops. Made for deckbuilders, roguelikes and turn-based battles.

## What is inside (counted by the build)

{contents}

## Card layout (1x pixels, card is 88 x 124)

- Title plate: x 5, y 5, 78 x 13
- Art window: x 6, y 20, 76 x 40. It is transparent: draw your art first, then the frame on top.
  `cards/art_backgrounds` has a ready backdrop per card type.
- Type tab: centred on the bottom edge of the art. `frames_no_label` has blank tabs if you localise.
- Text box: x 6, y 70, 76 x 48 (five lines of Forge Sans).
- Cost gem: 17 x 17, placed at x 1, y 14 in the previews.
The same numbers are in `cards/layout.json`.

## Import

Use nearest-neighbour (point) filtering and no compression, or the pixels blur.
9-slice borders for buttons, panels, bars and ribbons are in `ui/atlas_ui.json` as [left, top, right, bottom] at 1x.

- Godot: Texture Filter = Nearest. NinePatchRect patch margins = the 9-slice values. Fonts: use the .ttf (turn off antialiasing,
  size = a multiple of the "crisp at" size) or import the .fnt as FontFile.
- Unity: Filter Mode = Point, Compression = None, Pixels Per Unit = 16 x your scale. Sprite Editor border = the 9-slice values.
- Web / Phaser / PixiJS: `image-rendering: pixelated`; load the .fnt with the bitmap-font loader, or the .ttf with @font-face.

## Fonts

{fonts}

## Honest notes

- Sounds and music are synthesised (chiptune style), not recorded. The music loops are simple generated beds.
- Forge Sans Bold and Forge Display are made from Forge Sans by code (thickened / doubled with smoothed corners).
- Ember Tiny has capitals, digits and punctuation; lowercase letters show as capitals.
- Characters in the battle mock-up come from the Pixel Sprites pack and are not part of this kit.
{extra}
"""


def _write_docs(root: Path, title: str, contents: list[str], font_keys: list[str], extra: str) -> None:
    fs = pixfonts.fonts()
    fonts_txt = "\n".join(f"- **{fs[k].name}** (`{fs[k].file}`): {fs[k].note}" for k in font_keys)
    (root / "README.md").write_text(README.format(title=title, contents="\n".join(f"- {x}" for x in contents), fonts=fonts_txt, extra=extra))
    (root / "LICENSE.txt").write_text(LICENSE.format(title=title, version=__version__))
    (root / "cards" / "layout.json").write_text(json.dumps({"card": [deck.CW, deck.CH], "title": deck.TITLE, "art": deck.ART, "text": deck.TEXT, "gem": [1, 14, 17, 17],
                                                            "types": list(deck.TYPES), "rarities": list(deck.RARITIES)}, indent=1))


def build_deck(out: Path, variants: int = 4) -> Path:
    root = out / "forge-deckbuilder-kit"
    cards = deck.all_cards()
    for group, imgs in cards.items():
        _save(imgs, root / "cards" / group)
    icons = deckicons.all_icons()
    _save(icons, root / "icons"); _atlas(icons, root / "icons", "atlas_icons", max_w=176)
    parts = deck.ui_parts()
    uimgs = {k: c for k, (c, _) in parts.items()}
    _save(uimgs, root / "ui")
    _atlas(uimgs, root / "ui", "atlas_ui", {k: {"nine_slice": list(margins(m)) if m is not None else None} for k, (_, m) in parts.items()})
    font_names, ttf = _fonts(root, list(pixfonts.fonts()))
    n_sfx, secs, n_ogg = _sfx(root, list(cardsfx.RECIPES), variants)
    tracks = _music(root, list(music.TRACKS))
    # previews
    P = root / "previews"
    battle_mockup().scaled(2).save(P / "battle-mockup.png")
    sc = _sample_cards(); sheet = Canvas(len(sc) * 92 + 4, 132, H("#1c1826"))
    for i, cd in enumerate(sc):
        sheet.blit(cd, 4 + i * 92, 4)
    sheet.scaled(3).save(P / "sample-cards.png")
    _contact_sheet(cards["frames"], 5, H("#1c1826")).scaled(2).save(P / "frames.png")
    _contact_sheet(cards["backs"], 6, H("#1c1826")).scaled(3).save(P / "backs.png")
    _contact_sheet(icons, 12, H("#262130")).scaled(4).save(P / "icons.png")
    _contact_sheet(uimgs, 8, H("#1c1826")).scaled(3).save(P / "ui.png")
    font_sheet(list(pixfonts.fonts())).scaled(3).save(P / "fonts.png")
    n_cards = sum(len(v) for v in cards.values())
    contents = [
        f"{len(cards['frames'])} card frames ({len(deck.TYPES)} types x {len(deck.RARITIES)} rarities) + the same {len(cards['frames_no_label'])} without the type label",
        f"{len(cards['backs'])} card backs, {len(cards['art_backgrounds'])} art backdrops, {len(cards['gems'])} cost gems, {len(cards['glows'])} card glows, {len(cards['mini'])} mini cards",
        f"{len(icons)} card-game icons (16x16): " + ", ".join(f"{len(v)} {k}" for k, v in deckicons.GROUPS.items()),
        f"{len(uimgs)} battle UI parts: buttons (4 colours x 4 states), panels, tooltip, intent bubble, bars, heat/energy gauge cells, map node badges, orbs, target arrow, ribbons",
        "Every image at 1x, 2x and 4x, plus atlases with JSON (rects + 9-slice borders)",
        f"{len(font_names)} pixel fonts ({', '.join(font_names)}) as " + ("TTF and " if ttf else "") + "BMFont (.fnt + PNG at 1x and 2x)",
        f"{n_sfx} sound effects ({len(cardsfx.RECIPES)} sounds x {variants} variations, {secs:.0f} s), WAV 44.1 kHz 16-bit" + (" + OGG" if n_ogg else "") + ": " + ", ".join(f"{len(v)} {k}" for k, v in cardsfx.CATEGORIES.items()),
        f"{len(tracks)} seamless music loops ({sum(t['seconds'] for t in tracks):.0f} s): " + ", ".join(f"{t['title']} ({t['use']}, {t['bpm']} bpm)" for t in tracks),
    ]
    _write_docs(root, "Forge Deckbuilder Kit", contents, list(pixfonts.fonts()), "")
    meta = {"version": __version__, "images": n_cards + len(icons) + len(uimgs), "icons": len(icons), "ui_parts": len(uimgs), "card_images": n_cards,
            "fonts": font_names, "ttf": ttf, "sfx": n_sfx, "sfx_recipes": len(cardsfx.RECIPES), "sfx_seconds": round(secs, 1), "music": tracks, "contents": contents}
    (root / "metadata.json").write_text(json.dumps(meta, indent=1))
    body = "".join(f'<h2>{t}</h2><img src="previews/{f}" alt="">' for t, f in (("Battle mock-up", "battle-mockup.png"), ("Sample cards", "sample-cards.png"), ("Frames", "frames.png"),
                   ("Card backs", "backs.png"), ("Icons", "icons.png"), ("UI parts", "ui.png"), ("Fonts", "fonts.png")))
    body += "<h2>Music</h2>" + "".join(f'<p>{t["title"]} ({t["use"]})<br><audio controls loop src="music/ogg/{t["file"]}.ogg"></audio></p>' for t in tracks)
    body += '<h2>Sounds</h2><div class="g">' + "".join(f'<figure><audio controls src="sfx/ogg/{cardsfx.CATEGORY_OF[n]}/{n}_01.ogg"></audio><figcaption>{n}</figcaption></figure>' for n in cardsfx.RECIPES) + "</div>"
    (root / "preview.html").write_text(_preview("Forge Deckbuilder Kit", body))
    return root


def build_deck_free(out: Path) -> Path:
    root = out / "forge-deckbuilder-starter-free"
    cards = deck.all_cards()
    keep = {
        "frames": {k: v for k, v in cards["frames"].items() if k.endswith("_common")},
        "frames_no_label": {k: v for k, v in cards["frames_no_label"].items() if k.endswith("_common")},
        "art_backgrounds": cards["art_backgrounds"],
        "backs": {k: cards["backs"][k] for k in ("ember", "frost")},
        "gems": {k: cards["gems"][k] for k in ("heat", "energy")},
        "glows": {k: cards["glows"][k] for k in ("playable", "selected")},
    }
    for group, imgs in keep.items():
        _save(imgs, root / "cards" / group)
    all_icons = deckicons.all_icons()
    icons = {k: all_icons[k] for k in FREE_ICONS}
    _save(icons, root / "icons"); _atlas(icons, root / "icons", "atlas_icons", max_w=112)
    parts = deck.ui_parts()
    uimgs = {k: parts[k][0] for k in FREE_UI}
    _save(uimgs, root / "ui")
    _atlas(uimgs, root / "ui", "atlas_ui", {k: {"nine_slice": list(margins(parts[k][1])) if parts[k][1] is not None else None} for k in FREE_UI})
    font_names, ttf = _fonts(root, FREE_FONTS)
    n_sfx, secs, n_ogg = _sfx(root, FREE_SFX, 1)
    tracks = _music(root, FREE_MUSIC)
    P = root / "previews"
    battle_mockup().scaled(2).save(P / "battle-mockup-full-kit.png")
    _contact_sheet(keep["frames"], 5, H("#1c1826")).scaled(3).save(P / "frames.png")
    _contact_sheet(icons, 12, H("#262130")).scaled(4).save(P / "icons.png")
    _contact_sheet(uimgs, 8, H("#1c1826")).scaled(3).save(P / "ui.png")
    font_sheet(FREE_FONTS).scaled(3).save(P / "fonts.png")
    n_cards = sum(len(v) for v in keep.values())
    full = json.loads((out / "forge-deckbuilder-kit" / "metadata.json").read_text()) if (out / "forge-deckbuilder-kit" / "metadata.json").exists() else None
    contents = [
        f"{len(keep['frames'])} card frames (one per card type, common rarity) + {len(keep['frames_no_label'])} without labels, {len(keep['art_backgrounds'])} art backdrops, "
        f"{len(keep['backs'])} card backs, {len(keep['gems'])} cost gems, {len(keep['glows'])} glows",
        f"{len(icons)} card-game icons (16x16)", f"{len(uimgs)} battle UI parts (button with 4 states, panel, tooltip, bars, gauge cells, map badges, orb, target arrow)",
        "Every image at 1x, 2x and 4x, plus atlases with JSON",
        f"{len(font_names)} pixel fonts ({', '.join(font_names)}) as " + ("TTF and " if ttf else "") + "BMFont",
        f"{n_sfx} sound effects, WAV" + (" + OGG" if n_ogg else ""), f"{len(tracks)} seamless music loop ({tracks[0]['title']}, {tracks[0]['seconds']:.0f} s)",
    ]
    extra = "\n## The full kit\n\n"
    if full:
        extra += "The full Forge Deckbuilder Kit has:\n" + "\n".join(f"- {x}" for x in full["contents"]) + "\n"
    extra += f"\nGet it at {STORE} or on itch.io. This free starter is complete enough to ship a small game on its own.\n"
    extra += "\n`previews/battle-mockup-full-kit.png` shows the full kit; some parts in it are not in this free starter.\n"
    _write_docs(root, "Forge Deckbuilder Starter (free)", contents, FREE_FONTS, extra)
    lic = root / "LICENSE.txt"
    lic.write_text(lic.read_text().replace("You may NOT resell", "This starter is free. You may NOT resell"))
    (root / "metadata.json").write_text(json.dumps({"version": __version__, "images": n_cards + len(icons) + len(uimgs), "icons": len(icons), "ui_parts": len(uimgs),
                                                    "card_images": n_cards, "fonts": font_names, "ttf": ttf, "sfx": n_sfx, "music": tracks, "contents": contents}, indent=1))
    return root


def build(out: Path, variants: int = 4, zip_packs: bool = True) -> list[Path]:
    packs = [build_deck(out, variants), build_deck_free(out)]
    if zip_packs:
        for p in packs:
            _zip(p)
    return packs
