"""Deterministic daily-run keys and seeds."""

from datetime import date
from typing import Optional, Tuple


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
