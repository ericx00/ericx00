import { ActionRowBuilder, ButtonBuilder, ButtonStyle, MessageFlags, PermissionFlagsBits } from 'discord.js';

export const BRAND_COLOR = 0x7c5cff;

export function isManager(interaction) {
  return interaction.memberPermissions?.has(PermissionFlagsBits.ManageGuild) ?? false;
}

export function ephemeral(content, extra = {}) {
  return { content, flags: MessageFlags.Ephemeral, ...extra };
}

/** Upsell row: Discord's native premium button when a SKU is configured, else a link. */
export function upgradeRow(ctx) {
  if (ctx.config.premiumSkuId) {
    return new ActionRowBuilder().addComponents(
      new ButtonBuilder().setStyle(ButtonStyle.Premium).setSKUId(ctx.config.premiumSkuId),
    );
  }
  if (ctx.config.upgradeUrl) {
    return new ActionRowBuilder().addComponents(
      new ButtonBuilder().setStyle(ButtonStyle.Link).setURL(ctx.config.upgradeUrl).setLabel('Upgrade to Premium'),
    );
  }
  return null;
}

export function limitReply(ctx, message) {
  const row = upgradeRow(ctx);
  return ephemeral(`${message}\nPremium raises this limit for the whole server.`, row ? { components: [row] } : {});
}
