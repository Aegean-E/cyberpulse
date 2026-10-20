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

### ADR-005: Authentic Hacker Simulation Pivot: Realistic IP Networking, Port Exploitation, Virtual Filesystems, and Data Theft Contracts
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Player feedback revealed that abstract math/puzzle mini-games (frequency tuning, hex matching, hash ciphers) created high cognitive friction and felt alienating rather than immersive ("Gaming is too complex and hard to get inside"). Players desire an authentic, immersive hacker simulation grounded in realistic networking concepts (IP addresses, open service ports, vulnerability exploitation, file browsing, data theft, and log scrubbing) inspired by genre classics like *Uplink* and *Hacknet*.
- **Decision**: Pivot CyberPulse into an authentic hacker simulation:
  1. *IP-Based Network Architecture*: Hosts have realistic IPv4 addresses (`192.168.1.1`, `10.0.4.15`, `172.16.80.1`), hostnames, subnet topology, and network gateways.
  2. *Port & Service Vulnerability Model*: Hosts expose standard network ports (SSH:22, HTTP:80, FTP:21, SQL:3306, SMTP:25). Players use `probe <ip>` to scan ports and deploy targeted exploits (`exploit <ip> <port>`) to obtain root shell access.
  3. *Virtual Filesystem & Data Theft*: Breached hosts provide realistic directory structures (`/bin`, `/etc`, `/var/log`, `/home/corporate/`). Players explore with `ls`, inspect with `cat <file>`, exfiltrate high-value files with `download <file>` / `steal <file>`, and cover tracks with `wipe_logs`.
  4. *Espionage & Data Theft Mission Contracts*: Syndicate contracts provide narrative corporate espionage objectives (e.g. steal employee payroll, exfiltrate AI weights, or erase audit logs) with cash payouts upon safe extraction.
- **Consequences**: Replaces arbitrary abstract mini-games with intuitive, natural, and compelling hacker simulation mechanics that players instantly understand and enjoy, while maintaining pure Python standard library zero-dependency guarantees.

### ADR-006: Virtual Netrunner Rig, Malware Workshop Crafting, Phishing Infiltration, and Background Daemon Exploits
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players requested expanding the simulation with their own personal cyberdeck computer identity ("Our Computer Files", "Our IP"), social engineering vectors (phishing attacks to harvest credentials), custom virus/payload synthesis in a netrunner workshop, and background persistence tools (keylogger daemons).
- **Decision**: Introduce synthetic in-game mechanics within CyberPulse:
  1. *Virtual Localhost Rig*: CyberDeck maintains its own virtual host identity (`127.0.0.1` / `10.99.0.2`, hostname `rig.netrunner.local`) and persistent local filesystem (`/home/deck/`, `/loot/`, `/tools/`). Stolen exfiltrated files are archived into the player's local loot drive.
  2. *In-Game Social Engineering (Phishing Dispatch)*: Players can dispatch simulated spear-phishing campaigns (`phish <ip>`) targeting employee credentials, which bypasses port firewalls on success to leak credentials or reduce security tiers.
  3. *In-Game Malware Crafting Workshop*: A modular virus synthesis bay (`craft` / `workshop`) allows assembling custom in-game payload scripts by combining injection vectors (e.g. stealth, brute, worm replication) and payloads (credit siphon, trace dampening, credential scrapers).
  4. *In-Game Background Keylogger Daemons*: Deploy in-game background listener scripts (`deploy_keylogger <ip>`) onto compromised remote hosts to passively harvest unbanked credits turn-by-turn until scrubbed or detected.
  5. *Strict Synthetic Sandbox Isolation*: All files, IPs, and payloads are strictly simulated in-memory Python dataclasses; no real-world host files, network sockets, or external systems are ever accessed.
- **Consequences**: Deepens tactical variety, strategic pre-planning, and immersion while maintaining pure Python 3 standard library zero-dependency constraints and sub-second test execution.

