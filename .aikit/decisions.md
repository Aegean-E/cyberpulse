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

