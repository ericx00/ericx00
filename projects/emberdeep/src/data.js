// Emberdeep: all game content. Card text is generated from `fx` (see describe()),
// so what a card says is always what it does.

export const HOT_AT = 5;   // HOT bonuses trigger when Heat >= 5 (before the card is played)
export const COLD_AT = 2;  // COLD bonuses trigger when Heat <= 2
export const BASE_LIMIT = 8;
export const BASE_COOL = 4;
export const BURN_PER_OVER = 2; // HP lost per point of Heat over the limit

export const HEROES = {
  knight: { name: 'Knight', sprite: 'hero_knight', hp: 72, blurb: 'Blocks hard, hits harder when HOT.',
    deck: ['strike', 'strike', 'strike', 'strike', 'guard', 'guard', 'guard', 'guard', 'bash', 'vent'] },
  mage: { name: 'Mage', sprite: 'hero_mage', hp: 62, blurb: 'Burns everything. Lives on the edge of Overheat.',
    deck: ['spark', 'spark', 'spark', 'spark', 'ward', 'ward', 'ward', 'ward', 'fireball', 'meditate'] },
  ranger: { name: 'Ranger', sprite: 'hero_ranger', hp: 64, blurb: 'Stays COLD. Many small, precise hits.',
    deck: ['shot', 'shot', 'shot', 'shot', 'dodge', 'dodge', 'dodge', 'dodge', 'quick_shot', 'mark'] },
};

// rarity: 0 starter, 1 common, 2 uncommon, 3 rare
const c = (id, name, hero, type, heat, rar, art, fx, up) => ({ id, name, hero, type, heat, rar, art, fx, up });
const A = 'attack', S = 'skill', P = 'power';

