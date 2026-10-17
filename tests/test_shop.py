"""Unit tests for Black Market Shop in CyberPulse."""

import unittest
from cyberpulse.models import CyberDeck
from cyberpulse.shop import BlackMarketShop


class TestShop(unittest.TestCase):
    def setUp(self):
        self.shop = BlackMarketShop()
        self.deck = CyberDeck(cryptocreds=500)

    def test_list_items(self):
        items = self.shop.list_available(self.deck)
        self.assertGreaterEqual(len(items), 4)
        item_ids = [it["item_id"] for it in items]
        self.assertIn("overclock_cpu", item_ids)
        self.assertIn("ice_dampener", item_ids)

    def test_purchase_cpu_overclock(self):
        initial_cpu = self.deck.max_cpu
        ok, msg = self.shop.purchase(self.deck, "overclock_cpu")
        self.assertTrue(ok)
        self.assertEqual(self.deck.max_cpu, initial_cpu + 2)
        self.assertEqual(self.deck.overclock_level, 1)
        self.assertEqual(self.deck.cryptocreds, 350)  # 500 - 150

    def test_purchase_ice_dampener(self):
        ok, msg = self.shop.purchase(self.deck, "ice_dampener")
        self.assertTrue(ok)
        self.assertEqual(self.deck.ice_dampener_level, 1)
        self.assertEqual(self.deck.cryptocreds, 250)  # 500 - 250

    def test_purchase_insufficient_funds(self):
        self.deck.cryptocreds = 50
        ok, msg = self.shop.purchase(self.deck, "overclock_cpu")
        self.assertFalse(ok)
        self.assertIn("Insufficient funds", msg)

    def test_purchase_max_level(self):
        self.deck.cryptocreds = 2000
        # Buy 3 times to hit max level
        self.shop.purchase(self.deck, "overclock_cpu")
        self.shop.purchase(self.deck, "overclock_cpu")
        self.shop.purchase(self.deck, "overclock_cpu")
        self.assertEqual(self.deck.overclock_level, 3)

        # 4th time should fail
        ok, msg = self.shop.purchase(self.deck, "overclock_cpu")
        self.assertFalse(ok)
        self.assertIn("maximum level", msg)


if __name__ == "__main__":
    unittest.main()
