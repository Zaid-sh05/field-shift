"""Role 6 regression checks. Run: python -m unittest discover -s tests -v."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.ui import FileDataAdapter, ScoringRequest
from src.ui_state import CRITERIA, init_state, update_state
from src.ui_components.priorities import resolve_weights
from src.ui_i18n import translate
from src.ui_mock import mock_preview

ROOT = Path(__file__).resolve().parents[1]


class StateTests(unittest.TestCase):
    def test_state_isolation_and_rerun_preservation(self):
        a, b = {}, {}
        snapshot = init_state(a)
        snapshot["priorities"]["water"] = 9
        self.assertEqual(init_state(a)["priorities"]["water"], 3)
        update_state(a, selected_field="maru_1", language="en", screen="priorities")
        self.assertEqual(init_state(a)["selected_field"], "maru_1")
        self.assertIsNone(init_state(b)["selected_field"])

    def test_invalid_update_is_atomic(self):
        state = {}
        before = init_state(state)
        with self.assertRaises(ValueError):
            update_state(state, screen="unknown", language="en")
        self.assertEqual(before, init_state(state))

    def test_all_six_criteria_required(self):
        with self.assertRaises(ValueError):
            ScoringRequest("maru_1", {"water": 1})
        weights = dict.fromkeys(CRITERIA, 1)
        request = ScoringRequest("maru_1", weights)
        weights["water"] = 100
        self.assertEqual(request.weights["water"], 1)
        for bad in (float("nan"), float("inf"), -1, True, None):
            with self.assertRaises(ValueError):
                ScoringRequest("maru_1", dict.fromkeys(CRITERIA, bad))

    def test_configurable_control_mapping(self):
        mapping = dict(zip(CRITERIA, ("a", "b", "b", "c", "d", "e")))
        got = resolve_weights(dict.fromkeys("abcde", 2), mapping)
        self.assertEqual(set(got), set(CRITERIA))
        with self.assertRaises(ValueError):
            resolve_weights({"a": 1}, {"water": "a"})


class AdapterTests(unittest.TestCase):
    def test_absent_and_malformed_files_do_not_create_mock(self):
        with tempfile.TemporaryDirectory() as folder:
            adapter = FileDataAdapter(folder)
            self.assertTrue(adapter.load_fields().issues)
            self.assertEqual(adapter.load_fields().geojson["features"], [])
            path = Path(folder) / "fields.geojson"
            for content in ("{broken", "[]", '{"type":"FeatureCollection","features":[null]}'):
                path.write_text(content, encoding="utf-8")
                self.assertTrue(adapter.load_fields().issues)

    def test_real_ids_preserved_with_contract_warnings(self):
        original = json.loads((ROOT / "data/fields.geojson").read_text(encoding="utf-8"))
        loaded = FileDataAdapter(ROOT / "data").load_fields()
        self.assertEqual(loaded.geojson, original)
        self.assertTrue(any("zone" in issue for issue in loaded.issues))

    def test_mock_has_no_scientific_results_or_field_ids(self):
        preview = mock_preview()
        self.assertTrue(preview.is_mock)
        self.assertIn("MOCK", preview.label)
        self.assertEqual(preview.card_slots, (None,) * 3)
        self.assertEqual(preview.months, (None,) * 12)

    def test_translations_have_matching_keys(self):
        catalog = json.loads((ROOT / "i18n.json").read_text(encoding="utf-8"))
        self.assertEqual(set(catalog["ar"]), set(catalog["en"]))
        self.assertEqual(translate("missing"), "missing")
        self.assertEqual(translate("field", "ar", catalog={"ar": {}, "en": {"field": "Field"}}), "Field")
        for malformed in (None, [], {"ar": None, "en": []}, {"ar": {"field": 12}}):
            if malformed is not None:
                self.assertEqual(translate("field", "ar", catalog=malformed), "field")

    def test_imports_without_site_packages(self):
        # -S disables site-packages: UI imports must not require Streamlit/Folium.
        modules = ["src.ui", "src.ui_state", "src.ui_i18n", "src.ui_mock",
                   "src.ui_components.field_selector", "src.ui_components.priorities",
                   "src.ui_components.rotation_cards", "src.ui_components.timeline",
                   "src.ui_screens.field", "src.ui_screens.priorities", "src.ui_screens.comparison"]
        code = "import importlib; " + "; ".join(f"importlib.import_module({m!r})" for m in modules)
        subprocess.run([sys.executable, "-S", "-c", code], cwd=ROOT, check=True)


class RuntimeTests(unittest.TestCase):
    def test_language_switch_preserves_state(self):
        from streamlit.testing.v1 import AppTest
        code = '''import streamlit as st
from src.ui import render_frontend, FieldData
from src.ui_state import update_state, CRITERIA
class Adapter:
    def load_fields(self):
        return FieldData({"type": "FeatureCollection", "features": []})
if "fieldshift_ui" not in st.session_state:
    update_state(st.session_state, selected_field="maru_1", priorities=dict.fromkeys(CRITERIA, 3), screen="comparison")
render_frontend(adapter=Adapter())
'''
        at = AppTest.from_string(code).run()
        self.assertEqual(at.subheader[0].value, translate("comparison", "ar"))
        at.selectbox[0].set_value("en").run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.subheader[0].value, translate("comparison", "en"))
        saved = at.session_state["fieldshift_ui"]
        self.assertEqual(saved["selected_field"], "maru_1")
        self.assertEqual(saved["screen"], "comparison")
        self.assertEqual(saved["priorities"], dict.fromkeys(CRITERIA, 3))
        self.assertEqual(saved["language"], "en")
        at.selectbox[0].set_value("ar").run()
        self.assertEqual(at.session_state["fieldshift_ui"]["language"], "ar")
        self.assertEqual(at.subheader[0].value, translate("comparison", "ar"))

    def test_screen_shells_with_missing_data(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as folder:
            for screen in ("field", "priorities", "comparison"):
                for language in ("ar", "en"):
                    code = ("import streamlit as st\n"
                            "from src.ui import render_frontend, FileDataAdapter\n"
                            "from src.ui_state import update_state\n"
                            f"update_state(st.session_state, screen={screen!r}, language={language!r})\n"
                            f"render_frontend(adapter=FileDataAdapter({folder!r}), preview=True)\n")
                    at = AppTest.from_string(code).run(timeout=30)
                    self.assertEqual(len(at.exception), 0)
                    self.assertEqual(at.subheader[0].value, translate(screen, language))

    def test_original_app(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.dataframe), 1)


if __name__ == "__main__":
    unittest.main()