### ADR-007: Tactical Exploits, Host Antivirus Detection, Network Firewalls, and Multi-Vector Social Engineering
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Players requested deeper tactical cyber-warfare layers: "Add Exploits, Add Antivirus Mechanics, Add Firewalls, Add Social Engineering Component to the GAME". Straightforward open-port zero-days and single-tier phishing need to evolve into an interlocking tactical system featuring stateful network firewalls, active host antivirus heuristics and daemon quarantine sweeps, a diverse catalog of specialized exploit CVE payloads, and interactive multi-vector social engineering campaigns (pretexting IT support, baiting USB drops, executive impersonation).
- **Decision**: Introduce four interlocking tactical simulation systems:
  1. *Network Firewalls (`FirewallRule`, `HostFirewall`)*:
     - Hosts can run active packet-filtering firewalls with rules (`DEFAULT_DROP`, `PORT_FILTER`, `STATEFUL_IDS`).
     - Ports can be `FILTERED` by firewalls, preventing direct exploitation unless bypassed or knocked.
     - Mechanics: `firewall <ip>` to inspect rules, `bypass <ip> [method]` via port knocking, packet fragmentation, or proxy tunneling.
  2. *Host Antivirus Systems (`HostAntivirus`, `AVStatus`)*:
     - Target hosts (especially Tier 2+ enterprise nodes) run active Antivirus suites (e.g. *SentinelCore*, *AegisShield*, *CyberDefender*).
     - AV maintains an `alert_level` (0 to 100%) and runs periodic memory heuristic scans.
     - If alert level exceeds threshold, AV quarantines/kills active background daemons (`keyloggers`, `worms`) and triggers an immediate spike in ICE trace.
     - Mechanics: `av <ip>` to inspect AV status, `evade <ip>` / `kill_av <ip>` to inject rootkit evasion hooks or suppress AV processes.
  3. *Expanded Exploit Payload Matrix (`ExploitPayload`, `CVE`)*:
     - Players discover and weaponize specific vulnerability CVEs (`CVE-2024-SHELLSHOCK`, `CVE-2023-MEMCORRUPT`, `CVE-2025-SQLINJECT`, `CVE-2024-BUFFERLEAK`).
     - Each exploit payload has specific RAM requirements, target service affinities, stealth ratings (affecting AV detection), and payload yields.
     - Commands: `cve` / `exploits` to view catalog, `exploit <ip> <port> [cve_id]` to select matched exploit payloads.
  4. *Multi-Vector Social Engineering Component (`SocialVector`, `EmployeeProfile`)*:
     - Expands beyond basic phishing into multi-vector social engineering:
       - `pretext`: Masquerading as internal IT support requesting emergency access.
       - `bait`: Dropping infected simulated USB drives / payload PDFs.
       - `spear_phish`: Executive CEO fraud urgent wire / credential lure.
       - `vishing`: Voice-phishing helpdesk operator for MFA token bypass.
     - Hosts feature dynamic employee security awareness profiles (Naive, Standard, Paranoid).
     - Commands: `social <ip> [vector]` (e.g. `social 192.168.1.10 pretext`).
  5. *Zero External Dependencies & Synthetic Invariant*:
     - 100% in-memory standard library dataclasses, deterministic RNG generation, zero external pip dependencies, sub-second test execution.
- **Consequences**: Deepens the hacker simulation with strategic counters (Firewalls block ports -> require Bypass or Social Eng; Antivirus hunts Keyloggers -> requires Evade or Rootkit; CVEs give tactical choices).

### ADR-008: System-Wide Engine Hardening, Full CVE Network Matrix, CLI Completion Lifecycle, and Probed Port HUD
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: A holistic audit across `cyberpulse` identified several gaps, edge-case risks, and user-experience opportunities:
  1. Several engine methods (`spoof_ip`, `scan_surroundings`, `use_exploit`, `list_files`, `read_file`, `craft_virus`) lacked `is_game_over` / `is_jacked_out` guards, allowing operations to execute after terminal disconnect or trace lockout.
  2. Engine string parameters (e.g. `exploit_name`, `recipe_name`, `query`, `method`, `filepath`) lacked defensive `None`/type coercion, risking `AttributeError` on malformed API payloads or empty CLI inputs.
  3. Turn progression was inconsistent: `exploit_service` did not advance `turns_elapsed` or tick daemons, and `SaveManager.load()` did not re-seed the engine RNG with turn offset.
  4. The CVE exploit catalog had gaps: `CyberDeck.known_cves` referenced `CVE-2025-9901` which was missing from `KNOWN_CVES`, and no CVEs existed for `https` or the AI Supercore.
  5. The CLI batch execution mode (`--exec`) bypassed career completion hooks upon victory/game-over.
  6. The Web Cyberdeck only rendered open ports when a host was already breached; probing an unbreached host only logged text into the terminal, missing an opportunity for interactive visual port exploration and direct exploit/bypass buttons.
