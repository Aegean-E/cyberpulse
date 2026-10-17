# cyberpulse

CyberPulse is a retro-cyberpunk terminal hacking simulation game with procedural puzzle nodes, ICE defenses, cyberdeck resource management, and deterministic state transitions.

## ⚡ 30-Second Cold-Start Quick Reference

- **Runtime Prerequisites**: git and Python 3.10+ (AIKit's gates); add this project's own.
- **Canonical Regression Shield Gate**:
  ```bash
  python aikit.py check cyberpulse
  ```

### 🛠️ AIKit Commands (run from the AIKit folder)
| Role | Command |
|---|---|
| Status, task and gates | `python aikit.py status cyberpulse` |
| Phase 4: every gate | `python aikit.py check cyberpulse` |
| Repair memory and map, then check | `python aikit.py fix cyberpulse` |
| Resume an interrupted task | `python aikit.py resume cyberpulse` |

## 📦 What's Inside

```text
cyberpulse/
├── .aikit/                   <- this project's memory: record, ledger, decisions
├── .gitignore                <- transient AIKit state excluded
├── README.md
├── pyproject.toml            <- build and package configuration
├── cyberpulse/               <- core game engine and CLI
└── tests/                    <- unit and integration test suite
```

## 🎮 How to Play

Launch the interactive neural intrusion harness directly:

```bash
# Launch interactive game with default seed
python -m cyberpulse.cli

# Launch with a specific world seed
python -m cyberpulse.cli --seed 42069
```

### In-Game Commands

| Command | Action |
|---|---|
| `scan` | Scan surrounding connected nodes to reveal security levels and puzzle types |
| `hack <node_id>` | Initiate cyber-attack mini-game on discovered target |
| `move <node_id>` | Jack your terminal session into an adjacent breached node |
| `spoof` | Burn 3 CPU cycles to bounce your proxy and reduce security trace by 25% |
| `status` | Display cyberdeck hardware specs, inventory, and connected nodes |
| `save` | Atomically persist your current infiltration state to disk |
| `load` | Restore previous saved game state |
| `quit` | Sever connection and terminate terminal link |

### 🧩 Hacking Mini-Games

1. **Frequency Resonance Tuning**: Match target broadcast frequency within designated tolerance range.
2. **Buffer Overflow Sequence**: Match the memory buffer payload hex sequence without corruption.
3. **Cryptographic Hash Cracking**: Terminal Bulls & Cows style keyword decryptor.

## 🛡️ Architecture & Guarantees

- **Zero Undeclared Dependencies**: Built with 100% pure Python standard library modules (`random`, `json`, `dataclasses`, `pathlib`, `argparse`).
- **Deterministic State Engine**: Every network grid and puzzle sequence can be reproduced using `--seed <int>`.
- **Power-Loss Safe Savegames**: Uses atomic temporary file writes and `fsync` to avoid corrupted save states.
- **Sub-Second Test Shield**: 100% test pass rate in under 0.5s via `python -m unittest discover`.
