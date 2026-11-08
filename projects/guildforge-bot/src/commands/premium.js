import { InteractionContextType, EmbedBuilder, SlashCommandBuilder } from 'discord.js';
import { PLANS } from '../lib/plans.js';
import { BRAND_COLOR, upgradeRow } from './shared.js';

export const data = new SlashCommandBuilder()
  .setName('premium')
  .setDescription("Show this server's plan and what Premium unlocks")
  .setContexts(InteractionContextType.Guild);

const row = (label, key) => `${label}: **${PLANS.free[key]}** → **${PLANS.premium[key]}**`;

export async function execute(interaction, ctx) {
  const plan = ctx.planFor(interaction);
  const embed = new EmbedBuilder()
    .setColor(BRAND_COLOR)
    .setTitle(`This server is on ${plan.name}`)
    .setDescription([
      row('Tournament size', 'maxTournamentSize'),
      row('Active tournaments', 'maxOpenTournaments'),
      row('Active giveaways', 'maxActiveGiveaways'),
      row('Giveaway winners', 'maxGiveawayWinners'),
      row('Leaderboard size', 'leaderboardSize'),
    ].join('\n'));
  const upsell = plan === PLANS.premium ? null : upgradeRow(ctx);
  return interaction.reply({ embeds: [embed], components: upsell ? [upsell] : [] });
}
