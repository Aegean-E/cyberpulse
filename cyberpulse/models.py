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
class BountyContract:
    """A syndicate-issued objective with bonus rewards upon fulfillment (Zeigarnik Effect)."""
    contract_id: str
    title: str
    target_node_type: str
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CyberDeck":
        return cls(**data)


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
