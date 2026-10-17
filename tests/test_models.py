"""Unit tests for CyberPulse domain models."""

import unittest
from cyberpulse.models import (
    BountyContract,
    CareerProfile,
    CyberDeck,
    GameState,
    Node,
    NodeStatus,
    NodeType,
    RewardType,
)


class TestModels(unittest.TestCase):
    def test_node_roundtrip(self):
        node = Node(
            node_id="n1",
            name="Proxy Server",
            node_type=NodeType.FIREWALL,
            security_level=2,
            status=NodeStatus.DISCOVERED,
            connected_ids=["n2"],
            trace_rate=15,
            credits_reward=100,
        )
        data = node.to_dict()
        restored = Node.from_dict(data)
        self.assertEqual(restored.node_id, "n1")
        self.assertEqual(restored.node_type, NodeType.FIREWALL)
        self.assertEqual(restored.credits_reward, 100)

    def test_deck_roundtrip(self):
        deck = CyberDeck(cryptocreds=500, cpu_cycles=8, ice_dampener_level=1)
        data = deck.to_dict()
        restored = CyberDeck.from_dict(data)
        self.assertEqual(restored.cryptocreds, 500)
        self.assertEqual(restored.cpu_cycles, 8)
        self.assertEqual(restored.ice_dampener_level, 1)

    def test_game_state_roundtrip(self):
        contract = BountyContract(contract_id="c1", title="Heist", target_node_type=NodeType.DATA_VAULT)
        state = GameState(
            seed=42,
            current_node_id="node_gateway",
            trace_percent=25,
            unbanked_creds=150,
            active_contract=contract,
        )
        data = state.to_dict()
        restored = GameState.from_dict(data)
        self.assertEqual(restored.seed, 42)
        self.assertEqual(restored.trace_percent, 25)
        self.assertEqual(restored.unbanked_creds, 150)
        self.assertIsNotNone(restored.active_contract)
        self.assertEqual(restored.active_contract.contract_id, "c1")

    def test_career_profile_roundtrip(self):
        profile = CareerProfile(alias="Phantom", banked_creds=1200, current_streak=3)
        data = profile.to_dict()
        restored = CareerProfile.from_dict(data)
        self.assertEqual(restored.alias, "Phantom")
        self.assertEqual(restored.banked_creds, 1200)
        self.assertEqual(restored.current_streak, 3)


if __name__ == "__main__":
    unittest.main()
