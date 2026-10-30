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

    def test_contract_briefing_and_job_clock(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "contract;status")

        self.assertEqual(code, 0)
        self.assertIn("SYNDICATE JOB BOARD", out)
        self.assertIn("POSTED OFFERS", out)
        self.assertIn("accept_job", out)
        self.assertIn("Deadline", out)
        self.assertIn("Rush", out)
        self.assertIn("Job Clock", out)
        self.assertIn("PRIORITY RISK", out)

    def test_contract_expiry_is_surfaced_in_cli(self):
        batch = ";".join(["lay_low 3"] * 9)
        code, out = self.run_cli("--seed", "1337", "--exec", batch)

        self.assertEqual(code, 0)
        self.assertIn("CONTRACT EXPIRED", out)
        self.assertIn("job offer(s)", out)
        self.assertIn("accept_job", out)

    def test_decline_contract_command_opens_the_board(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "contracts;decline_contract;contracts")

        self.assertEqual(code, 0)
        self.assertIn("CONTRACT DECLINED", out)
        self.assertIn("ACTIVE:    none", out)
        self.assertIn("POSTED OFFERS", out)

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

    def test_batch_named_slot_round_trip(self):
        batch_cmds = "scan;hack node_proxy_a;move node_proxy_a;save 2"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)

        self.assertEqual(code, 0)
        self.assertIn("SLOT 2", out)
        self.assertTrue((self.temp_dir / "savegame_slot2.json").exists())

        code, out_load = self.run_cli("--seed", "999", "--exec", "load 2;status")

        self.assertEqual(code, 0)
        self.assertIn("Loaded saved infiltration session", out_load)
        self.assertIn("SLOT 2", out_load)
        self.assertIn("Subnet Router Alpha", out_load)

    def test_saves_command_lists_manual_slots(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "save 1;save 3;saves")

        self.assertEqual(code, 0)
        self.assertIn("SAVED RUNS", out)
        self.assertIn("SLOT 1", out)
        self.assertIn("SLOT 3", out)

    def test_named_slot_round_trip_and_rename(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "save 2 Night Run;saves")
        self.assertEqual(code, 0)
        self.assertIn("SLOT 2", out)
        self.assertIn("Night Run", out)

        code, out = self.run_cli("--seed", "1337", "--exec", "rename 2 Vault Run;saves")
        self.assertEqual(code, 0)
        self.assertIn("Vault Run", out)
        self.assertNotIn("Night Run", out)

    def test_delete_slot_command_requires_an_explicit_slot(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "save 1;save 2;delete 1;saves")

        self.assertEqual(code, 0)
        self.assertIn("Deleted SLOT 1", out)
        self.assertFalse((self.temp_dir / "savegame.json").exists())
        self.assertTrue((self.temp_dir / "savegame_slot2.json").exists())
        self.assertIn("SLOT 2", out)

        code, out = self.run_cli("--seed", "1337", "--exec", "delete")
        self.assertEqual(code, 0)
        self.assertIn("Usage: delete <1|2|3|auto>", out)

    def test_batch_commands_autosave_state_changes(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "scan")

        self.assertEqual(code, 0)
        self.assertTrue((self.temp_dir / "autosave.json").exists())

    def test_invalid_save_slot_reports_usage(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "save 9")

        self.assertEqual(code, 0)
        self.assertIn("Usage: save [1|2|3]", out)
        self.assertFalse((self.temp_dir / "savegame.json").exists())

    def test_jackout_purges_owned_slots_and_autosave(self):
        batch_cmds = "hack node_proxy_a;move node_proxy_a;save 2;scan;jackout"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)

        self.assertEqual(code, 0)
        self.assertIn("SAFE EXTRACTION", out)
        self.assertFalse((self.temp_dir / "savegame_slot2.json").exists())
        self.assertFalse((self.temp_dir / "autosave.json").exists())

    def test_replay_starts_a_run_from_an_archived_seed(self):
        batch_cmds = "hack node_proxy_a;jackout;replay 1;status"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)

        self.assertEqual(code, 0)
        self.assertIn("Replaying run 1", out)
        self.assertIn("seed 1337", out)
        self.assertIn("External Border Gateway", out)

    def test_replay_rejects_an_out_of_range_index(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "replay 9")

        self.assertEqual(code, 0)
        self.assertIn("Usage: replay <1-5>", out)

    def test_rival_commands_inspect_and_counter(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "rival;counter_rival;rival")

        self.assertEqual(code, 0)
        self.assertIn("RIVAL NETRUNNER", out)
        self.assertIn("Counter-traced", out)
        self.assertIn("contract(s) stolen", out)

    def test_tutorial_command_lists_the_first_run_steps(self):
        code, out = self.run_cli("--exec", "tutorial")

        self.assertEqual(code, 0)
        self.assertIn("FIRST RUN CHECKLIST", out)
        self.assertIn("SCAN THE GRID", out)
        self.assertIn("EXTRACT", out)

        code, out = self.run_cli("--exec", "scan;tutorial")
        self.assertEqual(code, 0)
        self.assertIn("[x] SCAN", out)

    def test_difficulty_flag_reaches_the_hud(self):
        code, out = self.run_cli("--difficulty", "hard", "--exec", "status")

        self.assertEqual(code, 0)
        self.assertIn("Difficulty: HARD", out)

    def test_daily_flag_uses_the_date_seed(self):
        with mock.patch("cyberpulse.cli.daily_run", return_value=("2026-10-30", 20261030)):
            code, out = self.run_cli("--daily", "--exec", "status")

        self.assertEqual(code, 0)
        self.assertIn("DAILY RUN 2026-10-30", out)
        self.assertIn("seed 20261030", out)
        self.assertIn("DAILY MODIFIER:", out)

    def test_daily_career_dossier_shows_the_streak(self):
        with mock.patch("cyberpulse.cli.daily_run", return_value=("2026-10-30", 20261030)):
            code, out = self.run_cli(
                "--daily", "--auto-solve", "--exec", "hack node_proxy_a;jackout;career"
            )

        self.assertEqual(code, 0)
        self.assertIn("Daily Streak:     1 (Best: 1)", out)

    def test_dead_mans_switch_does_not_become_a_career_upgrade(self):
        batch_cmds = "hack node_proxy_a;move node_proxy_a;jackout;buy dead_mans_switch;career"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)

        self.assertEqual(code, 0)
        self.assertIn("Dead Man's Switch armed", out)
        self.assertIn("Hardware Rig:     None", out)

    def test_career_dossier_lists_recent_runs(self):
        batch_cmds = "hack node_proxy_a;jackout;career"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)

        self.assertEqual(code, 0)
        self.assertIn("RECENT RUNS", out)
        self.assertIn("JACKOUT", out)
        self.assertIn("SEED 1337", out)
        self.assertIn("COMBO x1", out)
        self.assertIn("Milestones", out)
        self.assertIn("First Extraction", out)
        self.assertIn("HALL OF FAME", out)
        self.assertIn("Score:", out)

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

    def test_failed_puzzle_breaks_combo(self):
        from cyberpulse.cli import execute_hack_puzzle
        from cyberpulse.engine import GameEngine

        engine = GameEngine(seed=1337)
        ok, _, puzzle, _ = engine.get_or_create_puzzle("node_proxy_a")
        self.assertTrue(ok)
        puzzle.target_freq = 50.0
        puzzle.tolerance = 0.1
        engine.state.combo_streak = 3
        engine.state.best_combo = 3

        with mock.patch("builtins.input", side_effect=["1.0", "2.0", "3.0"]):
            solved = execute_hack_puzzle(engine, "node_proxy_a")

        self.assertFalse(solved)
        self.assertNotEqual(engine.nodes["node_proxy_a"].status, "BREACHED")
        self.assertEqual(engine.state.combo_streak, 0)
        self.assertEqual(engine.state.best_combo, 3)
        self.assertTrue(any("COMBO BROKEN" in m for m in engine.state.message_log))

    def test_cli_hunter_and_counter_commands(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "hunter")
        self.assertEqual(code, 0)
        self.assertIn("NETWATCH COUNTER-INFILTRATION RADAR", out)
        self.assertIn("Radar Status: CLEAR", out)

        code, out = self.run_cli("--seed", "1337", "--exec", "counter hunter")
        self.assertEqual(code, 0)
        self.assertNotIn("Unknown countermeasure method", out)
        self.assertIn("No active NetWatch hunters", out)

    def test_unknown_command_reports_and_tactical_commands_run(self):
        code, out = self.run_cli("--seed", "1337", "--exec", "bogus_command")
        self.assertEqual(code, 0)
        self.assertIn("Unknown command: 'bogus_command'", out)

        code, out = self.run_cli(
            "--seed",
            "1337",
            "--exec",
            "stance stealth;quickhack node_proxy_a;proxy node_proxy_a;unproxy",
        )
        self.assertEqual(code, 0)
        self.assertIn("Stance shifted to [STEALTH]", out)
        self.assertIn("QUICKHACK LANDED", out)
        self.assertIn("Proxy tunnel established", out)
        self.assertIn("Proxy tunnel severed", out)

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



