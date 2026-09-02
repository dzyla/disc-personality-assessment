"""Response-quality checks that can actually return a bad verdict.

The metric this replaces was ``82 + variance * 8.5`` clamped to 75-99, which
could only ever report that the person had been consistent. Everything here is
computable from a single respondent's answers, which rules out the classical
sample-based coefficients (Cronbach's alpha needs variance across people, not
across items within one person).
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from ..types import adjust


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx, my = _mean(xs), _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def acquiescence(items: Sequence[dict], answers: dict[str, int], group_key: str) -> dict[str, float]:
    """Agreement between forward- and reverse-keyed items of the same construct.

    Someone who agrees both that they take charge and that they defer is not
    expressing a strong style, they are agreeing with whatever is put in front
    of them. A consistent responder's forward and reverse raw means sum to
    roughly 6; the deviation from 6 is the inconsistency, scaled by its maximum
    of 4.
    """
    out: dict[str, float] = {}
    groups = sorted({item[group_key] for item in items})
    for group in groups:
        forward = [answers[i["id"]] for i in items if i[group_key] == group and i["keyed"] > 0 and i["id"] in answers]
        reverse = [answers[i["id"]] for i in items if i[group_key] == group and i["keyed"] < 0 and i["id"] in answers]
        if not forward or not reverse:
            continue
        deviation = abs(_mean(forward) + _mean(reverse) - 6.0)
        out[group] = round(max(0.0, 1.0 - deviation / 4.0), 3)
    return out


def split_half(items: Sequence[dict], answers: dict[str, int], group_key: str) -> float | None:
    """Spearman-Brown corrected agreement between two halves of the instrument.

    Each half produces its own profile across the constructs; a person answering
    from a stable self-view produces the same shape twice.
    """
    groups = sorted({item[group_key] for item in items})
    first: list[float] = []
    second: list[float] = []
    for group in groups:
        scored = [
            adjust(answers[i["id"]], i["keyed"])
            for i in items
            if i[group_key] == group and i["id"] in answers
        ]
        if len(scored) < 2:
            return None
        first.append(_mean(scored[0::2]))
        second.append(_mean(scored[1::2]))
    r = _pearson(first, second)
    if r is None:
        return None
    if r <= -1.0:
        return -1.0
    corrected = (2 * r) / (1 + r) if r > -1 else -1.0
    return round(max(-1.0, min(1.0, corrected)), 3)


def straight_lining(responses: Iterable[int]) -> dict[str, float]:
    """Longest identical run and overall spread, for detecting careless answering."""
    values = list(responses)
    if not values:
        return {"longest_run": 0, "sd": 0.0}
    longest = run = 1
    for prev, cur in zip(values, values[1:]):
        run = run + 1 if cur == prev else 1
        longest = max(longest, run)
    mean = _mean(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    return {"longest_run": longest, "sd": round(sd, 3)}


def verdict(acq: dict[str, float], half: float | None, lining: dict[str, float]) -> dict:
    """High / Moderate / Low confidence, with the reasons that drove it."""
    reasons: list[str] = []
    acq_mean = _mean(list(acq.values())) if acq else None

    if acq_mean is not None and acq_mean < 0.50:
        reasons.append(
            "Your answers to positively and negatively worded versions of the same trait "
            "pointed the same way, which usually means the wording was carrying the answer "
            "more than the content."
        )
    # A long run alone is weak evidence: a real profile answering "neutral" to a
    # run of items that do not load on their strong dimension produces one
    # honestly. It only indicates careless answering when the spread is low too.
    if lining["longest_run"] >= 10 and lining["sd"] < 1.0:
        reasons.append(
            f"You gave the same response {lining['longest_run']} times in a row, "
            f"with little variation elsewhere."
        )
    if lining["sd"] < 0.40:
        reasons.append("Almost every answer was the same value, so there is little to tell the dimensions apart.")
    if half is not None and half < 0.30:
        reasons.append("The first and second halves of the questionnaire produced noticeably different profiles.")

    if reasons:
        level = "Low"
    elif (acq_mean is None or acq_mean >= 0.72) and (half is None or half >= 0.65):
        level = "High"
    else:
        level = "Moderate"

    return {
        "level": level,
        "reasons": reasons,
        "acquiescence": acq,
        "acquiescence_mean": round(acq_mean, 3) if acq_mean is not None else None,
        "split_half": half,
        "longest_run": lining["longest_run"],
        "response_sd": lining["sd"],
    }