- **Decision**:
  1. Add universal session state checks (`is_game_over`, `is_jacked_out`) and defensive string sanitization across all engine methods.
  2. Implement turn progression and daemon ticks in `exploit_service`, and ensure RNG persistence determinism on save load.
  3. Expand `KNOWN_CVES` to include `CVE-2025-9901` (Project Omega Neural Core Deserialization RCE, target_service: `"any"`) and `CVE-2022-0778` (OpenSSL BN_mod_sqrt loop on `"https"`), aligning with `CyberDeck.known_cves`.
  4. Unify CLI run completion logic (`handle_run_completion`) across interactive and batch modes.
  5. Add visual Probed Ports Subsystem, keyboard shortcuts, and interactive exploit selectors in Web Cyberdeck UI.
- **Consequences**: Hardens system integrity, eliminates runtime exceptions, provides complete CVE network coverage, and delivers an enriched, seamless hacker simulation experience.


### ADR-009: Post-Review Defect Remediation: Command Dispatch, Static Containment, Save Honesty, Career Accounting, and Offline Assets
- **Date**: 2026-10-18
- **Status**: Accepted
- **Context**: An independent review of the shipped game confirmed several user-facing defects: the `buy` branch never returned, so every purchase printed "Unknown command: 'buy'"; `serve_static` joined raw request paths onto the static root, allowing `../` path traversal (arbitrary local file read); numeric ports from CLI and REST input were parsed with a bare `int()` (ValueError tracebacks in the REPL and dropped connections from the API); a piped batch run tracebacked when a minigame read EOF; `_write_atomic` returned the target path after five failed replaces, so the CLI printed "progress saved" although nothing landed; every jackout added the entire wallet to `lifetime_creds`, double-counting the previously banked credits (fresh career starts at 100/100); the Web Cyberdeck workshop posted a nonexistent `recipe.recipe_id`, so every browser craft failed with "Unknown recipe ''"; the UI advertised wrong bypass CPU/trace costs; and two static assets loaded Google Fonts.
- **Decision**: Return `True` after a handled `buy`; resolve static requests and reject paths outside the static root via `is_relative_to`; parse ports inside try/except (the REST API answers 400 `{"ok": false, "error": ...}`, the CLI prints a usage line); catch `EOFError` in the batch loop and stop the batch gracefully; make `_write_atomic` return `Optional[Path]`, create temp files with `tempfile.mkstemp` (cleaned in a `finally`), and have the CLI report an unpersisted save instead of claiming success; compute `gained = max(0, deck + unbanked - banked_before)` on jackout and victory paths (CLI and REST) and add only that to `lifetime_creds`; send `recipe.name` from the workshop client and render `[vector]` in the card; align the Web UI bypass cost labels with the engine's cost table; drop the Google Fonts links and extend the CSS font variables with local fallbacks.
- **Consequences**: Purchases and browser crafting work, the web server cannot read files outside its static root, malformed input yields messages instead of tracebacks, saves never claim false success, `lifetime_creds` grows by the run's net gain over the starting bank instead of re-counting banked credits, and the UI renders fully offline. Test suite: 94 tests, 100% green in about a second.

