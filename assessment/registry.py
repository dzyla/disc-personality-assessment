"""Declarative registry of assessment modules.

Adding a lens means adding an entry here plus its data and scorer. The runner,
the picker, the results page and the export all work off this table, so none of
them need to know which modules exist.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable

from . import items as pools
from .scoring import disc, motivators, stress, strengths
from .types import Item, ModuleResult

NATURAL_FRAME = (
    "Answer as you are when nothing in particular is pulling on you — "
    "off duty, at your most natural."
)
ADAPTIVE_FRAME = (
    "Same statements, different frame: answer for your current role — "
    "how you actually behave at work."
)
STRESS_FRAME = "Think about your last genuinely stretched week, not an average one."


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    icon: str
    blurb: str
    kind: str  # "core" | "addon"
    item_type: str  # "likert5" | "forced_choice"
    build: Callable[[random.Random, str, dict], list[Item]]
    rebuild: Callable[[list[str], str], list[Item]]
    score: Callable[[list[Item], dict[str, Any], dict], ModuleResult]
    minutes: dict[str, int] = field(default_factory=lambda: {"standard": 5})
    variants: tuple[str, ...] = ("standard",)
    depends_on: tuple[str, ...] = ()
    variant_labels: dict[str, str] = field(default_factory=dict)

    def length(self, variant: str, context: dict | None = None) -> int:
        return len(self.build(random.Random(0), variant, context or {}))


def _answers_by_source(items: list[Item], answers: dict[str, Any]) -> dict[str, Any]:
    return {item.source_id: answers[item.uid] for item in items if item.uid in answers}


# --------------------------------------------------------------------------- DISC

def _build_disc_natural(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_likert_items(pools.sample_disc(rng), "disc_natural", NATURAL_FRAME)


def _score_disc(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return disc.score([i.source for i in items], _answers_by_source(items, answers))


def _build_disc_adaptive(rng: random.Random, variant: str, context: dict) -> list[Item]:
    """Re-present exactly the stems used for the natural run.

    The two profiles are only comparable if the items match, so this module
    borrows the natural module's item ids rather than drawing its own.
    """
    ids = context.get("disc_natural_item_ids") or [q["id"] for q in pools.sample_disc(rng)]
    return pools.rebuild_from_ids("disc_adaptive", "disc", ids, ADAPTIVE_FRAME)


# ---------------------------------------------------------------------- strengths

def _build_strengths(rng: random.Random, variant: str, context: dict) -> list[Item]:
    count = 60 if variant == "deep" else 35
    return pools.to_choice_items(pools.sample_strengths(rng, count), "strengths_core")


def _score_strengths(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return strengths.score(
        [i.source for i in items], _answers_by_source(items, answers), pools.strengths_themes()
    )


# ------------------------------------------------------------------------- stress

def _build_stress(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_likert_items(pools.sample_stress(rng), "stress_profile", STRESS_FRAME)


def _score_stress(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return stress.score([i.source for i in items], _answers_by_source(items, answers))


# --------------------------------------------------------------------- motivators

def _build_motivators(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_choice_items(pools.sample_motivators(rng), "motivators")


def _score_motivators(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return motivators.score([i.source for i in items], _answers_by_source(items, answers))


def _rebuilder(kind: str, module_id: str, frame: str = "") -> Callable[[list[str], str], list[Item]]:
    def rebuild(ids: list[str], variant: str) -> list[Item]:
        return pools.rebuild_from_ids(module_id, kind, ids, frame)

    return rebuild


REGISTRY: dict[str, Module] = {}


def _register(module: Module) -> None:
    REGISTRY[module.id] = module


_register(Module(
    id="disc_natural",
    title="DISC — your natural style",
    icon="\U0001f9ed",
    blurb=(
        "Forty statements, balanced across the four dimensions and mixing positively "
        "and negatively worded items so the result can be checked for consistency."
    ),
    kind="core",
    item_type="likert5",
    build=_build_disc_natural,
    rebuild=_rebuilder("disc", "disc_natural", NATURAL_FRAME),
    score=_score_disc,
    minutes={"standard": 5},
))

_register(Module(
    id="strengths_core",
    title="Signature strengths",
    icon="\U0001f48e",
    blurb=(
        "Forced choices between two ways of working, drawn so every one of the 34 "
        "themes gets offered a comparable number of times."
    ),
    kind="core",
    item_type="forced_choice",
    build=_build_strengths,
    rebuild=_rebuilder("strengths", "strengths_core"),
    score=_score_strengths,
    minutes={"standard": 5, "deep": 9},
    variants=("standard", "deep"),
    variant_labels={
        "standard": "Standard — 35 choices",
        "deep": "Deep — 60 choices, sharper separation between themes",
    },
))

_register(Module(
    id="disc_adaptive",
    title="DISC — your work style",
    icon="\U0001f3e2",
    blurb=(
        "The same forty statements answered for your current role. The gap between "
        "this and your natural profile is the strain your job is asking of you."
    ),
    kind="addon",
    item_type="likert5",
    build=_build_disc_adaptive,
    rebuild=_rebuilder("disc", "disc_adaptive", ADAPTIVE_FRAME),
    score=_score_disc,
    minutes={"standard": 5},
    depends_on=("disc_natural",),
))

_register(Module(
    id="stress_profile",
    title="Under pressure",
    icon="⚡",
    blurb=(
        "Twenty statements about a genuinely stretched week, scored as four pressure "
        "modes: push, perform, accommodate, retreat."
    ),
    kind="addon",
    item_type="likert5",
    build=_build_stress,
    rebuild=_rebuilder("stress", "stress_profile", STRESS_FRAME),
    score=_score_stress,
    minutes={"standard": 3},
))

_register(Module(
    id="motivators",
    title="What drives you",
    icon="\U0001f9f2",
    blurb=(
        "Twenty-eight either-or trades over eight drivers. Every driver meets every "
        "other exactly once, so nothing is decided by how often it came up."
    ),
    kind="addon",
    item_type="forced_choice",
    build=_build_motivators,
    rebuild=_rebuilder("motivators", "motivators"),
    score=_score_motivators,
    minutes={"standard": 4},
))

CORE_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "core")
ADDON_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "addon")
