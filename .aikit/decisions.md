# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: Architecture, Game State Machine, and Zero-Dependency Engine for CyberPulse
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players and AI agents need a compelling, deterministic retro-cyberpunk terminal hacking simulation game that runs instantly on any terminal without external dependencies, supports saved state, and provides sub-second automated test verification.
- **Decision**: Build CyberPulse using pure Python 3 standard library. Structure it into modular domain models (`Node`, `Deck`, `Exploit`, `NetworkGrid`), an engine with deterministic state transitions and seed support, an atomic save/load manager, interactive hacking puzzles (frequency alignment, code sequence matching, hash cracking), and an ANSI-powered interactive CLI.
- **Consequences**: Zero external package installation overhead on Python 3.10+. Game mechanics are fully reproducible with fixed random seeds for automated test suites.
