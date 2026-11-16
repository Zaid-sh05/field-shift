# تباشير · Agri-Signs: Rotation Explorer for Jordanian Farms

*Tabasheer* (تباشير) is Arabic for the first signs of good news: the first signs of rain, the first signs of a season. The tool reads the signs from NASA satellites and brings them to the farmer. Built for the Field Shift challenge; the repository keeps the challenge's name.

> NASA Space Apps Challenge 2026 · Challenge: **Field Shift: Adapting Farms with NASA Data** · Local event: Jordan University of Science and Technology (JUST), 14–15 Nov 2026

**Live app: https://zaid-sh05.github.io/field-shift/app/**

An Arabic-first decision-support tool for rainfed farms around **Maru, Irbid (northern Jordan)**. A farmer picks a field, sets their priorities, and compares **three crop-rotation strategies side by side**: wheat–wheat, wheat–lentil and wheat–fallow (the rotations tested at Maru in published trials), against what the field has been doing. Each rotation gets a score for the farmer's own priorities, a plain sentence and the numbers behind every criterion, a month-by-month crop and bare-soil calendar, and a **confidence badge on every score**, so the farmer can see what the satellites observed and what is only an estimate.

On top of the comparison, the farmer can simulate a drier or warmer season and watch the ranking move, see how each rotation would have fared in each of the 27 real seasons on record, and ask a next-season advisor what to grow after the last three seasons' crops. A small model trained on our own NASA data estimates crop vigour for the chosen rain, with its error shown.

The tool supports the farmer's judgment. It does not replace the farmer or local agricultural extension officers.

## What makes it different

Crop-comparison tools exist. Most take satellite data as the truth and hand back a recommendation. We did five things differently:

1. **We checked NASA before trusting it.** Against the Maru ground station, NASA POWER read 2.4 °C too warm, because its grid cell sits 440 m lower. We corrected for elevation and cut the error by two thirds. We also found that both NASA rainfall products miss about 22% of local rain, and we say so on screen.
2. **Every score carries a confidence level.** The farmer sees which numbers the satellites observed on the field and which are regional estimates or rules.
3. **The current rotation comes from space.** Eleven years of imagery show no fallow season on any of the three fields, so the tool rules wheat–fallow out without asking, and asks the farmer only what satellites cannot see.
4. **It can be tested, not just trusted.** The farmer can replay all 27 real seasons, including the 2024–25 drought, and simulate a drier or warmer season to see when the ranking stops being clear.
5. **It ranks; it does not decide.** The order follows the farmer's own priorities, close calls are flagged, and the decision stays with the farmer and the extension officer.

## Why this matters

- More than 90% of Jordan gets under 200 mm of rain a year, and renewable freshwater is about 61 m³ per person per year.
- The Azraq aquifer is pumped at roughly 2.6× its safe yield.
- In January 2022, frost destroyed 30–90% of open-field crops in the Jordan Valley.

Rotation choices that fit the water budget and avoid known heat and frost windows are one of the few levers small farms control.

## Study site: three fields at Maru

Following our mentor's advice to go deep on one area with local data, we focus on Maru, a rainfed cereal area north-east of Irbid with published research-station records (NARC and JUST). We drew three real fields (5–8 ha each) over satellite imagery and pulled 11 years of NASA data for each.

What the data showed:

- **No fallow season in 11 years.** HLS NDVI shows a clear winter crop in 31 of 33 field-seasons from 2015 to 2025; the other 2 are borderline green, and none is bare. The current practice is continuous winter cropping, which is the baseline we compare against. (NDVI cannot tell wheat from lentil, so the farmer confirms the crop.)
- **NASA temperature runs hot here, and we know why.** The NASA POWER grid cell sits at 149 m; the Maru station is at 589 m. Against 18 months of published station data, the mean-temperature error is 2.37 °C raw and 0.56–0.96 °C after a standard lapse-rate correction (5–7 °C/km). The result holds across the whole range, so it does not depend on one tuned number.
- **Both satellite rainfall products under-count.** NASA POWER and GPM IMERG show 23% and 22% less rain than the station over the same months, so rainfall is shown with medium confidence.
- **2024–25 was the driest season on record, and the satellites saw the crop suffer.** NASA POWER puts it 55% below the mean of the other 26 seasons, GPM IMERG 56% below, and the HLS greenness peak averaged over the three fields fell from 0.82 to 0.48.
- **The crop calendar is local and measured from space.** Sowing follows Maru trials (14 December). The wheat season end, 5 June, is the median of 32 satellite field-seasons, two days from NARC’s announced Maru harvest date. With balanced priorities wheat–lentil comes first; when water is all that matters, resting the land (wheat–fallow) leads. Details in [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md).

