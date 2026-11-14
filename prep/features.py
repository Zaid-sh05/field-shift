"""Pure-pandas feature helpers shared by the prep scripts.

Run `python prep/features.py` for the self-check.
"""
import pandas as pd

FALLOW_MAX = 0.25  # seasonal peak NDVI below this = bare/fallow (bright dry soil reads 0.10-0.15)
CROP_MIN = 0.40    # seasonal peak NDVI at or above this = an active crop
# ponytail: fixed NDVI thresholds; calibrate on known fields, k-means on monthly curves if they misfire


def add_anomaly(df: pd.DataFrame, min_years: int = 3) -> pd.DataFrame:
    """Add a z-score `anomaly` per field, variable and calendar month (long-format input)."""
    out = df.copy()
    cal = pd.to_datetime(out["month"]).dt.month
    g = out.groupby([out["field_id"], out["variable"], cal])["value"]
    mean, std, n = g.transform("mean"), g.transform("std"), g.transform("count")
    z = (out["value"] - mean) / std
    out["anomaly"] = z.where((n >= min_years) & (std > 0))
    return out


def classify_seasons(ndvi: pd.DataFrame) -> pd.DataFrame:
    """Label each field-season from monthly NDVI rows (`field_id, month, value`).

    season = harvest year; winter = Nov(prev year)-May, summer = Jun-Sep.
    Seasons with no Feb-Apr observation (the winter peak) are dropped: unfinished or too cloudy to judge.
    NDVI cannot tell wheat from lentil, so both are `winter_crop`.
    """
    d = ndvi.copy()
    date = pd.to_datetime(d["month"])
    m = date.dt.month
    d["season"] = date.dt.year + (m >= 11).astype(int)
    keys = ["field_id", "season"]
    winter = d[(m >= 11) | (m <= 5)].groupby(keys)["value"].max().rename("winter_max")
    summer = d[(m >= 6) & (m <= 9)].groupby(keys)["value"].max().rename("summer_max")
    peak = d[(m >= 2) & (m <= 4)].groupby(keys)["value"].count().rename("n_peak")
    out = pd.concat([winter, summer, peak], axis=1).reset_index()
    out = out[out["n_peak"] > 0].drop(columns="n_peak")

    def label(r):
        if r.summer_max >= CROP_MIN:
            return "irrigated_summer"  # green in the dry season = irrigated
        if r.winter_max >= CROP_MIN:
            return "winter_crop"
        if r.winter_max < FALLOW_MAX:
            return "fallow"
        return "uncertain"

    out["ndvi_max"] = out[["winter_max", "summer_max"]].max(axis=1)
    out["class"] = out.apply(label, axis=1)
    return out


def monthly_profile(ndvi: pd.DataFrame) -> pd.DataFrame:
    """Typical NDVI per field and calendar month, and the share of years the field was bare (NDVI < FALLOW_MAX)."""
    d = ndvi.assign(cal_month=pd.to_datetime(ndvi["month"]).dt.month)
    g = d.groupby(["field_id", "cal_month"])["value"]
    return pd.DataFrame({
        "ndvi_median": g.median().round(3),
        "bare_share": g.apply(lambda v: (v < FALLOW_MAX).mean()).round(2),
        "n_years": g.count(),
    }).reset_index()


def _selftest():
    months = pd.date_range("2021-11-01", "2022-09-01", freq="MS").strftime("%Y-%m")
    peak = {"A": ("2022-03", 0.6), "B": (None, 0), "C": ("2022-07", 0.55), "D": ("2022-02", 0.3)}
    rows = [
        {"field_id": f, "month": mo, "value": v if mo == pm else 0.15}
        for f, (pm, v) in peak.items() for mo in months
    ]
    got = classify_seasons(pd.DataFrame(rows)).set_index("field_id")["class"].to_dict()
    assert got == {"A": "winter_crop", "B": "fallow", "C": "irrigated_summer", "D": "uncertain"}, got
    unfinished = pd.DataFrame({"field_id": "A", "month": ["2025-11", "2025-12"], "value": [0.15, 0.15]})
    assert classify_seasons(unfinished).empty  # Nov-Dec only: season not judged, not "fallow"

    ts = pd.DataFrame({"field_id": "A", "variable": "ndvi",
                       "month": ["2019-03", "2020-03", "2021-03", "2022-03"],
                       "value": [0.5, 0.5, 0.5, 0.1]})
    an = add_anomaly(ts)["anomaly"]
    assert an.iloc[-1] < -1 < 0 < an.iloc[0], an.tolist()
    assert add_anomaly(ts.head(2))["anomaly"].isna().all()  # too few years -> empty
    prof = monthly_profile(pd.DataFrame({"field_id": "A", "month": ["2020-03", "2021-03", "2020-08"],
                                         "value": [0.6, 0.1, 0.12]})).set_index("cal_month")
    assert prof.loc[3, "bare_share"] == 0.5 and prof.loc[8, "bare_share"] == 1.0 and prof.loc[3, "n_years"] == 2
    print("ok")


if __name__ == "__main__":
    _selftest()
