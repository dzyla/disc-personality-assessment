from __future__ import annotations

import random

from assessment.registry import ADDON_MODULES, CORE_MODULES, REGISTRY
from assessment.report.build import build_report


def _run(module_ids, seed=6):
    """Answer every item of the given modules and score them."""
    rng = random.Random(seed)
    context, results, sources, answers = {}, {}, {}, {}
    for module_id in module_ids:
        module = REGISTRY[module_id]
        items = module.build(random.Random(seed), module.variants[0], context)
        given = {
            item.uid: (rng.randint(1, 5) if item.kind == "likert5"
                       else rng.choice(["option_a", "option_b"]))
            for item in items
        }
        results[module_id] = module.score(items, given, context)
        sources[module_id] = [i.source for i in items]
        answers[module_id] = {i.source_id: given[i.uid] for i in items}
        if module_id == "disc_natural":
            context["disc_natural_item_ids"] = [i.source_id for i in items]
    return results, sources, answers


def test_every_module_builds_scores_and_round_trips():
    context = {"disc_natural_item_ids": None}
    for module_id, module in REGISTRY.items():
        for variant in module.variants:
            items = module.build(random.Random(1), variant, {})
            assert items, f"{module_id}/{variant} built no items"
            ids = [i.source_id for i in items]
            rebuilt = module.rebuild(ids, variant)
            assert [i.source_id for i in rebuilt] == ids
            assert all(i.module_id == module_id for i in rebuilt)


def test_adaptive_module_reuses_the_natural_items():
    """The two profiles are only comparable if the stems match."""
    natural = REGISTRY["disc_natural"].build(random.Random(2), "standard", {})
    ids = [i.source_id for i in natural]
    adaptive = REGISTRY["disc_adaptive"].build(
        random.Random(99), "standard", {"disc_natural_item_ids": ids}
    )
    assert [i.source_id for i in adaptive] == ids
    assert adaptive[0].uid != natural[0].uid, "answers must not collide between the two frames"


def test_report_builds_for_the_core_alone():
    results, sources, answers = _run(CORE_MODULES)
    report = build_report(results, sources, answers)
    assert "disc" in report and "strengths" in report
    assert report["plan"]
    assert "strain" not in report


def test_report_builds_for_every_module():
    order = list(CORE_MODULES) + list(ADDON_MODULES)
    results, sources, answers = _run(order)
    report = build_report(results, sources, answers)
    for key in ("disc", "strengths", "strain", "stress", "motivators"):
        assert key in report, f"missing {key}"
    titles = [s["title"] for s in report["integrations"]]
    assert len(titles) == len(set(titles)) and len(titles) >= 3
    assert 1 <= len(report["plan"]) <= 3


def test_report_survives_a_single_module():
    for module_id in ("disc_natural", "strengths_core"):
        results, sources, answers = _run([module_id])
        report = build_report(results, sources, answers)
        assert report["integrations"] == []
        assert report["plan"]


def test_built_items_are_tagged_with_their_own_module():
    """The runner looks the module up by the item's module_id; a mismatch breaks
    the questionnaire even though scoring still works."""
    for module_id, module in REGISTRY.items():
        for variant in module.variants:
            items = module.build(
                random.Random(1), variant,
                {"disc_natural_item_ids": [i.source_id for i in
                                           REGISTRY["disc_natural"].build(random.Random(1), "standard", {})]},
            )
            assert {i.module_id for i in items} == {module_id}
            assert all(i.uid.startswith(f"{module_id}:") for i in items)


def test_pdf_builds_for_every_module_combination():
    from app.pdf import build_pdf

    for modules in (["disc_natural"], ["strengths_core"], list(CORE_MODULES),
                    list(CORE_MODULES) + list(ADDON_MODULES)):
        results, sources, answers = _run(modules)
        report = build_report(results, sources, answers)
        data = build_pdf(report, results).getvalue()
        assert data.startswith(b"%PDF"), f"{modules} produced no PDF"
        assert data.rstrip().endswith(b"%%EOF"), f"{modules} produced a truncated PDF"
        assert data.count(b"/Type /Page") >= 1, f"{modules} produced no pages"
