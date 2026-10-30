"""Unit tests for faction standing normalization and bonuses."""

import unittest

from cyberpulse.factions import (
    allegiance_contract_bonus,
    allegiance_shop_discount,
    contract_bonus,
    normalize_allegiance,
    normalize_standing,
    rank_for,
    street_discount,
    update_standing,
)


class TestFactions(unittest.TestCase):
    def test_normalize_standing_drops_unknown_and_invalid_values(self):
        standing = normalize_standing({
            "syndicate": "12",
            "street": -4,
            "netwatch": 9,
            "bad": object(),
        })

        self.assertEqual(standing, {"syndicate": 12, "street": 0})

    def test_bonuses_are_capped(self):
        self.assertEqual(contract_bonus({"syndicate": 10}), 0.10)
        self.assertEqual(contract_bonus({"syndicate": 999}), 0.20)
        self.assertEqual(street_discount({"street": 10}), 0.10)
        self.assertEqual(street_discount({"street": 999}), 0.15)

    def test_ranks_follow_standing_thresholds(self):
        self.assertEqual(rank_for("syndicate", 0), (0, "Associate", 0))
        self.assertEqual(rank_for("syndicate", 10), (1, "Fixer", 100))
        self.assertEqual(rank_for("syndicate", 49), (2, "Broker", 250))
        self.assertEqual(rank_for("syndicate", 50), (3, "Kingpin", 500))
        self.assertEqual(rank_for("street", 10), (1, "Runner", 100))
        self.assertEqual(rank_for("street", 25), (2, "Ghost", 250))

    def test_allegiance_normalization_and_bonuses(self):
        self.assertEqual(normalize_allegiance("SYNDICATE"), "syndicate")
        self.assertEqual(normalize_allegiance("street"), "street")
        self.assertEqual(normalize_allegiance("corp"), "none")
        self.assertGreater(allegiance_contract_bonus("syndicate"), 0)
        self.assertEqual(allegiance_contract_bonus("street"), 0)
        self.assertGreater(allegiance_shop_discount("street"), 0)
        self.assertEqual(allegiance_shop_discount("syndicate"), 0)

    def test_update_standing_clamps_growth(self):
        standing = update_standing({"syndicate": 99, "street": 0}, "syndicate", 5)

        self.assertEqual(standing["syndicate"], 100)
        self.assertEqual(standing["street"], 0)


if __name__ == "__main__":
    unittest.main()
