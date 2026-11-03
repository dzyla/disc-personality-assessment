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
        forward = 5 if item["style"] == style else 3
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


def test_an_item_counts_only_toward_its_own_style():
    items = _sample()
    answers = {i["id"]: (5 if i["style"] == "D" and i["keyed"] > 0 else 1 if i["style"] == "D" else 3) for i in items}
    normalized = disc.score(items, answers).summary["normalized"]
    assert normalized["D"] == 100.0
    assert normalized["I"] == normalized["S"] == normalized["C"] == 50.0


def test_scoring_does_not_build_in_correlations_between_styles():
    """Random answers have no real relationship between styles, so scores must
    show none. Hand-set cross-weights used to produce about -0.5 for D and S."""
    import numpy as np

    rows = []
    for seed in range(600):
        rng = random.Random(seed)
        items = pools.sample_disc(rng)
        score = disc.score(items, {i["id"]: rng.randint(1, 5) for i in items}).summary["normalized"]
        rows.append([score[s] for s in "DISC"])
    corr = np.corrcoef(np.array(rows).T)
    off_diagonal = corr[np.triu_indices(4, 1)]
    assert np.abs(off_diagonal).max() < 0.15, off_diagonal


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
