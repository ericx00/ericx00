import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDb } from '../src/db.js';
import { createBracket, reportResult } from '../src/lib/bracket.js';

test('tournament lifecycle persists', () => {
  const db = openDb();
  const id = db.createTournament({ guildId: 'g', channelId: 'c', name: 'Cup', maxSize: 8, createdBy: 'u' });
  assert.equal(db.getTournament('other-guild', id), null, 'tournaments are scoped to their guild');
  assert.ok(db.addPlayer(id, 'a', 'Alice'));
  assert.ok(!db.addPlayer(id, 'a', 'Alice'), 'no double sign-up');
  db.addPlayer(id, 'b', 'Bob');
  db.addPlayer(id, 'c', 'Cara');
  assert.ok(db.removePlayer(id, 'c'));
  assert.equal(db.countTournaments('g'), 1);

  const bracket = createBracket(db.listPlayers(id).map((p) => ({ id: p.user_id, name: p.display_name })));
  db.saveBracket(id, bracket, 'running');
  const t = db.getTournament('g', id);
  reportResult(t.bracket, 'b');
  db.saveBracket(id, t.bracket, 'finished');
  assert.equal(db.getTournament('g', id).status, 'finished');
  assert.equal(db.countTournaments('g'), 0);
  db.close();
});

test('ratings accumulate and rank', () => {
  const db = openDb();
  db.saveRating({ guildId: 'g', userId: 'a', displayName: 'A', rating: 1016, won: true });
  db.saveRating({ guildId: 'g', userId: 'b', displayName: 'B', rating: 984, won: false });
  db.saveRating({ guildId: 'g', userId: 'a', displayName: null, rating: 1030, won: true });
  const a = db.getRating('g', 'a');
  assert.equal(a.wins, 2);
  assert.equal(a.display_name, 'A');
  assert.equal(db.rankOf('g', 'a'), 1);
  assert.equal(db.rankOf('g', 'b'), 2);
  assert.equal(db.rankOf('g', 'zzz'), null);
  assert.equal(db.getRating('g', 'new').rating, 1000);
});

test('giveaways end exactly once', () => {
  const db = openDb();
  const id = db.createGiveaway({ guildId: 'g', channelId: 'c', prize: 'Skin', winnerCount: 1, endsAt: 10, hostId: 'h' });
  db.enterGiveaway(id, 'x');
  assert.ok(!db.enterGiveaway(id, 'x'));
  assert.deepEqual(db.dueGiveaways(5), []);
  assert.deepEqual(db.dueGiveaways(10), [id]);
  assert.ok(db.finishGiveaway(id, ['x']));
  assert.ok(!db.finishGiveaway(id, ['y']), 'second finish is a no-op');
  assert.deepEqual(db.getGiveaway(id).winners, ['x']);
  assert.equal(db.countActiveGiveaways('g'), 0);
});

test('premium override', () => {
  const db = openDb();
  assert.equal(db.getOverride('g'), null);
  db.setOverride('g', true, 123);
  assert.deepEqual(db.getOverride('g'), { premium: true, until: 123 });
});
