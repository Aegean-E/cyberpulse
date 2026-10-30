"""Deterministic rival-netrunner generation."""

import random
from typing import Tuple

from cyberpulse.models import RivalNetrunner

RIVAL_ROSTER: Tuple[Tuple[str, str, int, str], ...] = (
    (
        "Vex",
        "vex_01",
        3,
        "A razor-thin ghost who treats every contract as a personal auction.",
    ),
    (
        "Marrow",
        "marrow",
        2,
        "A patient cold-storage specialist who never leaves a clean extraction.",
    ),
    (
        "Static",
        "static_9",
        1,
        "A loud street runner whose botnet makes up for what finesse lacks.",
    ),
)


def generate_rival(seed: int) -> RivalNetrunner:
    """Create the run's rival from a deterministic seed stream."""
    rng = random.Random(int(seed) ^ 0x5A17)
    name, handle, skill, tagline = rng.choice(RIVAL_ROSTER)
    return RivalNetrunner(
        name=name,
        handle=handle,
        skill=skill,
        tagline=tagline,
        next_move_turn=6 + rng.randint(0, 2),
    )
