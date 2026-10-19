"""Living-grid world simulation: in-game clock, corporate alert, news, and grid response."""

import random
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from cyberpulse.models import NetWatchHunter, NewsItem, Node, NodeStatus, NodeType, WorldState

MINUTES_PER_TURN = 15
NEWS_CAPACITY = 60
ALERT_MAX = 100
MARKET_FLOOR = 0.80
MARKET_CEILING = 1.35
RESECURE_ALERT_THRESHOLD = 50
HUNTER_ALERT_THRESHOLD = 60
RESECURE_COOLDOWN = 12
RESECURE_MAX_PER_TURN = 1
AMBIENT_EVENT_COOLDOWN = 2

SHIFT_BOUNDS = ((0, "Late Night"), (6, "Morning"), (12, "Afternoon"), (18, "Evening"))


@dataclass(frozen=True)
class AmbientEvent:
    """A deterministic grid event that can nudge credits, CPU, trace, alert, or topology."""
    key: str
    source: str
    headline: str
    tone: str = "neutral"
    credits: int = 0
    cpu: int = 0
    trace: int = 0
    alert: int = 0
    reveal: bool = False
    min_alert: int = 0
    weight: int = 10


AMBIENT_EVENTS: Sequence[AmbientEvent] = (
    AmbientEvent(
        key="street_chatter",
        source="StreetFeed",
        headline="Chrome vendors hawk bootleg ICE burners in the night market.",
        weight=12,
    ),
    AmbientEvent(
        key="cooling_front",
        source="GridWire",
        headline="Municipal cooling front restores deck thermals across the Sprawl.",
        tone="positive",
        cpu=1,
        weight=8,
    ),
    AmbientEvent(
        key="freelance_wire",
        source="DeadDrop",
        headline="An anonymous wire transfer clears the dead-drop account.",
        tone="positive",
        credits=25,
        weight=8,
    ),
    AmbientEvent(
        key="informant_tip",
        source="DeadDrop",
        headline="An informant leaks a fresh subnet address.",
        tone="positive",
        reveal=True,
        weight=6,
    ),
    AmbientEvent(
        key="corporate_pr",
        source="OmniCorp PR",
        headline="OmniCorp PR blitz calms the grid after last night's breach reports.",
        tone="positive",
        alert=-4,
        weight=7,
    ),
    AmbientEvent(
        key="grid_brownout",
        source="GridWire",
        headline="Rolling brownout browns out deck capacitors.",
        tone="negative",
        cpu=-1,
        min_alert=35,
        weight=7,
    ),
    AmbientEvent(
        key="ice_patrol",
        source="NetWatch",
        headline="NetWatch ICE patrol pings the local subnet.",
        tone="negative",
        trace=4,
        min_alert=35,
        weight=8,
    ),
    AmbientEvent(
        key="crackdown",
        source="NetWatch",
        headline="City council announces an anti-netrunner crackdown.",
        tone="negative",
        alert=6,
        min_alert=35,
        weight=7,
    ),
)


def world_rng(seed: int, tick: int, stream: str = "ambient") -> random.Random:
    """Return a deterministic per-tick RNG stream independent of the engine reward RNG."""
    return random.Random(f"cyberpulse-world:{int(seed)}:{int(tick)}:{stream}")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def clock_minute_text(minute: int) -> str:
    """Render an in-game minute of day as HH:MM."""
    minute = int(minute) % (24 * 60)
    return f"{minute // 60:02d}:{minute % 60:02d}"


def shift_name(minute: int) -> str:
    """Return the named shift covering an in-game minute of day."""
    hour = (int(minute) % (24 * 60)) // 60
    name = SHIFT_BOUNDS[0][1]
    for start, label in SHIFT_BOUNDS:
        if hour >= start:
            name = label
    return name


def clock_label(world: WorldState) -> str:
    """Return a compact clock label such as ``Day 2 13:45 (Afternoon)``."""
    return f"Day {world.day} {clock_minute_text(world.minute)} ({shift_name(world.minute)})"


def record_news(world: WorldState, tick: int, source: str, headline: str, tone: str = "neutral") -> NewsItem:
    """Append a headline to the living-grid feed, keeping the newest entries."""
    item = NewsItem(
        tick=int(tick),
        day=int(world.day),
        minute=int(world.minute),
        source=source,
        headline=headline,
        tone=tone,
    )
    world.news.append(item)
    if len(world.news) > NEWS_CAPACITY:
        del world.news[:-NEWS_CAPACITY]
    return item


def format_news_item(item: NewsItem) -> str:
    return f"[Day {item.day} {clock_minute_text(item.minute)}] {item.source}: {item.headline}"