export const CARD_LIST = [
  // ---------- Knight ----------
  c('strike', 'Strike', 'knight', A, 1, 0, 'sword_steel', [['dmg', 6]], { fx: [['dmg', 9]] }),
  c('guard', 'Guard', 'knight', S, 1, 0, 'shield_sapphire', [['block', 5]], { fx: [['block', 8]] }),
  c('bash', 'Bash', 'knight', A, 2, 0, 'sword_wood', [['dmg', 8], ['vuln', 1]], { fx: [['dmg', 10], ['vuln', 2]] }),
  c('vent', 'Vent', 'knight', S, 0, 0, 'k:action_transform', [['cool', 2], ['draw', 1]], { fx: [['cool', 3], ['draw', 1]] }),
  c('cleave', 'Cleave', 'knight', A, 2, 1, 'sword_ruby', [['aoe', 7]], { fx: [['aoe', 10]] }),
  c('heavy_blow', 'Heavy Blow', 'knight', A, 3, 1, 'sword_gold', [['dmg', 14], ['hot', [['dmg', 8]]]], { fx: [['dmg', 18], ['hot', [['dmg', 10]]]] }),
  c('iron_wall', 'Iron Wall', 'knight', S, 2, 1, 'shield_emerald', [['block', 12]], { fx: [['block', 16]] }),
  c('taunt', 'Taunt', 'knight', S, 1, 1, 'flag', [['weak', 2], ['block', 4]], { fx: [['weak', 3], ['block', 6]] }),
  c('war_cry', 'War Cry', 'knight', S, 1, 1, 'k:intent_debuff', [['aoevuln', 1], ['draw', 1]], { fx: [['aoevuln', 2], ['draw', 1]] }),
  c('tempered_blade', 'Hot Blade', 'knight', A, 1, 1, 'sword_crystal', [['dmg', 5], ['hot', [['dmg', 5]]]], { fx: [['dmg', 7], ['hot', [['dmg', 7]]]] }),
  c('shield_slam', 'Shield Slam', 'knight', A, 1, 2, 'shield_ruby', [['dmgBlock', 1]], { heat: 0 }),
  c('forge_strike', 'Forge Strike', 'knight', A, 2, 2, 'sword_ruby', [['dmg', 10], ['hot', [['str', 1]]]], { fx: [['dmg', 13], ['hot', [['str', 1]]]] }),
  c('bulwark', 'Bulwark', 'knight', S, 1, 2, 'shield_amethyst', [['block', 7], ['cold', [['block', 4]]]], { fx: [['block', 9], ['cold', [['block', 6]]]] }),
  c('quench', 'Quench', 'knight', S, 0, 2, 'potion_sapphire', [['cool', 4], ['block', 4]], { fx: [['cool', 5], ['block', 6]] }),
  c('spiked_armor', 'Spiked Armor', 'knight', P, 2, 2, 'ring_gold_ruby', [['power', 'thorns', 3]], { fx: [['power', 'thorns', 5]] }),
  c('smolder', 'Banked Coals', 'knight', P, 1, 2, 'gem_ruby', [['power', 'forge', 3]], { fx: [['power', 'forge', 5]] }),
  c('second_wind', 'Second Wind', 'knight', S, 1, 2, 'heart', [['heal', 5], ['exhaust']], { fx: [['heal', 8], ['exhaust']] }),
  c('berserk', 'Berserk', 'knight', P, 2, 3, 'skull', [['str', 2]], { fx: [['str', 3]] }),
  c('whirlwind', 'Whirlwind', 'knight', A, 3, 3, 'sword_crystal', [['aoe', 6, 3]], { fx: [['aoe', 8, 3]] }),
  c('last_stand', 'Last Stand', 'knight', S, 2, 3, 'trophy', [['block', 20], ['exhaust']], { fx: [['block', 26], ['exhaust']] }),
  c('molten_edge', 'Molten Edge', 'knight', A, 2, 3, 'sword_gold', [['dmgHeat', 3]], { fx: [['dmgHeat', 4]] }),

  // ---------- Mage ----------
  c('spark', 'Spark', 'mage', A, 1, 0, 'gem_gold', [['dmg', 6], ['hot', [['dmg', 3]]]], { fx: [['dmg', 8], ['hot', [['dmg', 4]]]] }),
  c('ward', 'Ward', 'mage', S, 1, 0, 'shield_amethyst', [['block', 6]], { fx: [['block', 9]] }),
  c('fireball', 'Fireball', 'mage', A, 2, 0, 'gem_ruby', [['aoe', 6], ['aoeburn', 2]], { fx: [['aoe', 8], ['aoeburn', 3]] }),
  c('meditate', 'Meditate', 'mage', S, 0, 0, 'k:status_slow', [['cool', 3]], { fx: [['cool', 4], ['draw', 1]] }),
  c('ignite', 'Ignite', 'mage', S, 1, 1, 'k:status_burn', [['burn', 5]], { fx: [['burn', 7]] }),
  c('flame_wave', 'Flame Wave', 'mage', A, 2, 1, 'potion_gold', [['aoeburn', 3]], { fx: [['aoeburn', 5]] }),
  c('frost_shield', 'Frost Shield', 'mage', S, 1, 1, 'gem_diamond', [['block', 7], ['cool', 1]], { fx: [['block', 9], ['cool', 2]] }),
  c('arcane_bolt', 'Arcane Bolt', 'mage', A, 1, 1, 'gem_amethyst', [['dmg', 4, 2]], { fx: [['dmg', 5, 2]] }),
  c('insight', 'Insight', 'mage', S, 1, 1, 'scroll', [['draw', 2]], { fx: [['draw', 3]] }),
  c('hex', 'Hex', 'mage', S, 1, 1, 'skull', [['weak', 2], ['vuln', 1]], { fx: [['weak', 3], ['vuln', 2]] }),
  c('cinder', 'Cinder', 'mage', S, 0, 1, 'coin_copper', [['burn', 2], ['draw', 1]], { fx: [['burn', 3], ['draw', 1]] }),
  c('combust', 'Combust', 'mage', A, 2, 2, 'bomb', [['dmgBurn', 3]], { fx: [['dmgBurn', 4]] }),
  c('ice_lance', 'Ice Lance', 'mage', A, 1, 2, 'key_crystal', [['dmg', 7], ['cold', [['dmg', 7]]]], { fx: [['dmg', 9], ['cold', [['dmg', 9]]]] }),
  c('arcane_barrier', 'Mana Barrier', 'mage', P, 2, 2, 'ring_silver_sapphire', [['power', 'forge', 4]], { fx: [['power', 'forge', 6]] }),
  c('prism_ward', 'Prism Ward', 'mage', S, 2, 2, 'shield_sapphire', [['block', 10], ['draw', 1]], { fx: [['block', 13], ['draw', 1]] }),
  c('thermal_vent', 'Thermal Vent', 'mage', P, 1, 2, 'potion_diamond', [['power', 'vent', 1]], { fx: [['power', 'vent', 2]] }),
  c('discharge', 'Discharge', 'mage', A, 1, 3, 'star', [['dmgHeat', 2], ['cool', 4]], { fx: [['dmgHeat', 3], ['cool', 4]] }),
  c('inferno', 'Inferno', 'mage', A, 3, 3, 'gem_ruby', [['aoe', 12], ['hot', [['aoeburn', 4]]]], { fx: [['aoe', 16], ['hot', [['aoeburn', 5]]]] }),
  c('pyromania', 'Pyromania', 'mage', P, 1, 3, 'potion_ruby', [['power', 'kindle', 2]], { fx: [['power', 'kindle', 3]] }),
  c('meteor', 'Meteor', 'mage', A, 4, 3, 'gem_gold', [['dmg', 28]], { fx: [['dmg', 36]] }),
  c('phoenix', 'Phoenix Ash', 'mage', S, 2, 3, 'heart', [['heal', 8], ['aoeburn', 2], ['exhaust']], { fx: [['heal', 12], ['aoeburn', 3], ['exhaust']] }),

  // ---------- Ranger ----------
  c('shot', 'Shot', 'ranger', A, 1, 0, 'key_silver', [['dmg', 6]], { fx: [['dmg', 9]] }),
  c('dodge', 'Dodge', 'ranger', S, 1, 0, 'shield_emerald', [['block', 5]], { fx: [['block', 8]] }),
  c('quick_shot', 'Quick Shot', 'ranger', A, 0, 0, 'key_copper', [['dmg', 3], ['cold', [['draw', 1]]]], { fx: [['dmg', 5], ['cold', [['draw', 1]]]] }),
  c('mark', 'Mark', 'ranger', S, 1, 0, 'k:status_mark', [['vuln', 2]], { fx: [['vuln', 3]] }),
  c('volley', 'Volley', 'ranger', A, 1, 1, 'key_gold', [['dmg', 3, 3]], { fx: [['dmg', 4, 3]] }),
  c('snipe', 'Snipe', 'ranger', A, 2, 1, 'key_crystal', [['dmg', 9], ['cold', [['dmg', 9]]]], { fx: [['dmg', 12], ['cold', [['dmg', 10]]]] }),
  c('roll', 'Roll', 'ranger', S, 1, 1, 'k:status_haste', [['block', 6], ['draw', 1]], { fx: [['block', 8], ['draw', 1]] }),
  c('fire_arrow', 'Fire Arrow', 'ranger', A, 1, 1, 'potion_ruby', [['dmg', 4], ['burn', 3]], { fx: [['dmg', 5], ['burn', 5]] }),
  c('cripple', 'Cripple', 'ranger', A, 1, 1, 'sword_wood', [['dmg', 5], ['weak', 2]], { fx: [['dmg', 7], ['weak', 2]] }),
  c('sidestep', 'Sidestep', 'ranger', S, 0, 1, 'k:status_dodge', [['block', 2], ['draw', 1]], { fx: [['block', 4], ['draw', 1]] }),
  c('steady_aim', 'Steady Aim', 'ranger', S, 1, 2, 'k:status_slow', [['str', 1], ['cold', [['draw', 2]]]], { fx: [['str', 2], ['cold', [['draw', 2]]]] }),
  c('arrow_rain', 'Arrow Rain', 'ranger', A, 2, 2, 'gem_emerald', [['aoe', 4, 2]], { fx: [['aoe', 5, 2]] }),
  c('ambush', 'Ambush', 'ranger', A, 0, 2, 'sword_steel', [['cold', [['vuln', 2]]], ['dmg', 6], ['exhaust']], { fx: [['cold', [['vuln', 2]]], ['dmg', 9], ['exhaust']] }),
  c('smoke_bomb', 'Smoke Bomb', 'ranger', S, 1, 2, 'bomb', [['aoeweak', 2], ['block', 4]], { fx: [['aoeweak', 2], ['block', 7]] }),
  c('caltrops', 'Caltrops', 'ranger', P, 1, 2, 'ring_gold_emerald', [['power', 'thorns', 2]], { fx: [['power', 'thorns', 3]] }),
  c('backstab', 'Backstab', 'ranger', A, 1, 2, 'sword_ruby', [['dmg', 6], ['ifVuln', [['dmg', 6]]]], { fx: [['dmg', 8], ['ifVuln', [['dmg', 8]]]] }),
  c('flurry', 'Flurry', 'ranger', A, 2, 3, 'sword_crystal', [['dmg', 2, 6]], { fx: [['dmg', 3, 6]] }),
  c('evasion', 'Evasion', 'ranger', P, 2, 3, 'ring_silver_sapphire', [['power', 'forge', 4]], { fx: [['power', 'forge', 6]] }),
  c('cool_head', 'Cool Head', 'ranger', P, 1, 3, 'potion_sapphire', [['power', 'vent', 2]], { fx: [['power', 'vent', 3]] }),
  c('deadeye', 'Deadeye', 'ranger', A, 3, 3, 'star', [['cold', [['vuln', 2]]], ['dmg', 20]], { fx: [['cold', [['vuln', 2]]], ['dmg', 26]] }),

  // ---------- Any hero ----------
  c('bandage', 'Bandage', 'any', S, 1, 1, 'potion_emerald', [['heal', 4], ['exhaust']], { fx: [['heal', 6], ['exhaust']] }),
  c('iron_skin', 'Iron Skin', 'any', S, 2, 1, 'shield_ruby', [['block', 10]], { fx: [['block', 13]] }),
  c('throwing_axe', 'Throwing Axe', 'any', A, 1, 1, 'sword_wood', [['dmg', 8]], { fx: [['dmg', 11]] }),
  c('deep_breath', 'Deep Breath', 'any', S, 0, 1, 'potion_diamond', [['cool', 3]], { fx: [['cool', 4]] }),
  c('fire_bomb', 'Fire Bomb', 'any', A, 2, 2, 'bomb', [['aoe', 9], ['exhaust']], { fx: [['aoe', 12], ['exhaust']] }),
  c('sharpen', 'Sharpen', 'any', P, 1, 2, 'gem_sapphire', [['str', 1]], { fx: [['str', 2]] }),
  c('scout', 'Scout', 'any', S, 1, 2, 'map', [['draw', 2], ['cool', 1]], { fx: [['draw', 3], ['cool', 1]] }),
  c('adrenaline', 'Adrenaline', 'any', S, 0, 3, 'apple', [['draw', 2], ['exhaust']], { fx: [['draw', 3], ['exhaust']] }),
];
export const CARDS = Object.fromEntries(CARD_LIST.map((x) => [x.id, x]));

