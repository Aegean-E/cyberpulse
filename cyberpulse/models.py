"""Domain models for CyberPulse cyberspace nodes, decks, and game state."""

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
    message_log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        return cls(**data)
