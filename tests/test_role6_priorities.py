"""Raw farmer preferences and preview navigation regression checks."""
from pathlib import Path
import unittest

from src.ui_state import KEY, CRITERIA, init_state, get_preferences
from src.ui_i18n import translate

PREVIEW = Path(__file__).resolve().parent / "role6_preview.py"


class PreferenceTests(unittest.TestCase):
    def test_defaults_and_isolation(self):
        state = {}
        values = get_preferences(state)
        self.assertEqual(values, dict.fromkeys(CRITERIA, 3))
        values["water"] = 5
        self.assertEqual(get_preferences(state)["water"], 3)

    def test_recover_invalid_session(self):
        for invalid in (None, [], {"water": True, "bare": 0, "soil": 6, "risk": float("nan"), "income": "4", "effort": None}):
            state = {KEY: {"selected_field": "maru_2", "language": "en", "screen": "priorities", "priorities": invalid}}
            self.assertEqual(get_preferences(state), dict.fromkeys(CRITERIA, 3))
            self.assertEqual(init_state(state)["selected_field"], "maru_2")
        state = {KEY: "broken"}
        self.assertEqual(init_state(state)["language"], "ar")

    def test_preview_persistence_and_navigation(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(PREVIEW)).run(timeout=30)
        at.selectbox(key="fieldshift_field_selector").set_value("maru_2").run()
        at.button(key="fieldshift_continue").click().run()
        self.assertEqual(len(at.slider), 6)
        self.assertEqual(len(at.expander[-1].slider), 1)
        expected = dict(zip(CRITERIA, (1, 2, 3, 4, 5, 1)))
        for criterion, value in expected.items():
            slider = at.slider(key=f"fieldshift_priority_{criterion}")
            self.assertEqual(slider.label, translate(f"priority_{criterion}", "ar"))
            slider.set_value(value).run()
        at.run()
        at.selectbox(key="fieldshift_language_selector").set_value("en").run()
        for criterion, value in expected.items():
            slider = at.slider(key=f"fieldshift_priority_{criterion}")
            self.assertEqual(slider.value, value)
            self.assertEqual(slider.label, translate(f"priority_{criterion}", "en"))
        at.button(key="priorities_back").click().run()
        self.assertEqual(at.session_state[KEY]["screen"], "field")
        self.assertEqual(at.session_state[KEY]["selected_field"], "maru_2")
        at.button(key="fieldshift_continue").click().run()
        self.assertEqual([s.value for s in at.slider], [expected[k] for k in ("water", "soil", "risk", "income", "effort", "bare")])
        at.button(key="priorities_continue").click().run()
        self.assertEqual(at.session_state[KEY]["screen"], "comparison")
        self.assertEqual(at.session_state[KEY]["priorities"], expected)
        self.assertEqual(at.session_state[KEY]["language"], "en")
        self.assertEqual(len(at.exception), 0)

    def test_invalid_field_has_only_back_navigation(self):
        from streamlit.testing.v1 import AppTest
        code = '''import streamlit as st
from src.ui import render_frontend
from src.ui_state import update_state
update_state(st.session_state, selected_field="not_real", screen="priorities")
render_frontend()
'''
        at = AppTest.from_string(code).run()
        self.assertEqual(len(at.slider), 0)
        self.assertEqual([b.key for b in at.button], ["priorities_back"])
        self.assertEqual(len(at.exception), 0)


if __name__ == "__main__":
    unittest.main()
