// Plan limits. Keep the free tier genuinely useful: it is what gets you listed,
// reviewed and voted for on top.gg. Premium removes the ceilings that only
// larger, more active communities hit.
export const PLANS = Object.freeze({
  free: Object.freeze({
    name: 'Free',
    maxTournamentSize: 16,
    maxOpenTournaments: 1,
    maxActiveGiveaways: 1,
    maxGiveawayWinners: 3,
    leaderboardSize: 10,
  }),
  premium: Object.freeze({
    name: 'Premium',
    maxTournamentSize: 128,
    maxOpenTournaments: 10,
    maxActiveGiveaways: 10,
    maxGiveawayWinners: 20,
    leaderboardSize: 25,
  }),
});

/**
 * Is an entitlement currently active for this guild and SKU?
 * Works with discord.js Entitlement objects and plain objects alike.
 */
export function isActiveEntitlement(ent, { skuId, guildId, now = Date.now() }) {
  if (!ent || !skuId) return false;
  if (ent.skuId !== skuId) return false;
  if (ent.deleted) return false;
  if (ent.guildId && guildId && ent.guildId !== guildId) return false;
  const ends = ent.endsTimestamp ?? (ent.endsAt ? new Date(ent.endsAt).getTime() : null);
  if (ends != null && ends <= now) return false;
  const starts = ent.startsTimestamp ?? (ent.startsAt ? new Date(ent.startsAt).getTime() : null);
  if (starts != null && starts > now) return false;
  return true;
}

/**
 * Resolve the plan for a guild. Discord entitlements are the source of truth;
 * the manual override covers comps, partners and off-platform payments.
 */
export function resolvePlan({ guildId, entitlements = [], skuId, override, now = Date.now() }) {
  const list = Array.isArray(entitlements) ? entitlements : [...entitlements.values()];
  if (list.some((e) => isActiveEntitlement(e, { skuId, guildId, now }))) return PLANS.premium;
  if (override && override.premium && (override.until == null || override.until > now)) return PLANS.premium;
  return PLANS.free;
}
