"""Role 3: fill per-field context that was empty.

- fields.geojson `rain_mm`: mean Oct-Jun rain per field from GPM IMERG (data/sat_monthly.csv), complete seasons only.
- soil.json: topsoil (0-30 cm, depth-weighted) clay, sand, organic carbon and pH per field from SoilGrids 250 m.
  SoilGrids is a modelled map, not a lab test: it is checked against the published Maru station profile.

Usage: python prep/field_context.py --project YOUR_GEE_PROJECT
"""
import argparse
import json
from pathlib import Path

import ee
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
DEPTHS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}  # layer thickness in cm, for depth weighting
# property -> (SoilGrids asset, divisor to reach the unit in soil.json)
SOIL = {"clay_pct": ("clay", 10), "sand_pct": ("sand", 10), "soc_gkg": ("soc", 10), "ph": ("phh2o", 10)}
STATION = {"clay_pct": 56.2, "sand_pct": 9.95, "soc_gkg": round(0.76 / 1.724 * 10, 1), "ph": 7.75}  # OM -> SOC (van Bemmelen)


def season_rain(sat):
    r = sat[sat.variable == "precip_imerg_mm"].copy()
    d = pd.to_datetime(r.month)
    r = r[(d.dt.month >= 10) | (d.dt.month <= 6)]
    r["season"] = d.dt.year + (d.dt.month >= 10)
    g = r.groupby(["field_id", "season"]).value
    full = g.sum()[g.count() == 9]  # Oct-Jun = 9 months; skip partial seasons
    return full.groupby("field_id").mean().round(0)


def topsoil(img_name, fc):
    img = ee.Image(f"projects/soilgrids-isric/{img_name}_mean")
    total = sum(DEPTHS.values())
    layers = [img.select(f"{img_name}_{d}_mean").multiply(w / total) for d, w in DEPTHS.items()]
    weighted = layers[0].add(layers[1]).add(layers[2])
    out = weighted.rename("v").reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=250).getInfo()
    return {f["properties"]["field_id"]: f["properties"]["mean"] for f in out["features"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    gj_path = DATA / "fields.geojson"
    gj = json.loads(gj_path.read_text(encoding="utf-8"))
    rain = season_rain(pd.read_csv(DATA / "sat_monthly.csv"))
    for f in gj["features"]:
        f["properties"]["rain_mm"] = float(rain[f["properties"]["field_id"]])
    gj_path.write_text(json.dumps(gj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ee.Initialize(project=args.project)
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]), {"field_id": f["properties"]["field_id"]})
                               for f in gj["features"]])
    vals = {key: topsoil(asset, fc) for key, (asset, _) in SOIL.items()}
    soil = {fid: {key: round(vals[key][fid] / SOIL[key][1], 1) for key in SOIL}
            | {"source": "SoilGrids 250 m, 0-30 cm (modelled, not a field test)"}
            for fid in sorted(vals["clay_pct"])}
    (DATA / "soil.json").write_text(json.dumps(soil, indent=2) + "\n", encoding="utf-8")

    print("rain_mm (Oct-Jun mean, IMERG):", rain.to_dict())
    print("soil:", json.dumps(soil, indent=1))
    print("Maru station profile for comparison:", STATION)


if __name__ == "__main__":
    main()
