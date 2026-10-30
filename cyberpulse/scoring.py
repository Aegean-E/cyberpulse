"""Transparent run scoring for legacy and Hall of Fame rankings."""

from typing import Any, Dict


def score_run(
    *,
    gained: int,
    best_combo: int,
    quests_done: int,
    nodes_breached: int,
    outcome: str,
    contract_completed: bool,
    main_story_complete: bool,
) -> Dict[str, Any]:
    """Return a score and its itemized breakdown for one settled run."""
    breakdown = {
        "credits": max(0, int(gained)),
        "combo": max(0, int(best_combo)) * 75,
        "quests": max(0, int(quests_done)) * 150,
        "breaches": max(0, int(nodes_breached)) * 25,
        "contract": 200 if contract_completed else 0,
        "outcome": 500 if outcome == "victory" else (250 if outcome == "jackout" else 0),
        "story": 100 if main_story_complete else 0,
    }
    return {"score": sum(breakdown.values()), "breakdown": breakdown}
