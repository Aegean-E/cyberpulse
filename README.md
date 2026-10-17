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

### 1. Web Cyberdeck (Visual CRT & Web Audio)
Launch the visual browser-based cyberpunk cyberdeck with interactive 2D node matrix canvas, visual oscilloscope/buffer mini-games, and synthesized 8-bit sound FX:

```bash
# Launch interactive Web Cyberdeck (auto-opens browser at http://127.0.0.1:8420)
python -m cyberpulse.cli --web

# Launch with custom world seed and port
python -m cyberpulse.cli --web --port 9000 --seed 42069
```

### 2. Interactive Terminal CLI
Or operate purely in the retro terminal REPL harness:

```bash
# Launch interactive terminal game with default seed
python -m cyberpulse.cli

# Launch terminal game with custom world seed
python -m cyberpulse.cli --seed 42069
```

### In-Game Commands (Authentic Simulation & Tactical Netrunning)

| Command | Action | Simulation Role |
|---|---|---|
| `myip` / `whoami` | Display player's local CyberDeck identity (`10.99.0.2` / `rig.netrunner.local`) | Virtual localhost identity & rig telemetry |
| `myfiles` / `ls local` | List files on player's local CyberDeck drive (`/home/deck`, `/bin`, `/loot`) | Local rig file inspection & stolen loot archive |
| `cat <file>` | Inspect local cyberdeck files or remote breached host files | Data surveillance & loot inspection |
| `probe <ip>` / `nmap <ip>` | Scan open network ports, service banners, and software versions | Reconnaissance & vulnerability detection |
| `phish <ip>` | Dispatch targeted spear-phishing credential lure to compromise target | Social engineering & security downgrade |
| `exploit <ip> <port>` | Inject zero-day payload against vulnerable open port to acquire root shell | System penetration & breach |
| `ls [ip]` | List virtual directory contents on breached host (`/etc`, `/home`, `/data`) | Target file discovery & intel gathering |
| `steal <file>` / `download` | Exfiltrate data for credits; auto-archives copy to local rig `/loot/` | Data theft & primary heist objective |
| `keylogger [ip]` | Deploy passive background keylogger daemon on breached host (+25 CR/turn) | In-game persistent background surveillance |
| `daemons` | Monitor all active background listener daemons and their credit yields | Passive income & risk telemetry |
| `workshop` | Inspect malware crafting lab recipes and synthesis requirements | In-game virus & exploit workshop |
| `craft <recipe>` | Synthesize custom virus chips (`keylogger_daemon`, `worm_replicator`, etc.) | Custom malware creation |
| `wipe_logs [ip]` | Clear access logs and sanitize intruder timestamps (drops active ICE trace by 20%) | Anti-forensics & trace mitigation |
| `move <ip>` / `ssh <ip>` | Transfer your active terminal session to an adjacent breached host | Network lateral movement |
| `scan` | Scan surrounding connected nodes to reveal topology and IP addresses | Information foraging & strategic autonomy |
| `exploit <chip_name>` | Deploy executable exploit chip (`logic_bomb`, `ghost_protocol`, `worm_replicator`) | Tactical leverage & consumable empowerment |
| `spoof` | Burn 3 CPU cycles to bounce your proxy and reduce security trace by 25% | Risk mitigation & resource trade-offs |
| `cash_out` / `jackout` | Safely disconnect, bank all unbanked credits, and update career dossier | Loss aversion & push-your-luck extraction |
| `shop` | Open the Black Market vendor to inspect permanent hardware upgrades | Anticipation of reward & meta-progression |
| `buy <item_id>` | Purchase permanent cyberdeck upgrades with banked career credits | Long-term investment & competence scaling |
| `career` | View lifetime operative dossier, breach stats, and installed cyberware | Identity, pride & meta-game mastery |
| `status` | Display cyberdeck specs, unbanked credits, and active syndicate contract | HUD awareness & contract progress tracking |
| `save` | Atomically persist your current infiltration state to disk | Power-loss protection & player security |
| `load` | Restore previous saved game state | Resumption fidelity |
| `quit` | Sever connection and terminate terminal link | Clean exit |

### 🕹️ Authentic Hacker Simulation Workflow
1. **Discover & Phish**: Discover subnet routing table via `scan` or `/etc/hosts`. Dispatch social engineering lures with `phish 192.168.1.10` to downgrade security and harvest tokens into local `/loot/`.
2. **Recon & Port Scan**: Scan services with `probe 192.168.1.10` to discover vulnerable ports (e.g. FTP on port 21, MariaDB on port 3306).
3. **Exploit & Breach**: Exploit the vulnerable service via `exploit 192.168.1.10 21` to gain root access.
4. **Deploy Background Daemons**: Plant a listener with `keylogger 192.168.1.10` to passively siphon +25 Creds on every future turn.
5. **Inspect & Steal**: Explore remote directories with `ls`, view contents with `cat /data/corporate_slush_fund.csv`, and steal data with `steal /data/corporate_slush_fund.csv`. The file is automatically archived to your local rig `/loot/`!
6. **Malware Workshop**: Access the malware workshop via `workshop` and synthesize custom viruses with `craft worm_replicator` or `craft keylogger_daemon`.
7. **Sanitize & Cash Out**: Erase intruder traces with `wipe_logs` to drop active ICE trace, then safely extract via `cash_out` to bank your stolen wealth into permanent career meta-progression!

## 🛡️ Architecture & Guarantees

- **Zero Undeclared Dependencies**: Built with 100% pure Python standard library modules (`random`, `json`, `dataclasses`, `pathlib`, `argparse`).
- **Deterministic State Engine**: Every network grid and puzzle sequence can be reproduced using `--seed <int>`.
- **Power-Loss Safe Savegames & Shadow Backup**: Uses atomic temporary file writes, `fsync`, `.bak` shadow recovery, and corruption quarantine to eliminate state loss risk.
- **Dynamic Resource Loop**: Turn-based CPU cooling (+1/turn) and hardware RAM constraints (`security_level * 16` MB).
- **Sub-Second Test Shield**: 100% test pass rate across unit and integration suites in under 0.5s via `python -m unittest discover`.


