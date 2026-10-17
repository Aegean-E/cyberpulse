"""Unit tests for CyberPulse game engine."""

import unittest
from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus, NodeType


class TestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=42)

    def test_initial_state(self):
        curr = self.engine.get_current_node()
        self.assertEqual(curr.node_id, "node_gateway")
        self.assertEqual(self.engine.state.trace_percent, 0)
        self.assertFalse(self.engine.state.is_game_over)
        self.assertFalse(self.engine.state.is_victory)
        self.assertFalse(self.engine.state.is_jacked_out)
        self.assertIsNotNone(self.engine.state.active_contract)

    def test_scan_reveals_connected(self):
        ok, msg, revealed = self.engine.scan_surroundings()
        self.assertTrue(ok)
        self.assertGreaterEqual(len(revealed), 1)
        self.assertEqual(self.engine.state.trace_percent, 5)

    def test_cannot_move_to_unbreached_node(self):
        allowed, reason = self.engine.move_to("node_proxy_a")
        self.assertFalse(allowed)
        self.assertIn("unbreached", reason)

    def test_breach_and_move(self):
        self.engine.complete_breach("node_proxy_a")
        self.assertEqual(self.engine.nodes["node_proxy_a"].status, NodeStatus.BREACHED)

        ok, msg = self.engine.move_to("node_proxy_a")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.current_node_id, "node_proxy_a")

    def test_trace_lockout_burns_unbanked_loot(self):
        self.engine.complete_breach("node_proxy_a")
        self.assertGreater(self.engine.state.unbanked_creds, 0)

        # Trigger trace lockout
        self.engine.add_trace(100)
        self.assertTrue(self.engine.state.is_game_over)
        self.assertEqual(self.engine.state.unbanked_creds, 0)
        self.assertEqual(len(self.engine.state.looted_payloads), 0)

    def test_jackout_safely_banks_loot(self):
        self.engine.complete_breach("node_proxy_a")
        unbanked = self.engine.state.unbanked_creds
        initial_creds = self.engine.deck.cryptocreds

        ok, msg = self.engine.jackout()
        self.assertTrue(ok)
        self.assertTrue(self.engine.state.is_jacked_out)
        self.assertEqual(self.engine.deck.cryptocreds, initial_creds + unbanked)
        self.assertEqual(self.engine.state.unbanked_creds, 0)

    def test_ice_dampener_reduces_trace_gain(self):
        engine_normal = GameEngine(seed=10)
        engine_normal.add_trace(20)
        normal_trace = engine_normal.state.trace_percent

        engine_damped = GameEngine(seed=10)
        engine_damped.deck.ice_dampener_level = 2
        engine_damped.add_trace(20)
        damped_trace = engine_damped.state.trace_percent

        self.assertLess(damped_trace, normal_trace)

    def test_bounty_contract_fulfillment(self):
        contract = self.engine.state.active_contract
        self.assertIsNotNone(contract)
        target_type = contract.target_node_type

        # Find node matching contract type
        target_node = next(n for n in self.engine.nodes.values() if n.node_type == target_type)
        self.engine.complete_breach(target_node.node_id)

        # First contract completed and new contract dispatched
        self.assertIsNotNone(self.engine.state.active_contract)
        self.assertGreater(self.engine.state.unbanked_creds, contract.reward_creds)

    def test_cpu_regeneration(self):
        self.engine.deck.cpu_cycles = 4
        self.engine.deck.max_cpu = 10
        recovered = self.engine.regenerate_cpu(2)
        self.assertEqual(recovered, 2)
        self.assertEqual(self.engine.deck.cpu_cycles, 6)

        # Cannot exceed max_cpu
        self.engine.regenerate_cpu(10)
        self.assertEqual(self.engine.deck.cpu_cycles, 10)

    def test_ram_capacity_check(self):
        # Central core has Sec Level 5 -> requires 80MB RAM
        core = self.engine.nodes["node_central_core"]
        self.assertEqual(core.security_level, 5)

        # Move to adjacent node
        self.engine.state.current_node_id = "node_ice_perimeter"

        # Default deck has 64MB RAM -> should fail RAM check
        self.engine.deck.ram_mb = 64
        ok, msg = self.engine.can_hack_node("node_central_core")
        self.assertFalse(ok)
        self.assertIn("INSUFFICIENT RAM", msg)

        # Upgrading deck RAM to 96MB -> satisfies requirement
        self.engine.deck.ram_mb = 96
        ok, msg = self.engine.can_hack_node("node_central_core")
        self.assertTrue(ok)

    def test_use_exploit_ghost_protocol(self):
        self.engine.state.trace_percent = 50
        self.engine.deck.exploits.append("ghost_protocol")
        ok, msg = self.engine.use_exploit("ghost_protocol")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.trace_percent, 10)
        self.assertNotIn("ghost_protocol", self.engine.deck.exploits)

    def test_use_exploit_logic_bomb(self):
        self.engine.deck.exploits.append("logic_bomb")
        ok, msg = self.engine.use_exploit("logic_bomb", "node_proxy_a")
        self.assertTrue(ok)
        self.assertEqual(self.engine.nodes["node_proxy_a"].status, NodeStatus.BREACHED)
        self.assertNotIn("logic_bomb", self.engine.deck.exploits)

    def test_use_exploit_brute_miner(self):
        self.engine.deck.exploits.append("brute_miner")
        unbanked_before = self.engine.state.unbanked_creds
        ok, msg = self.engine.use_exploit("brute_miner")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.unbanked_creds, unbanked_before + 150)
        self.assertGreater(self.engine.state.trace_percent, 0)
        self.assertNotIn("brute_miner", self.engine.deck.exploits)


if __name__ == "__main__":
    unittest.main()
