"""Role 1: export everything the React site needs into web/src/data.json.

The site does no science of its own. Per field and per climate scenario this writes each crop's water numbers
from src/scoring.py; the site only applies the farmer's weights and the rotation rules. `fixtures` holds results
computed here by the Python engine, and web/test/engine.test.mjs checks the JavaScript against them.

Usage: python prep/export_web.py
"""
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import scoring  # noqa: E402
from src.ui_components.evidence import field_summary  # noqa: E402

RAIN_STEPS = list(range(-50, 21, 10))          # % change in rain
WARMING_STEPS = [0, 0.5, 1, 1.5, 2, 2.5, 3]    # °C
OUT = ROOT / "web" / "src" / "data.json"


def crop_stats(field_id, crop, rain_factor, warming):
    seasons = scoring.crop_seasons(field_id, crop, rain_factor, warming)
    wheat = scoring.crop_seasons(field_id, "WHEAT", rain_factor, warming)
    dry = sorted(wheat, key=lambda y: wheat[y]["rain_mm"])[:max(1, math.ceil(len(wheat) * scoring.DRY_SHARE))]
    met = sorted(v["met"] for v in seasons.values())
    mean = lambda key: sum(v[key] for v in seasons.values()) / len(seasons)
    return {"water": round(100 * sum(met) / len(met), 4), "risk": round(100 * sum(seasons[y]["met"] for y in dry) / len(dry), 4),
            "demand_mm": round(mean("demand_mm")), "rain_mm": round(mean("rain_mm")),
            "half_or_more": sum(m >= 0.5 for m in met), "typical": round(100 * met[len(met) // 2]),
            "worst": round(100 * met[0]), "best": round(100 * met[-1])}


def field_block(feature):
    fid = feature["properties"]["field_id"]
    _, crops, profile, rotations, elevation = scoring._tables()
    static = json.loads((ROOT / "data" / "soil.json").read_text(encoding="utf-8")).get(fid, {})
    summary = field_summary(fid)
    wheat = scoring.crop_seasons(fid, "WHEAT")
    grown = [c for c in crops.index if scoring._is_crop(c)]
    import pandas as pd
    slope = pd.read_csv(ROOT / "data" / "field_static.csv").set_index("field_id").slope_deg[fid]
    return {
        "name_ar": feature["properties"]["name_ar"], "name_en": feature["properties"]["name_en"],
        "polygon": feature["geometry"]["coordinates"][0],
        "elevation_m": round(float(elevation[fid])), "slope_deg": round(float(slope), 1),
        "evidence": {**{k: v for k, v in summary.items() if k not in ("ndvi", "soil")},
                     "ndvi": [[m, round(float(v), 3)] for m, v in summary["ndvi"].items()]},
        "soil": {k: static[k] for k in ("clay_pct", "sand_pct", "ph") if k in static},
        "green_months": round(float((1 - profile[profile.field_id == fid].bare_share).sum()), 4),
        "seasons": len(wheat), "dry_seasons": max(1, math.ceil(len(wheat) * scoring.DRY_SHARE)),
        "mean_rain_mm": round(sum(v["rain_mm"] for v in wheat.values()) / len(wheat), 2),
        "rotations": rotations[fid],
        "crop_stats": {f"{r}|{w}": {c: crop_stats(fid, c, 1 + r / 100, w) for c in grown}
                       for r in RAIN_STEPS for w in WARMING_STEPS},
        "replay": {str(y): row for y, row in scoring.season_replay(fid).items()},
        "backtest": scoring.backtest_summary(fid),
        "soil_moisture": scoring.soil_moisture_now(fid),
        "last_season": scoring.next_season(fid, ["WHEAT"], {c: 1 for c in scoring.CRITERIA})["last_season"],
    }


def fixtures(field_ids):
    """Reference answers from the Python engine for the JavaScript test."""
    weight_sets = [{c: 3 for c in scoring.CRITERIA}, {"water": 5, "risk": 5, "soil": 1, "bare": 1, "harvest": 1},
                   {"water": 1, "risk": 2, "soil": 5, "bare": 4, "harvest": 3}]
    scenarios = [(0, 0), (-40, 0), (-50, 3), (20, 1.5)]
    out = []
    for fid, weights, (rain, warming) in itertools.product(field_ids, weight_sets, scenarios):
        result = scoring.evaluate(fid, weights, 1 + rain / 100, warming)
        entry = {"field": fid, "weights": weights, "rain": rain, "warming": warming,
                 "order": [r["id"] for r in result["rotations"]], "totals": {r["id"]: r["total"] for r in result["rotations"]},
                 "close_call": result["close_call"], "low_confidence_top": result["low_confidence_top"], "next": []}
        for history in (["WHEAT", "WHEAT", "WHEAT"], ["WHEAT", "LENTIL"], ["LENTIL", "WHEAT"], ["FALLOW"]):
            nxt = scoring.next_season(fid, history, weights, 1 + rain / 100, warming)
            entry["next"].append({"history": history, "order": [o["crop"] for o in nxt["options"]],
                                  "totals": {o["crop"]: o["total"] for o in nxt["options"]},
                                  "rules": {o["crop"]: o["rules"] for o in nxt["options"]},
                                  "close_call": nxt["close_call"]})
        out.append(entry)
    return out


def main():
    _, crops, _, _, _ = scoring._tables()
    fields = json.loads((ROOT / "data" / "fields.geojson").read_text(encoding="utf-8"))["features"]
    data = {
        "criteria": list(scoring.CRITERIA), "confidence": scoring.CONFIDENCE, "close_margin": scoring.CLOSE_MARGIN,
        "rain_steps": RAIN_STEPS, "warming_steps": WARMING_STEPS,
        "crops": {c: {"legume": bool(crops.loc[c].legume), "grown": scoring._is_crop(c),
                      "calendar": scoring.crop_calendar([c])[0]} for c in crops.index},
        "vigor": scoring.vigor_model(),
        "validation": json.loads((ROOT / "data" / "validation.json").read_text(encoding="utf-8")),
        "fields": {f["properties"]["field_id"]: field_block(f) for f in fields},
        "i18n": json.loads((ROOT / "i18n.json").read_text(encoding="utf-8")),
    }
    data["fixtures"] = fixtures(list(data["fields"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(data['fixtures'])} fixtures)")


if __name__ == "__main__":
    main()
