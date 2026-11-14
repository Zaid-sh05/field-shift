
"""Checks for the rotation scoring engine against the real Maru data."""
import unittest

from src import scoring as s

EQUAL = {c: 3 for c in s.CRITERIA}


class ScoringTests(unittest.TestCase):

    def test_kc_curve_follows_fao56_stages(self):
        self.assertEqual(
            s.kc_on_day("WHEAT", 0, 1.15, 0.4),
            0.7
        )
        self.assertEqual(
            s.kc_on_day("WHEAT", 180, 1.15, 0.4),
            1.15
        )
        self.assertAlmostEqual(
            s.kc_on_day("WHEAT", 239, 1.15, 0.4),
            0.425,
            places=3
        )
        self.assertAlmostEqual(
            s.kc_on_day("WHEAT", 100, 1.15, 0.4),
            0.925,
            places=3
        )

    def test_reference_et_is_in_the_known_range_for_irbid(self):
        # ~1300-1400 mm a year is the published range for the Irbid highlands.
        wide, *_, elevation = s._tables()
        months = wide.loc["maru_1"]

        import pandas as pd

        year = sum(
            s.et0_penman_monteith(
                m.tmean_c,
                m.tmax_c,
                m.tmin_c,
                m.rh_pct,
                m.wind_m_s,
                m.solar_mj_m2_day,
                pd.Timestamp(k + "-15").dayofyear,
                elevation["maru_1"],
            )
            * pd.Timestamp(k + "-15").days_in_month
            for k, m in months.loc["2010-01":"2019-12"].iterrows()
        ) / 10

        self.assertTrue(1200 < year < 1500, year)

    def test_driest_season_on_record_is_2024_25(self):
        seasons = s.crop_seasons("maru_1", "WHEAT")

        self.assertEqual(len(seasons), 27)
        self.assertEqual(
            min(seasons, key=lambda y: seasons[y]["rain_mm"]),
            2025
        )
        self.assertLess(seasons[2025]["met"], 0.3)

    def test_scores_are_bounded_and_counted_criteria_are_exact(self):
        for field in ("maru_1", "maru_2", "maru_3"):

            by_id = {
                r["id"]: r["criteria"]
                for r in s.evaluate(field, EQUAL)["rotations"]
            }

            for crit in by_id.values():
                for c in s.CRITERIA:
                    self.assertTrue(
                        0 <= crit[c]["score"] <= 100,
                        (field, c)
                    )
                    self.assertIn(
                        crit[c]["confidence"],
                        ("high", "medium", "low")
                    )

            self.assertEqual(
                [by_id[r]["soil"]["score"] for r in ("WW", "WL", "WF")],
                [0, 100, 50]
            )

            self.assertEqual(
                [by_id[r]["harvest"]["score"] for r in ("WW", "WL", "WF")],
                [100, 100, 50]
            )

            self.assertAlmostEqual(
                by_id["WF"]["bare"]["score"],
                by_id["WW"]["bare"]["score"] / 2,
                delta=0.1
            )

            self.assertGreater(
                by_id["WF"]["risk"]["score"],
                by_id["WW"]["risk"]["score"]
            )

    def test_weights_drive_the_ranking_not_their_scale(self):
        a = s.evaluate("maru_1", EQUAL)

        b = s.evaluate(
            "maru_1",
            {c: 30 for c in s.CRITERIA}
        )

        self.assertEqual(
            [r["total"] for r in a["rotations"]],
            [r["total"] for r in b["rotations"]]
        )

        only_harvest = s.evaluate(
            "maru_1",
            {
                **{c: 0 for c in s.CRITERIA},
                "harvest": 1
            }
        )

        self.assertEqual(
            only_harvest["rotations"][-1]["id"],
            "WF"
        )

        self.assertTrue(
            only_harvest["low_confidence_top"]
        )

        self.assertTrue(
            only_harvest["close_call"]
        )  # WW and WL tie on harvest count

    def test_water_first_farmer_gets_a_close_call_flag(self):
        result = s.evaluate(
            "maru_1",
            {
                "water": 5,
                "risk": 5,
                "soil": 1,
                "bare": 1,
                "harvest": 1
            }
        )

        self.assertTrue(result["close_call"])
        self.assertFalse(result["low_confidence_top"])

    def test_interface_sliders_match_engine_criteria(self):
        from src.ui_state import CRITERIA

        self.assertEqual(CRITERIA, s.CRITERIA)

    def test_bad_weights_are_rejected(self):
        bad_weights = (
            {},
            {**EQUAL, "effort": 3},
            {**EQUAL, "water": -1},
            {c: 0 for c in s.CRITERIA},
            {**EQUAL, "water": True},
        )

        for bad in bad_weights:
            with self.assertRaises(ValueError):
                s.evaluate("maru_1", bad)

        with self.assertRaises(ValueError):
            s.evaluate("nowhere", EQUAL)

    def test_calendar_marks_bare_months(self):
        wheat, fallow = s.crop_calendar(["WHEAT", "FALLOW"])

        self.assertEqual(
            wheat,
            [None] + ["WHEAT"] * 8 + [None] * 3
        )

        self.assertEqual(fallow, [None] * 12)


if __name__ == "__main__":
    unittest.main()
