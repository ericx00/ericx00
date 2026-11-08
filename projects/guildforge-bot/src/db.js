import { DatabaseSync } from 'node:sqlite';
import { DEFAULT_RATING } from './lib/elo.js';

const SCHEMA = `
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS guild_settings (
  guild_id TEXT PRIMARY KEY,
  premium_override INTEGER NOT NULL DEFAULT 0,
  premium_until INTEGER
);
CREATE TABLE IF NOT EXISTS tournaments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guild_id TEXT NOT NULL,
  channel_id TEXT,
  message_id TEXT,
  name TEXT NOT NULL,
  max_size INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  bracket TEXT,
  created_by TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tournaments_guild ON tournaments(guild_id, status);
CREATE TABLE IF NOT EXISTS tournament_players (
  tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  display_name TEXT NOT NULL,
  joined_at INTEGER NOT NULL,
  PRIMARY KEY (tournament_id, user_id)
);
CREATE TABLE IF NOT EXISTS ratings (
  guild_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  display_name TEXT,
  rating REAL NOT NULL DEFAULT ${DEFAULT_RATING},
  wins INTEGER NOT NULL DEFAULT 0,
  losses INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS giveaways (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  guild_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  message_id TEXT,
  prize TEXT NOT NULL,
  winner_count INTEGER NOT NULL,
  ends_at INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  host_id TEXT NOT NULL,
  winners TEXT
);
CREATE INDEX IF NOT EXISTS idx_giveaways_due ON giveaways(status, ends_at);
CREATE TABLE IF NOT EXISTS giveaway_entries (
  giveaway_id INTEGER NOT NULL REFERENCES giveaways(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  PRIMARY KEY (giveaway_id, user_id)
);
`;

