import { InteractionContextType, EmbedBuilder, SlashCommandBuilder } from 'discord.js';
import { updateRatings } from '../lib/elo.js';
import { BRAND_COLOR, ephemeral, isManager } from './shared.js';

export const data = new SlashCommandBuilder()
  .setName('ladder')
  .setDescription('Server Elo ladder')
  .setContexts(InteractionContextType.Guild)
  .addSubcommand((s) => s.setName('top').setDescription('Show the top players'))
  .addSubcommand((s) => s.setName('rank').setDescription("Show a player's rating")
    .addUserOption((o) => o.setName('player').setDescription('Defaults to you')))
  .addSubcommand((s) => s.setName('record').setDescription('Record a match result (Manage Server)')
    .addUserOption((o) => o.setName('winner').setDescription('Winner').setRequired(true))
    .addUserOption((o) => o.setName('loser').setDescription('Loser').setRequired(true)));

const MEDALS = ['🥇', '🥈', '🥉'];

export async function execute(interaction, ctx) {
  const sub = interaction.options.getSubcommand();
  const { db } = ctx;
  const guildId = interaction.guildId;

  if (sub === 'top') {
    const plan = ctx.planFor(interaction);
    const rows = db.topRatings(guildId, plan.leaderboardSize);
    const body = rows.length
      ? rows.map((r, i) => `${MEDALS[i] ?? `\`#${i + 1}\``} **${r.display_name ?? `<@${r.user_id}>`}** — ${Math.round(r.rating)} (${r.wins}W/${r.losses}L)`).join('\n')
      : 'No games recorded yet. Use `/ladder record` or finish a tournament match.';
    return interaction.reply({ embeds: [new EmbedBuilder().setColor(BRAND_COLOR).setTitle('🏅 Server ladder').setDescription(body)] });
  }

  if (sub === 'rank') {
    const user = interaction.options.getUser('player') ?? interaction.user;
    const r = db.getRating(guildId, user.id);
    const rank = db.rankOf(guildId, user.id);
    return interaction.reply(ephemeral(rank
      ? `${user} is **#${rank}** with **${Math.round(r.rating)}** (${r.wins}W/${r.losses}L).`
      : `${user} has no recorded games yet.`));
  }

  if (sub === 'record') {
    if (!isManager(interaction)) return interaction.reply(ephemeral('You need the **Manage Server** permission to record results.'));
    const winner = interaction.options.getUser('winner', true);
    const loser = interaction.options.getUser('loser', true);
    if (winner.id === loser.id) return interaction.reply(ephemeral('Winner and loser must be different players.'));
    const w = db.getRating(guildId, winner.id);
    const l = db.getRating(guildId, loser.id);
    const next = updateRatings({ rating: w.rating, games: w.wins + w.losses }, { rating: l.rating, games: l.wins + l.losses });
    db.saveRating({ guildId, userId: winner.id, displayName: winner.displayName ?? winner.username, rating: next.winner, won: true });
    db.saveRating({ guildId, userId: loser.id, displayName: loser.displayName ?? loser.username, rating: next.loser, won: false });
    const dw = next.winner - w.rating;
    const dl = next.loser - l.rating;
    return interaction.reply(`✅ ${winner} beat ${loser}. ${Math.round(next.winner)} (+${dw.toFixed(1)}) / ${Math.round(next.loser)} (${dl.toFixed(1)})`);
  }
}
