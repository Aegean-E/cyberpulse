"""Unit tests for career milestone evaluation and catalog integrity."""

import unittest

from cyberpulse.achievements import (
    ACHIEVEMENTS,
    achievement_status,
    evaluate_achievements,
)
from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile, NodeStatus, NodeType


class TestAchievements(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=1337)
        self.profile = CareerProfile()

    def test_catalog_ids_are_unique_and_described(self):
        ids = [entry.achievement_id for entry in ACHIEVEMENTS]

        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(entry.name and entry.description for entry in ACHIEVEMENTS))

    def test_catalog_status_marks_unlocked_entries(self):
        self.profile.achievements = ["veteran"]

        status = {entry["achievement_id"]: entry for entry in achievement_status(self.profile)}

        self.assertTrue(status["veteran"]["unlocked"])
        self.assertFalse(status["first_extraction"]["unlocked"])

    def test_combo_milestones_unlock_at_their_thresholds(self):
        self.engine.state.best_combo = 5
        self.assertEqual(evaluate_achievements(self.engine, self.profile), ["combo_adept"])
        self.profile.achievements = ["combo_adept"]

        self.engine.state.best_combo = 10

        self.assertEqual(evaluate_achievements(self.engine, self.profile), ["combo_legend"])

    def test_victory_conditions_unlock_ghost_and_speed(self):
        self.engine.state.is_victory = True
        self.engine.state.trace_percent = 20
        self.engine.state.turns_elapsed = 20
        self.engine.state.story_act = 5

        unlocked = evaluate_achievements(self.engine, self.profile)

        self.assertIn("ghost_protocol", unlocked)
        self.assertIn("speed_run", unlocked)
        self.assertIn("full_story", unlocked)

    def test_contract_vault_and_economy_conditions(self):
        contract = self.engine.state.active_contract
        contract.risk_tier = "black"
        contract.completed = True
        vaults = [node for node in self.engine.nodes.values() if node.node_type == NodeType.DATA_VAULT][:3]
        for node in vaults:
            node.status = NodeStatus.BREACHED
        self.engine.state.turns_elapsed = 50
        self.engine.deck.cryptocreds = 1200

        unlocked = evaluate_achievements(self.engine, self.profile)

        self.assertIn("black_contract", unlocked)
        self.assertIn("vault_runner", unlocked)
        self.assertIn("deep_dive", unlocked)
        self.assertIn("high_roller", unlocked)

    def test_hot_extraction_and_veteran_conditions(self):
        self.engine.state.is_jacked_out = True
        self.engine.state.trace_percent = 85
        self.profile.successful_runs = 5

        unlocked = evaluate_achievements(self.engine, self.profile)

        self.assertIn("first_extraction", unlocked)
        self.assertIn("veteran", unlocked)
        self.assertIn("hot_extraction", unlocked)

    def test_hard_clear_requires_a_hard_victory(self):
        hard = GameEngine(seed=1, difficulty="hard")
        normal = GameEngine(seed=1)
        hard.state.is_victory = True
        normal.state.is_victory = True

        self.assertIn("hard_clear", evaluate_achievements(hard, CareerProfile()))
        self.assertNotIn("hard_clear", evaluate_achievements(normal, CareerProfile()))

    def test_daily_streak_milestones(self):
        profile = CareerProfile(daily_streak=7, best_daily_streak=30)

        unlocked = evaluate_achievements(self.engine, profile)

        self.assertIn("daily_devotion", unlocked)
        self.assertIn("daily_legend", unlocked)

    def test_faction_insider_at_ten_standing(self):
        profile = CareerProfile(faction_standing={"syndicate": 10, "street": 0})

        self.assertIn("faction_insider", evaluate_achievements(self.engine, profile))

    def test_unlocks_are_not_returned_twice(self):
        self.engine.state.best_combo = 5
        first = evaluate_achievements(self.engine, self.profile)
        self.profile.achievements = first

        self.assertEqual(evaluate_achievements(self.engine, self.profile), [])


if __name__ == "__main__":
    unittest.main()
