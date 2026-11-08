# Research notes (November 2026)

Facts checked while building. Re-check anything money-related before launch, because platform terms change.

## 1. Discord bot (GuildForge)
- Discord's monetization model: **SKUs** (what you sell) and **entitlements** (who has access). Entitlements are the source of truth.
  Subscriptions can be **user**-scoped or **guild**-scoped. GuildForge uses guild-scoped: one purchase upgrades the whole server.
  Test entitlements can be created and deleted for development. [Discord docs: monetization overview](https://docs.discord.com/developers/monetization/overview), [app subscriptions](https://docs.discord.com/developers/monetization/app-subscriptions), [managing SKUs](https://docs.discord.com/developers/monetization/managing-skus)
- **Eligibility caveat:** a Discord help-center article (date not shown) listed Premium Apps as available to developers in the US, UK and EU, and said the price in Discord can't be higher than other payment options.
  **If you're in Kenya**, confirm current eligibility first. The bot has a manual premium override (`db.setOverride`) so you can sell through
  M-Pesa / Paystack / Ko-fi meanwhile. [Discord dev support article](https://support-dev.discord.com/hc/en-us/articles/17709085688727)
- discord.js current release **14.28.1** (npm, `engines: node >=18`). Pinned `^14.28.1`.
- Distribution: top.gg and other bot lists. Votes drive rankings, so the bot design includes a vote-reward hook (roadmap).

## 2. Meta guides (PatchMeta)
- Demand spikes per patch, so speed is the moat. The engine produces a Reddit-ready diff in seconds and a full static site in ~30 ms.
- Ship only data you're allowed to use: official patch notes, official APIs within their terms, or your own match data.

## 3. Stream overlays (OverlayKit)
- StreamElements custom widgets take HTML/CSS/JS/fields. Events arrive via `onEventReceived` with listeners like `follower-latest`, `subscriber-latest`, `tip-latest`, `cheer-latest`, `raid-latest`.
- Twitch panels: 320 px wide images.

## 4. Sensitivity / aim (SensForge)
- Yaw values: CS2 & Apex **0.022**, VALORANT **0.07**, Overwatch 2 & CoD **0.0066**, Fortnite **≈0.005555** (FOV-dependent, so it's approximate). Reference conversions:
  VALORANT→CS2 ×3.18, CS2→OW2 ×3.333, CS2 3.09 @ 400 DPI ≈ 33.6 cm/360 (≈0.97 VALORANT). All are pinned in tests.
  [csdb.gg converter](https://csdb.gg/sensitivity-converter/), [recharge.com overview](https://www.recharge.com/blog/en-gb/valorant-sensitivity-converter-cs2-apex-ow2-fortnite), [mouse-sensitivity.com](https://www.mouse-sensitivity.com/n/valorant/)
- Established competitors exist (mouse-sensitivity.com, Aim Lab, Kovaak's). The angle here is free + in-browser + PSA built in + "trainer uses your exact sens".

## 5. Asset packs (AssetForge)
- itch.io top-seller listings for UI-tagged asset packs are dominated by **SFX packs and pixel UI kits**. Example prices seen: pixel UI kits ~$4–$30, large SFX libraries ~$6–$40, with deep discounts during sales and bundles.
  These are storefront examples, not a sales ranking. [itch.io top sellers: asset pack + UI](https://itch.io/game-assets/top-sellers/tag-asset-pack/tag-user-interface-ui)
- Everything is generated from scratch, so there are no third-party IP or ToS issues. The work that adds value is curation.

## Launch order (solo-dev reality)
1. **GuildForge**: 2–3 weeks to live; recurring revenue; free distribution via bot lists.
2. **SensForge**: already shippable as a static site; SEO + Shorts.
3. **PatchMeta**: pick one game you actually play; first real patch day is the launch.
4. **OverlayKit** and **AssetForge**: packaging and listings; mostly curation and marketing time.

Cross-sell: the bot links to the guides and sens tool; the guides advertise the bot; the asset packs and overlays share one storefront.
