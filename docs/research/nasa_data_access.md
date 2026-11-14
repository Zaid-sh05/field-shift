# NASA Earth-Observation Data Access Cheat Sheet for Crop-Rotation Decision Support (2-day hackathon, Jordan focus)

Researched 2026-11-11. Tags: **[verified]** = confirmed on a fetched primary page this session; **[unverified]** = from prior knowledge or a standard catalog URL pattern that was not fetched this session. Check [unverified] items before you depend on them.

## Datasets: variables, resolution, record length, latency

### Takeaway
For a 2-day build, use NASA POWER for daily weather and agroclimate (no auth, 1981 to near-real-time, about 0.5 degree). Add SMAP L4 for root-zone soil moisture (about 9 km, 3-hourly, 2015 on), IMERG V07 for precipitation (about 0.1 degree, 1998 on), HLS for 30 m field-scale NDVI (2013 on, 2 to 3 day revisit), and GRACE mascons for regional groundwater context (monthly, 3-degree native). Everything else (ECOSTRESS, GEDI, NASADEM, MCD12Q1) is optional garnish. OpenET is not usable for Jordan because it covers only CONUS.

### Cited Findings

**NASA POWER (agroclimatology)**
- Daily point endpoint `/api/temporal/daily/point`, regional endpoint `/api/temporal/daily/regional`. Example: `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PS,WS10M&community=AG&longitude=0&latitude=0&start=20170101&end=20170201&format=CSV` — [POWER daily API docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- Formats are NetCDF, ASCII, JSON and CSV. ICASA format is point-only and AG community only — [POWER daily API docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- A point request takes at most 20 parameters. A regional request takes 1 parameter and returns a 0.5 degree grid — [POWER daily API docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- Daily data runs from 1981-01-01 to near real time. The default time standard is Local Solar Time; set `time-standard=UTC` to change it — [POWER daily API docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- Rate limiting: no numeric limit is published. The docs warn that applications that repeatedly request the same grid cell may be blocked — [POWER daily API docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- Meteorology comes from MERRA-2 (1981 on, lags real time by several months) and GEOS FP-IT/GEOS-IT (fills in to within several days of real time) on a 0.5 x 0.625 degree grid. Solar fluxes come from CERES SYN1deg, FLASHFlux and GEWEX SRB at 1 x 1 degree — [POWER methodology](https://power.larc.nasa.gov/docs/methodology/)
- Useful AG parameters:
  - T2M_MAX: max hourly 2 m temperature, degrees C.
  - PRECTOTCORR: bias-corrected precipitation, mm/day.
  - FROST_DAYS: counts days when 2 m temperature cools to the dew point and both are below 0 degrees C.
  - GWETROOT: root-zone soil wetness, 0 to 1.
  - EVPTRNS: reported as an evapotranspiration/transpiration energy flux in W/m2. Sources disagree on the exact definition.
  - The default AG climatology set is T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, ALLSKY_SFC_SW_DWN, RH2M and WS2M.
  - Sources: [POWER parameters tutorial](https://power.larc.nasa.gov/docs/tutorials/parameters/), [rOpenSci nasapower](https://docs.ropensci.org/nasapower/articles/nasapower.html), [nasapower parameters](https://www.rdocumentation.org/packages/nasapower/versions/1.1.3/topics/parameters)
- Gotcha: the GWETROOT depth is inconsistent. POWER text says 200 cm, while MERRA-2 documentation says 0 to 100 cm, and POWER staff said they were double-checking — [Earthdata forum](https://forum.earthdata.nasa.gov/viewtopic.php?p=24413)

**SMAP soil moisture**
- L4 (model-assimilated, gap-free): GEE `NASA/SMAP/SPL4SMGP/008`. 9 km EASE-Grid (GEE lists an 11 km pixel), 3-hourly, 2015-03-31 to about 3 days ago (catalog ended 2026-11-07). Bands are `sm_surface` (0 to 5 cm) and `sm_rootzone` (0 to 100 cm), as volume fraction — [GEE SPL4SMGP](https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008)
- L3 enhanced (radiometer retrieval): GEE `NASA/SMAP/SPL3SMP_E/006`, 9 km, daily. It starts 2023-12-04; earlier dates are in `/005`. Bands are `soil_moisture_am` / `soil_moisture_pm`, with QC in `retrieval_qual_flag_am/pm` (0 = passed) — [GEE SPL3SMP_E](https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL3SMP_E_006)

**GPM IMERG precipitation**
- GEE `NASA/GPM_L3/IMERG_V07`, about 11 km (0.1 degree), 30-minute steps, 1998-01-01 to near real time. The main band is `precipitation`, in mm/hr. Products are marked `status` "provisional" until gauge-corrected ("permanent"). The catalog says there are no permanent products after 2025-09-30, so recent data are provisional — [GEE IMERG V07](https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07)

**GRACE / GRACE-FO**
- GEE `NASA/GRACE/MASS_GRIDS_V04/MASCON`, monthly, 2002-03-31 to 2024-09-30 in the catalog. Band `lwe_thickness` (cm) plus `uncertainty`. The underlying solution is a 3-degree equal-area mascon grid with 4,551 cells, resampled to about 55 km pixels — [GEE GRACE mascon](https://developers.google.com/earth-engine/datasets/catalog/NASA_GRACE_MASS_GRIDS_V04_MASCON)

**HLS (Harmonized Landsat Sentinel-2)**
- GEE `NASA/HLS/HLSL30/v002` (Landsat 8/9) and `NASA/HLS/HLSS30/v002` (Sentinel-2), 30 m. Combined revisit is 2 to 3 days. L30 data run from 2013-04-11 to near real time. In L30, Red is B4 and NIR is B5. Clouds come from the `Fmask` bits: bit 1 cloud, bit 2 adjacent, bit 3 shadow, bit 4 snow, bit 5 water — [GEE HLSL30](https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSL30_v002)

**ECOSTRESS**
- Collection 2, 70 m tiled COGs: ECO_L3T_JET.002 (ET), ECO_L4T_ESI.002 (Evaporative Stress Index) and ECO_L4T_WUE.002. These have been in AppEEARS since v3.60 (Aug 2024) — [Earthdata alert](https://www.earthdata.nasa.gov/data/alerts-outages/ecostress-v2-level-3-et-level-4-esi-wue-tiled-data-now-available-appeears)
- The sensor is on the ISS, so coverage is limited to about 52 N to 52 S (the catalog bbox is 54 N to 54 S). Jordan (29 to 33 N) is covered. Known issues: ~500 m to 1 km artifacts in V2 L3/L4, ISS solar-array obstructions, and noisy data from 2025-05-15 to 2025-07-01 — [ESI catalog](https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l4t-esi-002), [ESI data.gov](https://catalog.data.gov/dataset/ecostress-gridded-evaporative-stress-index-pt-jpl-instantaneous-l4-global-70-m-v002)

**OpenET**
- Coverage is CONUS only (v2.1; earlier versions covered the Western US). Daily ET is available from 2016 and monthly from 2000, through 2025. The point endpoint is `POST openet-api.org/raster/timeseries/point` with an API key from the account dashboard, and daily requests are capped at 10 years — [OpenET data availability](https://openet.gitbook.io/docs/additional-resources/data-availability), [OpenET API](https://openet.gitbook.io/docs/reference/api-reference/raster)

**MODIS / NASADEM / GEDI / MCD12Q1 [unverified IDs, standard GEE catalog entries]**
- These were not fetched this session, so check each ID in the [GEE catalog](https://developers.google.com/earth-engine/datasets):
  - `MODIS/061/MOD13Q1`: NDVI/EVI, 250 m, 16-day, 2000 on.
  - `MODIS/061/MOD11A2`: LST, 1 km, 8-day.
  - `MODIS/061/MOD16A2GF`: ET, 500 m, 8-day, gap-filled.
  - `MODIS/061/MCD12Q1`: land cover, 500 m, annual.
  - `NASA/NASADEM_HGT/001`: 30 m elevation; derive slope with `ee.Terrain.slope`.
  - `LARSE/GEDI/GEDI04_B_002`: gridded biomass, 1 km, mission-level.

### Inferences
- For Jordan crop rotation, POWER (climate, frost, heat) plus HLS NDVI (field-level crop/fallow history) carries about 80% of the value. SMAP, IMERG and GRACE add regional water-stress context.
- Use ECOSTRESS ESI/ET as a "wow" layer only. ISS overpasses are irregular, so expect sparse dates per field.
- In HLSS30 the harmonized NIR band is B8A, not B8, so NDVI for S30 uses (B8A-B4)/(B8A+B4). This is from prior knowledge; check it on the GEE HLSS30 page.

### Gaps
- POWER solar-data latency and the full list of AG parameter names were not confirmed from the official parameter dictionary page.
- SMAP L4 latency is not stated on the GEE page. Prior knowledge puts it at about 2 to 3 days.
- The GRACE-FO gap (Jul 2017 to May 2018) is not stated on the GEE page; it is known from mission history.
- The ECOSTRESS revisit interval was not found.

## Access methods: auth, limits, wait times, example requests

### Takeaway
Fastest path: POWER REST (no login, instant), then GEE (one account, every gridded product above, server-side reduction to field points), then AppEEARS (Earthdata login, good for point CSVs, with jobs taking minutes to an hour). Use earthaccess only if you need raw granules. GIBS gives free map tiles with no auth.

### Cited Findings
- **AppEEARS API** (base `https://appeears.earthdatacloud.nasa.gov/api`):
  - Login is `POST /login` with HTTP Basic auth using your Earthdata credentials. It returns a Bearer token valid for about 48 hours; get a new one on a 403.
  - Submit with `POST /task` and a JSON body (shown below). The response is 202 plus a `task_id`.
  - Poll `GET /status/{task_id}` for `pending`, `processing`, `done` or `error`.
  - List files with `GET /bundle/{task_id}`, then fetch each with `GET /bundle/{task_id}/{file_id}`. That redirects to an S3 URL valid for 48 hours, so follow redirects.
  - `GET /product` and `GET /product/{id}` need no auth.
  - A 429 response means slow down. No numeric limit is published.
  - Source: [AppEEARS API docs](https://appeears.earthdatacloud.nasa.gov/api/)
- Example point task body — [AppEEARS API docs](https://appeears.earthdatacloud.nasa.gov/api/):
  ```json
  {"task_type":"point","task_name":"my-task",
   "params":{"dates":[{"startDate":"01-01-2010","endDate":"01-31-2010"}],
             "layers":[{"product":"MOD11A1.061","layer":"LST_Day_1km"}],
             "coordinates":[{"latitude":42,"longitude":-72}]}}
  ```
- AppEEARS wait times: run time depends on date range, number of points and layers. Small requests usually finish within 15 minutes; large ones take an hour or more. Outputs are kept for 30 days — [Earthdata AppEEARS article](https://www.earthdata.nasa.gov/learn/articles/appeears-data-tool-focus)
- **GIBS tiles** (public, no auth): `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{Layer}/default/{Time}/{TileMatrixSet}/{z}/{y}/{x}.{ext}`, e.g. `.../MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-07-09/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`. Leaflet examples are in the gibs-web-examples repo — [GIBS access basics](https://nasa-gibs.github.io/gibs-api-docs/access-basics/)
- **earthaccess**: a Python library that searches CMR and downloads granules or streams them via fsspec, and it manages Earthdata Login — [earthaccess docs](https://earthaccess.readthedocs.io/en/stable/)
- **OpenET**: free API key, but CONUS only, so not relevant to Jordan — [OpenET data availability](https://openet.gitbook.io/docs/additional-resources/data-availability)

Example code. The earthaccess and GEE calls are standard library usage, not fetched this session.
```python
# POWER: no auth
import requests, pandas as pd
u = ("https://power.larc.nasa.gov/api/temporal/daily/point"
     "?parameters=T2M_MAX,T2M_MIN,PRECTOTCORR,FROST_DAYS,GWETROOT,ALLSKY_SFC_SW_DWN"
     "&community=AG&latitude=32.0&longitude=35.9&start=20000101&end=20251231&format=JSON")
d = requests.get(u, timeout=120).json()["properties"]["parameter"]
df = pd.DataFrame(d); df.index = pd.to_datetime(df.index); df = df.replace(-999, pd.NA)

# earthaccess (pip install earthaccess) [unverified snippet]
import earthaccess
earthaccess.login()  # prompts, or reads EARTHDATA_USERNAME/PASSWORD env vars or ~/.netrc
res = earthaccess.search_data(short_name="SPL4SMGP", bounding_box=(35, 29, 39.5, 33.5),
                              temporal=("2024-01-01", "2024-01-07"))
files = earthaccess.download(res, "./smap")

# GEE: SMAP root-zone monthly mean at a field point [unverified snippet]
import ee; ee.Initialize(project="YOUR_PROJECT")
pt = ee.Geometry.Point(35.9, 32.0)
ic = ee.ImageCollection("NASA/SMAP/SPL4SMGP/008").select("sm_rootzone").filterDate("2016-01-01", "2026-01-01")
```

### Inferences
- GEE needs a Google Cloud project registered for noncommercial use. Do this on day 0, because approval can take time. This is prior knowledge, not checked this session.
- Cache every API response to local CSV/Parquet. POWER may block apps that repeat the same cell request, and AppEEARS jobs are slow.
- Giovanni, CMR direct search and Planetary Computer are fallbacks only. GEE plus POWER covers everything here faster.

### Gaps
- The AppEEARS maximum points per request and area-size limits were not found on the pages fetched.
- Microsoft Planetary Computer collection IDs for HLS/MODIS were not checked this session.
- The OpenET free-tier numeric quota is not published on the pages fetched.

## Harmonizing resolutions to a common grid

### Takeaway
Don't regrid rasters. Choose the field point or polygon as the unit and sample each product there (point or `reduceRegion` mean over the field), then aggregate to monthly values and a monthly climatology (e.g. 2001 to 2025). You end up with one tidy table: field_id, month, variable, value, anomaly.

### Cited Findings
- POWER regional output is on a 0.5 degree grid, and parameters are delivered at source resolution — [POWER daily API docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- Native resolutions to keep in mind:
  - SMAP: 9 km — [GEE SPL4SMGP](https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008)
  - IMERG: about 11 km — [GEE IMERG](https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07)
  - GRACE: 3-degree mascons — [GEE GRACE](https://developers.google.com/earth-engine/datasets/catalog/NASA_GRACE_MASS_GRIDS_V04_MASCON)
  - HLS: 30 m — [GEE HLSL30](https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSL30_v002)
  - ECOSTRESS: 70 m — [ESI catalog](https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l4t-esi-002)

### Inferences
- Recipe:
  1. Fields go in a GeoJSON.
  2. For 30 to 70 m products, use `reduceRegion(mean)` over the field polygon.
  3. For products of 9 km and coarser, sample the field centroid (nearest pixel) and label it "regional context".
  4. Resample everything to monthly values (sum for P, mean for SM/T, count for frost/heat days).
  5. Compute climatology by calendar month, then anomaly = value - clim (or z-score).
- Report the native resolution next to each indicator in the UI so judges can see you understand scale.

### Gaps
- No official NASA "harmonization recipe" document was found. The recipe above is standard practice.

## Computing key indicators

### Takeaway
Every indicator here is a few lines of pandas or GEE on the per-field monthly table. Frost and heat counts can come straight from POWER daily data, and bare or fallow fields from HLS NDVI thresholds.

### Cited Findings
- POWER provides FROST_DAYS (defined as 2 m temperature reaching the dew point with both below 0 degrees C) and daily T2M_MAX/T2M_MIN, so you can count heat and frost days directly — [POWER parameters tutorial](https://power.larc.nasa.gov/docs/tutorials/parameters/), [nasapower parameters](https://www.rdocumentation.org/packages/nasapower/versions/1.1.3/topics/parameters)
- SMAP `sm_rootzone` is in volume fraction (m3/m3) — [GEE SPL4SMGP](https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008)
- GRACE `lwe_thickness` is a monthly anomaly in cm with a 1-sigma `uncertainty` band — [GEE GRACE](https://developers.google.com/earth-engine/datasets/catalog/NASA_GRACE_MASS_GRIDS_V04_MASCON)
- The HLS Fmask bits for cloud, shadow and adjacency must be masked before NDVI — [GEE HLSL30](https://developers.google.com/earth-engine/datasets/catalog/NASA_HLS_HLSL30_v002)

### Inferences (formulas; thresholds are choices to state in the UI, not NASA-defined)
- **Soil-moisture anomaly:** `z = (SM_month - mean_month_2016_2025) / std_month`. With only about 10 years of SMAP, call it a "relative anomaly". Use POWER GWETROOT (1981 on) if you need a longer baseline.
- **Frost-risk days:** `(T2M_MIN <= 0).sum()` per month, averaged over years. Use the last frost date in spring as a planting-window cue. POWER FROST_DAYS works as a cross-check.
- **Heat-stress days:** `(T2M_MAX > 35).sum()`. Use crop-specific thresholds (e.g. about 30 to 32 degrees C during wheat anthesis; about 35 degrees C for many summer crops) and cite an agronomy source in the pitch.
- **Water balance:** `P - ET`, monthly. P comes from IMERG or POWER PRECTOTCORR; ET from MOD16A2GF (8-day, kg/m2 per 8 days, scale 0.1 [unverified]). POWER has no direct ET in mm, and EVPTRNS is an energy flux in W/m2: divide by about 28.94 to get mm/day (latent heat 2.45 MJ/kg). Label that conversion approximate.
- **Bare or fallow detection:** after masking clouds, take the max NDVI over a growing season (Nov to May for rainfed Jordan). If the max is below about 0.2 to 0.25, the field was bare or fallow that season, and a clear peak (e.g. above 0.4) marks a crop. That gives a season-by-season crop/fallow history, which is a proxy for rotation.
- **GRACE trend:** linear regression of monthly `lwe_thickness` over 2003 to 2024 (`np.polyfit`), in cm/yr. Treat it as basin-scale context only, never per field.

### Gaps
- No NASA-sanctioned NDVI fallow thresholds for Jordan were found. Calibrate on a few known fields.

## Data caveats for Jordan and the Middle East

### Takeaway
Small fields of 1 to 5 ha are far below SMAP, IMERG and GRACE pixel size. Treat those products as regional context. Only HLS and ECOSTRESS resolve fields. Arid soils, bright backgrounds and sparse rainfall add noise.

### Cited Findings
- SMAP is 9 km at best and GRACE about 3 degrees, so a single pixel spans many farms — [GEE SPL4SMGP](https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008), [GEE GRACE](https://developers.google.com/earth-engine/datasets/catalog/NASA_GRACE_MASS_GRIDS_V04_MASCON)
- POWER meteorology is about 50 km (0.5 x 0.625 degree) and solar is 1 degree. Valley vs plateau microclimates (Jordan Valley below sea level vs the highlands) will be smoothed. The `site-elevation` point option adjusts pressure only — [POWER methodology](https://power.larc.nasa.gov/docs/methodology/), [POWER daily API docs](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- Recent IMERG data are provisional, not gauge-corrected: no permanent products after 2025-09-30 — [GEE IMERG](https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07)
- ECOSTRESS covers Jordan, but V2 has coarse artifacts and a noisy period in mid-2025 — [ESI catalog](https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l4t-esi-002)
- OpenET does not cover Jordan (CONUS only) — [OpenET data availability](https://openet.gitbook.io/docs/additional-resources/data-availability)

### Inferences
- Jordan Valley pixels mix irrigated strips with desert and the Dead Sea or water bodies. Mask water with HLS Fmask bit 5 and be careful with coastal SMAP pixels.
- Bright arid soils inflate the NDVI floor (bare soil around 0.1 to 0.15), so calibrate the fallow threshold locally.
- Irrigation is not visible in POWER or IMERG rainfall. A field that is green in summer with no rain implies irrigation, which is a useful derived feature.
- Use the Jordan Valley's sub-sea-level elevation, from NASADEM, as an explicit feature, because coarse climate grids will miss it.

### Gaps
- No published SMAP validation statistics specific to Jordan were found this session.
- No source was found on IMERG skill over Jordan's sparse-rainfall regime.
