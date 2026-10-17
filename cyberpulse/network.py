"""Procedural cyberspace network generator with deterministic topology."""

import random
from typing import Dict

from cyberpulse.models import Node, NodeStatus, NodeType


def generate_network(seed: int) -> Dict[str, Node]:
    """Generate a deterministic cyberspace infiltration network grid from seed."""
    rng = random.Random(seed)

    nodes: Dict[str, Node] = {
        "node_gateway": Node(
            node_id="node_gateway",
            name="External Border Gateway",
            node_type=NodeType.GATEWAY,
            security_level=1,
            status=NodeStatus.BREACHED,  # Player starts here
            connected_ids=["node_proxy_a", "node_proxy_b"],
            trace_rate=5,
            credits_reward=0,
            puzzle_type=None,
        ),
        "node_proxy_a": Node(
            node_id="node_proxy_a",
            name="Subnet Router Alpha",
            node_type=NodeType.FIREWALL,
            security_level=1,
            status=NodeStatus.DISCOVERED,
            connected_ids=["node_gateway", "node_vault_1", "node_ice_perimeter"],
            trace_rate=10,
            credits_reward=50,
            data_payload="System architecture specs",
            puzzle_type="frequency",
        ),
        "node_proxy_b": Node(
            node_id="node_proxy_b",
            name="Subnet Router Beta",
            node_type=NodeType.FIREWALL,
            security_level=2,
            status=NodeStatus.DISCOVERED,
            connected_ids=["node_gateway", "node_vault_2", "node_ice_perimeter"],
            trace_rate=15,
            credits_reward=75,
            data_payload="Admin credential fragment",
            puzzle_type="buffer",
        ),
        "node_vault_1": Node(
            node_id="node_vault_1",
            name="Financial Ledger Vault",
            node_type=NodeType.DATA_VAULT,
            security_level=2,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_a"],
            trace_rate=15,
            credits_reward=250,
            data_payload="Corporate slush fund transaction logs",
            puzzle_type="hash",
        ),
        "node_vault_2": Node(
            node_id="node_vault_2",
            name="Research & Prototype Archive",
            node_type=NodeType.DATA_VAULT,
            security_level=3,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_b"],
            trace_rate=20,
            credits_reward=350,
            data_payload="Classified Neural Interface schematic",
            puzzle_type="buffer",
        ),
        "node_ice_perimeter": Node(
            node_id="node_ice_perimeter",
            name="Black ICE Defense Cluster",
            node_type=NodeType.ICE_DEFENSE,
            security_level=4,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_a", "node_proxy_b", "node_central_core"],
            trace_rate=30,
            credits_reward=150,
            data_payload="Root clearance security token",
            puzzle_type="frequency",
        ),
        "node_central_core": Node(
            node_id="node_central_core",
            name="Nexus Central Supercore",
            node_type=NodeType.CENTRAL_CORE,
            security_level=5,
            status=NodeStatus.LOCKED,
            connected_ids=["node_ice_perimeter"],
            trace_rate=40,
            credits_reward=1000,
            data_payload="PROJECT OMEGA: Master AI Decryption Keys",
            puzzle_type="hash",
        ),
    }

    return nodes
