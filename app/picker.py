"""Module selection. Everything is opt-in and states its own cost up front."""

from __future__ import annotations

import html
import json

import streamlit as st

from assessment.registry import ADDON_MODULES, CORE_MODULES, REGISTRY

from . import components as ui
from . import state


def _module_row(module_id: str, default: bool) -> tuple[bool, str]:
    module = REGISTRY[module_id]
    blocked = [d for d in module.depends_on if d not in st.session_state.get("_picked", set())]
    label = f"{module.icon}  {module.title}"

    if blocked:
        # Rendered as text rather than a disabled checkbox: there is nothing to
        # click, and a dead widget only adds noise to the list.
        needs = ", ".join(REGISTRY[d].title for d in blocked)
        st.markdown(
            f'<p style="color:{ui.SLATE};margin-bottom:14px;">{html.escape(label)}<br>'
            f'<span class="chan">needs {html.escape(needs)} first — '
            f'the comparison has no meaning without it</span></p>',
            unsafe_allow_html=True,
        )
        return False, module.variants[0]

    picked = st.checkbox(label, value=default, key=f"pick_{module_id}")
    variant = module.variants[0]
    if picked and len(module.variants) > 1:
        variant = st.radio(
            "Length",
            options=list(module.variants),
            format_func=lambda v: module.variant_labels.get(v, v),
            key=f"variant_{module_id}",
            label_visibility="collapsed",
        )
    minutes = module.minutes.get(variant, 5)
    st.markdown(
        f'<div style="margin:-6px 0 14px 30px;color:{ui.SLATE};font-size:0.93rem;line-height:1.55;">'
        f'{html.escape(module.blurb)}<br><span class="chan">≈ {minutes} min</span></div>',
        unsafe_allow_html=True,
    )
    return picked, variant


def render() -> None:
    ui.masthead(
        "Work style, measured",
        "A behavioural profile reported with its uncertainty — including when the numbers "
        "are too close to call. Pick the lenses you want; each one states what it costs.",
        eyebrow="Assessment · select modules",
    )

    st.markdown('<div class="chan">Core</div>', unsafe_allow_html=True)
    selection: dict[str, str] = {}
    st.session_state["_picked"] = set()
    for module_id in CORE_MODULES:
        picked, variant = _module_row(module_id, default=True)
        if picked:
            selection[module_id] = variant
            st.session_state["_picked"].add(module_id)

    st.markdown('<div class="chan" style="margin-top:0.8rem;">Add-ons</div>', unsafe_allow_html=True)
    for module_id in ADDON_MODULES:
        picked, variant = _module_row(module_id, default=False)
        if picked:
            selection[module_id] = variant
            st.session_state["_picked"].add(module_id)

    total_minutes = sum(REGISTRY[m].minutes.get(v, 5) for m, v in selection.items())
    st.markdown("---")
    if not selection:
        st.markdown(
            f'<p style="color:{ui.SLATE};">Select at least one module to begin.</p>',
            unsafe_allow_html=True,
        )
    else:
        names = ", ".join(REGISTRY[m].title for m in state.resolve_order(selection))
        st.markdown(
            f'<div class="chan">Selected</div><p style="margin-top:4px;">{html.escape(names)} '
            f'<span class="num" style="color:{ui.SLATE};">· ≈ {total_minutes} min total</span></p>',
            unsafe_allow_html=True,
        )
        if st.button("Begin", key="begin", use_container_width=True, type="primary"):
            state.build_queue(selection)
            st.session_state.stage = "running"
            st.rerun()

    with st.expander("Continue a saved profile"):
        st.caption(
            "Upload the JSON this app gave you. It restores your answers, lets you add modules "
            "you skipped, and compares a new take against the old one."
        )
        uploaded = st.file_uploader("Saved profile", type=["json"], label_visibility="collapsed")
        if uploaded is not None:
            try:
                message = state.load_payload(json.loads(uploaded.getvalue().decode("utf-8")))
                st.success(message)
                st.rerun()
            except (ValueError, KeyError, json.JSONDecodeError) as error:
                st.error(f"Could not read that file: {error}")
