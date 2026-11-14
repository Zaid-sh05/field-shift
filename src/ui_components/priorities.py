"""Configurable mapping boundary; grouping requires explicit values for all criteria."""
from ..ui_state import validate_weights


def resolve_weights(values, mapping):
    """mapping: criterion -> control ID. No implicit grouping or hidden defaults.

    Multiple criteria may reference one control only when Role 5 approves that
    mapping. Six criteria must be represented even with three to five controls.
    """
    weights = {criterion: values[control] for criterion, control in mapping.items()}
    return validate_weights(weights)
