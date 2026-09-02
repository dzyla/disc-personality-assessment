"""Session state, the item queue, and the portable JSON that carries a profile
between sessions. There is no server, so this file is the whole persistence
story."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from assessment.registry import REGISTRY
from assessment.report.build import confidence_for
from assessment.types import Item

SCHEMA_VERSION = 2

DEFAULTS: dict[str, Any] = {
    "stage": "picker",
    "seed": None,
    "selection": {},
    "flat": [],
    "answers": {},
    "position": 0,
    "results": {},
    "history": [],
    "legacy_notice": "",
}


def init() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value
    if st.session_state.seed is None:
        st.session_state.seed = random.randrange(1, 2**31 - 1)


def reset() -> None:
    st.session_state.clear()
    init()


def resolve_order(selection: dict[str, str]) -> list[str]:
    """Dependencies first, otherwise registry order."""
    ordered: list[str] = []
    for module_id in REGISTRY:
        if module_id not in selection:
            continue
        for dependency in REGISTRY[module_id].depends_on:
            if dependency in selection and dependency not in ordered:
                ordered.append(dependency)
        if module_id not in ordered:
            ordered.append(module_id)
    return ordered


def _context() -> dict[str, Any]:
    """What later modules need to know about earlier ones."""
    context: dict[str, Any] = {}
    natural = [i for i in st.session_state.flat if i.module_id == "disc_natural"]
    if natural:
        context["disc_natural_item_ids"] = [i.source_id for i in natural]
    return context


def build_queue(selection: dict[str, str], keep_answers: bool = False) -> None:
    rng = random.Random(st.session_state.seed)
    flat: list[Item] = []
    for module_id in resolve_order(selection):
        module = REGISTRY[module_id]
        context = {}
        natural = [i for i in flat if i.module_id == "disc_natural"]
        if natural:
            context["disc_natural_item_ids"] = [i.source_id for i in natural]
        flat.extend(module.build(rng, selection[module_id], context))
    st.session_state.selection = dict(selection)
    st.session_state.flat = flat
    if not keep_answers:
        st.session_state.answers = {}
        st.session_state.results = {}
    st.session_state.position = first_unanswered()


def first_unanswered() -> int:
    answers = st.session_state.answers
    for index, item in enumerate(st.session_state.flat):
        if item.uid not in answers:
            return index
    return len(st.session_state.flat)


def current_item() -> Item | None:
    flat = st.session_state.flat
    position = st.session_state.position
    return flat[position] if 0 <= position < len(flat) else None


def module_items(module_id: str) -> list[Item]:
    return [i for i in st.session_state.flat if i.module_id == module_id]


def module_progress(module_id: str) -> tuple[int, int]:
    items = module_items(module_id)
    done = sum(1 for i in items if i.uid in st.session_state.answers)
    return done, len(items)


def record(uid: str, value: Any) -> None:
    st.session_state.answers[uid] = value


def advance() -> None:
    """Move forward one item and score any module that just finished.

    Scoring per module rather than at the end means a partial run still exports
    usable results, and an add-on taken later slots into an existing report.
    """
    flat = st.session_state.flat
    finished = flat[st.session_state.position]
    st.session_state.position += 1
    following = current_item()
    if following is None or following.module_id != finished.module_id:
        score_module(finished.module_id)
    if st.session_state.position >= len(flat):
        st.session_state.stage = "results"


def score_module(module_id: str) -> None:
    module = REGISTRY[module_id]
    items = module_items(module_id)
    answers = st.session_state.answers
    if any(i.uid not in answers for i in items):
        return
    st.session_state.results[module_id] = module.score(items, answers, _context())


def completed() -> list[str]:
    return [m for m in REGISTRY if m in st.session_state.results]


def add_module(module_id: str, variant: str) -> None:
    selection = dict(st.session_state.selection)
    selection[module_id] = variant
    build_queue(selection, keep_answers=True)
    st.session_state.stage = "running"


def source_answers(module_id: str) -> dict[str, Any]:
    return {
        i.source_id: st.session_state.answers[i.uid]
        for i in module_items(module_id)
        if i.uid in st.session_state.answers
    }


def sources(module_id: str) -> list[dict]:
    return [i.source for i in module_items(module_id)]


# --------------------------------------------------------------------------
# export / import
# --------------------------------------------------------------------------

def export_payload() -> dict:
    """Every started module, finished or not, so a half-done run can resume."""
    modules: dict[str, Any] = {}
    for module_id in st.session_state.selection:
        items = module_items(module_id)
        answers = source_answers(module_id)
        if not answers:
            continue
        entry: dict[str, Any] = {
            "variant": st.session_state.selection.get(module_id, "standard"),
            "item_ids": [i.source_id for i in items],
            "answers": answers,
            "complete": module_id in st.session_state.results,
        }
        if entry["complete"]:
            entry["summary"] = st.session_state.results[module_id].summary
            entry["confidence"] = confidence_for(module_id, sources(module_id), answers)
        modules[module_id] = entry

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    history = list(st.session_state.history)
    finished = {mid: data["summary"] for mid, data in modules.items() if data.get("complete")}
    if finished:
        history.append({"date": now, "modules": finished})
    return {
        "schema_version": SCHEMA_VERSION,
        "created": now,
        "seed": st.session_state.seed,
        "modules": modules,
        "history": history,
    }


def _migrate_v1(payload: dict) -> dict | None:
    """Old exports stored final scores only, so they become a history entry
    without item-level evidence rather than a restorable session."""
    disc = None
    if isinstance(payload.get("disc"), dict) and "normalized_scores" in payload["disc"]:
        disc = payload["disc"]["normalized_scores"]
    elif "normalized_scores" in payload:
        disc = payload["normalized_scores"]
    elif all(k in payload for k in ("D", "I", "S", "C")):
        disc = {k: payload[k] for k in ("D", "I", "S", "C")}
    if disc is None:
        return None
    return {
        "date": payload.get("date", "an earlier take"),
        "legacy": True,
        "modules": {"disc_natural": {"normalized": disc, "standard_error": {k: 0.0 for k in disc}}},
    }


def load_payload(payload: dict) -> str:
    """Restore a saved run. Returns a human-readable status line."""
    if payload.get("schema_version") != SCHEMA_VERSION:
        entry = _migrate_v1(payload)
        if entry is None:
            raise ValueError("This file is not an assessment export.")
        st.session_state.history = [entry]
        return (
            "Loaded an export from the previous version. It only stored final scores, so it is "
            "kept for comparison but cannot show which answers produced it — take the assessment "
            "again to get evidence-backed results."
        )

    st.session_state.seed = payload.get("seed") or st.session_state.seed
    st.session_state.history = payload.get("history", [])
    modules = payload.get("modules", {})

    flat: list[Item] = []
    selection: dict[str, str] = {}
    for module_id, data in modules.items():
        if module_id not in REGISTRY:
            continue
        variant = data.get("variant", "standard")
        selection[module_id] = variant
        flat.extend(REGISTRY[module_id].rebuild(data["item_ids"], variant))

    st.session_state.selection = selection
    st.session_state.flat = flat
    st.session_state.answers = {
        f"{module_id}:{source_id}": value
        for module_id, data in modules.items()
        if module_id in REGISTRY
        for source_id, value in data.get("answers", {}).items()
    }
    st.session_state.results = {}
    for module_id in selection:
        score_module(module_id)
    st.session_state.position = first_unanswered()

    unfinished = st.session_state.position < len(flat)
    if unfinished:
        st.session_state.stage = "running"
    elif st.session_state.results:
        st.session_state.stage = "results"
    else:
        st.session_state.stage = "picker"

    names = ", ".join(REGISTRY[m].title for m in selection if m in REGISTRY)
    if not names:
        return "That export had no answers in it."
    if unfinished:
        remaining = len(flat) - st.session_state.position
        return f"Loaded: {names}. Picking up where you stopped — {remaining} questions left."
    return f"Loaded: {names}."


def drift() -> dict[str, Any] | None:
    """Compare the current DISC profile with the most recent previous take."""
    previous = [h for h in st.session_state.history if "disc_natural" in h.get("modules", {})]
    current = st.session_state.results.get("disc_natural")
    if not previous or current is None:
        return None
    last = previous[-1]
    before = last["modules"]["disc_natural"]
    moves = {}
    for style in ("D", "I", "S", "C"):
        old = before["normalized"].get(style)
        new = current.summary["normalized"][style]
        if old is None:
            continue
        se_old = before.get("standard_error", {}).get(style, 0.0)
        se_new = current.summary["standard_error"][style]
        band = (se_old ** 2 + se_new ** 2) ** 0.5
        delta = new - old
        moves[style] = {
            "before": old,
            "after": new,
            "delta": round(delta, 1),
            "real": bool(band > 0 and abs(delta) >= 1.96 * band),
        }
    return {"date": last.get("date", ""), "legacy": last.get("legacy", False), "moves": moves}
