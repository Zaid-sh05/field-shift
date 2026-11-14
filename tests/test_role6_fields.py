"""Farm selection tests use repository data; they do not write shared files."""
import json
import tempfile
import unittest
from pathlib import Path

from src.ui import FileDataAdapter
from src.ui_state import select_field, init_state, update_state, KEY, CRITERIA
from src.ui_components.field_selector import valid_polygon, field_options, build_map

ROOT = Path(__file__).resolve().parents[1]


class FieldTests(unittest.TestCase):
    def test_real_fields_and_geometry(self):
        data = FileDataAdapter().load_fields()
        self.assertEqual(set(field_options(data.geojson)), {"maru_1", "maru_2", "maru_3"})
        self.assertTrue(all(valid_polygon(f["geometry"]) for f in data.geojson["features"]))
        self.assertEqual(set(data.static), {"maru_1", "maru_2", "maru_3"})

    def test_invalid_geometry(self):
        for geometry in (None, {}, {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [2, 2]]]},
                         {"type": "Polygon", "coordinates": [[[0, 0], [999, 1], [2, 2], [0, 0]]]}):
            self.assertFalse(valid_polygon(geometry))

    def test_invalid_selection_is_rejected(self):
        state = {}
        select_field(state, "maru_1", {"maru_1"})
        with self.assertRaises(ValueError):
            select_field(state, "invented", {"maru_1"})
        self.assertEqual(init_state(state)["selected_field"], "maru_1")
        update_state(state, priorities=dict.fromkeys(CRITERIA, 2))
        self.assertEqual(init_state(state)["selected_field"], "maru_1")

    def test_missing_static_and_bad_measurements(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            target.joinpath("fields.geojson").write_bytes((ROOT / "data/fields.geojson").read_bytes())
            adapter = FileDataAdapter(target)
            self.assertEqual(adapter.load_fields().static, {})
            target.joinpath("field_static.csv").write_text("field_id,elevation_m,slope_deg\nmaru_1,,nan\nmaru_2,-999,abc\n", encoding="utf-8")
            data = adapter.load_fields()
            self.assertIsNone(data.static["maru_1"]["elevation_m"])
            self.assertIsNone(data.static["maru_2"]["slope_deg"])

    def test_corrupt_name_falls_back_to_exact_id(self):
        data = FileDataAdapter().load_fields().geojson
        data["features"][0]["properties"]["name_ar"] = "Øbroken"
        self.assertEqual(field_options(data)["maru_1"], "maru_1")

    def test_map_styles_and_attribution(self):
        import folium
        data = FileDataAdapter().load_fields().geojson
        m = build_map(data, "maru_2", "en")
        layers = [x for x in m._children.values() if isinstance(x, folium.GeoJson)]
        self.assertEqual(len(layers), 3)
        self.assertEqual([x.style_function(x.data["features"][0])["weight"] for x in layers], [2, 5, 2])
        self.assertIn("Esri World Imagery", m.get_root().render())

    def test_each_selection_rerun_language_and_navigation(self):
        from streamlit.testing.v1 import AppTest
        for fid in ("maru_1", "maru_2", "maru_3"):
            at = AppTest.from_string("from src.ui import render_frontend\nrender_frontend()").run(timeout=30)
            self.assertTrue(at.button(key="fieldshift_continue").disabled)
            at.selectbox(key="fieldshift_field_selector").set_value(fid).run()
            at.run()
            self.assertEqual(at.session_state[KEY]["selected_field"], fid)
            at.selectbox(key="fieldshift_language_selector").set_value("en").run()
            self.assertEqual(at.session_state[KEY]["selected_field"], fid)
            self.assertTrue(any(fid in text.value for text in at.text))
            at.button(key="fieldshift_continue").click().run()
            self.assertEqual(at.session_state[KEY]["screen"], "priorities")
            self.assertEqual(at.session_state[KEY]["selected_field"], fid)
            state = at.session_state[KEY].copy()
            state["screen"] = "field"
            at.session_state[KEY] = state
            at.run()
            self.assertEqual(at.selectbox(key="fieldshift_field_selector").value, fid)
            self.assertEqual(len(at.exception), 0)


if __name__ == "__main__":
    unittest.main()
