"""Unit tests for CyberPulse savegame persistence."""

import shutil
import tempfile
import unittest
from pathlib import Path

from cyberpulse.engine import GameEngine
from cyberpulse.storage import SaveManager


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)
        self.save_mgr = SaveManager(self.temp_dir)

    def test_save_and_load(self):
        engine = GameEngine(seed=42)
        engine.deck.cryptocreds = 850
        engine.state.trace_percent = 35

        path = self.save_mgr.save(engine)
        self.assertTrue(path.exists())

        loaded = self.save_mgr.load()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.seed, 42)
        self.assertEqual(loaded.deck.cryptocreds, 850)
        self.assertEqual(loaded.state.trace_percent, 35)

    def test_load_nonexistent(self):
        self.assertIsNone(self.save_mgr.load())


if __name__ == "__main__":
    unittest.main()
