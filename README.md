# Field Shift: Rotation Explorer for Jordanian Farms

> NASA Space Apps Challenge 2026 · Challenge: **Field Shift: Adapting Farms with NASA Data** · Local event: Jordan University of Science and Technology (JUST), 14–15 Nov 2026

**Live app: https://field-shift-maru.streamlit.app**

An Arabic-first decision-support tool for rainfed farms around **Maru, Irbid (northern Jordan)**. A farmer picks a field, sets their priorities, and compares **three crop-rotation strategies side by side**: wheat–wheat, wheat–lentil and wheat–fallow (the rotations tested at Maru in published trials), against the rotation the field is already using. Each strategy comes with a plain-language explanation, a 12-month bare-soil timeline, and a **confidence badge on every number**, so the farmer can see what the satellites actually observed and what is only an estimate.

The tool supports the farmer's judgment. It does not replace the farmer or local agricultural extension officers.

## Why this matters

- More than 90% of Jordan gets under 200 mm of rain a year, and renewable freshwater is about 61 m³ per person per year.
- The Azraq aquifer is pumped at roughly 2.6× its safe yield.
- In January 2022, frost destroyed 30–90% of open-field crops in the Jordan Valley.

Rotation choices that fit the water budget and avoid known heat and frost windows are one of the few levers small farms control.

## Study site: three fields at Maru

Following our mentor's advice to go deep on one area with local data, we focus on Maru, a rainfed cereal area north-east of Irbid with published research-station records (NARC and JUST). We drew three real fields (5–8 ha each) over satellite imagery and pulled 11 years of NASA data for each.

What the data showed:

- **No fallow season in 11 years.** HLS NDVI shows a green winter crop on all three fields in every season from 2015 to 2025. The current practice is continuous winter cropping, which is the baseline we compare against. (NDVI cannot tell wheat from lentil, so the farmer confirms the crop.)
- **NASA temperature runs hot here, and we know why.** The NASA POWER grid cell sits at 149 m; the Maru station is at 589 m. Against 18 months of published station data, the mean-temperature error is 2.37 °C raw and 0.56–0.96 °C after a standard lapse-rate correction (5–7 °C/km). The result holds across the whole range, so it does not depend on one tuned number.
- **Both satellite rainfall products under-count.** NASA POWER and GPM IMERG each show about 22% less rain than the station over the same months, so rainfall is shown with medium confidence.

Numbers are in [`data/validation.json`](data/validation.json), produced by [`prep/validate.py`](prep/validate.py).

## NASA and partner data used

| Dataset | What we take from it | Native resolution | How we use it |
|---|---|---|---|
| NASA POWER (AG community) | Daily Tmax/Tmin, precipitation, radiation, root-zone wetness | ~0.5° | Frost and heat days, reference ET (ET0), water balance |
| HLS (Harmonized Landsat Sentinel-2) | Red and NIR reflectance → NDVI | 30 m | When the field is green or bare, current rotation, bare-soil days |
| SMAP L4 | Root-zone soil moisture | 9 km | Regional drought context and anomalies |
| GPM IMERG | Precipitation | ~0.1° | Independent rainfall check against POWER and the Maru station |
| GRACE / GRACE-FO | Terrestrial water storage | ~3° mascons | Groundwater depletion trend for the basin |
| SRTM | Elevation and slope | 30 m | Per-field elevation for the temperature correction; erosion risk |
| FAO GAEZ, FAO-56, ICARDA | Crop suitability, crop coefficients (Kc), rotation evidence | – | Crop table and rotation rules |
| Maru station (NARC, JUST) | Published monthly temperature and rain, soil | point | Ground truth for checking NASA data |

Every number in the interface shows its source resolution next to it. Coarse products (9 km and up) are labelled **regional context**, not field measurements.

## How it works

```text
prep/ (runs before the demo)          data/ (files, the contract)        app.py (live demo)
──────────────────────────           ──────────────────────────         ─────────────────────
fetch_power.py   ── NASA POWER ──►   climate_monthly.csv      ─┐
gee_export.py    ── HLS, SMAP, ──►   sat_monthly.csv           ├──►  scoring + confidence ──► Streamlit UI (Arabic / English)
                    IMERG, GRACE,    field_history.csv         │     LLM explanations (cached)
                    SRTM             ndvi_monthly_profile.csv  │
validate.py      ── station data ─►  validation.json          ─┤
crop table (FAO, ICARDA) ─────────►  crops.csv, soil.json,    ─┘
                                     rotations.json
```

The live app never calls Earth Engine or a remote API. It reads files only, so it keeps working on bad venue Wi-Fi.

The file formats are fixed in [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md). Change them only through the integration lead.

## Repository layout

```text
app.py                 Streamlit entry point (Role 1 wires it, Role 6 owns the UI)
prep/                  Offline data scripts (Roles 2, 3, 4)
  fetch_power.py       NASA POWER climate, elevation-corrected per field → data/
  gee_export.py        HLS NDVI, SMAP, IMERG, GRACE, SRTM per field → data/
  validate.py          NASA vs Maru station checks → data/validation.json
  features.py          Anomalies, season classification, NDVI monthly profile (pure pandas, self-tested)
data/                  Generated data files + fields.geojson
docs/                  Data contract, research notes
requirements.txt       What the deployed app needs
requirements-prep.txt  Extra packages for the prep scripts (Earth Engine etc.)
```

## Quick start

```bash
git clone https://github.com/Zaid-sh05/field-shift.git
cd field-shift
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

To regenerate the satellite data (Role 3):

```bash
pip install -r requirements-prep.txt
earthengine authenticate
python prep/gee_export.py --project YOUR_GEE_PROJECT
python prep/validate.py --package PATH/TO/Maru_data --project YOUR_GEE_PROJECT
python prep/features.py        # self-check: prints "ok"
```

## Team

| Role | Owner | Owns |
|---|---|---|
| 1. Integration and deployment | Zaid | Repo, `app.py` wiring, deployment, submission page |
| 2. Climate data | Sadeel | NASA POWER, IMERG, frost/heat/ET0 indicators |
| 3. Satellite data | Dr. Hossam | HLS NDVI, SMAP, IMERG, GRACE, SRTM, season classification, validation |
| 4. Agronomy and story | Kosay | Crop table, soil, field choice, rotations, video |
| 5. Scoring and AI | Lana | Multi-criteria scoring, confidence, LLM explanations |
| 6. Interface | Mohammad | Streamlit UI, Arabic RTL, cards and timeline |

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how we work.

## Use of AI

In line with the Space Apps rules, we disclose AI use:

- An LLM writes the plain-language explanations from numbers our scoring engine has already computed. It never picks the recommended rotation.
- AI coding assistants helped with research and with parts of the code.

The final submission page lists the exact tools.

## License

[MIT](LICENSE)

---

### للفريق بالعربي

- **كل واحد بيشتغل بملفاته بس**، على branch باسمه، وبيفتح Pull Request. الدمج على `main` بيعمله الدور 1 بس.
- **شكل الملفات ثابت** ومكتوب بـ `docs/DATA_CONTRACT.md`. إذا بدك تغيّر عمود، احكي مع الدور 1 أول.
- **ممنوع ترفع أي مفتاح API** للـ repo. المفاتيح بتنحط بـ `.streamlit/secrets.toml`، وهاد الملف مستثنى من git.
- **مهامك موجودة كـ Issue** على GitHub باسم دورك.
