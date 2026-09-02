"""Entry point: page config, then whichever stage the session is in."""

from __future__ import annotations

import streamlit as st

from . import components as ui
from . import picker, results, runner, state


def main() -> None:
    st.set_page_config(page_title="Work style, measured", layout="centered", page_icon="◐")
    ui.inject_css()
    state.init()

    stage = st.session_state.stage
    if stage == "running":
        runner.render()
    elif stage == "results":
        results.render()
    else:
        picker.render()

    st.markdown(
        f'<div style="text-align:center;color:{ui.SLATE};font-size:0.8rem;margin-top:2.5rem;">'
        f'<a href="https://github.com/dzyla/disc-personality-assessment" '
        f'style="color:{ui.SIGNAL};text-decoration:none;">Source</a> · built by Dawid Zyla</div>',
        unsafe_allow_html=True,
    )
