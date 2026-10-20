"""Integration tests for CyberPulse CLI."""

import io
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from cyberpulse.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

    def run_cli(self, *args):
        stdout_buf = io.StringIO()
        cmd_args = ["--data-dir", str(self.temp_dir)] + list(args)
        exit_code = 0
        try:
            with redirect_stdout(stdout_buf):
                exit_code = main(cmd_args)
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 0
        return exit_code, stdout_buf.getvalue()

    def test_cli_help(self):
        code, out = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("cyberpulse", out)
        self.assertIn("--web", out)
        self.assertIn("--port", out)

    def test_main_menu_quit(self):
        with mock.patch("builtins.input", side_effect=["q"]):
            code, out = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("MAIN MENU", out)
        self.assertIn("Neural link closed", out)

    def test_main_menu_starts_run_then_quits(self):
        with mock.patch("builtins.input", side_effect=["1", "quit"]):
            code, out = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("External Border Gateway", out)
        self.assertIn("Neural link terminated", out)

    def test_story_quests_contacts_and_overdrive_commands(self):
        batch_cmds = "story;quests;contacts;overdrive;status"
        code, out = self.run_cli("--seed", "1337", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("STORY // ACT I", out)
        self.assertIn("MISSION BOARD", out)
        self.assertIn("OPERATIVE CHANNELS", out)
        self.assertIn("NEURAL OVERDRIVE", out)
        self.assertIn("Combo: x1", out)

    def test_world_news_commands_and_hud_grid_line(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "world;news;status")
        self.assertEqual(code, 0)
        self.assertIn("LIVING GRID // CITY PULSE", out)
        self.assertIn("Grid Alert:", out)
        self.assertIn("GRID NEWS WIRE", out)
        self.assertIn("Grid:", out)
        self.assertIn("Market:", out)

    def test_lay_low_command_and_shift_doctrine(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "lay_low 2;world;status")
        self.assertEqual(code, 0)
        self.assertIn("LAY LOW", out)
        self.assertIn("Ghosted the connection for 2 turn", out)
        self.assertIn("Doctrine:", out)
        self.assertIn("Shift:", out)
        self.assertIn("Re-secured hosts:", out)

    def test_lay_low_rejects_bad_turn_count(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "lay_low later;lay_low 9")
        self.assertEqual(code, 0)
        self.assertIn("Usage: lay_low", out)
        self.assertIn("Lay low accepts 1-3 turns", out)

    def test_shop_command_reports_market_index(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "shop")
        self.assertEqual(code, 0)
        self.assertIn("Market index: x", out)

    def test_agent_zero_alliance_after_act_three(self):
        batch_cmds = (
            "hack node_proxy_a;hack node_proxy_b;move node_proxy_a;"
            "hack node_vault_1;move node_vault_1;steal /data/corporate_slush_fund.csv;"
            "contact zero ally;contacts"
        )
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("ALLIANCE FORGED", out)
        self.assertIn("ACT III", out)
        self.assertIn("Agent Zero", out)

    def test_jackout_records_best_combo_in_career(self):
        batch_cmds = "overdrive;overdrive;jackout;career"
        code, out = self.run_cli("--seed", "1337", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("RUN LEGACY", out)
        self.assertIn("Best Neural Combo: x2", out)

    def test_contact_job_and_favor_commands(self):
        batch_cmds = "overdrive;contact kilo favor;contact kilo job;quests"
        code, out = self.run_cli("--seed", "1337", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("CPU restored", out)
        self.assertIn("QUEST ACCEPTED", out)
        self.assertIn("Script Kiddie No More", out)

    def test_batch_infiltration_playthrough(self):
        # Scan, hack proxy a, move to proxy a, spoof trace, save game
        batch_cmds = "scan;hack node_proxy_a;move node_proxy_a;spoof;save"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("Scanned", out)
        self.assertIn("breached", out)
        self.assertIn("Transferred terminal session", out)
        self.assertIn("IP Proxy bounced", out)
        self.assertIn("Infiltration progress saved", out)

        # Test loading the saved session
        code, out_load = self.run_cli("--seed", "1337", "--exec", "load;status")
        self.assertEqual(code, 0)
        self.assertIn("Loaded saved infiltration session", out_load)
        self.assertIn("Subnet Router Alpha", out_load)

    def test_jackout_command(self):
        # Hack proxy a, then jack out safely
        batch_cmds = "hack node_proxy_a;jackout;career"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("SAFE EXTRACTION", out)
        self.assertIn("RUN LEGACY", out)
        self.assertIn("Career progression profile updated", out)
        self.assertIn("HACKER CAREER DOSSIER", out)
        self.assertIn("Heists Cleared:   1 successful", out)

    def test_shop_and_buy_command(self):
        # View shop and buy overclock_cpu
        batch_cmds = "shop;buy overclock_cpu;status"
        code, out = self.run_cli("--seed", "1337", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("BLACK MARKET CYBER-VENDOR", out)
        # Deck starts with 100 creds, overclock_cpu costs 150 creds -> should report insufficient funds
        self.assertIn("Insufficient funds", out)
        self.assertNotIn("Unknown command: 'buy'", out)

    def test_career_progression_across_sessions(self):
        # Session 1: Hack proxy a and jackout safely to bank credits
        self.run_cli("--seed", "1337", "--auto-solve", "--exec", "hack node_proxy_a;jackout")

        # Session 2: Fresh CLI start should load career profile into active deck
        code, out = self.run_cli("--seed", "9999", "--exec", "status;career")
        self.assertEqual(code, 0)
        self.assertIn("Heists Cleared:   1 successful", out)
        # Deck funds should match banked creds (> 100)
    def test_exploit_command(self):
        # Exploit usage: try using logic_bomb without having it, then load it and deploy
        code, out = self.run_cli("--seed", "1337", "--exec", "exploit logic_bomb node_proxy_a")
        self.assertEqual(code, 0)
        self.assertIn("not loaded in cyberdeck firmware", out)

    def test_ram_insufficient_message_in_cli(self):
        # Reach Act IV and stand adjacent to the central core with the default 64MB deck
        batch_cmds = (
            "hack node_proxy_a;hack node_proxy_b;move node_proxy_a;"
            "hack node_vault_1;steal 10.0.4.15 /data/corporate_slush_fund.csv;"
            "hack node_ice_perimeter;move node_ice_perimeter;hack node_central_core"
        )
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("INSUFFICIENT RAM", out)

    def test_simulation_cli_workflow(self):
        batch_cmds = (
            "probe 192.168.1.10;"
            "exploit 192.168.1.10 21;"
            "move 192.168.1.10;"
            "ls;"
            "cat /home/admin/network_map.txt;"
            "steal /home/admin/network_map.txt;"
            "wipe_logs;"
            "cash_out"
        )
        code, out = self.run_cli("--seed", "1337", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("Nmap scan report for alpha.internal", out)
        self.assertIn("EXPLOIT SUCCESSFUL", out)
        self.assertIn("Transferred terminal session to 'Subnet Router Alpha'", out)
        self.assertIn("Directory listing for alpha.internal", out)
        self.assertIn("Subnet topology routing table", out)
        self.assertIn("EXFILTRATION COMPLETE: Stole '/home/admin/network_map.txt'", out)
        self.assertIn("LOGS SANITIZED", out)
        self.assertIn("SAFE EXTRACTION", out)

    def test_cli_virtual_rig_and_phishing_commands(self):
        batch_cmds = (
            "myip;"
            "myfiles;"
            "cat /home/deck/notes.txt;"
            "phish 192.168.1.10;"
            "workshop;"
            "craft trace_cleaner;"
            "daemons"
        )
        code, out = self.run_cli("--seed", "1337", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("Cyberdeck Local Identity", out)
        self.assertIn("10.99.0.2", out)
        self.assertIn("Local Rig Filesystem", out)
        self.assertIn("NETRUNNER LOG", out)
        self.assertIn("PHISHING", out)
        self.assertIn("NETRUNNER MALWARE SYNTHESIS BAY", out)
        self.assertIn("WORKSHOP SYNTHESIS COMPLETE", out)
        self.assertIn("ACTIVE BACKGROUND MALWARE DAEMONS", out)


    def test_cli_cyber_warfare_commands(self):
        batch_cmds = (
            "cve;"
            "firewall 192.168.1.20;"
            "bypass 192.168.1.20 22 knock;"
            "av 192.168.1.20;"
            "evade 192.168.1.20 rootkit;"
            "social 192.168.1.10 pretext;"
            "exploit 192.168.1.10 21 cve-2011-2523"
        )
        code, out = self.run_cli("--seed", "1337", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("WEAPONIZED CVE VULNERABILITY EXPLOIT CATALOG", out)
        self.assertIn("FIREWALL REPORT", out)
        self.assertIn("Port 22/tcp: [BLOCKED]", out)
        self.assertIn("FIREWALL BYPASSED", out)
        self.assertIn("ANTIVIRUS REPORT", out)
        self.assertIn("ANTIVIRUS EVADED", out)
        self.assertIn("SOCIAL ENGINEERING SUCCESS", out)
        self.assertIn("CVE-2011-2523", out)
        self.assertIn("EXPLOIT SUCCESSFUL", out)

    def test_handle_run_completion_in_batch_mode(self):
        from cyberpulse.cli import handle_run_completion
        from cyberpulse.engine import GameEngine
        from cyberpulse.storage import SaveManager

        save_mgr = SaveManager(self.temp_dir)
        engine = GameEngine(seed=42)

        # 1. No completion when game is active
        self.assertIsNone(handle_run_completion(engine, save_mgr))

        # 2. Victory completion banks unbanked loot
        engine.state.is_victory = True
        engine.state.unbanked_creds = 250
        prof = handle_run_completion(engine, save_mgr)
        self.assertIsNotNone(prof)
        self.assertEqual(prof.successful_runs, 1)
        self.assertEqual(prof.current_streak, 1)
        self.assertEqual(prof.banked_creds, 350)
        self.assertEqual(engine.deck.cryptocreds, 350)
        self.assertEqual(engine.state.unbanked_creds, 0)

        # A terminal run is settled exactly once.
        self.assertIsNone(handle_run_completion(engine, save_mgr))

        # 3. Game-over completion on a separate run
        game_over_engine = GameEngine(seed=42)
        game_over_engine.state.is_game_over = True
        prof2 = handle_run_completion(game_over_engine, save_mgr)
        self.assertIsNotNone(prof2)
        self.assertEqual(prof2.failed_runs, 1)
        self.assertEqual(prof2.current_streak, 0)


    def test_lifetime_creds_not_double_counted(self):
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", "hack node_proxy_a;jackout;career")
        self.assertEqual(code, 0)
        first_banked = int(re.search(r"Banked Funds:\s+(\d+)", out).group(1))
        first_lifetime = int(re.search(r"Lifetime Stolen:\s+(\d+)", out).group(1))

        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", "hack node_proxy_a;jackout;career")
        self.assertEqual(code, 0)
        second_banked = int(re.search(r"Banked Funds:\s+(\d+)", out).group(1))
        second_lifetime = int(re.search(r"Lifetime Stolen:\s+(\d+)", out).group(1))

        self.assertEqual(second_lifetime - first_lifetime, second_banked - first_banked)

    def test_bypass_rejects_non_numeric_port(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "bypass 192.168.1.20 abc")
        self.assertEqual(code, 0)
        self.assertIn("Invalid port 'abc'", out)

    def test_minigame_eof_stops_batch_without_traceback(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            code, out = self.run_cli("--seed", "1337", "--exec", "hack node_proxy_a")
        self.assertEqual(code, 0)
        self.assertIn("Input stream closed", out)

    def test_cli_reuses_pending_puzzle_attempts(self):
        from cyberpulse.cli import execute_hack_puzzle
        from cyberpulse.engine import GameEngine

        engine = GameEngine(seed=1337)
        ok, _, puzzle, _ = engine.get_or_create_puzzle("node_proxy_a")
        self.assertTrue(ok)
        puzzle.target_freq = 50.0
        puzzle.tolerance = 0.1
        puzzle.attempts_left = 1

        with mock.patch("builtins.input", return_value="50.0"):
            solved = execute_hack_puzzle(engine, "node_proxy_a")

        self.assertTrue(solved)
        self.assertEqual(engine.nodes["node_proxy_a"].status, "BREACHED")
    def test_cli_hunter_and_counter_commands(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "hunter")
        self.assertEqual(code, 0)
        self.assertIn("NETWATCH COUNTER-INFILTRATION RADAR", out)
        self.assertIn("Radar Status: CLEAR", out)

    def test_start_launcher_function(self):
        import start

        with mock.patch.object(start.cli, "main", return_value=0) as mock_main:
            ret = start.start([])
            self.assertEqual(ret, 0)
            mock_main.assert_called_with(["--web"])

            ret_custom = start.start(["--seed", "42", "--exec", "status"])
            self.assertEqual(ret_custom, 0)
            mock_main.assert_called_with(["--seed", "42", "--exec", "status"])


if __name__ == "__main__":
    unittest.main()



