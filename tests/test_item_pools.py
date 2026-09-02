"""Data-integrity checks. Three tags in the original strengths pool resolved to
no theme and were silently discarded at scoring time; these tests make that
class of bug impossible to reintroduce."""

from __future__ import annotations

import collections

from assessment import items as pools
from assessment.scoring.motivators import DRIVERS
from assessment.scoring.stress import MODES


def test_every_strengths_tag_resolves_to_a_theme():
    themes = set(pools.strengths_themes())
    tags = {
        tag
        for item in pools.strengths_items()
        for option in ("option_a", "option_b")
        for tag in pools.option_themes(item, option)
    }
    assert not tags - themes, f"tags with no theme: {sorted(tags - themes)}"


def test_every_theme_is_reachable():
    themes = set(pools.strengths_themes())
    offered = {
        tag
        for item in pools.strengths_items()
        for option in ("option_a", "option_b")
        for tag in pools.option_themes(item, option)
    }
    assert not themes - offered, f"themes never offered: {sorted(themes - offered)}"


def test_no_strengths_option_is_untagged():
    for item in pools.strengths_items():
        for option in ("option_a", "option_b"):
            assert pools.option_themes(item, option), f"{item['id']} {option} has no theme"


def test_every_theme_has_a_cost_written():
    for name, theme in pools.strengths_themes().items():
        assert theme.get("shadow"), f"{name} has no shadow text"
        assert theme.get("overuse"), f"{name} has no overuse text"


def test_disc_items_are_keyed_and_balanced():
    items = pools.disc_items()
    per_style = collections.Counter(item["style"] for item in items)
    assert set(per_style) == set(pools.STYLES)
    assert len(set(per_style.values())) == 1, f"unbalanced pool: {per_style}"
    for item in items:
        assert item["keyed"] in (1, -1), f"{item['id']} is not keyed"
        assert item["mapping"].get(item["style"], 0) > 0


def test_every_dimension_has_reverse_keyed_items():
    reverse = collections.Counter(
        item["style"] for item in pools.disc_items() if item["keyed"] < 0
    )
    for style in pools.STYLES:
        assert reverse[style] >= 3, f"{style} has too few reverse items for a consistency check"


def test_no_duplicate_stems_or_ids():
    for pool in (pools.disc_items(), pools.stress_items()):
        stems = [item["question"].strip().lower() for item in pool]
        assert len(stems) == len(set(stems))
        ids = [item["id"] for item in pool]
        assert len(ids) == len(set(ids))


def test_stress_pool_shape():
    modes = collections.Counter(item["mode"] for item in pools.stress_items())
    assert set(modes) == set(MODES)
    assert len(set(modes.values())) == 1
    for mode in MODES:
        reverse = [i for i in pools.stress_items() if i["mode"] == mode and i["keyed"] < 0]
        assert reverse, f"{mode} has no reverse-keyed item"


def test_motivator_round_robin_is_complete():
    pairs = set()
    exposure = collections.Counter()
    for item in pools.motivator_items():
        a, b = item["alignment"]["option_a"], item["alignment"]["option_b"]
        assert a in DRIVERS and b in DRIVERS
        pairs.add(frozenset((a, b)))
        exposure[a] += 1
        exposure[b] += 1
    assert len(pairs) == len(DRIVERS) * (len(DRIVERS) - 1) // 2
    assert len(set(exposure.values())) == 1, f"unequal exposure: {exposure}"
