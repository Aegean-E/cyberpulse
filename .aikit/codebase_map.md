# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `22`
- **Total Classes**: `41`
- **Total Top-Level Functions**: `29`
- **Total Class Methods**: `287`
- **Total Source Lines**: `6801`

---

## 📦 Modules & Exported Symbols

### [`cyberpulse/__init__.py`](cyberpulse/__init__.py)
> *CyberPulse: Retro-cyberpunk terminal hacking simulation game.*

**Size**: `3` lines (`91` bytes)

---

### [`cyberpulse/cli.py`](cyberpulse/cli.py)
> *Interactive and scriptable retro-cyberpunk terminal CLI for CyberPulse with behavioral mechanics.*

**Size**: `761` lines (`33864` bytes)

**Functions:**
- `def setup_terminal_encoding()` - *Ensure stdout and stderr handle utf-8 safely across all Windows code pages.*
- `def safe_print(msg)` - *Print message to stdout with graceful fallback for legacy terminal code pages.*
- `def get_default_data_dir()`
- `def render_trace_bar(trace_percent, width)`
- `def print_hud(engine)`
- `def print_shop(shop, deck)`
- `def print_career(profile)`
- `def print_workshop(engine)`
- `def print_daemons(engine)`
- `def print_cves(engine)`
- `def print_story(engine)`
- `def print_run_summary(engine)`
- `def print_quests(engine)`
- `def print_contacts(engine)`
- `def show_main_menu(engine, save_mgr)` - *Render the interactive main menu and return 'start', 'load', or 'quit'.*
- `def execute_hack_puzzle(engine, target_id, auto_solve)`
- `def run_command(cmd_line, engine, save_mgr, auto_solve)` - *Execute a single command string. Returns False to quit.*
- `def handle_run_completion(engine, save_mgr)` - *Persist career stats and clean up savegame when run concludes (victory or game-over).*
- `def main(argv)`

---

### [`cyberpulse/engine.py`](cyberpulse/engine.py)
> *Deterministic cyberspace game engine with risk-reward loss aversion and near-miss feedback.*

**Size**: `1807` lines (`83465` bytes)

