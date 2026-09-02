"""Pressure-mode scoring: how the person behaves when the load goes up."""

from __future__ import annotations

import math
from typing import Sequence

from ..types import ModuleResult, adjust

MODES = ("push", "perform", "accommodate", "retreat")

MODE_LABELS = {
    "push": "Push",
    "perform": "Perform",
    "accommodate": "Accommodate",
    "retreat": "Retreat",
}

MODE_BLURBS = {
    "push": "You take hold of the situation: faster decisions, blunter language, less patience for discussion.",
    "perform": "You turn outward: more talking, more selling, more visible involvement in the response.",
    "accommodate": "You absorb it: extra work taken on, objections kept private, your own limits deferred.",
    "retreat": "You pull inward: more analysis, higher standards, harder to reach while you work it through.",
}

# Which natural DISC style each pressure mode is the loaded form of.
MODE_TO_STYLE = {"push": "D", "perform": "I", "accommodate": "S", "retreat": "C"}


def score(items: Sequence[dict], answers: dict[str, int]) -> ModuleResult:
    scores: dict[str, float] = {}
    errors: dict[str, float] = {}
    evidence: dict[str, list[dict]] = {}

    for mode in MODES:
        rows = [i for i in items if i["mode"] == mode and i["id"] in answers]
        if not rows:
            scores[mode] = 50.0
            errors[mode] = 0.0
            evidence[mode] = []
            continue
        adjusted = [adjust(answers[i["id"]], i["keyed"]) for i in rows]
        mean = sum(adjusted) / len(adjusted)
        scores[mode] = round((mean - 1) / 4 * 100.0, 1)
        if len(adjusted) > 1:
            var = sum((a - mean) ** 2 for a in adjusted) / (len(adjusted) - 1)
            errors[mode] = round(math.sqrt(var / len(adjusted)) / 4 * 100.0, 1)
        else:
            errors[mode] = 0.0
        evidence[mode] = sorted(
            (
                {
                    "id": i["id"],
                    "question": i["question"],
                    "response": answers[i["id"]],
                    "reverse": i["keyed"] < 0,
                }
                for i in rows
            ),
            key=lambda r: abs(adjust(r["response"], -1 if r["reverse"] else 1) - 3),
            reverse=True,
        )[:4]

    ranked = sorted(MODES, key=lambda m: scores[m], reverse=True)
    return ModuleResult(
        module_id="stress",
        summary={
            "scores": scores,
            "standard_error": errors,
            "dominant": ranked[0],
            "ranking": ranked,
        },
        detail={"evidence": evidence, "item_ids": [i["id"] for i in items]},
    )
