"""Pure state helpers; pass st.session_state or a plain dictionary in tests."""
from collections.abc import MutableMapping, Mapping
from copy import deepcopy
from math import isfinite

CRITERIA = ("water", "bare", "soil", "risk", "income", "effort")
SCREENS = ("field", "priorities", "comparison")
KEY = "fieldshift_ui"


def init_state(state: MutableMapping) -> dict:
    if KEY not in state:
        state[KEY] = {"selected_field": None, "language": "ar",
                      "priorities": dict.fromkeys(CRITERIA), "screen": "field"}
    return deepcopy(state[KEY])


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
        raise ValueError("All six scoring criteria must be explicit")
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
