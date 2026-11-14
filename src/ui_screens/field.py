from ..ui_components.field_selector import field_options, build_map, render_map
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
        select_field(st.session_state, st.session_state[key], options)

    st.selectbox(t("choose_field"), [None, *options], format_func=lambda fid: options.get(fid, t("select_field")), key=key, on_change=changed)
    st.caption(t("geometry_source"))
    result = render_map(build_map(geojson, selected, state["language"]))
    if isinstance(result, dict) and result.get("available") is False:
        st.warning(t("map_unavailable"))
    if selected:
        props = next(f["properties"] for f in geojson["features"] if f["properties"]["field_id"] == selected)
        measurements = (static or {}).get(selected, {})
        with st.container(border=True):
            st.markdown(f'**{t("selected_farm")}**')
            for label, value in (("field_id", selected), ("field_name", options[selected]), ("zone", props.get("zone"))):
                st.text(f'{t(label)}: {value if value is not None else t("not_available")}')
            for name, unit in (("elevation_m", "m"), ("slope_deg", "°")):
                value = measurements.get(name)
                st.text(f'{t(name)}: {value:.2f} {unit}' if value is not None else f'{t(name)}: {t("not_available")}')
            st.caption(t("static_source"))
            st.caption(t("observations_notice"))
    st.button(t("continue"), key="fieldshift_continue", disabled=selected is None,
              on_click=lambda: update_state(st.session_state, screen="priorities"))
