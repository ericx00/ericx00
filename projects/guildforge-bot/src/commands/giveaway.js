import { InteractionContextType, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder, SlashCommandBuilder, time, TimestampStyles } from 'discord.js';
import { parseDuration, pickWinners } from '../lib/giveaway.js';
import { BRAND_COLOR, ephemeral, isManager, limitReply } from './shared.js';

const MAX_DURATION = 30 * 86400e3;

export const data = new SlashCommandBuilder()
  .setName('giveaway')
  .setDescription('Run giveaways')
  .setContexts(InteractionContextType.Guild)
  .addSubcommand((s) => s.setName('start').setDescription('Start a giveaway in this channel')
    .addStringOption((o) => o.setName('prize').setDescription('What are you giving away?').setRequired(true).setMaxLength(200))
    .addStringOption((o) => o.setName('duration').setDescription('e.g. 30m, 2h, 1d, 1h30m').setRequired(true))
    .addIntegerOption((o) => o.setName('winners').setDescription('Number of winners (default 1)').setMinValue(1).setMaxValue(20)))
  .addSubcommand((s) => s.setName('end').setDescription('End a giveaway now')
    .addIntegerOption((o) => o.setName('id').setDescription('Giveaway ID').setRequired(true)))
  .addSubcommand((s) => s.setName('reroll').setDescription('Pick new winners for an ended giveaway')
    .addIntegerOption((o) => o.setName('id').setDescription('Giveaway ID').setRequired(true)));

export function giveawayEmbed(g, entrantCount) {
  const ended = g.status !== 'active';
  const e = new EmbedBuilder()
    .setColor(ended ? 0x555555 : BRAND_COLOR)
    .setTitle(`🎁 ${g.prize}`)
    .setFooter({ text: `Giveaway ID ${g.id} · ${g.winner_count} winner(s)` });
  if (ended) {
    e.setDescription(g.winners.length ? `Winners: ${g.winners.map((w) => `<@${w}>`).join(', ')}` : 'Ended with no valid entries.');
  } else {
    e.setDescription(`Hosted by <@${g.host_id}>\nEnds ${time(Math.floor(g.ends_at / 1000), TimestampStyles.RelativeTime)}\nEntries: **${entrantCount}**`);
  }
  return e;
}

export function giveawayButtons(id, disabled = false) {
  return new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId(`giveaway:enter:${id}`).setLabel('Enter').setEmoji('🎉').setStyle(ButtonStyle.Primary).setDisabled(disabled),
    new ButtonBuilder().setCustomId(`giveaway:leave:${id}`).setLabel('Leave').setStyle(ButtonStyle.Secondary).setDisabled(disabled),
  );
}

/** End a giveaway, announce winners and lock the original message. Safe to call twice. */
export async function concludeGiveaway(client, db, id) {
  const g = db.getGiveaway(id);
  if (!g || g.status !== 'active') return null;
  const winners = pickWinners(db.entrants(id), g.winner_count);
  if (!db.finishGiveaway(id, winners)) return null;
  const ended = db.getGiveaway(id);
  const channel = await client.channels.fetch(g.channel_id).catch(() => null);
  if (channel?.isTextBased()) {
    if (g.message_id) {
      const msg = await channel.messages.fetch(g.message_id).catch(() => null);
      await msg?.edit({ embeds: [giveawayEmbed(ended, 0)], components: [giveawayButtons(id, true)] }).catch(() => null);
    }
    await channel.send(winners.length
      ? `🎉 Congratulations ${winners.map((w) => `<@${w}>`).join(', ')}! You won **${g.prize}**.`
      : `The giveaway for **${g.prize}** ended with no entries.`).catch(() => null);
  }
  return ended;
}

export async function execute(interaction, ctx) {
  const sub = interaction.options.getSubcommand();
  const { db } = ctx;
  if (!isManager(interaction)) return interaction.reply(ephemeral('You need the **Manage Server** permission to manage giveaways.'));

  if (sub === 'start') {
    const plan = ctx.planFor(interaction);
    if (db.countActiveGiveaways(interaction.guildId) >= plan.maxActiveGiveaways) {
      return interaction.reply(limitReply(ctx, `The ${plan.name} plan allows ${plan.maxActiveGiveaways} active giveaway(s) at a time.`));
    }
    const winnerCount = interaction.options.getInteger('winners') ?? 1;
    if (winnerCount > plan.maxGiveawayWinners) {
      return interaction.reply(limitReply(ctx, `The ${plan.name} plan allows up to ${plan.maxGiveawayWinners} winners.`));
    }
    const ms = parseDuration(interaction.options.getString('duration', true));
    if (!ms || ms > MAX_DURATION) return interaction.reply(ephemeral('Use a duration like `30m`, `2h` or `1d` (max 30 days).'));
    const id = db.createGiveaway({
      guildId: interaction.guildId, channelId: interaction.channelId, prize: interaction.options.getString('prize', true),
      winnerCount, endsAt: Date.now() + ms, hostId: interaction.user.id,
    });
    const g = db.getGiveaway(id);
    const res = await interaction.reply({ embeds: [giveawayEmbed(g, 0)], components: [giveawayButtons(id)], withResponse: true });
    db.setGiveawayMessage(id, res.resource?.message?.id ?? null);
    return;
  }

  const id = interaction.options.getInteger('id', true);
  const g = db.getGiveaway(id);
  if (!g || g.guild_id !== interaction.guildId) return interaction.reply(ephemeral(`No giveaway with ID \`${id}\` here.`));

  if (sub === 'end') {
    if (g.status !== 'active') return interaction.reply(ephemeral('That giveaway already ended.'));
    await interaction.deferReply({ flags: ephemeral('').flags });
    await concludeGiveaway(interaction.client, db, id);
    return interaction.editReply('Giveaway ended.');
  }

  if (sub === 'reroll') {
    if (g.status === 'active') return interaction.reply(ephemeral('End the giveaway before rerolling.'));
    const pool = db.entrants(id).filter((u) => !g.winners.includes(u));
    const winners = pickWinners(pool, g.winner_count);
    if (!winners.length) return interaction.reply(ephemeral('No other entrants to reroll to.'));
    db.setGiveawayWinners(id, winners);
    return interaction.reply(`🔁 New winner(s) for **${g.prize}**: ${winners.map((w) => `<@${w}>`).join(', ')}`);
  }
}

export async function onButton(interaction, ctx) {
  const [, action, rawId] = interaction.customId.split(':');
  const id = Number(rawId);
  const g = ctx.db.getGiveaway(id);
  if (!g || g.status !== 'active' || g.ends_at <= Date.now()) return interaction.reply(ephemeral('This giveaway has ended.'));
  if (action === 'enter') {
    if (!ctx.db.enterGiveaway(id, interaction.user.id)) return interaction.reply(ephemeral('You are already entered. Good luck!'));
  } else if (action === 'leave') {
    if (!ctx.db.leaveGiveaway(id, interaction.user.id)) return interaction.reply(ephemeral('You were not entered.'));
  } else {
    return;
  }
  return interaction.update({ embeds: [giveawayEmbed(g, ctx.db.entrants(id).length)], components: [giveawayButtons(id)] });
}
