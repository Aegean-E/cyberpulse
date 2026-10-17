"""Crash-resilient savegame storage engine for CyberPulse."""

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

from cyberpulse.engine import GameEngine
from cyberpulse.models import CyberDeck, GameState, Node


class SaveManager:
    """Manages atomic saving and loading of game states."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = self.data_dir / "savegame.json"

    def save(self, engine: GameEngine) -> Path:
        """Atomically persist engine state to disk."""
        data = {
            "seed": engine.seed,
            "deck": engine.deck.to_dict(),
            "state": engine.state.to_dict(),
            "nodes": {nid: n.to_dict() for nid, n in engine.nodes.items()},
        }

        temp_path = self.data_dir / f".tmp_save_{int(time.time() * 1000)}"
        backup_path = self.save_file.with_suffix(".bak")

        payload = json.dumps(data, indent=2)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())

        if self.save_file.exists():
            shutil.copy2(self.save_file, backup_path)

        for _ in range(5):
            try:
                os.replace(temp_path, self.save_file)
                return self.save_file
            except OSError:
                time.sleep(0.02)

        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        return self.save_file

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
