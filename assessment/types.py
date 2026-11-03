"""Core data types shared by sampling, scoring and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Kept short: these are laid out as a horizontal scale, five across.
LIKERT_OPTIONS = (
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
)


@dataclass(frozen=True)
class Item:
    """One question as presented to the user.

    ``uid`` is unique across the whole session and is what answers are keyed by.
    The adaptive DISC module re-presents the same source stems under a different
    frame, so the source id alone would collide.
    """

    uid: str
    module_id: str
    kind: str  # "likert5" | "forced_choice"
    prompt: str
    source: dict[str, Any]
    frame: str = ""  # optional context line shown above the prompt
    options: tuple[str, ...] = ()

    @property
    def source_id(self) -> str:
        return self.source["id"]


@dataclass
class ModuleResult:
    """Scored output of one module."""

    module_id: str
    summary: dict[str, Any] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)


def adjust(response: int, keyed: int) -> int:
    """Flip a reverse-keyed response onto the forward scale."""
    return response if keyed >= 0 else 6 - response
