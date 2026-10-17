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


if __name__ == "__main__":
    unittest.main()
