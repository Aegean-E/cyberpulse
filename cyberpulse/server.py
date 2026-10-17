"""Zero-dependency HTTP REST backend and static file server for CyberPulse Web Cyberdeck."""

import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus, NodeType
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle
from cyberpulse.shop import BlackMarketShop
from cyberpulse.storage import SaveManager


STATIC_DIR = Path(__file__).resolve().parent / "static"


class CyberdeckSession:
    """Encapsulates the stateful game session driving the Web Cyberdeck interface."""

    def __init__(self, data_dir: Optional[Path] = None, seed: int = 1337):
        self.data_dir = data_dir or (Path.cwd() / ".cyberpulse")
        self.save_mgr = SaveManager(self.data_dir)
        self.shop = BlackMarketShop()
        self.career = self.save_mgr.load_career()
        self.engine = GameEngine(seed=seed, career_profile=self.career)
        self.active_puzzle: Optional[Any] = None
        self.active_puzzle_node_id: Optional[str] = None

    def get_full_state(self) -> Dict[str, Any]:
        """Aggregate complete runtime state for frontend rendering."""
        curr = self.engine.get_current_node()
        career = self.save_mgr.load_career()
        return {
            "seed": self.engine.seed,
            "state": self.engine.state.to_dict(),
            "deck": self.engine.deck.to_dict(),
            "current_node": curr.to_dict(),
            "nodes": {nid: n.to_dict() for nid, n in self.engine.nodes.items()},
            "career": career.to_dict(),
            "shop_items": self.shop.list_available(self.engine.deck),
        }

    def reset_game(self, seed: Optional[int] = None) -> Dict[str, Any]:
        new_seed = seed if seed is not None else (self.engine.seed + 1)
        self.career = self.save_mgr.load_career()
        self.engine = GameEngine(seed=new_seed, career_profile=self.career)
        self.active_puzzle = None
        self.active_puzzle_node_id = None
        return self.get_full_state()


class CyberdeckHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler providing REST API endpoints and static cyberdeck assets."""

    server_session: CyberdeckSession

    def log_message(self, format: str, *args: Any) -> None:
        """Route cyberdeck request logs without cluttering console."""
        sys.stdout.flush()

    def send_json_response(self, data: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/state":
            self.send_json_response(self.server_session.get_full_state())
            return

        if path == "/api/shop":
            items = self.server_session.shop.list_available(self.server_session.engine.deck)
            self.send_json_response({"items": items, "creds": self.server_session.engine.deck.cryptocreds})
            return

        if path == "/api/career":
            profile = self.server_session.save_mgr.load_career()
            self.send_json_response(profile.to_dict())
            return

        if path == "/api/puzzle":
            # Extract query params
            node_id = None
            if "?" in self.path:
                for pair in self.path.split("?")[1].split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        if k == "node_id":
                            node_id = v

            if not node_id or node_id not in self.server_session.engine.nodes:
                self.send_json_response({"ok": False, "error": f"Invalid node '{node_id}'"}, HTTPStatus.BAD_REQUEST)
                return

            can_hack, reason = self.server_session.engine.can_hack_node(node_id)
            if not can_hack:
                self.send_json_response({"ok": False, "error": reason})
                return

            node = self.server_session.engine.nodes[node_id]
            p_type = node.puzzle_type or "frequency"
            seed = self.server_session.engine.seed + self.server_session.engine.state.turns_elapsed

            puzzle_payload: Dict[str, Any] = {
                "ok": True,
                "node_id": node_id,
                "node_name": node.name,
                "security_level": node.security_level,
                "puzzle_type": p_type,
            }

            if p_type == "frequency":
                p = FrequencyPuzzle.generate(seed)
                self.server_session.active_puzzle = p
                self.server_session.active_puzzle_node_id = node_id
                puzzle_payload.update({
                    "tolerance": p.tolerance,
                    "attempts_left": p.attempts_left,
                    "min_freq": 20.0,
                    "max_freq": 99.0,
                })
            elif p_type == "buffer":
                p = BufferPuzzle.generate(seed)
                self.server_session.active_puzzle = p
                self.server_session.active_puzzle_node_id = node_id
                puzzle_payload.update({
                    "matrix": p.matrix,
                    "target_seq": p.target_seq,
                })
            elif p_type == "hash":
                p = HashCrackPuzzle.generate(seed)
                self.server_session.active_puzzle = p
                self.server_session.active_puzzle_node_id = node_id
                puzzle_payload.update({
                    "word_list": p.word_list,
                    "word_length": len(p.target_word),
                    "attempts_left": p.attempts_left,
                })

            self.send_json_response(puzzle_payload)
            return

        # Serve static assets
        self.serve_static(path)

    def serve_static(self, path: str) -> None:
        if path in ("", "/"):
            req_file = STATIC_DIR / "index.html"
        else:
            rel = path.lstrip("/")
            req_file = STATIC_DIR / rel

        if not req_file.exists() or not req_file.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, f"Asset '{path}' not found")
            return

        mime_type, _ = mimetypes.guess_type(str(req_file))
        mime_type = mime_type or "application/octet-stream"

        try:
            with open(req_file, "rb") as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to read file")

    def do_POST(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_json_response({"ok": False, "error": "Malformed JSON payload"}, HTTPStatus.BAD_REQUEST)
            return

        path = self.path.split("?")[0]

        if path == "/api/action":
            action = payload.get("action")
            engine = self.server_session.engine
            save_mgr = self.server_session.save_mgr
            shop = self.server_session.shop

            if action == "scan":
                ok, msg, _ = engine.scan_surroundings()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "move":
                target = payload.get("target")
                ok, msg = engine.move_to(target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "spoof":
                ok, msg = engine.spoof_ip()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "jackout":
                ok, msg = engine.jackout()
                if ok:
                    profile = save_mgr.load_career()
                    profile.successful_runs += 1
                    profile.current_streak += 1
                    profile.best_streak = max(profile.best_streak, profile.current_streak)
                    profile.banked_creds = engine.deck.cryptocreds
                    profile.lifetime_creds += engine.deck.cryptocreds
                    save_mgr.save_career(profile)
                    save_mgr.delete_save()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "exploit":
                name = payload.get("name")
                target = payload.get("target")
                ok, msg = engine.use_exploit(name, target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "shop_buy":
                item_id = payload.get("item_id")
                ok, msg = shop.purchase(engine.deck, item_id)
                if ok:
                    profile = save_mgr.load_career()
                    profile.purchased_upgrades.append(item_id)
                    profile.banked_creds = engine.deck.cryptocreds
                    save_mgr.save_career(profile)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "reset":
                seed = payload.get("seed")
                state = self.server_session.reset_game(seed)
                self.send_json_response({"ok": True, "message": "Neural link reset.", "state": state})
                return

            self.send_json_response({"ok": False, "error": f"Unknown action '{action}'"}, HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/puzzle/solve":
            p = self.server_session.active_puzzle
            node_id = self.server_session.active_puzzle_node_id

            if not p or not node_id:
                self.send_json_response({"ok": False, "error": "No active hacking puzzle"}, HTTPStatus.BAD_REQUEST)
                return

            engine = self.server_session.engine
            node = engine.nodes[node_id]
            guess = payload.get("guess")

            solved = False
            near_miss = False
            message = ""

            if isinstance(p, FrequencyPuzzle):
                try:
                    val = float(guess)
                    solved, message = p.tune(val)
                    near_miss = p.near_miss
                    if near_miss:
                        engine.state.near_miss_count += 1
                    if not solved and p.attempts_left <= 0:
                        engine.add_trace(node.trace_rate)
                except (ValueError, TypeError):
                    self.send_json_response({"ok": False, "error": "Invalid frequency numeric value"}, HTTPStatus.BAD_REQUEST)
                    return

            elif isinstance(p, BufferPuzzle):
                if not isinstance(guess, list):
                    self.send_json_response({"ok": False, "error": "Guess must be a sequence list"}, HTTPStatus.BAD_REQUEST)
                    return
                solved, message = p.verify_sequence(guess)
                near_miss = p.near_miss
                if near_miss:
                    engine.state.near_miss_count += 1
                if not solved:
                    engine.add_trace(node.trace_rate)

            elif isinstance(p, HashCrackPuzzle):
                solved, message = p.guess(str(guess))
                near_miss = p.near_miss
                if near_miss:
                    engine.state.near_miss_count += 1
                if not solved and p.attempts_left <= 0:
                    engine.add_trace(node.trace_rate)

            if solved:
                engine.complete_breach(node_id)
                self.server_session.active_puzzle = None
                self.server_session.active_puzzle_node_id = None

            attempts_left = getattr(p, "attempts_left", 0)
            self.send_json_response({
                "ok": True,
                "solved": solved,
                "near_miss": near_miss,
                "message": message,
                "attempts_left": attempts_left,
                "state": self.server_session.get_full_state(),
            })
            return

        self.send_json_response({"ok": False, "error": f"Unknown endpoint '{path}'"}, HTTPStatus.NOT_FOUND)


def create_server(host: str = "127.0.0.1", port: int = 8420, data_dir: Optional[Path] = None, seed: int = 1337) -> ThreadingHTTPServer:
    """Instantiate and configure the ThreadingHTTPServer for CyberPulse Web Cyberdeck."""
    session = CyberdeckSession(data_dir=data_dir, seed=seed)

    class CustomHandler(CyberdeckHTTPHandler):
        server_session = session

    server = ThreadingHTTPServer((host, port), CustomHandler)
    server.allow_reuse_address = True
    return server


def run_web(host: str = "127.0.0.1", port: int = 8420, data_dir: Optional[Path] = None, seed: int = 1337, open_browser: bool = True) -> None:
    """Launch the Web Cyberdeck server and optionally launch default system web browser."""
    import webbrowser

    server = create_server(host=host, port=port, data_dir=data_dir, seed=seed)
    url = f"http://{host}:{port}"
    print(f"\n+==========================================================================+")
    print(f"|            >> CYBERPULSE // WEB CYBERDECK ONLINE <<                     |")
    print(f"+==========================================================================+")
    print(f"[*] Visual Interface:  {url}")
    print(f"[*] World Seed:        {seed}")
    print(f"[*] Standard Library:  Pure Python 3 (Zero External Packages)")
    print(f"[*] Terminate:         Press Ctrl+C to sever neural connection")
    print(f"+==========================================================================+\n")

    if open_browser:
        webbrowser.open_new_tab(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Severing cyberdeck web connection.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_web(open_browser=True)
