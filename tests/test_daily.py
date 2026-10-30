"""Unit tests for deterministic daily-run keys and seeds."""

import unittest
from datetime import date

from cyberpulse.daily import daily_key, daily_run, daily_seed, is_next_day


class TestDailyRun(unittest.TestCase):
    def test_key_and_seed_are_stable_for_a_date(self):
        day = date(2026, 10, 30)

        self.assertEqual(daily_key(day), "2026-10-30")
        self.assertEqual(daily_seed(day), 20261030)
        self.assertEqual(daily_run(day), ("2026-10-30", 20261030))

    def test_different_days_produce_different_seeds(self):
        first = daily_run(date(2026, 10, 30))
        second = daily_run(date(2026, 10, 31))

        self.assertNotEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])

    def test_next_day_detection_handles_gaps_and_bad_keys(self):
        self.assertTrue(is_next_day("2026-10-30", "2026-10-31"))
        self.assertFalse(is_next_day("2026-10-30", "2026-10-30"))
        self.assertFalse(is_next_day("2026-10-30", "2026-11-01"))
        self.assertFalse(is_next_day("bad", "2026-10-31"))
        self.assertFalse(is_next_day("", "2026-10-31"))


if __name__ == "__main__":
    unittest.main()
