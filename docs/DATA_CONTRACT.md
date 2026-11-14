# Data contract

All roles write to and read from `data/`. These names and columns are fixed. If you need to change one, open an issue and tag the integration lead (Role 1).

| File | Owner | Columns / shape |
|---|---|---|
| `fields.geojson` | Role 4 | Polygon features with properties `field_id`, `name_ar`, `name_en`, `zone` (`valley` \| `highland` \| `azraq`), `rain_mm` |
| `climate_monthly.csv` | Role 2 | `field_id, month (YYYY-MM), variable, value, anomaly` |
| `sat_monthly.csv` | Role 3 | `field_id, month (YYYY-MM), variable, value, anomaly, native_res_m` |
| `field_static.csv` | Role 3 | `field_id, elevation_m, slope_deg` |
| `field_history.csv` | Role 3 | `field_id, season, winter_max, summer_max, ndvi_max, class` (`winter_crop` \| `irrigated_summer` \| `fallow` \| `uncertain`; NDVI cannot separate wheat from lentil; seasons without Feb–Apr data are omitted) |
| `crops.csv` | Role 4 | `crop, family, legume, kc_mid, kc_end, season_days, sow_month, min_rain_mm, frost_sens, heat_c, income_level, source_url` |
| `soil.json` | Role 4 | `{field_id: {clay_pct, sand_pct, soc_gkg, ph, awc_mm, q05, q95}}` |
| `rotations.json` | Role 4 | `{field_id: [{id, name_ar, name_en, sequence: [crop, ...], is_current}]}` |
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
| `tws_cm` | GRACE mascon `lwe_thickness`, monthly | cm water equivalent | 300000 |
