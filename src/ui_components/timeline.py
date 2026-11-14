"""A layout boundary, with no inferred crop calendar or bare-soil estimates."""


def render_placeholder(st, t, months):
    if len(months) != 12:
        raise ValueError("Timeline must contain twelve months")
    st.caption(t("timeline_pending"))
