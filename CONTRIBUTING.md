# How we work

## Branches and merges

1. Work on a branch named after your role: `role-2-climate`, `role-3-satellite`, and so on.
2. Push and open a Pull Request into `main`. Keep PRs small, ideally one every 2–3 hours.
3. Only Role 1 (integration) merges into `main`. This keeps merge conflicts close to zero.

## File ownership

| Path | Owner |
|---|---|
| `app.py`, `requirements*.txt`, deployment config | Role 1 |
| `prep/fetch_power.py`, `data/climate_monthly.csv` | Role 2 |
| `prep/gee_export.py`, `prep/features.py`, `data/sat_monthly.csv`, `data/field_history.csv`, `data/field_static.csv` | Role 3 |
| `data/fields.geojson`, `data/crops.csv`, `data/soil.json`, `data/rotations.json` | Role 4 |
| `src/scoring.py`, `data/explanations.json` | Role 5 |
| `src/ui.py`, `i18n.json`, styles | Role 6 |

If you need to edit a file you do not own, ask its owner first.

## Rules

- **No secrets in git.** API keys go in `.streamlit/secrets.toml`, which is already in `.gitignore`. If a key is ever pushed, revoke it with the provider right away; deleting the commit is not enough.
- **Follow the data contract.** Formats are fixed in [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md).
- **Every number gets a source.** Crop values need a `source_url`. Satellite values carry `native_res_m`.
- **Use `pathlib` for paths**, never Windows backslashes, so the code runs on the deployment server.
- **Stand-up every 2 hours, 5 minutes:** what you finished, what's next, what's blocking you. If you've been stuck for more than 45 minutes, say so straight away.
