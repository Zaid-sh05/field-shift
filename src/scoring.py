
"""Transparent rotation scoring. Every score is a physical quantity or a counted practice, never a fitted number.

Criteria (0-100, higher is better), for a two-season rotation on one field:
  water   share of crop water demand met by rain, mean of all seasons
  risk    the same share in the driest fifth of seasons only
  soil    soil-health practices present, out of 2:
          a legume in the rotation; no cereal directly after the same cereal
  bare    share of the year the soil is green, as HLS NDVI observed it
  harvest share of seasons that end in a harvest (no prices or yields assumed)

The engine ranks by the farmer's own weights. It never recommends:
the farmer and the extension officer decide.
"""

import calendar
import json
import math
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import pandas as pd


DATA = Path(__file__).resolve().parents[1] / "data"

CRITERIA = ("water", "risk", "soil", "bare", "harvest")

CONFIDENCE = {
    "water": "medium",
    "risk": "medium",
    "soil": "low",
    "bare": "high",
    "harvest": "low",
}

LAT_RAD = math.radians(32.62)

STAGES = {
    "WHEAT": (30, 140, 40, 30),
    "LENTIL": (25, 35, 70, 40),
}

KC_INI = {
    "WHEAT": 0.7,
    "LENTIL": 0.4,
}

CLOSE_MARGIN = 5.0
DRY_SHARE = 0.2


def extraterrestrial_radiation(doy):
    """Ra, MJ/m2/day (FAO-56 equation 21)."""

    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    decl = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(-math.tan(LAT_RAD) * math.tan(decl))

    return (24 * 60 / math.pi) * 0.082 * dr * (
        ws * math.sin(LAT_RAD) * math.sin(decl)
        + math.cos(LAT_RAD) * math.cos(decl) * math.sin(ws)
    )


def et0_penman_monteith(
    tmean,
    tmax,
    tmin,
    rh_pct,
    wind_m_s,
    solar_mj,
    doy,
    elevation_m,
):
    """Reference evapotranspiration, mm/day, using FAO-56 Penman-Monteith."""

    pressure = 101.3 * (
        (293 - 0.0065 * elevation_m) / 293
    ) ** 5.26

    gamma = 0.000665 * pressure

    def svp(t):
        return 0.6108 * math.exp(17.27 * t / (t + 237.3))

    es = (svp(tmax) + svp(tmin)) / 2
    ea = es * rh_pct / 100

    slope = 4098 * svp(tmean) / (tmean + 237.3) ** 2

    clear_sky = (
        0.75 + 2e-5 * elevation_m
    ) * extraterrestrial_radiation(doy)

    long_wave = (
        4.903e-9
        * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4)
        / 2
        * (0.34 - 0.14 * math.sqrt(ea))
        * (1.35 * min(solar_mj / clear_sky, 1) - 0.35)
    )

    net = 0.77 * solar_mj - long_wave

    return (
        0.408 * slope * net
        + gamma * 900 / (tmean + 273) * wind_m_s * (es - ea)
    ) / (
        slope + gamma * (1 + 0.34 * wind_m_s)
    )


def kc_on_day(crop, day, kc_mid, kc_end):
    """Crop coefficient on day after sowing (FAO-56 single-Kc curve)."""

    ini, dev, mid, late = STAGES[crop]
    k0 = KC_INI[crop]

    if day < ini:
        return k0

    if day < ini + dev:
        return k0 + (kc_mid - k0) * (day - ini) / dev

    if day < ini + dev + mid:
        return kc_mid

    return kc_mid + (
        (kc_end - kc_mid)
        * min(day - ini - dev - mid, late)
        / late
    )


@lru_cache(maxsize=None)
def _tables():
    climate = pd.read_csv(DATA / "climate_monthly.csv")

    wide = climate.pivot_table(
        index=["field_id", "month"],
        columns="variable",
        values="value",
    )

    crops = pd.read_csv(DATA / "crops.csv").set_index("crop")

    profile = pd.read_csv(DATA / "ndvi_monthly_profile.csv")

    rotations = json.loads(
        (DATA / "rotations.json").read_text(encoding="utf-8")
    )

    elevation = pd.read_csv(
        DATA / "field_static.csv"
    ).set_index("field_id").elevation_m

    return wide, crops, profile, rotations, elevation


@lru_cache(maxsize=None)
def crop_seasons(field_id, crop):
    """Calculate crop water demand, rainfall and met share per harvest year."""

    wide, crops, _, _, elevation = _tables()

    row = crops.loc[crop]
    months = wide.loc[field_id]

    out = {}

    for year in sorted({int(m[:4]) for m in months.index})[1:]:

        day0 = date(year - 1, int(row.sow_month), 1)

        demand = 0.0
        rain = 0.0

        for d in range(int(row.season_days)):

            day = day0 + timedelta(days=d)
            key = day.strftime("%Y-%m")

            if key not in months.index:
                break

            m = months.loc[key]

            demand += kc_on_day(
                crop,
                d,
                row.kc_mid,
                row.kc_end,
            ) * et0_penman_monteith(
                m.tmean_c,
                m.tmax_c,
                m.tmin_c,
                m.rh_pct,
                m.wind_m_s,
                m.solar_mj_m2_day,
                day.timetuple().tm_yday,
                elevation[field_id],
            )

            rain += (
                m.precip_mm
                / calendar.monthrange(day.year, day.month)[1]
            )

        else:
            out[year] = {
                "demand_mm": float(demand),
                "rain_mm": float(rain),
                "met": float(min(1.0, rain / demand)),
            }

    return out