### ADR-010: Run-State Coherence: Idempotent Breaches, Persistent Puzzles, One-Shot Settlement, and Session Hardening
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: A second coherence audit found several state-lifecycle defects that survived the earlier reviews: `complete_breach` and `worm_replicator` could re-award a node already breached; `spoof_ip` always reported a 25% reduction even near zero; daemons kept harvesting after a trace lockout; `bypass_firewall`, `evade_antivirus`, and social engineering accepted targets outside the direct subnet; reopening a CLI/Web puzzle regenerated its attempts; the CLI victory path counted unbanked loot in `lifetime_creds` but never added it to the bank; the Web session settled only on jackout, not on victory or lockout; workshop affordability ignored banked credits; `wipe_logs` could be repeated for free trace loss; the initial extraction contract completed on a bare breach; the API sent wildcard CORS; a non-integer reset seed crashed the server; request bodies and JSON types were unvalidated; and shared session state was mutated concurrently by `ThreadingHTTPServer`.
- **Decision**:
  1. Make `complete_breach` reject terminal runs and already-breached nodes, clear any pending puzzle, and award rewards exactly once; require extraction contracts (target file/IP/log wipe) to complete through `download_file` plus `wipe_logs`, while simple sector contracts still complete on breach.
  2. Persist one puzzle instance per node in `GameEngine.pending_puzzles`; CLI and REST resume remaining attempts and clear the entry on solve or exhaustion.
  3. Add `GameEngine.settle_career` as the single one-shot run lifecycle used by CLI and Web: victory and jackout bank unbanked loot, lockout records a failure, and `lifetime_creds` grows only by net gain. Crafting and purchases persist banked spending immediately.
  4. Guard daemon ticks, spoof reporting, wipe idempotence, and subnet reachability; advance daemon ticks for probes and log wipes.
  5. Remove wildcard CORS, serialize state mutation with a session lock, validate body size/type and seeds (including float seeds), cap request bodies, read request bodies and serve static assets outside the lock, and keep the API same-origin.
  6. Fix Web workshop affordability to use banked plus unbanked credits and make port-card bypass buttons target the selected port.
  7. Do not delete a savegame from the Web session; it never loads one, so terminal Web runs must not destroy a CLI-owned save. Enforce the same terminal-state guards on every CLI-reachable mutating action and stop batch execution at victory/lockout.
- **Consequences**: Rewards and career totals are truthful and idempotent; puzzle retries cost their remaining attempts; runs settle once across both interfaces; Web state is race-free and not readable by cross-site scripts; slow clients and static assets cannot hold the state lock; malformed input cannot crash the server or delete unrelated saves. Test suite: 119 tests, 100% green in about a second.

### ADR-011: Story Campaign, Operative Relationships, Quest Board, and Combo/Overdrive Loop
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: CyberPulse had a strong tactical loop but no main menu, no narrative framing, no persistent goals beyond random contracts, no characters to interact with, and no moment-to-moment reward escalation. The Web and CLI also started abruptly, which made the game harder to onboard and gave the world no context.
- **Decision**:
  1. Add a CLI main menu (new run, continue, story briefing, operatives, career, help) and a Web main-menu overlay with the same entry points.
  2. Add a five-act story campaign in `story.py`: Gateway, Money, Black ICE, Nexus Protocol, Zero Day. Story acts advance when main quests complete; story log seed lines and act titles are persisted.
  3. Add persistent `Quest` and `ContactProfile` models on `GameState`. Seven quests cover main story and side objectives (breach types, file theft, log wipes, crafting, daemon deployment). Main quests auto-accept on act unlock; side quests are accepted through contacts or the mission board.
  4. Add four operatives (Mira, Kilo, The Archivist, Agent Zero) with act-gated dialogue, trust, jobs, and one-time favors that reduce trace, restore CPU, reveal a locked node, or grant a chip.
  5. Add combo-streak rewards (up to +50% breach bonus) and `overdrive` (2 CPU + 8% trace for +1 combo and +10 unbanked credits), with combo reset on lockout.
  6. Expose story, quests, contacts, overdrive, contacts/interaction, and quest acceptance through the REST API and the Web CRT UI; keep CLI and Web behavior aligned.
  7. Backfill story state in `SaveManager.load` for saves created before this feature, and persist all new fields atomically with the existing savegame.
