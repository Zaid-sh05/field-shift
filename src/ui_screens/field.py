from ..ui_components.field_selector import field_options


def render(st, t, geojson, state):
    st.subheader(t("field"))
    options = field_options(geojson, state["language"])
    if not options:
        st.info(t("no_fields"))
    elif state["selected_field"] not in options:
        st.info(t("select_field"))
    else:
        st.caption(options[state["selected_field"]])
