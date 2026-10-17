"""Domain models for CyberPulse cyberspace nodes, decks, contracts, and career profiles."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


class NodeType:
    GATEWAY = "GATEWAY"
    FIREWALL = "FIREWALL"
    DATA_VAULT = "DATA_VAULT"
    ICE_DEFENSE = "ICE_DEFENSE"
    CENTRAL_CORE = "CENTRAL_CORE"


class NodeStatus:
    LOCKED = "LOCKED"
    DISCOVERED = "DISCOVERED"
    BREACHED = "BREACHED"


class RewardType:
    STANDARD = "STANDARD"
    CRITICAL_JACKPOT = "CRITICAL_JACKPOT"
    CHIP_DROP = "CHIP_DROP"


@dataclass
class PortService:
    """An exposed TCP/UDP network service on a target host."""
    port: int
    service: str  # "ssh", "ftp", "http", "mysql", "smtp"
    version: str
    vulnerable: bool = True
    exploit_tool: str = "ssh_overflow"
    breached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortService":
        return cls(**data)


@dataclass
class VirtualFile:
    """A file stored on a target host's virtual filesystem."""
    path: str
    size_kb: int
    content: str
    is_target_data: bool = False
    value_creds: int = 150
    downloaded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VirtualFile":
        return cls(**data)


@dataclass
class BountyContract:
    """A syndicate-issued objective with bonus rewards upon fulfillment (Zeigarnik Effect)."""
    contract_id: str
    title: str
    target_node_type: str
    target_ip: Optional[str] = None
    target_file: Optional[str] = None
    wipe_logs_required: bool = False
    max_trace_limit: int = 75
    reward_creds: int = 150
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BountyContract":
        return cls(**data)


@dataclass
class CareerProfile:
    """Persistent meta-progression profile tracking permanent stats and upgrades."""
    alias: str = "ZeroCool"
    banked_creds: int = 100
    lifetime_creds: int = 100
    successful_runs: int = 0
    failed_runs: int = 0
    current_streak: int = 0
    best_streak: int = 0
    purchased_upgrades: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CareerProfile":
        return cls(**data)


class FirewallPolicy:
    ALLOW_ALL = "ALLOW_ALL"
    FILTER_PORTS = "FILTER_PORTS"
    STRICT_DROP = "STRICT_DROP"


@dataclass
class FirewallRule:
    """A packet filtering or port access rule enforced by a host firewall."""
    rule_id: str
    port: int
    action: str = "BLOCK"  # "BLOCK", "ALLOW"
    bypassed: bool = False
    bypass_method: Optional[str] = None  # "knock", "fragment", "tunnel"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FirewallRule":
        return cls(**data)


@dataclass
class HostFirewall:
    """A network firewall defending a host's open ports against unauthorized ingress."""
    enabled: bool = True
    policy: str = FirewallPolicy.FILTER_PORTS
    firewall_type: str = "Stateful-Packet-Filter"
    rules: List[FirewallRule] = field(default_factory=list)
    tampered: bool = False

    def is_port_blocked(self, port: int) -> bool:
        if not self.enabled or self.tampered:
            return False
        for rule in self.rules:
            if rule.port == port and rule.action == "BLOCK" and not rule.bypassed:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["rules"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.rules]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HostFirewall":
        clean = dict(data)
        if "rules" in clean and isinstance(clean["rules"], list):
            clean["rules"] = [
                FirewallRule.from_dict(r) if isinstance(r, dict) else r for r in clean["rules"]
            ]
        return cls(**clean)


@dataclass
class HostAntivirus:
    """An active endpoint detection and response (EDR) / antivirus service on a target host."""
    name: str = "SentinelCore EDR"
    version: str = "v4.2"
    enabled: bool = True
    alert_level: int = 0          # 0% to 100%
    heuristic_sensitivity: int = 3 # 1 (low) to 5 (high)
    evaded: bool = False           # True if player has hooked/blinded the AV
    quarantine_log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HostAntivirus":
        return cls(**data)


@dataclass
class ExploitPayload:
    """A weaponized vulnerability exploit / CVE targeting specific network services."""
    cve_id: str                    # e.g. "CVE-2024-38812"
    name: str                      # e.g. "SSH Buffer Overflow"
    target_service: str            # "ssh", "ftp", "http", "mysql", "smtp", "any"
    required_ram_mb: int = 16
    cpu_cost: int = 2
    stealth_rating: int = 3        # 1 (noisy, triggers AV) to 5 (stealthy zero-day)
    damage_trace: int = 10         # Trace generated on launch
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExploitPayload":
        return cls(**data)


