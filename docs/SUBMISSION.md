# Submission drafts (NASA Space Apps 2026)

Final text for the submission page. Every section is filled in; copy each one into the matching field.
Deadline: **Sunday 15 Nov 2026, 11:59 PM**.

---

## 1. High-level summary

Field Shift is an Arabic-first crop-rotation explorer for rainfed farms around Maru, Irbid, in northern Jordan, one of the most water-scarce countries on Earth. A farmer picks their field, sets what matters to them, and compares three rotations side by side (wheat–wheat, wheat–lentil, wheat–fallow) against what the field is already doing.

The current rotation is not guessed: 11 years of NASA HLS satellite imagery show that our three study fields were never left fallow: in 31 of 33 field-seasons since 2015 they carried a clear winter crop, and the other 2 were borderline green, never bare. Every number the farmer sees carries a confidence badge, because we tested NASA data against the ground before trusting it. Near Maru, NASA POWER temperatures ran 2.4 °C too warm because its grid cell sits 440 m lower than the farm. We corrected for elevation and cut the error by two thirds. Satellite rainfall still misses about 22% of local rain, so the tool says so. The same data shows why this matters now: 2024–25 was the driest season in 27 years, 55% below normal, and the satellites watched the crop's greenness fall by almost half.

The tool supports the farmer's decision. It does not make it.

## 2. Project demo

Seven-slide deck (PowerPoint): https://zaid-sh05.github.io/field-shift/Field_Shift_Pitch_Deck.pptx

The deck is built by `prep/deck/build_deck.py`. Figures behind it, in `docs/figures/`:

- `ndvi_history.png`: 11 years of NDVI for the three fields (no fallow year)
- `temperature_check.png`: station vs NASA POWER, raw and elevation-corrected
- `rain_check.png`: station vs NASA POWER vs GPM IMERG rainfall
- `drought_2025.png`: season rain and crop greenness, 2016–2025 (the 2024–25 drought)

## 3. Final project link

- Live app: https://zaid-sh05.github.io/field-shift/
- Earlier Streamlit version: https://field-shift-maru.streamlit.app
- Code and data: https://github.com/Zaid-sh05/field-shift

## 4. Project details

**What makes it different.** Crop-comparison tools exist, and most take satellite data as the truth. Ours starts by testing it:

- *Checked against the ground.* NASA POWER read 2.4 °C too warm at Maru because its grid cell sits 440 m lower than the station. We corrected for elevation and cut the error by two thirds. Both NASA rainfall products miss about 22% of local rain, and the tool says so.
- *Confidence on every score.* The farmer sees what satellites observed on the field and what is a regional estimate or a rule.
- *The current rotation read from space.* Eleven years of imagery show no fallow season, so wheat–fallow is ruled out without asking the farmer.
- *Testable.* A replay of 27 real seasons and a what-if simulator show when the ranking holds and when it does not.
- *It ranks, it does not decide.* The order follows the farmer's priorities, and close calls are flagged.

**What it does.** For each field, the app shows:

- the rotation the field is using today, read from satellite vegetation history;
- what the satellites saw on the field: 11 years of greenness, the crop history, season rain, the 2024–25 drought, and soil;
- three rotations scored on the farmer's own priorities, set with five sliders;
- for every criterion, one plain sentence with the numbers behind the score;
- a month-by-month calendar of crop and bare soil for each season of the rotation;
- a panel showing how NASA data compared with the ground station;
- a what-if simulator: move the rain and temperature sliders and the scores, the ranking and the advice update, labelled as a scenario and not a forecast;
- a backtest: how each rotation would have held up in each of the 27 real seasons, including the 2024–25 drought;
- a next-season advisor: the farmer enters the last three seasons' crops and gets the options ranked, with the rotation rules each one meets and the odds from the record;
- an expected crop-vigour estimate from a small model trained on our own NASA data, shown with its error;
- a confidence badge on every number: high for field-scale satellite data, medium for regional data checked against the ground, low for assumptions and reference values.

**How it works.**

