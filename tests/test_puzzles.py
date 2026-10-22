"""Unit tests for CyberPulse hacking mini-game puzzles."""

import unittest
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle


class TestPuzzles(unittest.TestCase):
    def test_frequency_puzzle_tuning(self):
        puzzle = FrequencyPuzzle(target_freq=50.0, tolerance=0.5)
        # Off target
        success, msg = puzzle.tune(40.0)
        self.assertFalse(success)
        self.assertIn("TOO LOW", msg)

        # On target
        success, msg = puzzle.tune(50.2)
        self.assertTrue(success)
        self.assertIn("RESONANCE LOCKED", msg)

    def test_frequency_exhaustion(self):
        puzzle = FrequencyPuzzle(target_freq=50.0, tolerance=0.2)
        puzzle.tune(10.0)
        puzzle.tune(10.0)
        success, msg = puzzle.tune(10.0)
        self.assertFalse(success)
        self.assertIn("FAILED", msg)

    def test_buffer_puzzle_verification(self):
        puzzle = BufferPuzzle(
            matrix=[["1C", "FF"], ["7A", "BD"]],
            target_seq=["1C", "7A"],
        )
        # Invalid sequence
        ok, msg = puzzle.verify_sequence(["1C", "BD"])
        self.assertFalse(ok)
        self.assertIn("CORRUPTION", msg)

        # Correct sequence
        ok, msg = puzzle.verify_sequence(["1C", "7A"])
        self.assertTrue(ok)
        self.assertIn("EXPLOIT EXECUTED", msg)

    def test_frequency_near_miss_grants_one_bonus_attempt(self):
        puzzle = FrequencyPuzzle(target_freq=50.0, tolerance=0.8)
        ok, _ = puzzle.tune(51.9)
        self.assertFalse(ok)
        self.assertTrue(puzzle.near_miss)
        self.assertEqual(puzzle.attempts_left, 2)

        self.assertTrue(puzzle.claim_near_miss_bonus())
        self.assertEqual(puzzle.attempts_left, 3)
        self.assertFalse(puzzle.claim_near_miss_bonus())
        self.assertEqual(puzzle.attempts_left, 3)

    def test_buffer_near_miss_grants_one_retry(self):
        puzzle = BufferPuzzle(matrix=[["1C", "FF"], ["7A", "BD"]], target_seq=["1C", "7A"])
        ok, _ = puzzle.verify_sequence(["1C", "BD"])
        self.assertFalse(ok)
        self.assertTrue(puzzle.near_miss)
        self.assertTrue(puzzle.claim_near_miss_bonus())
        self.assertFalse(puzzle.claim_near_miss_bonus())

    def test_hash_near_miss_grants_one_bonus_attempt(self):
        puzzle = HashCrackPuzzle(target_word="CYBER", word_list=["CYBER", "GHOST", "PULSE"])
        ok, _ = puzzle.guess("CYBEZ")
        self.assertFalse(ok)
        self.assertTrue(puzzle.near_miss)
        self.assertEqual(puzzle.attempts_left, 3)

        self.assertTrue(puzzle.claim_near_miss_bonus())
        self.assertEqual(puzzle.attempts_left, 4)
        self.assertFalse(puzzle.claim_near_miss_bonus())

    def test_hash_crack_puzzle(self):
        puzzle = HashCrackPuzzle(target_word="CYBER", word_list=["CYBER", "GHOST", "PULSE"])
        # Partial match
        ok, msg = puzzle.guess("PULSE")
        self.assertFalse(ok)
        self.assertIn("ACCESS DENIED", msg)

        # Full match
        ok, msg = puzzle.guess("CYBER")
        self.assertTrue(ok)
        self.assertIn("ACCESS GRANTED", msg)


if __name__ == "__main__":
    unittest.main()
