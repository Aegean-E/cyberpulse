# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: Architecture, Game State Machine, and Zero-Dependency Engine for CyberPulse
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players and AI agents need a compelling, deterministic retro-cyberpunk terminal hacking simulation game that runs instantly on any terminal without external dependencies, supports saved state, and provides sub-second automated test verification.
- **Decision**: Build CyberPulse using pure Python 3 standard library. Structure it into modular domain models (`Node`, `Deck`, `Exploit`, `NetworkGrid`), an engine with deterministic state transitions and seed support, an atomic save/load manager, interactive hacking puzzles (frequency alignment, code sequence matching, hash cracking), and an ANSI-powered interactive CLI.
- **Consequences**: Zero external package installation overhead on Python 3.10+. Game mechanics are fully reproducible with fixed random seeds for automated test suites.

### ADR-002: Behavioral Psychology & Addiction Loop Mechanics: Variable Rewards, Near-Miss Feedback, Loss Aversion, and Meta-Progression
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Literature on human gaming behavior and engagement (Ryan, Rigby & Przybylski's Self-Determination Theory PENS model; Skinner's variable-ratio reinforcement schedules; Clark et al.'s near-miss striatal activation; Kahneman & Tversky's loss aversion and prospect theory; and Csikszentmihalyi's flow channel) proves that games become intensely engaging when they combine autonomy, competence scaffolding, unpredictable reward magnitude, near-miss tension, and push-your-luck risk/reward decisions. CyberPulse v0.1.0 had deterministic rewards and binary outcomes without persistent progression or risk-hedging.
- **Decision**: Introduce five evidence-based behavioral mechanics into CyberPulse:
  1. *Compulsion Loop & Black Market Shop*: A core loop of Action (node hack) -> Variable Reward -> Deck Customization (spending CryptoCreds on permanent hardware upgrades: CPU overclock, RAM modules, ICE dampeners).
  2. *Variable-Ratio Reward Schedules (Skinner/Schultz)*: Node breaches yield variable payouts: Standard (70%), Critical Data Jackpot (20% with 2.5x payout), or Hardware Chip Drop (10%).
  3. *Loss Aversion & Push-Your-Luck (Prospect Theory)*: Players can `jackout` from any breached node to safely bank stolen creds into their persistent career ledger. Reaching 100% trace burns unbanked loot from the current run.
  4. *Near-Miss Feedback Engine (Clark et al.)*: In puzzles and trace thresholds, generate high-arousal near-miss signals (e.g. "NEAR MISS! Resonance aligned within 0.1 GHz" or "CRITICAL TRACE WARNING: 85%").
  5. *Persistent Career Meta-Progression & Syndicate Contracts (Zeigarnik Effect)*: Career stats, rank, and bounty contracts tracked in `.cyberpulse/career.json`.
- **Consequences**: Deepens tactical decision-making and intrinsic motivation (competence and autonomy), while creating thrilling dopamine anticipation loops without manipulative paywalls or external dependencies.

### ADR-003: Operational Gap Remediation: Crash-Safe Shadow Recovery, Career Synchronization, Dynamic CPU/RAM Constraints, and Usable Exploit Chips
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: A comprehensive codebase audit revealed several architectural gaps and usability weaknesses:
  1. `cyberpulse/shop.py` used `Optional` in type annotations without importing it from `typing`, triggering `NameError` on Python 3.14 PEP 649 annotation evaluation.
  2. `cyberpulse/storage.py` created `.bak` backups during atomic writes, but failed to fall back to `.bak` when reading a corrupted `savegame.json` or `career.json`, risking total loss of player meta-progression.
  3. `cyberpulse/cli.py` initialized `GameEngine` with default deck stats (100 creds, 0 upgrades), failing to apply persistent upgrades and banked credits from `career.json` to the player's active deck.
  4. CPU cycles never regenerated across moves or turns, permanently disabling the `spoof` command after 3 uses.
  5. Cyberdeck RAM capacity (`ram_mb`) and shop RAM upgrades were never checked or consumed by any game action or puzzle.
  6. Exploit chips (`logic_bomb`, `ghost_protocol`, `brute_miner`) dropped as loot or purchased in the shop were inert with no activation mechanism.
  7. Only a single static syndicate contract was issued with no replenishment.
- **Decision**: Remediate all gaps systematically:
  1. Fix typing import in `shop.py` and verify annotation evaluation across all modules.
  2. Implement automatic `.bak` recovery with corruption quarantine in `storage.py`.
  3. Introduce `apply_career_profile(deck, profile)` and synchronize deck/career credits across runs.
  4. Implement turn-based CPU cycle regeneration (+1 per move/turn up to `max_cpu`).
  5. Enforce RAM buffer capacity requirements for high-tier node intrusions (`node.security_level * 16` MB).
  6. Implement an active `exploit <name> [target]` system allowing players to deploy chips tactically.
  7. Dynamically dispatch new syndicate bounty contracts upon contract fulfillment.
- **Consequences**: Closes all meta-progression and resource disconnects, elevates player agency and tactical depth, guarantees zero-data-loss power-loss resilience, and maintains 100% test pass rate in sub-second execution with zero external dependencies.

### ADR-004: Zero-Dependency Web Cyberdeck Interface with Interactive Matrix Canvas and Web Audio Synthesizer
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players seeking maximum immersion benefit from rich visual and auditory feedback (retro CRT phosphor scanlines, real-time node matrix topology visualization, interactive waveform oscilloscopes, and responsive audio feedback). External web frameworks or heavy dependencies (Flask, FastAPI, npm packages) violate AIKit's zero-friction onboarding and standard-library-only constraints (PRINCIPLE-011).
- **Decision**: Build a zero-dependency Web Cyberdeck Interface:
  1. *Backend*: Lightweight Python standard library HTTP server (`http.server.ThreadingHTTPServer`) exposing JSON REST APIs (`/api/state`, `/api/action`, `/api/shop`, `/api/career`, `/api/puzzle`).
  2. *Frontend*: Pure Vanilla HTML5, CSS3, and JavaScript served directly from `cyberpulse/static/`.
  3. *Visual Design*: Retro CRT aesthetic (phosphor green, cyber-cyan, amber alert themes), glassmorphic telemetry panels, scanlines, and animated HUD meters.
  4. *Cyberspace Node Matrix Canvas*: Real-time interactive 2D canvas visualizing network topology, node statuses (`LOCKED`, `DISCOVERED`, `BREACHED`), and pulsing connection vectors.
  5. *Web Audio API Synthesizer*: Native in-browser algorithmic sound engine (zero audio asset downloads), synthesizing retro terminal beeps, modem handshake hums, near-miss heartbeats, and victory fanfare.
- **Consequences**: Delivers a rich, cinematic audiovisual experience accessible in any modern browser via `python -m cyberpulse.cli --web` without installing any third-party packages or node modules.



