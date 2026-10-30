"""Deterministic daily-run keys, seeds and rule modifiers."""

from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class DailyModifier:
    """A rule twist applied only to a daily run."""

    modifier_id: str
    name: str
    description: str
    start_alert: int = 0
    start_cpu: int = 0
    trace_multiplier: float = 1.0
    contract_multiplier: float = 1.0


DAILY_MODIFIERS: Tuple[DailyModifier, ...] = (
    DailyModifier(
        "hot_grid", "HOT GRID", "Start at +20 grid alert.", start_alert=20,
    ),
    DailyModifier(
        "blackout", "BLACKOUT", "Start with 2 fewer CPU cycles.", start_cpu=-2,
    ),
    DailyModifier(
        "thin_ice", "THIN ICE", "Trace gain is 15% higher.", trace_multiplier=1.15,
    ),
    DailyModifier(
        "data_bloom", "DATA BLOOM", "Contract pay is 20% higher.", contract_multiplier=1.2,
    ),
)

MODIFIERS_BY_ID: Dict[str, DailyModifier] = {
    modifier.modifier_id: modifier for modifier in DAILY_MODIFIERS
}


def daily_modifier(day: Optional[date] = None) -> DailyModifier:
    """Return the deterministic modifier for a date."""
    current = day or date.today()
    return DAILY_MODIFIERS[current.toordinal() % len(DAILY_MODIFIERS)]


def modifier_by_id(modifier_id: str) -> Optional[DailyModifier]:
    """Return a modifier by id, or None for normal runs."""
    return MODIFIERS_BY_ID.get(str(modifier_id or ""))


def daily_key(day: Optional[date] = None) -> str:
    """Return the ISO date key for a daily run."""
    return (day or date.today()).isoformat()


def daily_seed(day: Optional[date] = None) -> int:
    """Return a stable numeric seed derived from the local date."""
    return int((day or date.today()).strftime("%Y%m%d"))


def daily_run(day: Optional[date] = None) -> Tuple[str, int]:
    """Return the (key, seed) pair for a daily run."""
    current = day or date.today()
    return current.isoformat(), int(current.strftime("%Y%m%d"))


def is_next_day(previous_key: str, current_key: str) -> bool:
    """Return True when current_key is exactly one calendar day after previous_key."""
    try:
        previous = date.fromisoformat(str(previous_key))
        current = date.fromisoformat(str(current_key))
    except (TypeError, ValueError):
        return False
    return (current - previous).days == 1
