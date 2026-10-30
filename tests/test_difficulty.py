"""Unit tests for difficulty normalization and modifiers."""

import unittest

from cyberpulse.difficulty import contract_multiplier, normalize_difficulty, trace_multiplier


class TestDifficulty(unittest.TestCase):
    def test_normalization_defaults_unknown_values(self):
        self.assertEqual(normalize_difficulty("HARD"), "hard")
        self.assertEqual(normalize_difficulty(" easy "), "easy")
        self.assertEqual(normalize_difficulty("nightmare"), "normal")
        self.assertEqual(normalize_difficulty(None), "normal")

    def test_trace_multipliers_order_by_difficulty(self):
        self.assertLess(trace_multiplier("easy"), trace_multiplier("normal"))
        self.assertGreater(trace_multiplier("hard"), trace_multiplier("normal"))

    def test_contract_multipliers_favor_easy_and_tax_hard(self):
        self.assertGreater(contract_multiplier("easy"), contract_multiplier("normal"))
        self.assertLess(contract_multiplier("hard"), contract_multiplier("normal"))


if __name__ == "__main__":
    unittest.main()