/** Resolve a deck entry {id, up} to its effective stats. */
export function cardOf(entry) {
  const base = CARDS[entry.id];
  if (!entry.up) return base;
  return { ...base, ...base.up, name: base.name + '+', up: null, upgraded: true };
}

const fxText = (f) => {
  const [op, a, b] = f;
  switch (op) {
    case 'dmg': return b > 1 ? `Deal ${a} damage ${b} times.` : `Deal ${a} damage.`;
    case 'aoe': return b > 1 ? `Deal ${a} damage to ALL enemies ${b} times.` : `Deal ${a} damage to ALL enemies.`;
    case 'block': return `Gain ${a} Block.`;
    case 'draw': return `Draw ${a}.`;
    case 'cool': return `Cool ${a}.`;
    case 'vuln': return `Apply ${a} Vulnerable.`;
    case 'weak': return `Apply ${a} Weak.`;
    case 'burn': return `Apply ${a} Burn.`;
    case 'aoeburn': return `Apply ${a} Burn to ALL.`;
    case 'aoevuln': return `Apply ${a} Vulnerable to ALL.`;
    case 'aoeweak': return `Apply ${a} Weak to ALL.`;
    case 'str': return `Gain ${a} Strength.`;
    case 'heal': return `Heal ${a}.`;
    case 'exhaust': return 'Exhaust.';
    case 'dmgHeat': return `Deal ${a}x your Heat as damage.`;
    case 'dmgBlock': return 'Deal damage equal to your Block.';
    case 'dmgBurn': return `Deal ${a}x the target's Burn as damage.`;
    case 'hot': return 'HOT: ' + a.map(fxText).join(' ');
    case 'cold': return 'COLD: ' + a.map(fxText).join(' ');
    case 'ifVuln': return 'If target is Vulnerable: ' + a.map(fxText).join(' ');
    case 'power':
      if (a === 'thorns') return `Attackers take ${b} damage.`;
      if (a === 'forge') return `Gain ${b} Block at the start of each turn.`;
      if (a === 'vent') return `Cool ${b} more each turn.`;
      if (a === 'kindle') return `Each turn, apply ${b} Burn to ALL enemies.`;
  }
  return '';
};
export const describe = (card) => card.fx.map(fxText).join(' ');
/** Does the card need an enemy target? */
export const needsTarget = (card) => {
  const single = new Set(['dmg', 'vuln', 'weak', 'burn', 'dmgHeat', 'dmgBlock', 'dmgBurn', 'ifVuln']);
  const walk = (fx) => fx.some((f) => single.has(f[0]) || ((f[0] === 'hot' || f[0] === 'cold') && walk(f[1])));
  return walk(card.fx);
};