1. *Fields.* We drew three real rainfed fields near Maru (5–8 ha each) over satellite imagery, inside the field and away from roads, houses and olive groves.
2. *Satellite data (Google Earth Engine).* For every field we extract monthly series for 2015–2025:
   - HLS (Landsat 8/9 and Sentinel-2) cloud-masked NDVI at 30 m;
   - SMAP L4 root-zone soil moisture;
   - GPM IMERG rainfall;
   - GRACE/GRACE-FO water storage;
   - SRTM elevation and slope.
3. *Climate (NASA POWER).* We use 28 years of daily weather and correct temperature for each field's real elevation from SRTM. From that we derive frost days, heat days, dry spells and water-balance inputs.
4. *Ground check.* We compare NASA data with 18 months of published weather from the Maru research station (NARC/JUST):
   - Temperature error drops from 2.37 °C to 0.56–0.96 °C after the elevation correction. The range covers any lapse rate from 5 to 7 °C/km, so the result does not hinge on one tuned number.
   - NASA POWER and IMERG both under-count rain by about 22%.
5. *Season reading.* A rule-based classifier labels each field-season from NDVI as winter crop, irrigated summer, fallow or uncertain. NDVI cannot tell wheat from lentil, so the farmer confirms the crop.
6. *Scoring.* Five criteria, each a physical quantity or a counted practice rather than a fitted number:
   - *Saving water:* the share of crop water demand that rain covers, averaged over 27 seasons. Demand is FAO-56 Penman-Monteith evapotranspiration from NASA POWER, times FAO-56 crop coefficients.
   - *Holding up in dry years:* the same share in the driest fifth of seasons only.
   - *Soil health:* practices present out of two (a legume in the rotation; no cereal directly after the same cereal).
   - *Soil cover:* months a year the field is green, as HLS observed it on that field. A fallow year counts as bare.
   - *Harvests:* the share of seasons that end in a harvest. We assume no prices or yields.

   The farmer's sliders are the weights. The app flags a close call when the top two are within 5 points or when a 10% change in one weight flips the order, and it warns when the farmer's top priority rests on low-confidence data. It ranks; it never recommends.
7. *Interface.* A React single-page site, Arabic right-to-left with an English switch, built for phones first. It ships with every result precomputed by the Python engine, so it needs no server and keeps working on weak internet; a test checks the site's JavaScript against the Python engine on 36 reference cases.

**Tools.** Python, Google Earth Engine, pandas, React, Vite, Leaflet, Streamlit, matplotlib, pytest, GitHub Pages.

**Goals.**

- Give smallholders a fair comparison of rotations using free NASA data.
- Be honest about how far each number can be trusted.
- Show a method that any extension office could repeat for another village.

**Limits we state openly.**

- One site and three fields.
- An 18-month ground check, which is a check, not a calibration.
- No field-level soil measurements: we show the published Maru profile as a low-confidence reference.
- Heat and frost days are not verified against local records, so no score is built on them.
- Daily maximum and minimum temperature feed the crop water demand (FAO-56 Penman-Monteith) and were not checked against ground data; only the mean was. This limits confidence in the water and dry-year scores, which is why they carry medium confidence.
- Crop water demand is potential demand for a well-watered crop, and NASA rain reads low here, so the water scores are conservative.
- The harvest count is not income: we have no local prices, costs or yields.
- The vigour model is small (11 seasons on three fields that share one rain series) and sees rain only. It is a modest aid, not a yield forecast.
- Scenarios shift the observed record; they are not climate projections. They change the water and dry-year scores only.
- NDVI cannot tell wheat from lentil, so the satellite history rules out wheat–fallow as the current rotation but cannot choose between the other two.

## 5. Use of NASA data and AI

### NASA data

