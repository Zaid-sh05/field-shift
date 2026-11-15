"""Transparent rotation scoring. Every score is a physical quantity or a counted practice, never a fitted number.

Criteria (0-100, higher is better), for a two-season rotation on one field:
  water   share of crop water demand met by rain, mean of all seasons (FAO-56 Penman-Monteith demand vs NASA POWER rain)
  risk    the same share in the driest fifth of seasons only
  soil    soil-health practices present, out of 2: a legume in the rotation; no cereal directly after the same cereal
  bare    share of the year the soil is green, as HLS NDVI observed it on this field (fallow years count as bare)
  harvest share of seasons that end in a harvest (no prices or yields are assumed)

The engine ranks by the farmer's own weights. It never recommends: the farmer and the extension officer decide.
"""
import json
import math
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
CRITERIA = ("water", "risk", "soil", "bare", "harvest")
# How far each criterion can be trusted here (see data/validation.json and docs/DATA_CONTRACT.md).
CONFIDENCE = {"water": "medium", "risk": "medium", "soil": "low", "bare": "high", "harvest": "low"}
LAT_RAD = math.radians(32.62)  # Maru fields
# FAO-56 Table 11 growth-stage lengths in days (initial, development, mid, late) and Table 12 initial Kc.
# The stage shares are kept and stretched to the local season length in data/crops.csv, as FAO-56 advises when a
# local calendar is known (wheat: Maru sowing date + satellite-observed season end; lentil: Maru trial dates).
# kc_mid, kc_end, season_days and sow_month come from data/crops.csv (Role 4).
STAGES = {"WHEAT": (30, 140, 40, 30), "LENTIL": (25, 35, 70, 40)}
KC_INI = {"WHEAT": 0.7, "LENTIL": 0.4}
CLOSE_MARGIN = 5.0  # points: below this the top two are reported as a close call
DRY_SHARE = 0.2     # "dry seasons" = the driest fifth of the record


def extraterrestrial_radiation(doy):
    """Ra, MJ/m2/day (FAO-56 eq. 21)."""
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    decl = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(-math.tan(LAT_RAD) * math.tan(decl))
    return (24 * 60 / math.pi) * 0.082 * dr * (
        ws * math.sin(LAT_RAD) * math.sin(decl) + math.cos(LAT_RAD) * math.cos(decl) * math.sin(ws))


def et0_penman_monteith(tmean, tmax, tmin, rh_pct, wind_m_s, solar_mj, doy, elevation_m):
    """Reference evapotranspiration, mm/day (FAO-56 eq. 6), from NASA POWER temperature, humidity, wind and
    solar radiation. Gives about 1335 mm a year at Maru; temperature-only Hargreaves gave 1600 because
    POWER's daily temperature range runs wide here."""
    pressure = 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26
    gamma = 0.000665 * pressure
    svp = lambda t: 0.6108 * math.exp(17.27 * t / (t + 237.3))
    es = (svp(tmax) + svp(tmin)) / 2
    ea = es * rh_pct / 100
    slope = 4098 * svp(tmean) / (tmean + 237.3) ** 2
    clear_sky = (0.75 + 2e-5 * elevation_m) * extraterrestrial_radiation(doy)
    long_wave = 4.903e-9 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * math.sqrt(ea)) * (
        1.35 * min(solar_mj / clear_sky, 1) - 0.35)
    net = 0.77 * solar_mj - long_wave
    return (0.408 * slope * net + gamma * 900 / (tmean + 273) * wind_m_s * (es - ea)) / (
        slope + gamma * (1 + 0.34 * wind_m_s))


def kc_on_day(crop, day, kc_mid, kc_end, season_days=None):
    """Crop coefficient on day `day` after sowing (FAO-56 single-Kc curve).

    With `season_days`, the four FAO-56 stages keep their shares and are scaled to that season length.
    """
    stages = STAGES[crop]
    scale = season_days / sum(stages) if season_days else 1.0
    ini, dev, mid, late = (length * scale for length in stages)
    k0 = KC_INI[crop]
    if day < ini:
        return k0
    if day < ini + dev:
        return k0 + (kc_mid - k0) * (day - ini) / dev
    if day < ini + dev + mid:
        return kc_mid
    return kc_mid + (kc_end - kc_mid) * min(day - ini - dev - mid, late) / late