export const KEYWORDS = {
  Heat: `Every card adds its Heat cost. You cool ${BASE_COOL} at the start of your turn. Heat stays between turns.`,
  Overheat: `Going past your Heat limit burns you for ${BURN_PER_OVER} HP per point over.`,
  HOT: `Bonus if your Heat is ${HOT_AT} or more when you play the card.`,
  COLD: `Bonus if your Heat is ${COLD_AT} or less when you play the card.`,
  Block: 'Prevents damage until your next turn.',
  Vulnerable: 'Takes 50% more attack damage. Drops by 1 each turn.',
  Weak: 'Deals 25% less attack damage. Drops by 1 each turn.',
  Burn: 'Takes that much damage at the end of its turn, then drops by 1.',
  Strength: 'Each attack hit deals that much more damage.',
  Exhaust: 'Removed from your deck until the fight ends.',
  Stoke: 'Enemy move: adds Heat to you (never past your limit).',
};

// ---------- Relics ----------
export const RELIC_LIST = [
  { id: 'whetstone', name: 'Whetstone', art: 'sword_steel', text: 'Start each fight with 1 Strength.' },
  { id: 'buckler', name: 'Iron Buckler', art: 'shield_sapphire', text: 'Start each fight with 6 Block.' },
  { id: 'heat_sink', name: 'Heat Sink', art: 'gem_diamond', text: 'Heat limit +2.' },
  { id: 'bellows', name: 'Bellows', art: 'bag', text: 'Cool 1 more each turn.' },
  { id: 'lucky_coin', name: 'Lucky Coin', art: 'coin_gold', text: 'Gain 25% more gold.' },
  { id: 'heartstone', name: 'Heartstone', art: 'heart', text: 'Max HP +10.' },
  { id: 'moss', name: 'Healing Moss', art: 'apple', text: 'Heal 5 after each fight.' },
  { id: 'ember_charm', name: 'Ember Charm', art: 'gem_ruby', text: 'Enemies start each fight with 3 Burn.' },
  { id: 'scroll_case', name: 'Scroll Case', art: 'scroll', text: 'Draw 2 more cards on your first turn.' },
  { id: 'cold_iron', name: 'Cold Iron', art: 'key_silver', text: 'The first card you play each turn adds no Heat.' },
  { id: 'thorn_ring', name: 'Thorn Ring', art: 'ring_gold_emerald', text: 'Attackers take 2 damage.' },
  { id: 'safety_valve', name: 'Safety Valve', art: 'key_crystal', text: 'Your first Overheat each fight does no damage.' },
  { id: 'tempering_oil', name: 'Tempering Oil', art: 'potion_gold', text: 'HOT triggers at 4 Heat instead of 5.' },
  { id: 'frost_flask', name: 'Frost Flask', art: 'potion_sapphire', text: 'COLD triggers at 3 Heat instead of 2.' },
  { id: 'anvil', name: 'Pocket Anvil', art: 'trophy', text: 'On pickup: upgrade 2 random cards.' },
  { id: 'rations', name: 'Travel Rations', art: 'bread', text: 'Resting heals 10 more.' },
  { id: 'powder_keg', name: 'Powder Keg', art: 'bomb', text: 'Deal 8 damage to ALL enemies at the start of each fight.' },
  { id: 'silver_ring', name: 'Silver Ring', art: 'ring_silver_sapphire', text: 'Gain 1 Block whenever you play a card.' },
];
export const RELICS = Object.fromEntries(RELIC_LIST.map((r) => [r.id, r]));

