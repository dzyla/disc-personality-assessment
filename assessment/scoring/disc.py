"""DISC scoring with per-dimension standard errors.

The scores are reported with a confidence interval and, crucially, the ordering
of dimensions is only asserted when the gap survives a test against the
uncertainty in both estimates. A 40-item instrument does not support the
one-decimal certainty the previous version printed.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..types import ModuleResult, adjust

STYLES = ("D", "I", "S", "C")

# Circumplex placement: D upper-right through C lower-left, matching the plot.
STYLE_ANGLES = {
    "D": 7 * math.pi / 4,
    "I": math.pi / 4,
    "S": 3 * math.pi / 4,
    "C": 5 * math.pi / 4,
}

STYLE_NAMES = {
    "D": "Dominance",
    "I": "Influence",
    "S": "Steadiness",
    "C": "Conscientiousness",
}

_SECTORS = [
    (300, 330, "D"), (330, 360, "DI"), (0, 30, "ID"), (30, 60, "I"),
    (60, 90, "IS"), (90, 120, "SI"), (120, 150, "S"), (150, 180, "SC"),
    (180, 210, "CS"), (210, 240, "C"), (240, 270, "CD"), (270, 300, "DC"),
]


def _sd(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))


def contributions(items: Sequence[dict], answers: dict[str, int], style: str) -> list[dict]:
    """Per-item signed contribution to one dimension, largest influence first."""
    out = []
    for item in items:
        weight = item["mapping"].get(style, 0)
        if weight == 0 or item["id"] not in answers:
            continue
        response = answers[item["id"]]
        value = weight * (adjust(response, item["keyed"]) - 3)
        out.append({
            "id": item["id"],
            "question": item["question"],
            "response": response,
            "reverse": item["keyed"] < 0,
            "weight": weight,
            "contribution": value,
        })
    out.sort(key=lambda c: abs(c["contribution"]), reverse=True)
    return out


def separation(a: float, b: float, se_a: float, se_b: float) -> dict:
    """Is the gap between two dimension scores bigger than the noise in them?"""
    diff = abs(a - b)
    se = math.sqrt(se_a ** 2 + se_b ** 2)
    if se == 0:
        return {"difference": round(diff, 1), "z": None, "separated": diff > 0}
    z = diff / se
    return {"difference": round(diff, 1), "z": round(z, 2), "separated": z >= 1.96}


def score(items: Sequence[dict], answers: dict[str, int]) -> ModuleResult:
    normalized: dict[str, float] = {}
    errors: dict[str, float] = {}
    evidence: dict[str, list[dict]] = {}

    for style in STYLES:
        contribs = contributions(items, answers, style)
        evidence[style] = contribs[:5]
        # Each contribution lies in [-2|w|, +2|w|], so the raw total spans
        # [-reach, +reach] and the full range is twice that.
        reach = sum(2 * abs(c["weight"]) for c in contribs)
        raw = sum(c["contribution"] for c in contribs)
        if reach == 0:
            normalized[style] = 50.0
            errors[style] = 0.0
            continue
        full_range = 2 * reach
        normalized[style] = round(max(0.0, min(100.0, (raw + reach) / full_range * 100.0)), 1)
        # SE of a sum of n item contributions, expressed on the 0-100 scale.
        se_raw = _sd([c["contribution"] for c in contribs]) * math.sqrt(len(contribs))
        errors[style] = round(se_raw / full_range * 100.0, 1)

    ordered = sorted(STYLES, key=lambda s: normalized[s], reverse=True)
    primary, secondary, lowest = ordered[0], ordered[1], ordered[-1]

    x = sum(normalized[s] / 100.0 * math.cos(STYLE_ANGLES[s]) for s in STYLES)
    y = sum(normalized[s] / 100.0 * math.sin(STYLE_ANGLES[s]) for s in STYLES)
    magnitude = math.hypot(x, y)
    angle = math.atan2(y, x) % (2 * math.pi)
    degrees = math.degrees(angle)

    if magnitude >= 0.55:
        intensity = "Pronounced"
    elif magnitude >= 0.25:
        intensity = "Moderate"
    else:
        intensity = "Situational"

    if magnitude < 0.15:
        style_code = "balanced"
    else:
        style_code = next((c for lo, hi, c in _SECTORS if lo <= degrees < hi), "D")

    pace = round((normalized["D"] + normalized["I"] - normalized["S"] - normalized["C"]) / 2.0, 1)
    focus = round((normalized["I"] + normalized["S"] - normalized["D"] - normalized["C"]) / 2.0, 1)

    return ModuleResult(
        module_id="disc",
        summary={
            "normalized": normalized,
            "standard_error": errors,
            "primary": primary,
            "secondary": secondary,
            "lowest": lowest,
            "style_code": style_code,
            "intensity": intensity,
            "magnitude": round(magnitude, 3),
            "angle_degrees": round(degrees, 1),
            "pace": pace,
            "focus": focus,
        },
        detail={
            "evidence": evidence,
            "primary_vs_secondary": separation(
                normalized[primary], normalized[secondary], errors[primary], errors[secondary]
            ),
            "ranking": ordered,
            "item_ids": [i["id"] for i in items],
        },
    )


def strain(natural, adaptive) -> dict:
    """Distance between the natural and the at-work profile.

    A large gap on a dimension means the role is asking for behaviour the person
    does not produce by default. That is not automatically bad — it is the cost
    of the job, and worth knowing the size of.
    """
    n, a = natural.summary["normalized"], adaptive.summary["normalized"]
    n_se, a_se = natural.summary["standard_error"], adaptive.summary["standard_error"]
    shifts = {}
    for style in STYLES:
        delta = a[style] - n[style]
        pooled = math.sqrt(n_se[style] ** 2 + a_se[style] ** 2)
        shifts[style] = {
            "natural": n[style],
            "adaptive": a[style],
            "delta": round(delta, 1),
            "significant": bool(pooled > 0 and abs(delta) / pooled >= 1.96),
        }
    total = sum(abs(v["delta"]) for v in shifts.values()) / len(STYLES)
    if total >= 15:
        band = "high"
    elif total >= 7:
        band = "moderate"
    else:
        band = "low"
    largest = max(STYLES, key=lambda s: abs(shifts[s]["delta"]))
    return {"shifts": shifts, "index": round(total, 1), "band": band, "largest": largest}
