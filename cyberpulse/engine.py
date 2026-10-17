"""Deterministic cyberspace game engine with risk-reward loss aversion and near-miss feedback."""

import random
from typing import Any, Dict, List, Optional, Tuple

from cyberpulse.models import (
    BountyContract,
    CareerProfile,
    CyberDeck,
    EmployeeProfile,
    ExploitPayload,
    FirewallPolicy,
    FirewallRule,
    GameState,
    HostAntivirus,
    HostFirewall,
    MalwareDaemon,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    SecurityAwarenessLevel,
    SocialVectorType,
    VirtualFile,
    VirusCraftRecipe,
    apply_career_profile,
)
from cyberpulse.network import generate_network
from cyberpulse.rewards import roll_breach_reward

KNOWN_CVES: Dict[str, ExploitPayload] = {
    "cve-2024-38812": ExploitPayload(
        cve_id="CVE-2024-38812",
        name="Heap Overflow Zero-Day",
        target_service="http",
        required_ram_mb=32,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=8,
        description="Remote code execution heap corruption in network packet parser.",
    ),
    "cve-2023-22515": ExploitPayload(
        cve_id="CVE-2023-22515",
        name="Broken Auth Privilege Escalation",
        target_service="http",
        required_ram_mb=16,
        cpu_cost=2,
        stealth_rating=5,
        damage_trace=5,
        description="Zero-day unauthorized administrator account creation flaw.",
    ),
    "cve-2024-21413": ExploitPayload(
        cve_id="CVE-2024-21413",
        name="Outlook Moniker Link Bypass",
        target_service="smtp",
        required_ram_mb=16,
        cpu_cost=1,
        stealth_rating=3,
        damage_trace=10,
        description="Remote credential theft and code execution via moniker parsing.",
    ),
    "cve-2024-6387": ExploitPayload(
        cve_id="CVE-2024-6387",
        name="RegreSSHion Race Condition",
        target_service="ssh",
        required_ram_mb=48,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=12,
        description="Signal handler race condition leading to unauthenticated root RCE.",
    ),
    "cve-2023-38606": ExploitPayload(
        cve_id="CVE-2023-38606",
        name="Blind SQL Injection",
        target_service="mysql",
        required_ram_mb=32,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=8,
        description="Blind SQL injection bypassing WAF filters to extract root hashes.",
    ),
    "cve-2011-2523": ExploitPayload(
        cve_id="CVE-2011-2523",
        name="vsftpd Backdoor Payload",
        target_service="ftp",
        required_ram_mb=16,
        cpu_cost=1,
        stealth_rating=2,
        damage_trace=14,
        description="Legacy backdoor payload triggering root shell on port 6200.",
    ),
}

