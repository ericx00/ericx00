export const DEFAULT_RATING = 1000;

export function expectedScore(ratingA, ratingB) {
  return 1 / (1 + 10 ** ((ratingB - ratingA) / 400));
}

/** K-factor: new players move faster so the ladder settles quickly. */
export function kFactor(gamesPlayed) {
  if (gamesPlayed < 10) return 40;
  if (gamesPlayed < 30) return 24;
  return 16;
}

/** Returns new ratings for a decisive game (winner beats loser). */
export function updateRatings(winner, loser) {
  const expW = expectedScore(winner.rating, loser.rating);
  const kW = kFactor(winner.games ?? 0);
  const kL = kFactor(loser.games ?? 0);
  return {
    winner: Math.round((winner.rating + kW * (1 - expW)) * 10) / 10,
    loser: Math.round((loser.rating + kL * (0 - (1 - expW))) * 10) / 10,
  };
}
