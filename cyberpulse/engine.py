"""Deterministic cyberspace game engine with risk-reward loss aversion and near-miss feedback."""

import random
from typing import Any, Dict, List, Optional, Tuple

from cyberpulse.models import (
    BountyContract,
    CareerProfile,
    CyberDeck,
    GameState,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    VirtualFile,
    apply_career_profile,
)
from cyberpulse.network import generate_network
from cyberpulse.rewards import roll_breach_reward


class GameEngine:
    """Manages gameplay rules, push-your-luck risk, and victory/defeat conditions."""

    def __init__(self, seed: int = 1337, career_profile: Optional[CareerProfile] = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.nodes: Dict[str, Node] = generate_network(seed)
        self.deck: CyberDeck = CyberDeck()
        if career_profile:
            apply_career_profile(self.deck, career_profile)

        # Generate a procedural Syndicate Bounty Contract (Zeigarnik Effect)
        contract = BountyContract(
            contract_id=f"cnt_{seed % 1000:03d}",
            title="Syndicate Infiltration Order: Data Extraction",
            target_node_type=NodeType.DATA_VAULT,
            target_ip="10.0.4.15",
            target_file="/data/corporate_slush_fund.csv",
            wipe_logs_required=True,
            max_trace_limit=70,
            reward_creds=200,
        )

        self.state: GameState = GameState(
            seed=seed,
            current_node_id="node_gateway",
            trace_percent=0,
            turns_elapsed=0,
            active_contract=contract,
        )

    def get_current_node(self) -> Node:
        return self.nodes[self.state.current_node_id]

    def add_trace(self, raw_amount: int) -> None:
        """Increase system trace, mitigated by ICE dampeners. 100% triggers lockout & loss of loot."""
        # Passive ICE dampener mitigation (20% reduction per dampener level)
        if self.deck.ice_dampener_level > 0:
            reduction = min(0.60, 0.20 * self.deck.ice_dampener_level)
            amount = max(1, int(raw_amount * (1.0 - reduction)))
        else:
            amount = raw_amount

        self.state.trace_percent = min(100, self.state.trace_percent + amount)

        # High-arousal near-miss tension feedback (Clark et al.)
        if 80 <= self.state.trace_percent < 100:
            self.state.near_miss_count += 1
            self.state.message_log.append(f"⚠️ CRITICAL TRACE WARNING: {self.state.trace_percent}%! Black ICE locks tightening!")

        if self.state.trace_percent >= 100:
            self.state.is_game_over = True
            lost_loot = self.state.unbanked_creds
            self.state.unbanked_creds = 0
            self.state.looted_payloads.clear()
            self.state.message_log.append(
                f"🚨 SECURITY TRACE LOCKOUT DETECTED! Connection severed. Lost {lost_loot} unbanked Creds!"
            )

    def regenerate_cpu(self, amount: int = 1) -> int:
        """Cool down cyberdeck processing units and recover CPU cycles."""
        old = self.deck.cpu_cycles
        self.deck.cpu_cycles = min(self.deck.max_cpu, self.deck.cpu_cycles + amount)
        return self.deck.cpu_cycles - old

    def spoof_ip(self) -> Tuple[bool, str]:
        """Reduce active trace level by burning CPU cycles."""
        if self.deck.cpu_cycles < 3:
            return False, "Insufficient CPU cycles (need 3 CPU)."
        self.deck.cpu_cycles -= 3
        reduced = 25
        self.state.trace_percent = max(0, self.state.trace_percent - reduced)
        msg = f"🛡️ IP Proxy bounced. Trace reduced by {reduced}% (current: {self.state.trace_percent}%)."
        self.state.message_log.append(msg)
        return True, msg

    def scan_surroundings(self) -> Tuple[bool, str, List[Node]]:
        """Scan adjacent nodes to reveal their security level and status."""
        current = self.get_current_node()
        revealed: List[Node] = []
        for adj_id in current.connected_ids:
            node = self.nodes.get(adj_id)
            if node:
                if node.status == NodeStatus.LOCKED:
                    node.status = NodeStatus.DISCOVERED
                revealed.append(node)

        self.add_trace(5)
        self.regenerate_cpu(1)
        self.state.turns_elapsed += 1
        return True, f"Scanned {len(revealed)} adjacent network nodes. Recovered 1 CPU cycle.", revealed

    def can_move_to(self, target_id: str) -> Tuple[bool, str]:
        """Verify whether the player can transition to target node."""
        if self.state.is_game_over:
            return False, "Cannot move: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot move: terminal session jacked out."
        if target_id not in self.nodes:
            return False, f"Unknown node: {target_id}"

        current = self.get_current_node()
        if target_id not in current.connected_ids:
            return False, f"Node '{target_id}' is not directly connected to '{current.node_id}'."

        target = self.nodes[target_id]
        if target.status != NodeStatus.BREACHED:
            return False, f"Node '{target.name}' is unbreached ({target.status}). Breach security first."

        return True, "Path clear."

    def move_to(self, target_id: str) -> Tuple[bool, str]:
        """Move player's intrusion session to an adjacent breached node."""
        allowed, reason = self.can_move_to(target_id)
        if not allowed:
            return False, reason

        self.state.current_node_id = target_id
        self.state.turns_elapsed += 1
        self.regenerate_cpu(1)
        self.add_trace(2)
        node = self.get_current_node()
        msg = f"⚡ Transferred terminal session to '{node.name}'. Recovered 1 CPU cycle."
        self.state.message_log.append(msg)
        return True, msg

    def can_hack_node(self, target_id: str) -> Tuple[bool, str]:
        """Verify whether player cyberdeck meets hardware requirements to attack node."""
        if self.state.is_game_over:
            return False, "Cannot hack: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot hack: terminal session jacked out."
        if target_id not in self.nodes:
            return False, f"Unknown node '{target_id}'."

        node = self.nodes[target_id]
        if node.status == NodeStatus.BREACHED:
            return False, f"Node '{node.name}' is already breached."

        curr = self.get_current_node()
        if target_id not in curr.connected_ids and target_id != curr.node_id:
            return False, f"Node '{node.name}' is not in direct subnet range of '{curr.name}'."

        required_ram = node.security_level * 16
        if self.deck.ram_mb < required_ram:
            return False, f"INSUFFICIENT RAM: Infiltration requires {required_ram}MB buffer memory (deck has {self.deck.ram_mb}MB). Upgrade RAM in the Black Market shop."

        return True, "Requirements met."

    def dispatch_next_contract(self) -> Optional[BountyContract]:
        """Dispatch a new Syndicate Bounty Contract after previous completion (Zeigarnik Effect)."""
        targets = [NodeType.FIREWALL, NodeType.DATA_VAULT, NodeType.ICE_DEFENSE]
        next_target = self.rng.choice(targets)
        contract_num = self.state.turns_elapsed + 1
        new_contract = BountyContract(
            contract_id=f"cnt_{contract_num:03d}",
            title=f"Syndicate Priority Bounty: Sector {next_target}",
            target_node_type=next_target,
            max_trace_limit=80,
            reward_creds=175,
        )
        self.state.active_contract = new_contract
        return new_contract

    def complete_breach(self, node_id: str) -> Tuple[bool, str]:
        """Mark node as breached, evaluate variable-ratio rewards, and check contracts."""
        if node_id not in self.nodes:
            return False, f"Invalid node '{node_id}'."

        node = self.nodes[node_id]
        node.status = NodeStatus.BREACHED

        # Variable-ratio reward roll (Skinner reinforcement schedule)
        creds_awarded, reward_desc, exploit_drop = roll_breach_reward(node, self.rng)
        self.state.unbanked_creds += creds_awarded

        if exploit_drop and exploit_drop not in self.deck.exploits:
            self.deck.exploits.append(exploit_drop)

        msg = f"💥 Infiltration successful! '{node.name}' breached. {reward_desc}"

        if node.data_payload:
            self.state.looted_payloads.append(node.data_payload)
            msg += f" Acquired: [{node.data_payload}]."

        # Syndicate Contract Check (Zeigarnik Effect)
        contract = self.state.active_contract
        if contract and not contract.completed:
            if node.node_type == contract.target_node_type and self.state.trace_percent <= contract.max_trace_limit:
                contract.completed = True
                self.state.unbanked_creds += contract.reward_creds
                msg += f" 🏆 CONTRACT FULFILLED! +{contract.reward_creds} Creds!"
                self.dispatch_next_contract()

        # Unlock adjacent nodes to DISCOVERED
        for adj_id in node.connected_ids:
            adj = self.nodes.get(adj_id)
            if adj and adj.status == NodeStatus.LOCKED:
                adj.status = NodeStatus.DISCOVERED

        if node.node_type == NodeType.CENTRAL_CORE:
            self.state.is_victory = True
            msg += " 🏆 CORE INFILTRATED! MISSION ACCOMPLISHED!"

        self.state.message_log.append(msg)
        return True, msg

    def use_exploit(self, exploit_name: str, target_id: Optional[str] = None) -> Tuple[bool, str]:
        """Deploy an executable exploit chip loaded in cyberdeck firmware."""
        name = exploit_name.lower().strip()
        if name not in self.deck.exploits:
            return False, f"Exploit '{name}' is not loaded in cyberdeck firmware."

        if name == "ghost_protocol":
            reduced = min(self.state.trace_percent, 40)
            self.state.trace_percent = max(0, self.state.trace_percent - 40)
            self.deck.exploits.remove(name)
            msg = f"👻 GHOST PROTOCOL DEPLOYED! Neural signature masked. Trace dropped by {reduced}% (current: {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        if name == "logic_bomb":
            if not target_id:
                return False, "Usage: exploit logic_bomb <node_id>"
            if target_id not in self.nodes:
                return False, f"Unknown node '{target_id}'."
            target = self.nodes[target_id]
            if target.status == NodeStatus.BREACHED:
                return False, f"Node '{target.name}' is already breached."
            curr = self.get_current_node()
            if target_id not in curr.connected_ids and target_id != curr.node_id:
                return False, f"Target '{target.name}' is not in direct subnet range of '{curr.name}'."

            self.deck.exploits.remove(name)
            _, breach_msg = self.complete_breach(target_id)
            msg = f"💣 LOGIC BOMB DETONATED! Destroyed ICE defenses on '{target.name}'. {breach_msg}"
            return True, msg

        if name == "brute_miner":
            curr = self.get_current_node()
            if curr.status != NodeStatus.BREACHED:
                return False, "Brute miner can only be executed on a securely breached node."
            mined = 150
            self.state.unbanked_creds += mined
            self.add_trace(15)
            self.deck.exploits.remove(name)
            msg = f"⛏️ BRUTE MINER EXECUTED! Mined +{mined} unbanked CryptoCreds (Trace +15% -> {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        return False, f"Exploit '{name}' has no active payload handler."

    def jackout(self) -> Tuple[bool, str]:
        """Push-Your-Luck extraction: safely bank all unbanked credits and looted payloads."""
        if self.state.is_game_over:
            return False, "Cannot jack out: terminal already locked out."
        if self.state.is_jacked_out:
            return False, "Already jacked out."

        curr = self.get_current_node()
        if curr.status != NodeStatus.BREACHED:
            return False, "Can only jack out from a securely breached node."

        banked = self.state.unbanked_creds
        payload_count = len(self.state.looted_payloads)
        self.deck.cryptocreds += banked
        self.state.unbanked_creds = 0
        self.state.is_jacked_out = True

        msg = f"🚪 SAFE EXTRACTION! Banked {banked} CryptoCreds and secured {payload_count} data payloads."
        self.state.message_log.append(msg)
        return True, msg

    def find_node(self, query: str) -> Optional[Node]:
        """Lookup node by node_id, ip_address, or hostname."""
        q = query.strip().lower()
        if query in self.nodes:
            return self.nodes[query]
        for node in self.nodes.values():
            if node.node_id.lower() == q or node.ip_address.lower() == q or node.hostname.lower() == q:
                return node
        return None

    def probe_host(self, target_query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Perform network port scan (nmap-style) against a target IP, hostname, or node_id."""
        if self.state.is_game_over:
            return False, "Cannot probe: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot probe: terminal session jacked out.", None

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not reachable or does not exist.", None

        curr = self.get_current_node()
        if node.status == NodeStatus.LOCKED and node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Host {node.ip_address} ({node.hostname}) is unreachable from current subnet.", None

        if node.status == NodeStatus.LOCKED:
            node.status = NodeStatus.DISCOVERED

        self.add_trace(4)
        self.regenerate_cpu(1)
        self.state.turns_elapsed += 1

        port_data = []
        for p in node.ports:
            port_data.append({
                "port": p.port,
                "service": p.service,
                "version": p.version,
                "vulnerable": p.vulnerable,
                "breached": p.breached,
                "exploit_tool": p.exploit_tool,
            })

        report = {
            "node_id": node.node_id,
            "ip_address": node.ip_address,
            "hostname": node.hostname,
            "status": node.status.value if hasattr(node.status, "value") else str(node.status),
            "security_level": node.security_level,
            "ports": port_data,
        }

        port_lines = []
        for p in node.ports:
            status_str = "BREACHED" if p.breached else ("VULNERABLE" if p.vulnerable else "SECURE")
            port_lines.append(f"  {p.port:<5}/tcp  OPEN  {p.service:<10}  {p.version:<25}  [{status_str}]")

        summary = (
            f"Nmap scan report for {node.hostname} ({node.ip_address})\n"
            f"Host is UP (latency 12ms). Security Tier: {node.security_level} (RAM required: {node.security_level * 16}MB)\n"
            f"PORT     STATE SERVICE     VERSION                     STATUS\n"
            + "\n".join(port_lines)
        )
        self.state.message_log.append(f"Probed {node.ip_address} ({node.hostname}). Found {len(node.ports)} open port(s).")
        return True, summary, report

    def exploit_service(self, target_query: str, port_num: int) -> Tuple[bool, str]:
        """Launch an exploit payload against an open service port on target host."""
        if self.state.is_game_over:
            return False, "Cannot exploit: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot exploit: terminal session jacked out."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        if node.status == NodeStatus.BREACHED:
            return False, f"Host {node.hostname} ({node.ip_address}) is already breached (root shell active)."

        curr = self.get_current_node()
        if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Host {node.hostname} ({node.ip_address}) is not in direct subnet routing range."

        required_ram = node.security_level * 16
        if self.deck.ram_mb < required_ram:
            return False, f"INSUFFICIENT RAM: Infiltration requires {required_ram}MB buffer memory (deck has {self.deck.ram_mb}MB)."

        if self.deck.cpu_cycles < 2:
            return False, "INSUFFICIENT CPU: Launching zero-day exploit requires at least 2 CPU cycles."

        target_port = next((p for p in node.ports if p.port == port_num), None)
        if not target_port:
            self.add_trace(8)
            return False, f"Port {port_num}/tcp is closed or filtered on {node.ip_address}."

        if not target_port.vulnerable:
            self.add_trace(12)
            return False, f"Exploit failed: Service '{target_port.service}' on port {port_num} has no known vulnerabilities. IDS alert triggered!"

        self.deck.cpu_cycles -= 2
        target_port.breached = True
        self.add_trace(node.trace_rate)
        _, breach_msg = self.complete_breach(node.node_id)
        msg = f"💥 EXPLOIT SUCCESSFUL! Injected payload via port {port_num} ({target_port.service}). Root access acquired on {node.hostname} ({node.ip_address})!\n{breach_msg}"
        return True, msg

    def list_files(self, target_query: Optional[str] = None) -> Tuple[bool, str, List[VirtualFile]]:
        """List files (ls) on target host's virtual filesystem (requires host to be breached)."""
        if target_query:
            node = self.find_node(target_query)
        else:
            node = self.get_current_node()

        if not node:
            return False, f"Host '{target_query}' not found.", []

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} ({node.ip_address}) is not breached. Exploit open ports first.", []

        files = node.filesystem
        lines = [f"Directory listing for {node.hostname} ({node.ip_address}):", "PERM        SIZE     VALUE    TARGET  PATH"]
        for f in files:
            target_mark = "★ YES" if f.is_target_data else "  no "
            val_str = f"{f.value_creds}cr" if f.value_creds > 0 else "---"
            lines.append(f"-rw-r--r--  {f.size_kb:>4}KB  {val_str:>7}  {target_mark:>6}  {f.path}")

        return True, "\n".join(lines), files

    def read_file(self, target_query: str, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """Read file contents (cat) on breached host."""
        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not found.", None

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} is not breached.", None

        fp = file_path.strip()
        vfile = next((f for f in node.filesystem if f.path == fp or f.path.endswith("/" + fp) or f.path.split("/")[-1] == fp), None)
        if not vfile:
            return False, f"File '{file_path}' not found on {node.hostname}.", None

        return True, f"=== [cat {vfile.path}] ===\n{vfile.content}\n=== [EOF] ===", vfile.content

    def download_file(self, target_query: str, file_path: str) -> Tuple[bool, str, Optional[VirtualFile]]:
        """Download / steal data file from breached host (yields unbanked credits and fulfills bounties)."""
        if self.state.is_game_over:
            return False, "Cannot download: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot download: terminal session jacked out.", None

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not found.", None

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} is not breached.", None

        fp = file_path.strip()
        vfile = next((f for f in node.filesystem if f.path == fp or f.path.endswith("/" + fp) or f.path.split("/")[-1] == fp), None)
        if not vfile:
            return False, f"File '{file_path}' not found on {node.hostname}.", None

        self.add_trace(8)
        self.state.turns_elapsed += 1

        already_looted = vfile.path in self.state.looted_payloads
        if not already_looted:
            self.state.looted_payloads.append(vfile.path)
            self.state.unbanked_creds += vfile.value_creds

        msg = f"📥 EXFILTRATION COMPLETE: Stole '{vfile.path}' ({vfile.size_kb}KB) from {node.hostname}."
        if vfile.value_creds > 0 and not already_looted:
            msg += f" Data sold on darknet for +{vfile.value_creds} unbanked Creds!"

        contract = self.state.active_contract
        if contract and not contract.completed:
            if (contract.target_file and (contract.target_file == vfile.path or vfile.is_target_data)) or \
               (contract.target_ip and contract.target_ip == node.ip_address):
                if not contract.wipe_logs_required or node.logs_cleared:
                    contract.completed = True
                    self.state.unbanked_creds += contract.reward_creds
                    msg += f"\n🏆 SYNDICATE CONTRACT COMPLETED! Reward: +{contract.reward_creds} Creds!"
                    self.dispatch_next_contract()
                else:
                    msg += f"\n⚠️ BOUNTY OBJECTIVE: Target data stolen, but contract requires logs to be wiped! Run: wipe_logs {node.ip_address}"

        self.state.message_log.append(msg)
        return True, msg, vfile

    def wipe_logs(self, target_query: str) -> Tuple[bool, str]:
        """Clear access logs (wipe_logs) on target host to reduce active trace by 20% and fulfill clean escape clauses."""
        if self.state.is_game_over:
            return False, "Cannot wipe logs: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot wipe logs: terminal session jacked out."

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not found."

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} is not breached."

        node.logs_cleared = True
        trace_drop = min(self.state.trace_percent, 20)
        self.state.trace_percent = max(0, self.state.trace_percent - 20)

        msg = f"🧹 LOGS SANITIZED: Erased intruder access timestamps on {node.hostname} ({node.ip_address}). Trace dropped by {trace_drop}% (current: {self.state.trace_percent}%)."

        contract = self.state.active_contract
        if contract and not contract.completed and contract.wipe_logs_required:
            has_looted_target = any(
                (contract.target_file and contract.target_file in p) or
                (contract.target_ip and contract.target_ip == node.ip_address)
                for p in self.state.looted_payloads
            )
            if has_looted_target:
                contract.completed = True
                self.state.unbanked_creds += contract.reward_creds
                msg += f"\n🏆 SYNDICATE CONTRACT COMPLETED! Clean exit confirmed. +{contract.reward_creds} Creds!"
                self.dispatch_next_contract()

        self.state.message_log.append(msg)
        return True, msg

