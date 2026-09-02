from __future__ import annotations

import random

from assessment import items as pools
from assessment.scoring import disc


def _sample():
    return pools.sample_disc(random.Random(3))


def _coherent(items, style="D"):
    """Someone with a genuine, consistently reported lean on one dimension."""
    answers = {}
    for item in items:
        forward = {2: 5, 1: 4, 0: 3, -1: 2}.get(item["mapping"].get(style, 0), 3)
        answers[item["id"]] = 6 - forward if item["keyed"] < 0 else forward
    return answers


def test_scores_stay_inside_the_reported_scale():
    items = _sample()
    for style in "DISC":
        result = disc.score(items, _coherent(items, style))
        for value in result.summary["normalized"].values():
            assert 0.0 <= value <= 100.0


def test_a_coherent_responder_leads_on_the_dimension_they_reported():
    items = _sample()
    for style in "DISC":
        result = disc.score(items, _coherent(items, style))
        assert result.summary["primary"] == style


def test_reverse_keyed_items_actually_flip():
    """Agreeing with a reverse item must push the dimension down, not up."""
    item = next(i for i in pools.disc_items() if i["keyed"] < 0 and i["style"] == "D")
    agree = disc.score([item], {item["id"]: 5}).summary["normalized"]["D"]
    disagree = disc.score([item], {item["id"]: 1}).summary["normalized"]["D"]
    assert agree < disagree


def test_uniform_answers_produce_a_flat_profile_with_no_confidence_in_the_order():
    items = _sample()
    result = disc.score(items, {i["id"]: 3 for i in items})
    assert set(result.summary["normalized"].values()) == {50.0}
    assert not result.detail["primary_vs_secondary"]["separated"]


def test_close_dimensions_are_not_claimed_as_separate():
    close = disc.separation(52.0, 50.0, 6.0, 6.0)
    assert not close["separated"]
    clear = disc.separation(85.0, 40.0, 5.0, 5.0)
    assert clear["separated"]


def test_evidence_cites_the_items_that_moved_the_score():
    items = _sample()
    result = disc.score(items, _coherent(items, "D"))
    evidence = result.detail["evidence"]["D"]
    assert evidence
    ids = {i["id"] for i in items}
    for entry in evidence:
        assert entry["id"] in ids
        assert "question" in entry and "response" in entry


def test_strain_flags_only_moves_larger_than_the_error():
    items = _sample()
    natural = disc.score(items, _coherent(items, "D"))
    same = disc.score(items, _coherent(items, "D"))
    unchanged = disc.strain(natural, same)
    assert unchanged["index"] == 0.0
    assert not any(s["significant"] for s in unchanged["shifts"].values())

    shifted = disc.score(items, _coherent(items, "S"))
    moved = disc.strain(natural, shifted)
    assert moved["band"] == "high"
    assert any(s["significant"] for s in moved["shifts"].values())
