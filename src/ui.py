"""Role 6 integration boundary.

Role 1 may call render_frontend() after st.set_page_config in app.py.
Importing this module neither renders UI nor reads data. ScoringProvider is a
provisional Python injection point, not an amendment to DATA_CONTRACT.md.
Role 5 must confirm its response shape and slider mapping before live wiring.
"""
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .ui_state import init_state, update_state, validate_weights
from .ui_i18n import translate


@dataclass(frozen=True)
class FieldData:
    geojson: dict
    issues: tuple[str, ...] = ()


class DataAdapter(Protocol):
    def load_fields(self) -> FieldData: ...


class FileDataAdapter:
    """Read-only adapter. Preserve field IDs and report malformed/missing input.

    Additional contract files should be adapted when their consumers are ready;
    absent files are never replaced automatically with mock data.
    """
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir is not None else Path(__file__).resolve().parents[1] / "data"

    def load_fields(self) -> FieldData:
        empty = {"type": "FeatureCollection", "features": []}
        try:
            data = json.loads((self.data_dir / "fields.geojson").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return FieldData(empty, (f"fields.geojson: {exc}",))
        if not isinstance(data, dict) or data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
            return FieldData(empty, ("fields.geojson: invalid FeatureCollection",))
        issues, seen = [], set()
        for feature in data["features"]:
            if not isinstance(feature, dict):
                return FieldData(empty, ("fields.geojson: invalid feature",))
            props = feature.get("properties")
            geometry = feature.get("geometry")
            if not isinstance(props, dict) or not isinstance(geometry, dict) or geometry.get("type") != "Polygon" or not geometry.get("coordinates"):
                return FieldData(empty, ("fields.geojson: expected polygon and properties",))
            field_id = props.get("field_id")
            if not isinstance(field_id, str) or not field_id or field_id in seen:
                return FieldData(empty, ("fields.geojson: missing or duplicate field ID",))
            seen.add(field_id)
            if props.get("zone") not in ("valley", "highland", "azraq"):
                issues.append(f"{field_id}: zone outside DATA_CONTRACT")
            for key in ("name_ar", "name_en", "rain_mm"):
                if props.get(key) is None:
                    issues.append(f"{field_id}: {key} unavailable")
        return FieldData(data, tuple(issues))


@dataclass(frozen=True)
class ScoringRequest:
    field_id: str
    weights: Mapping[str, float]

    def __post_init__(self):
        if not isinstance(self.field_id, str) or not self.field_id:
            raise ValueError("A selected field is required")
        # Snapshot caller data so subsequent edits cannot alter the request.
        from types import MappingProxyType
        object.__setattr__(self, "weights", MappingProxyType(validate_weights(self.weights)))


class ScoringProvider(Protocol):
    def evaluate(self, request: ScoringRequest) -> Mapping:
        """Response schema awaits Role 5; Phase 1 does not call this method."""
        ...


def render_frontend(*, adapter: DataAdapter | None = None, preview=False) -> None:
    """Public entry point: render the chosen screen shell, with optional mock layout.

    State is configured through ui_state helpers. No scoring or navigation
    widgets are implemented in Phase 1. Existing Folium maps may be passed to
    ui_components.field_selector.render_map by the integration owner.
    """
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError("Streamlit is required to render the frontend") from exc
    from .ui_screens import field, priorities, comparison
    state = init_state(st.session_state)
    widget_key = "fieldshift_language_selector"
    # Keep the widget in sync when an integrator updates the shared state.
    if st.session_state.get(widget_key) != state["language"]:
        st.session_state[widget_key] = state["language"]

    def change_language():
        update_state(st.session_state, language=st.session_state[widget_key])

    css_path = Path(__file__).resolve().parents[1] / "styles" / "main.css"
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        css = ""
    direction = "rtl" if state["language"] == "ar" else "ltr"
    st.markdown(f'<style>{css}</style><span class="fieldshift-direction" dir="{direction}" lang="{state["language"]}"></span>', unsafe_allow_html=True)
    t = lambda key: translate(key, state["language"])
    st.selectbox(t("language"), ("ar", "en"), format_func=lambda code: {"ar": "العربية", "en": "English"}[code], key=widget_key, on_change=change_language)
    data = (adapter if adapter is not None else FileDataAdapter()).load_fields()
    if data.issues:
        st.warning(t("data_warning"))
        with st.expander(t("data_details")):
            for issue in data.issues:
                st.write(issue)
    if state["screen"] == "field":
        field.render(st, t, data.geojson, state)
    elif state["screen"] == "priorities":
        priorities.render(st, t, state)
    else:
        comparison.render(st, t, state, preview=preview)