Numbers are in [`data/validation.json`](data/validation.json), produced by [`prep/validate.py`](prep/validate.py).

## NASA and partner data used

| Dataset | What we take from it | Native resolution | How we use it |
|---|---|---|---|
| NASA POWER (AG community) | Daily temperature, precipitation, radiation, humidity, wind | ~0.5° | Crop water demand (FAO-56 Penman-Monteith) against rain, in all seasons and in dry seasons |
| HLS (Harmonized Landsat Sentinel-2) | Red and NIR reflectance → NDVI | 30 m | Crop history per field, which rotation is ruled out, months the soil is green |
| Landsat 5/7/8/9 Collection 2 | Surface reflectance → NDVI, 1999–2025 | 30 m | Long-record test of the vigour model (27 seasons); not used in the scores |
| SMAP L4 | Root-zone soil moisture | 9 km | Extracted per field as regional context; not used in the scores |
| GPM IMERG | Precipitation | ~0.1° | Season rain per field; independent rainfall check against POWER and the Maru station |
| GRACE / GRACE-FO | Terrestrial water storage | ~3° mascons | Extracted as regional context; not used in the scores |
| SRTM | Elevation and slope | 30 m | Per-field elevation for the temperature correction; slope shown per field |
| FAO-56, FAO rotation guidance, IAEA Maru trials | Crop coefficients and growth-stage shares, rotation evidence | – | Crop table and the crop rotation practices score |
| Maru field trials (Bani Khalaf et al. 2024, 2025) | Sowing and harvest dates | point | Local crop calendar, with the wheat season end measured from HLS |
| SoilGrids (ISRIC) | Clay, sand, organic carbon, pH | 250 m | Soil per field, shown as modelled |
| ERA5-Land (ECMWF) | Daily maximum temperature | ~9 km | Cross-check only: it showed POWER heat days are overstated |
| Maru station (NARC, JUST) | Published monthly temperature and rain, soil | point | Ground truth for checking NASA data |

Every score in the interface names its source and carries a confidence level: high for field-scale satellite observation, medium for regional data checked against the station, low for rules and counts with no local measurement.

## How it works

```text
prep/ (runs before the demo)          data/ (files, the contract)        live demo
──────────────────────────           ──────────────────────────         ─────────────────────
fetch_power.py   ── NASA POWER ──►   climate_monthly.csv      ─┐
gee_export.py    ── HLS, SMAP, ──►   sat_monthly.csv           ├──►  src/scoring.py
                    IMERG, GRACE,    field_history.csv         │      │
                    SRTM             ndvi_monthly_profile.csv  │      ├─► export_web.py ─► React site (docs/app, GitHub Pages)
validate.py      ── station data ─►  validation.json          ─┤      └─► app.py ─► Streamlit version (backup)
crop table (FAO-56, Maru trials) ─►  crops.csv, soil.json,    ─┘
                                     rotations.json
```

The live app never calls Earth Engine or a remote API. The React site ships with every result precomputed by the Python engine for each field and 56 climate scenarios, so it needs no server and keeps working on bad venue Wi-Fi. A test checks the site's JavaScript against the Python engine.

The file formats are fixed in [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md). Change them only through the integration lead.

## Repository layout

