// Drives the real command handlers with fake interactions (no network).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb } from '../src/db.js';
import { createContext } from '../src/context.js';
import * as tournament from '../src/commands/tournament.js';
import * as ladder from '../src/commands/leaderboard.js';
import * as giveaway from '../src/commands/giveaway.js';
import * as premium from '../src/commands/premium.js';

function fakeInteraction({ sub, options = {}, user = 'admin', manager = true, customId }) {
  const replies = [];
  const users = { admin: { id: 'admin', username: 'admin' } };
  const i = {
    guildId: 'g1', channelId: 'c1', customId,
    user: users[user] ?? { id: user, username: user },
    member: { displayName: user },
    entitlements: new Map(),
    memberPermissions: { has: () => manager },
    options: {
      getSubcommand: () => sub,
      getString: (k) => options[k] ?? null,
      getInteger: (k) => options[k] ?? null,
      getUser: (k) => options[k] ?? null,
    },
    reply: async (p) => { replies.push(p); return { resource: { message: { id: 'm1' } } }; },
    update: async (p) => { replies.push(p); },
    deferReply: async () => {},
    editReply: async (p) => { replies.push(p); },
    replies,
  };
  return i;
}

const text = (r) => (typeof r === 'string' ? r : r.content ?? r.embeds?.map((e) => JSON.stringify(e.toJSON())).join(' ') ?? '');

test('tournament: create, join, start, report to champion', async () => {
  const ctx = createContext({ db: openDb(), env: {} });
  await tournament.execute(fakeInteraction({ sub: 'create', options: { name: 'Friday Cup' } }), ctx);
  const t = ctx.db.listTournaments('g1')[0];
  assert.equal(t.max_size, 16);

  for (const u of ['ann', 'ben', 'cat']) {
    const i = fakeInteraction({ user: u, customId: `tournament:join:${t.id}` });
    await tournament.onButton(i, ctx);
    assert.ok(text(i.replies[0]).includes(u));
  }
  const dup = fakeInteraction({ user: 'ann', customId: `tournament:join:${t.id}` });
  await tournament.onButton(dup, ctx);
  assert.match(text(dup.replies[0]), /already/);

  await tournament.execute(fakeInteraction({ sub: 'start', options: { id: t.id } }), ctx);
  // 3 players: seed 1 (ann, first joined) has a bye; ben vs cat play first.
  let r = fakeInteraction({ sub: 'report', options: { id: t.id, winner: { id: 'ben' } } });
  await tournament.execute(r, ctx);
  assert.match(text(r.replies[0]), /beat/);
  r = fakeInteraction({ sub: 'report', options: { id: t.id, winner: { id: 'ann' } } });
  await tournament.execute(r, ctx);
  assert.match(text(r.replies[0]), /wins \*\*Friday Cup/);
  assert.equal(ctx.db.getTournament('g1', t.id).status, 'finished');
  assert.ok(ctx.db.getRating('g1', 'ann').rating > 1000);
});

test('free plan limits trigger the upsell', async () => {
  const ctx = createContext({ db: openDb(), env: { UPGRADE_URL: 'https://example.com/premium' } });
  const big = fakeInteraction({ sub: 'create', options: { name: 'Big', size: 64 } });
  await tournament.execute(big, ctx);
  assert.match(big.replies[0].content, /up to 16 players/);
  assert.equal(big.replies[0].components.length, 1);

  ctx.db.setOverride('g1', true);
  const ok = fakeInteraction({ sub: 'create', options: { name: 'Big', size: 64 } });
  await tournament.execute(ok, ctx);
  assert.equal(ctx.db.listTournaments('g1')[0].max_size, 64);
});

test('non-managers cannot create', async () => {
  const ctx = createContext({ db: openDb(), env: {} });
  const i = fakeInteraction({ sub: 'create', options: { name: 'X' }, manager: false });
  await tournament.execute(i, ctx);
  assert.match(i.replies[0].content, /Manage Server/);
});

test('ladder record + top', async () => {
  const ctx = createContext({ db: openDb(), env: {} });
  await ladder.execute(fakeInteraction({ sub: 'record', options: { winner: { id: 'a', username: 'a' }, loser: { id: 'b', username: 'b' } } }), ctx);
  const top = fakeInteraction({ sub: 'top' });
  await ladder.execute(top, ctx);
  assert.match(text(top.replies[0]), /1020/);
});

test('giveaway start, enter, limit', async () => {
  const ctx = createContext({ db: openDb(), env: {} });
  await giveaway.execute(fakeInteraction({ sub: 'start', options: { prize: 'Nitro', duration: '1h' } }), ctx);
  const enter = fakeInteraction({ user: 'z', customId: 'giveaway:enter:1' });
  await giveaway.onButton(enter, ctx);
  assert.deepEqual(ctx.db.entrants(1), ['z']);
  const second = fakeInteraction({ sub: 'start', options: { prize: 'More', duration: '1h' } });
  await giveaway.execute(second, ctx);
  assert.match(second.replies[0].content, /1 active giveaway/);
  const bad = fakeInteraction({ sub: 'start', options: { prize: 'x', duration: 'forever' } });
  ctx.db.setOverride('g1', true);
  await giveaway.execute(bad, ctx);
  assert.match(bad.replies[0].content, /duration/);
});

test('premium status', async () => {
  const ctx = createContext({ db: openDb(), env: {} });
  const i = fakeInteraction({ sub: null });
  await premium.execute(i, ctx);
  assert.match(text(i.replies[0]), /Free/);
});
