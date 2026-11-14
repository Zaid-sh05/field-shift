"""What NASA data shows for the chosen field, and how far that data can be trusted here."""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA, FIGURES = ROOT / "data", ROOT / "docs" / "figures"
BADGE = {"high": "🟢", "medium": "🟡", "low": "🔴"}


def badge(t, level):
    return f'{BADGE[level]} {t("confidence")}: {t("confidence_" + level)}'


@lru_cache(maxsize=None)
def _load():
    import pandas as pd
    return (pd.read_csv(DATA / "sat_monthly.csv"), pd.read_csv(DATA / "field_history.csv"),
            json.loads((DATA / "soil.json").read_text(encoding="utf-8")),
            json.loads((DATA / "validation.json").read_text(encoding="utf-8")))


def field_summary(field_id):
    """Numbers for one field, all read from the data files: crop history, NDVI series, season rain, soil."""
    import pandas as pd
    sat, history, soil, _ = _load()
    h = history[history.field_id == field_id].sort_values("season")
    mine = sat[sat.field_id == field_id]
    ndvi = mine[mine.variable == "ndvi"].set_index("month").value
    rain = mine[mine.variable == "precip_imerg_mm"].copy()
    when = pd.to_datetime(rain.month)
    rain = rain[(when.dt.month >= 10) | (when.dt.month <= 6)]
    rain["season"] = when.dt.year + (when.dt.month >= 10)
    by_season = rain.groupby("season").value
    totals = by_season.sum()[by_season.count() == 9]  # complete Oct-Jun seasons only
    last = int(totals.index.max())
    others = totals.drop(last)
    peak = h.set_index("season").winter_max
    return {
        "seasons": len(h), "winter_crop": int((h["class"] == "winter_crop").sum()),
        "fallow": int((h["class"] == "fallow").sum()), "first": int(h.season.min()), "last": int(h.season.max()),
        "ndvi": ndvi,
        "rain_mean": round(float(others.mean())), "rain_last": round(float(totals[last])),
        "rain_change_pct": round(float(totals[last] / others.mean() * 100 - 100)), "rain_season": last,
        "rain_driest": bool(totals[last] == totals.min()), "rain_seasons": len(totals),
        "peak_last": round(float(peak[last]), 2), "peak_prev": round(float(peak[last - 1]), 2),
        "soil": soil.get(field_id, {}),
    }


def render_field_evidence(st, t, field_id):
    s = field_summary(field_id)
    st.markdown(f'**{t("evidence_title")}**')
    a, b, c = st.columns(3)
    a.metric(t("ev_winter_crop"), f'{s["winter_crop"]} / {s["seasons"]}')
    b.metric(t("ev_fallow"), s["fallow"])
    c.metric(t("ev_rain"), f'{s["rain_mean"]} mm')
    st.caption(t("ev_history_note").format(first=s["first"], last=s["last"]) + " " + badge(t, "high"))
    st.line_chart(s["ndvi"], height=220, y_label="NDVI", color="#176B48")
    st.caption(t("ev_ndvi_note"))
    season = f'{s["rain_season"] - 1}–{str(s["rain_season"])[2:]}'
    st.warning(t("ev_drought" if s["rain_driest"] else "ev_last_season").format(
        season=season, rain=s["rain_last"], change=abs(s["rain_change_pct"]), n=s["rain_seasons"],
        prev=s["peak_prev"], last=s["peak_last"]))
    st.caption(t("ev_rain_note") + " " + badge(t, "medium"))
    soil = s["soil"]
    if soil:
        st.text(t("ev_soil").format(clay=soil["clay_pct"], sand=soil["sand_pct"], ph=soil["ph"]))
        st.caption(t("ev_soil_note") + " " + badge(t, "medium"))


def render_trust(st, t):
    """How NASA data compared with the Maru ground station, from data/validation.json."""
    v = _load()[3]
    temp, rain, site = v["temperature_mean_c"], v["rain_mm"], v["station"]
    with st.expander(t("trust_title")):
        st.markdown(t("trust_intro").format(months=site["months"]))
        a, b = st.columns(2)
        a.metric(t("trust_temp_raw"), f'{temp["power_raw"]["mae"]} °C')
        b.metric(t("trust_temp_fixed"), f'{temp["power_lapse_corrected"]["6.5"]["mae"]} °C')
        errors = [x["mae"] for x in temp["power_lapse_corrected"].values()]
        st.caption(t("trust_temp_note").format(
            gap=round(site["elevation_m"] - site["power_cell_elevation_m"]), low=min(errors), high=max(errors)))
        a, b, c = st.columns(3)
        a.metric(t("trust_rain_station"), f'{rain["station_total"]:.0f} mm')
        b.metric("NASA POWER", f'{rain["power"]["total"]:.0f} mm')
        c.metric("GPM IMERG", f'{rain["imerg"]["total"]:.0f} mm')
        st.caption(t("trust_rain_note").format(pct=round(100 - 100 * rain["power"]["total"] / rain["station_total"])))
        st.caption(t("trust_heat_note"))
        for name in ("temperature_check", "rain_check", "ndvi_history"):
            path = FIGURES / f"{name}.png"
            if path.exists():
                st.image(str(path))
