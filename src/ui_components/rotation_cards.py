
"""Phase 1 placeholder; consumes no unconfirmed scoring output schema."""


def render_placeholders(st, t, slots):
    for _ in slots:
        st.caption(t("result_pending"))


def render_confidence(st, t, value=None):
    """Display supplied confidence only; unknown values mean not assessed."""
    levels = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    level = value if value in levels else "not_assessed"
    st.text(
        f'{levels.get(level, "○")} '
        f'{t("confidence")}: {t("confidence_" + level)}'
    )


def render_evidence(st, t, evidence=None):
    if not evidence:
        st.caption(t("evidence_unavailable"))
        return

    for record in evidence:
        for key in (
            "dataset",
            "organization",
            "period",
            "resolution",
            "limitations",
        ):
            st.text(
                f'{t(key)}: {record.get(key) or t("not_available")}'
            )


CURRENT_KEYS = {
    True: "current_rotation",
    False: "not_current_rotation",
    None: "current_rotation_unknown",
}


def criterion_detail(t, criterion, values):
    """One plain sentence with the numbers behind a criterion score."""

    score = round(values["score"])

    if criterion == "water":
        pairs = " · ".join(
            t("water_pair").format(
                crop=t(f"crop_{crop}"),
                demand=values["demand_mm"][crop],
                rain=values["rain_mm"][crop],
            )
            for crop in sorted(values["demand_mm"])
        )
        return t("detail_water").format(
            score=score,
            pairs=pairs,
        )

    if criterion == "risk":
        return t("detail_risk").format(
            score=score,
            dry=values["dry_seasons"],
            n=values["seasons"],
        )

    if criterion == "soil":
        mark = lambda ok: "✓" if ok else "✗"
        return t("detail_soil").format(
            n=values["legume"] + values["no_repeat"],
            legume=mark(values["legume"]),
            no_repeat=mark(values["no_repeat"]),
        )

    if criterion == "bare":
        return t("detail_bare").format(
            months=values["green_months"]
        )

    return t("detail_harvest").format(
        harvests=values["harvests"],
        of=values["of"],
    )


def render_scored_cards(st, t, rotations, result, language):
    """Cards ranked by the farmer's priorities. Every score shows its numbers, confidence and source."""

    from .evidence import badge

    by_id = {r["id"]: r for r in rotations}
    name = lambda rid: by_id[rid].get(f"name_{language}") or rid

    columns = st.columns(len(result["rotations"]))

    for index, (column, scored) in enumerate(
        zip(columns, result["rotations"])
    ):
        rotation = by_id[scored["id"]]
        criteria = scored["criteria"]

        with column, st.container(
            border=True,
            key=f"role6_card_rotation_{index}",
        ):
            st.caption(t("rank_n").format(n=index + 1))
            st.markdown(f"### {name(scored['id'])}")
            st.metric(t("score"), f"{scored['total']:.0f} / 100")
            st.caption(t(CURRENT_KEYS[rotation.get("is_current")]))

            ordered = sorted(
                criteria,
                key=lambda c: criteria[c]["score"],
            )

            st.text(
                t("strongest").format(
                    a=t(f"priority_{ordered[-1]}"),
                    b=t(f"priority_{ordered[0]}"),
                )
            )

            for criterion, values in criteria.items():
                st.progress(
                    values["score"] / 100,
                    text=(
                        f"{t('priority_' + criterion)}: "
                        f"{values['score']:.0f}"
                    ),
                )

                st.caption(
                    f"{criterion_detail(t, criterion, values)} "
                    f"{badge(t, values['confidence'])}"
                )

            with st.expander(t("sources")):
                for criterion in criteria:
                    st.caption(
                        f"{t('priority_' + criterion)}: "
                        f"{t('source_' + criterion)}"
                    )

    st.success(
        t("top_by_priorities").format(
            name=name(result["rotations"][0]["id"])
        )
    )

    if result["close_call"]:
        st.warning(t("close_call"))

    if result["low_confidence_top"]:
        st.warning(t("low_conf_top"))


def render_cards(st, t, rotations, language, *, demo=False):
    """Presentation dictionaries are internal UI models, not a scoring contract."""

    from ..ui_mock import DEMO_LABEL

    columns = st.columns(3)

    for index, column in enumerate(columns):
        with column, st.container(
            border=True,
            key=f"role6_card_rotation_{index}",
        ):
            if demo:
                st.warning(DEMO_LABEL)

            if index >= len(rotations):
                st.text(t("awaiting_rotation"))
                continue

            rotation = rotations[index]

            st.text(
                rotation.get(f"name_{language}") or rotation["id"]
            )
            st.text(rotation["id"])

            sequence = (
                rotation.get("sequence_ar")
                if language == "ar"
                else None
            )
            sequence = sequence or rotation.get("sequence", [])

            st.text(
                t("crop_sequence")
                + ": "
                + (" → ".join(sequence) or t("not_available"))
            )

            if not demo and "is_current" in rotation:
                st.caption(
                    t(
                        {
                            True: "current_rotation",
                            False: "not_current_rotation",
                        }.get(
                            rotation["is_current"],
                            "current_rotation_unknown",
                        )
                    )
                )

            st.text(
                f'{t("score")}: '
                f'{rotation.get("score") if rotation.get("score") is not None else t("not_available")}'
            )

            if rotation.get("metrics"):
                for label, value in rotation["metrics"].items():
                    st.text(
                        f'{label}: '
                        f'{value if value is not None else t("not_available")}'
                    )
            else:
                st.caption(t("metrics_pending"))

            render_confidence(
                st,
                t,
                rotation.get("confidence"),
            )

            render_evidence(
                st,
                t,
                rotation.get("evidence"),
            )

            st.caption(
                t("demo_limitations")
                if demo
                else t("real_limitations")
            )
