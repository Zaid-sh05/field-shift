from ..ui_components.rotation_cards import render_cards, render_scored_cards
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


def _scenario_controls(st, t, rotations, language):
    """What-if sliders and the farmer's own answer about the current rotation. Returns (rain_factor, warming, current)."""
    with st.container(border=True, key="role6_card_scenario"):
        st.markdown(f'**{t("scenario_title")}**')
        a, b = st.columns(2)
        rain = a.slider(t("scenario_rain"), min_value=-50, max_value=20, value=0, step=10, format="%d%%",
                        key="fieldshift_scenario_rain")
        warming = b.slider(t("scenario_warming"), min_value=0.0, max_value=3.0, value=0.0, step=0.5, format="+%.1f °C",
                           key="fieldshift_scenario_warming")
        if rain or warming:
            st.warning(t("scenario_note").format(rain=rain, warming=warming))
        else:
            st.caption(t("scenario_hint"))
    # Satellites ruled some rotations out (is_current false); only the farmer can settle the rest.
    possible = [r for r in rotations if r.get("is_current") is not False]
    names = {r["id"]: r.get(f"name_{language}") or r["id"] for r in possible}
    current = st.selectbox(t("current_question"), [None, *names], key="fieldshift_current_rotation",
                           format_func=lambda rid: names.get(rid, t("current_unsure")))
    return 1 + rain / 100, warming, current


def _score(field_id, preferences, rotations, rain_factor=1.0, warming_c=0.0):
    """Scores for the rotations on screen, or None when the engine's data does not cover exactly these."""
    from .. import scoring
    try:
        result = scoring.evaluate(field_id, preferences, rain_factor, warming_c)
    except (ValueError, KeyError, OSError):
        return None
    return result if {r["id"] for r in rotations} == {r["id"] for r in result["rotations"]} else None


def _render_replay(st, t, field_id, rotations, language):
    """How each rotation would have held up in every real season on record."""
    from .. import scoring
    replay = scoring.season_replay(field_id)
    names = {r["id"]: r.get(f"name_{language}") or r["id"] for r in rotations}
    st.markdown(f'**{t("replay_title")}**')
    st.line_chart({names[rid]: {f"{year - 1}-{str(year)[2:]}": row[rid] for year, row in replay.items()}
                   for rid in names}, height=260, y_label=t("replay_axis"))
    worst = min(replay, key=lambda year: min(replay[year].values()))
    st.caption(t("replay_note").format(n=len(replay), season=f"{worst - 1}–{str(worst)[2:]}", values=" · ".join(
        f"{names[rid]} {replay[worst][rid]}%" for rid in names)))


def _render_scored(st, t, state, rotations, result, current=None):
    from .. import scoring
    render_scored_cards(st, t, rotations, result, state["language"], current=current)
    _render_replay(st, t, result["field_id"], rotations, state["language"])
    st.markdown(f'**{t("timeline_title")}**')
    by_id = {r["id"]: r for r in rotations}
    for scored in result["rotations"]:
        rotation = by_id[scored["id"]]
        st.text(rotation.get(f'name_{state["language"]}') or rotation["id"])
        for number, slots in enumerate(scoring.crop_calendar(rotation["sequence"]), 1):
            st.caption(t("season_n").format(n=number) + ": " + t(f"crop_{rotation['sequence'][number - 1]}"))
            render_timeline(st, t, [t(f"crop_{crop}") if crop else t("bare_soil") for crop in slots],
                            start_month=10, legend=False)
    st.caption(t("timeline_legend"))
    st.info(t("scientific_disclaimer"))
    st.button(t("back_to_priorities"), key="comparison_back",
              on_click=lambda: update_state(st.session_state, screen="priorities"))


def render(st, t, state, *, preview=False, data=None):
    st.subheader(t("comparison"))
    options = field_options(data.geojson if data else {}, state["language"])
    selected = state["selected_field"]
    if selected not in options:
        st.info(t("select_field"))
        st.button(t("back_to_field"), key="comparison_field_back", on_click=lambda: update_state(st.session_state, screen="field"))
        return
    st.text(f'{t("selected_farm")}: {options[selected]}')
    for key, value in data.static.get(selected, {}).items():
        st.text(f'{t(key)}: {_format_static_measurement(key, value, t)}')
    preferences = get_preferences(st.session_state)
    st.caption(t("priorities") + ": " + " · ".join(f'{t("priority_" + c)} {v}/5' for c, v in preferences.items()))
    rotations = _production_rotation_records(data.rotations.get(selected, []))
    if preview:
        from ..ui_mock import demo_rotations, DEMO_LABEL
        rotations = demo_rotations()
        st.warning(DEMO_LABEL)
        st.caption(t("demo_limitations"))
    else:
        rain_factor, warming, current = _scenario_controls(st, t, rotations, state["language"])
        result = _score(selected, preferences, rotations, rain_factor, warming)
        if result:
            _render_scored(st, t, state, rotations, result, current)
            return
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
