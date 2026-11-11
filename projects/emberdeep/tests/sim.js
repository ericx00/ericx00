import { playRun } from './bot.js';
import { TUNE } from '../src/logic.js';
if (process.env.HP) TUNE.hp = process.env.HP.split(',').map(Number);
if (process.env.ATK) TUNE.atk = process.env.ATK.split(',').map(Number);
const N = +(process.argv[2] ?? 300), diff = +(process.argv[3] ?? 0);
for (const hero of ['knight', 'mage', 'ranger']) {
  let wins = 0; const reach = [0, 0, 0]; let turns = 0, fights = 0, oh = 0; const deaths = {};
  for (let i = 0; i < N; i++) {
    const s = playRun({ hero, seed: 1000 + i, diff });
    if (s.phase === 'win') wins++;
    else { const k = `${s.act + 1}.${s.step + 1}`; deaths[k] = (deaths[k] ?? 0) + 1; }
    for (let a = 0; a < 3; a++) if (s.act > a || s.phase === 'win') reach[a]++;
    turns += s.stats.turns; oh += s.stats.overheats; fights += s.stats.fights;
  }
  const top = Object.entries(deaths).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k, v]) => `${k}:${v}`).join(' ');
  console.log(`${hero.padEnd(7)} win ${(100 * wins / N).toFixed(1)}%  beat act1 ${(100 * reach[0] / N).toFixed(0)}% act2 ${(100 * reach[1] / N).toFixed(0)}%  turns/fight ${(turns / fights).toFixed(1)}  overheats/run ${(oh / N).toFixed(1)}  deaths at ${top}`);
}
