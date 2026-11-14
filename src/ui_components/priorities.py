"""Configurable mapping boundary; grouping requires explicit values for all criteria."""
from ..ui_state import validate_weights
from ..ui_state import CRITERIA, get_preferences, update_state



def render_controls(st, t):
    def render_slider(criterion):
        key = f"fieldshift_priority_{criterion}"
        value = get_preferences(st.session_state)[criterion]
        if st.session_state.get(key) != value:
            st.session_state[key] = value

        def changed():
            preferences = get_preferences(st.session_state)
            preferences[criterion] = st.session_state[key]
            update_state(st.session_state, priorities=preferences)

        st.slider(t(f"priority_{criterion}"), min_value=1, max_value=5, step=1,
                  key=key, on_change=changed)

    for criterion in CRITERIA:
        render_slider(criterion)


def resolve_weights(values, mapping):
    """mapping: criterion -> control ID. No implicit grouping or hidden defaults.

    Multiple criteria may reference one control only when Role 5 approves that
    mapping. Six criteria must be represented even with three to five controls.
    """
    weights = {criterion: values[control] for criterion, control in mapping.items()}
    return validate_weights(weights)
