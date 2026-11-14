# Source data

Inputs the prep scripts start from, so every result in `data/` can be rebuilt from this repository.

| File | What it is | Source |
|---|---|---|
| `01_climate_daily.csv` | NASA POWER daily weather, 1998–2025, for the grid cell at 32.55° N, 35.85° E | NASA POWER API, Agroclimatology community (public domain) |
| `02_climate_monthly.csv` | Monthly summaries of the file above | Derived from NASA POWER |
| `08_local_weather_published.csv` | 18 months of temperature and rain measured at the Maru research station | Table 2 of the NARC/JUST study, https://doi.org/10.15159/AR.20.236 |
| `09_nasa_local_comparison.csv` | The station months next to NASA POWER for the same months | Built from the two sources above |
| `06_site.csv` | Station coordinates and elevation, and the elevation of the NASA POWER cell | Same study; NASA POWER response |
| `16_sources.csv` | Source list with links and review dates | – |

The station values are quoted from a published paper for validation, with the citation above. They are 18 monthly
values, not the paper's dataset.

Which script reads what:

- `prep/fetch_power.py` reads `01` and `02` and writes `data/climate_monthly.csv`.
- `prep/validate.py` reads `09` and writes `data/validation.json`.
- `prep/figures.py` reads `09` for the temperature figure.
