"""Unit and integration tests for CyberPulse HTTP REST server."""

import json
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from cyberpulse.server import create_server


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

    def test_get_shop(self):
        status, data = self._get("/api/shop")
        self.assertEqual(status, 200)
        self.assertIn("items", data)
        self.assertGreater(len(data["items"]), 0)

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

    def test_static_assets_served(self):
        # GET /
        url = f"{self.base_url}/"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            html = resp.read().decode("utf-8")
            self.assertIn("CYBERPULSE", html)

        # GET /style.css
        url_css = f"{self.base_url}/style.css"
        with urllib.request.urlopen(url_css, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/css", resp.headers.get("Content-Type", ""))
            css = resp.read().decode("utf-8")
            self.assertIn("--font-mono", css)

        # GET /app.js
        url_js = f"{self.base_url}/app.js"
        with urllib.request.urlopen(url_js, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("javascript", resp.headers.get("Content-Type", ""))
            js = resp.read().decode("utf-8")
            self.assertIn("SoundFX", js)

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


if __name__ == "__main__":
    unittest.main()

