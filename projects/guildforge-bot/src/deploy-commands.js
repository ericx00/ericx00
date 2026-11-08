import { REST, Routes } from 'discord.js';
import { commands } from './commands/index.js';

const { DISCORD_TOKEN, DISCORD_CLIENT_ID, DEV_GUILD_ID } = process.env;
if (!DISCORD_TOKEN || !DISCORD_CLIENT_ID) {
  console.error('Set DISCORD_TOKEN and DISCORD_CLIENT_ID in .env');
  process.exit(1);
}

const body = [...commands.values()].map((c) => c.data.toJSON());
const rest = new REST().setToken(DISCORD_TOKEN);
const route = DEV_GUILD_ID
  ? Routes.applicationGuildCommands(DISCORD_CLIENT_ID, DEV_GUILD_ID)
  : Routes.applicationCommands(DISCORD_CLIENT_ID);

const result = await rest.put(route, { body });
console.log(`Registered ${result.length} command(s) ${DEV_GUILD_ID ? `to guild ${DEV_GUILD_ID}` : 'globally'}.`);
