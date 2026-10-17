"""Unit tests for CyberPulse domain models."""

import unittest
from cyberpulse.models import CyberDeck, GameState, Node, NodeStatus, NodeType


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
        deck = CyberDeck(cryptocreds=500, cpu_cycles=8)
        data = deck.to_dict()
        restored = CyberDeck.from_dict(data)
        self.assertEqual(restored.cryptocreds, 500)
        self.assertEqual(restored.cpu_cycles, 8)

    def test_game_state_roundtrip(self):
        state = GameState(seed=42, current_node_id="node_gateway", trace_percent=25)
        data = state.to_dict()
        restored = GameState.from_dict(data)
        self.assertEqual(restored.seed, 42)
        self.assertEqual(restored.trace_percent, 25)


if __name__ == "__main__":
    unittest.main()
