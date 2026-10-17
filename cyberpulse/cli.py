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
    contract_str = (
        f"{contract.title} (+{contract.reward_creds} Creds) [COMPLETED]"
        if contract and contract.completed
        else (f"{contract.title} (+{contract.reward_creds} Creds) [ACTIVE]" if contract else "None")
    )

    print("\n+==========================================================================+")
    print("|          >> CYBERPULSE // NEURAL INTRUSION HARNESS v0.2.0 <<             |")
    print("+==========================================================================+")
    print(f"[*] Location:   {curr.name} [{curr.node_id}] ({curr.node_type})")
    print(f"[*] Trace:      {trace_bar} | Turns: {engine.state.turns_elapsed}")
    print(f"[*] Deck:       CPU: {engine.deck.cpu_cycles}/{engine.deck.max_cpu} | RAM: {engine.deck.ram_mb}MB | Creds: {engine.deck.cryptocreds}{unbanked_str}")
    print(f"[*] Upgrades:   ICE Dampener: Lvl {engine.deck.ice_dampener_level} | Overclock: Lvl {engine.deck.overclock_level}")
    exploits_str = ', '.join(engine.deck.exploits) if engine.deck.exploits else "None"
    print(f"[*] Exploits:   {exploits_str}")
    print(f"[*] Contract:   {contract_str}")
    if engine.state.near_miss_count > 0:
        print(f"[*] Adrenaline: [NEAR-MISS ENCOUNTERS: {engine.state.near_miss_count}]")
    print("--------------------------------------------------------------------------")
    print("Network Connections:")
    for cid in curr.connected_ids:
        adj = engine.nodes.get(cid)
        if adj:
            icon = "[BREACHED]" if adj.status == NodeStatus.BREACHED else ("[DISCOVERED]" if adj.status == NodeStatus.DISCOVERED else "[LOCKED]")
            print(f"   * {adj.node_id:<20} | {adj.name:<32} | {icon} (Sec: {adj.security_level})")
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

    if action == "move":
        if len(parts) < 2:
            print("Usage: move <node_id>")
            return True
        ok, msg = engine.move_to(parts[1])
        print(msg)
        return True

    if action in ("hack", "breach"):
        if len(parts) < 2:
            print("Usage: hack <node_id>")
            return True
        execute_hack_puzzle(engine, parts[1], auto_solve=auto_solve)
        return True

    if action in ("exploit", "use"):
        if len(parts) < 2:
            exploits_list = ', '.join(engine.deck.exploits) if engine.deck.exploits else 'None'
            print(f"Usage: exploit <name> [target] (Loaded exploits: {exploits_list})")
            return True
        exploit_name = parts[1]
        target = parts[2] if len(parts) > 2 else None
        ok, msg = engine.use_exploit(exploit_name, target)
        print(msg)
        return True

    if action == "spoof":
        ok, msg = engine.spoof_ip()
        print(msg)
        return True

    if action == "jackout":
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

    print(f"Unknown command: '{action}'. Commands: scan, move, hack, exploit, spoof, jackout, shop, buy, career, status, save, load, quit")
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
