"""Unit and integration tests for CyberPulse HTTP REST server."""

import json
import shutil
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from cyberpulse.server import CyberdeckSession, create_server


class TestCyberdeckServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp())
        # Bind to port 0 so the OS assigns an ephemeral free port
        cls.server = create_server(host="127.0.0.1", port=0, data_dir=cls.temp_dir, seed=1337)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _get(self, path: str):
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, json.loads(data)

    def _post(self, path: str, payload: dict):
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, json.loads(data)

    def test_get_state(self):
        status, data = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(data["seed"], 1337)
        self.assertIn("node_gateway", data["nodes"])
        self.assertEqual(data["current_node"]["node_id"], "node_gateway")
        self.assertIn("deck", data)
        self.assertIn("career", data)
        self.assertIn("lethal", data["extraction_risk"])
        contract = data["state"]["active_contract"]
        self.assertEqual(contract["risk_tier"], "priority")
        self.assertGreater(contract["expires_turn"], 0)
        self.assertGreater(contract["bonus_creds"], 0)
        self.assertEqual(len(data["state"]["contract_offers"]), 3)

    def test_get_shop(self):
        status, data = self._get("/api/shop")
        self.assertEqual(status, 200)
        self.assertIn("items", data)
        self.assertGreater(len(data["items"]), 0)

    def test_get_world_state_and_grid_fields(self):
        status, res = self._get("/api/world")
        self.assertEqual(status, 200)
        self.assertIn("clock", res["world"])
        self.assertIn("alert_level", res["world"])
        self.assertIn("shift_effect", res["world"])
        self.assertIn("news", res)

        status, data = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("world", data)
        self.assertEqual(data["world"]["alert_level"], 10)

    def test_market_markup_reaches_shop_endpoint(self):
        session = self.server.RequestHandlerClass.server_session
        session.engine.state.world.market_index = 1.25
        try:
            status, res = self._get("/api/shop")
            self.assertEqual(status, 200)
            self.assertEqual(res["market_multiplier"], 1.25)
            overclock = next(i for i in res["items"] if i["item_id"] == "overclock_cpu")
            self.assertEqual(overclock["cost"], 188)
            self.assertEqual(overclock["base_cost"], 150)
        finally:
            session.engine.state.world.market_index = 1.0

    def test_get_career(self):
        status, data = self._get("/api/career")
        self.assertEqual(status, 200)
        self.assertIn("alias", data)
        self.assertIn("banked_creds", data)

    def test_action_scan_and_spoof(self):
        # Scan
        status, res = self._post("/api/action", {"action": "scan"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertIn("Scanned", res["message"])

        # Spoof
        status, res_spoof = self._post("/api/action", {"action": "spoof"})
        self.assertEqual(status, 200)
        self.assertTrue(res_spoof["ok"])

    def test_puzzle_endpoint_and_solve(self):
        # Request frequency puzzle on proxy_a
        status, pdata = self._get("/api/puzzle?node_id=node_proxy_a")
        self.assertEqual(status, 200)
        self.assertTrue(pdata["ok"])
        self.assertEqual(pdata["puzzle_type"], "frequency")

        # Guess wrong frequency
        status, res = self._post("/api/puzzle/solve", {"guess": 10.0})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertFalse(res["solved"])

    def test_static_not_found(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/missing_asset.xyz")
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()

    def test_static_path_traversal_blocked(self):
        # Raw socket: urllib would normalize dot segments before sending, hiding the defect.
        # Two levels up from cyberpulse/static/ reaches the repository root README.md.
        with socket.create_connection(("127.0.0.1", self.port), timeout=3) as sock:
            sock.sendall(b"GET /../../README.md HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        status_line = response.split(b"\r\n", 1)[0]
        self.assertIn(b"404", status_line)

    def test_static_assets_served(self):
        # GET /
        url = f"{self.base_url}/"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            html = resp.read().decode("utf-8")
            self.assertIn("CYBERPULSE", html)
            self.assertIn('id="grid-ticker"', html)
            self.assertIn('id="grid-alert"', html)
            self.assertIn('id="grid-shift-effect"', html)
            self.assertIn('id="btn-lay-low"', html)

        # GET /style.css
        url_css = f"{self.base_url}/style.css"
        with urllib.request.urlopen(url_css, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/css", resp.headers.get("Content-Type", ""))
            css = resp.read().decode("utf-8")
            self.assertIn("--font-mono", css)
            self.assertIn(".grid-bar", css)

        # GET /app.js
        url_js = f"{self.base_url}/app.js"
        with urllib.request.urlopen(url_js, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("javascript", resp.headers.get("Content-Type", ""))
            js = resp.read().decode("utf-8")
            self.assertIn("SoundFX", js)
            self.assertIn("renderGridTicker", js)
            self.assertIn("handleLayLow", js)
            self.assertIn("grid-shift-effect", js)

    def test_server_simulation_actions(self):
        # 1. Probe proxy a
        status, probe_res = self._post("/api/action", {"action": "probe", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(probe_res["ok"])
        self.assertIn("Nmap scan report", probe_res["message"])

        # 2. Exploit FTP port 21
        status, exp_res = self._post("/api/action", {"action": "exploit_service", "target": "192.168.1.10", "port": 21})
        self.assertEqual(status, 200)
        self.assertTrue(exp_res["ok"])
        self.assertIn("EXPLOIT SUCCESSFUL", exp_res["message"])

        # 3. List files
        status, ls_res = self._post("/api/action", {"action": "list_files", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(ls_res["ok"])
        self.assertTrue(len(ls_res["files"]) >= 1)

        # 4. Read file
        status, cat_res = self._post("/api/action", {"action": "read_file", "target": "192.168.1.10", "path": "/home/admin/network_map.txt"})
        self.assertEqual(status, 200)
        self.assertTrue(cat_res["ok"])
        self.assertIn("Subnet topology", cat_res["content"])

        # 5. Download file
        status, dl_res = self._post("/api/action", {"action": "download_file", "target": "192.168.1.10", "path": "/home/admin/network_map.txt"})
        self.assertEqual(status, 200)
        self.assertTrue(dl_res["ok"])
        self.assertIn("EXFILTRATION COMPLETE", dl_res["message"])

        # 6. Wipe logs
        status, wipe_res = self._post("/api/action", {"action": "wipe_logs", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(wipe_res["ok"])
        self.assertIn("LOGS SANITIZED", wipe_res["message"])

    def test_get_workshop_and_local_files(self):
        # 1. Test GET /api/workshop
        status, data = self._get("/api/workshop")
        self.assertEqual(status, 200)
        self.assertIn("recipes", data)
        self.assertGreater(len(data["recipes"]), 0)

        # 2. Test GET /api/local_files
        status, ldata = self._get("/api/local_files")
        self.assertEqual(status, 200)
        self.assertEqual(ldata["ip"], "10.99.0.2")
        self.assertEqual(ldata["hostname"], "rig.netrunner.local")
        self.assertIsInstance(ldata["files"], list)
        self.assertIsInstance(ldata["daemons"], list)

    def test_server_phish_craft_and_daemon(self):
        # 1. Phish target
        status, phish_res = self._post("/api/action", {"action": "phish", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(phish_res["ok"])
        self.assertIn("PHISHING SUCCESS", phish_res["message"])

        # 2. Deploy daemon fails when target is not breached
        status, d_fail = self._post("/api/action", {"action": "deploy_daemon", "target": "192.168.1.10", "daemon_type": "keylogger"})
        self.assertEqual(status, 200)
        self.assertFalse(d_fail["ok"])
        self.assertIn("not breached", d_fail["message"])

        # Breach host via exploit service
        self._post("/api/action", {"action": "exploit_service", "target": "192.168.1.10", "port": 21})

        # Deploy daemon succeeds now that host is breached
        status, d_res = self._post("/api/action", {"action": "deploy_daemon", "target": "192.168.1.10", "daemon_type": "keylogger"})
        self.assertEqual(status, 200)
        self.assertTrue(d_res["ok"])
        self.assertIn("DAEMON INITIALIZED", d_res["message"])

        # 3. Craft invalid recipe gives error
        try:
            status, craft_err = self._post("/api/action", {"action": "craft", "recipe": "non_existent_recipe"})
            self.assertEqual(status, 200)
            self.assertFalse(craft_err["ok"])
            self.assertIn("Unknown recipe", craft_err["message"])
        finally:
            # Reset server session state for subsequent test isolation
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_get_cves_firewall_antivirus(self):
        # 1. GET /api/cves
        status, cve_data = self._get("/api/cves")
        self.assertEqual(status, 200)
        self.assertIn("cves", cve_data)
        self.assertGreaterEqual(len(cve_data["cves"]), 5)
        cve_ids = [c["cve_id"] for c in cve_data["cves"]]
        self.assertIn("CVE-2023-38606", cve_ids)

        # 2. GET /api/firewall
        status, fw_data = self._get("/api/firewall?ip=192.168.1.10")
        self.assertEqual(status, 200)
        self.assertTrue(fw_data["ok"])
        self.assertIn("firewall", fw_data)
        self.assertTrue(fw_data["firewall"]["enabled"])
        self.assertGreater(len(fw_data["firewall"]["rules"]), 0)

        # 3. GET /api/antivirus
        status, av_data = self._get("/api/antivirus?ip=192.168.1.10")
        self.assertEqual(status, 200)
        self.assertTrue(av_data["ok"])
        self.assertIn("antivirus", av_data)
        self.assertIn("DefenderBasic", av_data["antivirus"]["name"])

    def test_firewall_bypass_evade_and_social(self):
        try:
            # 1. Bypass blocked port 22 on proxy_b
            status, bp_res = self._post("/api/action", {
                "action": "bypass",
                "target": "192.168.1.20",
                "port": 22,
                "method": "knock",
            })
            self.assertEqual(status, 200)
            self.assertTrue(bp_res["ok"])
            self.assertIn("FIREWALL BYPASSED", bp_res["message"])
            self.assertIn("Port 22/tcp rule deactivated", bp_res["message"])

            # 2. Evade AV on proxy_a
            status, ev_res = self._post("/api/action", {
                "action": "evade",
                "target": "192.168.1.10",
                "method": "rootkit",
            })
            self.assertEqual(status, 200)
            self.assertTrue(ev_res["ok"])
            self.assertIn("ANTIVIRUS EVADED", ev_res["message"])

            # 3. Multi-vector social engineering on proxy_a
            status, soc_res = self._post("/api/action", {
                "action": "social",
                "target": "192.168.1.10",
                "vector": "pretext",
            })
            self.assertEqual(status, 200)
            self.assertTrue(soc_res["ok"])
            self.assertIn("SOCIAL ENGINEERING SUCCESS", soc_res["message"])

            # 4. Exploit service specifying known CVE
            status, exp_cve = self._post("/api/action", {
                "action": "exploit_service",
                "target": "192.168.1.10",
                "port": 21,
                "cve_id": "CVE-2011-2523",
            })
            self.assertEqual(status, 200)
            self.assertTrue(exp_cve["ok"])
            self.assertIn("CVE-2011-2523", exp_cve["message"])
        finally:
            self._post("/api/action", {"action": "reset", "seed": 1337})


    def test_malformed_port_is_rejected_with_json_error(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/api/action", {"action": "bypass", "target": "192.168.1.20", "port": "not-a-number"})
        self.assertEqual(ctx.exception.code, 400)
        payload = json.loads(ctx.exception.read().decode("utf-8"))
        ctx.exception.close()
        self.assertFalse(payload["ok"])

    def test_craft_accepts_recipe_name_from_web_client(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})

        status, res = self._post("/api/action", {"action": "craft", "recipe": "trace_cleaner"})

        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertIn("trace_cleaner", res["state"]["deck"]["exploits"])

    def test_json_responses_do_not_enable_wildcard_cors(self):
        with urllib.request.urlopen(f"{self.base_url}/api/state", timeout=3.0) as resp:
            self.assertIsNone(resp.headers.get("Access-Control-Allow-Origin"))

    def test_reset_accepts_float_seed(self):
        status, res = self._post("/api/action", {"action": "reset", "seed": 42.9})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertEqual(res["state"]["seed"], 42)

    def test_reset_rejects_invalid_seed(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/api/action", {"action": "reset", "seed": "not-a-seed"})
        self.assertEqual(ctx.exception.code, 400)
        payload = json.loads(ctx.exception.read().decode("utf-8"))
        ctx.exception.close()
        self.assertFalse(payload["ok"])

    def test_puzzle_retry_keeps_remaining_attempts(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, first = self._get("/api/puzzle?node_id=node_proxy_a")
        self.assertEqual(status, 200)
        self.assertEqual(first["attempts_left"], 3)

        self._post("/api/puzzle/solve", {"guess": 0.0})
        status, second = self._get("/api/puzzle?node_id=node_proxy_a")

        self.assertEqual(status, 200)
        self.assertEqual(second["attempts_left"], 2)

    def test_buffer_near_miss_grants_one_web_retry_then_locks_host(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        _, puzzle = self._get("/api/puzzle?node_id=node_proxy_b")
        target_seq = puzzle["target_seq"]
        near_seq = [target_seq[0], "ZZ"]

        _, first = self._post("/api/puzzle/solve", {"guess": near_seq})
        self.assertFalse(first["solved"])
        self.assertTrue(first["near_miss"])
        self.assertTrue(first["near_miss_bonus"])
        self.assertIn("NEAR-MISS SURGE", first["message"])

        _, second = self._post("/api/puzzle/solve", {"guess": near_seq})
        self.assertFalse(second["solved"])
        self.assertFalse(second["near_miss_bonus"])
        self.assertIn("HOST LOCKDOWN", second["message"])
        self.assertGreater(second["state"]["nodes"]["node_proxy_b"]["lockdown_until_turn"], 0)

    def test_victory_settles_career_once(self):
        data_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data_dir, ignore_errors=True)
        session = CyberdeckSession(data_dir=data_dir, seed=7)
        session.engine.state.is_victory = True
        session.engine.state.unbanked_creds = 175
        session.engine.state.best_combo = 3

        first = session.get_full_state()
        second = session.get_full_state()

        self.assertEqual(first["career"]["successful_runs"], 1)
        self.assertEqual(second["career"]["successful_runs"], 1)
        self.assertEqual(second["career"]["banked_creds"], 275)
        self.assertEqual(second["career"]["best_combo"], 3)
        self.assertEqual(second["state"]["unbanked_creds"], 0)
        self.assertEqual(second["run_summary"]["outcome"], "victory")

    def test_game_over_settles_failed_run_once(self):
        data_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data_dir, ignore_errors=True)
        session = CyberdeckSession(data_dir=data_dir, seed=7)
        session.engine.state.is_game_over = True

        first = session.get_full_state()
        second = session.get_full_state()

        self.assertEqual(first["career"]["failed_runs"], 1)
        self.assertEqual(second["career"]["failed_runs"], 1)

    def test_craft_persists_banked_spend(self):
        session = self.server.RequestHandlerClass.server_session
        session.save_mgr.career_file.unlink(missing_ok=True)
        session.save_mgr.career_file.with_suffix(".bak").unlink(missing_ok=True)
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, res = self._post("/api/action", {"action": "craft", "recipe": "trace_cleaner"})

        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertEqual(res["state"]["deck"]["cryptocreds"], 20)
        self.assertEqual(res["state"]["career"]["banked_creds"], 20)

    def test_web_settlement_does_not_delete_unowned_save(self):
        data_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data_dir, ignore_errors=True)
        session = CyberdeckSession(data_dir=data_dir, seed=7)
        saved = session.save_mgr.save(session.engine)
        self.assertIsNotNone(saved)
        self.assertTrue(session.save_mgr.save_file.exists())

        session.engine.state.is_victory = True
        session.get_full_state()

        self.assertTrue(session.save_mgr.save_file.exists())

    def test_state_includes_story_quests_and_contacts(self):
        status, res = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("story", res)
        self.assertIn("run_summary", res)
        self.assertIn("quests", res)
        self.assertIn("contacts", res)
        self.assertEqual(res["story"]["act"], 1)
        self.assertEqual(res["run_summary"]["outcome"], "active")
        self.assertTrue(any(q["quest_id"] == "q_gateway" for q in res["quests"]))
        self.assertTrue(any(c["contact_id"] == "mira" for c in res["contacts"]))

    def test_overdrive_action(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, res = self._post("/api/action", {"action": "overdrive"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertEqual(res["state"]["state"]["combo_streak"], 1)
        self.assertEqual(res["state"]["state"]["trace_percent"], 8)
        self.assertEqual(res["state"]["deck"]["cpu_cycles"], 8)

    def test_contact_talk_job_and_favor_actions(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, res = self._post("/api/action", {"action": "contact", "contact_id": "kilo", "mode": "talk"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertIn("Kilo", res["message"])

        status, res = self._post("/api/action", {"action": "contact", "contact_id": "kilo", "mode": "job"})
        self.assertTrue(res["ok"])
        self.assertIn("QUEST ACCEPTED", res["message"])
        self.assertTrue(any(q["quest_id"] == "q_side_craft" and q["accepted"] for q in res["state"]["quests"]))

        self._post("/api/action", {"action": "overdrive"})
        status, res = self._post("/api/action", {"action": "contact", "contact_id": "kilo", "mode": "favor"})
        self.assertTrue(res["ok"])
        self.assertIn("CPU restored", res["message"])
        self.assertEqual(res["state"]["deck"]["cpu_cycles"], res["state"]["deck"]["max_cpu"])

    def test_agent_zero_alliance_action(self):
        session = self.server.RequestHandlerClass.server_session
        session.engine.state.story_act = 3
        try:
            status, res = self._post("/api/action", {
                "action": "contact",
                "contact_id": "zero",
                "mode": "ally",
            })
            self.assertEqual(status, 200)
            self.assertTrue(res["ok"])
            self.assertIn("ALLIANCE FORGED", res["message"])
            self.assertEqual(res["state"]["story"]["choice"], "zero_ally")
            self.assertEqual(res["state"]["story"]["choice_label"], "ALLIED WITH AGENT ZERO")
            self.assertTrue(any(
                c["contact_id"] == "zero" and not c["pact_available"]
                for c in res["state"]["contacts"]
            ))
        finally:
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_accept_quest_action(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, res = self._post("/api/action", {"action": "accept_quest", "quest_id": "q_side_ghost"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertTrue(any(q["quest_id"] == "q_side_ghost" and q["accepted"] for q in res["state"]["quests"]))

    def test_contract_board_decline_and_accept_action(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        _, declined = self._post("/api/action", {"action": "decline_contract"})
        self.assertTrue(declined["ok"])
        self.assertIsNone(declined["state"]["state"]["active_contract"])
        offers = declined["state"]["state"]["contract_offers"]
        self.assertEqual(len(offers), 3)
        offer_id = offers[0]["contract_id"]
        self._post("/api/action", {"action": "lay_low", "turns": 1})

        _, accepted = self._post(
            "/api/action", {"action": "accept_contract", "contract_id": offer_id}
        )

        self.assertTrue(accepted["ok"])
        active = accepted["state"]["state"]["active_contract"]
        self.assertEqual(active["contract_id"], offer_id)
        self.assertGreater(active["expires_turn"], 0)
        self.assertEqual(len(accepted["state"]["state"]["contract_offers"]), 3)

    def test_accept_quest_after_jackout_is_rejected(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        try:
            status, res = self._post("/api/action", {"action": "jackout"})
            self.assertTrue(res["ok"])

            status, res = self._post("/api/action", {"action": "accept_quest", "quest_id": "q_side_ghost"})

            self.assertEqual(status, 200)
            self.assertFalse(res["ok"])
            self.assertIn("jacked out", res["message"])
        finally:
            # Restore the shared session so later tests do not inherit the jacked-out run.
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_static_assets_do_not_wait_for_session_lock(self):
        session = self.server.RequestHandlerClass.server_session
        acquired = threading.Event()
        release = threading.Event()

        def hold_session_lock():
            with session.lock:
                acquired.set()
                release.wait(3)

        thread = threading.Thread(target=hold_session_lock, daemon=True)
        thread.start()
        self.assertTrue(acquired.wait(1))
        try:
            with urllib.request.urlopen(f"{self.base_url}/style.css", timeout=1.0) as resp:
                self.assertEqual(resp.status, 200)
        finally:
            release.set()
            thread.join(2)

    def test_get_world_and_state_contains_hunters(self):
        status, data = self._get("/api/world")
        self.assertEqual(status, 200)
        self.assertIn("world", data)
        self.assertIn("active_hunters_count", data["world"])
        self.assertIn("hunters", data["world"])
        self.assertIn("nearest_hunter_distance", data["world"])

        status, state = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("world", state)
        self.assertIn("hunters", state["world"])

    def test_counter_hunter_api_action(self):
        # When no hunter active
        status, res = self._post("/api/action", {"action": "counter", "method": "logic_bomb"})
        self.assertEqual(status, 200)
        self.assertFalse(res["ok"])
        self.assertIn("No active NetWatch hunters", res["message"])

    def test_lay_low_api_action(self):
        session = self.server.RequestHandlerClass.server_session
        engine = session.engine
        world = engine.state.world
        saved = (
            world.alert_level,
            world.minute,
            world.day,
            world.turns_since_event,
            engine.state.trace_percent,
            engine.deck.cpu_cycles,
            engine.state.turns_elapsed,
        )
        world.alert_level = 0
        world.turns_since_event = -50
        engine.state.trace_percent = 0
        engine.deck.cpu_cycles = 0
        start_turns = engine.state.turns_elapsed
        try:
            status, res = self._post("/api/action", {"action": "lay_low", "turns": 2})
            self.assertEqual(status, 200)
            self.assertTrue(res["ok"])
            self.assertIn("LAY LOW", res["message"])
            self.assertEqual(res["state"]["state"]["turns_elapsed"], start_turns + 2)
            self.assertEqual(res["state"]["deck"]["cpu_cycles"], 2)
            self.assertIn("shift_effect", res["state"]["world"])

            status, alias = self._post("/api/action", {"action": "wait", "turns": 1})
            self.assertEqual(status, 200)
            self.assertTrue(alias["ok"])
            self.assertIn("LAY LOW", alias["message"])
        finally:
            (
                world.alert_level,
                world.minute,
                world.day,
                world.turns_since_event,
                engine.state.trace_percent,
                engine.deck.cpu_cycles,
                engine.state.turns_elapsed,
            ) = saved


if __name__ == "__main__":
    unittest.main()


