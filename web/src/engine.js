// Mirrors src/scoring.py: applies the farmer's weights and the rotation rules to numbers the Python engine
// exported (data.json). All physics (rain, crop water demand, satellite greenness) is computed in Python.
// test/engine.test.mjs checks every function here against Python results stored in data.fixtures.

const round1 = (x) => Math.round(x * 10) / 10;

export const scenarioKey = (rain, warming) => `${rain}|${warming}`;

export function rotationCriteria(data, field, sequence, rain = 0, warming = 0) {
  const stats = field.crop_stats[scenarioKey(rain, warming)];
  const grown = sequence.filter((c) => data.crops[c].grown);
  // fallow seasons have no crop to fail, so they count as fully met
  const meanOf = (key) => sequence.reduce((sum, c) => sum + (data.crops[c].grown ? stats[c][key] : 100), 0) / sequence.length;
  const legume = grown.some((c) => data.crops[c].legume);
  const noRepeat = !sequence.some((c, i) => c === sequence[(i + 1) % sequence.length] && data.crops[c].grown);
  const greenMonths = sequence.reduce((sum, c) => sum + (data.crops[c].grown ? field.green_months : 0), 0) / sequence.length;
  const crops = [...new Set(grown)].sort();
  return {
    water: { score: meanOf("water"), crops: crops.map((c) => ({ crop: c, demand: stats[c].demand_mm, rain: stats[c].rain_mm })) },
    risk: { score: meanOf("risk"), dry: field.dry_seasons, seasons: field.seasons },
    soil: { score: 50 * (legume + noRepeat), legume, noRepeat },
    bare: { score: (100 * greenMonths) / 12, greenMonths: round1(greenMonths) },
    income: { score: (100 * grown.length) / sequence.length, harvests: grown.length, of: sequence.length },
  };
}

function totalsFor(data, perRotation, weights) {
  const weightSum = data.criteria.reduce((s, c) => s + weights[c], 0);
  return Object.fromEntries(Object.entries(perRotation).map(([id, crit]) =>
    [id, data.criteria.reduce((s, c) => s + weights[c] * crit[c].score, 0) / weightSum]));
}

const firstMax = (totals) => Object.keys(totals).reduce((best, id) => (totals[id] > totals[best] ? id : best));

export function evaluate(data, fieldId, weights, rain = 0, warming = 0) {
  const field = data.fields[fieldId];
  const perRotation = Object.fromEntries(field.rotations.map((r) => [r.id, rotationCriteria(data, field, r.sequence, rain, warming)]));
  const totals = totalsFor(data, perRotation, weights);
  const order = Object.keys(totals).sort((a, b) => totals[b] - totals[a]);
  let close = order.length > 1 && totals[order[0]] - totals[order[1]] < data.close_margin;
  for (const c of data.criteria) {
    for (const factor of [0.9, 1.1]) {
      // does nudging one weight by 10% change which rotation comes first?
      close = close || firstMax(totalsFor(data, perRotation, { ...weights, [c]: weights[c] * factor })) !== order[0];
    }
  }
  const heaviest = Math.max(...data.criteria.map((c) => weights[c]));
  return {
    rotations: order.map((id) => ({ id, total: round1(totals[id]), criteria: perRotation[id], rotation: field.rotations.find((r) => r.id === id) })),
    closeCall: close,
    lowConfidenceTop: data.criteria.some((c) => weights[c] === heaviest && data.confidence[c] === "low"),
  };
}

export function nextSeason(data, fieldId, history, weights, rain = 0, warming = 0) {
  const field = data.fields[fieldId];
  const stats = field.crop_stats[scenarioKey(rain, warming)];
  const weightSum = data.criteria.reduce((s, c) => s + weights[c], 0);
  const last = history[history.length - 1];
  const options = Object.keys(data.crops).map((crop) => {
    const { grown, legume } = data.crops[crop];
    const window = [...history.slice(-2), crop];
    const rules = {
      varied: crop !== last,
      legume: window.some((c) => data.crops[c].legume),
      no_third: !(grown && history.length >= 2 && last === crop && history[history.length - 2] === crop),
    };
    const criteria = {
      water: grown ? stats[crop].water : 100,
      risk: grown ? stats[crop].risk : 100,
      soil: (100 * Object.values(rules).filter(Boolean).length) / 3,
      bare: grown ? (100 * field.green_months) / 12 : 0,
      income: grown ? 100 : 0,
    };
    const total = round1(data.criteria.reduce((s, c) => s + weights[c] * criteria[c], 0) / weightSum);
    // a legume straight after the same legume builds up soil-borne disease: shown, but never ranked first
    return { crop, total, rules, criteria, legumeRepeat: Boolean(grown && legume && last === crop), outlook: grown ? stats[crop] : null };
  });
  options.sort((a, b) => a.legumeRepeat - b.legumeRepeat || b.total - a.total);
  return { options, closeCall: options[0].total - options[1].total < data.close_margin };
}

export function predictVigor(data, fieldId, rain = 0) {
  const { intercept, slope_per_mm: slope, error, rain_min: lo, rain_max: hi } = data.vigor;
  const mm = (1 + rain / 100) * data.fields[fieldId].mean_rain_mm;
  const ndvi = Math.min(1, Math.max(0, intercept + slope * mm));
  return { rain: Math.round(mm), ndvi, error, state: ndvi >= 0.4 ? "clear" : ndvi >= 0.25 ? "weak" : "failed", extrapolated: mm < lo || mm > hi };
}
