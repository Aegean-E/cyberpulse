"""Crash-resilient savegame and career profile storage engine for CyberPulse."""

import json
import os
import shutil
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

    def _write_atomic(self, target_path: Path, data: Any) -> Path:
        """Write JSON payload to target_path atomically using tempfile, fsync, and backup."""
        temp_path = self.data_dir / f".tmp_{target_path.name}_{int(time.time() * 1000)}"
        backup_path = target_path.with_suffix(".bak")

        payload = json.dumps(data, indent=2)
        with open(temp_path, "w", encoding="utf-8") as f:
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

        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        return target_path

    def save(self, engine: GameEngine) -> Path:
        """Atomically persist engine state to disk."""
        data = {
            "seed": engine.seed,
            "deck": engine.deck.to_dict(),
            "state": engine.state.to_dict(),
            "nodes": {nid: n.to_dict() for nid, n in engine.nodes.items()},
        }
        return self._write_atomic(self.save_file, data)

    def load(self) -> Optional[GameEngine]:
        """Load and restore engine state from savegame."""
        if not self.save_file.exists():
            return None

        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        engine = GameEngine(seed=data["seed"])
        engine.deck = CyberDeck.from_dict(data["deck"])
        engine.state = GameState.from_dict(data["state"])
        engine.nodes = {nid: Node.from_dict(ndata) for nid, ndata in data["nodes"].items()}
        return engine

    def save_career(self, profile: CareerProfile) -> Path:
        """Atomically persist career meta-progression profile."""
        return self._write_atomic(self.career_file, profile.to_dict())

    def load_career(self) -> CareerProfile:
        """Load persistent career profile or return fresh profile."""
        if not self.career_file.exists():
            return CareerProfile()

        try:
            with open(self.career_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return CareerProfile.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return CareerProfile()
