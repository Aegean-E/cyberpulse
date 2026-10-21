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
        self.assertTrue(contract.wipe_logs_required)

        # The extraction contract is not satisfied by a bare breach.
        self.engine.complete_breach("node_vault_1")
        self.assertFalse(contract.completed)

        # Stealing the named file warns that the logs must still be wiped.
        ok, msg, _ = self.engine.download_file("10.0.4.15", "/data/corporate_slush_fund.csv")
        self.assertTrue(ok)
        self.assertIn("requires logs to be wiped", msg)
        self.assertFalse(contract.completed)

        # Wiping the target host's logs completes the contract and dispatches the next one.
        ok, msg = self.engine.wipe_logs("10.0.4.15")
        self.assertTrue(ok)
        self.assertIn("CONTRACT COMPLETED", msg)
        self.assertTrue(contract.completed)
        self.assertIsNot(self.engine.state.active_contract, contract)

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
        self.engine.state.story_act = 4

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

    def test_firewall_inspection_and_bypass(self):
        # 1. Inspect firewall on node_proxy_b
        ok, msg, fw_dict = self.engine.get_firewall_status("192.168.1.20")
        self.assertTrue(ok)
        self.assertIn("FIREWALL REPORT", msg)
        self.assertIn("Port 22/tcp: [BLOCKED]", msg)

        # 2. Exploit blocked by firewall
        exp_ok, exp_msg = self.engine.exploit_service("192.168.1.20", 22)
        self.assertFalse(exp_ok)
        self.assertIn("FIREWALL BLOCKED", exp_msg)

        # 3. Bypass firewall via port-knocking
        self.engine.deck.cpu_cycles = 4
        by_ok, by_msg = self.engine.bypass_firewall("192.168.1.20", 22, "knock")
        self.assertTrue(by_ok)
        self.assertIn("FIREWALL BYPASSED", by_msg)

        # 4. Exploit now reaches service without firewall block
        self.engine.deck.cpu_cycles = 4
        exp_ok2, exp_msg2 = self.engine.exploit_service("192.168.1.20", 22)
        self.assertTrue(exp_ok2)
        self.assertIn("EXPLOIT SUCCESSFUL", exp_msg2)

    def test_antivirus_status_and_evasion(self):
        # 1. Check AV status
        ok, msg, av_dict = self.engine.get_antivirus_status("192.168.1.20")
        self.assertTrue(ok)
        self.assertIn("ANTIVIRUS REPORT", msg)
        self.assertIn("SentinelCore", msg)

        # 2. Evade AV
        self.engine.deck.cpu_cycles = 4
        ev_ok, ev_msg = self.engine.evade_antivirus("192.168.1.20", "rootkit")
        self.assertTrue(ev_ok)
        self.assertIn("ANTIVIRUS EVADED", ev_msg)
        self.assertTrue(self.engine.nodes["node_proxy_b"].antivirus.evaded)

    def test_cve_catalog_and_exploit_execution(self):
        cves = self.engine.list_cves()
        self.assertEqual(len(cves), 8)
        cve_ids = [c["cve_id"] for c in cves]
        self.assertIn("CVE-2011-2523", cve_ids)
        self.assertIn("CVE-2022-0778", cve_ids)
        self.assertIn("CVE-2025-9901", cve_ids)

        # Exploit with mismatched service
        err_ok, err_msg = self.engine.exploit_service("192.168.1.10", 21, cve_id="cve-2024-6387")
        self.assertFalse(err_ok)
        self.assertIn("Exploit mismatch", err_msg)

        # Universal CVE-2025-9901 works on any vulnerable port
        self.engine.deck.cpu_cycles = 5
        self.engine.deck.ram_mb = 128
        ok, msg = self.engine.exploit_service("192.168.1.10", 21, cve_id="cve-2025-9901")
        self.assertTrue(ok)
        self.assertIn("CVE-2025-9901", msg)
        self.assertIn("EXPLOIT SUCCESSFUL", msg)

    def test_social_engineering_vectors(self):
        self.engine.deck.cpu_cycles = 5
        # 1. Invalid vector
        inv_ok, inv_msg, _ = self.engine.social_engineer("192.168.1.1", vector="invalid_vector")
        self.assertFalse(inv_ok)
        self.assertIn("Invalid vector", inv_msg)

        # 2. Pretext vector against junior admin
        ok, msg, report = self.engine.social_engineer("192.168.1.10", vector="pretext")
        self.assertIn("SOCIAL ENGINEERING", msg)
        self.assertEqual(report["vector"], "pretext")
        self.assertEqual(report["employee"], "Alice Vance")

    def test_game_over_and_jacked_out_guards(self):
        # When game over
        self.engine.state.is_game_over = True
        self.assertFalse(self.engine.spoof_ip()[0])
        self.assertFalse(self.engine.scan_surroundings()[0])
        self.assertFalse(self.engine.use_exploit("192.168.1.1", "PortBypass.sh")[0])
        self.assertFalse(self.engine.list_files()[0])
        self.assertFalse(self.engine.read_file("192.168.1.10", "notes.txt")[0])
        self.assertFalse(self.engine.download_file("192.168.1.10", "notes.txt")[0])
        self.assertFalse(self.engine.list_local_files()[0])
        self.assertFalse(self.engine.read_local_file("credentials.txt")[0])
        self.assertFalse(self.engine.craft_virus("hydra_worm")[0])

        # When jacked out
        self.engine.state.is_game_over = False
        self.engine.state.is_jacked_out = True
        self.assertFalse(self.engine.spoof_ip()[0])
        self.assertFalse(self.engine.scan_surroundings()[0])
        self.assertFalse(self.engine.use_exploit("192.168.1.1", "PortBypass.sh")[0])
        self.assertFalse(self.engine.list_files()[0])
        self.assertFalse(self.engine.read_file("192.168.1.10", "notes.txt")[0])
        self.assertFalse(self.engine.download_file("192.168.1.10", "notes.txt")[0])
        self.assertFalse(self.engine.list_local_files()[0])
        self.assertFalse(self.engine.read_local_file("credentials.txt")[0])
        self.assertFalse(self.engine.craft_virus("hydra_worm")[0])

    def test_defensive_input_sanitization(self):
        self.assertIsNone(self.engine.find_node(None))
        self.assertIsNone(self.engine.find_node(""))
        ok, msg = self.engine.use_exploit(None)
        self.assertFalse(ok)
        self.assertIn("No exploit name specified", msg)

        # Local and remote file read with None/empty
        ok, msg, _ = self.engine.read_local_file(None)
        self.assertFalse(ok)
        self.assertIn("cannot be empty", msg)

        ok, msg = self.engine.craft_virus(None)
        self.assertFalse(ok)
        self.assertIn("Unknown recipe", msg)

    def test_exploit_service_turn_advancement(self):
        self.engine.deck.cpu_cycles = 4
        initial_turns = self.engine.state.turns_elapsed
        ok, _ = self.engine.exploit_service("192.168.1.10", 21, cve_id="cve-2011-2523")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.turns_elapsed, initial_turns + 1)

    def test_complete_breach_is_idempotent(self):
        ok, _ = self.engine.complete_breach("node_proxy_a")
        self.assertTrue(ok)
        unbanked = self.engine.state.unbanked_creds

        ok_again, msg = self.engine.complete_breach("node_proxy_a")

        self.assertFalse(ok_again)
        self.assertIn("already breached", msg)
        self.assertEqual(self.engine.state.unbanked_creds, unbanked)

    def test_worm_replicator_rejects_breached_target_without_consuming_chip(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.deck.exploits.append("worm_replicator")
        unbanked = self.engine.state.unbanked_creds

        ok, msg = self.engine.use_exploit("worm_replicator", "node_proxy_a")

        self.assertFalse(ok)
        self.assertIn("already breached", msg)
        self.assertIn("worm_replicator", self.engine.deck.exploits)
        self.assertEqual(self.engine.state.unbanked_creds, unbanked)

    def test_spoof_reports_actual_reduction(self):
        self.engine.state.trace_percent = 10
        self.engine.deck.cpu_cycles = 5

        ok, msg = self.engine.spoof_ip()

        self.assertTrue(ok)
        self.assertEqual(self.engine.state.trace_percent, 0)
        self.assertIn("reduced by 10%", msg)

    def test_spoof_rejects_zero_trace_without_burning_cpu(self):
        self.engine.deck.cpu_cycles = 5
        ok, msg = self.engine.spoof_ip()
        self.assertFalse(ok)
        self.assertIn("already at 0%", msg)
        self.assertEqual(self.engine.deck.cpu_cycles, 5)

    def test_tick_daemons_stops_after_lockout(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.deck.cpu_cycles = 4
        self.engine.deploy_daemon("192.168.1.10", "keylogger")
        self.engine.state.trace_percent = 99

        self.engine.tick_daemons()

        self.assertTrue(self.engine.state.is_game_over)
        self.assertEqual(self.engine.state.unbanked_creds, 0)

    def test_bypass_and_evade_require_direct_subnet(self):
        self.engine.deck.cpu_cycles = 5

        ok, msg = self.engine.bypass_firewall("10.0.4.15", 3306)
        self.assertFalse(ok)
        self.assertIn("direct subnet range", msg)

        ok, msg = self.engine.evade_antivirus("10.0.4.15")
        self.assertFalse(ok)
        self.assertIn("direct subnet range", msg)

    def test_social_engineering_requires_direct_subnet(self):
        self.engine.nodes["node_vault_1"].status = NodeStatus.DISCOVERED
        ok, msg, _ = self.engine.social_engineer("10.0.4.15", vector="pretext")
        self.assertFalse(ok)
        self.assertIn("out of subnet range", msg)

    def test_wipe_logs_is_idempotent(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.state.trace_percent = 50
        ok, _ = self.engine.wipe_logs("192.168.1.10")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.trace_percent, 30)

        ok_again, msg = self.engine.wipe_logs("192.168.1.10")

        self.assertFalse(ok_again)
        self.assertIn("already sanitized", msg)
        self.assertEqual(self.engine.state.trace_percent, 30)

    def test_probe_advances_daemon_tick(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.deck.cpu_cycles = 4
        self.engine.deploy_daemon("192.168.1.10", "keylogger")
        daemon = self.engine.deck.active_daemons[0]
        turns_before = daemon.turns_active
        unbanked_before = self.engine.state.unbanked_creds

        ok, _, _ = self.engine.probe_host("192.168.1.10")

        self.assertTrue(ok)
        self.assertEqual(daemon.turns_active, turns_before + 1)
        self.assertGreater(self.engine.state.unbanked_creds, unbanked_before)

    def test_pending_puzzle_keeps_attempts_between_calls(self):
        ok, _, puzzle, _ = self.engine.get_or_create_puzzle("node_proxy_a")
        self.assertTrue(ok)
        self.assertIsNotNone(puzzle)
        puzzle.tune(0.0)

        ok_again, _, same_puzzle, _ = self.engine.get_or_create_puzzle("node_proxy_a")

        self.assertTrue(ok_again)
        self.assertIs(puzzle, same_puzzle)
        self.assertEqual(same_puzzle.attempts_left, 2)

        self.engine.clear_pending_puzzle("node_proxy_a")
        _, _, new_puzzle, _ = self.engine.get_or_create_puzzle("node_proxy_a")
        self.assertIsNot(puzzle, new_puzzle)

    def test_settle_career_banks_victory_loot_once(self):
        from cyberpulse.models import CareerProfile

        self.engine.state.story_act = 4
        self.engine.complete_breach("node_central_core")
        self.assertTrue(self.engine.state.is_victory)
        self.engine.state.unbanked_creds = 500
        profile = CareerProfile()

        settled = self.engine.settle_career(profile)

        self.assertTrue(settled)
        self.assertEqual(profile.successful_runs, 1)
        self.assertEqual(profile.banked_creds, 600)
        self.assertEqual(profile.lifetime_creds, 600)
        self.assertEqual(self.engine.state.unbanked_creds, 0)
        self.assertFalse(self.engine.settle_career(profile))
        self.assertEqual(profile.successful_runs, 1)

    def test_exploit_lockout_does_not_claim_root_access(self):
        self.engine.state.trace_percent = 99
        self.engine.deck.cpu_cycles = 4

        ok, msg = self.engine.exploit_service("192.168.1.10", 21, cve_id="cve-2011-2523")

        self.assertFalse(ok)
        self.assertIn("root access was interrupted", msg)
        self.assertEqual(self.engine.nodes["node_proxy_a"].status, NodeStatus.DISCOVERED)
        self.assertTrue(self.engine.state.is_game_over)

    def test_float_seed_is_coerced(self):
        engine = GameEngine(seed=42.9)
        self.assertEqual(engine.seed, 42)
        self.assertEqual(engine.state.seed, 42)
        self.assertTrue(engine.state.active_contract.contract_id.startswith("cnt_042"))

    def test_run_summary_reflects_legacy(self):
        self.engine.state.is_game_over = True
        self.engine.state.best_combo = 5
        self.engine._find_contact("mira").trust = 3
        self.engine._find_contact("kilo").favor_used = True

        summary = self.engine.run_summary()

        self.assertEqual(summary["outcome"], "lockout")
        self.assertEqual(summary["best_combo"], 5)
        self.assertTrue(any("Five clean breaches" in line for line in summary["epilogue"]))
        self.assertTrue(any("Mira" in line for line in summary["epilogue"]))
        self.assertTrue(any("Kilo" in line for line in summary["epilogue"]))
        self.assertTrue(any(c["name"] == "Mira Voss" for c in summary["contacts"]))

    def test_settle_career_records_best_combo_on_failure(self):
        from cyberpulse.models import CareerProfile

        self.engine.state.is_game_over = True
        self.engine.state.best_combo = 4
        profile = CareerProfile()

        self.engine.settle_career(profile)

        self.assertEqual(profile.best_combo, 4)
        self.assertEqual(profile.failed_runs, 1)

    def test_run_summary_victory_marks_main_story_complete(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.complete_breach("node_proxy_b")
        self.engine.complete_breach("node_vault_1")
        self.engine.download_file("10.0.4.15", "/data/corporate_slush_fund.csv")
        self.engine.complete_breach("node_ice_perimeter")
        self.engine.complete_breach("node_central_core")

        summary = self.engine.run_summary()

        self.assertEqual(summary["outcome"], "victory")
        self.assertTrue(summary["main_story_complete"])
        self.assertGreaterEqual(summary["quests_completed_count"], 4)

    def test_mutating_actions_reject_after_victory(self):
        self.engine.state.is_victory = True

        self.assertFalse(self.engine.scan_surroundings()[0])
        self.assertFalse(self.engine.move_to("node_proxy_a")[0])
        self.assertFalse(self.engine.probe_host("192.168.1.10")[0])
        self.assertFalse(self.engine.download_file("192.168.1.10", "/home/admin/network_map.txt")[0])
        self.assertFalse(self.engine.wipe_logs("192.168.1.10")[0])

    def test_story_state_and_contacts_initialize(self):
        self.assertEqual(self.engine.state.story_act, 1)
        self.assertTrue(self.engine.state.story_log)
        self.assertEqual(len(self.engine.state.contacts), 4)
        gateway_quest = self.engine._find_quest("q_gateway")
        self.assertIsNotNone(gateway_quest)
        self.assertTrue(gateway_quest.accepted)
        self.assertFalse(self.engine._find_quest("q_money").accepted)

    def test_overdrive_stacks_combo_and_trace(self):
        start_cpu = self.engine.deck.cpu_cycles
        ok, msg = self.engine.overdrive()
        self.assertTrue(ok)
        self.assertIn("Combo x1", msg)
        self.assertEqual(self.engine.state.combo_streak, 1)
        self.assertEqual(self.engine.state.trace_percent, 8)
        self.assertEqual(self.engine.deck.cpu_cycles, start_cpu - 2)

    def test_break_combo_resets_streak_keeps_best(self):
        self.engine.state.combo_streak = 3
        self.engine.state.best_combo = 3

        broke = self.engine.break_combo("test failure")

        self.assertTrue(broke)
        self.assertEqual(self.engine.state.combo_streak, 0)
        self.assertEqual(self.engine.state.best_combo, 3)
        self.assertTrue(any("COMBO BROKEN" in m for m in self.engine.state.message_log))

        # Breaking an empty combo is a no-op, not a repeated message.
        self.assertFalse(self.engine.break_combo("nothing to break"))

    def test_social_failure_breaks_combo(self):
        self.engine.state.combo_streak = 2
        self.engine.state.best_combo = 2
        self.engine.deck.cpu_cycles = 5

        class RiggedRng:
            def random(self):
                return 0.999

            def randint(self, low, high):
                return low

        self.engine.rng = RiggedRng()
        ok, msg, report = self.engine.social_engineer("192.168.1.10", vector="pretext")

        self.assertFalse(ok)
        self.assertTrue(report["success"] is False)
        self.assertEqual(self.engine.state.combo_streak, 0)
        self.assertEqual(self.engine.state.best_combo, 2)
        self.assertTrue(any("COMBO BROKEN" in m for m in self.engine.state.message_log))

    def test_av_quarantine_breaks_combo(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.deck.cpu_cycles = 6
        ok, _ = self.engine.deploy_daemon("192.168.1.10", "keylogger")
        self.assertTrue(ok)
        self.engine.state.combo_streak = 2
        self.engine.state.best_combo = 2

        node = self.engine.nodes["node_proxy_a"]
        node.antivirus.alert_level = 60

        class RiggedRng:
            def random(self):
                return 0.0

        self.engine.rng = RiggedRng()
        messages = self.engine.tick_daemons()

        self.assertTrue(any("QUARANTINE" in m for m in messages))
        self.assertEqual(self.engine.state.combo_streak, 0)
        self.assertEqual(self.engine.state.best_combo, 2)

    def test_gateway_quest_advances_story_and_unlocks_contact(self):
        self.engine.complete_breach("node_proxy_a")
        quest = self.engine._find_quest("q_gateway")
        self.assertEqual(quest.progress, 1)
        self.assertFalse(quest.completed)

        self.engine.complete_breach("node_proxy_b")

        self.assertTrue(quest.completed)
        self.assertEqual(self.engine.state.story_act, 2)
        self.assertTrue(self.engine._find_quest("q_money").accepted)
        archivist = self.engine._find_contact("archivist")
        self.assertLessEqual(archivist.unlock_act, self.engine.state.story_act)
        self.assertEqual(self.engine.state.combo_streak, 2)
        self.assertEqual(self.engine.state.best_combo, 2)

    def test_main_story_quest_chain_reaches_finale(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.complete_breach("node_proxy_b")
        self.assertEqual(self.engine.state.story_act, 2)

        self.engine.complete_breach("node_vault_1")
        self.engine.download_file("10.0.4.15", "/data/corporate_slush_fund.csv")
        self.assertEqual(self.engine.state.story_act, 3)

        self.engine.complete_breach("node_ice_perimeter")
        self.assertEqual(self.engine.state.story_act, 4)
        self.assertTrue(self.engine._find_quest("q_core").accepted)

        self.engine.complete_breach("node_central_core")
        self.assertEqual(self.engine.state.story_act, 5)
        self.assertTrue(self.engine._find_quest("q_core").completed)
        self.assertTrue(self.engine.state.is_victory)

    def test_contact_job_and_favor(self):
        self.engine.overdrive()
        ok, msg, _ = self.engine.interact_contact("kilo", "favor")
        self.assertTrue(ok)
        self.assertIn("CPU restored", msg)
        self.assertEqual(self.engine.deck.cpu_cycles, self.engine.deck.max_cpu)

        ok, msg, report = self.engine.interact_contact("kilo", "job")
        self.assertTrue(ok)
        self.assertIn("QUEST ACCEPTED", msg)
        self.assertEqual(report["quest_id"], "q_side_craft")
        self.assertTrue(self.engine._find_quest("q_side_craft").accepted)

    def test_locked_contact_rejects_interaction(self):
        ok, msg, _ = self.engine.interact_contact("zero", "talk")
        self.assertFalse(ok)
        self.assertIn("not on the grid yet", msg)

    def test_agent_zero_pact_requires_act_three(self):
        ok, msg, _ = self.engine.interact_contact("zero", "ally")
        self.assertFalse(ok)
        self.assertIn("not on the grid yet", msg)

        self.engine.state.story_act = 2
        ok, msg, _ = self.engine.interact_contact("zero", "ally")
        self.assertFalse(ok)
        self.assertIn("not on the grid yet", msg)

    def test_agent_zero_alliance_branch(self):
        self.engine.state.story_act = 3
        ok, msg, report = self.engine.interact_contact("zero", "ally")

        self.assertTrue(ok)
        self.assertIn("ALLIANCE FORGED", msg)
        self.assertEqual(self.engine.state.story_choice, "zero_ally")
        self.assertEqual(report["choice"], "zero_ally")
        self.assertIn("ghost_protocol", self.engine.deck.exploits)
        zero = self.engine._find_contact("zero")
        self.assertEqual(zero.trust, 3)

        ok_again, msg_again, _ = self.engine.interact_contact("zero", "defy")
        self.assertFalse(ok_again)
        self.assertIn("already chose", msg_again)

        dialogue = next(c["dialogue"] for c in self.engine.list_contacts() if c["contact_id"] == "zero")
        self.assertIn("together", dialogue)
        summary = self.engine.run_summary()
        self.assertTrue(any("Two ghosts" in line for line in summary["epilogue"]))

    def test_agent_zero_defiance_branch(self):
        self.engine.state.story_act = 3
        ok, msg, _ = self.engine.interact_contact("zero", "defy")

        self.assertTrue(ok)
        self.assertIn("DEFIANCE DECLARED", msg)
        self.assertEqual(self.engine.state.story_choice, "zero_defy")
        self.assertEqual(self.engine._find_contact("zero").trust, -1)
        self.assertEqual(self.engine._find_contact("mira").trust, 2)
        summary = self.engine.run_summary()
        self.assertTrue(any("blinked first" in line for line in summary["epilogue"]))

    def test_locked_story_quest_cannot_be_accepted_early(self):
        ok, msg = self.engine.accept_quest("q_core")
        self.assertFalse(ok)
        self.assertIn("not available until the story advances", msg)
        self.assertFalse(self.engine._find_quest("q_core").accepted)

    def test_archivist_favor_reveals_locked_node(self):
        self.engine.state.story_act = 2
        archivist = self.engine._find_contact("archivist")
        before = sum(1 for n in self.engine.nodes.values() if n.status == NodeStatus.LOCKED)
        ok, msg, _ = self.engine.interact_contact("archivist", "favor")
        self.assertTrue(ok)
        after = sum(1 for n in self.engine.nodes.values() if n.status == NodeStatus.LOCKED)
        self.assertEqual(after, before - 1)
        self.assertTrue(archivist.favor_used)

    def test_ensure_story_state_backfills_old_save(self):
        self.engine.state.quests = []
        self.engine.state.contacts = []
        self.engine.state.story_log = []
        self.engine.ensure_story_state()
        self.assertEqual(len(self.engine.state.quests), 7)
        self.assertEqual(len(self.engine.state.contacts), 4)
        self.assertTrue(self.engine.state.story_log)

    def test_out_of_order_ice_breach_still_completes_black_ice_quest(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.move_to("node_proxy_a")
        self.engine.complete_breach("node_ice_perimeter")
        self.engine.move_to("node_gateway")
        self.engine.complete_breach("node_proxy_b")
        self.engine.move_to("node_proxy_a")
        self.engine.complete_breach("node_vault_1")
        self.engine.download_file("10.0.4.15", "/data/corporate_slush_fund.csv")

        self.assertTrue(self.engine._find_quest("q_blackice").completed)
        self.assertEqual(self.engine.state.story_act, 4)
        self.assertTrue(self.engine._find_quest("q_core").accepted)

    def test_out_of_order_file_theft_counts_when_money_quest_unlocks(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.move_to("node_proxy_a")
        self.engine.complete_breach("node_vault_1")
        self.engine.download_file("10.0.4.15", "/data/corporate_slush_fund.csv")
        self.engine.move_to("node_gateway")
        self.engine.complete_breach("node_proxy_b")

        self.assertTrue(self.engine._find_quest("q_money").completed)
        self.assertEqual(self.engine.state.story_act, 3)

    def test_out_of_order_log_wipe_completes_side_quest_when_accepted(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.move_to("node_proxy_a")
        self.engine.complete_breach("node_vault_1")
        self.engine.wipe_logs("10.0.4.15")
        self.engine.move_to("node_gateway")
        self.engine.complete_breach("node_proxy_b")

        ok, _, report = self.engine.interact_contact("archivist", "job")

        self.assertTrue(ok)
        self.assertEqual(report["quest_id"], "q_side_wipe")
        self.assertTrue(self.engine._find_quest("q_side_wipe").completed)

    def test_accept_quest_rejects_terminal_states(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.jackout()
        self.assertFalse(self.engine.accept_quest("q_side_ghost")[0])

        locked_out = GameEngine(seed=42)
        locked_out.state.is_game_over = True
        self.assertFalse(locked_out.accept_quest("q_side_ghost")[0])

        won = GameEngine(seed=42)
        won.state.is_victory = True
        self.assertFalse(won.accept_quest("q_side_ghost")[0])

    def test_core_is_sealed_until_act_four(self):
        self.engine.deck.ram_mb = 128
        self.engine.complete_breach("node_proxy_a")
        self.engine.move_to("node_proxy_a")
        self.engine.complete_breach("node_ice_perimeter")
        self.engine.move_to("node_ice_perimeter")

        ok, msg = self.engine.can_hack_node("node_central_core")
        self.assertFalse(ok)
        self.assertIn("Act IV", msg)

        ok, msg = self.engine.complete_breach("node_central_core")
        self.assertFalse(ok)
        self.assertFalse(self.engine.state.is_victory)

        cpu_before = self.engine.deck.cpu_cycles
        ok, msg = self.engine.exploit_service("172.16.80.1", 8888)
        self.assertFalse(ok)
        self.assertIn("Act IV", msg)
        self.assertEqual(self.engine.deck.cpu_cycles, cpu_before)

    def test_download_contract_respects_trace_limit(self):
        from cyberpulse.models import BountyContract

        contract = BountyContract(
            contract_id="cnt_sector_test",
            title="Sector Bounty",
            target_node_type=NodeType.FIREWALL,
            max_trace_limit=10,
            reward_creds=175,
        )
        self.engine.state.active_contract = contract
        self.engine.state.trace_percent = 50
        self.engine.complete_breach("node_proxy_a")
        self.assertFalse(contract.completed)

        ok, _, _ = self.engine.download_file("192.168.1.10", "/var/log/auth.log")
        self.assertTrue(ok)
        self.assertFalse(contract.completed)

        self.engine.state.trace_percent = 0
        ok, _, _ = self.engine.download_file("192.168.1.10", "/home/admin/network_map.txt")
        self.assertTrue(ok)
        self.assertTrue(contract.completed)


if __name__ == "__main__":
    unittest.main()



