"""Cross-module sections. These only exist when more than one lens was completed
and are the reason for doing more than the core."""

from __future__ import annotations

from ..scoring.disc import STYLE_NAMES
from ..scoring.stress import MODE_BLURBS, MODE_LABELS, MODE_TO_STYLE

# Which DISC dimension each strength theme leans on. Used to find where a
# person's strengths pull against their behavioural default.
THEME_AFFINITY = {
    "Achiever": "D", "Activator": "D", "Adaptability": "S", "Analytical": "C",
    "Arranger": "C", "Belief": "S", "Command": "D", "Communication": "I",
    "Competition": "D", "Connectedness": "S", "Consistency": "C", "Context": "C",
    "Deliberative": "C", "Developer": "S", "Discipline": "C", "Empathy": "S",
    "Focus": "D", "Futuristic": "I", "Harmony": "S", "Ideation": "I",
    "Includer": "I", "Individualization": "I", "Input": "C", "Intellection": "C",
    "Learner": "C", "Maximizer": "C", "Positivity": "I", "Relator": "S",
    "Responsibility": "C", "Restorative": "C", "Self-Assurance": "D",
    "Significance": "I", "Strategic": "D", "Woo": "I",
}


def _verb(names: list[str], singular: str, plural: str) -> str:
    return singular if len(names) == 1 else plural


def disc_x_strengths(disc_result, strengths_result) -> dict | None:
    d = disc_result.summary
    primary, lowest = d["primary"], d["lowest"]
    top = strengths_result.summary["top"]

    reinforcing = [t for t in top if THEME_AFFINITY.get(t) == primary]
    conflicting = [t for t in top if THEME_AFFINITY.get(t) == lowest]

    lines = []
    if reinforcing:
        lines.append(
            f"<b>Reinforcing:</b> {', '.join(reinforcing)} "
            f"{_verb(reinforcing, 'leans', 'lean')} on {STYLE_NAMES[primary]}, "
            f"which is already your strongest dimension. This is where you are most reliably "
            f"yourself — and where you will be least inclined to check your own judgement."
        )
    if conflicting:
        lines.append(
            f"<b>Pulling against you:</b> {', '.join(conflicting)} "
            f"{_verb(conflicting, 'draws', 'draw')} on "
            f"{STYLE_NAMES[lowest]}, your <i>lowest</i> dimension. You value this way of working "
            f"and it is not how you behave by default. Expect it to show up in your intentions "
            f"more than in your calendar, and expect that gap to be visible to colleagues."
        )
    if not lines:
        lines.append(
            f"Your signature themes spread across dimensions rather than concentrating on "
            f"{STYLE_NAMES[primary]}. That makes you harder to predict, and harder to pigeonhole."
        )
    return {"title": "Behaviour vs. strengths", "icon": "\U0001f501", "lines": lines}


def strain_x_stress(strain: dict | None, stress_result) -> dict | None:
    if strain is None or stress_result is None:
        return None
    mode = stress_result.summary["dominant"]
    lines = [
        f"Under load your dominant mode is <b>{MODE_LABELS[mode]}</b>. {MODE_BLURBS[mode]}"
    ]
    if strain["band"] == "high":
        lines.append(
            f"You are also holding a <b>high adaptation load</b> (strain index {strain['index']:.0f}): "
            f"your work profile sits well away from your natural one, most of all on "
            f"{STYLE_NAMES[strain['largest']]}. Sustained adaptation plus a "
            f"{MODE_LABELS[mode].lower()} response under pressure is the combination that precedes "
            f"burnout — not because either is unhealthy, but because the recovery has to come from "
            f"somewhere and the role is not providing it."
        )
    elif strain["band"] == "moderate":
        lines.append(
            f"Your adaptation load is moderate (index {strain['index']:.0f}), concentrated on "
            f"{STYLE_NAMES[strain['largest']]}. That is a normal cost of a role rather than a warning, "
            f"but it is worth knowing which part of the job is charging it."
        )
    else:
        lines.append(
            f"Your adaptation load is low (index {strain['index']:.0f}). Your role is largely asking "
            f"for behaviour you produce anyway, which is a real and underrated form of fit."
        )
    return {"title": "Strain and pressure", "icon": "⚡", "lines": lines}


def stress_x_disc(disc_result, stress_result) -> dict | None:
    if stress_result is None:
        return None
    mode = stress_result.summary["dominant"]
    expected = MODE_TO_STYLE[mode]
    primary = disc_result.summary["primary"]
    if expected == primary:
        line = (
            f"Your pressure mode is the loaded form of your natural style: you become "
            f"<b>more</b> of what you already are. Colleagues get an intensified version of "
            f"someone they recognise, which is easier for them than the alternative — and means "
            f"your usual blind spot gets sharper exactly when it matters most."
        )
    else:
        line = (
            f"Under pressure you switch: your natural dimension is {STYLE_NAMES[primary]}, but "
            f"your pressure mode is <b>{MODE_LABELS[mode]}</b>, the loaded form of "
            f"{STYLE_NAMES[expected]}. People who know your calm self do not recognise your "
            f"stressed one. That mismatch is worth naming to your team in advance, because they "
            f"will otherwise read the change as being about them."
        )
    return {"title": "Who you become under load", "icon": "\U0001f329", "lines": [line]}


def motivators_x_role(motivator_result, strain: dict | None) -> dict | None:
    if motivator_result is None:
        return None
    top = motivator_result.summary["top"]
    bottom = motivator_result.summary["bottom"]
    lines = [
        f"You traded consistently for <b>{', '.join(top)}</b> and gave away "
        f"<b>{', '.join(bottom)}</b> when forced to choose. Those trades, not your job title, "
        f"are what will make a role feel worth staying in."
    ]
    if strain and strain["band"] == "high":
        lines.append(
            "Set against your high adaptation load, the question worth sitting with is whether the "
            "role is paying you in the currency you actually chose here. A stretch is affordable when "
            "it buys your top drivers and expensive when it does not."
        )
    return {"title": "What you are actually buying", "icon": "\U0001f9f2", "lines": lines}
