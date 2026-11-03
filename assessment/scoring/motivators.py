"""Motivator scoring over a round-robin of forced-choice pairs.

Every driver meets every other driver exactly once, so exposure is equal by
construction and the win rate needs no correction.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..types import ModuleResult

DRIVERS = (
    "Autonomy", "Mastery", "Recognition", "Security",
    "Purpose", "Connection", "Status", "Variety",
)

DRIVER_BLURBS = {
    "Autonomy": "Room to choose your own approach and be judged on the outcome.",
    "Mastery": "Getting demonstrably better at something hard.",
    "Recognition": "Specific, personal credit from people whose judgement you respect.",
    "Security": "A stable floor: predictable demands and a role that will still be there.",
    "Purpose": "Work whose point you believe in outside of work.",
    "Connection": "Belonging to a group of people you genuinely like working with.",
    "Status": "Standing and influence over decisions that matter.",
    "Variety": "Enough change that the problem keeps being interesting.",
}


def score(items: Sequence[dict], answers: dict[str, str]) -> ModuleResult:
    wins = {d: 0 for d in DRIVERS}
    exposure = {d: 0 for d in DRIVERS}
    evidence = {d: [] for d in DRIVERS}

    for item in items:
        chosen = answers.get(item["id"])
        if chosen is None:
            continue
        for option in ("option_a", "option_b"):
            driver = item["alignment"][option]
            if driver not in wins:
                continue
            exposure[driver] += 1
            picked = option == chosen
            wins[driver] += 1 if picked else 0
            other = item["alignment"]["option_b" if option == "option_a" else "option_a"]
            evidence[driver].append({
                "id": item["id"],
                "text": item[option],
                "against": other,
                "chosen": picked,
            })

    rates = {
        d: round(wins[d] / exposure[d], 4) if exposure[d] else 0.0 for d in DRIVERS
    }
    errors = {
        d: round(math.sqrt(rates[d] * (1 - rates[d]) / exposure[d]), 4) if exposure[d] else 0.0
        for d in DRIVERS
    }
    ranking = sorted(DRIVERS, key=lambda d: (-rates[d], d))

    return ModuleResult(
        module_id="motivators",
        summary={
            "win_rates": rates,
            "wins": wins,
            "exposure": exposure,
            "standard_error": errors,
            "ranking": ranking,
            "top": ranking[:3],
            "bottom": ranking[-2:],
        },
        detail={"evidence": evidence, "item_ids": [i["id"] for i in items]},
    )
