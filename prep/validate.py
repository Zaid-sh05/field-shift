"""Role 3: check NASA data against the published Maru station months, write data/validation.json.

Temperature: NASA POWER raw vs lapse-rate corrected (5, 6.5, 7 °C/km; 6.5 is the standard atmosphere,
not fitted to these months). Rainfall: NASA POWER and GPM IMERG vs the station.

Usage:
  python prep/validate.py --package PATH/TO/Maru_Jordan_FieldShift/data --project YOUR_GEE_PROJECT
"""
import argparse
import json
from pathlib import Path

import ee
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
STATION = (35.85, 32.55)       # published Maru coordinates (arc-minute precision)
STATION_ELEV_M = 589           # published station elevation
POWER_ELEV_M = 148.86          # elevation of the NASA POWER grid cell
LAPSE_RATES = [5.0, 6.5, 7.0]  # °C per km


def corrected(t, rate, dz_m=STATION_ELEV_M - POWER_ELEV_M):
    return t - rate * dz_m / 1000


def stats(est, ref):
    d = est - ref
    return {"mae": round(d.abs().mean(), 2), "bias": round(d.mean(), 2)}


def imerg_months(months):
    pt = ee.Geometry.Point(*STATION)

    def total(img):
        d = img.date()
        mm = (img.select("precipitation").multiply(24).multiply(d.advance(1, "month").difference(d, "day"))
              .reduceRegion(ee.Reducer.mean(), pt, 11132).get("precipitation"))
        return ee.Feature(None, {"month": d.format("YYYY-MM"), "mm": mm})

    fc = ee.ImageCollection("NASA/GPM_L3/IMERG_MONTHLY_V07").filterDate(
        min(months) + "-01", (pd.Period(max(months), "M") + 1).strftime("%Y-%m-01")).map(total)
    got = fc.getInfo()["features"]
    return pd.Series({f["properties"]["month"]: f["properties"]["mm"] for f in got})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True, help="folder with 09_nasa_local_comparison.csv")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    df = pd.read_csv(Path(args.package) / "09_nasa_local_comparison.csv", encoding="utf-8-sig").set_index("month")
    t_ref, t_nasa = df["published_T_mean_C"], df["NASA_T_mean_C"]
    r_ref, r_power = df["published_rain_mm"], df["NASA_rain_mm"]

    ee.Initialize(project=args.project)
    r_imerg = imerg_months(list(df.index)).reindex(df.index)

    out = {
        "station": {"lon": STATION[0], "lat": STATION[1], "elevation_m": STATION_ELEV_M,
                    "power_cell_elevation_m": POWER_ELEV_M, "months": len(df),
                    "period": f"{df.index.min()} to {df.index.max()}",
                    "source": "published Maru station months (MARU_NARC_JUST_2021)"},
        "temperature_mean_c": {
            "power_raw": stats(t_nasa, t_ref),
            "power_lapse_corrected": {str(r): stats(corrected(t_nasa, r), t_ref) for r in LAPSE_RATES},
            "note": "6.5 °C/km is the standard atmosphere, not fitted to these months. Only mean temperature "
                    "is checked; there is no local Tmax/Tmin, so heat and frost days are unverified.",
        },
        "rain_mm": {
            "station_total": round(r_ref.sum(), 1),
            "power": {**stats(r_power, r_ref), "total": round(r_power.sum(), 1)},
            "imerg": {**stats(r_imerg, r_ref), "total": round(r_imerg.sum(), 1)},
            "note": "18 months only: a check, not a calibration.",
        },
    }
    (DATA / "validation.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    assert corrected(20.0, 6.5, 1000) == 13.5
    main()
