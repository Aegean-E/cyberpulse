"""Crash-resilient savegame and career profile storage engine for CyberPulse."""

import json
import os
import random
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile, CyberDeck, GameState, Node


class SaveManager:
    """Manages atomic saving and loading of game states and career profiles."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = self.data_dir / "savegame.json"
        self.career_file = self.data_dir / "career.json"

    def _write_atomic(self, target_path: Path, data: Any) -> Optional[Path]:
        """Write JSON payload to target_path atomically; returns None when the replace never lands."""
        backup_path = target_path.with_suffix(".bak")

        payload = json.dumps(data, indent=2)
        fd, temp_name = tempfile.mkstemp(dir=self.data_dir, prefix=f".tmp_{target_path.name}_")
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())

            if target_path.exists():
                shutil.copy2(target_path, backup_path)

            for _ in range(5):
                try:
                    os.replace(temp_path, target_path)
                    return target_path
                except OSError:
                    time.sleep(0.02)
            return None
        finally:
            temp_path.unlink(missing_ok=True)

    def _read_json_with_backup(self, target_path: Path) -> Optional[Any]:
        """Read JSON from target_path, falling back to shadow .bak if corrupted or missing."""
        backup_path = target_path.with_suffix(".bak")

        if target_path.exists():
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                # Quarantine corrupted file
                corrupt_path = self.data_dir / f"{target_path.name}.corrupt_{int(time.time())}"
                try:
                    shutil.move(target_path, corrupt_path)
                except OSError:
                    pass

        # Attempt recovery from shadow backup
        if backup_path.exists():
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        return None

    def save(self, engine: GameEngine) -> Optional[Path]:
        """Atomically persist engine state to disk."""
        data = {
            "seed": engine.seed,
            "deck": engine.deck.to_dict(),
            "state": engine.state.to_dict(),
            "nodes": {nid: n.to_dict() for nid, n in engine.nodes.items()},
        }
        return self._write_atomic(self.save_file, data)

    def load(self) -> Optional[GameEngine]:
        """Load and restore engine state from savegame with backup recovery."""
        data = self._read_json_with_backup(self.save_file)
        if not data or not isinstance(data, dict):
            return None

        try:
            engine = GameEngine(seed=data["seed"])
            engine.deck = CyberDeck.from_dict(data["deck"])
            engine.state = GameState.from_dict(data["state"])
            engine.nodes = {nid: Node.from_dict(ndata) for nid, ndata in data["nodes"].items()}
            engine.rng = random.Random(engine.seed + engine.state.turns_elapsed)
            return engine
        except (KeyError, TypeError):
            return None

    def delete_save(self) -> None:
        """Remove savegame and its shadow backup after completed or failed run."""
        self.save_file.unlink(missing_ok=True)
        self.save_file.with_suffix(".bak").unlink(missing_ok=True)

    def save_career(self, profile: CareerProfile) -> Optional[Path]:
        """Atomically persist career meta-progression profile."""
        return self._write_atomic(self.career_file, profile.to_dict())

    def load_career(self) -> CareerProfile:
        """Load persistent career profile with backup recovery or return fresh profile."""
        data = self._read_json_with_backup(self.career_file)
        if not data or not isinstance(data, dict):
            return CareerProfile()

        try:
            return CareerProfile.from_dict(data)
        except (KeyError, TypeError):
            return CareerProfile()
