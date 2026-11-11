# Emberdeep

A browser roguelike deckbuilder with one new rule: **there is no energy, only Heat**. Every card heats the forge.
You can keep playing cards past your limit, but each point over burns you. Heat carries over between turns, so a big
turn now means a careful turn next. Cards get HOT bonuses at high Heat and COLD bonuses at low Heat.

- 3 heroes (Knight, Mage, Ranger), each with its own 20-card pool, plus 8 shared cards: **68 cards**, every one upgradable
- **24 enemies** across 3 acts, with 3 elites and 3 bosses; enemies show what they will do next
- **18 relics**, 4 events, shops, campfires, branching path choices
- 6 difficulty levels (unlocked by winning), a **daily run** with the same seed for everyone
- Saves the run in the browser; mouse, keyboard and touch
- Plain JavaScript and canvas, no engine, no dependencies. About 3.4 MB zipped.

Every sprite, icon, font, sound and music loop comes from the Forge asset packs
(Deckbuilder Kit + Pixel Sprites, built by `assetforge`). The game is also the live demo of those packs.

## Run, test, build

    python3 -m http.server 8123        # then open http://localhost:8123
    npm test                           # 10 tests: rules, content, card text fit, assets present
    npm run sim                        # bot plays 300 runs per hero and prints win rates
    npm run build                      # dist/emberdeep-html5.zip for itch.io
    scripts/assets.sh <kit dist> <sprites dist>   # refresh assets/ from built packs

`src/logic.js` is the whole rules engine (pure, seeded, serialisable). `src/main.js` draws and animates what it reports.
Card text is generated from the same data the rules run on, so a card cannot say one thing and do another.

## Balance (measured, not guessed)

`tests/bot.js` is a simple greedy bot that looks one card ahead. Over 400 runs per hero at difficulty 0 it wins
17.8% (Knight), 22.3% (Mage) and 22.3% (Ranger). A person who plans turns does much better. At difficulty 3 the bot wins under 5%.

## Benchmark (itch.io, Nov 2026)

| Game | Price | What it offers | Where we stand |
|---|---|---|---|
| Sleigh the Spire (browser) | Free, donations | Jam deckbuilder; 88 ratings in 10 days. Players criticised how close it is to its inspiration and its balance | Our core rule (Heat) is our own, and balance is bot-tested. We have less charm and no seasonal hook |
| Pixross Remastered | $3.99+ | 220 puzzles, editor, 50 visual options, 5 years of updates | Far more content and polish than us. We should not charge like this yet |
| Tower of Gold | Name your price | Very large hand-made adventure | Much larger. Shows name-your-price works for a free-first game |

Recommendation: release free in the browser with "name your own price" donations on. It is a first release and its job is to
bring players and to show the asset packs in use.

## Honest limits

- No human has play-tested it yet. The bot proves runs are winnable and heroes are close to each other; it cannot tell whether it is fun.
- Sounds and music are synthesised; nobody has listened to the music loops. Listen before publishing and tell me what sounds wrong.
- Tested in headless Chromium only. Not yet tested on a real phone, Safari or Firefox.
- No card art beyond item sprites and icons, no story, no achievements, one save slot.
- The name "Emberdeep" has not been checked against existing games or trademarks.
