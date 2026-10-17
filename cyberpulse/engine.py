"""Deterministic cyberspace game engine managing player movement, trace, and breach states."""

from typing import Dict, List, Optional, Tuple

from cyberpulse.models import CyberDeck, GameState, Node, NodeStatus, NodeType
from cyberpulse.network import generate_network


class GameEngine:
    """Manages gameplay rules, movement across network topology, and victory/defeat conditions."""

    def __init__(self, seed: int = 1337):
        self.seed = seed
        self.nodes: Dict[str, Node] = generate_network(seed)
        self.deck: CyberDeck = CyberDeck()
        self.state: GameState = GameState(
            seed=seed,
            current_node_id="node_gateway",
            trace_percent=0,
            turns_elapsed=0,
        )

    def get_current_node(self) -> Node:
        return self.nodes[self.state.current_node_id]

    def add_trace(self, amount: int) -> None:
        """Increase system security trace. If 100% is reached, player is locked out."""
        self.state.trace_percent = min(100, self.state.trace_percent + amount)
        if self.state.trace_percent >= 100:
            self.state.is_game_over = True
            self.state.message_log.append("🚨 SECURITY TRACE LOCKOUT DETECTED! Connection severed.")

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
        self.state.turns_elapsed += 1
        return True, f"Scanned {len(revealed)} adjacent network nodes.", revealed

    def can_move_to(self, target_id: str) -> Tuple[bool, str]:
        """Verify whether the player can transition to target node."""
        if self.state.is_game_over:
            return False, "Cannot move: system lockout in effect."
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
        self.add_trace(2)
        node = self.get_current_node()
        msg = f"⚡ Transferred terminal session to '{node.name}'."
        self.state.message_log.append(msg)
        return True, msg

    def complete_breach(self, node_id: str) -> Tuple[bool, str]:
        """Mark node as breached, award loot, and trigger victory if Central Core."""
        if node_id not in self.nodes:
            return False, f"Invalid node '{node_id}'."

        node = self.nodes[node_id]
        node.status = NodeStatus.BREACHED
        self.deck.cryptocreds += node.credits_reward
        msg = f"💥 Infiltration successful! '{node.name}' breached."

        if node.credits_reward > 0:
            msg += f" Extracted {node.credits_reward} CryptoCreds."
        if node.data_payload:
            msg += f" Acquired: [{node.data_payload}]."

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
