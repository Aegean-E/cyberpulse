"""Deterministic cyberspace game engine with risk-reward loss aversion and near-miss feedback."""

import random
from typing import Dict, List, Optional, Tuple

from cyberpulse.models import (
    BountyContract,
    CareerProfile,
    CyberDeck,
    GameState,
    Node,
    NodeStatus,
    NodeType,
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
