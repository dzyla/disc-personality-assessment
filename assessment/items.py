"""Loading item pools and drawing balanced samples from them.

Sampling is deterministic given a seed: the export stores the seed and the item
ids, so a retake can either repeat the same items (measuring change in the
person) or draw fresh ones (measuring robustness of the result).
"""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from .types import LIKERT_OPTIONS, Item

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

STYLES = ("D", "I", "S", "C")
STRESS_MODES = ("push", "perform", "accommodate", "retreat")


def _load(name: str) -> Any:
    with open(DATA_DIR / name, encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=None)
def disc_items() -> list[dict]:
    return _load("disc_items.json")


@lru_cache(maxsize=None)
def disc_descriptions() -> dict:
    return _load("disc_descriptions.json")


@lru_cache(maxsize=None)
def strengths_items() -> list[dict]:
    return _load("strengths_items.json")


@lru_cache(maxsize=None)
def strengths_themes() -> dict:
    return _load("strengths_themes.json")


@lru_cache(maxsize=None)
def stress_items() -> list[dict]:
    return _load("stress_items.json")


@lru_cache(maxsize=None)
def motivator_items() -> list[dict]:
    return _load("motivator_items.json")


def option_themes(item: dict, option: str) -> list[str]:
    return item["alignment"].get(option, [])


# --------------------------------------------------------------------------
# sampling
# --------------------------------------------------------------------------

def sample_disc(rng: random.Random, per_style: int = 10, reverse_per_style: int = 3) -> list[dict]:
    """Equal items per dimension, with a guaranteed share of reverse-keyed ones.

    The reverse items are what make an acquiescence check possible, so they are
    drawn explicitly rather than left to chance.
    """
    pool = disc_items()
    chosen: list[dict] = []
    for style in STYLES:
        forward = [q for q in pool if q["style"] == style and q["keyed"] > 0]
        reverse = [q for q in pool if q["style"] == style and q["keyed"] < 0]
        n_rev = min(reverse_per_style, len(reverse), per_style)
        n_fwd = min(per_style - n_rev, len(forward))
        chosen.extend(rng.sample(reverse, n_rev))
        chosen.extend(rng.sample(forward, n_fwd))
    rng.shuffle(chosen)
    return chosen


def sample_strengths(rng: random.Random, count: int = 35) -> list[dict]:
    """Greedy stratified draw that equalises how often each theme is offered.

    The pool is badly unbalanced by construction (some themes appear in 41
    items, others in 9), so a uniform random draw makes a theme's rank partly a
    property of the pool. Each pick here goes to the item that does most for the
    themes currently least represented.
    """
    pool = list(strengths_items())
    rng.shuffle(pool)  # breaks ties reproducibly
    exposure = {theme: 0 for theme in strengths_themes()}
    chosen: list[dict] = []
    remaining = pool[:]

    while remaining and len(chosen) < count:
        def gain(item: dict) -> float:
            tags = set(option_themes(item, "option_a")) | set(option_themes(item, "option_b"))
            return sum(1.0 / (1.0 + exposure[t]) for t in tags if t in exposure)

        best = max(remaining, key=gain)
        remaining.remove(best)
        chosen.append(best)
        for option in ("option_a", "option_b"):
            for theme in option_themes(best, option):
                if theme in exposure:
                    exposure[theme] += 1

    rng.shuffle(chosen)
    return chosen


def sample_stress(rng: random.Random, per_mode: int = 5, reverse_per_mode: int = 1) -> list[dict]:
    pool = stress_items()
    chosen: list[dict] = []
    for mode in STRESS_MODES:
        forward = [q for q in pool if q["mode"] == mode and q["keyed"] > 0]
        reverse = [q for q in pool if q["mode"] == mode and q["keyed"] < 0]
        n_rev = min(reverse_per_mode, len(reverse), per_mode)
        chosen.extend(rng.sample(reverse, n_rev))
        chosen.extend(rng.sample(forward, min(per_mode - n_rev, len(forward))))
    rng.shuffle(chosen)
    return chosen


def sample_motivators(rng: random.Random) -> list[dict]:
    """All 28 pairs: a round robin over the eight drivers, so exposure is exact."""
    chosen = list(motivator_items())
    rng.shuffle(chosen)
    return chosen


# --------------------------------------------------------------------------
# item construction
# --------------------------------------------------------------------------

def to_likert_items(sources: list[dict], module_id: str, frame: str = "") -> list[Item]:
    return [
        Item(
            uid=f"{module_id}:{src['id']}",
            module_id=module_id,
            kind="likert5",
            prompt=src["question"],
            source=src,
            frame=frame,
            options=LIKERT_OPTIONS,
        )
        for src in sources
    ]


def to_choice_items(sources: list[dict], module_id: str, frame: str = "") -> list[Item]:
    return [
        Item(
            uid=f"{module_id}:{src['id']}",
            module_id=module_id,
            kind="forced_choice",
            prompt=src["question"],
            source=src,
            frame=frame,
            options=(src["option_a"], src["option_b"]),
        )
        for src in sources
    ]


def rebuild_from_ids(module_id: str, kind: str, ids: list[str], frame: str = "") -> list[Item]:
    """Recreate a saved item sequence from stored ids, preserving order."""
    pools = {
        "disc": disc_items(),
        "strengths": strengths_items(),
        "stress": stress_items(),
        "motivators": motivator_items(),
    }
    index = {src["id"]: src for src in pools[kind]}
    sources = [index[i] for i in ids if i in index]
    if kind in ("disc", "stress"):
        return to_likert_items(sources, module_id, frame)
    return to_choice_items(sources, module_id, frame)
