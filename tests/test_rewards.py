"""Unit tests for variable-ratio rewards and dopamine loot schedules."""

import random
import unittest
from cyberpulse.models import Node, NodeType
from cyberpulse.rewards import roll_breach_reward


class TestRewards(unittest.TestCase):
    def setUp(self):
        self.node = Node(
            node_id="test_vault",
            name="Crypto Vault",
            node_type=NodeType.DATA_VAULT,
            security_level=2,
            credits_reward=200,
        )

    def test_zero_reward_node(self):
        empty_node = Node(node_id="gate", name="Gate", node_type=NodeType.GATEWAY, security_level=1, credits_reward=0)
        creds, desc, drop = roll_breach_reward(empty_node)
        self.assertEqual(creds, 0)
        self.assertIsNone(drop)

    def test_exploit_chip_drop_threshold(self):
        # Seed that produces roll < 0.10
        rng = random.Random(42)
        # Find seed with drop
        found = False
        for s in range(50):
            r = random.Random(s)
            creds, desc, drop = roll_breach_reward(self.node, rng=r)
            if drop is not None:
                found = True
                self.assertIn("EXPLOIT CHIP", desc)
                self.assertIn(drop, ["logic_bomb", "ghost_protocol", "brute_miner"])
                break
        self.assertTrue(found)

    def test_jackpot_multiplier(self):
        # Find seed that triggers jackpot (0.10 <= roll < 0.30)
        found = False
        for s in range(50):
            r = random.Random(s)
            creds, desc, drop = roll_breach_reward(self.node, rng=r)
            if creds > 200:
                found = True
                self.assertEqual(creds, 500)  # 200 * 2.5
                self.assertIn("JACKPOT", desc)
                break
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
