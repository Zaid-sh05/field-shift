// The JavaScript engine must agree with the Python engine (src/scoring.py) on every exported fixture.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { evaluate, nextSeason, predictVigor } from "../src/engine.js";

const data = JSON.parse(readFileSync(new URL("../src/data.json", import.meta.url), "utf-8"));
const near = (a, b, label) => assert.ok(Math.abs(a - b) <= 0.11, `${label}: ${a} vs ${b}`);

test("rotation ranking matches Python for every field, weight set and scenario", () => {
  assert.ok(data.fixtures.length >= 36);
  for (const f of data.fixtures) {
    const label = `${f.field} rain ${f.rain} warming ${f.warming} ${JSON.stringify(f.weights)}`;
    const result = evaluate(data, f.field, f.weights, f.rain, f.warming);
    assert.deepEqual(result.rotations.map((r) => r.id), f.order, label);
    for (const r of result.rotations) near(r.total, f.totals[r.id], `${label} ${r.id}`);
    assert.equal(result.closeCall, f.close_call, `${label} close call`);
    assert.equal(result.lowConfidenceTop, f.low_confidence_top, `${label} low confidence`);
  }
});

test("next-season advice matches Python for every history", () => {
  for (const f of data.fixtures) {
    for (const expected of f.next) {
      const label = `${f.field} rain ${f.rain} after ${expected.history.join(">")}`;
      const result = nextSeason(data, f.field, expected.history, f.weights, f.rain, f.warming);
      assert.deepEqual(result.options.map((o) => o.crop), expected.order, label);
      for (const o of result.options) {
        near(o.total, expected.totals[o.crop], `${label} ${o.crop}`);
        assert.deepEqual(o.rules, expected.rules[o.crop], `${label} ${o.crop} rules`);
      }
      assert.equal(result.closeCall, expected.close_call, `${label} close call`);
    }
  }
});

test("an unknown season preserves the place of older history", () => {
  const weights = Object.fromEntries(data.criteria.map((c) => [c, 3]));
  for (const oldest of ["WHEAT", "LENTIL"]) {
    const result = nextSeason(data, "maru_1", [oldest, null, "WHEAT"], weights);
    assert.deepEqual(result, nextSeason(data, "maru_1", ["WHEAT"], weights));
  }
  const result = nextSeason(data, "maru_1", ["WHEAT", null, "LENTIL"], weights);
  assert.equal(result.options.at(-1).crop, "LENTIL");
  assert.equal(result.options.at(-1).legumeRepeat, true);
});

test("vigour estimate falls with rain and flags extrapolation", () => {
  const normal = predictVigor(data, "maru_1", 0);
  const drought = predictVigor(data, "maru_1", -50);
  assert.ok(normal.ndvi > drought.ndvi);
  assert.equal(normal.state, "clear");
  assert.equal(normal.extrapolated, false);
  assert.ok(Math.abs(normal.ndvi - 0.65) < 0.01);
});

test("every scenario the sliders can reach has data", () => {
  for (const field of Object.values(data.fields)) {
    for (const rain of data.rain_steps) for (const warming of data.warming_steps) {
      assert.ok(field.crop_stats[`${rain}|${warming}`], `${rain}|${warming}`);
    }
  }
});
