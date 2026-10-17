"""Unit tests for CyberPulse game engine."""

import unittest
from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus


class TestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=42)

    def test_initial_state(self):
        curr = self.engine.get_current_node()
        self.assertEqual(curr.node_id, "node_gateway")
        self.assertEqual(self.engine.state.trace_percent, 0)
        self.assertFalse(self.engine.state.is_game_over)
        self.assertFalse(self.engine.state.is_victory)

    def test_scan_reveals_connected(self):
        ok, msg, revealed = self.engine.scan_surroundings()
        self.assertTrue(ok)
        self.assertGreaterEqual(len(revealed), 1)
        # Scan increases trace
        self.assertEqual(self.engine.state.trace_percent, 5)

    def test_cannot_move_to_unbreached_node(self):
        allowed, reason = self.engine.move_to("node_proxy_a")
        self.assertFalse(allowed)
        self.assertIn("unbreached", reason)

    def test_breach_and_move(self):
        self.engine.complete_breach("node_proxy_a")
        self.assertEqual(self.engine.nodes["node_proxy_a"].status, NodeStatus.BREACHED)

        # Now movement is allowed
        ok, msg = self.engine.move_to("node_proxy_a")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.current_node_id, "node_proxy_a")

    def test_trace_lockout_game_over(self):
        self.engine.add_trace(100)
        self.assertTrue(self.engine.state.is_game_over)
        allowed, _ = self.engine.move_to("node_proxy_a")
        self.assertFalse(allowed)

    def test_spoof_ip_reduces_trace(self):
        self.engine.add_trace(50)
        self.assertEqual(self.engine.state.trace_percent, 50)
        ok, msg = self.engine.spoof_ip()
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.trace_percent, 25)

    def test_central_core_breach_victory(self):
        self.engine.complete_breach("node_central_core")
        self.assertTrue(self.engine.state.is_victory)


if __name__ == "__main__":
    unittest.main()