@lru_cache(maxsize=None)
def _tables():
    climate = pd.read_csv(DATA / "climate_monthly.csv")
    wide = climate.pivot_table(index=["field_id", "month"], columns="variable", values="value")
    crops = pd.read_csv(DATA / "crops.csv").set_index("crop")
    profile = pd.read_csv(DATA / "ndvi_monthly_profile.csv")
    rotations = json.loads((DATA / "rotations.json").read_text(encoding="utf-8"))
    elevation = pd.read_csv(DATA / "field_static.csv").set_index("field_id").elevation_m
    return wide, crops, profile, rotations, elevation


@lru_cache(maxsize=None)
def _daily_rain():
    """Daily NASA POWER precipitation in mm/day, indexed by date."""
    daily = pd.read_csv(
        DATA / "source" / "01_climate_daily.csv",
        usecols=["date", "PRECTOTCORR"],
    )
    daily["date"] = pd.to_datetime(daily["date"]).dt.strftime("%Y-%m-%d")
    daily["PRECTOTCORR"] = pd.to_numeric(daily["PRECTOTCORR"], errors="raise")
    if daily["date"].duplicated().any() or daily["PRECTOTCORR"].isna().any():
        raise ValueError("Daily rainfall data contains duplicate dates or missing values.")
    return daily.set_index("date")["PRECTOTCORR"]


@lru_cache(maxsize=None)
def crop_seasons(field_id, crop, rain_factor=1.0, warming_c=0.0):
    """Per harvest year: crop water demand (mm), rain during the crop's days (mm) and the share met (0-1).

    `rain_factor` and `warming_c` build a what-if scenario from the real record: daily rain is
    multiplied by the factor and every temperature raised by the warming (relative humidity held constant,
    so warmer air is also drier air). The defaults give the observed record.
    """
    wide, crops, _, _, elevation = _tables()
    daily_rain = _daily_rain()
    row = crops.loc[crop]
    months = wide.loc[field_id]
    out = {}
    for year in sorted({int(m[:4]) for m in months.index})[1:]:
        day0 = date(year - 1, int(row.sow_month), int(row.sow_day))
        demand = rain = 0.0
        for d in range(int(row.season_days)):
            day = day0 + timedelta(days=d)
            key = day.strftime("%Y-%m")
            if key not in months.index:
                break
            m = months.loc[key]
            demand += kc_on_day(crop, d, row.kc_mid, row.kc_end, int(row.season_days)) * et0_penman_monteith(
                m.tmean_c + warming_c, m.tmax_c + warming_c, m.tmin_c + warming_c, m.rh_pct, m.wind_m_s,
                m.solar_mj_m2_day, day.timetuple().tm_yday, elevation[field_id])
            rain += rain_factor * float(daily_rain.loc[day.isoformat()])
        else:
            out[year] = {"demand_mm": float(demand), "rain_mm": float(rain), "met": float(min(1.0, rain / demand))}
    return out


def _is_crop(name):
    return name in STAGES


