# Data contract

All roles write to and read from `data/`. These names and columns are fixed. If you need to change one, open an issue and tag the integration lead (Role 1).

| File | Owner | Columns / shape |
|---|---|---|
| `fields.geojson` | Role 4 | Polygon features with properties `field_id`, `name_ar`, `name_en`, `zone` (`maru`), `rain_mm` (mean Oct–Jun rain from GPM IMERG; all three fields share one ~11 km IMERG cell, so it is regional) |
| `climate_monthly.csv` | Role 2 | `field_id, month (YYYY-MM), variable, value, anomaly` |
| `sat_monthly.csv` | Role 3 | `field_id, month (YYYY-MM), variable, value, anomaly, native_res_m` |
| `field_static.csv` | Role 3 | `field_id, elevation_m, slope_deg` |
| `field_history.csv` | Role 3 | `field_id, season, winter_max, summer_max, ndvi_max, class` (`winter_crop` \| `summer_green` \| `fallow` \| `uncertain`; `summer_green` = green in the dry season, from irrigation or weeds; NDVI cannot separate wheat from lentil; seasons without Feb–Apr data are omitted) |
| `ndvi_monthly_profile.csv` | Role 3 | `field_id, cal_month (1-12), ndvi_median, bare_share, n_years` — typical NDVI per calendar month 2015–2025; `bare_share` = share of years with NDVI < 0.25 (bare soil) |
| `validation.json` | Role 3 | NASA vs local station checks: temperature (raw, lapse-corrected, sensitivity 5–7 °C/km) and rainfall (POWER, IMERG) |
| `crops.csv` | Role 4 | `crop, family, legume, kc_mid, kc_end, season_days, sow_month, min_rain_mm, frost_sens, heat_c, income_level, source_url` |
| `soil.json` | Role 4 (values from Role 3) | `{field_id: {clay_pct, sand_pct, soc_gkg, ph, source}}`: modelled SoilGrids topsoil (0–30 cm) at 250 m. The field description shows clay, sand and pH. The station profile is an approximate local reference. The rotation practices score uses crop sequences. `prep/field_context.py` |
| `soil_reference.json` | Role 4 | Published Maru research-site soil profile (NARC/JUST 2021). Reference only, **not** field measurements; use with low confidence |
| `rotations.json` | Role 4 | `{field_id: [{id, name_ar, name_en, sequence: [crop, ...], is_current}]}`; `is_current` is `true`, `false` or `null` (null = unknown. Satellite history rules out wheat–fallow (`false`: no fallow season since 2015); wheat–wheat vs wheat–lentil stays `null` because NDVI cannot tell wheat from lentil, so the farmer confirms) |
| (scores) | Role 5 | Not a file: `src/scoring.py` computes scores live from the files above, so they always match the farmer's sliders |

## Conventions

- **Long format.** Monthly files have one row per field, month and variable. Add a variable by adding rows, not columns.
- **`anomaly`** is a z-score against the same calendar month for that field and variable. It is empty when there are fewer than 3 years of data for that month.
- **`season`** is the harvest year. The winter season runs November of the previous year to May; summer runs June to September.
- **Missing values** are empty cells. Never write `-999`.
- **Units go in the variable name** when they are not obvious, for example `tws_cm` or `precip_mm`.

## Variables in `sat_monthly.csv`

| variable | source | unit | native_res_m |
|---|---|---|---|
| `ndvi` | HLS L30 + S30, cloud-masked monthly median | – | 30 |
| `sm_rootzone` | SMAP L4 `sm_rootzone`, monthly mean | m³/m³ | 9000 |
| `precip_imerg_mm` | GPM IMERG V07 monthly, rate × hours in month | mm/month | 11132 |
| `tws_cm` | GRACE mascon `lwe_thickness`, monthly | cm water equivalent | 300000 |

## Heat and frost in `climate_monthly.csv`

| variable | meaning | confidence |
|---|---|---|
| `heat_days` | days above the site's own 90th percentile of daily Tmax (39.6 °C raw POWER, 1998–2025), about 36 a year | low: a relative indicator. A fixed 35 °C threshold gave ~82 days a year against ~46 in ERA5-Land, because POWER Tmax runs hot here, so it was dropped |
| `frost_days` | days with elevation-corrected POWER Tmin < 0 °C | low: not checked against local Tmin |

No score is built on either variable.

## Water coverage calculation

`wind_m_s` is NASA POWER `WS2M` in m/s at 2 m. `solar_mj_m2_day` is `ALLSKY_SFC_SW_DWN` from the Agroclimatology community in MJ/m²/day. `precip_mm` is monthly `PRECTOTCORR` summed in mm.

The engine uses monthly weather summaries in the daily FAO-56 Penman–Monteith calculation, assumes zero daily soil heat flux, and spreads monthly rainfall evenly over that month's days. It estimates actual vapour pressure from mean relative humidity and sums daily `Kc × ET0` over the crop calendar. The crop coverage score is seasonal rain divided by estimated demand, capped at 100%. This is a potential water demand estimate. The model does not track effective rainfall, runoff or soil water storage.

The rotation score averages the phase scores equally. Fallow contributes 100% by convention because it has zero crop water demand. In Maru 1 in 2024–25, wheat received 158.35 mm against an estimated 700.77 mm of demand, for a crop score of 22.6%. The wheat–fallow rotation score is `(22.6 + 100) / 2`, or 61.3% before rounding to the displayed integer.

## Crop calendar check

`crops.csv` sows wheat and lentil on 1 November (`sow_month`) with FAO-56 season lengths: wheat 240 days (ends late June), lentil 170 days. Maru trials sowed both on 14 December 2021 (Bani Khalaf et al. 2024, 2025); lentil was harvested 2 June 2022 (170 days, the same length). No wheat harvest date from that trial season is published.

Sensitivity run with 14 December sowing, all three fields:

| calendar | equal priorities, first | water-first, first | largest score change |
|---|---|---|---|
| 1 November, FAO-56 lengths (used) | wheat–lentil | wheat–lentil | – |
| 14 December, wheat 240 days (runs to August) | wheat–lentil | wheat–fallow | 9.3 points |
| 14 December, wheat to 7 June (175 days) | wheat–lentil | wheat–fallow | 5.3 points |

The November calendar is kept: a 240-day wheat season from 14 December would run into August, past any Maru harvest, and the 7 June harvest date comes from a different season (2026).