- **Consequences**: Players get a clear entry point, a narrative campaign, relationship-driven side content, and a risk/reward combo loop. Existing commands and saves remain compatible; the CLI/Web schemas grow additively. Test suite: 138 tests, 100% green.

### ADR-012: Endgame Legacy Summary, Story Epilogues, and Career Best Combo
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: The story, quest, contact, and combo systems ended abruptly. Terminal runs showed a generic banner, combo skill was not recorded in the career dossier, and operative relationships never paid off after the run ended.
- **Decision**:
  1. Add `run_summary()` to the engine, deriving outcome, best combo, quest completion, unlocked operatives, and an epilogue from existing run state.
  2. Add outcome, contact, and combo epilogue data in `story.py`; epilogues reflect victory/jackout/lockout, trust or favors spent, and combo milestones.
  3. Add `best_combo` to `CareerProfile` with a default, update it on every settlement (including failures), and show it in the CLI dossier and Web career modal.
  4. Include `run_summary` in `/api/state`; print the legacy block in CLI completion/jackout and show epilogue plus run stats in the Web victory/lockout banner.
  5. Keep old saves compatible: missing `best_combo` defaults to 0 and story state is backfilled on load.
- **Consequences**: Runs now end with narrative and statistical closure, combo mastery persists across the career, and operative relationships visibly affect the epilogue. Test suite: 143 tests, 100% green.

### ADR-013: Act III Alliance Choice and Branching Operative Consequences
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: Operative interactions changed trust and rewards but never branched the story or ending. Agent Zero was introduced as a rival with no meaningful decision attached, so character relationships were still mostly cosmetic.
- **Decision**:
  1. Add persistent `GameState.story_choice` with an empty default for backward compatibility.
  2. Offer a one-time Act III choice when Agent Zero is unlocked: ally (`zero_ally`) or defy (`zero_defy`).
  3. Ally grants Zero trust and a ghost_protocol chip (or 150 unbanked credits if already owned); defy grants Mira trust and 150 unbanked credits.
  4. Add choice-specific dialogue for Acts III/IV/V, a locked-choice label in the story payload, and choice-specific epilogue lines.
  5. Expose the choice through the same `contact` mode on CLI and REST; the Web contacts modal shows ALLY/DEFY controls only when the pact is available.
- **Consequences**: The story now has a consequential character branch that changes relationships, rewards, late dialogue, and the ending. The choice is persisted and old saves remain valid. Test suite: 148 tests, 100% green.

### ADR-014: Order-Robust Story Progression, Settled-Run Guards, and the Act IV Core Seal
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: A hardening audit of the story campaign found three coherence defects. One-shot story objectives only counted while their quest was accepted: breaching Black ICE before Act III made `q_blackice` impossible (the node cannot be breached twice) and permanently stalled the campaign, while early target thefts and log wipes were likewise uncounted. `accept_quest` lacked terminal-state guards, so the REST API could accept quests and grant trust after a lockout or jackout. The Nexus supercore could also be breached before Act IV, producing a victory whose run summary reported an incomplete main story.
- **Decision**:
  1. Extract quest completion into `_complete_quest` and reconcile one-shot progress from world state (`_quest_progress_from_state`) whenever a quest is accepted, including auto-accepted main quests; retroactive progress can complete a quest and advance the act chain immediately.
  2. Guard `accept_quest` against lockout, jackout, and victory like every other mutating action.
  3. Seal the central core until Act IV in `can_hack_node`, `complete_breach`, and `exploit_service`, so the node refuses even a direct engine call and no CPU or trace is paid.
  4. Correct the README claim about save continuation in the Web main menu and add `ally | defy` to the CLI contact usage line.
- **Consequences**: Any exploration order can complete the campaign; one-shot objectives credit events that already happened; settled runs cannot mutate; the final breach is consistent with the narrative. No save schema changed and old saves remain valid. Test suite: 154 tests, 100% green.

