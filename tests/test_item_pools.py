"""Data-integrity checks, including the guard that keeps third-party names out."""

from __future__ import annotations

import collections
import itertools
import re
from pathlib import Path

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
    per_group = collections.Counter((item["style"], item["keyed"]) for item in items)
    assert {group[0] for group in per_group} == set(pools.STYLES)
    assert {group[1] for group in per_group} == {1, -1}
    assert len({per_group[(s, 1)] for s in pools.STYLES}) == 1, f"unbalanced: {per_group}"
    assert len({per_group[(s, -1)] for s in pools.STYLES}) == 1, f"unbalanced: {per_group}"


def test_disc_items_carry_no_weights_on_other_styles():
    for item in pools.disc_items():
        assert "mapping" not in item, f"{item['id']} still has cross-style weights"


def test_disc_twins_are_mirror_images_of_each_other():
    index = {item["id"]: item for item in pools.disc_items()}
    for item in index.values():
        if "twin" in item:
            twin = index[item["twin"]]
            assert twin["twin"] == item["id"]
            assert twin["style"] == item["style"]
            assert twin["keyed"] == -item["keyed"]


def test_strengths_are_24_split_evenly_across_three_domains():
    themes = pools.strengths_themes()
    assert len(themes) == 24
    domains = collections.Counter(t["domain"] for t in themes.values())
    assert domains == {"Doing": 8, "Thinking": 8, "People": 8}
    leans = collections.Counter(t["disc_affinity"] for t in themes.values())
    assert leans == {"D": 6, "I": 6, "S": 6, "C": 6}


def test_strength_pool_holds_every_pair_exactly_once():
    themes = pools.strengths_themes()
    pairs = collections.Counter(
        frozenset(item["alignment"]["option_a"] + item["alignment"]["option_b"])
        for item in pools.strengths_items()
    )
    assert set(pairs) == {frozenset(p) for p in itertools.combinations(themes, 2)}
    assert set(pairs.values()) == {1}


def test_each_option_counts_for_exactly_one_strength():
    for item in pools.strengths_items():
        for option in ("option_a", "option_b"):
            assert len(pools.option_themes(item, option)) == 1


# Third-party labels the strengths module must not use. They are listed only here,
# to stop them coming back. Some are everyday words, so
# those are only refused as labels; the distinctive ones are refused anywhere.
_THIRD_PARTY_LABELS = {
    "Achiever", "Activator", "Adaptability", "Analytical", "Arranger", "Belief", "Command",
    "Communication", "Competition", "Connectedness", "Consistency", "Context", "Deliberative",
    "Developer", "Discipline", "Empathy", "Focus", "Futuristic", "Harmony", "Ideation",
    "Includer", "Individualization", "Input", "Intellection", "Learner", "Maximizer",
    "Positivity", "Relator", "Responsibility", "Restorative", "Self-Assurance", "Significance",
    "Strategic", "Woo", "Executing", "Influencing", "Relationship Building", "Strategic Thinking",
}
_DISTINCTIVE = (
    "Gallup", "CliftonStrengths", "StrengthsFinder", "Achiever", "Activator", "Arranger",
    "Connectedness", "Deliberative", "Futuristic", "Ideation", "Includer", "Individualization",
    "Intellection", "Maximizer", "Relator", "Restorative", "Self-Assurance", "Woo",
    "Relationship Building", "Strategic Thinking", "Signature strengths", "signature themes",
)


def test_no_strength_or_domain_uses_a_third_party_label():
    themes = pools.strengths_themes()
    labels = set(themes) | {t["domain"] for t in themes.values()}
    assert not labels & _THIRD_PARTY_LABELS


def test_distinctive_third_party_terms_appear_nowhere_in_the_app():
    root = Path(__file__).resolve().parent.parent
    paths = [root / "README.md", *(root / "data").glob("*"), *(root / "app").glob("*.py")]
    paths += list((root / "assessment").rglob("*.py"))
    pattern = re.compile(r"\\b(" + "|".join(re.escape(t) for t in _DISTINCTIVE) + r")\\b")
    for path in paths:
        found = pattern.findall(path.read_text(encoding="utf-8"))
        assert not found, f"{path.name}: {sorted(set(found))}"


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
