"""Phase 1 placeholder; consumes no unconfirmed scoring output schema."""


def render_placeholders(st, t, slots):
    for _ in slots:
        st.caption(t("result_pending"))
