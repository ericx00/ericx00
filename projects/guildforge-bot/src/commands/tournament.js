import { InteractionContextType, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder, SlashCommandBuilder } from 'discord.js';
import { createBracket, renderBracket, reportResult, findPendingMatchFor } from '../lib/bracket.js';
import { updateRatings } from '../lib/elo.js';
import { BRAND_COLOR, ephemeral, isManager, limitReply } from './shared.js';

export const data = new SlashCommandBuilder()
  .setName('tournament')
  .setDescription('Run single-elimination tournaments')
  .setContexts(InteractionContextType.Guild)
  .addSubcommand((s) => s.setName('create').setDescription('Open sign-ups for a new tournament')
    .addStringOption((o) => o.setName('name').setDescription('Tournament name').setRequired(true).setMaxLength(80))
    .addIntegerOption((o) => o.setName('size').setDescription('Max players (default: plan max)').setMinValue(2).setMaxValue(128)))
  .addSubcommand((s) => s.setName('start').setDescription('Close sign-ups and generate the bracket')
    .addIntegerOption((o) => o.setName('id').setDescription('Tournament ID').setRequired(true)))
  .addSubcommand((s) => s.setName('report').setDescription('Report the winner of a match')
    .addIntegerOption((o) => o.setName('id').setDescription('Tournament ID').setRequired(true))
    .addUserOption((o) => o.setName('winner').setDescription('Who won the match').setRequired(true)))
  .addSubcommand((s) => s.setName('bracket').setDescription('Show the current bracket')
    .addIntegerOption((o) => o.setName('id').setDescription('Tournament ID').setRequired(true)))
  .addSubcommand((s) => s.setName('cancel').setDescription('Cancel a tournament')
    .addIntegerOption((o) => o.setName('id').setDescription('Tournament ID').setRequired(true)))
  .addSubcommand((s) => s.setName('list').setDescription('List recent tournaments'));

function signupEmbed(t, players) {
  return new EmbedBuilder()
    .setColor(BRAND_COLOR)
    .setTitle(`🏆 ${t.name}`)
    .setDescription(`Sign-ups are **${t.status === 'open' ? 'open' : 'closed'}**. Tournament ID: \`${t.id}\``)
    .addFields({
      name: `Players (${players.length}/${t.max_size})`,
      value: players.length ? players.map((p, i) => `${i + 1}. ${p.display_name}`).join('\n').slice(0, 1024) : '_Nobody yet. Be first!_',
    });
}

function signupButtons(id, disabled = false) {
  return new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId(`tournament:join:${id}`).setLabel('Join').setStyle(ButtonStyle.Success).setDisabled(disabled),
    new ButtonBuilder().setCustomId(`tournament:leave:${id}`).setLabel('Leave').setStyle(ButtonStyle.Secondary).setDisabled(disabled),
  );
}

function bracketEmbed(t) {
  return new EmbedBuilder().setColor(BRAND_COLOR).setTitle(`🏆 ${t.name} — bracket`)
    .setDescription(renderBracket(t.bracket).slice(0, 4096)).setFooter({ text: `Tournament ID ${t.id} · status: ${t.status}` });
}