### ADR-015: Living-Grid Simulation: Clock, Corporate Alert, Generated News, Ambient Events, Host Re-Securing, and Market Drift
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: The grid outside the player's current node was static. Turns advanced only to tick daemons, hosts never reacted to loud intrusions, black-market prices never moved, and nothing inside or outside the game reported on the player's actions. Requested behavior: more simulation-like mechanics, so the world reads as running on its own rather than waiting for input.
- **Decision**:
  1. Add `WorldState` (minute, day, alert level, market index, events cooldown, re-secured count, news feed) and `NewsItem` to `state` with defaults; backfill missing world state for old saves in `GameState.from_dict`.
  2. Add `world.py` as a pure simulation module: clock and shift math, alert clamping, bounded market random-walk, deterministic per-tick ambient events, and grid re-secure planning. World rolls use their own per-tick RNG stream seeded from `(seed, tick, stream)` so the engine's reward RNG sequence, and every existing seeded outcome, is untouched.
  3. Route all nine turn advance sites through `GameEngine.advance_turn()`, which ticks daemons and then the world. Every turn advances a 15-minute clock, drifts the market, decays or sustains alert based on trace, may fire an ambient event, applies NetWatch patrol trace at alert 50/75+, and may re-secure a host.
  4. Make alert actionable: breaches raise it by node security, daemons raise it, extraction cools it, and ambient events can move it. Negative ambient events only enter the pool at alert 35+, so quiet early runs stay fair.
  5. Re-secure rules: alert 50+, 12-turn cooldown since breach, at most one host per turn, never the player's current host or the central core. Re-securing restores ports, firewall, and antivirus, restores wiped logs, recalls embedded daemons, publishes a NetWatch headline, and bumps `resecured_count`.
  6. Add a per-host breach ledger (`breached_turn`, `reward_claimed`): a re-secured host pays no second reward, no combo, and no quest credit when re-breached, closing the farm loop introduced by host healing.
  7. Apply the market index to shop prices through an optional `price_multiplier` (default 1.0), surfaced in CLI shop output, `buy`, `shop_buy`, and `/api/shop`; keep `base_cost` visible.
  8. Surface the grid in both clients: CLI `world`/`news` commands plus a HUD grid line, `GET /api/world`, a `world` block in `/api/state`, and a Web Cyberdeck ticker bar showing clock, shift, alert, market index, and the newest headline.
- **Consequences**: The grid now reacts to player behavior and reports on it, giving loud play visible and mechanical consequences. Save schema changes are additive and old saves load with a fresh day-1 world. Seeded reward determinism is preserved by the separate world RNG stream. Test suite: 189 tests, 100% green.

### ADR-016: NetWatch Counter-Infiltration & Active Hunters: Autonomous Grid Pursuit, Connection Interception, Scent Confusion, and Tactical Countermeasures
- **Date**: 2026-10-19
- **Status**: Accepted
- **Context**: While the living-grid simulation (ADR-015) introduced corporate alert, news headlines, and sysadmin host re-securing, high corporate alert (60%+) lacked a direct predatory spatial threat navigating the network topology. Players could remain on breached nodes without fear of being tracked down or cornered across subnets, blunting late-game infiltration tension.
- **Decision**:
  1. Add `NetWatchHunter` model (`hunter_id`, `name`, `current_node_id`, `status`, `turns_active`, `target_node_id`, `confused_turns`) and `WorldState.hunters: List[NetWatchHunter]` with default factories and backward-compatible `to_dict`/`from_dict` serialization.
  2. Implement BFS shortest-path graph traversal and hop-distance calculation in `world.py` (`find_shortest_path`, `calculate_distance`).
  3. Deploy active NetWatch hunters (`deploy_hunter`) when `world.alert_level >= 60` from the Nexus Central Core or highest-tier host, broadcasting alert news headlines.
  4. Step hunters turn-by-turn during `tick_world()`: hunters track the player's active subnet along the shortest path. On connection interception (hunter reaches player's current host), trigger an ICE clash (+15% trace spike, -2 CPU cycles drain, news headline). When entering a breached non-player host, hunters quarantine active background daemons.
  5. Scent confusion & countermeasures: `spoof_ip` and `wipe_logs` scramble hunter radar for 2 turns; `counter_hunter` allows netrunners to deploy tactical countermeasures: `logic_bomb` payload neutralizes the hunter, `ghost_protocol` masks signature, sheds 30% trace, and banishes the hunter back to core with 4 confused turns, or 3 CPU cycles can be burned for active jamming.
  6. Surface hunters across both interfaces: CLI `hunter`/`radar` command and HUD proximity warnings (`[⚠️ HUNTER CLOSE: Aegis-1 (1 hop)!]`); Web Cyberdeck ticker chip (`grid-hunter`) and animated pulsing red threat beacon on the 2D network canvas; REST API endpoints and state telemetry (`/api/world`, `/api/state`, `/api/action`).
