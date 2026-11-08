import { Client, Events, GatewayIntentBits, MessageFlags } from 'discord.js';
import { openDb } from './db.js';
import { createContext } from './context.js';
import { commands } from './commands/index.js';
import { concludeGiveaway } from './commands/giveaway.js';

const token = process.env.DISCORD_TOKEN;
if (!token) {
  console.error('DISCORD_TOKEN is missing. Copy .env.example to .env and fill it in.');
  process.exit(1);
}

const db = openDb(process.env.DATABASE_PATH || 'guildforge.db');
const ctx = createContext({ db });
const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once(Events.ClientReady, (c) => {
  console.log(`Logged in as ${c.user.tag} in ${c.guilds.cache.size} server(s).`);
  // Giveaway scheduler: end anything that is due (also catches giveaways that expired while offline).
  const tick = async () => {
    for (const id of db.dueGiveaways()) {
      await concludeGiveaway(client, db, id).catch((err) => console.error(`giveaway ${id}:`, err));
    }
  };
  tick();
  setInterval(tick, 15_000).unref();
});

client.on(Events.InteractionCreate, async (interaction) => {
  try {
    if (interaction.isChatInputCommand()) {
      const cmd = commands.get(interaction.commandName);
      if (cmd) await cmd.execute(interaction, ctx);
    } else if (interaction.isButton()) {
      const cmd = commands.get(interaction.customId.split(':')[0]);
      if (cmd?.onButton) await cmd.onButton(interaction, ctx);
    }
  } catch (err) {
    console.error(err);
    const payload = { content: 'Something went wrong running that. It has been logged.', flags: MessageFlags.Ephemeral };
    if (interaction.isRepliable()) {
      if (interaction.replied || interaction.deferred) await interaction.followUp(payload).catch(() => null);
      else await interaction.reply(payload).catch(() => null);
    }
  }
});

client.on(Events.EntitlementCreate, (e) => console.log(`[billing] new entitlement sku=${e.skuId} guild=${e.guildId ?? '-'} user=${e.userId ?? '-'}`));
client.on(Events.EntitlementDelete, (e) => console.log(`[billing] entitlement removed sku=${e.skuId} guild=${e.guildId ?? '-'}`));
client.on(Events.GuildCreate, (g) => console.log(`[growth] joined ${g.name} (${g.memberCount} members)`));

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, async () => {
    await client.destroy();
    db.close();
    process.exit(0);
  });
}

client.login(token);
