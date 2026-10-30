"""Faction standing normalization and bounded reputation bonuses."""

from typing import Any, Dict

FACTIONS = ("syndicate", "street")
MAX_STANDING = 100
SYNDICATE_PAY_PER_POINT = 0.01
SYNDICATE_PAY_CAP = 0.20
STREET_SHOP_PER_POINT = 0.01
STREET_SHOP_CAP = 0.15


def normalize_standing(data: Any) -> Dict[str, int]:
    """Return a clean two-faction standing map with non-negative capped integers."""
    source = data if isinstance(data, dict) else {}
    clean: Dict[str, int] = {}
    for faction in FACTIONS:
        value = source.get(faction, 0)
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = 0
        if isinstance(value, bool):
            number = 0
        clean[faction] = max(0, min(MAX_STANDING, number))
    return clean


def update_standing(standing: Any, faction: str, delta: int) -> Dict[str, int]:
    """Add reputation to one faction and return a normalized copy."""
    clean = normalize_standing(standing)
    if faction in clean:
        try:
            amount = int(delta)
        except (TypeError, ValueError):
            amount = 0
        clean[faction] = max(0, min(MAX_STANDING, clean[faction] + amount))
    return clean


def contract_bonus(standing: Any) -> float:
    """Return the Syndicate contract-pay bonus (1% per point, capped at 20%)."""
    clean = normalize_standing(standing)
    return min(SYNDICATE_PAY_CAP, clean["syndicate"] * SYNDICATE_PAY_PER_POINT)


def street_discount(standing: Any) -> float:
    """Return the Street Black Market discount (1% per point, capped at 15%)."""
    clean = normalize_standing(standing)
    return min(STREET_SHOP_CAP, clean["street"] * STREET_SHOP_PER_POINT)
