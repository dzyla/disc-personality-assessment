from __future__ import annotations

import random

from assessment import items as pools
from assessment.scoring import reliability


def _sample():
    return pools.sample_disc(random.Random(5))


def _coherent(items):
    """A clear profile: high on D, low on S, around the middle elsewhere."""
    level = {"D": 5, "I": 3, "S": 1, "C": 3}
    answers = {}
    for item in items:
        forward = level[item["style"]]
        answers[item["id"]] = 6 - forward if item["keyed"] < 0 else forward
    return answers


def _verdict(items, answers):
    return reliability.verdict(
        reliability.acquiescence(items, answers, "style"),
        reliability.split_half(items, answers, "style"),
        reliability.straight_lining([answers[i["id"]] for i in items]),
        reliability.profile_spread(items, answers, "style"),
    )


def test_agreeing_with_everything_is_reported_as_low_confidence():
    """The metric this replaced could not return a bad verdict at all."""
    items = _sample()
    verdict = _verdict(items, {i["id"]: 5 for i in items})
    assert verdict["level"] == "Low"
    assert verdict["acquiescence_mean"] < 0.5


def test_a_coherent_responder_is_reported_as_high_confidence():
    items = _sample()
    verdict = _verdict(items, _coherent(items))
    assert verdict["level"] == "High"
    assert not verdict["reasons"]


def test_random_answers_rarely_earn_high_confidence():
    """Without the spread check, about a quarter of random responders got High."""
    high = 0
    for seed in range(600):
        rng = random.Random(seed)
        items = pools.sample_disc(rng)
        high += _verdict(items, {i["id"]: rng.randint(1, 5) for i in items})["level"] == "High"
    assert high / 600 < 0.05


def test_profile_spread_separates_a_clear_profile_from_a_flat_one():
    items = _sample()
    assert reliability.profile_spread(items, _coherent(items), "style") > 10
    flat = {i["id"]: (3 + (1 if n % 2 else -1)) for n, i in enumerate(items)}
    assert reliability.profile_spread(items, flat, "style") < 3.5


def test_straight_lining_is_detected():
    assert reliability.straight_lining([3] * 12)["longest_run"] == 12
    assert reliability.straight_lining([1, 2, 1, 2, 1])["longest_run"] == 1
    assert reliability.straight_lining([4, 4, 4, 1, 2])["longest_run"] == 3


def test_acquiescence_scores_opposite_answers_as_consistent():
    items = [
        {"id": "a", "style": "D", "keyed": 1},
        {"id": "b", "style": "D", "keyed": -1},
    ]
    consistent = reliability.acquiescence(items, {"a": 5, "b": 1}, "style")
    assert consistent["D"] == 1.0
    inconsistent = reliability.acquiescence(items, {"a": 5, "b": 5}, "style")
    assert inconsistent["D"] == 0.0


def test_acquiescence_is_skipped_when_no_reverse_items_were_asked():
    items = [{"id": "a", "style": "D", "keyed": 1}]
    assert reliability.acquiescence(items, {"a": 5}, "style") == {}


def test_a_long_run_alone_is_not_treated_as_carelessness():
    """A genuine profile produces runs of neutral answers on items that do not
    load on its strong dimension. Only a long run with little spread counts."""
    # Neutral on I and C, and shown those items consecutively: a run of 20.
    items = sorted(_sample(), key=lambda i: "ICDS".index(i["style"]))
    answers = _coherent(items)
    lining = reliability.straight_lining([answers[i["id"]] for i in items])
    assert lining["longest_run"] >= 10 and lining["sd"] > 1.0
    assert _verdict(items, answers)["level"] == "High"


def test_a_flat_run_with_no_spread_is_flagged():
    items = _sample()
    verdict = _verdict(items, {i["id"]: 4 for i in items})
    assert verdict["level"] == "Low"
    assert any("in a row" in r for r in verdict["reasons"])
