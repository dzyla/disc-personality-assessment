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


def test_stratified_sampling_equalises_theme_exposure():
    """The raw pool ranges from 9 to 41 appearances per theme. A drawn set must
    be far tighter than that or the ranking measures the pool, not the person."""
    counts = _exposure(pools.sample_strengths(random.Random(1), 35))
    assert len(counts) == len(pools.strengths_themes())
    assert max(counts.values()) - min(counts.values()) <= 4


def test_deep_variant_raises_exposure_for_everyone():
    standard = _exposure(pools.sample_strengths(random.Random(2), 35))
    deep = _exposure(pools.sample_strengths(random.Random(2), 60))
    assert min(deep.values()) > min(standard.values())


def test_sampling_is_deterministic_for_a_seed():
    first = [i["id"] for i in pools.sample_strengths(random.Random(9), 35)]
    second = [i["id"] for i in pools.sample_strengths(random.Random(9), 35)]
    assert first == second
    assert first != [i["id"] for i in pools.sample_strengths(random.Random(10), 35)]


def test_disc_sample_is_balanced_and_mixes_keying():
    for seed in range(5):
        sample = pools.sample_disc(random.Random(seed))
        per_style = collections.Counter(i["style"] for i in sample)
        assert set(per_style.values()) == {10}
        for style in pools.STYLES:
            keyings = {i["keyed"] for i in sample if i["style"] == style}
            assert keyings == {1, -1}, f"{style} sample has only {keyings}"


def test_rebuild_from_ids_restores_order():
    sample = pools.sample_disc(random.Random(3))
    ids = [i["id"] for i in sample]
    rebuilt = pools.rebuild_from_ids("disc_natural", "disc", ids)
    assert [i.source_id for i in rebuilt] == ids
