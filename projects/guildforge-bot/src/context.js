import { resolvePlan } from './lib/plans.js';

export function createContext({ db, env = process.env }) {
  const config = {
    premiumSkuId: env.PREMIUM_SKU_ID || null,
    upgradeUrl: env.UPGRADE_URL || null,
  };
  return {
    db,
    config,
    /** Resolve the plan for the guild an interaction came from. */
    planFor(interaction) {
      return resolvePlan({
        guildId: interaction.guildId,
        entitlements: interaction.entitlements ?? [],
        skuId: config.premiumSkuId,
        override: db.getOverride(interaction.guildId),
      });
    },
  };
}
