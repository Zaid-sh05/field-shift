"""Role 3: export per-field satellite features from Google Earth Engine.

Writes (see docs/DATA_CONTRACT.md):
  data/sat_monthly.csv    ndvi (HLS 30 m), sm_rootzone (SMAP L4 9 km), tws_cm (GRACE)
  data/field_history.csv  season classification from NDVI
  data/field_static.csv   elevation and slope (SRTM 30 m)

Usage:
  python prep/gee_export.py --project YOUR_GEE_PROJECT [--start 2015-01] [--end 2025-12]
"""
import argparse
import json
from pathlib import Path

import ee
import pandas as pd

from features import add_anomaly, classify_seasons

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _mask_hls(img):
    fmask = img.select("Fmask")
    cloudy = fmask.bitwiseAnd(0b1110).neq(0)  # bits 1-3: cloud, adjacent cloud, cloud shadow
    return img.updateMask(cloudy.Not())


def _ndvi(nir_band):
    def f(img):
        return (img.normalizedDifference([nir_band, "B4"]).rename("value")
                .copyProperties(img, ["system:time_start"]))
    return f


def hls_ndvi():
    # NIR band differs: B5 on Landsat (L30), B8A on Sentinel-2 (S30). Mixing them up gives wrong NDVI silently.
    l30 = ee.ImageCollection("NASA/HLS/HLSL30/v002").map(_mask_hls).map(_ndvi("B5"))
    s30 = ee.ImageCollection("NASA/HLS/HLSS30/v002").map(_mask_hls).map(_ndvi("B8A"))
    return l30.merge(s30)


# variable -> (collection factory, monthly composite, reduce scale m, native res m, sample at centroid?)
PRODUCTS = {
    "ndvi": (hls_ndvi, "median", 30, 30, False),
    "sm_rootzone": (lambda: ee.ImageCollection("NASA/SMAP/SPL4SMGP/008").select(["sm_rootzone"], ["value"]),
                    "mean", 9000, 9000, True),
    "tws_cm": (lambda: ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/MASCON").select(["lwe_thickness"], ["value"]),
               "mean", 55000, 300000, True),
}


def monthly_composites(coll, start, n_months, how):
    def one(i):
        d = ee.Date(start).advance(i, "month")
        sub = coll.filterDate(d, d.advance(1, "month"))
        img = sub.median() if how == "median" else sub.mean()
        return img.set({"month": d.format("YYYY-MM"), "n": sub.size()})
    ic = ee.ImageCollection(ee.List.sequence(0, n_months - 1).map(one))
    return ic.filter(ee.Filter.gt("n", 0))  # empty months have no bands and would break reduceRegions


def sample(ic, fields, scale):
    def per_image(img):
        fc = img.reduceRegions(collection=fields, reducer=ee.Reducer.mean(), scale=scale)
        return fc.map(lambda f: f.set("month", img.get("month")))
    return ic.map(per_image).flatten()


def to_rows(fc, variable, native_res):
    feats = fc.select(["field_id", "month", "mean"], retainGeometry=False).getInfo()["features"]
    return [{"field_id": f["properties"]["field_id"], "month": f["properties"]["month"],
             "variable": variable, "value": f["properties"].get("mean"), "native_res_m": native_res}
            for f in feats]


def static_terrain(fields):
    dem = ee.Image("USGS/SRTMGL1_003")
    img = dem.rename("elevation_m").addBands(ee.Terrain.slope(dem).rename("slope_deg"))
    fc = img.reduceRegions(collection=fields, reducer=ee.Reducer.mean(), scale=30)
    feats = fc.select(["field_id", "elevation_m", "slope_deg"], retainGeometry=False).getInfo()["features"]
    return pd.DataFrame([f["properties"] for f in feats])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="Google Cloud project registered for Earth Engine")
    ap.add_argument("--fields", default=str(DATA / "fields.geojson"))
    ap.add_argument("--start", default="2015-01")
    ap.add_argument("--end", default="2025-12")
    args = ap.parse_args()

    ee.Initialize(project=args.project)
    gj = json.loads(Path(args.fields).read_text(encoding="utf-8"))
    polys = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"field_id": f["properties"]["field_id"]}) for f in gj["features"]
    ])
    centroids = polys.map(lambda f: f.setGeometry(f.geometry().centroid(1)))
    start = pd.Period(args.start, "M")
    n_months = (pd.Period(args.end, "M") - start).n + 1

    rows = []
    for var, (make, how, scale, native, at_centroid) in PRODUCTS.items():
        print(f"{var}: requesting {n_months} monthly composites ...")
        ic = monthly_composites(make(), str(start.start_time.date()), n_months, how)
        rows += to_rows(sample(ic, centroids if at_centroid else polys, scale), var, native)

    sat = add_anomaly(pd.DataFrame(rows).dropna(subset=["value"]))
    cols = ["field_id", "month", "variable", "value", "anomaly", "native_res_m"]
    sat[cols].sort_values(cols[:3]).to_csv(DATA / "sat_monthly.csv", index=False)

    ndvi = sat[sat["variable"] == "ndvi"][["field_id", "month", "value"]]
    classify_seasons(ndvi).to_csv(DATA / "field_history.csv", index=False)
    static_terrain(polys).to_csv(DATA / "field_static.csv", index=False)
    print(f"wrote {len(sat)} rows to data/sat_monthly.csv, plus field_history.csv and field_static.csv")


if __name__ == "__main__":
    main()