def advance_clock(world: WorldState, turns: int = 1) -> None:
    """Advance the in-game clock, rolling over to the next day at midnight."""
    total = world.minute + (MINUTES_PER_TURN * int(turns))
    world.minute = total % (24 * 60)
    world.day += total // (24 * 60)


def adjust_alert(world: WorldState, delta: int) -> int:
    """Raise or lower the grid-wide corporate alert level within 0-100."""
    world.alert_level = int(clamp(world.alert_level + int(delta), 0, ALERT_MAX))
    return world.alert_level


def adjust_market(world: WorldState, delta: float) -> float:
    """Nudge the black-market price multiplier within its bounds."""
    world.market_index = round(clamp(world.market_index + float(delta), MARKET_FLOOR, MARKET_CEILING), 3)
    return world.market_index


def drift_market(world: WorldState, rng: random.Random) -> float:
    """Random-walk the black market, pulled upward while the grid is hot."""
    hot_target = 1.0 + max(0, world.alert_level - 50) / 500.0
    drift = rng.uniform(-0.05, 0.05) + (hot_target - world.market_index) * 0.20
    return adjust_market(world, drift)


def market_multiplier(world: WorldState) -> float:
    """Current black-market price multiplier applied to shop costs."""
    return round(clamp(world.market_index, MARKET_FLOOR, MARKET_CEILING), 3)


def patrol_pressure(world: WorldState) -> int:
    """Trace added per turn by NetWatch patrol sweeps at higher alert levels."""
    if world.alert_level >= 75:
        return 2
    if world.alert_level >= 50:
        return 1
    return 0


def ambient_event_for(
    seed: int,
    tick: int,
    alert_level: int,
    turns_since_event: int,
) -> Optional[AmbientEvent]:
    """Roll one deterministic ambient event for a world tick, or None for a quiet turn."""
    if turns_since_event < AMBIENT_EVENT_COOLDOWN:
        return None
    rng = world_rng(seed, tick, "ambient")
    chance = 0.18 + min(0.22, max(0, alert_level) / 500.0)
    if rng.random() > chance:
        return None

    eligible = [e for e in AMBIENT_EVENTS if alert_level >= e.min_alert]
    weights = [
        e.weight + (4 if e.min_alert and alert_level >= e.min_alert else 0)
        for e in eligible
    ]
    return rng.choices(eligible, weights=weights, k=1)[0]


def plan_resecures(
    seed: int,
    tick: int,
    alert_level: int,
    nodes: Dict[str, Node],
    current_node_id: str,
) -> List[str]:
    """Choose hosts the grid re-secures this tick: hot grid, cooled-down, looted targets."""
    if alert_level < RESECURE_ALERT_THRESHOLD:
        return []
    rng = world_rng(seed, tick, "response")
    picks: List[str] = []
    for node in sorted(nodes.values(), key=lambda n: n.node_id):
        if len(picks) >= RESECURE_MAX_PER_TURN:
            break
        if node.status != NodeStatus.BREACHED or node.node_id == current_node_id:
            continue
        if node.node_type == NodeType.CENTRAL_CORE:
            continue
        if node.breached_turn < 0 or tick - node.breached_turn < RESECURE_COOLDOWN:
            continue
        chance = min(0.60, 0.10 + (alert_level - RESECURE_ALERT_THRESHOLD) / 200.0 + node.security_level * 0.03)
        if rng.random() < chance:
            picks.append(node.node_id)
    return picks


def apply_resecure(node: Node) -> str:
    """Undo a breach in place and restore the host's defensive posture."""
    node.status = NodeStatus.DISCOVERED
    for port in node.ports:
        port.breached = False
    node.logs_cleared = False
    if node.firewall:
        node.firewall.tampered = False
        for rule in node.firewall.rules:
            rule.bypassed = False
    if node.antivirus:
        node.antivirus.alert_level = 0
        node.antivirus.evaded = False
    return (
        f"🧹 [GRID RESPONSE] Sysadmins re-secured {node.hostname} ({node.ip_address}); "
        "root access revoked and logs restored."
    )


def find_shortest_path(nodes: Dict[str, Node], start_id: str, goal_id: str) -> List[str]:
    """Find the shortest unweighted path of node IDs from start_id to goal_id using BFS."""
    if start_id not in nodes or goal_id not in nodes:
        return []
    if start_id == goal_id:
        return [start_id]
    queue: deque = deque([[start_id]])
    visited = {start_id}
    while queue:
        path = queue.popleft()
        current = path[-1]
        node = nodes.get(current)
        if not node:
            continue
        for neighbor in sorted(node.connected_ids):
            if neighbor == goal_id:
                return path + [neighbor]
            if neighbor not in visited and neighbor in nodes:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return []


