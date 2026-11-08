# PatchMeta — patch-day meta guide engine

Meta guides sell on **speed**: the first good "best builds after patch X" page wins the search
traffic for that patch. PatchMeta turns structured patch data and match stats into a static, SEO-ready
guide site in milliseconds. Your job on patch day is updating JSON, not writing HTML.

## What it generates

- **Tier lists**: ranked by the Wilson lower bound of win rate, so a hero with 3/3 wins can't top the list, plus a small pick-rate bonus. Tiers come from percentiles (S top 10%, A next 20%, …).
- **Best builds per role**: an exact branch-and-bound optimizer that maximises role-weighted stats under a gold budget, slot count and per-category caps (e.g. one pair of boots). It's checked against brute force on 200 random item pools in the test suite.
- **"Every change explained"**: a buff/nerf diff between patches (knows lower cooldown/cost = buff), as an HTML page **and** Markdown for Reddit, newsletters and video scripts.
- `sitemap.xml`, `robots.txt`, canonical URLs, Open Graph tags and `Article` JSON-LD on every page.

No dependencies. Node 20+.

```bash
npm test
node src/cli.js tiers                     # print the latest tier list
node src/cli.js optimize ironvale-arena mage --require hourwand --exclude void-lens
node src/cli.js diff > post.md            # Reddit-ready patch breakdown
npm run build && npm run serve            # site in dist/, preview at http://localhost:4173
```

## Data format

```
data/<game>/game.json            name, siteUrl, roles (stat weights), build limits
data/<game>/patches/<ver>.json   heroes (stats, wins, games) and items (cost, category, stats)
```

The included **Ironvale Arena** data is a fictional sample. For a real game:

1. **Stats:** use the game's official API where one exists and its terms allow it, or your own aggregated match data. Check each source's terms of service before republishing numbers.
2. **Item/hero numbers:** official patch notes.
3. **Role weights:** these are your expertise, and they're what makes your guides better than everyone else's. Tune them, then publish the reasoning.

## Patch-day playbook (the actual business)

| When | Do |
|---|---|
| Notes drop (T+0) | Update the patch JSON numbers → `diff` → post the Markdown to the game's subreddit and your Discord within the hour |
| T+1h | `build` + deploy (Cloudflare Pages / Netlify / GitHub Pages, all free). Cut a 30–60s TikTok/Short: "3 biggest changes in patch X" |
| T+2–3 days | Update the stats once real match data exists → the tier list becomes the evergreen page for the patch |
| Ongoing | Paid tier: detailed matchup sheets / per-rank builds via Patreon, Ko-fi or Gumroad. The `Get Pro guides` card on every tier page is the CTA |

**Monetization stack:** display ads once traffic exists, the Pro guide subscription, and cross-selling the GuildForge Discord bot ("patch alerts in your server").

## Next steps

- Hero pages (`/<game>/<ver>/<hero>.html`) with per-hero builds: biggest SEO multiplier
- Per-hero weight overrides
- RSS feed + a webhook that pings a Discord channel (GuildForge) on publish
- Rank-bracket tier lists