| Dataset | Earth Engine / API ID | Used for |
|---|---|---|
| HLS Landsat 30 m (HLSL30 v2.0) | `NASA/HLS/HLSL30/v002` | NDVI, crop history, bare-soil months |
| HLS Sentinel-2 30 m (HLSS30 v2.0) | `NASA/HLS/HLSS30/v002` | NDVI, crop history, bare-soil months |
| SMAP L4 soil moisture | `NASA/SMAP/SPL4SMGP/008` | Root-zone moisture context |
| GPM IMERG V07 monthly | `NASA/GPM_L3/IMERG_MONTHLY_V07` | Rainfall, cross-check with POWER and station |
| GRACE/GRACE-FO mascons (JPL) | `NASA/GRACE/MASS_GRIDS_V04/MASCON` | Regional water-storage trend |
| SRTM 30 m | `USGS/SRTMGL1_003` | Field elevation (temperature correction), slope |
| NASA POWER (Agroclimatology) | power.larc.nasa.gov API | Daily temperature, rain, radiation, humidity, wind, soil wetness, 1998–2025 |

### AI

- **Claude (Anthropic)** helped with research and preparation, with writing and reviewing data-processing code, with analysis (the elevation check, validation and figures), and with drafting documentation. The team reviewed and ran all code.
- **ChatGPT / Codex (OpenAI)** helped a teammate assemble the Maru data package from published sources.
- **The app runs no generative AI.** Scores and advice come from a transparent rule-based engine, and the sentences on screen are fixed templates filled with its numbers. Nothing in the app recommends a rotation.
- **One small statistical model is trained on our own data:** a least-squares line that predicts the winter greenness peak (HLS NDVI) from season rain (NASA POWER), fitted on 33 field-seasons. Correlation 0.53. On seasons held out of training its error is 0.12 NDVI, against 0.15 for always guessing the mean. The app shows that error next to every estimate.
- The 30-second video uses AI-generated illustrative footage (Google Flow), labelled as such on screen.
- No AI-generated data is presented as measurement. Every number traces to a NASA dataset or a cited publication.

## 6. References

**NASA and satellite data**

- NASA POWER API, Agroclimatology community. https://power.larc.nasa.gov/docs/services/api/
- Harmonized Landsat Sentinel-2 (HLS) v2.0, NASA LP DAAC. https://lpdaac.usgs.gov/products/hlsl30v002/ and https://lpdaac.usgs.gov/products/hlss30v002/
- SMAP L4 Global 3-hourly Surface and Root Zone Soil Moisture (SPL4SMGP v8), NASA NSIDC DAAC. https://nsidc.org/data/spl4smgp
- GPM IMERG Final Run V07, NASA GES DISC. https://gpm.nasa.gov/data/imerg
- GRACE/GRACE-FO JPL mascons RL06. https://grace.jpl.nasa.gov/
- NASA SRTM Version 3 (SRTMGL1). https://lpdaac.usgs.gov/products/srtmgl1v003/
- MERRA-2 FAQ (soil wetness in POWER). https://gmao.gsfc.nasa.gov/gmao-products/merra-2/faq_merra-2/

**Other data and tools**

- ECMWF ERA5-Land daily aggregates (used only to cross-check heat days). `ECMWF/ERA5_LAND/DAILY_AGGR`
- SoilGrids 250 m v2.0, ISRIC (soil per field). https://soilgrids.org/ · `projects/soilgrids-isric`
- Google Earth Engine. https://earthengine.google.com/

**Local and agronomic sources**

- Maru station weather and soil, NARC/JUST study. https://doi.org/10.15159/AR.20.236
- Maru rotation trials (wheat–wheat, wheat–lentil, wheat–fallow), IAEA TECDOC-1468. https://www-pub.iaea.org/MTCD/Publications/PDF/te_1468_web.pdf
- FAO Irrigation and Drainage Paper 56: Penman-Monteith reference evapotranspiration, crop coefficients (Table 12) and growth-stage lengths (Table 11). https://www.fao.org/4/x0490e/x0490e00.htm
- FAO crop water needs. https://www.fao.org/4/s2022e/s2022e02.htm
- FAO crop rotation guidance. https://www.fao.org/4/Y5146E/y5146e0a.htm

**Challenge**

- Space Apps 2026, Field Shift: Adapting Farms with NASA Data. https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
