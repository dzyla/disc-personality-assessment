"""Assembles the full report from whichever modules were completed."""

from __future__ import annotations

from typing import Any

from .. import items as pools
from ..scoring import reliability
from ..scoring.disc import strain as disc_strain
from . import disc as disc_report
from . import integration, plan
from . import strengths as strengths_report


def confidence_for(module_id: str, source_items: list[dict], answers: dict[str, Any]) -> dict | None:
    """Response-quality verdict for the Likert modules, which are the only ones
    with the forward/reverse structure the checks need."""
    group = {"disc_natural": "style", "disc_adaptive": "style", "stress_profile": "mode"}.get(module_id)
    if group is None:
        return None
    responses = [answers[i["id"]] for i in source_items if i["id"] in answers]
    return reliability.verdict(
        reliability.acquiescence(source_items, answers, group),
        reliability.split_half(source_items, answers, group),
        reliability.straight_lining(responses),
    )


def build_report(results: dict[str, Any], sources: dict[str, list[dict]],
                 answers: dict[str, dict[str, Any]]) -> dict:
    """`results` maps module id to ModuleResult; `sources` and `answers` are the
    raw item dicts and source-keyed answers used to compute response quality."""
    report: dict[str, Any] = {"sections": [], "integrations": []}

    confidence = {
        mid: confidence_for(mid, sources.get(mid, []), answers.get(mid, {}))
        for mid in results
    }
    report["confidence"] = {k: v for k, v in confidence.items() if v}

    disc_result = results.get("disc_natural")
    adaptive_result = results.get("disc_adaptive")
    strengths_result = results.get("strengths_core")
    stress_result = results.get("stress_profile")
    motivator_result = results.get("motivators")

    disc_narrative = None
    if disc_result is not None:
        disc_narrative = disc_report.narrative(
            disc_result,
            confidence.get("disc_natural") or {"level": "Moderate"},
            pools.disc_descriptions(),
        )
        report["disc"] = disc_narrative

    strain = None
    if disc_result is not None and adaptive_result is not None:
        strain = disc_strain(disc_result, adaptive_result)
        report["strain"] = strain
        report["adaptive"] = adaptive_result.summary

    strengths_narrative = None
    if strengths_result is not None:
        strengths_narrative = strengths_report.narrative(strengths_result, pools.strengths_themes())
        report["strengths"] = strengths_narrative

    if stress_result is not None:
        report["stress"] = stress_result.summary
        report["stress_evidence"] = stress_result.detail["evidence"]

    if motivator_result is not None:
        report["motivators"] = motivator_result.summary
        report["motivator_evidence"] = motivator_result.detail["evidence"]

    sections = []
    if disc_result is not None and strengths_result is not None:
        sections.append(integration.disc_x_strengths(disc_result, strengths_result))
    if disc_result is not None and stress_result is not None:
        sections.append(integration.stress_x_disc(disc_result, stress_result))
    if strain is not None:
        sections.append(integration.strain_x_stress(strain, stress_result))
    if motivator_result is not None:
        sections.append(integration.motivators_x_role(motivator_result, strain))
    report["integrations"] = [s for s in sections if s]

    report["plan"] = plan.build(disc_result, strengths_narrative, stress_result, strain, motivator_result)
    return report
