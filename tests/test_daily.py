"""Unit tests for deterministic daily-run keys and seeds."""

import unittest
from datetime import date

from cyberpulse.daily import (
    DAILY_MODIFIERS,
    daily_key,
    daily_modifier,
    daily_run,
    daily_seed,
    is_next_day,
    modifier_by_id,
)


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

    def test_daily_modifier_is_stable_and_from_the_table(self):
        day = date(2026, 10, 30)
        first = daily_modifier(day)
        second = daily_modifier(day)

        self.assertEqual(first.modifier_id, second.modifier_id)
        self.assertIn(first, DAILY_MODIFIERS)
        self.assertEqual(modifier_by_id(first.modifier_id).name, first.name)

    def test_daily_modifier_changes_across_the_roster(self):
        ids = {daily_modifier(date(2026, 10, day)).modifier_id for day in range(1, 8)}

        self.assertEqual(len(ids), len(DAILY_MODIFIERS))

    def test_next_day_detection_handles_gaps_and_bad_keys(self):
        self.assertTrue(is_next_day("2026-10-30", "2026-10-31"))
        self.assertFalse(is_next_day("2026-10-30", "2026-10-30"))
        self.assertFalse(is_next_day("2026-10-30", "2026-11-01"))
        self.assertFalse(is_next_day("bad", "2026-10-31"))
        self.assertFalse(is_next_day("", "2026-10-31"))


if __name__ == "__main__":
    unittest.main()