**Classes:**
- `class GameEngine` - *Manages gameplay rules, push-your-luck risk, and victory/defeat conditions.*
  - Method `.__init__(seed, career_profile)`
  - Method `.get_current_node()`
  - Method `._find_quest(quest_id)`
  - Method `._find_contact(contact_id)`
  - Method `._log_story(message)`
  - Method `._sync_story_quests()` - *Auto-accept unlocked main-story quests so the campaign cannot stall.*
  - Method `._quest_progress_from_state(quest)` - *Progress the world already holds for a one-shot objective.*
  - Method `._reconcile_quest_progress(quest)` - *Credit one-shot events that happened before the quest was accepted.*
  - Method `._complete_quest(quest)` - *Mark a quest complete once, grant its reward, and advance the main story.*
  - Method `._advance_story(act, chapter, reason)`
  - Method `._progress_quests(objective, target, amount)`
  - Method `.is_quest_locked(quest)`
  - Method `._story_gate_reason(node)` - *A story lock the network topology alone does not enforce.*
  - Method `.accept_quest(quest_id)` - *Accept a contact's side quest or expose an unlocked story objective.*
  - Method `._apply_contact_favor(contact)`
  - Method `.interact_contact(contact_id, mode)` - *Talk to an operative, accept their job, or spend their one-time favor.*
  - Method `.ensure_story_state()` - *Backfill story content when loading a save created before story support.*
  - Method `.story_summary()`
  - Method `.run_summary()` - *Return the terminal (or in-progress) run's legacy for CLI and Web display.*
  - Method `.list_quests()`
  - Method `.list_contacts()`
  - Method `.get_or_create_puzzle(node_id)` - *Return the pending hacking puzzle for a node, creating it only once.*
  - Method `.clear_pending_puzzle(node_id)` - *Discard a solved or exhausted puzzle so the node cannot replay its attempts.*
  - Method `.add_trace(raw_amount)` - *Increase system trace, mitigated by ICE dampeners. 100% triggers lockout & loss of loot.*
  - Method `.regenerate_cpu(amount)` - *Cool down cyberdeck processing units and recover CPU cycles.*
  - Method `.spoof_ip()` - *Reduce active trace level by burning CPU cycles.*
  - Method `.overdrive()` - *Burn CPU and trace to stack a combo before the next breach.*
  - Method `.scan_surroundings()` - *Scan adjacent nodes to reveal their security level and status.*
  - Method `.can_move_to(target_id)` - *Verify whether the player can transition to target node.*
  - Method `.move_to(target_id)` - *Move player's intrusion session to an adjacent breached node.*
  - Method `.can_hack_node(target_id)` - *Verify whether player cyberdeck meets hardware requirements to attack node.*
  - Method `.dispatch_next_contract()` - *Dispatch a new Syndicate Bounty Contract after previous completion (Zeigarnik Effect).*
  - Method `._contract_completes_on_breach(contract, node)` - *Return True when a node breach satisfies a contract without extra objectives.*
  - Method `.complete_breach(node_id)` - *Mark node as breached, evaluate variable-ratio rewards, and check contracts.*
  - Method `.use_exploit(exploit_name, target_id)` - *Deploy an executable exploit chip loaded in cyberdeck firmware.*
  - Method `.jackout()` - *Push-Your-Luck extraction: safely bank all unbanked credits and looted payloads.*
  - Method `.settle_career(profile)` - *Apply a finished run's outcome to the persistent profile exactly once.*
  - Method `.find_node(query)` - *Lookup node by node_id, ip_address, or hostname.*
  - Method `.probe_host(target_query)` - *Perform network port scan (nmap-style) against a target IP, hostname, or node_id.*
  - Method `.exploit_service(target_query, port_num, cve_id)` - *Launch an exploit payload (generic zero-day or targeted CVE) against an open service port on target host.*
  - Method `.list_files(target_query)` - *List files (ls) on target host's virtual filesystem (requires host to be breached).*
  - Method `.read_file(target_query, file_path)` - *Read file contents (cat) on breached host.*
  - Method `.download_file(target_query, file_path)` - *Download / steal data file from breached host (yields unbanked credits and fulfills bounties).*
  - Method `.wipe_logs(target_query)` - *Clear access logs (wipe_logs) on target host to reduce active trace by 20% and fulfill clean escape clauses.*
  - Method `.tick_daemons()` - *Process active background malware daemons (e.g. keyloggers) and host antivirus sweeps.*
  - Method `.deploy_daemon(target_query, daemon_type)` - *Deploy an in-game background malware listener daemon onto a breached host.*
  - Method `.list_local_files()` - *List files (ls) stored on player's local cyberdeck rig (localhost).*
  - Method `.read_local_file(file_path)` - *Read content (cat) of a file on player's local cyberdeck rig.*
  - Method `.social_engineer(target_query, vector, employee_name)` - *Launch an interactive social engineering attack (pretext, bait, spear_phish, vishing) against target employees.*
  - Method `.phish_target(target_query)` - *Dispatch a simulated social engineering spear-phishing campaign to target host employees (backward compatible).*
  - Method `.get_firewall_status(target_query)` - *Inspect the network firewall rules defending a target host.*
  - Method `.bypass_firewall(target_query, port, method)` - *Execute a firewall bypass against a blocked port via port-knocking, packet fragmentation, or proxy-tunneling.*
  - Method `.get_antivirus_status(target_query)` - *Inspect the active Antivirus / EDR status on a target host.*
  - Method `.evade_antivirus(target_query, method)` - *Inject a stealth evasion hook or memory-patch into a target host's Antivirus suite.*
  - Method `.list_cves()` - *Return the catalog of weaponized CVE exploit payloads.*
  - Method `.craft_virus(recipe_name)` - *Assemble a custom virus chip in the netrunner workshop.*
  - Method `.list_crafting_recipes()` - *List available malware crafting recipes in the workshop.*