// ---------- Enemies ----------
// Moves cycle in order. a=attack, h=hits, b=block, s=strength, w=weak, v=vulnerable, heat=stoke.
const e = (id, name, hp, moves, scale = 2) => ({ id, name, hp, moves, scale });
export const ENEMIES = Object.fromEntries([
  // Act 1: Greenwood
  e('slime_green', 'Green Slime', [13, 17], [{ a: 5 }, { a: 5 }, { b: 4, a: 3 }]),
  e('slime_blue', 'Blue Slime', [16, 20], [{ b: 5 }, { a: 7 }]),
  e('mushroom_red', 'Red Cap', [20, 24], [{ w: 1, a: 3 }, { a: 6 }, { a: 6 }]),
  e('mushroom_blue', 'Blue Cap', [20, 24], [{ v: 1, a: 3 }, { a: 7 }, { b: 6 }]),
  e('goblin_forest', 'Forest Goblin', [18, 22], [{ a: 3, h: 2 }, { a: 7 }, { s: 1, b: 3 }]),
  e('bat_brown', 'Brown Bat', [10, 13], [{ a: 4 }, { a: 2, h: 2 }]),
  e('golem_moss', 'Moss Golem', [58, 64], [{ b: 8, s: 1 }, { a: 10 }, { a: 5, h: 2 }, { a: 14 }], 3),
  e('mushroom_gold', 'Sporelord', [110, 110], [{ a: 8, w: 1 }, { b: 10, s: 2 }, { a: 5, h: 3 }, { v: 2, a: 6 }, { a: 16 }], 4),
  // Act 2: The Undercrypt
  e('skeleton_bone', 'Skeleton', [26, 30], [{ a: 8 }, { a: 8 }, { b: 6, a: 5 }]),
  e('skeleton_cursed', 'Cursed Bones', [28, 32], [{ a: 6, w: 1 }, { a: 10 }, { s: 2 }]),
  e('bat_purple', 'Crypt Bat', [16, 19], [{ a: 5, h: 2 }, { a: 7 }]),
  e('ghost_pale', 'Pale Ghost', [22, 26], [{ v: 1 }, { a: 9 }, { a: 9 }]),
  e('ghost_spectral', 'Spectre', [24, 28], [{ w: 2 }, { a: 6, h: 2 }, { b: 8 }]),
  e('eye_crimson', 'Crimson Eye', [30, 34], [{ a: 11 }, { v: 2, a: 4 }, { a: 7, h: 2 }]),
  e('eye_venom', 'Venom Eye', [28, 32], [{ heat: 2, a: 5 }, { a: 10 }, { b: 7, a: 4 }]),
  e('goblin_cave', 'Cave Goblin', [24, 28], [{ a: 4, h: 3 }, { s: 1, b: 5 }, { a: 9 }]),
  e('golem_stone', 'Stone Golem', [95, 105], [{ b: 12 }, { a: 16 }, { a: 7, h: 2, v: 1 }, { s: 2, b: 6 }, { a: 20 }], 3),
  e('eye_void', 'The Watcher', [190, 190], [{ v: 2, w: 2 }, { a: 9, h: 2 }, { heat: 3, a: 8 }, { b: 14, s: 2 }, { a: 24 }, { a: 5, h: 4 }], 4),
  // Act 3: Frostforge Peak
  e('slime_magma', 'Magma Slime', [34, 38], [{ heat: 2, a: 6 }, { a: 12 }, { a: 12 }]),
  e('goblin_fire', 'Fire Goblin', [32, 36], [{ a: 5, h: 3 }, { a: 11, heat: 1 }, { s: 2, b: 6 }]),
  e('ghost_ember', 'Ember Wraith', [30, 34], [{ heat: 3 }, { a: 13 }, { w: 2, a: 7 }]),
  e('bat_crimson', 'Blood Bat', [20, 24], [{ a: 6, h: 2 }, { a: 9, v: 1 }]),
  e('skeleton_gilded', 'Gilded Knight', [130, 140], [{ b: 10, s: 1 }, { a: 12, h: 2 }, { a: 18, v: 1 }, { a: 9, h: 3 }, { b: 16 }], 3),
  e('golem_lava', 'The Forge Heart', [280, 280], [{ heat: 3, s: 1 }, { a: 14, h: 2 }, { b: 18, a: 10 }, { a: 30 }, { heat: 2, a: 8, h: 3 }, { w: 2, v: 2, b: 10 }], 4),
].map((x) => [x.id, x]));

