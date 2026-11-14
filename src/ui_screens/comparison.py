from ..ui_components.rotation_cards import render_cards
from ..ui_components.timeline import render_timeline
from ..ui_components.field_selector import field_options
from ..ui_state import get_preferences, update_state, valid_is_current


def _format_static_measurement(key, value, t):
    if value is None:
        return t("not_available")
    if key == "elevation_m" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.2f} m"
    if key == "slope_deg" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.2f}°"
    return str(value)


def _production_rotation_records(records):
    """Project adapter records onto Role 4's approved contract fields only."""
    allowed = ("id", "name_ar", "name_en", "sequence", "is_current")
    safe = []
    if not isinstance(records, list):
        return safe
    for record in records:
        if not isinstance(record, dict) or record.get("is_demo") is True:
            continue
        rotation_id = record.get("id")
        sequence = record.get("sequence")
        if (not isinstance(rotation_id, str) or not rotation_id.strip()
                or not isinstance(sequence, list)
                or not all(isinstance(crop, str) and crop.strip() for crop in sequence)
                or not valid_is_current(record.get("is_current"))
                or any(record.get(key) is not None and not isinstance(record.get(key), str)
                       for key in ("name_ar", "name_en"))):
            continue
        # This second guard matters for injected adapters too: presentation-only
        # fixture flags and unapproved scoring fields never enter production cards.
        safe.append({key: record[key] for key in allowed if key in record})
    return safe


def render(st, t, state, *, preview=False, data=None):
    st.subheader(t("comparison"))
    options = field_options(data.geojson if data else {}, state["language"])
    selected = state["selected_field"]
    if selected not in options:
        st.info(t("select_field"))
        st.button(t("back_to_field"), key="comparison_field_back", on_click=lambda: update_state(st.session_state, screen="field"))
        return
    st.text(f'{t("selected_farm")}: {options[selected]} ({selected})')
    st.caption(t("context_separate"))
    for key, value in data.static.get(selected, {}).items():
        st.text(f'{t(key)}: {_format_static_measurement(key, value, t)}')
    st.markdown(f'**{t("priorities")}**')
    for criterion, value in get_preferences(st.session_state).items():
        st.text(f'{t("priority_" + criterion)}: {value}/5')
    st.caption(t("preference_notice"))
    rotations = _production_rotation_records(data.rotations.get(selected, []))
    if preview:
        from ..ui_mock import demo_rotations, DEMO_LABEL
        rotations = demo_rotations()
        st.warning(DEMO_LABEL)
        st.caption(t("demo_limitations"))
    else:
        st.info(t("scoring_pending"))
    render_cards(st, t, rotations, state["language"], demo=preview)
    st.markdown(f'**{t("timeline_title")}**')
    if rotations:
        for rotation in rotations[:3]:
            st.text(rotation.get(f'name_{state["language"]}') or rotation["id"])
            calendar = rotation.get("calendar_ar") if state["language"] == "ar" else None
            render_timeline(st, t, calendar or rotation.get("calendar"), start_month=rotation.get("calendar_start"), demo=preview)
    else:
        render_timeline(st, t)
    st.info(t("scientific_disclaimer"))
    st.button(t("back_to_priorities"), key="comparison_back",
              on_click=lambda: update_state(st.session_state, screen="priorities"))
