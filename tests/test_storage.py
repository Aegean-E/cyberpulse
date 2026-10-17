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

    def test_load_corrupted_save_with_backup_recovery(self):
        engine = GameEngine(seed=77)
        engine.deck.cryptocreds = 999
        self.save_mgr.save(engine)
        self.save_mgr.save(engine)  # Second save ensures .bak exists

        # Corrupt primary save file
        with open(self.save_mgr.save_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json corrupted ")

        # Recovery from .bak should restore state and quarantine corrupted file
        recovered = self.save_mgr.load()
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.deck.cryptocreds, 999)

        # Check quarantine file was created
        quarantine_files = list(self.temp_dir.glob("savegame.json.corrupt_*"))
        self.assertEqual(len(quarantine_files), 1)

    def test_load_corrupted_career_with_backup_recovery(self):
        profile = CareerProfile(alias="Neo", banked_creds=7000)
        self.save_mgr.save_career(profile)

        # Trigger second save to ensure .bak exists
        profile.banked_creds = 7500
        self.save_mgr.save_career(profile)

        # Corrupt primary career file
        with open(self.save_mgr.career_file, "w", encoding="utf-8") as f:
            f.write("<<<not a json>>>")

        recovered = self.save_mgr.load_career()
        self.assertIn(recovered.banked_creds, (7000, 7500))

    def test_delete_save(self):
        engine = GameEngine(seed=101)
        self.save_mgr.save(engine)
        self.assertTrue(self.save_mgr.save_file.exists())
        self.save_mgr.delete_save()
        self.assertFalse(self.save_mgr.save_file.exists())

    def test_rng_reseeding_on_load(self):
        engine = GameEngine(seed=123)
        engine.state.turns_elapsed = 15
        self.save_mgr.save(engine)

        loaded = self.save_mgr.load()
        self.assertIsNotNone(loaded)
        # Expected roll corresponds to Random(123 + 15)
        import random
        expected_roll = random.Random(123 + 15).random()
        self.assertEqual(loaded.rng.random(), expected_roll)


if __name__ == "__main__":
    unittest.main()

