#!/usr/bin/env bash
# Copy the art, fonts and audio the game uses out of built asset packs.
#   scripts/assets.sh <dir with forge-deckbuilder-kit> <dir with assetforge-pixel-sprites>
set -euo pipefail
KIT="$1/forge-deckbuilder-kit"; SPR="$2/assetforge-pixel-sprites"; OUT="$(dirname "$0")/../assets"
rm -rf "$OUT"; mkdir -p "$OUT"/{cards,fonts,sfx,music,chars,items,fx}
cp "$KIT"/cards/frames/1x/*.png "$OUT/cards/"
for t in attack skill power item curse; do cp "$KIT/cards/art_backgrounds/1x/$t.png" "$OUT/cards/bg_$t.png"; done
cp "$KIT/cards/backs/1x/ember.png" "$OUT/cards/back.png"
cp "$KIT/cards/gems/1x/heat.png" "$OUT/cards/gem.png"
for g in playable selected hot cold danger; do cp "$KIT/cards/glows/1x/$g.png" "$OUT/cards/glow_$g.png"; done
cp "$KIT"/icons/atlas_icons.{png,json} "$KIT"/ui/atlas_ui.{png,json} "$OUT/"
for f in forge-sans forge-sans-bold forge-display ember-tiny; do cp "$KIT/fonts/bmfont/$f.png" "$KIT/fonts/bmfont/$f.fnt" "$OUT/fonts/"; done
find "$KIT/sfx/ogg" -name '*_0[12].ogg' -exec cp {} "$OUT/sfx/" \;
cp "$KIT"/music/ogg/*.ogg "$OUT/music/"
cp "$SPR"/characters/heroes/1x/*.png "$SPR"/characters/monsters/1x/*.png "$OUT/chars/"
cp "$SPR"/items/1x/*.png "$OUT/items/"
cp "$SPR"/effects/1x/*_strip.png "$OUT/fx/"
du -sh "$OUT"; find "$OUT" -type f | wc -l
