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

    def test_find_node_by_ip_and_hostname(self):
        node = self.engine.find_node("192.168.1.10")
        self.assertIsNotNone(node)
        self.assertEqual(node.node_id, "node_proxy_a")

        node_host = self.engine.find_node("alpha.internal")
        self.assertIsNotNone(node_host)
        self.assertEqual(node_host.node_id, "node_proxy_a")

        node_id = self.engine.find_node("node_proxy_a")
        self.assertIsNotNone(node_id)
        self.assertEqual(node_id.ip_address, "192.168.1.10")

    def test_probe_host(self):
        ok, summary, report = self.engine.probe_host("192.168.1.10")
        self.assertTrue(ok)
        self.assertIn("Nmap scan report", summary)
        self.assertIn("192.168.1.10", summary)
        self.assertIsNotNone(report)
        self.assertEqual(report["ip_address"], "192.168.1.10")
        self.assertTrue(any(p["port"] == 21 for p in report["ports"]))
        self.assertGreater(self.engine.state.trace_percent, 0)

    def test_exploit_service(self):
        # Exploit invalid/closed port
        ok, msg = self.engine.exploit_service("192.168.1.10", 9999)
        self.assertFalse(ok)
        self.assertIn("closed or filtered", msg)

        # Exploit open vulnerable FTP port 21
        self.engine.deck.cpu_cycles = 4
        ok, msg = self.engine.exploit_service("192.168.1.10", 21)
        self.assertTrue(ok)
        self.assertIn("EXPLOIT SUCCESSFUL", msg)
        node = self.engine.find_node("192.168.1.10")
        self.assertEqual(node.status, NodeStatus.BREACHED)
        self.assertEqual(self.engine.deck.cpu_cycles, 2)

    def test_virtual_filesystem_simulation(self):
        # Breach node_proxy_a
        self.engine.complete_breach("node_proxy_a")

        # List files
        ok, output, files = self.engine.list_files("192.168.1.10")
        self.assertTrue(ok)
        self.assertIn("Directory listing", output)
        self.assertTrue(len(files) >= 1)

        # Read file
        ok, content_view, raw_text = self.engine.read_file("192.168.1.10", "/home/admin/network_map.txt")
        self.assertTrue(ok)
        self.assertIn("Subnet topology", raw_text)

        # Download / steal file
        creds_before = self.engine.state.unbanked_creds
        ok, dl_msg, vfile = self.engine.download_file("192.168.1.10", "/home/admin/network_map.txt")
        self.assertTrue(ok)
        self.assertIn("EXFILTRATION COMPLETE", dl_msg)
        self.assertIn(vfile.path, self.engine.state.looted_payloads)
        self.assertGreaterEqual(self.engine.state.unbanked_creds, creds_before + vfile.value_creds)

    def test_wipe_logs_trace_reduction(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.state.trace_percent = 50
        ok, msg = self.engine.wipe_logs("192.168.1.10")
        self.assertTrue(ok)
        self.assertIn("LOGS SANITIZED", msg)
        self.assertEqual(self.engine.state.trace_percent, 30)
        self.assertTrue(self.engine.nodes["node_proxy_a"].logs_cleared)

    def test_local_deck_filesystem_and_loot_archiving(self):
        # List local files on rig
        ok, output, local_files = self.engine.list_local_files()
        self.assertTrue(ok)
        self.assertIn("Local Rig Filesystem", output)
        self.assertTrue(len(local_files) >= 2)

        # Read local file
        ok, view, content = self.engine.read_local_file("/home/deck/notes.txt")
        self.assertTrue(ok)
        self.assertIn("NETRUNNER LOG", content)

        # Stealing remote file archives into local /loot/
        self.engine.complete_breach("node_proxy_a")
        self.engine.download_file("192.168.1.10", "/home/admin/network_map.txt")
        self.assertTrue(any(f.path == "/loot/network_map.txt" for f in self.engine.deck.local_filesystem))

    def test_phishing_dispatch(self):
        self.engine.deck.cpu_cycles = 5
        ok, msg, report = self.engine.phish_target("192.168.1.10")
        self.assertIn("PHISHING", msg)
        self.assertIn("target_ip", report)
        self.assertEqual(report["target_ip"], "192.168.1.10")

    def test_craft_virus_workshop(self):
        self.engine.deck.cryptocreds = 200
        ok, msg = self.engine.craft_virus("worm_replicator")
        self.assertTrue(ok)
        self.assertIn("WORKSHOP SYNTHESIS COMPLETE", msg)
        self.assertIn("worm_replicator", self.engine.deck.exploits)
        self.assertEqual(self.engine.deck.cryptocreds, 50)

    def test_deploy_and_tick_keylogger_daemon(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.deck.cpu_cycles = 4
        ok, msg = self.engine.deploy_daemon("192.168.1.10", "keylogger")
        self.assertTrue(ok)
        self.assertIn("DAEMON INITIALIZED", msg)
        self.assertEqual(len(self.engine.deck.active_daemons), 1)

        # Tick daemons
        unbanked_before = self.engine.state.unbanked_creds
        msgs = self.engine.tick_daemons()
        self.assertTrue(len(msgs) >= 1)
        self.assertGreater(self.engine.state.unbanked_creds, unbanked_before)


if __name__ == "__main__":
    unittest.main()


