"""Unit tests for the first-run tutorial checklist."""

import unittest

from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus, NodeType


class TestTutorial(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=1337)

    def _done_map(self):
        return {step["step_id"]: step["done"] for step in self.engine.tutorial_progress()}

    def test_fresh_run_has_no_completed_steps(self):
        done = self._done_map()

        self.assertEqual(len(done), 5)
        self.assertFalse(any(done.values()))

    def test_steps_track_persisted_progress(self):
        self.engine.state.scanned = True
        self.engine.state.probed_nodes = ["node_gateway"]
        self.engine.nodes["node_proxy_a"].status = NodeStatus.BREACHED
        self.engine.state.looted_payloads = ["/data/ledger.csv"]

        done = self._done_map()

        self.assertTrue(done["scan"])
        self.assertTrue(done["probe"])
        self.assertTrue(done["breach"])
        self.assertTrue(done["loot"])
        self.assertFalse(done["jackout"])

        self.engine.state.is_jacked_out = True
        self.assertTrue(self._done_map()["jackout"])

    def test_scan_command_sets_the_scan_flag(self):
        self.assertFalse(self.engine.state.scanned)

        ok, _, _ = self.engine.scan_surroundings()

        self.assertTrue(ok)
        self.assertTrue(self.engine.state.scanned)


if __name__ == "__main__":
    unittest.main()
