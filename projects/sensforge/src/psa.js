// Perfect Sensitivity Approximation: repeated A/B choice that halves the interval each round.
// Start at your current sens; you test 0.5x vs 1.5x, pick the better one, the other end moves
// to the midpoint, and so on. ~7 rounds narrow it to within a few percent.

export function createPsa(startSens, { rounds = 7, low = 0.5, high = 1.5 } = {}) {
  if (!(startSens > 0)) throw new RangeError('startSens must be positive');
  return { start: startSens, lo: startSens * low, hi: startSens * high, round: 0, rounds, history: [] };
}

/** The two sensitivities to compare this round. */
export function candidates(state) {
  return { a: state.lo, b: state.hi };
}

/** Record a choice ('a' = lower, 'b' = higher). Returns a new state. */
export function choose(state, pick) {
  if (isDone(state)) throw new Error('PSA already finished');
  if (pick !== 'a' && pick !== 'b') throw new Error("pick must be 'a' or 'b'");
  const mid = (state.lo + state.hi) / 2;
  const next = { ...state, round: state.round + 1, history: [...state.history, { lo: state.lo, hi: state.hi, pick }] };
  if (pick === 'a') next.hi = mid;
  else next.lo = mid;
  return next;
}

export function isDone(state) {
  return state.round >= state.rounds;
}

export function result(state) {
  return (state.lo + state.hi) / 2;
}
