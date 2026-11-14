"""Role 6 integration boundary.

Role 1 may call render_frontend() after st.set_page_config in app.py.
Importing this module neither renders UI nor reads data. ScoringProvider is a
provisional Python injection point, not an amendment to DATA_CONTRACT.md.
Role 5 must confirm its response shape and slider mapping before live wiring.
"""
import json
import csv
from math import isfinite
from collections.abc import Mapping
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Protocol

from .ui_state import init_state, update_state, validate_weights
from .ui_i18n import translate


@dataclass(frozen=True)
class FieldData:
    geojson: dict
    issues: tuple[str, ...] = ()
    static: dict = dataclass_field(default_factory=dict)


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
        from .ui_components.field_selector import valid_polygon
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
            if not isinstance(props, dict) or not valid_polygon(geometry):
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
        static = {}
        try:
            with (self.data_dir / "field_static.csv").open(encoding="utf-8", newline="") as handle:
                rows = csv.DictReader(handle)
                if not {"field_id", "elevation_m", "slope_deg"}.issubset(rows.fieldnames or []):
                    raise ValueError("missing static columns")
                duplicates = set()
                for row in rows:
                    fid = row.get("field_id")
                    if fid not in seen:
                        issues.append("field_static.csv: unknown field ID")
                        continue
                    if fid in static or fid in duplicates:
                        static.pop(fid, None)
                        duplicates.add(fid)
                        issues.append(f"{fid}: duplicate static metadata")
                        continue
                    values = {}
                    for key in ("elevation_m", "slope_deg"):
                        try:
                            value = float(row.get(key))
                            if not isfinite(value) or value == -999 or (key == "slope_deg" and not 0 <= value <= 90):
                                raise ValueError("invalid measurement")
                            values[key] = value
                        except (TypeError, ValueError):
                            values[key] = None
                    static[fid] = values
        except (OSError, ValueError, csv.Error) as exc:
            issues.append(f"field_static.csv: {exc}")
        return FieldData(data, tuple(issues), static)


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
        field.render(st, t, data.geojson, state, static=data.static)
    elif state["screen"] == "priorities":
        priorities.render(st, t, state)
    else:
        comparison.render(st, t, state, preview=preview)
