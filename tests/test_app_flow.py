"""End-to-end runs of the real Streamlit app, headless.

Covers what unit tests cannot: the item queue, the forward-only advance, the
results page rendering, and the JSON round trip.

Note on structure: a stage change goes through ``st.rerun``, which leaves the
previous screen's widgets in AppTest's element tree and breaks the following
run. Tests that need to exercise the questionnaire therefore seed the stage
through the app's own state helpers instead of clicking through the picker; the
picker's own transition is covered separately.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

TIMEOUT = 120
# AppTest resolves a relative path against the calling file's directory.
APP = str(Path(__file__).resolve().parent.parent / "disc_style.py")


def _blank() -> AppTest:
    return AppTest.from_file(APP, default_timeout=TIMEOUT)


def _app() -> AppTest:
    app = _blank()
    app.run()
    return app


def _with_state(app: AppTest, call):
    """Run one of the app's own state helpers against the test session."""
    original = st.session_state
    try:
        st.session_state = app.session_state  # type: ignore[assignment]
        return call()
    finally:
        st.session_state = original  # type: ignore[assignment]


def _started(modules: dict[str, str], seed: int = 42) -> AppTest:
    """An app sitting on the first question of the given modules."""
    from app import state as app_state

    app = _blank()
    _with_state(app, app_state.init)
    app.session_state["seed"] = seed
    _with_state(app, lambda: app_state.build_queue(modules))
    app.session_state["stage"] = "running"
    app.run()
    return app


def _answer_current(app: AppTest, choice: int) -> None:
    item = app.session_state.flat[app.session_state.position]
    radio = app.radio(key=f"resp_{item.uid}")
    radio.set_value(radio.options[min(choice, len(radio.options) - 1)])


def _answer_everything(app: AppTest, choice: int = 3) -> AppTest:
    guard = 0
    while app.session_state.stage == "running":
        guard += 1
        assert guard < 400, "the runner did not terminate"
        _answer_current(app, choice)
        app.button(key="advance").click()
        app.run()
    return app


# --------------------------------------------------------------------- picker

def test_picker_offers_every_module_and_starts_the_queue():
    app = _app()
    keys = {c.key for c in app.checkbox}
    assert keys == {
        "pick_disc_natural", "pick_strengths_core",
        "pick_disc_adaptive", "pick_stress_profile", "pick_motivators",
    }
    app.button(key="begin").click()
    app.run()
    assert app.session_state.stage == "running"
    assert len(app.session_state.flat) == 75  # 40 DISC + 35 strengths


def test_an_addon_needing_a_dependency_is_not_selectable_without_it():
    app = _app()
    app.checkbox(key="pick_disc_natural").set_value(False)
    app.run()
    assert "pick_disc_adaptive" not in {c.key for c in app.checkbox}
    assert any("needs" in m.value.lower() for m in app.markdown)


# --------------------------------------------------------------------- runner

def test_advancing_without_an_answer_is_refused():
    app = _started({"stress_profile": "standard"})
    app.button(key="advance").click()
    app.run()
    assert app.warning, "clicking through without a response must warn"
    assert app.session_state.position == 0, "the queue must not advance"
    assert not app.session_state.answers


def test_the_queue_only_moves_forward():
    app = _started({"stress_profile": "standard"})
    positions = []
    for _ in range(4):
        positions.append(app.session_state.position)
        _answer_current(app, 3)
        app.button(key="advance").click()
        app.run()
    assert positions == [0, 1, 2, 3]
    assert all(b.label != "Back" for b in app.button)
    assert len(app.session_state.answers) == 4


def test_each_item_is_shown_once_and_only_once():
    app = _started({"motivators": "standard"})
    seen = []
    while app.session_state.stage == "running":
        seen.append(app.session_state.flat[app.session_state.position].uid)
        _answer_current(app, 0)
        app.button(key="advance").click()
        app.run()
    assert len(seen) == len(set(seen)) == 28


# -------------------------------------------------------------------- results

def test_a_full_run_produces_a_report():
    app = _answer_everything(
        _started({"stress_profile": "standard", "motivators": "standard"})
    )
    assert app.session_state.stage == "results"
    assert set(app.session_state.results) == {"stress_profile", "motivators"}
    assert not app.exception

    body = " ".join(m.value for m in app.markdown)
    assert "Under pressure" in body
    assert "What drives you" in body
    assert "Three things to try this week" in body


def test_core_run_renders_disc_strengths_and_their_intersection():
    app = _answer_everything(
        _started({"disc_natural": "standard", "strengths_core": "standard"}), choice=4
    )
    assert app.session_state.stage == "results"
    assert not app.exception
    body = " ".join(m.value for m in app.markdown)
    assert "Signature strengths" in body
    assert "Where the lenses meet" in body


def test_uniform_answers_surface_the_low_confidence_warning():
    """A responder who agrees with everything must be told so, prominently."""
    app = _answer_everything(_started({"disc_natural": "standard"}), choice=4)
    assert app.session_state.stage == "results"
    body = " ".join(m.value for m in app.markdown)
    assert "Low confidence" in body


# ------------------------------------------------------------------ portability

def test_export_round_trips_through_import():
    from app import state as app_state

    app = _answer_everything(_started({"stress_profile": "standard"}), choice=2)
    payload = json.loads(json.dumps(_with_state(app, app_state.export_payload)))
    assert payload["schema_version"] == 2
    assert payload["modules"]["stress_profile"]["answers"]
    assert payload["history"]

    fresh = _blank()
    _with_state(fresh, app_state.init)
    _with_state(fresh, lambda: app_state.load_payload(payload))
    assert fresh.session_state.stage == "results"
    before = app.session_state.results["stress_profile"].summary["scores"]
    after = fresh.session_state.results["stress_profile"].summary["scores"]
    assert before == after, "reloading a profile must reproduce the same scores"


def test_a_partial_run_resumes_where_it_stopped():
    from app import state as app_state

    app = _started({"motivators": "standard"})
    for _ in range(5):
        _answer_current(app, 0)
        app.button(key="advance").click()
        app.run()
    payload = _with_state(app, app_state.export_payload)

    fresh = _blank()
    _with_state(fresh, app_state.init)
    _with_state(fresh, lambda: app_state.load_payload(payload))
    assert fresh.session_state.position == 5
    assert fresh.session_state.stage == "running", "a partial run must resume, not restart"
    assert len(fresh.session_state.flat) == 28


def test_a_legacy_export_is_kept_for_comparison():
    from app import state as app_state

    app = _blank()
    _with_state(app, app_state.init)
    message = _with_state(
        app,
        lambda: app_state.load_payload(
            {"disc": {"normalized_scores": {"D": 70, "I": 50, "S": 40, "C": 45}}}
        ),
    )
    assert "previous version" in message
    assert app.session_state.history[0]["legacy"] is True


def test_an_unrecognised_file_is_rejected():
    import pytest

    from app import state as app_state

    app = _blank()
    _with_state(app, app_state.init)
    with pytest.raises(ValueError, match="not an assessment export"):
        _with_state(app, lambda: app_state.load_payload({"unrelated": True}))
