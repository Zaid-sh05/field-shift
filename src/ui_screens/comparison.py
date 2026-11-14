from ..ui_mock import mock_preview
from ..ui_components.rotation_cards import render_placeholders
from ..ui_components.timeline import render_placeholder


def render(st, t, state, *, preview=False):
    st.subheader(t("comparison"))
    st.info(t("scoring_pending"))
    if preview:
        mock = mock_preview()
        st.warning(mock.label)
        render_placeholders(st, t, mock.card_slots)
        render_placeholder(st, t, mock.months)
