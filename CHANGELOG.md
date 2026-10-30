# Changelog

All notable changes to CyberPulse are recorded here. The format follows Keep a Changelog, and versions use semantic versioning.

## [0.4.0] - 2026-10-30

### Added

- Three manual save slots plus autosave, legacy slot-1 compatibility, slot names, rename/delete, and a slot archive in both interfaces.
- Bounded career run history, sixteen milestones, a transparent run score, and a difficulty-filtered top-ten Hall of Fame.
- Deterministic daily runs with date-seeded modifiers, per-day bests, and consecutive-day streaks.
- Seed replay from the run archive.
- Three difficulty modes with trace, starting-condition and contract-pay modifiers.
- A contract-stealing rival netrunner with counter-tracing, HUD chip and Web modal.
- A one-use Dead Man's Switch lockout insurance consumable.
- A first-run field manual with live scan/probe/breach/loot/extract checkpoints.
- Career aliases, persisted Web theme/audio/CRT preferences and reduced-motion styles.
- Syndicate and Street standing, named ranks, promotion rewards, contract-pay bonuses and Black Market discounts.
- Guarded career reset with automatic backup and save cleanup.

### Changed

- Centralized the version in `cyberpulse.__version__`, derived the CLI banner from it, and added `--version`.
- Aligned `pyproject.toml`, the CLI banner and package metadata at 0.4.0.
- Added difficulty and faction context to run history, hall entries, save payloads and state responses.

### Fixed

- Corrupt primary saves can no longer overwrite a good `.bak`; non-finite metadata falls back safely.
- Faction snapshots survive save/load and are not retroactively changed by later career standing.
- Autosave cannot overwrite another run's checkpoint after a load.
- Same-day daily repeats cannot inflate streaks.

## [0.3.0] - 2026-10-26

- Public baseline with procedural networks and puzzles, five-act story, operatives, Syndicate contracts, living-grid simulation, Web Cyberdeck and terminal client.
