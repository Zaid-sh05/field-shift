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

    def test_driest_wheat_windows_on_record(self):
        # Wheat grows 14 Dec - 5 Jun. In that window 2013-14 is the driest season and 2024-25 the second.
        seasons = s.crop_seasons("maru_1", "WHEAT")
        self.assertEqual(len(seasons), 27)
        self.assertEqual(sorted(seasons, key=lambda y: seasons[y]["rain_mm"])[:2], [2014, 2025])
        self.assertLess(seasons[2025]["met"], 0.4)

    def test_local_calendar(self):
        # Wheat: sown 14 Dec (Maru trial), 173 days to 5 Jun (median satellite season end).
        # Lentil: 14 Dec to 2 Jun (Maru trial). FAO-56 stage shares are stretched to these lengths.
        crops = s._tables()[1]
        self.assertEqual([int(crops.loc[c].season_days) for c in ("WHEAT", "LENTIL")], [173, 170])
        self.assertEqual((int(crops.loc["WHEAT"].sow_month), int(crops.loc["WHEAT"].sow_day)), (12, 14))
        self.assertEqual(s.kc_on_day("WHEAT", 173, 1.15, 0.4, 173), 0.4)    # end of season reaches kc_end
        self.assertEqual(s.kc_on_day("WHEAT", 135, 1.15, 0.4, 173), 1.15)   # mid-season: days 122-151 of 173
        need = sum(v["demand_mm"] for v in s.crop_seasons("maru_1", "WHEAT").values()) / 27
        self.assertTrue(450 <= need <= 650, need)                         # FAO's range for wheat water need

    def test_scores_are_bounded_and_counted_criteria_are_exact(self):
        for field in ("maru_1", "maru_2", "maru_3"):
            by_id = {r["id"]: r["criteria"] for r in s.evaluate(field, EQUAL)["rotations"]}
            for crit in by_id.values():
                for c in s.CRITERIA:
                    self.assertTrue(0 <= crit[c]["score"] <= 100, (field, c))
                    self.assertIn(crit[c]["confidence"], ("high", "medium", "low"))
            self.assertEqual([by_id[r]["soil"]["score"] for r in ("WW", "WL", "WF")], [0, 100, 50])
            self.assertEqual([by_id[r]["harvest"]["score"] for r in ("WW", "WL", "WF")], [100, 100, 50])
            self.assertAlmostEqual(by_id["WF"]["bare"]["score"], by_id["WW"]["bare"]["score"] / 2, delta=0.1)
            self.assertGreater(by_id["WF"]["risk"]["score"], by_id["WW"]["risk"]["score"])  # fallow cannot fail

    def test_weights_drive_the_ranking_not_their_scale(self):
        a = s.evaluate("maru_1", EQUAL)
        b = s.evaluate("maru_1", {c: 30 for c in s.CRITERIA})
        self.assertEqual([r["total"] for r in a["rotations"]], [r["total"] for r in b["rotations"]])
        only_harvest = s.evaluate("maru_1", {**{c: 0 for c in s.CRITERIA}, "harvest": 1})
        self.assertEqual(only_harvest["rotations"][-1]["id"], "WF")
        self.assertTrue(only_harvest["low_confidence_top"])
        self.assertTrue(only_harvest["close_call"])  # WW and WL tie on harvest count

    def test_priorities_change_the_answer(self):
        # Balanced or soil-first farmers get wheat-lentil first; a water-first farmer gets resting the land.
        for field in ("maru_1", "maru_2", "maru_3"):
            self.assertEqual(s.evaluate(field, EQUAL)["rotations"][0]["id"], "WL")
            self.assertEqual(s.evaluate(field, {"water": 1, "risk": 1, "soil": 5, "bare": 3, "harvest": 1})["rotations"][0]["id"], "WL")
            water_first = s.evaluate(field, {"water": 5, "risk": 5, "soil": 1, "bare": 1, "harvest": 1})
            self.assertEqual(water_first["rotations"][0]["id"], "WF")
            self.assertFalse(water_first["low_confidence_top"])

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
            for c in ("soil", "bare", "harvest"):  # not climate-driven in this model
                self.assertEqual(dry[rid][c]["score"], base[rid][c]["score"])
        self.assertGreater(hot["WW"]["water"]["demand_mm"]["WHEAT"], base["WW"]["water"]["demand_mm"]["WHEAT"])
        observed = s.crop_seasons("maru_1", "WHEAT")
        self.assertEqual(dry["WW"]["water"]["rain_mm"]["WHEAT"], round(0.8 * sum(v["rain_mm"] for v in observed.values()) / 27))

    def test_replay_covers_every_real_season_and_shows_the_drought(self):
        replay = s.season_replay("maru_1")
        self.assertEqual(len(replay), 27)
        self.assertEqual(min(replay, key=lambda y: replay[y]["WW"]), 2014)
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

    def test_next_season_keeps_unknown_season_in_its_calendar_slot(self):
        for oldest in ("WHEAT", "LENTIL"):
            with self.subTest(oldest=oldest):
                result = s.next_season("maru_1", [oldest, None, "WHEAT"], EQUAL)
                self.assertEqual(result, s.next_season("maru_1", ["WHEAT"], EQUAL))
        result = s.next_season("maru_1", ["WHEAT", None, "LENTIL"], EQUAL)
        self.assertEqual(result["options"][-1]["crop"], "LENTIL")
        self.assertTrue(result["options"][-1]["legume_repeat"])

    def test_vigor_model_is_trained_validated_and_modest(self):
        model = s.vigor_model()
        self.assertEqual((model["points"], model["seasons"]), (33, 11))
        self.assertGreater(model["slope_per_mm"], 0)                    # more rain, greener crop
        self.assertLess(model["error"], model["mean_only_error"])       # beats guessing the mean on unseen seasons
        self.assertTrue(0.4 < model["r"] < 0.8, model["r"])             # a real but moderate link: do not oversell
        normal, drought = s.predict_vigor("maru_1"), s.predict_vigor("maru_1", 0.5)
        self.assertGreater(normal["ndvi"], drought["ndvi"])
        self.assertEqual(normal["state"], "clear")
        self.assertFalse(normal["extrapolated"])
        self.assertTrue(s.predict_vigor("maru_1", 2.0)["extrapolated"])

    def test_vigor_long_record_keeps_the_claim_honest(self):
        v = s.vigor_model()
        self.assertGreaterEqual(v["long_seasons"], 25)                  # tested well beyond the 11 training seasons
        self.assertGreater(v["landsat_hls_r"], 0.9)                     # Landsat matches HLS, so the long test is fair
        self.assertLess(v["r2_long_rain"], 0.2)                         # rain alone: a scenario, never sold as a forecast
        self.assertGreater(v["r2_long_jan"], v["r2_long_rain"])         # early-season greenness adds real information
        self.assertGreater(v["r2_feb"], v["r2_long_jan"])               # and the season gets clearer as it goes

    def test_drought_scenario_changes_the_next_season_advice(self):
        water_first = {"water": 5, "risk": 5, "soil": 1, "bare": 1, "harvest": 1}
        normal = {o["crop"]: o for o in s.next_season("maru_1", ["LENTIL", "WHEAT"], water_first)["options"]}
        drought = {o["crop"]: o for o in s.next_season("maru_1", ["LENTIL", "WHEAT"], water_first, rain_factor=0.5)["options"]}
        self.assertLess(drought["LENTIL"]["criteria"]["water"], normal["LENTIL"]["criteria"]["water"])
        self.assertLess(drought["WHEAT"]["outlook"]["half_or_more"], normal["WHEAT"]["outlook"]["half_or_more"])
        self.assertEqual(drought["FALLOW"]["criteria"]["water"], 100)
        gap = lambda o: o["FALLOW"]["total"] - o["LENTIL"]["total"]
        self.assertGreater(gap(drought), gap(normal))  # the drier it gets, the better resting the land looks

    def test_backtest_summary_matches_the_replay(self):
        summary, replay = s.backtest_summary("maru_1"), s.season_replay("maru_1")
        self.assertEqual(summary["WW"]["worst_year"], 2014)
        self.assertEqual(summary["WW"]["worst"], replay[2014]["WW"])
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
        self.assertEqual(wheat, [None] * 2 + ["WHEAT"] * 7 + [None] * 3)  # Oct-Nov bare, Dec-Jun wheat, Jul-Sep bare
        self.assertEqual(fallow, [None] * 12)


if __name__ == "__main__":
    unittest.main()