def rotation_criteria(field_id, sequence, rain_factor=1.0, warming_c=0.0, before=None):
    """The five criterion scores for one rotation, each with the numbers behind it.

    `before` keeps only harvest years earlier than it, so a past season can be judged on what was known then.
    """
    _, crops, profile, _, _ = _tables()
    grown = [c for c in sequence if _is_crop(c)]
    known = lambda seasons: {y: v for y, v in seasons.items() if before is None or y < before}
    per_crop = {c: known(crop_seasons(field_id, c, rain_factor, warming_c)) for c in set(grown)}
    years = sorted(set.intersection(*(set(v) for v in per_crop.values()))) if per_crop else []
    # Rank seasons by rain over the longest crop season so every rotation is tested on the same dry years.
    ref = known(crop_seasons(field_id, "WHEAT", rain_factor, warming_c))
    dry_years = sorted(ref, key=lambda y: ref[y]["rain_mm"])[:max(1, math.ceil(len(ref) * DRY_SHARE))]

    def met(year_list):  # fallow seasons have no crop to fail, so they count as fully met
        shares = [sum(per_crop[c][y]["met"] for y in year_list if y in per_crop[c]) / len(year_list) if _is_crop(c)
                  else 1.0 for c in sequence]
        return float(100 * sum(shares) / len(shares))

    legume = any(bool(crops.loc[c].legume) for c in grown)
    no_repeat = not any(a == b and _is_crop(a) for a, b in zip(sequence, sequence[1:] + sequence[:1]))
    p = profile[profile.field_id == field_id]
    green_months = float((1 - p.bare_share).sum())  # months a year this field is observed green under a winter crop
    covered = [green_months if _is_crop(c) else 0.0 for c in sequence]
    mean_of = lambda c, k: sum(per_crop[c][y][k] for y in years) / len(years)
    return {
        "water": {"score": met(years), "demand_mm": {c: round(mean_of(c, "demand_mm")) for c in per_crop},
                  "rain_mm": {c: round(mean_of(c, "rain_mm")) for c in per_crop}, "seasons": len(years)},
        "risk": {"score": met(dry_years), "dry_seasons": len(dry_years), "seasons": len(ref)},
        "soil": {"score": 50.0 * (legume + no_repeat), "legume": legume, "no_repeat": no_repeat},
        "bare": {"score": 100 * sum(covered) / (12 * len(covered)),
                 "green_months": round(sum(covered) / len(covered), 1)},
        "harvest": {"score": 100 * len(grown) / len(sequence), "harvests": len(grown), "of": len(sequence)},
    }


def _totals(per_rotation, weights):
    total_weight = sum(weights[c] for c in CRITERIA)
    return {rid: float(sum(weights[c] * crit[c]["score"] for c in CRITERIA) / total_weight)
            for rid, crit in per_rotation.items()}


