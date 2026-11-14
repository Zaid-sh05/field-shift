from ..ui_components.priorities import render_controls
from ..ui_components.field_selector import field_options
from ..ui_state import update_state


def render(st, t, state, *, geojson=None):
    st.subheader(t("priorities"))
    options = field_options(geojson or {}, state["language"])
    selected = state["selected_field"]
    if selected not in options:
        st.info(t("select_field"))
        st.button(t("back_to_field"), key="priorities_back",
                  on_click=lambda: update_state(st.session_state, screen="field"))
        return
    with st.container(border=True, key="role6_card_priorities"):
        st.text(f'{t("selected_farm")}: {options[selected]} ({selected})')
    st.caption(t("preference_notice"))
    st.caption(t("importance_scale"))
    render_controls(st, t)
    st.info(t("mapping_pending"))
    st.button(t("back_to_field"), key="priorities_back",
              on_click=lambda: update_state(st.session_state, screen="field"))
    st.button(t("continue_comparison"), key="priorities_continue",
              on_click=lambda: update_state(st.session_state, screen="comparison"))