export const ACTS = [
  { name: 'Greenwood', biome: 'grassland',
    easy: [['slime_green', 'slime_green'], ['bat_brown', 'slime_blue'], ['mushroom_red'], ['goblin_forest']],
    normal: [['slime_green', 'slime_blue', 'bat_brown'], ['mushroom_red', 'mushroom_blue'], ['goblin_forest', 'goblin_forest'],
      ['goblin_forest', 'bat_brown', 'bat_brown'], ['mushroom_blue', 'slime_green', 'slime_green'], ['slime_blue', 'mushroom_red']],
    elite: [['golem_moss']], boss: ['mushroom_gold'] },
  { name: 'The Undercrypt', biome: 'dungeon',
    easy: [['skeleton_bone', 'bat_purple'], ['ghost_pale', 'ghost_pale'], ['goblin_cave', 'bat_purple']],
    normal: [['skeleton_bone', 'skeleton_cursed'], ['eye_crimson', 'bat_purple'], ['ghost_spectral', 'ghost_pale', 'bat_purple'],
      ['eye_venom', 'goblin_cave'], ['skeleton_cursed', 'ghost_spectral'], ['goblin_cave', 'goblin_cave', 'bat_purple'], ['eye_crimson', 'eye_venom']],
    elite: [['golem_stone']], boss: ['eye_void'] },
  { name: 'Frostforge Peak', biome: 'snow',
    easy: [['slime_magma', 'bat_crimson'], ['goblin_fire', 'bat_crimson'], ['ghost_ember', 'slime_magma']],
    normal: [['slime_magma', 'slime_magma'], ['goblin_fire', 'ghost_ember'], ['bat_crimson', 'bat_crimson', 'ghost_ember'],
      ['goblin_fire', 'goblin_fire'], ['slime_magma', 'goblin_fire', 'bat_crimson'], ['ghost_ember', 'ghost_ember']],
    elite: [['skeleton_gilded']], boss: ['golem_lava'] },
];

