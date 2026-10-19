"""Interactive and scriptable retro-cyberpunk terminal CLI for CyberPulse with behavioral mechanics."""

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path when executed directly as a script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List, Optional

from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile, CyberDeck, NodeStatus, NodeType
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle
from cyberpulse.shop import BlackMarketShop
from cyberpulse.storage import SaveManager
from cyberpulse.world import clock_minute_text


def setup_terminal_encoding() -> None:
    """Ensure stdout and stderr handle utf-8 safely across all Windows code pages."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):  # hygiene: allow detached stream; plain prints still work
                pass


def safe_print(msg: str) -> None:
    """Print message to stdout with graceful fallback for legacy terminal code pages."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode("ascii", errors="replace").decode("ascii"))
        except (OSError, ValueError):  # hygiene: allow fallback stream unusable, nowhere to report
            pass


setup_terminal_encoding()


def get_default_data_dir() -> Path:
    return Path.cwd() / ".cyberpulse"


def render_trace_bar(trace_percent: int, width: int = 20) -> str:
    filled = int((trace_percent / 100) * width)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {trace_percent}%"


def print_hud(engine: GameEngine) -> None:
    curr = engine.get_current_node()
    trace_bar = render_trace_bar(engine.state.trace_percent)

    unbanked_str = f" [PUSH-YOUR-LUCK: +{engine.state.unbanked_creds} UNBANKED!]" if engine.state.unbanked_creds > 0 else ""
    contract = engine.state.active_contract
    if contract:
        target_info = f" -> Target: {contract.target_ip or contract.target_node_type}"
        if contract.target_file:
            target_info += f" ({contract.target_file})"
        status_tag = "[COMPLETED]" if contract.completed else "[ACTIVE]"
        contract_str = f"{contract.title}{target_info} (+{contract.reward_creds} Creds) {status_tag}"
    else:
        contract_str = "None"

    print("\n+==========================================================================+")
    print("|          >> CYBERPULSE // NEURAL INTRUSION HARNESS v0.3.0 <<             |")
    print("+==========================================================================+")
    print(f"[*] Location:   {curr.name} | {curr.hostname} ({curr.ip_address}) [{curr.node_id}]")
    print(f"[*] Local Rig:  {engine.deck.local_hostname} ({engine.deck.local_ip}) [{engine.deck.model_name}]")
    print(f"[*] Trace:      {trace_bar} | Turns: {engine.state.turns_elapsed}")
    print(f"[*] Deck:       CPU: {engine.deck.cpu_cycles}/{engine.deck.max_cpu} | RAM: {engine.deck.ram_mb}MB | Creds: {engine.deck.cryptocreds}{unbanked_str}")
    print(f"[*] Upgrades:   ICE Dampener: Lvl {engine.deck.ice_dampener_level} | Overclock: Lvl {engine.deck.overclock_level}")
    exploits_str = ', '.join(engine.deck.exploits) if engine.deck.exploits else "None"
    print(f"[*] Exploits:   {exploits_str}")
    if engine.deck.active_daemons:
        print(f"[*] Daemons:    {len(engine.deck.active_daemons)} background listener(s) active")
    print(f"[*] Contract:   {contract_str}")
    if engine.state.near_miss_count > 0:
        print(f"[*] Adrenaline: [NEAR-MISS ENCOUNTERS: {engine.state.near_miss_count}]")
    story = engine.story_summary()
    active_quests = sum(1 for q in engine.state.quests if q.accepted and not q.completed)
    print(f"[*] Story:      {story['act_title']} // {story['chapter_title']} | Combo: x{engine.state.combo_streak} | Quests: {active_quests} active")
    world = engine.state.world
    world_info = engine.world_summary()
    print(f"[*] Grid:       {world_info['clock']} | Alert: {world.alert_level}% | Market: x{world_info['market_multiplier']}")
    print("--------------------------------------------------------------------------")
    print("Discovered Subnet Nodes:")
    for cid in curr.connected_ids:
        adj = engine.nodes.get(cid)
        if adj:
            icon = "[BREACHED]" if adj.status == NodeStatus.BREACHED else ("[DISCOVERED]" if adj.status == NodeStatus.DISCOVERED else "[LOCKED]")
            print(f"   * {adj.ip_address:<15} | {adj.hostname:<24} | {icon} (Sec: {adj.security_level})")
    print("+==========================================================================+")