def evaluate(field_id, weights, rain_factor=1.0, warming_c=0.0, before=None):
    """Rank the field's rotations by the farmer's weights (any positive numbers per criterion).

    `rain_factor` and `warming_c` re-run the same physics on a what-if climate (see crop_seasons).

    Returns rotations sorted by total, plus two honesty flags:
      close_call        the top two are within CLOSE_MARGIN points, or a +/-10% change in one weight flips the order
      low_confidence_top  the farmer's heaviest criterion is one we can only score with low confidence
    """
    if set(weights) != set(CRITERIA) or any(not isinstance(w, (int, float)) or isinstance(w, bool) or w < 0
                                           for w in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("weights must give a non-negative number for each of: " + ", ".join(CRITERIA))
    rotations = _tables()[3].get(field_id)
    if not rotations:
        raise ValueError(f"no rotations for field {field_id!r}")
    per_rotation = {r["id"]: rotation_criteria(field_id, r["sequence"], rain_factor, warming_c, before)
                    for r in rotations}
    totals = _totals(per_rotation, weights)
    order = sorted(totals, key=totals.get, reverse=True)
    close = len(order) > 1 and totals[order[0]] - totals[order[1]] < CLOSE_MARGIN
    for c in CRITERIA:  # sensitivity: does nudging one weight by 10% change which rotation comes first?
        for factor in (0.9, 1.1):
            nudged = _totals(per_rotation, {**weights, c: weights[c] * factor})
            close = close or max(nudged, key=nudged.get) != order[0]
    heaviest = max(weights.values())
    return {
        "field_id": field_id,
        "rotations": [{"id": rid, "total": round(totals[rid], 1),
                       "criteria": {c: {**v, "score": round(v["score"], 1), "confidence": CONFIDENCE[c]}
                                    for c, v in per_rotation[rid].items()}} for rid in order],
        "close_call": bool(close),
        "low_confidence_top": any(weights[c] == heaviest and CONFIDENCE[c] == "low" for c in CRITERIA),
    }


def season_replay(field_id):
    """How each rotation would have fared in every real season: {harvest_year: {rotation_id: % of water need met}}.

    A rotation's value for a year is the mean over its phases, as if each phase were on part of the land that
    year. Fallow phases count as 100 (no crop to fail). This is the observed record, not a scenario.
    """
    rotations = _tables()[3].get(field_id) or []
    wheat = crop_seasons(field_id, "WHEAT")
    out = {}
    for year in wheat:
        out[year] = {}
        for r in rotations:
            shares = [crop_seasons(field_id, c)[year]["met"] if _is_crop(c) else 1.0 for c in r["sequence"]]
            out[year][r["id"]] = round(100 * sum(shares) / len(shares))
    return out


def backtest_summary(field_id):
    """Per rotation over the real record: mean and worst share of water need met, and seasons under half."""
    replay = season_replay(field_id)
    out = {}
    for rid in next(iter(replay.values())):
        values = [row[rid] for row in replay.values()]
        worst = min(replay, key=lambda y: replay[y][rid])
        out[rid] = {"mean": round(sum(values) / len(values)), "worst": replay[worst][rid], "worst_year": worst,
                    "under_half": sum(v < 50 for v in values), "seasons": len(values)}
    return out


@lru_cache(maxsize=None)
def vigor_model():
    """A small model trained on this project's own NASA data: crop greenness from season rain.

    Target: the winter NDVI peak of each field-season (HLS, 30 m). Input: rain over the wheat season from NASA
    POWER, the same series the scenarios scale. Fitted by least squares on every field-season in
    data/field_history.csv. The error is from leave-one-season-out validation (all fields of a season are held
    out together, because they share the same rain), next to the error of always guessing the mean.
    NDVI cannot tell wheat from lentil, so this is the vigour of "a winter crop", not of one species.
    """
    import numpy as np
    history = pd.read_csv(DATA / "field_history.csv")
    points = [(crop_seasons(r.field_id, "WHEAT")[int(r.season)]["rain_mm"], float(r.winter_max), int(r.season))
              for r in history.itertuples() if int(r.season) in crop_seasons(r.field_id, "WHEAT")]
    rain, peak, season = (np.array(v) for v in zip(*points))
    slope, intercept = np.polyfit(rain, peak, 1)
    model_err, mean_err = [], []
    for held_out in np.unique(season):
        train, test = season != held_out, season == held_out
        b, a = np.polyfit(rain[train], peak[train], 1)
        model_err += list(np.abs(a + b * rain[test] - peak[test]))
        mean_err += list(np.abs(peak[train].mean() - peak[test]))
    return {"slope_per_mm": float(slope), "intercept": float(intercept), "points": len(points),
            "seasons": int(len(np.unique(season))), "r": round(float(np.corrcoef(rain, peak)[0, 1]), 2),
            "error": round(float(np.mean(model_err)), 2), "mean_only_error": round(float(np.mean(mean_err)), 2),
            "rain_min": round(float(rain.min())), "rain_max": round(float(rain.max()))}


def predict_vigor(field_id, rain_factor=1.0):
    """Expected winter greenness peak for a season with `rain_factor` times the field's mean season rain."""
    model = vigor_model()
    seasons = crop_seasons(field_id, "WHEAT")
    rain = rain_factor * sum(v["rain_mm"] for v in seasons.values()) / len(seasons)
    ndvi = min(1.0, max(0.0, model["intercept"] + model["slope_per_mm"] * rain))
    return {"rain_mm": round(rain), "ndvi": round(ndvi, 2), "error": model["error"],
            # same thresholds the season classifier uses (prep/features.py): 0.40 clear crop, 0.25 bare soil
            "state": "clear" if ndvi >= 0.40 else "weak" if ndvi >= 0.25 else "failed",
            "extrapolated": not model["rain_min"] <= rain <= model["rain_max"]}


def soil_moisture_now(field_id):
    """Latest SMAP root-zone moisture for the field's ~9 km cell, as a z-score against the same calendar month."""
    sat = pd.read_csv(DATA / "sat_monthly.csv")
    rows = sat[(sat.field_id == field_id) & (sat.variable == "sm_rootzone")].dropna(subset=["anomaly"])
    last = rows.sort_values("month").iloc[-1]
    z = float(last.anomaly)
    return {"month": last.month, "anomaly": round(z, 1), "state": "dry" if z <= -1 else "wet" if z >= 1 else "normal"}


def next_season(field_id, history, weights, rain_factor=1.0, warming_c=0.0):
    """Options for the coming season, given what the farmer grew before (oldest first, most recent last).

    None preserves the position of an unknown earlier season. The most recent season must be known.

    Each option (every crop in data/crops.csv, including fallow) is scored on the same five criteria:
      water, risk   how often rain covered this crop's water need in the real record (fallow has no crop to fail)
      soil          rotation rules met out of 3: not the same as last season; a legume within the three-season
                    window; not a third season in a row of the same crop
      bare, harvest  whether the season has a crop on the ground and a harvest
    An option that repeats the same legume is listed last whatever its score (`legume_repeat`).
    `rain_factor` and `warming_c` apply the same what-if climate as evaluate().
    `outlook` gives the odds from the record (shifted by the scenario, if any). It is not a weather forecast: nobody knows the coming rain.
    """
    _, crops, profile, _, _ = _tables()
    history = list(history)
    if not history or history[-1] is None or any(c is not None and c not in crops.index for c in history):
        raise ValueError("history needs at least last season's crop, from: " + ", ".join(crops.index))
    if set(weights) != set(CRITERIA) or sum(weights.values()) <= 0:
        raise ValueError("weights must cover: " + ", ".join(CRITERIA))
    green = float((1 - profile[profile.field_id == field_id].bare_share).sum())
    observed = crop_seasons(field_id, "WHEAT")
    wheat = crop_seasons(field_id, "WHEAT", rain_factor, warming_c)
    dry_years = sorted(wheat, key=lambda y: wheat[y]["rain_mm"])[:max(1, math.ceil(len(wheat) * DRY_SHARE))]
    options = []
    for crop in crops.index:
        grown = _is_crop(crop)
        window = history[-2:] + [crop]
        rules = {
            "varied": crop != history[-1],
            "legume": any(bool(crops.loc[c].legume) for c in window if c is not None),
            "no_third": not (grown and len(history) >= 2 and history[-1] == history[-2] == crop),
        }
        seasons = crop_seasons(field_id, crop, rain_factor, warming_c) if grown else {}
        met = sorted(v["met"] for v in seasons.values())
        criteria = {
            "water": 100 * sum(met) / len(met) if grown else 100.0,
            "risk": 100 * sum(seasons[y]["met"] for y in dry_years) / len(dry_years) if grown else 100.0,
            "soil": 100 * sum(rules.values()) / len(rules),
            "bare": 100 * green / 12 if grown else 0.0,
            "harvest": 100.0 if grown else 0.0,
        }
        total = sum(weights[c] * criteria[c] for c in CRITERIA) / sum(weights.values())
        options.append({
            "crop": crop, "total": round(float(total), 1), "rules": rules,
            # A legume straight after the same legume builds up soil-borne disease: shown, but never ranked first.
            "legume_repeat": bool(grown and crops.loc[crop].legume and history[-1] == crop),
            "criteria": {c: round(float(v), 1) for c, v in criteria.items()},
            "outlook": {"seasons": len(met), "half_or_more": sum(m >= 0.5 for m in met),
                        "typical": round(100 * met[len(met) // 2]), "worst": round(100 * met[0]),
                        "best": round(100 * met[-1]),
                        "demand_mm": round(sum(v["demand_mm"] for v in seasons.values()) / len(seasons))} if grown else None,
        })
    options.sort(key=lambda o: (o["legume_repeat"], -o["total"]))
    last_year = max(wheat)
    return {"options": options, "close_call": options[0]["total"] - options[1]["total"] < CLOSE_MARGIN,
            "soil_moisture": soil_moisture_now(field_id),
            "last_season": {"year": last_year, "rain_mm": round(observed[last_year]["rain_mm"]),
                            "driest": last_year == min(observed, key=lambda y: observed[y]["rain_mm"])}}


def crop_calendar(sequence, start_month=10):
    """For each season of the rotation, 12 month slots from `start_month`: the crop growing, or None (bare soil)."""
    _, crops, _, _, _ = _tables()
    seasons = []
    for crop in sequence:
        slots = [None] * 12
        if _is_crop(crop):
            row = crops.loc[crop]
            sown = date(2001, int(row.sow_month), int(row.sow_day))
            for d in range(int(row.season_days) + 1):  # every month the crop is in the ground, even partly
                slots[((sown + timedelta(days=d)).month - start_month) % 12] = crop
        seasons.append(slots)
    return seasons