class SocialVectorType:
    PRETEXT = "pretext"         # Impersonating Internal IT support requesting urgent cred reset
    BAIT = "bait"               # Dropping infected simulated USB / trojan PDF document
    SPEAR_PHISH = "spear_phish" # Executive CEO fraud urgent wire / credential lure
    VISHING = "vishing"         # Voice-phishing helpdesk operator for MFA token


class SecurityAwarenessLevel:
    NAIVE = "NAIVE"             # 85% success on all vectors
    STANDARD = "STANDARD"       # 55% success, requires pretext/bait
    PARANOID = "PARANOID"       # 25% success, requires spear_phish/vishing


@dataclass
class EmployeeProfile:
    """Target organization employee persona susceptible to social engineering attacks."""
    name: str
    role: str                   # "Helpdesk Operator", "DevOps Engineer", "CFO", "Marketing Intern"
    email: str
    awareness_level: str = SecurityAwarenessLevel.STANDARD
    compromised: bool = False
    leaked_credential: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmployeeProfile":
        return cls(**data)


@dataclass
class Node:
    """A target host or infrastructure subsystem on the network grid."""
    node_id: str
    name: str
    node_type: str
    security_level: int
    status: str = NodeStatus.LOCKED
    connected_ids: List[str] = field(default_factory=list)
    trace_rate: int = 10
    credits_reward: int = 0
    data_payload: Optional[str] = None
    puzzle_type: Optional[str] = None  # "frequency", "buffer", "hash"
    ip_address: str = "127.0.0.1"
    hostname: str = "localhost"
    ports: List[PortService] = field(default_factory=list)
    filesystem: List[VirtualFile] = field(default_factory=list)
    logs_cleared: bool = False
    firewall: Optional[HostFirewall] = None
    antivirus: Optional[HostAntivirus] = None
    employees: List[EmployeeProfile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["ports"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.ports]
        res["filesystem"] = [f.to_dict() if hasattr(f, "to_dict") else f for f in self.filesystem]
        if self.firewall:
            res["firewall"] = self.firewall.to_dict() if hasattr(self.firewall, "to_dict") else self.firewall
        if self.antivirus:
            res["antivirus"] = self.antivirus.to_dict() if hasattr(self.antivirus, "to_dict") else self.antivirus
        res["employees"] = [e.to_dict() if hasattr(e, "to_dict") else e for e in self.employees]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        data_clean = dict(data)
        if "ports" in data_clean and isinstance(data_clean["ports"], list):
            data_clean["ports"] = [
                PortService.from_dict(p) if isinstance(p, dict) else p for p in data_clean["ports"]
            ]
        if "filesystem" in data_clean and isinstance(data_clean["filesystem"], list):
            data_clean["filesystem"] = [
                VirtualFile.from_dict(f) if isinstance(f, dict) else f for f in data_clean["filesystem"]
            ]
        if "firewall" in data_clean and isinstance(data_clean["firewall"], dict):
            data_clean["firewall"] = HostFirewall.from_dict(data_clean["firewall"])
        if "antivirus" in data_clean and isinstance(data_clean["antivirus"], dict):
            data_clean["antivirus"] = HostAntivirus.from_dict(data_clean["antivirus"])
        if "employees" in data_clean and isinstance(data_clean["employees"], list):
            data_clean["employees"] = [
                EmployeeProfile.from_dict(e) if isinstance(e, dict) else e for e in data_clean["employees"]
            ]
        return cls(**data_clean)


@dataclass
class MalwareDaemon:
    """An active background script deployed on a compromised host (e.g. keylogger, siphon)."""
    daemon_id: str
    daemon_type: str  # "keylogger", "siphon", "worm"
    target_node_id: str
    target_ip: str
    yield_per_turn: int = 25
    detection_risk: int = 4
    turns_active: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MalwareDaemon":
        return cls(**data)


@dataclass
class VirusCraftRecipe:
    """A crafting recipe to synthesize custom virus/malware chips in the netrunner workshop."""
    name: str
    vector: str   # "stealth", "brute", "worm"
    payload: str  # "keylogger", "credit_siphon", "trace_wipe", "logic_overload"
    cost_creds: int = 100
    cpu_cost: int = 2
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VirusCraftRecipe":
        return cls(**data)


@dataclass
class CyberDeck:
    """The player's hardware deck used to execute hacking exploits."""
    model_name: str = "Onyx-Vortex 400"
    cpu_cycles: int = 10
    max_cpu: int = 10
    ram_mb: int = 64
    max_ram: int = 64
    cryptocreds: int = 100
    exploits: List[str] = field(default_factory=lambda: ["port_scan", "buffer_overflow", "spoof_ip"])
    ice_dampener_level: int = 0
    overclock_level: int = 0
    ram_boost_level: int = 0
    local_ip: str = "10.99.0.2"
    local_hostname: str = "rig.netrunner.local"
    local_filesystem: List[VirtualFile] = field(default_factory=lambda: [
        VirtualFile(path="/home/deck/notes.txt", size_kb=2, content="NETRUNNER LOG:\n- Target Alpha router: 192.168.1.10\n- Target Finance Vault: 10.0.4.15\n- Target Supercore: 172.16.80.1"),
        VirtualFile(path="/bin/netrunner.sh", size_kb=4, content="#!/bin/sh\n# Cyberdeck intrusion helper matrix\necho 'Rig online. Neural link active.'"),
        VirtualFile(path="/loot/README.md", size_kb=1, content="# Loot Directory\nExfiltrated target data files are saved here automatically."),
    ])
    active_daemons: List[MalwareDaemon] = field(default_factory=list)
    known_cves: List[str] = field(default_factory=lambda: [
        "CVE-2024-38812", "CVE-2023-22515", "CVE-2024-21413", "CVE-2025-9901"
    ])

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["local_filesystem"] = [f.to_dict() if hasattr(f, "to_dict") else f for f in self.local_filesystem]
        res["active_daemons"] = [d.to_dict() if hasattr(d, "to_dict") else d for d in self.active_daemons]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CyberDeck":
        clean = dict(data)
        if "local_filesystem" in clean and isinstance(clean["local_filesystem"], list):
            clean["local_filesystem"] = [
                VirtualFile.from_dict(f) if isinstance(f, dict) else f for f in clean["local_filesystem"]
            ]
        if "active_daemons" in clean and isinstance(clean["active_daemons"], list):
            clean["active_daemons"] = [
                MalwareDaemon.from_dict(d) if isinstance(d, dict) else d for d in clean["active_daemons"]
            ]
        if "known_cves" not in clean:
            clean["known_cves"] = ["CVE-2024-38812", "CVE-2023-22515", "CVE-2024-21413", "CVE-2025-9901"]
        return cls(**clean)


def apply_career_profile(deck: CyberDeck, profile: CareerProfile) -> None:
    """Apply persistent upgrades and synchronize banked funds into an active cyberdeck."""
    deck.cryptocreds = profile.banked_creds
    for up in profile.purchased_upgrades:
        if up == "overclock_cpu":
            deck.overclock_level += 1
            deck.max_cpu += 2
            deck.cpu_cycles = max(deck.cpu_cycles, deck.max_cpu)
        elif up == "expand_ram":
            deck.ram_boost_level += 1
            deck.max_ram += 32
            deck.ram_mb = max(deck.ram_mb, deck.max_ram)
        elif up == "ice_dampener":
            deck.ice_dampener_level += 1
        elif up not in deck.exploits:
            deck.exploits.append(up)


@dataclass
class GameState:
    """The full runtime state of a CyberPulse infiltration run."""
    seed: int
    current_node_id: str
    trace_percent: int = 0
    turns_elapsed: int = 0
    is_game_over: bool = False
    is_victory: bool = False
    is_jacked_out: bool = False
    unbanked_creds: int = 0
    looted_payloads: List[str] = field(default_factory=list)
    active_contract: Optional[BountyContract] = None
    near_miss_count: int = 0
    message_log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        if self.active_contract:
            res["active_contract"] = self.active_contract.to_dict()
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        contract_data = data.get("active_contract")
        contract = BountyContract.from_dict(contract_data) if isinstance(contract_data, dict) else None
        data_clean = dict(data)
        data_clean["active_contract"] = contract
        return cls(**data_clean)
