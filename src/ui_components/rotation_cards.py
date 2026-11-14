"""Phase 1 placeholder; consumes no unconfirmed scoring output schema."""


def render_placeholders(st, t, slots):
    for _ in slots:
        st.caption(t("result_pending"))


def render_confidence(st, t, value=None):
    """Display supplied confidence only; unknown values mean not assessed."""
    levels = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    level = value if value in levels else "not_assessed"
    st.text(f'{levels.get(level, "○")} {t("confidence")}: {t("confidence_" + level)}')


def render_evidence(st, t, evidence=None):
    if not evidence:
        st.caption(t("evidence_unavailable"))
        return
    for record in evidence:
        for key in ("dataset", "organization", "period", "resolution", "limitations"):
            st.text(f'{t(key)}: {record.get(key) or t("not_available")}')


def render_cards(st, t, rotations, language, *, demo=False):
    """Presentation dictionaries are internal UI models, not a scoring contract."""
    from ..ui_mock import DEMO_LABEL
    columns = st.columns(3)
    for index, column in enumerate(columns):
        with column, st.container(border=True, key=f"role6_card_rotation_{index}"):
            if demo:
                st.warning(DEMO_LABEL)
            if index >= len(rotations):
                st.text(t("awaiting_rotation"))
                continue
            rotation = rotations[index]
            st.text(rotation.get(f"name_{language}") or rotation["id"])
            st.text(rotation["id"])
            sequence = rotation.get("sequence_ar") if language == "ar" else None
            sequence = sequence or rotation.get("sequence", [])
            st.text(t("crop_sequence") + ": " + (" → ".join(sequence) or t("not_available")))
            if not demo and rotation.get("is_current") is True:
                st.caption(t("current_rotation"))
            st.text(f'{t("score")}: {rotation.get("score") if rotation.get("score") is not None else t("not_available")}')
            if rotation.get("metrics"):
                for label, value in rotation["metrics"].items():
                    st.text(f'{label}: {value if value is not None else t("not_available")}')
            else:
                st.caption(t("metrics_pending"))
            render_confidence(st, t, rotation.get("confidence"))
            render_evidence(st, t, rotation.get("evidence"))
            st.caption(t("demo_limitations") if demo else t("real_limitations"))