- **Consequences**: Escalates high-alert gameplay into a thrilling cat-and-mouse spatial chase across subnets, elevating player agency, evasive lateral movement, and countermeasure timing. Additive dataclass defaults preserve full backward compatibility with legacy saves. Test suite: 204 tests, 100% green.

### ADR-017: Shift Dynamics & Downtime: Tactical Shift Profiles, Shift-Aware Grid Modifiers, and the Lay-Low Downtime Action
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The living-grid clock (ADR-015) advanced time and named shifts, but shift names were cosmetic: patrol pressure, re-secure chance, hunter deployment, and market drift behaved identically at 03:00 and 15:00, so the clock carried no tactical weight. Players also had no deliberate way to recover CPU and let a dangerous shift pass without spending trace elsewhere.
- **Decision**:
  1. Add a frozen `ShiftProfile` dataclass and a `SHIFT_PROFILES` registry (`late_night`, `morning`, `afternoon`, `evening`) to `world.py`, with `SHIFT_BOUNDS`, `shift_profile(minute)`, and `shift_effect_text(profile)` rendering its mechanical modifiers; the profile carries `market_bias`, `alert_decay_bonus`, `resecure_chance_delta`, and `hunter_threshold_delta`.
  2. Make each shift tactically legible: quiet nights cool alert faster (`+1/turn`) but re-secure less and push hunters to 70%+, morning audits re-secure aggressively (`+10%`) and discount the market (`-3%`), afternoons are hair-trigger (`-5` hunter threshold, `+5%` re-secure), and evening handovers lag re-secures (`-5%`) while patrols stay wired (`+5` hunter threshold, `+1/turn` alert cool).
  3. Apply the modifiers inside `tick_world`: `drift_market` takes a `bias`, `_decay_alert` takes a `shift_bonus`, `plan_resecures` takes a `chance_delta`, and `deploy_hunter` derives its threshold from `shift_profile(world.minute).hunter_threshold_delta`. All new parameters default to their prior behavior.
  4. Expose `shift_key`, `shift_tagline`, `shift_effect`, and a `shift_modifiers` block from `world_summary`; the shift is derived from `world.minute`, so existing saves need no migration and Morning defaults preserve today's tests.
  5. Add `GameEngine.lay_low(turns=1)` (cap `MAX_LAY_LOW_TURNS = 3`): it rejects terminal runs and non-integer or out-of-range input, then per turn regenerates 1 CPU and calls `advance_turn`, stopping early if the run reaches a terminal state, and reports a before/after summary of CPU, trace, alert, and clock.
  6. Surface downtime and doctrine across both clients: CLI `lay_low`/`wait`/`laylow`/`rest` command with 1-3 turn parsing plus a shift doctrine line in the world panel and HUD; REST has no wildcard grant and routes `lay_low`/`wait` through `POST /api/action`; the Web Cyberdeck gains a `LAY LOW` button with an `[L]` hotkey and a `#grid-shift-effect` chip populated from `world_summary.shift_effect`.
- **Consequences**: The clock becomes a resource: each shift has a distinct tactical identity and `lay_low` lets players trade grid momentum for CPU while accepting patrol, hunter, and ambient risk. The contract grows additively (`world_summary` keys and optional keyword parameters) with no persisted schema change and no disturbance to seeded reward determinism. Test suite: 218 tests, 100% green.
