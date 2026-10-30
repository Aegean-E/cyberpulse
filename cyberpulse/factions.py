"""Faction standing normalization and bounded reputation bonuses."""

from typing import Any, Dict

FACTIONS = ("syndicate", "street")
MAX_STANDING = 100
RANKS = {
    "syndicate": (
        (0, "Associate", 0),
        (10, "Fixer", 100),
        (25, "Broker", 250),
        (50, "Kingpin", 500),
    ),
    "street": (
        (0, "Lookout", 0),
        (10, "Runner", 100),
        (25, "Ghost", 250),
        (50, "Legend", 500),
    ),
}
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


def rank_for(faction: str, standing: Any) -> tuple:
    """Return (rank index, rank name, promotion reward) for a faction standing."""
    clean = normalize_standing({faction: (standing if not isinstance(standing, dict) else standing.get(faction, 0))})
    value = clean.get(faction, 0)
    table = RANKS.get(faction, RANKS["syndicate"])
    current = table[0]
    for index, entry in enumerate(table):
        if value >= entry[0]:
            current = (index, entry[1], entry[2])
    return current


def rank_up_reward(faction: str, old_standing: Any, new_standing: Any) -> tuple:
    """Return (rank name, reward) when a settlement crosses a rank threshold."""
    old_index = rank_for(faction, old_standing)[0]
    new_index, name, reward = rank_for(faction, new_standing)
    if new_index <= old_index:
        return None, 0
    return name, reward


def contract_bonus(standing: Any) -> float:
    """Return the Syndicate contract-pay bonus (1% per point, capped at 20%)."""
    clean = normalize_standing(standing)
    return min(SYNDICATE_PAY_CAP, clean["syndicate"] * SYNDICATE_PAY_PER_POINT)


def street_discount(standing: Any) -> float:
    """Return the Street Black Market discount (1% per point, capped at 15%)."""
    clean = normalize_standing(standing)
    return min(STREET_SHOP_CAP, clean["street"] * STREET_SHOP_PER_POINT)
