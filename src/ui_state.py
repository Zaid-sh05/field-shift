"""Pure state helpers; pass st.session_state or a plain dictionary in tests."""
from collections.abc import MutableMapping, Mapping
from copy import deepcopy
from math import isfinite

# Must match src/scoring.py CRITERIA (checked in tests). "effort" was dropped: no data source for it.
CRITERIA = ("water", "risk", "soil", "bare", "income")
SCREENS = ("field", "priorities", "comparison")
KEY = "fieldshift_ui"


def valid_is_current(value) -> bool:
    """DATA_CONTRACT: is_current is true, false or null (unknown until the farmer confirms)."""
    return value is None or type(value) is bool


def init_state(state: MutableMapping) -> dict:
    current = state.get(KEY)
    current = current if isinstance(current, dict) else {}
    selected = current.get("selected_field")
    state[KEY] = {
        "selected_field": selected if isinstance(selected, str) and selected else None,
        "language": current.get("language") if current.get("language") in ("ar", "en") else "ar",
        "screen": current.get("screen") if current.get("screen") in SCREENS else "field",
        "priorities": clean_preferences(current.get("priorities")),
    }
    return deepcopy(state[KEY])


def clean_preferences(values):
    """Recover UI values only. None from Phase 1 migrates to default importance 3."""
    values = values if isinstance(values, Mapping) else {}
    return {key: values.get(key) if type(values.get(key)) is int and 1 <= values[key] <= 5 else 3
            for key in CRITERIA}


def get_preferences(state: MutableMapping) -> dict:
    """Return the farmer's raw 1–5 importance per criterion; src/scoring.py uses them as weights."""
    return init_state(state)["priorities"]


def update_state(state: MutableMapping, **changes) -> dict:
    current = init_state(state)
    if changes.keys() - current.keys():
        raise ValueError("Unknown UI state key")
    candidate = current | deepcopy(changes)
    if candidate["language"] not in ("ar", "en"):
        raise ValueError("Unsupported language")
    if candidate["screen"] not in SCREENS:
        raise ValueError("Unknown screen")
    field = candidate["selected_field"]
    if field is not None and (not isinstance(field, str) or not field):
        raise ValueError("Field ID must be a nonempty string or None")
    validate_weights(candidate["priorities"], allow_unset=True)
    state[KEY] = candidate
    return deepcopy(candidate)


def validate_weights(weights: Mapping, *, allow_unset=False) -> dict:
    """Transport validation only. No normalization or agricultural scoring."""
    if set(weights) != set(CRITERIA):
        raise ValueError("Every scoring criterion must be explicit")
    for value in weights.values():
        if value is None and allow_unset:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise ValueError("Weights must be finite nonnegative numbers")
    return dict(weights)


def select_field(state, field_id, valid_ids):
    if field_id is not None and field_id not in valid_ids:
        raise ValueError("Unknown field ID")
    return update_state(state, selected_field=field_id)