def calculate_distance(nodes: Dict[str, Node], start_id: str, goal_id: str) -> int:
    """Return the hop distance between start_id and goal_id, or -1 if unreachable."""
    path = find_shortest_path(nodes, start_id, goal_id)
    if not path:
        return -1
    return len(path) - 1


def deploy_hunter(world: WorldState, nodes: Dict[str, Node], tick: int) -> Optional[NetWatchHunter]:
    """Deploy an active NetWatch Hunter if alert level exceeds threshold and none is active."""
    if world.alert_level < HUNTER_ALERT_THRESHOLD:
        return None
    for h in world.hunters:
        if h.status in ("hunting", "confused"):
            return None

    spawn_id = ""
    for nid, node in nodes.items():
        if node.node_type == NodeType.CENTRAL_CORE:
            spawn_id = nid
            break
    if not spawn_id and nodes:
        sorted_nodes = sorted(nodes.values(), key=lambda n: (n.security_level, n.node_id), reverse=True)
        spawn_id = sorted_nodes[0].node_id

    if not spawn_id:
        return None

    hunter_idx = len(world.hunters) + 1
    hunter = NetWatchHunter(
        hunter_id=f"hunter_{hunter_idx}_{tick}",
        name=f"NetWatch Hunter Aegis-{hunter_idx}",
        current_node_id=spawn_id,
        status="hunting",
        turns_active=0,
    )
    world.hunters.append(hunter)
    record_news(
        world,
        tick,
        "NetWatch",
        f"CRITICAL: {hunter.name} deployed to sector subnets to hunt intruder.",
        tone="alert",
    )
    return hunter


def step_hunter(
    hunter: NetWatchHunter,
    nodes: Dict[str, Node],
    player_node_id: str,
    rng: random.Random,
) -> Dict[str, Any]:
    """Advance the hunter by 1 hop along the network graph towards the player or random neighbor if confused."""
    if hunter.status == "neutralized":
        return {"action": "idle", "hunter": hunter}

    prev_node = hunter.current_node_id
    if hunter.confused_turns > 0:
        hunter.confused_turns -= 1
        curr = nodes.get(hunter.current_node_id)
        if curr and curr.connected_ids:
            candidates = sorted(curr.connected_ids)
            next_node = rng.choice(candidates)
            hunter.current_node_id = next_node
        hunter.turns_active += 1
        if hunter.confused_turns == 0 and hunter.status == "confused":
            hunter.status = "hunting"
        return {
            "action": "confused",
            "hunter": hunter,
            "from_node": prev_node,
            "to_node": hunter.current_node_id,
        }

    hunter.target_node_id = player_node_id
    path = find_shortest_path(nodes, hunter.current_node_id, player_node_id)
    if len(path) >= 2:
        next_node = path[1]
        hunter.current_node_id = next_node
        hunter.turns_active += 1
        if hunter.current_node_id == player_node_id:
            hunter.status = "intercepted"
            return {
                "action": "intercepted",
                "hunter": hunter,
                "from_node": prev_node,
                "to_node": next_node,
                "node_id": player_node_id,
            }
        return {
            "action": "moved",
            "hunter": hunter,
            "from_node": prev_node,
            "to_node": next_node,
        }
    elif hunter.current_node_id == player_node_id:
        hunter.status = "intercepted"
        return {
            "action": "intercepted",
            "hunter": hunter,
            "from_node": prev_node,
            "to_node": hunter.current_node_id,
            "node_id": player_node_id,
        }
    else:
        hunter.turns_active += 1
        return {"action": "idle", "hunter": hunter, "node_id": hunter.current_node_id}


def neutralize_hunter(hunter: NetWatchHunter, reason: str = "logic_bomb") -> str:
    """Neutralize an active NetWatch hunter."""
    hunter.status = "neutralized"
    return f"⚡ {hunter.name} was neutralized via {reason}! Sector radar clear."


def world_summary(world: WorldState) -> Dict[str, Any]:
    """Serialize the living-grid snapshot for CLI and Web consumers."""
    active_hunters = [h for h in world.hunters if h.status in ("hunting", "confused", "intercepted")]
    return {
        "clock": clock_label(world),
        "day": world.day,
        "minute": world.minute,
        "shift": shift_name(world.minute),
        "alert_level": world.alert_level,
        "market_multiplier": market_multiplier(world),
        "resecured_count": world.resecured_count,
        "news_count": len(world.news),
        "active_hunters_count": len(active_hunters),
        "hunters": [h.to_dict() for h in active_hunters],
    }
