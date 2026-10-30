"""Difficulty normalization and run modifiers."""

from typing import Any

DIFFICULTIES = ("easy", "normal", "hard")

TRACE_MULTIPLIERS = {"easy": 0.8, "normal": 1.0, "hard": 1.2}
CONTRACT_MULTIPLIERS = {"easy": 1.1, "normal": 1.0, "hard": 0.9}


def normalize_difficulty(value: Any = "normal") -> str:
    """Return a supported difficulty key, defaulting invalid input to normal."""
    key = str(value or "").strip().lower()
    return key if key in DIFFICULTIES else "normal"


def trace_multiplier(difficulty: Any = "normal") -> float:
    """Return the trace gain multiplier for a difficulty."""
    return TRACE_MULTIPLIERS[normalize_difficulty(difficulty)]


def contract_multiplier(difficulty: Any = "normal") -> float:
    """Return the contract payout multiplier for a difficulty."""
    return CONTRACT_MULTIPLIERS[normalize_difficulty(difficulty)]
