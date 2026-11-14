# Data contract

All roles write to and read from `data/`. These names and columns are fixed. If you need to change one, open an issue and tag the integration lead (Role 1).

| File | Owner | Columns / shape |
|---|---|---|
| `fields.geojson` | Role 4 | Polygon features with properties `field_id`, `name_ar`, `name_en`, `zone` (`maru`), `rain_mm` (may be empty) |
| `climate_monthly.csv` | Role 2 | `field_id, month (YYYY-MM), variable, value, anomaly` |
| `sat_monthly.csv` | Role 3 | `field_id, month (YYYY-MM), variable, value, anomaly, native_res_m` |
| `field_static.csv` | Role 3 | `field_id, elevation_m, slope_deg` |
| `field_history.csv` | Role 3 | `field_id, season, winter_max, summer_max, ndvi_max, class` (`winter_crop` \| `irrigated_summer` \| `fallow` \| `uncertain`; NDVI cannot separate wheat from lentil; seasons without Feb–Apr data are omitted) |
| `ndvi_monthly_profile.csv` | Role 3 | `field_id, cal_month (1-12), ndvi_median, bare_share, n_years` — typical NDVI per calendar month 2015–2025; `bare_share` = share of years with NDVI < 0.25 (bare soil) |
| `validation.json` | Role 3 | NASA vs local station checks: temperature (raw, lapse-corrected, sensitivity 5–7 °C/km) and rainfall (POWER, IMERG) |
| `crops.csv` | Role 4 | `crop, family, legume, kc_mid, kc_end, season_days, sow_month, min_rain_mm, frost_sens, heat_c, income_level, source_url` |
| `soil.json` | Role 4 | `{field_id: {clay_pct, sand_pct, soc_gkg, ph, awc_mm, q05, q95}}` |
| `soil_reference.json` | Role 4 | Published Maru research-site soil profile (NARC/JUST 2021). Reference only, **not** field measurements; use with low confidence |
| `rotations.json` | Role 4 | `{field_id: [{id, name_ar, name_en, sequence: [crop, ...], is_current}]}`; `is_current` is `true`, `false` or `null` (null = unknown: NDVI shows a winter crop every year but cannot tell wheat from lentil, so the farmer confirms) |
| `explanations.json` | Role 5 | `{field_id: {rotation_id: {ar, en}}}` |

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
