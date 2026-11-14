# Role 6 Integration Handoff — Phase 6A

## Frontend boundary

- Public entry point: `src.ui.render_frontend(*, adapter=None, preview=False)`.
- Role 1 should call it after `st.set_page_config(...)`.
- The default `FileDataAdapter` reads `fields.geojson`, `field_static.csv`, and an optional `rotations.json` from `data/`. The adapter is read-only and reports malformed or incompatible records through `FieldData.issues`.
- `DataAdapter.load_fields() -> FieldData` is the existing injection boundary. Existing frontend APIs remain unchanged.
- `ScoringProvider.evaluate(ScoringRequest) -> Mapping` is a provisional interface only. The frontend does not invoke it and the mapping is not an approved output schema.

## Current input inventory

| Input | Current status | Integration note |
|---|---|---|
| Field geometry and IDs | Available and verified | `fields.geojson` has three valid polygon features with IDs `maru_1`, `maru_2`, `maru_3`; original IDs/properties are retained. |
| Field zone and rainfall metadata | Available but incompatible/incomplete | All current zones are `maru`, outside the contract enum (`valley`, `highland`, `azraq`); all `rain_mm` values are null. Role 4/Role 1 must resolve this at the source. |
| Static field metadata | Available and verified | `field_static.csv` contains elevation and slope for all three field IDs. These remain separate context values, not scoring results. |
| Satellite observations and field history | Available, not yet adapted into Role 6 | `sat_monthly.csv` and `field_history.csv` exist in the contract's long/season formats. The current adapter does not expose them to the comparison screen or scoring boundary. |
| Climate data | Missing | `climate_monthly.csv` is not present. |
| Crop catalog and soil properties | Missing | `crops.csv` and `soil.json` are not present. |
| Rotation candidates | Missing | `rotations.json` is not present. Its approved fields are `id`, localized names, `sequence`, and `is_current`; malformed and unknown field IDs are rejected/reported. |
| Crop calendars | Contract not yet approved | The current rotation contract has sequences only. It has no calendar start convention, monthly crop/bare values, units, or missing-value semantics. The UI leaves months unknown instead of inferring them. |
| Scoring results and ranking | Missing; output contract not approved | No Role 5 results are available. Define per-rotation metric and aggregate score fields, units/scales, direction, ranking/ties, and error/partial-result behavior before wiring. |
| Confidence | Contract not yet approved | Define what confidence applies to (candidate, metric, or aggregate), representation, method, and missing/unknown behavior. The UI displays “not assessed” when absent. |
| Scientific evidence | Contract not yet approved | Define source identity/citation, period, native resolution, method/provenance, and limitations per result/metric. The UI reports evidence unavailable when absent. |
| Farmer priorities | Available as UI preferences; mapping not approved | Six raw 1–5 values exist: `water`, `bare`, `soil`, `risk`, `income`, `effort`. They are not normalized weights. Role 5 must confirm direction, units, normalization, and any control-to-criterion grouping. |
| Explanations | Missing | `explanations.json` is absent. Its contract provides Arabic/English text by field and rotation, but no current explanation data is available. |

## Role 5 scoring interface questions

Before implementing a provider, Role 5 should confirm:

1. Which inputs are required for one evaluation (field ID, farmer preferences, rotation candidates, source features, and configuration/version identifiers).
2. Whether the six 1–5 UI values are importance ratings or direct weights; how direction, normalization, omitted criteria, and control grouping work.
3. The response shape for each rotation: stable rotation ID, per-criterion values, aggregate result, units/scale, ranking and ties, and whether partial results are allowed.
4. Confidence scope, allowed values or numeric range, interpretation, method, and provenance.
5. Evidence schema and required source metadata (dataset/provider, time period, native resolution, method, citation/source URL, and limitations).
6. Explicit error behavior for unavailable inputs, malformed records, partial scoring, and provider failures. Missing data must not become a zero score or a recommendation.

Do not persist scoring output into shared datasets through the frontend. Adapt approved outputs at the Role 6 boundary only after Role 5 and Role 1 agree on the contract.

## Preview and production behavior

- `preview=True` opts into the isolated `src.ui_mock.demo_rotations()` fixtures; every demo card/calendar has the `DEMO DATA — NOT SCIENTIFIC RESULTS` label. Their crop names, scores, confidence, and January-based layout calendar are synthetic UI fixtures.
- `preview=False` never calls the mock provider. Production rotation records are projected onto the currently approved Role 4 fields, explicitly demo-marked records are ignored, and unapproved score/calendar/confidence/evidence fields are discarded. Missing scores, confidence, and evidence remain visibly unavailable.
- No recommendation is inferred from priorities, sequences, satellite data, or field metadata.

## Known limitations and mismatches

- Current `fields.geojson` has the valid geometry/IDs but `zone="maru"` conflicts with the contract enum and `rain_mm` is missing for all three fields.
- `field_history.csv` follows the listed contract columns, but its documented limitation remains: NDVI cannot distinguish wheat from lentil, and seasons without February–April observations are omitted. It must not be used to claim crop identity for those records.
- Input source/citation metadata is not provided for static measurements in their current CSV schema. `sat_monthly.csv` includes `native_res_m` as required, but source/method provenance is not represented per row in that contract.
- The Role 6 adapter presently exposes geometry, static values, and rotations; it does not load climate, satellite, history, crop, soil, or explanation inputs for scoring.
- The rotation contract does not define a 12-month calendar; Role 4 must supply/approve this before production timeline data can be shown.
- Role 5's output, confidence, evidence, and ranking structures have not been approved. `ScoringProvider` remains unused.

## Role 1 integration procedure

1. Keep `st.set_page_config(...)` before rendering and import `render_frontend` from `src.ui`.
2. Use production mode (`preview=False`, the default) for the deployed app. Do not set preview mode to obtain missing real rotations.
3. Keep the default file adapter for current fields, or inject a `DataAdapter` that preserves contract IDs and returns validated `FieldData` without mixing mock and real values.
4. Wait for Role 4 and Role 5 schemas and Role 1 approval before extending the adapter to calendars or connecting `ScoringProvider`.
5. Keep shared contract changes out of Role 6; request changes through Role 1 if the team approves a schema update.

## Required validation before live integration

- Valid/missing/malformed field and rotation files, unknown/duplicate field IDs, and optional localized names.
- Missing scoring, confidence, evidence, and calendar inputs remain unavailable rather than inferred.
- Production mode excludes preview fixtures and unapproved result fields; preview mode labels every synthetic result.
- Priority values and selected field persist across language changes and reruns.
- Arabic and English rendering for available and missing-data states.
- Role 6 regression suite, `app.py` AppTest, Python syntax/import checks, and `git diff --check`.
