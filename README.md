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
