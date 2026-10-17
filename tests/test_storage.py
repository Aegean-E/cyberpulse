"""Unit tests for CyberPulse savegame and career profile persistence."""

import shutil
import tempfile
import unittest
from pathlib import Path

from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile
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

    def test_career_save_and_load(self):
        profile = CareerProfile(
            alias="CrashOverride",
            banked_creds=450,
            lifetime_creds=1250,
            successful_runs=4,
            current_streak=2,
            purchased_upgrades=["overclock_cpu"],
        )
        path = self.save_mgr.save_career(profile)
        self.assertTrue(path.exists())

        restored = self.save_mgr.load_career()
        self.assertEqual(restored.alias, "CrashOverride")
        self.assertEqual(restored.banked_creds, 450)
        self.assertEqual(restored.successful_runs, 4)
        self.assertEqual(restored.current_streak, 2)
        self.assertIn("overclock_cpu", restored.purchased_upgrades)

    def test_career_default_fallback(self):
        fallback = self.save_mgr.load_career()
        self.assertEqual(fallback.alias, "ZeroCool")
        self.assertEqual(fallback.successful_runs, 0)


if __name__ == "__main__":
    unittest.main()
