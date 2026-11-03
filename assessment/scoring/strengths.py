"""Strengths scoring by win rate rather than raw hit count.

A strength's score is how often it was chosen out of how often it was offered.
The current pool offers every strength equally, but the scorer does not rely on
that: rank must never become a property of what the pool happened to contain.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..types import ModuleResult

DOMAINS = ("Doing", "Thinking", "People")
TOP_COUNT = 6
SUPPORTING_COUNT = 6
BOTTOM_COUNT = 5


def score(items: Sequence[dict], answers: dict[str, str], themes: dict) -> ModuleResult:
    exposure: dict[str, int] = {t: 0 for t in themes}
    wins: dict[str, int] = {t: 0 for t in themes}
    evidence: dict[str, list[dict]] = {t: [] for t in themes}

    for item in items:
        chosen = answers.get(item["id"])
        if chosen is None:
            continue
        offered = {
            option: [t for t in item["alignment"].get(option, []) if t in themes]
            for option in ("option_a", "option_b")
        }
        for option, tags in offered.items():
            for theme in tags:
                exposure[theme] += 1
                picked = option == chosen
                wins[theme] += 1 if picked else 0
                evidence[theme].append({
                    "id": item["id"],
                    "question": item["question"],
                    "text": item[option],
                    "chosen": picked,
                })

    rates: dict[str, float] = {}
    errors: dict[str, float] = {}
    for theme in themes:
        n = exposure[theme]
        if n == 0:
            rates[theme] = 0.0
            errors[theme] = 0.0
            continue
        p = wins[theme] / n
        rates[theme] = round(p, 4)
        errors[theme] = round(math.sqrt(p * (1 - p) / n), 4)

    ranking = sorted(
        themes,
        key=lambda t: (-rates[t], -wins[t], -exposure[t], t),
    )

    # Anything statistically level with the last top strength belongs in the
    # same cluster; claiming a clean cut-off over a tie would be false precision.
    tied_with_cutoff: list[str] = []
    if len(ranking) > TOP_COUNT:
        anchor = ranking[TOP_COUNT - 1]
        for theme in ranking[TOP_COUNT:]:
            pooled = math.sqrt(errors[anchor] ** 2 + errors[theme] ** 2)
            if pooled == 0 or abs(rates[anchor] - rates[theme]) <= pooled:
                tied_with_cutoff.append(theme)
            else:
                break

    domain_rates = {}
    for domain in DOMAINS:
        members = [t for t in themes if themes[t]["domain"] == domain]
        domain_rates[domain] = sum(rates[t] for t in members) / len(members) if members else 0.0
    total = sum(domain_rates.values())
    domain_pct = {
        d: round((v / total * 100.0) if total else 100.0 / len(DOMAINS), 1)
        for d, v in domain_rates.items()
    }

    return ModuleResult(
        module_id="strengths",
        summary={
            "ranking": ranking,
            "win_rates": rates,
            "wins": wins,
            "exposure": exposure,
            "standard_error": errors,
            "top": ranking[:TOP_COUNT],
            "supporting": ranking[TOP_COUNT:TOP_COUNT + SUPPORTING_COUNT],
            "bottom": ranking[-BOTTOM_COUNT:],
            "tied_with_cutoff": tied_with_cutoff,
            "domain_percentages": domain_pct,
        },
        detail={"evidence": evidence, "item_ids": [i["id"] for i in items]},
    )
