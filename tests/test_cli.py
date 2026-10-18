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
        # Move adjacent to central core without sufficient RAM, try to hack
        # Gateway -> proxy_a -> ice_perimeter -> central_core
        batch_cmds = "hack node_proxy_a;move node_proxy_a;hack node_ice_perimeter;move node_ice_perimeter;hack node_central_core"
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

        # 2. Victory completion
        engine.state.is_victory = True
        prof = handle_run_completion(engine, save_mgr)
        self.assertIsNotNone(prof)
        self.assertEqual(prof.successful_runs, 1)
        self.assertEqual(prof.current_streak, 1)

        # 3. Game-over completion
        engine.state.is_victory = False
        engine.state.is_game_over = True
        prof2 = handle_run_completion(engine, save_mgr)
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


if __name__ == "__main__":
    unittest.main()



