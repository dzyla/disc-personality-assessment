from __future__ import annotations

import collections
import random

from assessment import items as pools


def _exposure(sample):
    counts = collections.Counter()
    for item in sample:
        for option in ("option_a", "option_b"):
            for theme in pools.option_themes(item, option):
                counts[theme] += 1
    return counts


def test_every_strength_is_offered_exactly_equally():
    for count, offers in ((72, 6), (132, 11)):
        for seed in range(10):
            counts = _exposure(pools.sample_strengths(random.Random(seed), count))
            assert len(counts) == len(pools.strengths_themes())
            assert set(counts.values()) == {offers}


def test_a_draw_never_repeats_a_statement_or_a_pair():
    for count in (72, 132):
        for seed in range(25):
            sample = pools.sample_strengths(random.Random(seed), count)
            assert len(sample) == count
            statements = [i[o] for i in sample for o in ("option_a", "option_b")]
            assert len(statements) == len(set(statements))
            pairs = [frozenset(i["alignment"]["option_a"] + i["alignment"]["option_b"]) for i in sample]
            assert len(pairs) == len(set(pairs))


def test_retakes_draw_different_questions():
    first = {i["id"] for i in pools.sample_strengths(random.Random(1), 72)}
    second = {i["id"] for i in pools.sample_strengths(random.Random(2), 72)}
    assert first != second


def test_an_unworkable_length_is_refused():
    import pytest

    with pytest.raises(ValueError):
        pools.sample_strengths(random.Random(1), 35)


def test_sampling_is_deterministic_for_a_seed():
    first = [i["id"] for i in pools.sample_strengths(random.Random(9), 72)]
    second = [i["id"] for i in pools.sample_strengths(random.Random(9), 72)]
    assert first == second
    assert first != [i["id"] for i in pools.sample_strengths(random.Random(10), 72)]


def test_a_disc_draw_never_contains_both_mirrored_twins():
    for seed in range(100):
        sample = pools.sample_disc(random.Random(seed))
        ids = {i["id"] for i in sample}
        assert not any(i.get("twin") in ids for i in sample)


def test_disc_sample_is_balanced_and_mixes_keying():
    for seed in range(5):
        sample = pools.sample_disc(random.Random(seed))
        per_style = collections.Counter(i["style"] for i in sample)
        assert set(per_style.values()) == {10}
        for style in pools.STYLES:
            keyings = {i["keyed"] for i in sample if i["style"] == style}
            assert keyings == {1, -1}, f"{style} sample has only {keyings}"
            assert sum(i["keyed"] < 0 for i in sample if i["style"] == style) == 5


def test_rebuild_from_ids_restores_order():
    sample = pools.sample_disc(random.Random(3))
    ids = [i["id"] for i in sample]
    rebuilt = pools.rebuild_from_ids("disc_natural", "disc", ids)
    assert [i.source_id for i in rebuilt] == ids