def print_shop(shop: BlackMarketShop, deck: CyberDeck, price_multiplier: float = 1.0) -> None:
    items = shop.list_available(deck, price_multiplier=price_multiplier)
    print("\n+==========================================================================+")
    print("|                   >> BLACK MARKET CYBER-VENDOR <<                        |")
    print("+==========================================================================+")
    print(f"[*] Available Funds: {deck.cryptocreds} CryptoCreds | Market index: x{price_multiplier:.3f}")
    if price_multiplier > 1.0:
        print("[!] The grid is hot: black-market prices are marked up tonight.")
    elif price_multiplier < 1.0:
        print("[*] A quiet grid: black-market prices are discounted tonight.")
    print()
    for it in items:
        status = f"Lvl {it['current_level']}/{it['max_level']}" if it['max_level'] > 1 else ("OWNED" if it['current_level'] > 0 else "AVAILABLE")
        buy_tag = "[AFFORDABLE]" if it['can_buy'] else "[LOCKED]"
        cost_str = f"{it['cost']}" if it['cost'] == it['base_cost'] else f"{it['cost']} (base {it['base_cost']})"
        print(f"   * {it['item_id']:<18} | Cost: {cost_str:<16} Creds | {status:<12} | {buy_tag}")
        print(f"     Description: {it['description']}")
    print("--------------------------------------------------------------------------")
    print("Buy with: buy <item_id> (e.g. `buy overclock_cpu` or `buy ice_dampener`)")
    print("+==========================================================================+")


def print_career(profile: CareerProfile) -> None:
    print("\n+==========================================================================+")
    print(f"|               >> HACKER CAREER DOSSIER: {profile.alias} <<                  |")
    print("+==========================================================================+")
    print(f"[*] Banked Funds:     {profile.banked_creds} CryptoCreds")
    print(f"[*] Lifetime Stolen:  {profile.lifetime_creds} CryptoCreds")
    print(f"[*] Heists Cleared:   {profile.successful_runs} successful | {profile.failed_runs} severed")
    print(f"[*] Infiltration Run: Streak: {profile.current_streak} (Best: {profile.best_streak})")
    print(f"[*] Best Neural Combo: x{profile.best_combo}")
    upgrades = ', '.join(profile.purchased_upgrades) if profile.purchased_upgrades else "None"
    print(f"[*] Hardware Rig:     {upgrades}")
    print("+==========================================================================+")


def print_workshop(engine: GameEngine) -> None:
    recipes = engine.list_crafting_recipes()
    total_funds = engine.deck.cryptocreds + engine.state.unbanked_creds
    print("\n+==========================================================================+")
    print("|               >> NETRUNNER MALWARE SYNTHESIS BAY <<                      |")
    print("+==========================================================================+")
    print(f"[*] Available Funds: {total_funds} CryptoCreds (Banked: {engine.deck.cryptocreds}, Unbanked: {engine.state.unbanked_creds})\n")
    for r in recipes:
        can_afford = total_funds >= r["cost_creds"]
        afford_tag = "[AFFORDABLE]" if can_afford else "[INSUFFICIENT FUNDS]"
        print(f"   * {r['name']:<18} | Cost: {r['cost_creds']:<3}cr | Vector: {r['vector']:<7} | {afford_tag}")
        print(f"     Payload: {r['payload']} | {r['description']}")
    print("--------------------------------------------------------------------------")
    print("Synthesize with: craft <recipe_name> (e.g. `craft worm_replicator` or `craft keylogger_daemon`)")
    print("+==========================================================================+")


