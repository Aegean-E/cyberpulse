"""State-driven first-run field manual."""

from typing import Any, Dict, List

from cyberpulse.models import NodeStatus, NodeType

TUTORIAL_STEPS = (
    ("scan", "SCAN THE GRID", "Run `scan` to reveal the hosts beside the gateway."),
    ("probe", "PROBE A HOST", "Run `probe <ip>` to inspect services, ports and defenses."),
    ("breach", "BREACH A HOST", "Run `hack <ip>` and solve the intrusion puzzle."),
    ("loot", "EXFILTRATE DATA", "Run `ls`, then `steal <path>` on a breached host."),
    ("jackout", "EXTRACT", "Run `jackout` from a breached host to bank your loot."),
)


def tutorial_steps(engine: Any) -> List[Dict[str, Any]]:
    """Return the five core-loop steps annotated with live completion state."""
    state = engine.state
    breached = any(
        node.status == NodeStatus.BREACHED and node.node_type != NodeType.GATEWAY
        for node in engine.nodes.values()
    )
    done = {
        "scan": bool(getattr(state, "scanned", False)),
        "probe": bool(getattr(state, "probed_nodes", [])),
        "breach": breached,
        "loot": bool(getattr(state, "looted_payloads", [])),
        "jackout": bool(state.is_jacked_out or state.is_victory),
    }
    return [
        {
            "step_id": step_id,
            "title": title,
            "hint": hint,
            "done": done[step_id],
        }
        for step_id, title, hint in TUTORIAL_STEPS
    ]
