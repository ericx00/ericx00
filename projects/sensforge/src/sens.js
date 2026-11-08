// Sensitivity math. Everything is based on yaw: degrees turned per mouse count at sensitivity 1.
// Same physical distance per 360° (cm/360) = same muscle memory across games.

export const GAMES = {
  cs2:       { name: 'Counter-Strike 2',  yaw: 0.022,    fov: 106.26, note: 'Source engine; hFOV 106.26 = 90 at 4:3 stretched to 16:9.' },
  valorant:  { name: 'VALORANT',          yaw: 0.07,     fov: 103 },
  apex:      { name: 'Apex Legends',      yaw: 0.022,    fov: 110, note: 'Same scale as CS2. In-game FOV slider is 4:3-based.' },
  ow2:       { name: 'Overwatch 2',       yaw: 0.0066,   fov: 103 },
  cod:       { name: 'Call of Duty (MW-era, default settings)', yaw: 0.0066, fov: 103, note: 'Assumes legacy/default sensitivity settings; ADS multipliers vary.' },
  quake:     { name: 'Quake Champions',   yaw: 0.022,    fov: 103 },
  tf2:       { name: 'Team Fortress 2',   yaw: 0.022,    fov: 106.26 },
  fortnite:  { name: 'Fortnite',          yaw: 0.005555, fov: 80, approx: true, note: 'Approximate: assumes X/Y sensitivity values in %. Verify in-game.' },
};

const CM_PER_INCH = 2.54;

function assertPositive(name, v) {
  if (!(Number.isFinite(v) && v > 0)) throw new RangeError(`${name} must be a positive number`);
}

export function yawOf(game) {
  const g = typeof game === 'string' ? GAMES[game] : game;
  if (!g) throw new Error(`Unknown game: ${game}`);
  return g.yaw;
}

/** Degrees per mouse count. */
export function degreesPerCount(sens, game) {
  return sens * yawOf(game);
}

/** Centimetres of mouse travel for a full 360° turn. */
export function cm360(sens, dpi, game) {
  assertPositive('sens', sens); assertPositive('dpi', dpi);
  return (360 / (sens * yawOf(game) * dpi)) * CM_PER_INCH;
}

export function inches360(sens, dpi, game) {
  return cm360(sens, dpi, game) / CM_PER_INCH;
}

/** Sensitivity that gives `cm` per 360 at `dpi` in `game`. */
export function sensForCm360(cm, dpi, game) {
  assertPositive('cm', cm); assertPositive('dpi', dpi);
  return (360 * CM_PER_INCH) / (cm * yawOf(game) * dpi);
}

/** Convert a sensitivity between games (and optionally DPIs), keeping cm/360 identical. */
export function convert(sens, from, to, dpiFrom = 800, dpiTo = dpiFrom) {
  assertPositive('sens', sens); assertPositive('dpi', dpiFrom); assertPositive('dpi', dpiTo);
  return (sens * yawOf(from) * dpiFrom) / (yawOf(to) * dpiTo);
}

/** eDPI is only comparable within one game. */
export function edpi(sens, dpi) {
  return sens * dpi;
}

/** Round to what a settings menu accepts without drifting more than ~0.1%. */
export function roundSens(s) {
  if (s >= 100) return Math.round(s * 10) / 10;
  if (s >= 10) return Math.round(s * 100) / 100;
  if (s >= 1) return Math.round(s * 1000) / 1000;
  return Math.round(s * 10000) / 10000;
}

/** A conversion table from one setup to every game. */
export function conversionTable(sens, from, dpiFrom, dpiTo = dpiFrom) {
  const cm = cm360(sens, dpiFrom, from);
  return Object.entries(GAMES).map(([id, g]) => ({
    id, name: g.name, approx: !!g.approx, note: g.note,
    sens: roundSens(convert(sens, from, id, dpiFrom, dpiTo)),
    cm360: cm,
  }));
}

/** Rough feel buckets most players use when talking about cm/360. */
export function describeCm360(cm) {
  if (cm < 20) return 'Very high (arm-light, flick-heavy)';
  if (cm < 30) return 'High';
  if (cm < 45) return 'Medium (common for tactical shooters)';
  if (cm < 60) return 'Low';
  return 'Very low (full-arm aiming)';
}