```text
web/                   React site (Vite), the live app. Reads web/src/data.json; `npm test` checks its engine against Python
docs/app/              The built site, served by GitHub Pages
app.py                 Streamlit version (backup), same engine
src/scoring.py         Rotation scoring: five criteria, the farmer's weights, honesty flags
src/                   Streamlit interface: screens, components, state; translations in i18n.json (shared with the React site)
styles/                Role 6 design system (main.css)
tests/                 Engine and interface tests (python -m pytest tests)
prep/                  Offline data scripts (Roles 2, 3, 4)
  fetch_power.py       NASA POWER climate, elevation-corrected per field → data/
  gee_export.py        HLS NDVI, SMAP, IMERG, GRACE, SRTM per field → data/
  validate.py          NASA vs Maru station checks → data/validation.json
  field_context.py     Season rain (IMERG) and soil (SoilGrids) per field → data/
  figures.py           Slide figures → docs/figures/
  deck/                Pitch deck builder (python-pptx) → docs/Field_Shift_Pitch_Deck.pptx
  export_web.py        Engine results for every field and scenario → web/src/data.json
  landsat_long.py      Landsat NDVI 1999–2025 per field → data/landsat_ndvi_monthly.csv (vigour model long test)
  features.py          Anomalies, season classification, NDVI monthly profile (pure pandas, self-tested)
data/                  Generated data files + fields.geojson
data/source/           Inputs the prep scripts start from (NASA POWER daily, Maru station months)
docs/                  Data contract, research notes
requirements.txt       What the deployed app needs
requirements-prep.txt  Extra packages for the prep scripts (Earth Engine etc.)
```

## Quick start

```bash
git clone https://github.com/Zaid-sh05/field-shift.git
cd field-shift
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
cd web && npm install && npm run dev      # the live React site, at the address Vite prints
```

The Streamlit version (backup) runs from the repository root:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Checks: `python -m pytest -q tests` (56 tests) and `cd web && npm test` (5 tests).

To rebuild the React site after a data or engine change:

```bash
python prep/export_web.py      # a few minutes: every field × 56 climate scenarios
cd web && npm install && npm test && npm run build   # writes docs/app/
```

To regenerate the satellite data (Role 3):

```bash
pip install -r requirements-prep.txt
earthengine authenticate
python prep/gee_export.py --project YOUR_GEE_PROJECT
python prep/validate.py --project YOUR_GEE_PROJECT
python prep/fetch_power.py     # NASA POWER climate per field, from data/source/
python prep/figures.py         # slide figures
python prep/features.py        # self-check: prints "ok"
```

## Team

| Role | Owner | Owns |
|---|---|---|
| 1. Integration and deployment | Zaid | Repo, scoring engine, React site, deployment, submission page |
| 2. Climate data | Sadeel | NASA POWER climate, daily rain in the water score, heat and frost indicators, data review |
| 3. Satellite data | Dr. Hossam | HLS NDVI, SMAP, IMERG, GRACE, SRTM, season classification, validation |
| 4. Agronomy and story | Kosay | Crop table, rotations, Maru crop calendar sources, FAO-56 checks, video |
| 5. Scoring review | Lana | Scoring criteria and confidence, engine review |
| 6. Interface | Mohammad | Streamlit interface, Arabic RTL, next-season advisor fixes |

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how we work.

## Use of AI

In line with the Space Apps rules, we disclose AI use:

- The app uses no generative AI. Scores and advice come from a transparent, rule-based engine, and the sentences on screen are fixed templates filled with its numbers. Nothing in the app recommends a rotation.
- One small statistical model is trained on our own data: a least-squares line from season rain to the satellite greenness peak, fitted on 33 field-seasons and validated on held-out seasons (error 0.12 NDVI against 0.15 for guessing the mean). We then tested it on 27 seasons of Landsat (1999–2025, matching HLS at r 0.96): rain alone explains almost nothing (held-out R² −0.10), so the app shows this estimate as a scenario, not a forecast. The first signal that holds up is February greenness: held-out R² 0.65 over 24 Landsat seasons and 0.75 over the last 10 HLS seasons, error 0.06 NDVI. January does not hold up (it helps after 2013 and hurts before), so we do not claim it. The app shows a February check on the last season next to the estimate.
- AI assistants (Claude, ChatGPT) helped with research, with writing and reviewing code, with data analysis and with documentation. The team reviewed and ran everything.
- The demo video is AI-generated: every scene is illustrative, not filmed at Maru, and it says so on screen.

The final submission page lists the exact tools.

## License

[MIT](LICENSE)

----
