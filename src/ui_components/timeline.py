"""A layout boundary, with no inferred crop calendar or bare-soil estimates."""


def render_placeholder(st, t, months):
    if len(months) != 12:
        raise ValueError("Timeline must contain twelve months")
    st.caption(t("timeline_pending"))


def render_timeline(st, t, months=None, *, start_month=None, demo=False, legend=True):
    """No start date or crop schedule is inferred from a rotation sequence."""
    from html import escape
    from ..ui_mock import DEMO_LABEL
    values = list(months) if months is not None else [None] * 12
    if len(values) != 12:
        raise ValueError("Timeline must contain twelve months")
    if start_month is not None and (type(start_month) is not int or not 1 <= start_month <= 12):
        raise ValueError("Invalid calendar start")
    if demo:
        st.warning(DEMO_LABEL)
    if start_month is None:
        st.caption(t("calendar_start_unknown"))
    cells = []
    for index, value in enumerate(values):
        label = t(f"month_{(start_month - 1 + index) % 12 + 1}") if start_month else f'{t("month_slot")} {index + 1}'
        cells.append(f'<div class="fs-month"><strong>{escape(label)}</strong><br>{escape(str(value) if value else t("calendar_missing"))}</div>')
    st.markdown('<div class="fs-timeline">' + "".join(cells) + '</div>', unsafe_allow_html=True)
    if legend:
        st.caption(t("timeline_legend"))