def print_daemons(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|              >> ACTIVE BACKGROUND MALWARE DAEMONS <<                     |")
    print("+==========================================================================+")
    if not engine.deck.active_daemons:
        print("   No background daemons currently deployed.")
    else:
        for d in engine.deck.active_daemons:
            node = engine.nodes.get(d.target_node_id)
            hname = node.hostname if node else d.target_ip
            print(f"   * {d.daemon_id} [{d.daemon_type.upper()}] on {hname} ({d.target_ip})")
            print(f"     Yield: +{d.yield_per_turn} unbanked creds/turn | Detection Trace: +{d.detection_risk}%/turn | Turns Active: {d.turns_active}")
    print("+==========================================================================+")


def print_cves(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|             >> WEAPONIZED CVE VULNERABILITY EXPLOIT CATALOG <<          |")
    print("+==========================================================================+")
    cves = engine.list_cves()
    for c in cves:
        print(f"   * {c['cve_id']:<15} | {c['name']:<28} | Target: {c['target_service'].upper():<5}")
        print(f"     RAM: {c['required_ram_mb']}MB | CPU: {c['cpu_cost']} | Stealth: {c['stealth_rating']}/5 | Trace: +{c['damage_trace']}%")
        print(f"     {c['description']}")
    print("--------------------------------------------------------------------------")
    print("Deploy with: exploit <ip> <port> [cve_id] (e.g. `exploit 192.168.1.10 21 cve-2011-2523`)")
    print("+==========================================================================+")


def print_story(engine: GameEngine) -> None:
    story = engine.story_summary()
    print("\n+==========================================================================+")
    print(f"|                 >> STORY // {story['act_title']}: {story['chapter_title']} <<")
    print("+==========================================================================+")
    print(f"[*] {story['intro']}")
    print("--------------------------------------------------------------------------")
    for line in story["log"][-6:]:
        print(f"   > {line}")
    print("+==========================================================================+")


def print_world(engine: GameEngine) -> None:
    summary = engine.world_summary()
    print("\n+==========================================================================+")
    print("|                    >> LIVING GRID // CITY PULSE <<                       |")
    print("+==========================================================================+")
    print(f"[*] Clock:      {summary['clock']}")
    print(f"[*] Shift:      {summary['shift']} | Grid Alert: {summary['alert_level']}%")
    print(f"[*] Market:     x{summary['market_multiplier']} black-market index | Re-secured hosts: {summary['resecured_count']}")
    print("--------------------------------------------------------------------------")
    print("Latest headlines:")
    for item in summary["news"][-8:]:
        print(f"   > [{item['source']}] {item['headline']}")
    print("--------------------------------------------------------------------------")
    print("News wire: news | Flip through the whole feed with: news 20")
    print("+==========================================================================+")


def print_news(engine: GameEngine, limit: int = 12) -> None:
    items = engine.news_feed(limit)
    print("\n+==========================================================================+")
    print("|                       >> GRID NEWS WIRE <<                               |")
    print("+==========================================================================+")
    if not items:
        print("   > (the wire is quiet; breach a host to make headlines)")
    for item in items:
        stamp = f"Day {item['day']} {clock_minute_text(item['minute'])}"
        print(f"   > [{stamp}] {item['source']}: {item['headline']}")
    print("+==========================================================================+")


def print_run_summary(engine: GameEngine) -> None:
    summary = engine.run_summary()
    print("\n+==========================================================================+")
    print(f"|                 >> RUN LEGACY // {summary['outcome_title']} <<")
    print("+==========================================================================+")
    print(f"[*] Story:       {summary['story_title']}")
    print(f"[*] Best Combo:  x{summary['best_combo']} | Quests: {summary['quests_completed_count']}/{summary['quests_total']}")
    real_contacts = [c for c in summary["contacts"] if c["trust"] > 0 or c["favor_used"]]
    if real_contacts:
        print("[*] Operatives:  " + ", ".join(
            f"{c['name']} (trust {c['trust']}{', favor spent' if c['favor_used'] else ''})"
            for c in real_contacts
        ))
    print("--------------------------------------------------------------------------")
    for line in summary["epilogue"]:
        print(f"   > {line}")
    print("+==========================================================================+")


def print_quests(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|                     >> MISSION BOARD // QUESTS <<                        |")
    print("+==========================================================================+")
    for quest in engine.state.quests:
        if quest.completed:
            status = "[COMPLETE]"
        elif engine.is_quest_locked(quest):
            status = "[LOCKED]"
        elif quest.accepted:
            status = f"[{quest.progress}/{max(1, quest.required)}]"
        else:
            status = "[AVAILABLE]"
        giver = engine._find_contact(quest.giver)
        giver_name = giver.name if giver else quest.giver
        print(f"   * {quest.quest_id:<16} {status:<12} {quest.title} (+{quest.reward_creds} CR)")
        print(f"     {quest.description} // Contact: {giver_name}")
    print("--------------------------------------------------------------------------")
    print("Accept with: accept <quest_id>. Talk to contacts with: contact <handle> job")
    print("+==========================================================================+")


def print_contacts(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|                    >> OPERATIVE CHANNELS // CONTACTS <<                  |")
    print("+==========================================================================+")
    for contact in engine.list_contacts():
        if contact["locked"]:
            print(f"   * {contact['handle']:<16} [SIGNAL LOCKED] {contact['name']}")
            continue
        favor = "SPENT" if contact["favor_used"] else "READY"
        print(f"   * {contact['handle']:<16} {contact['name']:<16} Trust: {contact['trust']} | Favor: {favor}")
        print(f"     {contact['role']} // {contact['faction']} // {contact['tagline']}")
        print(f"     \"{contact['dialogue']}\"")
    print("--------------------------------------------------------------------------")
    print("Talk: contact <handle> talk | Job: contact <handle> job | Favor: contact <handle> favor")
    print("+==========================================================================+")


def show_main_menu(engine: GameEngine, save_mgr: SaveManager) -> str:
    """Render the interactive main menu and return 'start', 'load', or 'quit'."""
    print("\n+==========================================================================+")
    print("|              >> CYBERPULSE // NEURAL INTRUSION HARNESS <<                |")
    print("|                              MAIN MENU                                   |")
    print("+==========================================================================+")
    print("|  [1] JACK IN (new run)       [2] CONTINUE (load save)                    |")
    print("|  [3] STORY BRIEFING          [4] OPERATIVES                              |")
    print("|  [5] CAREER DOSSIER          [6] HOW TO PLAY                             |")
    print("|  [Q] QUIT                                                                |")
    print("+==========================================================================+")

    while True:
        try:
            choice = input("main-menu> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Neural link closed.")
            return "quit"

        if choice in ("1", "start", "new", "jackin", "jack in"):
            return "start"
        if choice in ("2", "continue", "load"):
            return "load"
        if choice in ("3", "story", "brief"):
            print_story(engine)
            print_quests(engine)
            continue
        if choice in ("4", "contacts", "crew"):
            print_contacts(engine)
            continue
        if choice in ("5", "career"):
            print_career(save_mgr.load_career())
            continue
        if choice in ("6", "help", "how"):
            print("Commands: status, story, quests, contacts, contact, accept, world, news, scan, probe, exploit,")
            print("          bypass, evade, social, ls, cat, steal, wipe_logs, keylogger, craft,")
            print("          move, overdrive, spoof, cash_out, shop, buy, career, save, load, quit")
            continue
        if choice in ("q", "quit", "exit"):
            print("👋 Neural link closed.")
            return "quit"
        print("Unknown choice. Enter 1-6 or Q.")


def execute_hack_puzzle(engine: GameEngine, target_id: str, auto_solve: bool = False) -> bool:
    can_hack, reason, puzzle, node = engine.get_or_create_puzzle(target_id)
    if not can_hack or node is None or puzzle is None:
        print(f"⚠️ {reason}")
        return False

    print(f"\n⚡ INITIATING CYBER-ATTACK ON: {node.name} (Sec Level: {node.security_level})")

    # If auto_solve is True (used in batch/tests)
    if auto_solve:
        engine.clear_pending_puzzle(target_id)
        _, msg = engine.complete_breach(target_id)
        print(msg)
        return True

    # Puzzle execution based on node puzzle_type
    p_type = node.puzzle_type or "frequency"
    if p_type == "frequency" and isinstance(puzzle, FrequencyPuzzle):
        print(f"📡 TUNING PROTOCOL: Target frequency between 20.0 and 99.0 GHz (tolerance ±{puzzle.tolerance} GHz).")
        while puzzle.attempts_left > 0:
            val_str = input(f"Enter target GHz [{puzzle.attempts_left} tries left]: ").strip()
            try:
                guess = float(val_str)
            except ValueError:
                print("Invalid frequency value.")
                continue
            ok, msg = puzzle.tune(guess)
            print(msg)
            if puzzle.near_miss:
                engine.state.near_miss_count += 1
            if ok:
                engine.clear_pending_puzzle(target_id)
                engine.complete_breach(target_id)
                return True
        engine.clear_pending_puzzle(target_id)
        engine.add_trace(node.trace_rate)
        return False

    elif p_type == "buffer" and isinstance(puzzle, BufferPuzzle):
        print("💾 BUFFER OVERFLOW PROTOCOL: Inject target hex sequence:")
        print(f"   Target: {puzzle.target_seq}")
        seq_str = input("Enter hex codes separated by space: ").strip().upper()
        player_seq = seq_str.split()
        ok, msg = puzzle.verify_sequence(player_seq)
        print(msg)
        if puzzle.near_miss:
            engine.state.near_miss_count += 1
        engine.clear_pending_puzzle(target_id)
        if ok:
            engine.complete_breach(target_id)
            return True
        engine.add_trace(node.trace_rate)
        return False

    elif p_type == "hash" and isinstance(puzzle, HashCrackPuzzle):
        print(f"🔑 HASH CRACK PROTOCOL: Potential keys: {', '.join(puzzle.word_list)}")
        while puzzle.attempts_left > 0:
            guess = input(f"Guess keyword [{puzzle.attempts_left} tries left]: ").strip()
            ok, msg = puzzle.guess(guess)
            print(msg)
            if puzzle.near_miss:
                engine.state.near_miss_count += 1
            if ok:
                engine.clear_pending_puzzle(target_id)
                engine.complete_breach(target_id)
                return True
        engine.clear_pending_puzzle(target_id)
        engine.add_trace(node.trace_rate)
        return False

    engine.clear_pending_puzzle(target_id)
    engine.complete_breach(target_id)
    return True


def run_command(cmd_line: str, engine: GameEngine, save_mgr: SaveManager, auto_solve: bool = False) -> bool:
    """Execute a single command string. Returns False to quit."""
    parts = cmd_line.strip().split()
    if not parts:
        return True
    action = parts[0].lower()
    shop = BlackMarketShop()

    if action in ("q", "quit", "exit"):
        print("👋 Neural link terminated.")
        return False

    if action == "status":
        print_hud(engine)
        return True

    if action in ("story", "lore"):
        print_story(engine)
        return True

    if action in ("world", "city", "grid"):
        print_world(engine)
        return True

    if action in ("news", "wire", "headlines"):
        limit = 12
        if len(parts) > 1 and parts[1].isdigit():
            limit = max(1, min(60, int(parts[1])))
        print_news(engine, limit)
        return True

    if action in ("quests", "missions", "jobs"):
        print_quests(engine)
        return True

    if action in ("contacts", "crew", "operatives"):
        print_contacts(engine)
        return True

    if action in ("contact", "talk", "interact"):
        if len(parts) < 2:
            print("Usage: contact <handle | name> [talk | job | favor | ally | defy]")
            return True
        mode = parts[2] if len(parts) > 2 else "talk"
        ok, msg, _ = engine.interact_contact(parts[1], mode)
        print(msg)
        return True

    if action in ("accept", "take", "accept_quest"):
        if len(parts) < 2:
            print("Usage: accept <quest_id> (see `quests`)")
            return True
        ok, msg = engine.accept_quest(parts[1])
        print(msg)
        return True

    if action == "scan":
        ok, msg, _ = engine.scan_surroundings()
        print(msg)
        return True

    if action in ("move", "cd", "ssh"):
        if len(parts) < 2:
            print("Usage: move <ip | hostname | node_id>")
            return True
        node = engine.find_node(parts[1])
        target_id = node.node_id if node else parts[1]
        ok, msg = engine.move_to(target_id)
        print(msg)
        return True

    if action in ("probe", "nmap"):
        if len(parts) < 2:
            print("Usage: probe <ip | hostname | node_id> (e.g. `probe 192.168.1.10`)")
            return True
        ok, summary, _ = engine.probe_host(parts[1])
        print(summary)
        return True

    if action in ("hack", "breach"):
        if len(parts) < 2:
            print("Usage: hack <node_id | ip> [port]")
            return True
        target_query = parts[1]
        # If user passed a port number (e.g. hack 192.168.1.10 21)
        if len(parts) >= 3 and parts[2].isdigit():
            ok, msg = engine.exploit_service(target_query, int(parts[2]))
            print(msg)
            return True
        # Resolve node_id if target_query is IP or hostname
        node = engine.find_node(target_query)
        target_id = node.node_id if node else target_query
        execute_hack_puzzle(engine, target_id, auto_solve=auto_solve)
        return True

    if action in ("exploit", "use"):
        if len(parts) < 2:
            exploits_list = ', '.join(engine.deck.exploits) if engine.deck.exploits else 'None'
            print(f"Usage: exploit <ip> <port> (e.g. `exploit 192.168.1.10 21`)\n       exploit <chip_name> [target] (Loaded chips: {exploits_list})")
            return True
        # Check if second arg is digit -> service port exploit
        if len(parts) >= 3 and parts[2].isdigit():
            cve_arg = parts[3] if len(parts) > 3 else None
            ok, msg = engine.exploit_service(parts[1], int(parts[2]), cve_id=cve_arg)
            print(msg)
            return True
        exploit_name = parts[1]
        target = parts[2] if len(parts) > 2 else None
        ok, msg = engine.use_exploit(exploit_name, target)
        print(msg)
        return True

    if action in ("ls", "dir"):
        target = parts[1] if len(parts) > 1 else None
        ok, output, _ = engine.list_files(target)
        print(output)
        return True

    if action == "cat":
        if len(parts) < 2:
            print("Usage: cat [ip] <filepath> (e.g. `cat /etc/hosts` or `cat local /home/deck/notes.txt`)")
            return True
        if len(parts) == 2:
            path_arg = parts[1]
            if path_arg.startswith(("/home/deck", "/loot", "/bin")):
                ok, output, _ = engine.read_local_file(path_arg)
            else:
                ok, output, _ = engine.read_file(engine.state.current_node_id, path_arg)
        else:
            target_arg = parts[1].lower()
            if target_arg in ("local", "localhost", "myip", "deck", "10.99.0.2", "127.0.0.1"):
                ok, output, _ = engine.read_local_file(parts[2])
            else:
                ok, output, _ = engine.read_file(parts[1], parts[2])
        print(output)
        return True

    if action in ("download", "steal"):
        if len(parts) < 2:
            print("Usage: steal [ip] <filepath> (e.g. `steal /data/corporate_slush_fund.csv`)")
            return True
        if len(parts) == 2:
            target = engine.state.current_node_id
            filepath = parts[1]
        else:
            target = parts[1]
            filepath = parts[2]
        ok, msg, _ = engine.download_file(target, filepath)
        print(msg)
        return True

    if action in ("wipe_logs", "wipe", "clean_logs"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg = engine.wipe_logs(target)
        print(msg)
        return True

    if action == "spoof":
        ok, msg = engine.spoof_ip()
        print(msg)
        return True

    if action in ("overdrive", "od", "surge"):
        ok, msg = engine.overdrive()
        print(msg)
        return True

    if action in ("jackout", "cash_out"):
        ok, msg = engine.jackout()
        print(msg)
        if ok:
            # Update career meta-progression through the shared run lifecycle.
            profile = save_mgr.load_career()
            engine.settle_career(profile)
            if save_mgr.save_career(profile):
                save_mgr.delete_save()
                print("📂 Career progression profile updated.")
            else:
                print("❌ Career update failed: progress is NOT persisted.")
            print_run_summary(engine)
        return True

    if action == "shop":
        print_shop(shop, engine.deck, price_multiplier=engine.world_summary()["market_multiplier"])
        return True

    if action == "buy":
        if len(parts) < 2:
            print("Usage: buy <item_id> (e.g. `buy overclock_cpu`)")
            return True
        ok, msg = shop.purchase(engine.deck, parts[1], price_multiplier=engine.world_summary()["market_multiplier"])
        print(msg)
        if ok:
            profile = save_mgr.load_career()
            profile.purchased_upgrades.append(parts[1])
            profile.banked_creds = engine.deck.cryptocreds
            save_mgr.save_career(profile)
        return True

    if action in ("myip", "whoami"):
        print(f"[*] Cyberdeck Local Identity: {engine.deck.local_hostname} ({engine.deck.local_ip}) [{engine.deck.model_name}]")
        return True

    if action in ("myfiles", "local_ls", "myloot"):
        ok, out, _ = engine.list_local_files()
        print(out)
        return True

    if action in ("phish", "spearphish"):
        if len(parts) < 2:
            print("Usage: phish <ip | hostname>")
            return True
        ok, msg, _ = engine.phish_target(parts[1])
        print(msg)
        return True

    if action in ("workshop", "recipes"):
        print_workshop(engine)
        return True

    if action == "craft":
        if len(parts) < 2:
            print_workshop(engine)
            return True
        ok, msg = engine.craft_virus(parts[1])
        print(msg)
        if ok:
            profile = save_mgr.load_career()
            profile.banked_creds = engine.deck.cryptocreds
            save_mgr.save_career(profile)
        return True

    if action in ("keylogger", "deploy_keylogger"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg = engine.deploy_daemon(target, "keylogger")
        print(msg)
        return True

    if action in ("daemons", "ps"):
        print_daemons(engine)
        return True

    if action in ("cve", "cves", "exploits"):
        print_cves(engine)
        return True

    if action in ("firewall", "fw"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg, _ = engine.get_firewall_status(target)
        print(msg)
        return True

    if action in ("bypass", "bypass_firewall"):
        if len(parts) < 3:
            print("Usage: bypass <ip> <port> [knock | fragment | tunnel] (e.g. `bypass 192.168.1.20 22 knock`)")
            return True
        target = parts[1]
        try:
            port = int(parts[2])
        except ValueError:
            print(f"❌ Invalid port '{parts[2]}'. Usage: bypass <ip> <port> [knock | fragment | tunnel]")
            return True
        method = parts[3] if len(parts) > 3 else "knock"
        ok, msg = engine.bypass_firewall(target, port, method)
        print(msg)
        return True

    if action in ("av", "antivirus", "edr"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg, _ = engine.get_antivirus_status(target)
        print(msg)
        return True

    if action in ("evade", "evade_av", "kill_av"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        method = parts[2] if len(parts) > 2 else "rootkit"
        ok, msg = engine.evade_antivirus(target, method)
        print(msg)
        return True

    if action in ("social", "social_engineer", "pretext", "vishing", "bait"):
        if len(parts) < 2:
            print("Usage: social <ip> [pretext | bait | spear_phish | vishing] [employee_name]")
            return True
        target = parts[1]
        vector = parts[2] if len(parts) > 2 else (action if action in ("pretext", "vishing", "bait") else "pretext")
        emp = parts[3] if len(parts) > 3 else None
        ok, msg, _ = engine.social_engineer(target, vector=vector, employee_name=emp)
        print(msg)
        return True

    if action == "career":
        print_career(save_mgr.load_career())
        return True

    if action == "save":
        path = save_mgr.save(engine)
        if path:
            print(f"💾 Infiltration progress saved to {path}.")
        else:
            print("❌ Save failed: the file could not be replaced after 5 attempts; progress is NOT persisted.")
        return True

    if action == "load":
        loaded = save_mgr.load()
        if loaded:
            engine.__dict__.update(loaded.__dict__)
            print("📂 Loaded saved infiltration session.")
        else:
            print("No saved game found.")
        return True

    print(f"Unknown command: '{action}'. Commands: story, quests, contacts, contact, accept, world, news, probe, exploit, cve, firewall, bypass, av, evade, social, phish, craft, workshop, keylogger, daemons, myip, myfiles, ls, cat, steal, wipe_logs, move, scan, overdrive, spoof, cash_out, shop, buy, career, status, save, load, quit")
    return True


def handle_run_completion(engine: GameEngine, save_mgr: SaveManager) -> Optional[CareerProfile]:
    """Persist career stats and clean up savegame when run concludes (victory or game-over)."""
    if engine.run_settled or not (engine.state.is_victory or engine.state.is_game_over):
        return None

    profile = save_mgr.load_career()
    if engine.state.is_victory:
        safe_print("\n🎉 MISSION SUCCESSFUL: System Core infiltrated. All unbanked loot extracted.")
    elif engine.state.is_game_over:
        safe_print("\n💀 CONNECTION TERMINATED: Security ICE traced and burned your cyberdeck.")

    engine.settle_career(profile)
    if save_mgr.save_career(profile):
        save_mgr.delete_save()
    else:
        safe_print("❌ Career update failed: progress is NOT persisted.")
    print_run_summary(engine)
    return profile


def main(argv: Optional[List[str]] = None) -> int:
    setup_terminal_encoding()
    parser = argparse.ArgumentParser(prog="cyberpulse", description="Retro-cyberpunk terminal hacking simulation game")
    parser.add_argument("--seed", type=int, default=1337, help="Deterministic world seed")
    parser.add_argument("--data-dir", type=Path, default=None, help="Savegame data directory")
    parser.add_argument("--exec", dest="commands", default=None, help="Execute semicolon-separated commands and exit")
    parser.add_argument("--auto-solve", action="store_true", help="Auto-solve hacking minigames (for testing/automation)")
    parser.add_argument("--web", action="store_true", help="Launch interactive Web Cyberdeck browser interface")
    parser.add_argument("--host", default="127.0.0.1", help="Web server bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8420, help="Web server bind port (default: 8420)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch system web browser")

    args = parser.parse_args(argv)
    data_dir = args.data_dir or get_default_data_dir()

    # Web Cyberdeck execution mode
    if args.web:
        from cyberpulse.server import run_web
        run_web(
            host=args.host,
            port=args.port,
            data_dir=data_dir,
            seed=args.seed,
            open_browser=not args.no_browser,
        )
        return 0

    save_mgr = SaveManager(data_dir)
    career = save_mgr.load_career()
    engine = GameEngine(seed=args.seed, career_profile=career)

    # Batch script execution mode
    if args.commands:
        cmds = args.commands.split(";")
        for c in cmds:
            try:
                if not run_command(c, engine, save_mgr, auto_solve=args.auto_solve):
                    break
                if engine.state.is_victory or engine.state.is_game_over:
                    break
            except EOFError:
                print("👋 Input stream closed during a minigame; stopping batch execution.")
                break
        handle_run_completion(engine, save_mgr)
        return 0

    # Interactive mode
    print("Initializing CyberPulse...")
    menu_action = show_main_menu(engine, save_mgr)
    if menu_action == "quit":
        return 0
    if menu_action == "load":
        loaded = save_mgr.load()
        if loaded:
            engine.__dict__.update(loaded.__dict__)
            print("📂 Loaded saved infiltration session.")
        else:
            print("No saved infiltration found. Starting a new run.")
    print_hud(engine)
    while not engine.state.is_game_over and not engine.state.is_victory and not engine.state.is_jacked_out:
        try:
            line = input("\ncyberpulse> ")
            if not run_command(line, engine, save_mgr, auto_solve=args.auto_solve):
                break
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Disconnected.")
            break

    handle_run_completion(engine, save_mgr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