def _is_crop(name):
    return name in STAGES


def rotation_criteria(field_id, sequence):
    """Calculate the five criterion scores for one rotation."""

    _, crops, profile, _, _ = _tables()

    grown = [c for c in sequence if _is_crop(c)]

    per_crop = {
        c: crop_seasons(field_id, c)
        for c in set(grown)
    }

    years = (
        sorted(
            set.intersection(
                *(set(v) for v in per_crop.values())
            )
        )
        if per_crop
        else []
    )

    ref = crop_seasons(field_id, "WHEAT")

    dry_years = sorted(
        ref,
        key=lambda y: ref[y]["rain_mm"],
    )[:max(1, math.ceil(len(ref) * DRY_SHARE))]

    def met(year_list):
        shares = [
            (
                sum(
                    per_crop[c][y]["met"]
                    for y in year_list
                    if y in per_crop[c]
                ) / len(year_list)
            )
            if _is_crop(c)
            else 1.0
            for c in sequence
        ]

        return float(100 * sum(shares) / len(shares))

    legume = any(
        bool(crops.loc[c].legume)
        for c in grown
    )

    no_repeat = not any(
        a == b and _is_crop(a)
        for a, b in zip(
            sequence,
            sequence[1:] + sequence[:1],
        )
    )

    p = profile[profile.field_id == field_id]

    green_months = float(
        (1 - p.bare_share).sum()
    )

    covered = [
        green_months if _is_crop(c) else 0.0
        for c in sequence
    ]

    mean_of = lambda c, k: (
        sum(per_crop[c][y][k] for y in years) / len(years)
    )

    return {
        "water": {
            "score": met(years),
            "demand_mm": {
                c: round(mean_of(c, "demand_mm"))
                for c in per_crop
            },
            "rain_mm": {
                c: round(mean_of(c, "rain_mm"))
                for c in per_crop
            },
            "seasons": len(years),
        },

        "risk": {
            "score": met(dry_years),
            "dry_seasons": len(dry_years),
            "seasons": len(ref),
        },

        "soil": {
            "score": 50.0 * (legume + no_repeat),
            "legume": legume,
            "no_repeat": no_repeat,
        },

        "bare": {
            "score": 100 * sum(covered) / (12 * len(covered)),
            "green_months": round(
                sum(covered) / len(covered), 1
            ),
        },

        "harvest": {
            "score": 100 * len(grown) / len(sequence),
            "harvests": len(grown),
            "of": len(sequence),
        },
    }


def _totals(per_rotation, weights):
    total_weight = sum(
        weights[c] for c in CRITERIA
    )

    return {
        rid: float(
            sum(
                weights[c] * crit[c]["score"]
                for c in CRITERIA
            ) / total_weight
        )
        for rid, crit in per_rotation.items()
    }


def evaluate(field_id, weights):
    """Rank rotations using the farmer's weights."""

    if (
        set(weights) != set(CRITERIA)
        or any(
            not isinstance(w, (int, float))
            or isinstance(w, bool)
            or w < 0
            for w in weights.values()
        )
        or sum(weights.values()) <= 0
    ):
        raise ValueError(
            "weights must give a non-negative number for each of: "
            + ", ".join(CRITERIA)
        )

    rotations = _tables()[3].get(field_id)

    if not rotations:
        raise ValueError(
            f"no rotations for field {field_id!r}"
        )

    per_rotation = {
        r["id"]: rotation_criteria(
            field_id,
            r["sequence"],
        )
        for r in rotations
    }

    totals = _totals(per_rotation, weights)

    order = sorted(
        totals,
        key=totals.get,
        reverse=True,
    )

    close = (
        len(order) > 1
        and totals[order[0]] - totals[order[1]] < CLOSE_MARGIN
    )

    for c in CRITERIA:
        for factor in (0.9, 1.1):

            nudged = _totals(
                per_rotation,
                {
                    **weights,
                    c: weights[c] * factor,
                },
            )

            close = (
                close
                or max(nudged, key=nudged.get) != order[0]
            )

    heaviest = max(weights.values())

    return {
        "field_id": field_id,

        "rotations": [
            {
                "id": rid,
                "total": round(totals[rid], 1),

                "criteria": {
                    c: {
                        **v,
                        "score": round(v["score"], 1),
                        "confidence": CONFIDENCE[c],
                    }
                    for c, v in per_rotation[rid].items()
                },
            }
            for rid in order
        ],

        "close_call": bool(close),

        "low_confidence_top": any(
            weights[c] == heaviest
            and CONFIDENCE[c] == "low"
            for c in CRITERIA
        ),
    }


def crop_calendar(sequence, start_month=10):
    """Return 12 monthly slots for each rotation season."""

    _, crops, _, _, _ = _tables()

    seasons = []

    for crop in sequence:

        slots = [None] * 12

        if _is_crop(crop):

            row = crops.loc[crop]

            n_months = math.ceil(
                int(row.season_days) / 30.4
            )

            for i in range(n_months):

                slots[
                    (int(row.sow_month) + i - start_month) % 12
                ] = crop

        seasons.append(slots)

    return seasons
