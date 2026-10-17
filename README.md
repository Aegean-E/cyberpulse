# cyberpulse

CyberPulse is a retro-cyberpunk terminal hacking simulation game designed around empirical behavioral psychology, featuring procedural puzzle nodes, ICE defenses, push-your-luck extraction mechanics, variable-ratio reward schedules, near-miss striatal feedback, and persistent career progression.

## ⚡ 30-Second Cold-Start Quick Reference

- **Runtime Prerequisites**: git and Python 3.10+ (AIKit's gates).
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
├── LICENSE                   <- MIT Open Source License
├── README.md
├── pyproject.toml            <- build and package configuration
├── cyberpulse/               <- core game engine and CLI
│   ├── __init__.py
│   ├── cli.py                <- interactive terminal interface & REPL
│   ├── engine.py             <- deterministic game state coordinator
│   ├── models.py             <- frozen dataclasses & domain state models
│   ├── network.py            <- procedural network grid generator
│   ├── puzzles.py            <- cyber-intrusion puzzle nodes & near-miss detection
│   ├── rewards.py            <- variable-ratio loot tables & reward schedules
│   ├── server.py             <- zero-dependency HTTP REST & cyberdeck server
│   ├── shop.py               <- black market tech vendor & hardware catalog
│   ├── static/               <- Web Cyberdeck UI (HTML, CSS, JS)
│   │   ├── app.js
│   │   ├── index.html
│   │   └── style.css
│   └── storage.py            <- atomic persistence & career dossier management
└── tests/                    <- sub-second unit & integration test suite
    ├── __init__.py
    ├── test_cli.py
    ├── test_engine.py
    ├── test_init.py
    ├── test_models.py
    ├── test_network.py
    ├── test_puzzles.py
    ├── test_rewards.py
    ├── test_server.py
    ├── test_shop.py
    └── test_storage.py
```

## 🧠 Behavioral Psychology & Engagement Mechanics

CyberPulse's mechanics are grounded in cognitive neuroscience and behavioral game design:

1. **Variable Ratio Reinforcement Schedules (Skinner / Schultz Dopamine Reward Prediction Error)**:
   - Node breach rewards utilize randomized reward schedules (70% standard yield, 20% high-yield 2.5x jackpot, 10% rare hardware chip).
   - Unpredictable payoff magnitude induces striatal dopamine bursts, maximizing engagement compared to fixed rewards.
2. **Near-Miss Effect & Striatal Dopamine Response (Clark et al., 2009)**:
   - Narrow failures (frequency within 1 Hz, keyword within 1 letter) trigger explicit near-miss sensory feedback.
   - Neuroimaging proves near-misses activate the same reward pathways (nucleus accumbens and anterior insula) as wins, driving re-engagement and persistent play.
3. **Push-Your-Luck & Loss Aversion (Kahneman & Tversky Prospect Theory)**:
   - Breached credits remain *unbanked* during an active run. Reaching 100% ICE trace triggers Burnout Lockout, destroying all unbanked bounty.
   - Operatives must weigh continuing deeper into secured sectors versus extracting safely via `jackout`.
4. **Zeigarnik Effect (Incomplete Contract Tension)**:
   - Active Syndicate Bounty Contracts track unfulfilled goals (e.g. breach 2 encryption nodes). Unfinished objectives create cognitive tension that motivates session continuation.
5. **Autonomy & Competence Loop (Ryan & Deci Self-Determination Theory - PENS)**:
   - Tactical agency through branching network topologies, upgrade pathways, and cyberdeck customization in the Black Market vendor.

## 🎮 How to Play

Launch the interactive neural intrusion harness directly:

```bash
# Launch interactive game with default seed
python -m cyberpulse.cli

# Launch with a specific world seed
python -m cyberpulse.cli --seed 42069
```

### In-Game Commands

| Command | Action | Behavioral Design Role |
|---|---|---|
| `scan` | Scan surrounding connected nodes to reveal security levels and puzzle types | Information foraging & strategic autonomy |
| `hack <node_id>` | Initiate cyber-attack mini-game on discovered target | Competence & skill expression |
| `exploit <name> [target]` | Deploy executable exploit chip (`logic_bomb`, `ghost_protocol`, `brute_miner`) | Tactical leverage & consumable empowerment |
| `move <node_id>` | Jack your terminal session into an adjacent breached node | Territory expansion & spatial agency |
| `spoof` | Burn 3 CPU cycles to bounce your proxy and reduce security trace by 25% | Risk mitigation & resource trade-offs |
| `jackout` | Safely disconnect, bank all unbanked credits, and update career dossier | Loss aversion & push-your-luck extraction |
| `shop` | Open the Black Market vendor to inspect permanent hardware upgrades | Anticipation of reward & meta-progression |
| `buy <item_id>` | Purchase permanent cyberdeck upgrades with banked career credits | Long-term investment & competence scaling |
| `career` | View lifetime operative dossier, breach stats, and installed cyberware | Identity, pride & meta-game mastery |
| `status` | Display cyberdeck specs, unbanked credits, and active syndicate contract | HUD awareness & contract progress tracking |
| `save` | Atomically persist your current infiltration state to disk | Power-loss protection & player security |
| `load` | Restore previous saved game state | Resumption fidelity |
| `quit` | Sever connection and terminate terminal link | Clean exit |

### 🧩 Hacking Mini-Games

1. **Frequency Resonance Tuning**: Match target broadcast frequency within designated tolerance range. Narrow misses trigger near-miss excitation alerts.
2. **Buffer Overflow Sequence**: Match memory buffer payload hex sequence without corruption.
3. **Cryptographic Hash Cracking**: Terminal Bulls & Cows style keyword decryptor with character feedback.

## 🛡️ Architecture & Guarantees

- **Zero Undeclared Dependencies**: Built with 100% pure Python standard library modules (`random`, `json`, `dataclasses`, `pathlib`, `argparse`).
- **Deterministic State Engine**: Every network grid and puzzle sequence can be reproduced using `--seed <int>`.
- **Power-Loss Safe Savegames & Shadow Backup**: Uses atomic temporary file writes, `fsync`, `.bak` shadow recovery, and corruption quarantine to eliminate state loss risk.
- **Dynamic Resource Loop**: Turn-based CPU cooling (+1/turn) and hardware RAM constraints (`security_level * 16` MB).
- **Sub-Second Test Shield**: 100% test pass rate across unit and integration suites in under 0.5s via `python -m unittest discover`.


