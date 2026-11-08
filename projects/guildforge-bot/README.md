# GuildForge — tournaments, ladders & giveaways for gaming Discords

A Discord bot for game communities: single-elimination **tournaments** with seeded brackets,
a server **Elo ladder** fed by tournament results, and **giveaways**. Free tier for growth,
per-server **Premium** subscription for bigger communities.

## Features

| Command | What it does |
|---|---|
| `/tournament create name [size]` | Posts a sign-up card with Join/Leave buttons |
| `/tournament start id` | Seeds players by ladder rating, builds the bracket (byes handled) |
| `/tournament report id winner` | Advances the bracket and updates Elo |
| `/tournament bracket id` · `list` · `cancel` | View / manage |
| `/ladder top` · `rank [player]` · `record winner loser` | Server Elo ladder |
| `/giveaway start prize duration [winners]` · `end` · `reroll` | Button-entry giveaways, crypto-random draws, survive restarts |
| `/premium` | Shows the plan and the native Discord upgrade button |

| Limit | Free | Premium |
|---|---|---|
| Tournament size | 16 | 128 |
| Active tournaments | 1 | 10 |
| Active giveaways | 1 | 10 |
| Giveaway winners | 3 | 20 |
| Ladder size shown | 10 | 25 |

## Run it

Requires Node.js **22.13+** (uses the built-in `node:sqlite`, so there are no native modules to compile).

```bash
npm install
cp .env.example .env          # fill DISCORD_TOKEN and DISCORD_CLIENT_ID
npm run deploy-commands       # set DEV_GUILD_ID for instant registration while testing
npm start
npm test                      # 18 tests, no network needed
```

Invite URL (replace CLIENT_ID): `https://discord.com/oauth2/authorize?client_id=CLIENT_ID&scope=bot+applications.commands&permissions=84992`
(View Channel, Send Messages, Embed Links, Read Message History). The bot only needs the `Guilds` intent, with no privileged intents, so you can verify it past 100 servers without applying for any.

## Billing

Premium uses **Discord's native App Subscriptions** (guild subscription SKU). Discord
handles checkout, tax and renewals; entitlements arrive on the interaction and are the
source of truth (`src/lib/plans.js`). Set `PREMIUM_SKU_ID` once the SKU exists in the Developer Portal → Monetization.

- Check current eligibility (country, team ownership, verification) in the
  [monetization docs](https://docs.discord.com/developers/monetization/overview) before you plan revenue around it.
- Discord's policy: if you also sell premium elsewhere, the in-Discord price can't be higher.
- `db.setOverride(guildId, true, untilMs)` covers comps, partner servers, and off-platform payments (e.g. M-Pesa/Ko-fi) if Discord monetization isn't available in your region yet.

## Deploy

Any always-on Node host works (Railway, Fly.io, a $5 VPS). Mount a volume for `DATABASE_PATH`.

```bash
# VPS example
npm ci --omit=dev && npx pm2 start "node --env-file=.env src/index.js" --name guildforge
```

## Go-to-market

1. **Pick one game niche first** and tune the copy for it, e.g. "tournament bot for FGC / chess / Valorant scrims".
   A generic bot gets lost; "the bracket bot for X" gets recommended.
2. **List on top.gg, discordbotlist.com and discords.com** on day 1. Add a vote reward (e.g. a temporary Premium boost for that server) because votes drive the rankings.
3. **Seed 10 servers by hand:** run a free tournament for small community servers in your niche. Every bracket post is an ad that members see.
4. **Upsell on hitting a limit, not with nags.** The upgrade button shows only when a server hits a free ceiling.
5. **Pricing to test:** $3.99/mo per server. Compare against what the established bots in your niche charge before you launch.
6. Track `[growth]` and `[billing]` log lines → servers joined vs. conversions.

## Roadmap

- Double elimination and Swiss formats
- Player-reported results with opponent confirmation
- Scheduled check-in before start
- Team tournaments (roles as teams)
- Web dashboard (shares billing with the other products)

## Layout

```
src/
  index.js            client, routing, giveaway scheduler
  deploy-commands.js  slash-command registration
  context.js          db + plan resolution per interaction
  db.js               node:sqlite schema + repository
  lib/bracket.js      seeding, byes, advancement, rendering (pure)
  lib/elo.js          ratings (pure)
  lib/giveaway.js     winner draw, duration parsing (pure)
  lib/plans.js        free/premium limits, entitlement checks (pure)
  commands/*.js       slash commands + button handlers
test/                 node:test suites
```
