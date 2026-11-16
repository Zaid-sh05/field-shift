"""Landsat 5/7/8/9 monthly NDVI per field, 1999-2025, to test the vigour model on 26 seasons instead of 11.

HLS starts in 2015. Landsat Collection 2 surface reflectance goes back decades with the same 30 m pixels;
on the 2015-2025 overlap its seasonal peak tracks the HLS peak closely (r 0.96, checked in src/scoring.py).

    python prep/landsat_long.py --project YOUR_GEE_PROJECT   ->  data/landsat_ndvi_monthly.csv
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

import ee
import pandas as pd

from gee_export import DATA, monthly_composites, sample, to_rows


def landsat(region, collection, nir, red):
    def ndvi(img):
        clear = img.select("QA_PIXEL").bitwiseAnd(0b11111).eq(0)  # fill, dilated cloud, cirrus, cloud, shadow
        sr = img.select([nir, red]).multiply(0.0000275).add(-0.2)
        return sr.normalizedDifference([nir, red]).rename("value").updateMask(clear).copyProperties(img, ["system:time_start"])
    return ee.ImageCollection(collection).filterBounds(region).map(ndvi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    gj = json.loads((DATA / "fields.geojson").read_text(encoding="utf-8"))
    polys = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]), {"field_id": f["properties"]["field_id"]})
                                  for f in gj["features"]])
    region = polys.geometry()
    # NIR/red bands differ: B4/B3 on Landsat 5 and 7, B5/B4 on Landsat 8 and 9
    coll = (landsat(region, "LANDSAT/LT05/C02/T1_L2", "SR_B4", "SR_B3")
            .merge(landsat(region, "LANDSAT/LE07/C02/T1_L2", "SR_B4", "SR_B3"))
            .merge(landsat(region, "LANDSAT/LC08/C02/T1_L2", "SR_B5", "SR_B4"))
            .merge(landsat(region, "LANDSAT/LC09/C02/T1_L2", "SR_B5", "SR_B4")))

    def year(y):  # one year per request stays under the Earth Engine limits
        start = f"{y}-01-01"
        ic = monthly_composites(coll.filterDate(start, ee.Date(start).advance(12, "month")), start, 12, "median")
        return to_rows(sample(ic, polys, 30), "ndvi", 30)

    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = [r for chunk in pool.map(year, range(1999, 2026)) for r in chunk]
    out = pd.DataFrame(rows).dropna(subset=["value"]).rename(columns={"value": "ndvi"})
    out["ndvi"] = out.ndvi.round(4)
    out[["field_id", "month", "ndvi"]].sort_values(["field_id", "month"]).to_csv(DATA / "landsat_ndvi_monthly.csv", index=False)
    print(f"wrote {len(out)} rows to data/landsat_ndvi_monthly.csv")


if __name__ == "__main__":
    main()
