"""Unit tests for deterministic rival generation."""

import unittest

from cyberpulse.rivals import generate_rival


class TestRivalGeneration(unittest.TestCase):
    def test_rival_is_deterministic_for_a_seed(self):
        first = generate_rival(1337)
        second = generate_rival(1337)

        self.assertEqual(first.name, second.name)
        self.assertEqual(first.handle, second.handle)
        self.assertEqual(first.skill, second.skill)
        self.assertEqual(first.next_move_turn, second.next_move_turn)

    def test_rival_fields_are_within_design_bounds(self):
        rival = generate_rival(42)

        self.assertTrue(rival.name)
        self.assertTrue(rival.handle)
        self.assertTrue(1 <= rival.skill <= 3)
        self.assertTrue(6 <= rival.next_move_turn <= 8)
        self.assertEqual(rival.contracts_stolen, 0)
        self.assertEqual(rival.status, "active")


if __name__ == "__main__":
    unittest.main()
