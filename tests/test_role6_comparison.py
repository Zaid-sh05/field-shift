import json
from pathlib import Path
import tempfile
import unittest

from src.ui import FileDataAdapter
from src.ui_mock import demo_rotations, DEMO_LABEL
from src.ui_state import KEY
from src.ui_i18n import translate

ROOT = Path(__file__).resolve().parents[1]


def comparison_app(preview=False, data_dir=None):
    from streamlit.testing.v1 import AppTest
    code = f'''import streamlit as st
from src.ui import render_frontend, FileDataAdapter
from src.ui_state import update_state
if "fieldshift_ui" not in st.session_state:
    update_state(st.session_state, selected_field="maru_1", screen="comparison")
render_frontend(preview={preview!r}, adapter=FileDataAdapter({str(data_dir or ROOT / "data")!r}))
'''
    return AppTest.from_string(code).run(timeout=30)


class ComparisonTests(unittest.TestCase):
    def test_demo_is_isolated_and_complete(self):
        rotations = demo_rotations()
        self.assertEqual(len(rotations), 3)
        self.assertTrue(all(len(r["calendar"]) == 12 and r["is_demo"] for r in rotations))
        rotations[0]["sequence"].clear()
        self.assertTrue(demo_rotations()[0]["sequence"])

    def test_preview_labels_months_language_and_back(self):
        at = comparison_app(True)
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(sum(w.value == DEMO_LABEL for w in at.warning), 7)
        timelines = [m.value for m in at.markdown if 'class="fs-timeline"' in m.value]
        self.assertEqual(len(timelines), 3)
        self.assertTrue(all(html.count('class="fs-month"') == 12 for html in timelines))
        self.assertIn(translate("month_1", "ar"), timelines[0])
        before = at.session_state[KEY].copy()
        at.selectbox(key="fieldshift_language_selector").set_value("en").run(timeout=30)
        self.assertTrue(any("January" in m.value for m in at.markdown))
        at.button(key="comparison_back").click().run(timeout=30)
        self.assertEqual(at.session_state[KEY]["screen"], "priorities")
        self.assertEqual(at.session_state[KEY]["selected_field"], before["selected_field"])
        self.assertEqual(at.session_state[KEY]["priorities"], before["priorities"])

    def test_production_never_falls_back_to_demo(self):
        at = comparison_app(False)
        self.assertEqual(len(at.exception), 0)
        # The three real Role 4 rotations render (not placeholders, not demo fixtures).
        self.assertEqual(sum(x.value == translate("awaiting_rotation") for x in at.text), 0)
        self.assertEqual(sum(" / 100" in x.value for x in at.metric), 3)  # one scored card per rotation
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(any(x.value == translate("not_current_rotation") for x in at.caption))
        self.assertTrue(any("530.22 m" in x.value for x in at.text))
        self.assertTrue(any("3.68°" in x.value for x in at.text))
        self.assertFalse(any(DEMO_LABEL in x.value for x in at.warning))
        self.assertFalse(any("demo_rotation_" in x.value for x in at.text))
        timeline = next(m.value for m in at.markdown if 'class="fs-timeline"' in m.value)
        self.assertEqual(timeline.count('class="fs-month"'), 12)
        # Real calendar from the crop table: starts in October (bare), wheat from November.
        self.assertTrue(timeline.index(translate("month_10")) < timeline.index(translate("month_11")))
        self.assertIn(translate("bare_soil"), timeline)
        self.assertIn(translate("crop_WHEAT"), timeline)

    def test_scenario_and_current_rotation_change_the_cards(self):
        at = comparison_app(False)
        base = [m.value for m in at.metric if " / 100" in m.value]
        self.assertFalse(any(translate("scenario_note")[:20] in w.value for w in at.warning))
        at.slider(key="fieldshift_scenario_rain").set_value(-40).run(timeout=30)
        self.assertEqual(len(at.exception), 0)
        self.assertNotEqual([m.value for m in at.metric if " / 100" in m.value], base)
        self.assertTrue(any(w.value.startswith(translate("scenario_note")[:20]) for w in at.warning))
        # Satellites ruled out wheat-fallow, so the farmer is only asked about the other two.
        self.assertEqual(at.selectbox(key="fieldshift_current_rotation").options[1:], ["قمح ← قمح", "قمح ← عدس"])
        at.selectbox(key="fieldshift_current_rotation").set_value("WW").run(timeout=30)
        self.assertTrue(any(c.value == translate("your_current") for c in at.caption))
        self.assertTrue(any(c.value.startswith(translate("vs_current_up")[:10]) for c in at.caption))

    def test_next_season_advisor_needs_history_then_ranks_options(self):
        at = comparison_app(False)
        self.assertTrue(any(i.value == translate("advisor_prompt") for i in at.info))
        for index in range(3):
            at.selectbox(key=f"fieldshift_history_{index}").set_value("WHEAT").run(timeout=30)
        self.assertEqual(len(at.exception), 0)
        self.assertFalse(any(i.value == translate("advisor_prompt") for i in at.info))
        ranked = [m.value for m in at.markdown if m.value.startswith("**1. ")]
        self.assertEqual(len(ranked), 1)
        self.assertIn(translate("crop_LENTIL"), ranked[0])  # after three wheat seasons a legume comes first
        self.assertTrue(any("✗ " + translate("rule_no_third") in c.value for c in at.caption))

    def test_rain_slider_moves_the_vigour_estimate_and_the_advisor(self):
        at = comparison_app(False)
        vigour = lambda: next(m.value for m in at.metric if m.label == translate("vigor_ndvi"))
        normal = vigour()
        at.selectbox(key="fieldshift_history_2").set_value("WHEAT").run(timeout=30)
        self.assertFalse(any(w.value.startswith(translate("adv_scenario")[:25]) for w in at.warning))
        at.slider(key="fieldshift_scenario_rain").set_value(-50).run(timeout=30)
        self.assertEqual(len(at.exception), 0)
        self.assertLess(float(vigour().split(" ")[0]), float(normal.split(" ")[0]))
        self.assertTrue(any(w.value.startswith(translate("adv_scenario")[:25]) for w in at.warning))

    def test_supplied_contract_rotation_without_fabricated_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "fields.geojson").write_bytes((ROOT / "data/fields.geojson").read_bytes())
            supplied = {"maru_1": [{"id": "supplied", "name_ar": "اسم مزود", "name_en": "Supplied name", "sequence": ["crop_from_owner"], "is_current": True, "score": 999, "calendar": ["bad"] * 12}]}
            (path / "rotations.json").write_text(json.dumps(supplied), encoding="utf-8")
            adapted = FileDataAdapter(path).load_fields().rotations["maru_1"][0]
            self.assertNotIn("score", adapted)
            self.assertNotIn("calendar", adapted)
            at = comparison_app(False, path)
            self.assertEqual(len(at.exception), 0)
            self.assertTrue(any("crop_from_owner" in x.value for x in at.text))
            self.assertTrue(any(translate("confidence_not_assessed") in x.value for x in at.text))
            self.assertTrue(any(x.value == translate("evidence_unavailable") for x in at.caption))
            self.assertFalse(any("999" in x.value for x in at.text))
            self.assertTrue(any(translate("confidence_not_assessed", "ar") in x.value for x in at.text))
            self.assertTrue(any(x.value == translate("evidence_unavailable", "ar") for x in at.caption))

    def test_rotation_adapter_rejects_malformed_and_unknown_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "fields.geojson").write_bytes((ROOT / "data/fields.geojson").read_bytes())
            valid = {"id": "rotation-a", "name_en": "Rotation A", "sequence": ["crop"], "is_current": False,
                     "score": 999, "confidence": "high", "evidence": [{"dataset": "invented"}],
                     "calendar": ["fabricated"] * 12}
            malformed = {"id": "rotation-b", "sequence": ["crop"], "is_current": "false"}
            duplicate = {"id": "rotation-a", "sequence": ["crop"], "is_current": False}
            payload = {"maru_1": [valid, malformed, duplicate, None], "unknown_field": [valid], "maru_2": "bad"}
            (path / "rotations.json").write_text(json.dumps(payload), encoding="utf-8")
            data = FileDataAdapter(path).load_fields()
            self.assertEqual([item["id"] for item in data.rotations["maru_1"]], ["rotation-a"])
            self.assertNotIn("score", data.rotations["maru_1"][0])
            self.assertNotIn("confidence", data.rotations["maru_1"][0])
            self.assertNotIn("evidence", data.rotations["maru_1"][0])
            self.assertNotIn("calendar", data.rotations["maru_1"][0])
            self.assertTrue(any("unknown field ID" in issue for issue in data.issues))
            self.assertTrue(any("malformed record" in issue for issue in data.issues))
            self.assertTrue(any("unapproved fields ignored" in issue for issue in data.issues))
            self.assertTrue(any("rotations must be a list" in issue for issue in data.issues))

    def test_injected_adapter_cannot_leak_demo_or_unapproved_results_in_production(self):
        from streamlit.testing.v1 import AppTest
        code = f'''import streamlit as st
from src.ui import render_frontend, FieldData
from src.ui_state import update_state
from src.ui_mock import demo_rotations
import json
from pathlib import Path
geojson = json.loads(Path({str(ROOT / "data/fields.geojson")!r}).read_text(encoding="utf-8"))
class Adapter:
    def load_fields(self):
        return FieldData(geojson, static={{}}, rotations={{"maru_1": [
            demo_rotations()[0],
            {{"id": "owner-rotation", "name_en": "Owner rotation", "sequence": ["provided crop"],
             "is_current": False, "score": 999, "confidence": "high",
             "evidence": [{{"dataset": "fabricated"}}], "calendar": ["invented"] * 12}}
        ]}})
update_state(st.session_state, selected_field="maru_1", screen="comparison", language="en")
render_frontend(adapter=Adapter(), preview=False)
'''
        at = AppTest.from_string(code).run(timeout=30)
        self.assertEqual(len(at.exception), 0)
        all_text = " ".join(item.value for item in at.text)
        self.assertIn("Owner rotation", all_text)
        self.assertIn("provided crop", all_text)
        self.assertNotIn("Synthetic example", all_text)
        self.assertNotIn("demo_rotation_", all_text)
        self.assertNotIn("999", all_text)
        self.assertNotIn("fabricated", all_text)
        self.assertTrue(any(item.value == translate("scoring_pending", "en") for item in at.info))
        self.assertTrue(any(translate("confidence_not_assessed", "en") in item.value for item in at.text))
        self.assertTrue(any(item.value == translate("evidence_unavailable", "en") for item in at.caption))
        self.assertTrue(any("January" not in item.value for item in at.markdown if 'class="fs-timeline"' in item.value))

    def test_invalid_selection_safe(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_string('''import streamlit as st
from src.ui import render_frontend
from src.ui_state import update_state
update_state(st.session_state, screen="comparison", selected_field="invalid")
render_frontend(preview=True)
''').run(timeout=30)
        self.assertEqual(len(at.exception), 0)
        self.assertFalse(any(DEMO_LABEL in x.value for x in at.warning))
        self.assertEqual(at.button[0].key, "comparison_field_back")


if __name__ == "__main__":
    unittest.main()
