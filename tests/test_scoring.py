"""Checks for the rotation scoring engine against the real Maru data."""
import unittest

from src import scoring as s

EQUAL = {c: 3 for c in s.CRITERIA}


class ScoringTests(unittest.TestCase):
    def test_kc_curve_follows_fao56_stages(self):
        self.assertEqual(s.kc_on_day("WHEAT", 0, 1.15, 0.4), 0.7)
        self.assertEqual(s.kc_on_day("WHEAT", 180, 1.15, 0.4), 1.15)      # mid-season
        self.assertAlmostEqual(s.kc_on_day("WHEAT", 239, 1.15, 0.4), 0.425, places=3)
        self.assertAlmostEqual(s.kc_on_day("WHEAT", 100, 1.15, 0.4), 0.925, places=3)  # halfway through development

    def test_reference_et_is_in_the_known_range_for_irbid(self):
        # ~1300-1400 mm a year is the published range for the Irbid highlands.
        wide, *_ , elevation = s._tables()
        months = wide.loc["maru_1"]
        import pandas as pd
        year = sum(s.et0_penman_monteith(m.tmean_c, m.tmax_c, m.tmin_c, m.rh_pct, m.wind_m_s, m.solar_mj_m2_day,
                                         pd.Timestamp(k + "-15").dayofyear, elevation["maru_1"])
                   * pd.Timestamp(k + "-15").days_in_month for k, m in months.loc["2010-01":"2019-12"].iterrows()) / 10
        self.assertTrue(1200 < year < 1500, year)

    def test_driest_season_on_record_is_2024_25(self):
        seasons = s.crop_seasons("maru_1", "WHEAT")
        self.assertEqual(len(seasons), 27)
        self.assertEqual(min(seasons, key=lambda y: seasons[y]["rain_mm"]), 2025)
        self.assertLess(seasons[2025]["met"], 0.3)

    def test_scores_are_bounded_and_counted_criteria_are_exact(self):
        for field in ("maru_1", "maru_2", "maru_3"):
            by_id = {r["id"]: r["criteria"] for r in s.evaluate(field, EQUAL)["rotations"]}
            for crit in by_id.values():
                for c in s.CRITERIA:
                    self.assertTrue(0 <= crit[c]["score"] <= 100, (field, c))
                    self.assertIn(crit[c]["confidence"], ("high", "medium", "low"))
            self.assertEqual([by_id[r]["soil"]["score"] for r in ("WW", "WL", "WF")], [0, 100, 50])
            self.assertEqual([by_id[r]["income"]["score"] for r in ("WW", "WL", "WF")], [100, 100, 50])
            self.assertAlmostEqual(by_id["WF"]["bare"]["score"], by_id["WW"]["bare"]["score"] / 2, delta=0.1)
            self.assertGreater(by_id["WF"]["risk"]["score"], by_id["WW"]["risk"]["score"])  # fallow cannot fail

    def test_weights_drive_the_ranking_not_their_scale(self):
        a = s.evaluate("maru_1", EQUAL)
        b = s.evaluate("maru_1", {c: 30 for c in s.CRITERIA})
        self.assertEqual([r["total"] for r in a["rotations"]], [r["total"] for r in b["rotations"]])
        only_income = s.evaluate("maru_1", {**{c: 0 for c in s.CRITERIA}, "income": 1})
        self.assertEqual(only_income["rotations"][-1]["id"], "WF")
        self.assertTrue(only_income["low_confidence_top"])
        self.assertTrue(only_income["close_call"])  # WW and WL tie on harvest count

    def test_water_first_farmer_gets_a_close_call_flag(self):
        result = s.evaluate("maru_1", {"water": 5, "risk": 5, "soil": 1, "bare": 1, "income": 1})
        self.assertTrue(result["close_call"])
        self.assertFalse(result["low_confidence_top"])

    def test_interface_sliders_match_engine_criteria(self):
        from src.ui_state import CRITERIA
        self.assertEqual(CRITERIA, s.CRITERIA)

    def test_scenarios_move_water_and_risk_in_the_physical_direction(self):
        base = {r["id"]: r["criteria"] for r in s.evaluate("maru_1", EQUAL)["rotations"]}
        dry = {r["id"]: r["criteria"] for r in s.evaluate("maru_1", EQUAL, rain_factor=0.8)["rotations"]}
        hot = {r["id"]: r["criteria"] for r in s.evaluate("maru_1", EQUAL, warming_c=2.0)["rotations"]}
        for rid in ("WW", "WL", "WF"):
            for c in ("water", "risk"):
                self.assertLess(dry[rid][c]["score"], base[rid][c]["score"])
                self.assertLess(hot[rid][c]["score"], base[rid][c]["score"])
            for c in ("soil", "bare", "income"):  # not climate-driven in this model
                self.assertEqual(dry[rid][c]["score"], base[rid][c]["score"])
        self.assertGreater(hot["WW"]["water"]["demand_mm"]["WHEAT"], base["WW"]["water"]["demand_mm"]["WHEAT"])
        observed = s.crop_seasons("maru_1", "WHEAT")
        self.assertEqual(dry["WW"]["water"]["rain_mm"]["WHEAT"], round(0.8 * sum(v["rain_mm"] for v in observed.values()) / 27))

    def test_replay_covers_every_real_season_and_shows_the_drought(self):
        replay = s.season_replay("maru_1")
        self.assertEqual(len(replay), 27)
        self.assertEqual(min(replay, key=lambda y: replay[y]["WW"]), 2025)
        for year, row in replay.items():
            self.assertEqual(set(row), {"WW", "WL", "WF"})
            self.assertGreaterEqual(row["WF"], row["WW"])  # half the land is fallow and cannot fail

    def test_past_seasons_can_be_judged_without_later_data(self):
        blind = {r["id"]: r for r in s.evaluate("maru_1", EQUAL, before=2025)["rotations"]}
        full = {r["id"]: r for r in s.evaluate("maru_1", EQUAL)["rotations"]}
        self.assertEqual(blind["WW"]["criteria"]["water"]["seasons"], 26)  # the 2024-25 drought is hidden
        self.assertGreater(blind["WW"]["criteria"]["risk"]["score"], full["WW"]["criteria"]["risk"]["score"])

    def test_next_season_after_three_wheat_years(self):
        result = s.next_season("maru_1", ["WHEAT", "WHEAT", "WHEAT"], EQUAL)
        by_crop = {o["crop"]: o for o in result["options"]}
        self.assertEqual(set(by_crop), {"WHEAT", "LENTIL", "FALLOW"})
        self.assertEqual(by_crop["WHEAT"]["rules"], {"varied": False, "legume": False, "no_third": False})
        self.assertEqual(by_crop["LENTIL"]["rules"], {"varied": True, "legume": True, "no_third": True})
        self.assertEqual(by_crop["FALLOW"]["rules"], {"varied": True, "legume": False, "no_third": True})
        self.assertEqual(result["options"][0]["crop"], "LENTIL")
        self.assertEqual(result["options"][-1]["crop"], "WHEAT")
        self.assertIsNone(by_crop["FALLOW"]["outlook"])
        outlook = by_crop["WHEAT"]["outlook"]
        self.assertEqual(outlook["seasons"], 27)
        self.assertTrue(outlook["worst"] <= outlook["typical"] <= outlook["best"] <= 100)
        self.assertLess(outlook["half_or_more"], by_crop["LENTIL"]["outlook"]["half_or_more"])  # wheat needs more water

    def test_next_season_history_changes_the_advice(self):
        after_lentil = {o["crop"]: o for o in s.next_season("maru_1", ["WHEAT", "LENTIL"], EQUAL)["options"]}
        self.assertEqual(after_lentil["WHEAT"]["rules"], {"varied": True, "legume": True, "no_third": True})
        self.assertFalse(after_lentil["LENTIL"]["rules"]["varied"])
        self.assertGreater(after_lentil["WHEAT"]["criteria"]["soil"], after_lentil["LENTIL"]["criteria"]["soil"])
        order = [o["crop"] for o in s.next_season("maru_1", ["WHEAT", "LENTIL"], EQUAL)["options"]]
        self.assertEqual(order[-1], "LENTIL")  # lentil after lentil is never ranked first, whatever its water score
        self.assertTrue(after_lentil["LENTIL"]["legume_repeat"])
        self.assertFalse(after_lentil["WHEAT"]["legume_repeat"])
        moisture = s.next_season("maru_1", ["WHEAT"], EQUAL)["soil_moisture"]
        self.assertIn(moisture["state"], ("dry", "normal", "wet"))
        for bad in ([], ["CORN"], ["WHEAT", None]):
            with self.assertRaises(ValueError):
                s.next_season("maru_1", bad, EQUAL)

    def test_backtest_summary_matches_the_replay(self):
        summary, replay = s.backtest_summary("maru_1"), s.season_replay("maru_1")
        self.assertEqual(summary["WW"]["worst_year"], 2025)
        self.assertEqual(summary["WW"]["worst"], replay[2025]["WW"])
        self.assertEqual(summary["WW"]["under_half"], sum(row["WW"] < 50 for row in replay.values()))
        self.assertGreaterEqual(summary["WF"]["mean"], summary["WW"]["mean"])

    def test_bad_weights_are_rejected(self):
        for bad in ({}, {**EQUAL, "effort": 3}, {**EQUAL, "water": -1}, {c: 0 for c in s.CRITERIA}, {**EQUAL, "water": True}):
            with self.assertRaises(ValueError):
                s.evaluate("maru_1", bad)
        with self.assertRaises(ValueError):
            s.evaluate("nowhere", EQUAL)

    def test_calendar_marks_bare_months(self):
        wheat, fallow = s.crop_calendar(["WHEAT", "FALLOW"])
        self.assertEqual(wheat, [None] + ["WHEAT"] * 8 + [None] * 3)  # Oct bare, Nov-Jun wheat, Jul-Sep bare
        self.assertEqual(fallow, [None] * 12)


if __name__ == "__main__":
    unittest.main()
