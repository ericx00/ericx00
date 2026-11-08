// Single-elimination bracket with standard seeding and automatic byes.

export function nextPowerOfTwo(n) {
  let p = 1;
  while (p < n) p *= 2;
  return p;
}

/** Standard seed order, e.g. size 8 -> [1, 8, 4, 5, 2, 7, 3, 6]. Top seeds meet last. */
export function seedOrder(size) {
  let order = [1];
  while (order.length < size) {
    const n = order.length * 2;
    order = order.flatMap((s) => [s, n + 1 - s]);
  }
  return order;
}

/**
 * Create a bracket. `players` is in seed order (best first): [{ id, name }].
 * Returns { size, rounds, matches } where matches is a flat array of
 * { round, slot, p1, p2, winner } (round is 1-based).
 */
export function createBracket(players) {
  if (players.length < 2) throw new Error('A bracket needs at least 2 players.');
  const ids = new Set(players.map((p) => p.id));
  if (ids.size !== players.length) throw new Error('Duplicate players in bracket.');

  const size = nextPowerOfTwo(players.length);
  const rounds = Math.log2(size);
  const order = seedOrder(size);
  const matches = [];

  for (let r = 1; r <= rounds; r++) {
    const count = size / 2 ** r;
    for (let s = 0; s < count; s++) matches.push({ round: r, slot: s, p1: null, p2: null, winner: null });
  }

  const bracket = { size, rounds, players: players.map((p) => ({ id: p.id, name: p.name })), matches };

  for (let s = 0; s < size / 2; s++) {
    const m = getMatch(bracket, 1, s);
    m.p1 = players[order[2 * s] - 1]?.id ?? null;
    m.p2 = players[order[2 * s + 1] - 1]?.id ?? null;
  }
  // Byes: a lone player advances immediately.
  for (let s = 0; s < size / 2; s++) {
    const m = getMatch(bracket, 1, s);
    if (m.p1 && !m.p2) setWinner(bracket, 1, s, m.p1);
    else if (!m.p1 && m.p2) setWinner(bracket, 1, s, m.p2);
  }
  return bracket;
}

export function getMatch(bracket, round, slot) {
  const m = bracket.matches.find((x) => x.round === round && x.slot === slot);
  if (!m) throw new Error(`No match at round ${round}, slot ${slot}.`);
  return m;
}

function setWinner(bracket, round, slot, winnerId) {
  const m = getMatch(bracket, round, slot);
  m.winner = winnerId;
  if (round < bracket.rounds) {
    const next = getMatch(bracket, round + 1, Math.floor(slot / 2));
    if (slot % 2 === 0) next.p1 = winnerId;
    else next.p2 = winnerId;
  }
}

/** Matches that have both players and no result yet. */
export function pendingMatches(bracket) {
  return bracket.matches.filter((m) => m.p1 && m.p2 && !m.winner);
}

/** Find the pending match that a given player is in. */
export function findPendingMatchFor(bracket, playerId) {
  return pendingMatches(bracket).find((m) => m.p1 === playerId || m.p2 === playerId) ?? null;
}

/** Report a result. Returns { match, loser, champion }. Mutates and returns the bracket. */
export function reportResult(bracket, winnerId) {
  const match = findPendingMatchFor(bracket, winnerId);
  if (!match) throw new Error('That player has no match waiting for a result.');
  const loser = match.p1 === winnerId ? match.p2 : match.p1;
  setWinner(bracket, match.round, match.slot, winnerId);
  return { match, loser, champion: championOf(bracket) };
}

export function championOf(bracket) {
  return getMatch(bracket, bracket.rounds, 0).winner;
}

export function roundName(round, rounds) {
  const fromEnd = rounds - round;
  if (fromEnd === 0) return 'Final';
  if (fromEnd === 1) return 'Semifinals';
  if (fromEnd === 2) return 'Quarterfinals';
  return `Round ${round}`;
}

/** Plain-text rendering for a Discord embed. */
export function renderBracket(bracket) {
  const name = (id) => (id ? bracket.players.find((p) => p.id === id)?.name ?? 'Unknown' : 'TBD');
  const lines = [];
  for (let r = 1; r <= bracket.rounds; r++) {
    lines.push(`**${roundName(r, bracket.rounds)}**`);
    for (const m of bracket.matches.filter((x) => x.round === r)) {
      if (r === 1 && (!m.p1 || !m.p2)) continue; // hide byes
      const a = name(m.p1);
      const b = name(m.p2);
      const result = m.winner ? ` → 🏆 ${name(m.winner)}` : '';
      lines.push(`\`M${m.slot + 1}\` ${a} vs ${b}${result}`);
    }
  }
  const champ = championOf(bracket);
  if (champ) lines.push('', `👑 **Champion: ${name(champ)}**`);
  return lines.join('\n');
}