// What can appear at each step of an act (the last step is always the boss).
export const STEP_POOLS = [
  ['easy', 'easy'],
  ['easy', 'event'],
  ['fight', 'shop', 'event'],
  ['elite', 'fight', 'rest'],
  ['fight', 'event', 'fight'],
  ['elite', 'shop', 'fight'],
  ['rest', 'shop'],
  ['boss'],
];

export const EVENTS = [
  { id: 'anvil', title: 'Abandoned Anvil', text: 'A cold anvil sits in the path. The hammer is still there.',
    options: [{ label: 'Upgrade a random card', fx: ['upgrade', 1] }, { label: 'Pry out the gold inlay (+40 gold)', fx: ['gold', 40] }] },
  { id: 'spring', title: 'Hot Spring', text: 'Steam curls off clear water. It smells faintly of iron.',
    options: [{ label: 'Bathe (heal 20)', fx: ['heal', 20] }, { label: 'Drink deep (max HP +6)', fx: ['maxhp', 6] }] },
  { id: 'chest', title: 'Scorched Chest', text: 'The lock is glowing red. Something valuable is inside.',
    options: [{ label: 'Force it open (relic, lose 8 HP)', fx: ['relicHurt', 8] }, { label: 'Leave it', fx: ['none'] }] },
  { id: 'smith', title: 'Wandering Smith', text: '"Too much dead weight in that pack. I can melt something down."',
    options: [{ label: 'Remove your weakest starter card', fx: ['remove'] }, { label: 'Buy a tip instead (+25 gold)', fx: ['gold', 25] }] },
];
