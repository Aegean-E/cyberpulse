"""Interactive and scriptable retro-cyberpunk terminal CLI for CyberPulse."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus, NodeType
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle
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

    print("\n+==========================================================================+")
    print("|          >> CYBERPULSE // NEURAL INTRUSION HARNESS v0.1.0 <<             |")
    print("+==========================================================================+")
    print(f"[*] Location:   {curr.name} [{curr.node_id}] ({curr.node_type})")
    print(f"[*] Trace:      {trace_bar} | Turns: {engine.state.turns_elapsed}")
    print(f"[*] Deck:       CPU: {engine.deck.cpu_cycles}/{engine.deck.max_cpu} | RAM: {engine.deck.ram_mb}MB | Creds: {engine.deck.cryptocreds}")
    print("--------------------------------------------------------------------------")
    print("Network Connections:")
    for cid in curr.connected_ids:
        adj = engine.nodes.get(cid)
        if adj:
            icon = "[BREACHED]" if adj.status == NodeStatus.BREACHED else ("[DISCOVERED]" if adj.status == NodeStatus.DISCOVERED else "[LOCKED]")
            print(f"   * {adj.node_id:<20} | {adj.name:<32} | {icon} (Sec: {adj.security_level})")
    print("+==========================================================================+")


def execute_hack_puzzle(engine: GameEngine, target_id: str, auto_solve: bool = False) -> bool:
    node = engine.nodes.get(target_id)
    if not node:
        print(f"Error: Unknown node '{target_id}'.")
        return False
    if node.status == NodeStatus.BREACHED:
        print(f"Node '{node.name}' is already breached!")
        return True

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

    if action == "spoof":
        ok, msg = engine.spoof_ip()
        print(msg)
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

    print(f"Unknown command: '{action}'. Commands: scan, move, hack, spoof, status, save, load, quit")
    return True


def main(argv: Optional[List[str]] = None) -> int:
    setup_terminal_encoding()
    parser = argparse.ArgumentParser(prog="cyberpulse", description="Retro-cyberpunk terminal hacking simulation game")
    parser.add_argument("--seed", type=int, default=1337, help="Deterministic world seed")
    parser.add_argument("--data-dir", type=Path, default=None, help="Savegame data directory")
    parser.add_argument("--exec", dest="commands", default=None, help="Execute semicolon-separated commands and exit")
    parser.add_argument("--auto-solve", action="store_true", help="Auto-solve hacking minigames (for testing/automation)")

    args = parser.parse_args(argv)
    data_dir = args.data_dir or get_default_data_dir()
    save_mgr = SaveManager(data_dir)
    engine = GameEngine(seed=args.seed)

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
    while not engine.state.is_game_over and not engine.state.is_victory:
        try:
            line = input("\ncyberpulse> ")
            if not run_command(line, engine, save_mgr, auto_solve=args.auto_solve):
                break
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Disconnected.")
            break

    if engine.state.is_victory:
        print("\n🎉 MISSION SUCCESSFUL: System Core infiltrated. You escaped without detection.")
    elif engine.state.is_game_over:
        print("\n💀 CONNECTION TERMINATED: Security ICE traced and burned your cyberdeck.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
