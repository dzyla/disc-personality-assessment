"""Narrative generation. Returns plain data structures that both the Streamlit
page and the PDF render, so the two can never drift apart."""

from .build import build_report  # noqa: F401
