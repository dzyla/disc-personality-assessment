"""The questionnaire: one item per screen, forward only.

There is no back button by design. The advance is always a deliberate click —
nothing auto-submits on selection.
"""

from __future__ import annotations

import html

import streamlit as st

from assessment.registry import REGISTRY
from assessment.types import LIKERT_OPTIONS

from . import components as ui
from . import state


def render() -> None:
    item = state.current_item()
    if item is None:
        st.session_state.stage = "results"
        st.rerun()
        return

    module = REGISTRY[item.module_id]
    done, total = state.module_progress(item.module_id)
    index = done + 1
    answered = st.session_state.position
    overall = len(st.session_state.flat)

    st.markdown(
        f'<div class="chan">{html.escape(module.title)} · '
        f'<span class="num">{index:02d} / {total:02d}</span>'
        f'{f" · {answered} of {overall} overall" if overall != total else ""}</div>',
        unsafe_allow_html=True,
    )
    ui.meter(answered / overall if overall else 0.0)

    frame = f'<div class="qframe">{html.escape(item.frame)}</div>' if item.frame else ""
    st.markdown(
        f'<div class="qcard"><div class="qprompt">{html.escape(item.prompt)}</div>{frame}</div>',
        unsafe_allow_html=True,
    )

    if item.kind == "likert5":
        options = list(LIKERT_OPTIONS)
        choice = st.radio(
            "Your response",
            options=options,
            index=None,
            key=f"resp_{item.uid}",
            label_visibility="collapsed",
            horizontal=True,
        )
        value = options.index(choice) + 1 if choice is not None else None
    else:
        options = [item.options[0], item.options[1]]
        choice = st.radio(
            "Which is more like you?",
            options=options,
            index=None,
            key=f"resp_{item.uid}",
            label_visibility="collapsed",
            horizontal=True,
        )
        value = ("option_a" if choice == options[0] else "option_b") if choice is not None else None

    last_overall = st.session_state.position == overall - 1
    label = "See your results" if last_overall else "Next"

    if st.button(label, key="advance", use_container_width=True, type="primary"):
        if value is None:
            st.warning("Pick a response to continue.")
        else:
            state.record(item.uid, value)
            state.advance()
            st.rerun()
