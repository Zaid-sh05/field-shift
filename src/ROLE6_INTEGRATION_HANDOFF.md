# Role 6 integration notes

- Entry point: `src.ui.render_frontend(*, adapter=None, preview=False)`, called from `app.py` after `st.set_page_config`.
- `preview=True` shows synthetic demo cards, each labelled `DEMO DATA — NOT SCIENTIFIC RESULTS`. The deployed app never uses it.
- Production flow: field screen (map, satellite evidence) → priorities (five sliders) → comparison (scored cards, calendar).
- Scores come from `src/scoring.py`. The five sliders are the engine's criteria (`CRITERIA` in `src/ui_state.py` and `src/scoring.py`, kept equal by a test) and are passed to `scoring.evaluate()` as weights.
- If the rotations on screen are not exactly the ones the engine can score, the cards fall back to the unscored layout instead of showing partial results.
- `src/ui_components/evidence.py` reads `sat_monthly.csv`, `field_history.csv`, `soil.json` and `validation.json`. It imports pandas lazily, so every Role 6 module still imports without third-party packages.
- All user-facing text lives in `i18n.json` (Arabic and English keys must match; a test checks this).
- Tests: `python -m pytest tests`.