CRAFTING_RECIPES: Dict[str, VirusCraftRecipe] = {
    "keylogger_daemon": VirusCraftRecipe(
        name="keylogger_daemon",
        vector="stealth",
        payload="keylogger",
        cost_creds=100,
        cpu_cost=2,
        description="Persistent background listener chip. Harvests credentials and passive credits from breached hosts.",
    ),
    "worm_replicator": VirusCraftRecipe(
        name="worm_replicator",
        vector="worm",
        payload="logic_overload",
        cost_creds=150,
        cpu_cost=3,
        description="Self-propagating payload. Breaches target node and forces disclosure of all adjacent subnet nodes.",
    ),
    "data_siphon": VirusCraftRecipe(
        name="data_siphon",
        vector="trojan",
        payload="credit_siphon",
        cost_creds=120,
        cpu_cost=2,
        description="Automated exfiltration script. Immediately drains 150 unbanked credits from target host.",
    ),
    "trace_cleaner": VirusCraftRecipe(
        name="trace_cleaner",
        vector="stealth",
        payload="trace_wipe",
        cost_creds=80,
        cpu_cost=2,
        description="Anti-forensic daemon. Scrub active trace by 35% on execution.",
    ),
}


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
        if self.state.is_game_over:
            return False, "Cannot spoof: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot spoof: terminal session jacked out."
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
        if self.state.is_game_over:
            return False, "Cannot scan: system lockout in effect.", []
        if self.state.is_jacked_out:
            return False, "Cannot scan: terminal session jacked out.", []
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
        self.tick_daemons()
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
        self.tick_daemons()
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
        if self.state.is_game_over:
            return False, "Cannot use exploit: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot use exploit: terminal session jacked out."

        name = str(exploit_name or "").lower().strip()
        if not name:
            return False, "No exploit name specified."
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

        if name == "trace_cleaner":
            reduced = min(self.state.trace_percent, 35)
            self.state.trace_percent = max(0, self.state.trace_percent - 35)
            self.deck.exploits.remove(name)
            msg = f"🧹 TRACE CLEANER EXECUTED! Scrubbed active forensic footprint by {reduced}% (current: {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        if name == "data_siphon":
            target = target_id or self.state.current_node_id
            node = self.find_node(target)
            if not node:
                return False, f"Target '{target}' not found."
            if node.status != NodeStatus.BREACHED:
                return False, f"Data siphon requires host {node.hostname} to be securely breached."
            siphoned = 150
            self.state.unbanked_creds += siphoned
            self.deck.exploits.remove(name)
            self.add_trace(10)
            msg = f"⚡ DATA SIPHON EXECUTED! Drained +{siphoned} unbanked Creds from {node.hostname} (Trace +10% -> {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        if name == "worm_replicator":
            if not target_id:
                return False, "Usage: exploit worm_replicator <target_ip | node_id>"
            node = self.find_node(target_id)
            if not node:
                return False, f"Target '{target_id}' not found."
            curr = self.get_current_node()
            if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
                return False, f"Target '{node.hostname}' is not in direct subnet range."
            self.deck.exploits.remove(name)
            _, breach_msg = self.complete_breach(node.node_id)
            for adj_id in node.connected_ids:
                adj = self.nodes.get(adj_id)
                if adj and adj.status == NodeStatus.LOCKED:
                    adj.status = NodeStatus.DISCOVERED
            msg = f"🐛 WORM REPLICATOR PROPAGATED! Infiltrated {node.hostname} and forced network disclosure of connected subnets!\n{breach_msg}"
            self.state.message_log.append(msg)
            return True, msg

        if name == "keylogger_daemon":
            target = target_id or self.state.current_node_id
            ok, d_msg = self.deploy_daemon(target, "keylogger")
            if ok:
                self.deck.exploits.remove(name)
            return ok, d_msg

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

    def find_node(self, query: Optional[str]) -> Optional[Node]:
        """Lookup node by node_id, ip_address, or hostname."""
        if not query:
            return None
        q = str(query).strip().lower()
        if str(query) in self.nodes:
            return self.nodes[str(query)]
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

    def exploit_service(self, target_query: str, port_num: int, cve_id: Optional[str] = None) -> Tuple[bool, str]:
        """Launch an exploit payload (generic zero-day or targeted CVE) against an open service port on target host."""
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

        target_port = next((p for p in node.ports if p.port == port_num), None)
        if not target_port:
            self.add_trace(8)
            return False, f"Port {port_num}/tcp is closed or filtered on {node.ip_address}."

        # 1. Network Firewall Ingress Filter Check
        if node.firewall and node.firewall.is_port_blocked(port_num):
            self.add_trace(10)
            return False, f"🛡️ FIREWALL BLOCKED: Port {port_num}/tcp on {node.hostname} is actively blocked by {node.firewall.firewall_type}. Bypass the firewall (bypass {node.ip_address} {port_num}) or use social engineering."

        # 2. Match Exploit Payload / CVE
        selected_cve: Optional[ExploitPayload] = None
        if cve_id:
            cve_key = cve_id.lower().strip()
            selected_cve = KNOWN_CVES.get(cve_key)
            if not selected_cve:
                avail = ", ".join(k.upper() for k in KNOWN_CVES.keys())
                return False, f"Unknown exploit payload '{cve_id}'. Available CVEs: {avail}"

            if selected_cve.target_service != "any" and selected_cve.target_service != target_port.service:
                return False, f"Exploit mismatch: {selected_cve.cve_id} targets '{selected_cve.target_service}', but port {port_num} runs '{target_port.service}'."

            required_ram = selected_cve.required_ram_mb
            cpu_needed = selected_cve.cpu_cost
            trace_add = selected_cve.damage_trace
            exploit_label = f"{selected_cve.cve_id} ({selected_cve.name})"
        else:
            required_ram = node.security_level * 16
            cpu_needed = 2
            trace_add = node.trace_rate
            exploit_label = f"Zero-Day Buffer Exploit on {target_port.service}"

        if self.deck.ram_mb < required_ram:
            return False, f"INSUFFICIENT RAM: Infiltration requires {required_ram}MB buffer memory (deck has {self.deck.ram_mb}MB)."

        if self.deck.cpu_cycles < cpu_needed:
            return False, f"INSUFFICIENT CPU: Launching exploit requires at least {cpu_needed} CPU cycles (deck has {self.deck.cpu_cycles})."

        if not target_port.vulnerable:
            self.add_trace(12)
            return False, f"Exploit failed: Service '{target_port.service}' on port {port_num} has no known vulnerabilities. IDS alert triggered!"

        # 3. Host Antivirus Heuristics Check
        av_notice = ""
        if node.antivirus and node.antivirus.enabled and not node.antivirus.evaded:
            stealth = selected_cve.stealth_rating if selected_cve else 3
            if stealth < 3:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + 25)
                self.add_trace(8)
                av_notice = f"\n⚠️ [ANTIVIRUS WARNING] {node.antivirus.name} detected noisy exploit signature! Alert level spiked to {node.antivirus.alert_level}%."
            else:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + 5)

        self.deck.cpu_cycles -= cpu_needed
        target_port.breached = True
        self.add_trace(trace_add)
        self.state.turns_elapsed += 1
        self.tick_daemons()
        _, breach_msg = self.complete_breach(node.node_id)
        msg = f"💥 EXPLOIT SUCCESSFUL! Injected {exploit_label} via port {port_num} ({target_port.service}). Root access acquired on {node.hostname} ({node.ip_address})!\n{breach_msg}{av_notice}"
        return True, msg

    def list_files(self, target_query: Optional[str] = None) -> Tuple[bool, str, List[VirtualFile]]:
        """List files (ls) on target host's virtual filesystem (requires host to be breached)."""
        if self.state.is_game_over:
            return False, "Cannot list files: system lockout in effect.", []
        if self.state.is_jacked_out:
            return False, "Cannot list files: terminal session jacked out.", []

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
        if self.state.is_game_over:
            return False, "Cannot read file: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot read file: terminal session jacked out.", None

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not found.", None

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} is not breached.", None

        fp = str(file_path or "").strip()
        if not fp:
            return False, "File path cannot be empty.", None

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

        fp = str(file_path or "").strip()
        if not fp:
            return False, "File path cannot be empty.", None

        vfile = next((f for f in node.filesystem if f.path == fp or f.path.endswith("/" + fp) or f.path.split("/")[-1] == fp), None)
        if not vfile:
            return False, f"File '{file_path}' not found on {node.hostname}.", None

        self.add_trace(8)
        self.state.turns_elapsed += 1
        self.tick_daemons()

        already_looted = vfile.path in self.state.looted_payloads
        if not already_looted:
            self.state.looted_payloads.append(vfile.path)
            self.state.unbanked_creds += vfile.value_creds

        # Archive copy into player's local deck filesystem under /loot/<filename>
        loot_name = vfile.path.split("/")[-1]
        loot_path = f"/loot/{loot_name}"
        if not any(f.path == loot_path for f in self.deck.local_filesystem):
            self.deck.local_filesystem.append(
                VirtualFile(path=loot_path, size_kb=vfile.size_kb, content=vfile.content, value_creds=vfile.value_creds)
            )

        msg = f"📥 EXFILTRATION COMPLETE: Stole '{vfile.path}' ({vfile.size_kb}KB) from {node.hostname}."
        if vfile.value_creds > 0 and not already_looted:
            msg += f" Data sold on darknet for +{vfile.value_creds} unbanked Creds! Archived to local rig ({loot_path})."

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

    def tick_daemons(self) -> List[str]:
        """Process active background malware daemons (e.g. keyloggers) and host antivirus sweeps."""
        messages = []
        for daemon in list(self.deck.active_daemons):
            daemon.turns_active += 1
            node = self.nodes.get(daemon.target_node_id)
            if not node or node.status != NodeStatus.BREACHED:
                continue

            # Check Antivirus heuristic sweep
            if node.antivirus and node.antivirus.enabled and not node.antivirus.evaded:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + (node.antivirus.heuristic_sensitivity * 4))
                if node.antivirus.alert_level >= 50:
                    quarantine_roll = self.rng.random()
                    if quarantine_roll <= (node.antivirus.alert_level / 100.0):
                        if daemon in self.deck.active_daemons:
                            self.deck.active_daemons.remove(daemon)
                        self.add_trace(15)
                        node.antivirus.quarantine_log.append(f"Quarantined {daemon.daemon_type} on turn {self.state.turns_elapsed}")
                        q_msg = f"🛡️ [ANTIVIRUS QUARANTINE] {node.antivirus.name} on {node.hostname} detected and terminated background {daemon.daemon_type}! Alert Level: {node.antivirus.alert_level}%. Active Trace +15%!"
                        messages.append(q_msg)
                        self.state.message_log.append(q_msg)
                        continue

            self.state.unbanked_creds += daemon.yield_per_turn
            self.add_trace(daemon.detection_risk)
            msg = f"📡 [{daemon.daemon_type.upper()}] Harvested +{daemon.yield_per_turn} unbanked Creds from {node.hostname} (Trace +{daemon.detection_risk}%)."
            messages.append(msg)
            self.state.message_log.append(msg)
        return messages

    def deploy_daemon(self, target_query: str, daemon_type: str = "keylogger") -> Tuple[bool, str]:
        """Deploy an in-game background malware listener daemon onto a breached host."""
        if self.state.is_game_over:
            return False, "Cannot deploy daemon: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot deploy daemon: terminal session jacked out."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        if node.status != NodeStatus.BREACHED:
            return False, f"Cannot deploy daemon: Host {node.hostname} ({node.ip_address}) is not breached."

        if any(d.target_node_id == node.node_id and d.daemon_type == daemon_type for d in self.deck.active_daemons):
            return False, f"Daemon '{daemon_type}' is already running on {node.hostname}."

        if self.deck.cpu_cycles < 2:
            return False, "Insufficient CPU cycles (need 2 CPU to initialize daemon listener)."

        self.deck.cpu_cycles -= 2
        daemon_id = f"dmn_{len(self.deck.active_daemons) + 1:03d}"
        daemon = MalwareDaemon(
            daemon_id=daemon_id,
            daemon_type=daemon_type,
            target_node_id=node.node_id,
            target_ip=node.ip_address,
            yield_per_turn=25,
            detection_risk=3,
        )
        self.deck.active_daemons.append(daemon)
        msg = f"👾 DAEMON INITIALIZED: [{daemon_type.upper()}] active on {node.hostname} ({node.ip_address}). Passively harvesting +25 unbanked Creds/turn."
        self.state.message_log.append(msg)
        return True, msg

    def list_local_files(self) -> Tuple[bool, str, List[VirtualFile]]:
        """List files (ls) stored on player's local cyberdeck rig (localhost)."""
        if self.state.is_game_over:
            return False, "Cannot list files: system lockout in effect.", []
        if self.state.is_jacked_out:
            return False, "Cannot list files: terminal session jacked out.", []

        lines = [
            f"Local Rig Filesystem ({self.deck.local_hostname} [{self.deck.local_ip}]):",
            "PERM        SIZE     VALUE    PATH"
        ]
        for f in self.deck.local_filesystem:
            val_str = f"{f.value_creds}cr" if f.value_creds > 0 else "---"
            lines.append(f"-rw-r--r--  {f.size_kb:>4}KB  {val_str:>7}  {f.path}")
        return True, "\n".join(lines), self.deck.local_filesystem

    def read_local_file(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """Read content (cat) of a file on player's local cyberdeck rig."""
        if self.state.is_game_over:
            return False, "Cannot read file: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot read file: terminal session jacked out.", None

        fp = str(file_path or "").strip()
        if not fp:
            return False, "File path cannot be empty.", None

        vfile = next((f for f in self.deck.local_filesystem if f.path == fp or f.path.endswith("/" + fp) or f.path.split("/")[-1] == fp), None)
        if not vfile:
            return False, f"File '{file_path}' not found on local deck.", None
        return True, f"=== [cat {vfile.path}] ===\n{vfile.content}\n=== [EOF] ===", vfile.content

    def social_engineer(self, target_query: str, vector: str = "spear_phish", employee_name: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Launch an interactive social engineering attack (pretext, bait, spear_phish, vishing) against target employees."""
        vector_key = vector.lower().strip()
        valid_vectors = [SocialVectorType.PRETEXT, SocialVectorType.BAIT, SocialVectorType.SPEAR_PHISH, SocialVectorType.VISHING]
        if vector_key not in valid_vectors:
            return False, f"Invalid vector '{vector}'. Valid options: pretext, bait, spear_phish, vishing.", {}

        if self.state.is_game_over:
            return False, "Cannot engage: system lockout in effect.", {}
        if self.state.is_jacked_out:
            return False, "Cannot engage: terminal session jacked out.", {}

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found.", {}

        if node.status == NodeStatus.BREACHED:
            return False, f"Host {node.hostname} ({node.ip_address}) is already compromised.", {}

        curr = self.get_current_node()
        if node.status == NodeStatus.LOCKED and node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Target {node.hostname} is out of subnet range.", {}

        if self.deck.cpu_cycles < 1:
            return False, "Insufficient CPU cycles (need 1 CPU).", {}

        # Pick target employee
        emp = None
        if employee_name and node.employees:
            emp = next((e for e in node.employees if e.name.lower() == employee_name.lower()), None)
        if not emp and node.employees:
            emp = node.employees[0]
        if not emp:
            emp = EmployeeProfile(name="Staff Associate", role="Operations", email=f"staff@{node.hostname}", awareness_level=SecurityAwarenessLevel.STANDARD)

        self.deck.cpu_cycles -= 1
        self.state.turns_elapsed += 1
        self.add_trace(6)
        self.tick_daemons()

        # Calculate success probability based on vector vs employee security awareness
        awareness = emp.awareness_level
        if vector_key == SocialVectorType.SPEAR_PHISH:
            base_chance = max(0.40, 0.90 - (node.security_level * 0.12))
        elif vector_key == SocialVectorType.PRETEXT:
            base_chance = 0.90 if awareness == SecurityAwarenessLevel.NAIVE else (0.75 if awareness == SecurityAwarenessLevel.STANDARD else 0.40)
        elif vector_key == SocialVectorType.BAIT:
            base_chance = 0.85 if awareness == SecurityAwarenessLevel.NAIVE else (0.70 if awareness == SecurityAwarenessLevel.STANDARD else 0.45)
        else:  # VISHING
            base_chance = 0.90 if awareness == SecurityAwarenessLevel.NAIVE else (0.70 if awareness == SecurityAwarenessLevel.STANDARD else 0.50)

        roll = self.rng.random()
        success = roll <= base_chance

        report = {
            "target_ip": node.ip_address,
            "target_hostname": node.hostname,
            "vector": vector_key,
            "employee": emp.name,
            "role": emp.role,
            "awareness": emp.awareness_level,
            "success": success,
            "roll": round(roll, 2),
            "chance": round(base_chance, 2),
        }

        if success:
            emp.compromised = True
            if node.status == NodeStatus.LOCKED:
                node.status = NodeStatus.DISCOVERED

            lowered = False
            if node.security_level > 1:
                node.security_level -= 1
                lowered = True

            # If host firewall has blocked rules, auto-bypass a blocked rule!
            fw_bypass_notice = ""
            if node.firewall and node.firewall.enabled:
                blocked_rule = next((r for r in node.firewall.rules if r.action == "BLOCK" and not r.bypassed), None)
                if blocked_rule:
                    blocked_rule.bypassed = True
                    blocked_rule.bypass_method = f"social_{vector_key}"
                    fw_bypass_notice = f"   * Leaked security override: Firewall port {blocked_rule.port}/tcp rule bypassed!\n"

            cred_file = f"/loot/{node.hostname}_credentials.token"
            token_content = (
                f"HARVESTED SOCIAL CREDENTIALS\n"
                f"Target: {emp.name} ({emp.role})\n"
                f"Host: {node.hostname} ({node.ip_address})\n"
                f"Vector: {vector_key.upper()}\n"
                f"Credential: {emp.leaked_credential or f'TOKEN-{self.rng.randint(1000, 9999)}-SEC'}\n"
            )
            if not any(f.path == cred_file for f in self.deck.local_filesystem):
                self.deck.local_filesystem.append(
                    VirtualFile(path=cred_file, size_kb=1, content=token_content, value_creds=40)
                )

            tag = "🎣 PHISHING SUCCESS" if vector_key == SocialVectorType.SPEAR_PHISH else f"🎭 SOCIAL ENGINEERING SUCCESS [{vector_key.upper()}]"
            msg = f"{tag}: Employee at {node.hostname} clicked credential lure!\n" if vector_key == SocialVectorType.SPEAR_PHISH else f"{tag}: Compromised {emp.name} ({emp.role}) at {node.hostname}!\n"
            if lowered:
                msg += f"   * Security tier downgraded to Level {node.security_level} (Buffer RAM required reduced to {node.security_level * 16}MB)!\n"
            if fw_bypass_notice:
                msg += fw_bypass_notice
            msg += f"   * Harvested auth token saved to local rig at {cred_file}."
            self.state.message_log.append(f"Social engineering [{vector_key}] success on {node.hostname}.")
            return True, msg, report
        else:
            self.add_trace(8)
            if node.antivirus:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + 20)
            tag = "🎣 PHISHING FAILED" if vector_key == SocialVectorType.SPEAR_PHISH else f"🎭 SOCIAL ENGINEERING FAILED [{vector_key.upper()}]"
            msg = f"{tag}: {emp.name} on {node.hostname} flagged lure. IDS alert triggered (Trace +8%)!"
            self.state.message_log.append(msg)
            return False, msg, report

    def phish_target(self, target_query: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Dispatch a simulated social engineering spear-phishing campaign to target host employees (backward compatible)."""
        return self.social_engineer(target_query, vector=SocialVectorType.SPEAR_PHISH)

    def get_firewall_status(self, target_query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Inspect the network firewall rules defending a target host."""
        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found.", None
        if not node.firewall:
            return True, f"Host {node.hostname} ({node.ip_address}) has no active network firewall.", None

        rules_desc = []
        for r in node.firewall.rules:
            status = "BYPASSED" if r.bypassed else ("BLOCKED" if r.action == "BLOCK" else "ALLOWED")
            rules_desc.append(f"  * Port {r.port}/tcp: [{status}] (Method: {r.bypass_method or 'None'})")

        msg = f"🛡️ [FIREWALL REPORT] {node.hostname} ({node.ip_address})\n"
        msg += f"Type: {node.firewall.firewall_type} | Policy: {node.firewall.policy} | Tampered: {node.firewall.tampered}\n"
        msg += "\n".join(rules_desc) if rules_desc else "  * No active port filtering rules."
        return True, msg, node.firewall.to_dict()

    def bypass_firewall(self, target_query: str, port: int, method: str = "knock") -> Tuple[bool, str]:
        """Execute a firewall bypass against a blocked port via port-knocking, packet fragmentation, or proxy-tunneling."""
        if self.state.is_game_over:
            return False, "Cannot bypass firewall: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot bypass firewall: terminal session jacked out."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        if not node.firewall or not node.firewall.enabled:
            return False, f"Host {node.hostname} has no active firewall."

        method_key = method.lower().strip()
        costs = {
            "knock": {"cpu": 1, "trace": 5, "name": "Port Knocking Sequence"},
            "fragment": {"cpu": 1, "trace": 7, "name": "MTU Packet Fragmentation"},
            "tunnel": {"cpu": 2, "trace": 9, "name": "Encapsulated Proxy Tunneling"},
        }
        if method_key not in costs:
            return False, f"Unknown bypass method '{method}'. Valid methods: knock, fragment, tunnel."

        spec = costs[method_key]
        if self.deck.cpu_cycles < spec["cpu"]:
            return False, f"INSUFFICIENT CPU: {spec['name']} requires {spec['cpu']} CPU cycles."

        rule = next((r for r in node.firewall.rules if r.port == port and r.action == "BLOCK"), None)
        if not rule:
            return False, f"Port {port}/tcp is not currently blocked by {node.hostname}'s firewall."

        if rule.bypassed:
            return False, f"Port {port}/tcp is already bypassed on {node.hostname}."

        self.deck.cpu_cycles -= spec["cpu"]
        self.state.turns_elapsed += 1
        self.add_trace(spec["trace"])
        self.tick_daemons()

        rule.bypassed = True
        rule.bypass_method = method_key
        msg = f"🔓 FIREWALL BYPASSED: Injected {spec['name']} into {node.hostname} ({node.ip_address}).\n"
        msg += f"   * Port {port}/tcp rule deactivated! Direct service exploitation is now enabled (Trace +{spec['trace']}%)."
        self.state.message_log.append(f"Bypassed firewall port {port} on {node.hostname}.")
        return True, msg

    def get_antivirus_status(self, target_query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Inspect the active Antivirus / EDR status on a target host."""
        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found.", None
        if not node.antivirus:
            return True, f"Host {node.hostname} ({node.ip_address}) has no active Antivirus software.", None

        status_str = "HOOKED / EVADED" if node.antivirus.evaded else ("ACTIVE / HUNTING" if node.antivirus.enabled else "DISABLED")
        msg = f"🛡️ [ANTIVIRUS REPORT] {node.hostname} ({node.ip_address})\n"
        msg += f"Engine: {node.antivirus.name} ({node.antivirus.version})\n"
        msg += f"Status: [{status_str}]\n"
        msg += f"Alert Level: {node.antivirus.alert_level}% (Sensitivity: {node.antivirus.heuristic_sensitivity}/5)\n"
        msg += f"Quarantined Daemons: {len(node.antivirus.quarantine_log)}"
        return True, msg, node.antivirus.to_dict()

    def evade_antivirus(self, target_query: str, method: str = "rootkit") -> Tuple[bool, str]:
        """Inject a stealth evasion hook or memory-patch into a target host's Antivirus suite."""
        if self.state.is_game_over:
            return False, "Cannot evade AV: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot evade AV: terminal session jacked out."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        if not node.antivirus or not node.antivirus.enabled:
            return False, f"Host {node.hostname} has no active Antivirus to evade."

        if node.antivirus.evaded:
            return False, f"Antivirus on {node.hostname} ({node.antivirus.name}) is already evaded and blinded."

        method_key = method.lower().strip()
        costs = {
            "rootkit": {"cpu": 2, "trace": 6, "name": "Kernel Rootkit Hook"},
            "spoof": {"cpu": 1, "trace": 8, "name": "Signature Morphing Shifter"},
        }
        if method_key not in costs:
            return False, f"Unknown evasion method '{method}'. Valid methods: rootkit, spoof."

        spec = costs[method_key]
        if self.deck.cpu_cycles < spec["cpu"]:
            return False, f"INSUFFICIENT CPU: {spec['name']} requires {spec['cpu']} CPU cycles."

        self.deck.cpu_cycles -= spec["cpu"]
        self.state.turns_elapsed += 1
        self.add_trace(spec["trace"])
        self.tick_daemons()

        node.antivirus.evaded = True
        node.antivirus.alert_level = max(0, node.antivirus.alert_level - 35)
        msg = f"👁️‍🗨️ ANTIVIRUS EVADED: Deployed {spec['name']} against {node.antivirus.name} on {node.hostname}.\n"
        msg += f"   * EDR scanner blinded! Memory sweeps suppressed for active daemons (Alert reduced to {node.antivirus.alert_level}%)."
        self.state.message_log.append(f"Blinded AV on {node.hostname}.")
        return True, msg

    def list_cves(self) -> List[Dict[str, Any]]:
        """Return the catalog of weaponized CVE exploit payloads."""
        return [cve.to_dict() for cve in KNOWN_CVES.values()]

    def craft_virus(self, recipe_name: str) -> Tuple[bool, str]:
        """Assemble a custom virus chip in the netrunner workshop."""
        if self.state.is_game_over:
            return False, "Cannot craft virus: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot craft virus: terminal session jacked out."

        recipe_key = str(recipe_name or "").lower().strip()
        recipe = CRAFTING_RECIPES.get(recipe_key)
        if not recipe:
            available = ", ".join(CRAFTING_RECIPES.keys())
            return False, f"Unknown recipe '{recipe_name}'. Available recipes: {available}"

        total_funds = self.deck.cryptocreds + self.state.unbanked_creds
        if total_funds < recipe.cost_creds:
            return False, f"Insufficient funds: Synthesis requires {recipe.cost_creds} Creds (available: {total_funds} Creds)."

        rem = recipe.cost_creds
        if self.state.unbanked_creds >= rem:
            self.state.unbanked_creds -= rem
        else:
            rem -= self.state.unbanked_creds
            self.state.unbanked_creds = 0
            self.deck.cryptocreds -= rem

        self.deck.exploits.append(recipe.name)
        msg = f"🧬 WORKSHOP SYNTHESIS COMPLETE: Crafted virus chip '{recipe.name}' (Vector: {recipe.vector}, Payload: {recipe.payload}). Loaded into deck exploits."
        self.state.message_log.append(msg)
        return True, msg

    def list_crafting_recipes(self) -> List[Dict[str, Any]]:
        """List available malware crafting recipes in the workshop."""
        return [r.to_dict() for r in CRAFTING_RECIPES.values()]


