"""Career milestone catalog and settlement-time evaluation."""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from cyberpulse.models import CareerProfile, NodeStatus, NodeType


@dataclass(frozen=True)
class Achievement:
    """A permanent career milestone shown in the dossier."""

    achievement_id: str
    name: str
    description: str


ACHIEVEMENTS: Tuple[Achievement, ...] = (
    Achievement("first_extraction", "First Extraction", "Clear your first successful run."),
    Achievement("veteran", "Veteran", "Clear five successful runs."),
    Achievement("combo_adept", "Combo Adept", "Reach a x5 breach combo in one run."),
    Achievement("combo_legend", "Combo Legend", "Reach a x10 breach combo in one run."),
    Achievement("ghost_protocol", "Ghost Protocol", "Win with trace at or below 25%."),
    Achievement("speed_run", "Speed Run", "Win in 25 turns or fewer."),
    Achievement("black_contract", "Black Contract", "Complete a black-tier Syndicate contract."),
    Achievement("vault_runner", "Vault Runner", "Breach three data vaults in one run."),
    Achievement("deep_dive", "Deep Dive", "Survive 50 turns in one run."),
    Achievement("high_roller", "High Roller", "Bank 1,000 credits."),
    Achievement("hot_extraction", "Hot Extraction", "Jack out at 85% trace or higher."),
    Achievement("full_story", "Full Story", "Reach Act V."),
    Achievement("hard_clear", "Hard Clear", "Win a run on Hard difficulty."),
    Achievement("daily_devotion", "Daily Devotion", "Reach a 7-day daily streak."),
    Achievement("daily_legend", "Daily Legend", "Reach a 30-day daily streak."),
    Achievement("faction_insider", "Faction Insider", "Reach 10 standing with the Syndicate or Street."),
)

BY_ID: Dict[str, Achievement] = {entry.achievement_id: entry for entry in ACHIEVEMENTS}


def achievement_name(achievement_id: str) -> str:
    """Return a display name, falling back to the raw identifier."""
    entry = BY_ID.get(str(achievement_id))
    return entry.name if entry else str(achievement_id)


def achievement_status(profile: CareerProfile) -> List[Dict[str, Any]]:
    """Return the catalog annotated with this profile's unlocked state."""
    unlocked = set(profile.achievements or [])
    return [
        {
            "achievement_id": entry.achievement_id,
            "name": entry.name,
            "description": entry.description,
            "unlocked": entry.achievement_id in unlocked,
        }
        for entry in ACHIEVEMENTS
    ]


def achievement_names(achievement_ids: Iterable[str]) -> List[str]:
    """Map stored identifiers to display names in catalog order."""
    wanted = set(achievement_ids)
    return [entry.name for entry in ACHIEVEMENTS if entry.achievement_id in wanted]


def evaluate_achievements(engine: Any, profile: CareerProfile) -> List[str]:
    """Return newly earned milestone identifiers for a settled run.

    Must run after the profile counters have been updated and only from the
    one-shot settlement path, so a run cannot farm achievements by re-settling.
    """
    earned = set(profile.achievements or [])
    new_ids: List[str] = []

    def unlock(achievement_id: str) -> None:
        if achievement_id in BY_ID and achievement_id not in earned:
            earned.add(achievement_id)
            new_ids.append(achievement_id)

    if profile.successful_runs >= 1:
        unlock("first_extraction")
    if profile.successful_runs >= 5:
        unlock("veteran")
    if engine.state.best_combo >= 5:
        unlock("combo_adept")
    if engine.state.best_combo >= 10:
        unlock("combo_legend")
    if engine.state.is_victory and engine.state.trace_percent <= 25:
        unlock("ghost_protocol")
    if engine.state.is_victory and engine.state.turns_elapsed <= 25:
        unlock("speed_run")

    contract = engine.state.active_contract
    if (
        contract
        and getattr(contract, "completed", False)
        and getattr(contract, "risk_tier", "") == "black"
    ):
        unlock("black_contract")

    vaults = sum(
        1
        for node in engine.nodes.values()
        if getattr(node, "node_type", None) == NodeType.DATA_VAULT
        and getattr(node, "status", None) == NodeStatus.BREACHED
    )
    if vaults >= 3:
        unlock("vault_runner")
    if engine.state.turns_elapsed >= 50:
        unlock("deep_dive")
    if engine.deck.cryptocreds >= 1000:
        unlock("high_roller")
    if engine.state.is_jacked_out and engine.state.trace_percent >= 85:
        unlock("hot_extraction")
    if engine.state.story_act >= 5:
        unlock("full_story")
    if engine.state.is_victory and getattr(engine, "difficulty", "normal") == "hard":
        unlock("hard_clear")
    if int(getattr(profile, "daily_streak", 0) or 0) >= 7:
        unlock("daily_devotion")
    if int(getattr(profile, "best_daily_streak", 0) or 0) >= 30:
        unlock("daily_legend")
    standing = getattr(profile, "faction_standing", {}) or {}
    if max(
        int(standing.get("syndicate", 0) or 0),
        int(standing.get("street", 0) or 0),
    ) >= 10:
        unlock("faction_insider")
    return new_ids
