"""Unit tests for the transparent run score formula."""

import unittest

from cyberpulse.scoring import score_run


class TestScoring(unittest.TestCase):
    def test_score_breakdown_uses_documented_weights(self):
        result = score_run(
            gained=100,
            best_combo=4,
            quests_done=2,
            nodes_breached=3,
            outcome="victory",
            contract_completed=True,
            main_story_complete=True,
        )

        self.assertEqual(result["breakdown"], {
            "credits": 100,
            "combo": 300,
            "quests": 300,
            "breaches": 75,
            "contract": 200,
            "outcome": 500,
            "story": 100,
        })
        self.assertEqual(result["score"], 1575)

    def test_lockout_has_no_outcome_bonus(self):
        result = score_run(
            gained=0,
            best_combo=0,
            quests_done=0,
            nodes_breached=1,
            outcome="lockout",
            contract_completed=False,
            main_story_complete=False,
        )

        self.assertEqual(result["breakdown"]["outcome"], 0)
        self.assertEqual(result["score"], 25)

    def test_negative_inputs_are_clamped(self):
        result = score_run(
            gained=-50,
            best_combo=-2,
            quests_done=-1,
            nodes_breached=-3,
            outcome="jackout",
            contract_completed=False,
            main_story_complete=False,
        )

        self.assertEqual(result["breakdown"]["credits"], 0)
        self.assertEqual(result["breakdown"]["combo"], 0)
        self.assertEqual(result["breakdown"]["quests"], 0)
        self.assertEqual(result["breakdown"]["breaches"], 0)
        self.assertEqual(result["score"], 250)


if __name__ == "__main__":
    unittest.main()