export function openDb(path = ':memory:') {
  const db = new DatabaseSync(path);
  db.exec('PRAGMA foreign_keys = ON;');
  db.exec(SCHEMA);
  const q = (sql) => db.prepare(sql);

  const repo = {
    raw: db,
    close: () => db.close(),

    // --- premium override ---
    getOverride(guildId) {
      const row = q('SELECT premium_override, premium_until FROM guild_settings WHERE guild_id = ?').get(guildId);
      return row ? { premium: !!row.premium_override, until: row.premium_until ?? null } : null;
    },
    setOverride(guildId, premium, until = null) {
      q(`INSERT INTO guild_settings (guild_id, premium_override, premium_until) VALUES (?, ?, ?)
         ON CONFLICT(guild_id) DO UPDATE SET premium_override = excluded.premium_override, premium_until = excluded.premium_until`)
        .run(guildId, premium ? 1 : 0, until);
    },

    // --- tournaments ---
    createTournament({ guildId, channelId, name, maxSize, createdBy, now = Date.now() }) {
      const r = q('INSERT INTO tournaments (guild_id, channel_id, name, max_size, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)')
        .run(guildId, channelId, name, maxSize, createdBy, now);
      return Number(r.lastInsertRowid);
    },
    setTournamentMessage(id, messageId) {
      q('UPDATE tournaments SET message_id = ? WHERE id = ?').run(messageId, id);
    },
    getTournament(guildId, id) {
      const row = q('SELECT * FROM tournaments WHERE id = ? AND guild_id = ?').get(id, guildId);
      if (!row) return null;
      return { ...row, bracket: row.bracket ? JSON.parse(row.bracket) : null };
    },
    countTournaments(guildId, statuses = ['open', 'running']) {
      const marks = statuses.map(() => '?').join(',');
      return q(`SELECT COUNT(*) AS n FROM tournaments WHERE guild_id = ? AND status IN (${marks})`).get(guildId, ...statuses).n;
    },
    listTournaments(guildId, limit = 10) {
      return q('SELECT id, name, status, max_size FROM tournaments WHERE guild_id = ? ORDER BY id DESC LIMIT ?').all(guildId, limit);
    },
    addPlayer(tournamentId, userId, displayName, now = Date.now()) {
      const r = q('INSERT OR IGNORE INTO tournament_players (tournament_id, user_id, display_name, joined_at) VALUES (?, ?, ?, ?)')
        .run(tournamentId, userId, displayName, now);
      return r.changes > 0;
    },
    removePlayer(tournamentId, userId) {
      return q('DELETE FROM tournament_players WHERE tournament_id = ? AND user_id = ?').run(tournamentId, userId).changes > 0;
    },
    listPlayers(tournamentId) {
      return q('SELECT user_id, display_name FROM tournament_players WHERE tournament_id = ? ORDER BY joined_at, user_id').all(tournamentId);
    },
    saveBracket(id, bracket, status) {
      q('UPDATE tournaments SET bracket = ?, status = ? WHERE id = ?').run(JSON.stringify(bracket), status, id);
    },
    setTournamentStatus(id, status) {
      q('UPDATE tournaments SET status = ? WHERE id = ?').run(status, id);
    },

    // --- ratings ---
    getRating(guildId, userId) {
      return q('SELECT * FROM ratings WHERE guild_id = ? AND user_id = ?').get(guildId, userId)
        ?? { guild_id: guildId, user_id: userId, display_name: null, rating: DEFAULT_RATING, wins: 0, losses: 0 };
    },
    saveRating({ guildId, userId, displayName, rating, won }) {
      q(`INSERT INTO ratings (guild_id, user_id, display_name, rating, wins, losses) VALUES (?, ?, ?, ?, ?, ?)
         ON CONFLICT(guild_id, user_id) DO UPDATE SET
           display_name = COALESCE(excluded.display_name, display_name),
           rating = excluded.rating,
           wins = wins + excluded.wins,
           losses = losses + excluded.losses`)
        .run(guildId, userId, displayName ?? null, rating, won ? 1 : 0, won ? 0 : 1);
    },
    topRatings(guildId, limit = 10) {
      return q('SELECT * FROM ratings WHERE guild_id = ? ORDER BY rating DESC, wins DESC LIMIT ?').all(guildId, limit);
    },
    rankOf(guildId, userId) {
      const me = q('SELECT rating FROM ratings WHERE guild_id = ? AND user_id = ?').get(guildId, userId);
      if (!me) return null;
      return q('SELECT COUNT(*) AS n FROM ratings WHERE guild_id = ? AND rating > ?').get(guildId, me.rating).n + 1;
    },

    // --- giveaways ---
    createGiveaway({ guildId, channelId, prize, winnerCount, endsAt, hostId }) {
      const r = q('INSERT INTO giveaways (guild_id, channel_id, prize, winner_count, ends_at, host_id) VALUES (?, ?, ?, ?, ?, ?)')
        .run(guildId, channelId, prize, winnerCount, endsAt, hostId);
      return Number(r.lastInsertRowid);
    },
    setGiveawayMessage(id, messageId) {
      q('UPDATE giveaways SET message_id = ? WHERE id = ?').run(messageId, id);
    },
    getGiveaway(id) {
      const row = q('SELECT * FROM giveaways WHERE id = ?').get(id);
      return row ? { ...row, winners: row.winners ? JSON.parse(row.winners) : [] } : null;
    },
    countActiveGiveaways(guildId) {
      return q("SELECT COUNT(*) AS n FROM giveaways WHERE guild_id = ? AND status = 'active'").get(guildId).n;
    },
    enterGiveaway(id, userId) {
      return q('INSERT OR IGNORE INTO giveaway_entries (giveaway_id, user_id) VALUES (?, ?)').run(id, userId).changes > 0;
    },
    leaveGiveaway(id, userId) {
      return q('DELETE FROM giveaway_entries WHERE giveaway_id = ? AND user_id = ?').run(id, userId).changes > 0;
    },
    entrants(id) {
      return q('SELECT user_id FROM giveaway_entries WHERE giveaway_id = ?').all(id).map((r) => r.user_id);
    },
    dueGiveaways(now = Date.now()) {
      return q("SELECT id FROM giveaways WHERE status = 'active' AND ends_at <= ?").all(now).map((r) => r.id);
    },
    finishGiveaway(id, winners) {
      // Only the first caller wins the race to end a giveaway.
      const r = q("UPDATE giveaways SET status = 'ended', winners = ? WHERE id = ? AND status = 'active'").run(JSON.stringify(winners), id);
      return r.changes > 0;
    },
    setGiveawayWinners(id, winners) {
      q('UPDATE giveaways SET winners = ? WHERE id = ?').run(JSON.stringify(winners), id);
    },
  };
  return repo;
}