export async function execute(interaction, ctx) {
  const sub = interaction.options.getSubcommand();
  const { db } = ctx;
  const guildId = interaction.guildId;

  if (sub === 'list') {
    const rows = db.listTournaments(guildId);
    return interaction.reply(ephemeral(rows.length
      ? rows.map((t) => `\`${t.id}\` **${t.name}** — ${t.status} (max ${t.max_size})`).join('\n')
      : 'No tournaments yet. Create one with `/tournament create`.'));
  }

  if (sub === 'create') {
    if (!isManager(interaction)) return interaction.reply(ephemeral('You need the **Manage Server** permission to create tournaments.'));
    const plan = ctx.planFor(interaction);
    if (db.countTournaments(guildId) >= plan.maxOpenTournaments) {
      return interaction.reply(limitReply(ctx, `The ${plan.name} plan allows ${plan.maxOpenTournaments} active tournament(s) at a time.`));
    }
    const requested = interaction.options.getInteger('size') ?? plan.maxTournamentSize;
    if (requested > plan.maxTournamentSize) {
      return interaction.reply(limitReply(ctx, `The ${plan.name} plan supports up to ${plan.maxTournamentSize} players.`));
    }
    const id = db.createTournament({
      guildId, channelId: interaction.channelId, name: interaction.options.getString('name', true),
      maxSize: requested, createdBy: interaction.user.id,
    });
    const t = db.getTournament(guildId, id);
    const reply = await interaction.reply({ embeds: [signupEmbed(t, [])], components: [signupButtons(id)], withResponse: true });
    db.setTournamentMessage(id, reply.resource?.message?.id ?? null);
    return;
  }

  const id = interaction.options.getInteger('id', true);
  const t = db.getTournament(guildId, id);
  if (!t) return interaction.reply(ephemeral(`No tournament with ID \`${id}\` in this server.`));

  if (sub === 'bracket') {
    if (!t.bracket) return interaction.reply(ephemeral('The bracket is generated when the tournament starts.'));
    return interaction.reply({ embeds: [bracketEmbed(t)] });
  }

  if (!isManager(interaction)) return interaction.reply(ephemeral('You need the **Manage Server** permission for that.'));

  if (sub === 'cancel') {
    db.setTournamentStatus(id, 'cancelled');
    return interaction.reply(`❌ **${t.name}** was cancelled.`);
  }

  if (sub === 'start') {
    if (t.status !== 'open') return interaction.reply(ephemeral(`This tournament is already ${t.status}.`));
    const players = db.listPlayers(id);
    if (players.length < 2) return interaction.reply(ephemeral('At least 2 players must join before starting.'));
    // Seed by server rating so the strongest players meet late.
    const seeded = players
      .map((p) => ({ id: p.user_id, name: p.display_name, rating: db.getRating(guildId, p.user_id).rating }))
      .sort((a, b) => b.rating - a.rating);
    const bracket = createBracket(seeded);
    db.saveBracket(id, bracket, 'running');
    return interaction.reply({ content: `🚦 **${t.name}** has started with ${players.length} players!`, embeds: [bracketEmbed({ ...t, bracket, status: 'running' })] });
  }

  if (sub === 'report') {
    if (t.status !== 'running') return interaction.reply(ephemeral('This tournament is not running.'));
    const winner = interaction.options.getUser('winner', true);
    if (!findPendingMatchFor(t.bracket, winner.id)) return interaction.reply(ephemeral(`${winner} has no match waiting for a result.`));
    const { loser, champion } = reportResult(t.bracket, winner.id);
    db.saveBracket(id, t.bracket, champion ? 'finished' : 'running');

    // Tournament games count toward the server's Elo ladder.
    const name = (uid) => t.bracket.players.find((p) => p.id === uid)?.name;
    const w = db.getRating(guildId, winner.id);
    const l = db.getRating(guildId, loser);
    const next = updateRatings({ rating: w.rating, games: w.wins + w.losses }, { rating: l.rating, games: l.wins + l.losses });
    db.saveRating({ guildId, userId: winner.id, displayName: name(winner.id), rating: next.winner, won: true });
    db.saveRating({ guildId, userId: loser, displayName: name(loser), rating: next.loser, won: false });

    const updated = { ...t, status: champion ? 'finished' : 'running' };
    const content = champion ? `👑 **${name(champion)}** wins **${t.name}**!` : `✅ ${name(winner.id)} beat ${name(loser)}.`;
    return interaction.reply({ content, embeds: [bracketEmbed(updated)] });
  }
}

export async function onButton(interaction, ctx) {
  const [, action, rawId] = interaction.customId.split(':');
  const id = Number(rawId);
  const t = ctx.db.getTournament(interaction.guildId, id);
  if (!t) return interaction.reply(ephemeral('This tournament no longer exists.'));
  if (t.status !== 'open') return interaction.reply(ephemeral('Sign-ups are closed.'));

  if (action === 'join') {
    if (ctx.db.listPlayers(id).length >= t.max_size) return interaction.reply(ephemeral('The tournament is full.'));
    const name = interaction.member?.displayName ?? interaction.user.globalName ?? interaction.user.username;
    if (!ctx.db.addPlayer(id, interaction.user.id, name)) return interaction.reply(ephemeral('You are already signed up.'));
  } else if (action === 'leave') {
    if (!ctx.db.removePlayer(id, interaction.user.id)) return interaction.reply(ephemeral('You were not signed up.'));
  } else {
    return;
  }
  const players = ctx.db.listPlayers(id);
  return interaction.update({ embeds: [signupEmbed(t, players)], components: [signupButtons(id)] });
}
