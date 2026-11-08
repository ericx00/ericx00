# Gamer digital products: five projects

Five independent products, each a self-contained folder ready to become its own GitHub repository
(see `../scripts/split-repos.sh`). Built in order of demand; ship #1 first.

| # | Project | What it is | Stack | Tests |
|---|---|---|---|---|
| 1 | [`guildforge-bot`](guildforge-bot) | Discord bot: tournaments, Elo ladder, giveaways; free tier + per-server Premium via Discord App Subscriptions | Node 22, discord.js 14, built-in SQLite | 18 |
| 2 | [`patchmeta`](patchmeta) | Patch-day meta guide engine: tier lists, exact build optimizer, patch-diff articles, static SEO site | Node, zero deps | 7 |
| 3 | [`overlaykit`](overlaykit) | Themeable stream overlay packs: OBS scenes, StreamElements alert widget, Twitch panels, store previews | HTML/CSS/JS, Node build | 9 |
| 4 | [`sensforge`](sensforge) | Sensitivity converter (cm/360), PSA sens finder, 3D aim trainer that uses your real sens | Static web app, zero deps | 7 |
| 5 | [`assetforge`](assetforge) | Procedural original asset packs: retro SFX, pixel sprites, 9-slice pixel UI kit | Python stdlib only | 10 |

See [RESEARCH.md](RESEARCH.md) for the market notes, sources and launch order.

```bash
(cd guildforge-bot && npm install && npm test)
(cd patchmeta && npm test && npm run build)
(cd overlaykit && npm test && npm run build)
(cd sensforge && npm test && npm run serve)
(cd assetforge && python3 -m unittest discover -s tests -t . && python3 -m assetforge build)
```
