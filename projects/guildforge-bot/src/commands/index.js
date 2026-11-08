import * as tournament from './tournament.js';
import * as ladder from './leaderboard.js';
import * as giveaway from './giveaway.js';
import * as premium from './premium.js';

export const commands = new Map([tournament, ladder, giveaway, premium].map((c) => [c.data.name, c]));