---

### [`cyberpulse/models.py`](cyberpulse/models.py)
> *Domain models for CyberPulse cyberspace nodes, decks, contracts, and career profiles.*

**Size**: `491` lines (`16885` bytes)

**Classes:**
- `class NodeType`
- `class NodeStatus`
- `class RewardType`
- `class PortService` - *An exposed TCP/UDP network service on a target host.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class VirtualFile` - *A file stored on a target host's virtual filesystem.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class BountyContract` - *A syndicate-issued objective with bonus rewards upon fulfillment (Zeigarnik Effect).*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class CareerProfile` - *Persistent meta-progression profile tracking permanent stats and upgrades.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class FirewallPolicy`
- `class FirewallRule` - *A packet filtering or port access rule enforced by a host firewall.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class HostFirewall` - *A network firewall defending a host's open ports against unauthorized ingress.*
  - Method `.is_port_blocked(port)`
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class HostAntivirus` - *An active endpoint detection and response (EDR) / antivirus service on a target host.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class ExploitPayload` - *A weaponized vulnerability exploit / CVE targeting specific network services.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class SocialVectorType`
- `class SecurityAwarenessLevel`
- `class EmployeeProfile` - *Target organization employee persona susceptible to social engineering attacks.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class Node` - *A target host or infrastructure subsystem on the network grid.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class MalwareDaemon` - *An active background script deployed on a compromised host (e.g. keylogger, siphon).*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class VirusCraftRecipe` - *A crafting recipe to synthesize custom virus/malware chips in the netrunner workshop.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class CyberDeck` - *The player's hardware deck used to execute hacking exploits.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class Quest` - *A tracked story or side objective with a reward.*
  - Property `.ready`
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class ContactProfile` - *A persistent in-game operative the player can talk to, work for, and call favors on.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class GameState` - *The full runtime state of a CyberPulse infiltration run.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`

**Functions:**
- `def apply_career_profile(deck, profile)` - *Apply persistent upgrades and synchronize banked funds into an active cyberdeck.*

---

### [`cyberpulse/network.py`](cyberpulse/network.py)
> *Procedural cyberspace network generator with deterministic topology.*

**Size**: `209` lines (`11110` bytes)

**Functions:**
- `def generate_network(seed)` - *Generate a deterministic cyberspace infiltration network grid from seed.*

---

### [`cyberpulse/puzzles.py`](cyberpulse/puzzles.py)
> *Interactive and deterministic cyberpunk hacking mini-game puzzles with near-miss feedback.*

**Size**: `101` lines (`4398` bytes)

**Classes:**
- `class FrequencyPuzzle` - *Tuning resonance frequency puzzle with near-miss feedback mechanics.*
  - Method `.__init__(target_freq, tolerance)`
  - Method `.generate(seed)`
  - Method `.tune(guess)` - *Test a frequency guess with near-miss detection.*
- `class BufferPuzzle` - *Memory buffer sequence matching puzzle with partial alignment detection.*
  - Method `.__init__(matrix, target_seq)`
  - Method `.generate(seed)`
  - Method `.verify_sequence(player_seq)` - *Verify whether player's sequence matches with near-miss feedback.*
- `class HashCrackPuzzle` - *Cryptographic password / hash cracking cipher puzzle with single-letter near miss.*
  - Method `.__init__(target_word, word_list)`
  - Method `.generate(seed)`
  - Method `.guess(candidate)` - *Evaluate a guess and return matching character count with near-miss detection.*

---

### [`cyberpulse/rewards.py`](cyberpulse/rewards.py)
> *Variable-ratio reward engine and dopamine loot schedules for CyberPulse.*

**Size**: `39` lines (`1312` bytes)

**Functions:**
- `def roll_breach_reward(node, rng)` - *Calculate variable-ratio reward payout and drops (Skinner box reinforcement schedule).*

---

### [`cyberpulse/server.py`](cyberpulse/server.py)
> *Zero-dependency HTTP REST backend and static file server for CyberPulse Web Cyberdeck.*

**Size**: `619` lines (`27472` bytes)

**Classes:**
- `class CyberdeckSession` - *Encapsulates the stateful game session driving the Web Cyberdeck interface.*
  - Method `.__init__(data_dir, seed)`
  - Method `.settle_run_if_finished()` - *Persist a victory/lockout exactly once as soon as the run reaches a terminal state.*
  - Method `.get_full_state()` - *Aggregate complete runtime state for frontend rendering.*
  - Method `.reset_game(seed)`
- `class CyberdeckHTTPHandler` - *HTTP request handler providing REST API endpoints and static cyberdeck assets.*
  - Method `.log_message(format, *args)` - *Route cyberdeck request logs without cluttering console.*
  - Method `.send_json_response(data, status)`
  - Method `.do_OPTIONS()`
  - Method `.do_GET()`
  - Method `._do_get()`
  - Method `.serve_static(path)`
  - Method `.do_POST()`
  - Method `._do_post(path, payload)`

**Functions:**
- `def coerce_seed(value)` - *Convert API/CLI seed input to an integer, rejecting non-finite or non-numeric values.*
- `def create_server(host, port, data_dir, seed)` - *Instantiate and configure the ThreadingHTTPServer for CyberPulse Web Cyberdeck.*
- `def run_web(host, port, data_dir, seed, open_browser)` - *Launch the Web Cyberdeck server and optionally launch default system web browser.*

---

### [`cyberpulse/shop.py`](cyberpulse/shop.py)
> *Black market cyberdeck upgrades and exploit vendor for CyberPulse.*

**Size**: `135` lines (`4856` bytes)

**Classes:**
- `class ShopItem`
- `class BlackMarketShop` - *Manages purchasing of cyberdeck hardware upgrades and exploit chips.*
  - Method `.__init__(catalog)`
  - Method `.list_available(deck)` - *List all shop items and current upgrade status.*
  - Method `.purchase(deck, item_id)` - *Attempt to buy an item and apply its stat bonuses to deck.*

---

### [`cyberpulse/storage.py`](cyberpulse/storage.py)
> *Crash-resilient savegame and career profile storage engine for CyberPulse.*

**Size**: `122` lines (`4803` bytes)

**Classes:**
- `class SaveManager` - *Manages atomic saving and loading of game states and career profiles.*
  - Method `.__init__(data_dir)`
  - Method `._write_atomic(target_path, data)` - *Write JSON payload to target_path atomically; returns None when the replace never lands.*
  - Method `._read_json_with_backup(target_path)` - *Read JSON from target_path, falling back to shadow .bak if corrupted or missing.*
  - Method `.save(engine)` - *Atomically persist engine state to disk.*
  - Method `.load()` - *Load and restore engine state from savegame with backup recovery.*
  - Method `.delete_save()` - *Remove savegame and its shadow backup after completed or failed run.*
  - Method `.save_career(profile)` - *Atomically persist career meta-progression profile.*
  - Method `.load_career()` - *Load persistent career profile with backup recovery or return fresh profile.*

---

### [`cyberpulse/story.py`](cyberpulse/story.py)
> *Story acts, quest blueprints, and operative dialogue for CyberPulse.*

**Size**: `265` lines (`10563` bytes)

**Functions:**
- `def initial_quests()` - *Return the persistent quest board for a new run.*
- `def initial_contacts()` - *Return the operatives available to a new run.*
- `def act_title(act)`
- `def dialogue_for(contact_id, act, choice)`

---

### [`tests/__init__.py`](tests/__init__.py)
> *Test suite for CyberPulse.*

**Size**: `1` lines (`33` bytes)

---

### [`tests/test_cli.py`](tests/test_cli.py)
> *Integration tests for CyberPulse CLI.*

**Size**: `300` lines (`12692` bytes)

**Classes:**
- `class TestCLI`
  - Method `.setUp()`
  - Method `.run_cli(*args)`
  - Method `.test_cli_help()`
  - Method `.test_main_menu_quit()`
  - Method `.test_main_menu_starts_run_then_quits()`
  - Method `.test_story_quests_contacts_and_overdrive_commands()`
  - Method `.test_agent_zero_alliance_after_act_three()`
  - Method `.test_jackout_records_best_combo_in_career()`
  - Method `.test_contact_job_and_favor_commands()`
  - Method `.test_batch_infiltration_playthrough()`
  - Method `.test_jackout_command()`
  - Method `.test_shop_and_buy_command()`
  - Method `.test_career_progression_across_sessions()`
  - Method `.test_exploit_command()`
  - Method `.test_ram_insufficient_message_in_cli()`
  - Method `.test_simulation_cli_workflow()`
  - Method `.test_cli_virtual_rig_and_phishing_commands()`
  - Method `.test_cli_cyber_warfare_commands()`
  - Method `.test_handle_run_completion_in_batch_mode()`
  - Method `.test_lifetime_creds_not_double_counted()`
  - Method `.test_bypass_rejects_non_numeric_port()`
  - Method `.test_minigame_eof_stops_batch_without_traceback()`
  - Method `.test_cli_reuses_pending_puzzle_attempts()`

---

### [`tests/test_engine.py`](tests/test_engine.py)
> *Unit tests for CyberPulse game engine.*

**Size**: `824` lines (`35170` bytes)

**Classes:**
- `class TestEngine`
  - Method `.setUp()`
  - Method `.test_initial_state()`
  - Method `.test_scan_reveals_connected()`
  - Method `.test_cannot_move_to_unbreached_node()`
  - Method `.test_breach_and_move()`
  - Method `.test_trace_lockout_burns_unbanked_loot()`
  - Method `.test_jackout_safely_banks_loot()`
  - Method `.test_ice_dampener_reduces_trace_gain()`
  - Method `.test_bounty_contract_fulfillment()`
  - Method `.test_cpu_regeneration()`
  - Method `.test_ram_capacity_check()`
  - Method `.test_use_exploit_ghost_protocol()`
  - Method `.test_use_exploit_logic_bomb()`
  - Method `.test_use_exploit_brute_miner()`
  - Method `.test_find_node_by_ip_and_hostname()`
  - Method `.test_probe_host()`
  - Method `.test_exploit_service()`
  - Method `.test_virtual_filesystem_simulation()`
  - Method `.test_wipe_logs_trace_reduction()`
  - Method `.test_local_deck_filesystem_and_loot_archiving()`
  - Method `.test_phishing_dispatch()`
  - Method `.test_craft_virus_workshop()`
  - Method `.test_deploy_and_tick_keylogger_daemon()`
  - Method `.test_firewall_inspection_and_bypass()`
  - Method `.test_antivirus_status_and_evasion()`
  - Method `.test_cve_catalog_and_exploit_execution()`
  - Method `.test_social_engineering_vectors()`
  - Method `.test_game_over_and_jacked_out_guards()`
  - Method `.test_defensive_input_sanitization()`
  - Method `.test_exploit_service_turn_advancement()`
  - Method `.test_complete_breach_is_idempotent()`
  - Method `.test_worm_replicator_rejects_breached_target_without_consuming_chip()`
  - Method `.test_spoof_reports_actual_reduction()`
  - Method `.test_spoof_rejects_zero_trace_without_burning_cpu()`
  - Method `.test_tick_daemons_stops_after_lockout()`
  - Method `.test_bypass_and_evade_require_direct_subnet()`
  - Method `.test_social_engineering_requires_direct_subnet()`
  - Method `.test_wipe_logs_is_idempotent()`
  - Method `.test_probe_advances_daemon_tick()`
  - Method `.test_pending_puzzle_keeps_attempts_between_calls()`
  - Method `.test_settle_career_banks_victory_loot_once()`
  - Method `.test_exploit_lockout_does_not_claim_root_access()`
  - Method `.test_float_seed_is_coerced()`
  - Method `.test_run_summary_reflects_legacy()`
  - Method `.test_settle_career_records_best_combo_on_failure()`
  - Method `.test_run_summary_victory_marks_main_story_complete()`
  - Method `.test_mutating_actions_reject_after_victory()`
  - Method `.test_story_state_and_contacts_initialize()`
  - Method `.test_overdrive_stacks_combo_and_trace()`
  - Method `.test_gateway_quest_advances_story_and_unlocks_contact()`
  - Method `.test_main_story_quest_chain_reaches_finale()`
  - Method `.test_contact_job_and_favor()`
  - Method `.test_locked_contact_rejects_interaction()`
  - Method `.test_agent_zero_pact_requires_act_three()`
  - Method `.test_agent_zero_alliance_branch()`
  - Method `.test_agent_zero_defiance_branch()`
  - Method `.test_locked_story_quest_cannot_be_accepted_early()`
  - Method `.test_archivist_favor_reveals_locked_node()`
  - Method `.test_ensure_story_state_backfills_old_save()`
  - Method `.test_out_of_order_ice_breach_still_completes_black_ice_quest()`
  - Method `.test_out_of_order_file_theft_counts_when_money_quest_unlocks()`
  - Method `.test_out_of_order_log_wipe_completes_side_quest_when_accepted()`
  - Method `.test_accept_quest_rejects_terminal_states()`
  - Method `.test_core_is_sealed_until_act_four()`
  - Method `.test_download_contract_respects_trace_limit()`

---

### [`tests/test_init.py`](tests/test_init.py)
> *Smoke test for cyberpulse package.*

**Size**: `13` lines (`266` bytes)

**Classes:**
- `class TestCyberpulseInit`
  - Method `.test_version_defined()`

---

### [`tests/test_models.py`](tests/test_models.py)
> *Unit tests for CyberPulse domain models.*

**Size**: `222` lines (`9003` bytes)

**Classes:**
- `class TestModels`
  - Method `.test_node_roundtrip()`
  - Method `.test_port_and_file_roundtrip()`
  - Method `.test_deck_roundtrip()`
  - Method `.test_recipe_roundtrip()`
  - Method `.test_game_state_roundtrip()`
  - Method `.test_career_profile_roundtrip()`
  - Method `.test_apply_career_profile()`
  - Method `.test_firewall_and_antivirus_models()`
  - Method `.test_exploit_payload_and_employee_models()`
  - Method `.test_node_with_cyber_warfare_components()`
  - Method `.test_known_cves_deck_and_catalog()`

---

### [`tests/test_network.py`](tests/test_network.py)
> *Unit tests for procedural network generation.*

**Size**: `49` lines (`2084` bytes)

**Classes:**
- `class TestNetwork`
  - Method `.test_network_topology()`
  - Method `.test_deterministic_generation()`
  - Method `.test_network_simulation_topology()`

---

### [`tests/test_puzzles.py`](tests/test_puzzles.py)
> *Unit tests for CyberPulse hacking mini-game puzzles.*

**Size**: `57` lines (`1790` bytes)

**Classes:**
- `class TestPuzzles`
  - Method `.test_frequency_puzzle_tuning()`
  - Method `.test_frequency_exhaustion()`
  - Method `.test_buffer_puzzle_verification()`
  - Method `.test_hash_crack_puzzle()`

---

### [`tests/test_rewards.py`](tests/test_rewards.py)
> *Unit tests for variable-ratio rewards and dopamine loot schedules.*

**Size**: `55` lines (`1827` bytes)

**Classes:**
- `class TestRewards`
  - Method `.setUp()`
  - Method `.test_zero_reward_node()`
  - Method `.test_exploit_chip_drop_threshold()`
  - Method `.test_jackpot_multiplier()`

---

### [`tests/test_server.py`](tests/test_server.py)
> *Unit and integration tests for CyberPulse HTTP REST server.*

**Size**: `504` lines (`21659` bytes)

**Classes:**
- `class TestCyberdeckServer`
  - Method `.setUpClass()`
  - Method `.tearDownClass()`
  - Method `._get(path)`
  - Method `._post(path, payload)`
  - Method `.test_get_state()`
  - Method `.test_get_shop()`
  - Method `.test_get_career()`
  - Method `.test_action_scan_and_spoof()`
  - Method `.test_puzzle_endpoint_and_solve()`
  - Method `.test_static_not_found()`
  - Method `.test_static_path_traversal_blocked()`
  - Method `.test_static_assets_served()`
  - Method `.test_server_simulation_actions()`
  - Method `.test_get_workshop_and_local_files()`
  - Method `.test_server_phish_craft_and_daemon()`
  - Method `.test_get_cves_firewall_antivirus()`
  - Method `.test_firewall_bypass_evade_and_social()`
  - Method `.test_malformed_port_is_rejected_with_json_error()`
  - Method `.test_craft_accepts_recipe_name_from_web_client()`
  - Method `.test_json_responses_do_not_enable_wildcard_cors()`
  - Method `.test_reset_accepts_float_seed()`
  - Method `.test_reset_rejects_invalid_seed()`
  - Method `.test_puzzle_retry_keeps_remaining_attempts()`
  - Method `.test_victory_settles_career_once()`
  - Method `.test_game_over_settles_failed_run_once()`
  - Method `.test_craft_persists_banked_spend()`
  - Method `.test_web_settlement_does_not_delete_unowned_save()`
  - Method `.test_state_includes_story_quests_and_contacts()`
  - Method `.test_overdrive_action()`
  - Method `.test_contact_talk_job_and_favor_actions()`
  - Method `.test_agent_zero_alliance_action()`
  - Method `.test_accept_quest_action()`
  - Method `.test_accept_quest_after_jackout_is_rejected()`
  - Method `.test_static_assets_do_not_wait_for_session_lock()`

---

### [`tests/test_shop.py`](tests/test_shop.py)
> *Unit tests for Black Market Shop in CyberPulse.*

**Size**: `55` lines (`1977` bytes)

**Classes:**
- `class TestShop`
  - Method `.setUp()`
  - Method `.test_list_items()`
  - Method `.test_purchase_cpu_overclock()`
  - Method `.test_purchase_ice_dampener()`
  - Method `.test_purchase_insufficient_funds()`
  - Method `.test_purchase_max_level()`

---

### [`tests/test_storage.py`](tests/test_storage.py)
> *Unit tests for CyberPulse savegame and career profile persistence.*

**Size**: `169` lines (`6086` bytes)

**Classes:**
- `class TestStorage`
  - Method `.setUp()`
  - Method `.test_save_and_load()`
  - Method `.test_load_nonexistent()`
  - Method `.test_save_preserves_story_quests_and_contacts()`
  - Method `.test_load_backfills_story_for_old_save()`
  - Method `.test_career_save_and_load()`
  - Method `.test_career_default_fallback()`
  - Method `.test_old_career_payload_uses_best_combo_default()`
  - Method `.test_load_corrupted_save_with_backup_recovery()`
  - Method `.test_load_corrupted_career_with_backup_recovery()`
  - Method `.test_delete_save()`
  - Method `.test_rng_reseeding_on_load()`
  - Method `.test_failed_replace_reports_no_save()`

---
