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


def setup_terminal_encoding() -> None:
    """Ensure stdout and stderr handle utf-8 safely across all Windows code pages."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


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
    print("--------------------------------------------------------------------------")
    print("Discovered Subnet Nodes:")
    for cid in curr.connected_ids:
        adj = engine.nodes.get(cid)
        if adj:
            icon = "[BREACHED]" if adj.status == NodeStatus.BREACHED else ("[DISCOVERED]" if adj.status == NodeStatus.DISCOVERED else "[LOCKED]")
            print(f"   * {adj.ip_address:<15} | {adj.hostname:<24} | {icon} (Sec: {adj.security_level})")
    print("+==========================================================================+")


def print_shop(shop: BlackMarketShop, deck: CyberDeck) -> None:
    items = shop.list_available(deck)
    print("\n+==========================================================================+")
    print("|                   >> BLACK MARKET CYBER-VENDOR <<                        |")
    print("+==========================================================================+")
    print(f"[*] Available Funds: {deck.cryptocreds} CryptoCreds\n")
    for it in items:
        status = f"Lvl {it['current_level']}/{it['max_level']}" if it['max_level'] > 1 else ("OWNED" if it['current_level'] > 0 else "AVAILABLE")
        buy_tag = "[AFFORDABLE]" if it['can_buy'] else "[LOCKED]"
        print(f"   * {it['item_id']:<18} | Cost: {it['cost']:<4} Creds | {status:<12} | {buy_tag}")
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


def execute_hack_puzzle(engine: GameEngine, target_id: str, auto_solve: bool = False) -> bool:
    can_hack, reason = engine.can_hack_node(target_id)
    if not can_hack:
        print(f"⚠️ {reason}")
        return False

    node = engine.nodes[target_id]
    print(f"\n⚡ INITIATING CYBER-ATTACK ON: {node.name} (Sec Level: {node.security_level})")

    # If auto_solve is True (used in batch/tests)
    if auto_solve:
        _, msg = engine.complete_breach(target_id)
        print(msg)
        return True

    # Puzzle execution based on node puzzle_type
    p_type = node.puzzle_type or "frequency"
    if p_type == "frequency":
        puzzle = FrequencyPuzzle.generate(engine.seed + engine.state.turns_elapsed)
        print(f"📡 TUNING PROTOCOL: Target frequency between 20.0 and 99.0 GHz (tolerance ±{puzzle.tolerance} GHz).")
        while puzzle.attempts_left > 0:
            val_str = input(f"Enter target GHz [{puzzle.attempts_left} tries left]: ").strip()
            try:
                guess = float(val_str)
                ok, msg = puzzle.tune(guess)
                print(msg)
                if puzzle.near_miss:
                    engine.state.near_miss_count += 1
                if ok:
                    engine.complete_breach(target_id)
                    return True
            except ValueError:
                print("Invalid frequency value.")
        engine.add_trace(node.trace_rate)
        return False

    elif p_type == "buffer":
        puzzle = BufferPuzzle.generate(engine.seed + engine.state.turns_elapsed)
        print("💾 BUFFER OVERFLOW PROTOCOL: Inject target hex sequence:")
        print(f"   Target: {puzzle.target_seq}")
        seq_str = input("Enter hex codes separated by space: ").strip().upper()
        player_seq = seq_str.split()
        ok, msg = puzzle.verify_sequence(player_seq)
        print(msg)
        if puzzle.near_miss:
            engine.state.near_miss_count += 1
        if ok:
            engine.complete_breach(target_id)
            return True
        engine.add_trace(node.trace_rate)
        return False

    elif p_type == "hash":
        puzzle = HashCrackPuzzle.generate(engine.seed + engine.state.turns_elapsed)
        print(f"🔑 HASH CRACK PROTOCOL: Potential keys: {', '.join(puzzle.word_list)}")
        while puzzle.attempts_left > 0:
            guess = input(f"Guess keyword [{puzzle.attempts_left} tries left]: ").strip()
            ok, msg = puzzle.guess(guess)
            print(msg)
            if puzzle.near_miss:
                engine.state.near_miss_count += 1
            if ok:
                engine.complete_breach(target_id)
                return True
        engine.add_trace(node.trace_rate)
        return False

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
            ok, msg = engine.exploit_service(parts[1], int(parts[2]))
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

    if action in ("jackout", "cash_out"):
        ok, msg = engine.jackout()
        print(msg)
        if ok:
            # Update career meta-progression
            profile = save_mgr.load_career()
            profile.successful_runs += 1
            profile.current_streak += 1
            profile.best_streak = max(profile.best_streak, profile.current_streak)
            profile.banked_creds = engine.deck.cryptocreds
            profile.lifetime_creds += engine.deck.cryptocreds
            save_mgr.save_career(profile)
            save_mgr.delete_save()
            print("📂 Career progression profile updated.")
        return True

    if action == "shop":
        print_shop(shop, engine.deck)
        return True

    if action == "buy":
        if len(parts) < 2:
            print("Usage: buy <item_id> (e.g. `buy overclock_cpu`)")
            return True
        ok, msg = shop.purchase(engine.deck, parts[1])
        print(msg)
        if ok:
            profile = save_mgr.load_career()
            profile.purchased_upgrades.append(parts[1])
            profile.banked_creds = engine.deck.cryptocreds
            save_mgr.save_career(profile)
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
        return True

    if action in ("keylogger", "deploy_keylogger"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg = engine.deploy_daemon(target, "keylogger")
        print(msg)
        return True

    if action in ("daemons", "ps"):
        print_daemons(engine)
        return True

    if action == "career":
        print_career(save_mgr.load_career())
        return True

    if action == "save":
        path = save_mgr.save(engine)
        print(f"💾 Infiltration progress saved to {path}.")
        return True

    if action == "load":
        loaded = save_mgr.load()
        if loaded:
            engine.__dict__.update(loaded.__dict__)
            print("📂 Loaded saved infiltration session.")
        else:
            print("No saved game found.")
        return True

    print(f"Unknown command: '{action}'. Commands: probe, exploit, phish, craft, workshop, keylogger, daemons, myip, myfiles, ls, cat, steal, wipe_logs, move, scan, spoof, cash_out, shop, buy, career, status, save, load, quit")
    return True


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
            if not run_command(c, engine, save_mgr, auto_solve=args.auto_solve):
                break
        return 0

    # Interactive mode
    print("Initializing CyberPulse...")
    print_hud(engine)
    while not engine.state.is_game_over and not engine.state.is_victory and not engine.state.is_jacked_out:
        try:
            line = input("\ncyberpulse> ")
            if not run_command(line, engine, save_mgr, auto_solve=args.auto_solve):
                break
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Disconnected.")
            break

    profile = save_mgr.load_career()
    if engine.state.is_victory:
        print("\n🎉 MISSION SUCCESSFUL: System Core infiltrated. You escaped without detection.")
        profile.successful_runs += 1
        profile.current_streak += 1
        profile.best_streak = max(profile.best_streak, profile.current_streak)
        profile.banked_creds = engine.deck.cryptocreds
        profile.lifetime_creds += engine.deck.cryptocreds
        save_mgr.save_career(profile)
        save_mgr.delete_save()
    elif engine.state.is_game_over:
        print("\n💀 CONNECTION TERMINATED: Security ICE traced and burned your cyberdeck.")
        profile.failed_runs += 1
        profile.current_streak = 0
        save_mgr.save_career(profile)
        save_mgr.delete_save()

    return 0


if __name__ == "__main__":
    sys.exit(main())
