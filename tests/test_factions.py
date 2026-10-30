"""Unit tests for faction standing normalization and bonuses."""

import unittest

from cyberpulse.factions import (
    contract_bonus,
    normalize_standing,
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

    def test_update_standing_clamps_growth(self):
        standing = update_standing({"syndicate": 99, "street": 0}, "syndicate", 5)

        self.assertEqual(standing["syndicate"], 100)
        self.assertEqual(standing["street"], 0)


if __name__ == "__main__":
    unittest.main()
