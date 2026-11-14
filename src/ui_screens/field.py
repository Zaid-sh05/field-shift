from ..ui_components.field_selector import field_options, build_map, render_map
from ..ui_components.evidence import render_field_evidence
from ..ui_state import select_field, update_state


def render(st, t, geojson, state, *, static=None):
    st.subheader(t("field"))
    options = field_options(geojson, state["language"])
    if not options:
        st.info(t("no_fields"))
        st.button(t("continue"), disabled=True, key="fieldshift_continue")
        return
    selected = state["selected_field"]
    if selected not in options:
        selected = None
        select_field(st.session_state, None, options)
    key = "fieldshift_field_selector"
    if st.session_state.get(key) != selected:
        st.session_state[key] = selected

    
def changed():
    field_id = st.session_state.get(key)

    print("SELECTED ID:", repr(field_id))
    print("VALID IDS:", [repr(x) for x in options.keys()])
    print("SELECTED TYPE:", type(field_id))
    print("VALID ID TYPES:", [type(x) for x in options.keys()])

    select_field(st.session_state, field_id, options)


    select_field(st.session_state, field_id, options)

    st.selectbox(t("choose_field"), [None, *options], format_func=lambda fid: options.get(fid, t("select_field")), key=key, on_change=changed)
    st.caption(t("geometry_source"))
    result = render_map(build_map(geojson, selected, state["language"]))
    if isinstance(result, dict) and result.get("available") is False:
        st.warning(t("map_unavailable"))
    if selected:
        measurements = (static or {}).get(selected, {})
        with st.container(border=True, key="role6_card_field"):
            st.markdown(f'**{options[selected]}**')
            for name, unit in (("elevation_m", "m"), ("slope_deg", "°")):
                value = measurements.get(name)
                st.text(f'{t(name)}: {value:.2f} {unit}' if value is not None else f'{t(name)}: {t("not_available")}')
            st.caption(t("static_source"))
            render_field_evidence(st, t, selected)
    st.button(t("continue"), key="fieldshift_continue", disabled=selected is None,
              on_click=lambda: update_state(st.session_state, screen="priorities"))
