"""Role 3: slide figures from the data files -> docs/figures/*.png

Usage: python prep/figures.py        (inputs default to data/source/)
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "docs" / "figures"
COLORS = {"maru_1": "#2a9d8f", "maru_2": "#e9c46a", "maru_3": "#e76f51"}
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False})


def ndvi_history():
    s = pd.read_csv(DATA / "sat_monthly.csv")
    s = s[s.variable == "ndvi"].assign(date=lambda d: pd.to_datetime(d.month))
    fig, ax = plt.subplots(figsize=(12, 4.5))
    for y in range(2015, 2026):  # shade the Feb-Apr winter peak window
        ax.axvspan(pd.Timestamp(f"{y}-02-01"), pd.Timestamp(f"{y}-05-01"), color="#2a9d8f", alpha=0.07, lw=0)
    for fid, g in s.groupby("field_id"):
        ax.plot(g.date, g.value, color=COLORS[fid], lw=1.8, label=fid.replace("maru_", "Maru field "))
    ax.axhline(0.40, color="#264653", ls="--", lw=1)
    ax.axhline(0.25, color="#8d6e63", ls=":", lw=1)
    ax.text(s.date.min(), 0.415, "crop (NDVI ≥ 0.40)", color="#264653", fontsize=10)
    ax.text(s.date.min(), 0.20, "bare soil (< 0.25)", color="#8d6e63", fontsize=10)
    ax.set_ylabel("NDVI (HLS, 30 m, monthly median)")
    ax.set_title("33 field-seasons, 2015-2025: 31 clear winter crops, 2 borderline, 0 fallow", loc="left")
    ax.legend(frameon=False, ncol=3, loc="upper right")
    return fig


def temperature_check(package):
    df = pd.read_csv(Path(package) / "09_nasa_local_comparison.csv", encoding="utf-8-sig")
    v = json.loads((DATA / "validation.json").read_text(encoding="utf-8"))
    st = v["station"]
    dz = st["elevation_m"] - st["power_cell_elevation_m"]
    x = range(len(df))
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(x, df.published_T_mean_C, "o-", color="#264653", lw=2.2, label="Maru station (ground)")
    ax.plot(x, df.NASA_T_mean_C, "o--", color="#e76f51", lw=1.5,
            label=f"NASA POWER raw (error {v['temperature_mean_c']['power_raw']['mae']} °C)")
    ax.plot(x, df.NASA_T_mean_C - 6.5 * dz / 1000, "o-", color="#2a9d8f", lw=1.5,
            label=f"NASA POWER, elevation-corrected (error {v['temperature_mean_c']['power_lapse_corrected']['6.5']['mae']} °C)")
    ax.set_xticks(list(x)[::2], df.month[::2], rotation=45)
    ax.set_ylabel("Monthly mean temperature (°C)")
    ax.set_title(f"NASA's grid cell sits {dz:.0f} m lower than Maru. Correcting for it cuts the error by two thirds",
                 loc="left")
    ax.legend(frameon=False)
    return fig


def rain_check():
    r = json.loads((DATA / "validation.json").read_text(encoding="utf-8"))["rain_mm"]
    names = ["Maru station", "NASA POWER", "GPM IMERG"]
    vals = [r["station_total"], r["power"]["total"], r["imerg"]["total"]]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(names, vals, color=["#264653", "#e76f51", "#f4a261"])
    ax.bar_label(bars, fmt="%.0f mm")
    ax.set_ylabel("Rain over the same 18 months (mm)")
    ax.set_title("Both satellite products miss ~22% of Maru's rain\n-> rainfall shown with medium confidence",
                 loc="left")
    return fig


def drought():
    sat = pd.read_csv(DATA / "sat_monthly.csv")
    rain = sat[sat.variable == "precip_imerg_mm"].copy()
    when = pd.to_datetime(rain.month)
    rain = rain[(when.dt.month >= 10) | (when.dt.month <= 6)]
    rain["season"] = when.dt.year + (when.dt.month >= 10)
    g = rain.groupby(["field_id", "season"]).value
    totals = g.sum()[g.count() == 9].groupby("season").mean()  # complete Oct-Jun seasons, mean of the three fields
    peak = pd.read_csv(DATA / "field_history.csv").groupby("season").winter_max.mean().reindex(totals.index)
    labels = [f"{y - 1}-{str(y)[2:]}" for y in totals.index]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    bars = ax.bar(labels, totals, color=["#e76f51" if y == totals.idxmin() else "#8ab6d6" for y in totals.index])
    ax.bar_label(bars, fmt="%.0f")
    ax.set_ylabel("Oct-Jun rain, GPM IMERG (mm)")
    ax.set_ylim(0, totals.max() * 1.3)  # headroom so the legend clears the bars
    ax2 = ax.twinx()
    ax2.plot(labels, peak, "o-", color="#2a9d8f", lw=2.2, label="Crop greenness peak (HLS NDVI, mean of 3 fields)")
    ax2.set_ylim(0, 1); ax2.set_ylabel("NDVI peak"); ax2.spines["right"].set_visible(True)
    ax2.legend(frameon=False, loc="upper left")
    drop = round(100 - 100 * totals.min() / totals.drop(totals.idxmin()).mean())
    ax.set_title(f"{labels[-1]}: {drop}% less rain than the other seasons, and the satellites saw the crop suffer",
                 loc="left")
    return fig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", default=str(DATA / "source"), help="folder with 09_nasa_local_comparison.csv")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fig in [("ndvi_history", ndvi_history()), ("temperature_check", temperature_check(args.package)),
                      ("rain_check", rain_check()), ("drought_2025", drought())]:
        fig.tight_layout()
        fig.savefig(OUT / f"{name}.png", dpi=160)
        print("wrote", OUT / f"{name}.png")


if __name__ == "__main__":
    main()
