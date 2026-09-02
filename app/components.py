"""Shared styling and readout primitives.

Design thesis: this is an instrument, not a personality quiz. Every number the
app reports carries uncertainty, so the signature element is the error bar — the
same visual grammar for dimension scores, win rates and strain. Numbers are set
in a monospace face and labelled like instrument channels; nothing is reported
as a bare figure.
"""

from __future__ import annotations

import html

import streamlit as st

INK = "#0F2233"
SLATE = "#46586B"
PAPER = "#F7F8FA"
RULE = "#DCE3EA"
SIGNAL = "#1B6E8C"
FLAG = "#B4471F"

STYLE_COLOURS = {"D": "#C2453B", "I": "#C98A16", "S": "#2E8B5A", "C": "#2C6FB5"}
DOMAIN_COLOURS = {
    "Executing": "#6D4AA6",
    "Influencing": "#C98A16",
    "Relationship Building": "#2E8B5A",
    "Strategic Thinking": "#2C6FB5",
}
CONFIDENCE_COLOURS = {"High": "#2E8B5A", "Moderate": "#C98A16", "Low": FLAG}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

.stApp {{ background: {PAPER}; }}
/* Streamlit's header is fixed and overlays the top of the page, so the first
   line needs to clear it rather than slide underneath. */
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ max-width: 880px; padding-top: 4.75rem; padding-bottom: 4rem; }}

html, body, [class*="css"], .stMarkdown, .stRadio label {{
    font-family: 'Source Sans 3', system-ui, sans-serif;
    color: {INK};
}}
h1, h2, h3, h4 {{ font-family: 'Archivo', system-ui, sans-serif; letter-spacing: -0.015em; }}

/* Instrument channel labels: mono, spaced, quiet. Used as eyebrows everywhere. */
.chan {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    line-height: 1.7;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {SLATE};
}}
.num {{ font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; }}

.masthead {{ border-bottom: 1px solid {RULE}; padding-bottom: 1.1rem; margin-bottom: 1.8rem; }}
.masthead h1 {{
    font-size: 1.72rem; font-weight: 700; margin: 0.25rem 0 0.3rem 0; line-height: 1.15;
}}
.masthead p {{ color: {SLATE}; margin: 0; font-size: 0.98rem; }}

/* ---- the signature: a value with its uncertainty drawn, never a bare number */
.readout {{ margin: 0 0 1.05rem 0; }}
.readout-head {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 5px; }}
.readout-val {{ font-family: 'IBM Plex Mono', monospace; font-size: 1.02rem; font-weight: 600; font-variant-numeric: tabular-nums; }}
.readout-pm {{ font-size: 0.78rem; font-weight: 400; color: {SLATE}; margin-left: 5px; }}
.track {{ position: relative; height: 15px; background: transparent; }}
.track:before {{
    content: ""; position: absolute; left: 0; right: 0; top: 7px; height: 1px; background: {RULE};
}}
.ci {{ position: absolute; top: 4px; height: 7px; border-radius: 1px; opacity: 0.26; }}
.ci:before, .ci:after {{
    content: ""; position: absolute; top: -3px; width: 1px; height: 13px; background: currentColor; opacity: 0.85;
}}
.ci:before {{ left: 0; }} .ci:after {{ right: 0; }}
.pt {{ position: absolute; top: 1px; width: 3px; height: 13px; border-radius: 1px; }}

/* ---- cards */
.panel {{
    background: #FFFFFF; border: 1px solid {RULE}; border-radius: 3px;
    padding: 20px 24px; margin-bottom: 16px;
}}
.panel h4 {{ margin: 0 0 0.5rem 0; font-size: 1.06rem; font-weight: 600; }}
.panel p {{ margin: 0 0 0.55rem 0; line-height: 1.62; }}
.panel p:last-child {{ margin-bottom: 0; }}

.theme-card {{
    background: #FFFFFF; border: 1px solid {RULE}; border-left: 3px solid {SIGNAL};
    border-radius: 3px; padding: 18px 22px; margin-bottom: 12px;
}}
.theme-rank {{ font-family: 'IBM Plex Mono', monospace; color: {SLATE}; font-size: 0.8rem; }}
.theme-name {{ font-family: 'Archivo', sans-serif; font-size: 1.14rem; font-weight: 600; }}
.theme-cost {{
    border-top: 1px dashed {RULE}; margin-top: 12px; padding-top: 10px;
    font-size: 0.93rem; color: {SLATE};
}}
.theme-cost b {{ color: {INK}; }}

.caveat {{
    border-left: 3px solid {FLAG}; background: #FDF6F3; padding: 14px 18px;
    border-radius: 0 3px 3px 0; margin-bottom: 18px; font-size: 0.95rem;
}}
.caveat ul {{ margin: 0.4rem 0 0 1rem; padding: 0; }}

.tag {{
    display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    letter-spacing: 0.1em; text-transform: uppercase; padding: 3px 9px;
    border: 1px solid {RULE}; border-radius: 2px; margin-right: 6px; color: {SLATE};
    background: #FFFFFF;
}}

/* ---- question screen */
.qprompt {{
    font-family: 'Archivo', sans-serif; font-size: 1.42rem; font-weight: 500;
    line-height: 1.38; margin: 0.2rem 0 0.15rem 0;
}}
.qframe {{ color: {SLATE}; font-size: 0.95rem; font-style: italic; margin-bottom: 1.4rem; }}
.qcard {{ animation: rise 220ms ease-out; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: none; }} }}
@media (prefers-reduced-motion: reduce) {{ .qcard {{ animation: none; }} }}

.meter {{ height: 2px; background: {RULE}; margin: 6px 0 26px 0; }}
.meter > div {{ height: 2px; background: {SIGNAL}; transition: width 220ms ease-out; }}

/* ---- widgets */
/* Options share one row and never wrap onto a second: five cells for the agree
   scale, two for a forced choice. Equal basis of 0 makes every cell the same
   width regardless of how long its label is. */
.stRadio > div[role="radiogroup"] {{
    display: flex; width: 100%;
    flex-direction: row; flex-wrap: nowrap; align-items: stretch;
    gap: 8px; padding: 4px 0 16px 0;
}}
/* The group is fit-content by default, so the cells were dividing a container
   narrower than the column and clipping their labels. */
.stRadio, .stRadio > div {{ width: 100%; }}
.stRadio > div[role="radiogroup"] > label {{
    flex: 1 1 0; min-width: 0; overflow: visible; margin: 0; padding: 11px 13px;
    background: #FFFFFF; border: 1px solid {RULE}; border-radius: 3px;
    font-size: 0.96rem; line-height: 1.4; align-items: flex-start;
    transition: border-color 120ms ease, background 120ms ease;
}}
/* The five-point scale is tighter than a two-way choice, so it gets a smaller
   type size and is held to a single line each. */
.stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) {{ gap: 6px; }}
.stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label {{
    padding: 10px 7px; font-size: 0.82rem; align-items: center;
}}
.stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label,
.stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label div {{
    white-space: nowrap;
}}
.stRadio > div[role="radiogroup"] > label:hover {{ border-color: {SIGNAL}; background: #FBFDFE; }}
.stRadio > div[role="radiogroup"] > label:focus-within {{ outline: 2px solid {INK}; outline-offset: 1px; }}

/* Below tablet width five across stops fitting, so the scale stacks instead. */
@media (max-width: 680px) {{
    .stRadio > div[role="radiogroup"] {{ flex-wrap: wrap; }}
    .stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label,
    .stRadio > div[role="radiogroup"]:has(> label:nth-child(5)) > label div {{
        white-space: normal;
    }}
    .stRadio > div[role="radiogroup"] > label {{ flex: 1 1 46%; }}
}}
.stButton > button {{
    background: {SIGNAL}; color: #FFFFFF; border: 1px solid {SIGNAL}; border-radius: 3px;
    font-family: 'Archivo', sans-serif; font-weight: 600; letter-spacing: 0.01em;
    padding: 0.62rem 1.5rem; transition: background 140ms ease;
}}
.stButton > button:hover {{ background: #12556D; border-color: #12556D; color: #FFFFFF; }}
.stButton > button:focus-visible {{ outline: 2px solid {INK}; outline-offset: 2px; }}
.stDownloadButton > button {{
    background: #FFFFFF; color: {INK}; border: 1px solid {RULE}; border-radius: 3px; font-weight: 600;
}}
.stExpander {{ border: 1px solid {RULE} !important; border-radius: 3px !important; background: #FFFFFF; }}
[data-testid="stExpanderDetails"] {{ font-size: 0.92rem; }}
footer, #MainMenu {{ visibility: hidden; }}
[data-testid="stToolbar"] {{ display: none; }}
/* Streamlit adds an anchor link to headings; these are not linkable sections. */
.stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a, .stMarkdown h4 a {{ display: none; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def masthead(title: str, subtitle: str, eyebrow: str = "") -> None:
    st.markdown(
        f"""<div class="masthead">
              {f'<div class="chan">{html.escape(eyebrow)}</div>' if eyebrow else ''}
              <h1>{html.escape(title)}</h1>
              <p>{subtitle}</p>
            </div>""",
        unsafe_allow_html=True,
    )


def errorbar(channel: str, value: float, error: float, colour: str,
             vmax: float = 100.0, suffix: str = "") -> str:
    """One measured value with its uncertainty drawn as a band and a marker."""
    lo = max(0.0, value - error) / vmax * 100.0
    hi = min(vmax, value + error) / vmax * 100.0
    point = min(max(value / vmax * 100.0, 0.0), 100.0)
    pm = f'<span class="readout-pm">± {error:.0f}</span>' if error else ""
    return f"""<div class="readout">
      <div class="readout-head">
        <span class="chan">{html.escape(channel)}</span>
        <span class="readout-val">{value:.0f}{suffix}{pm}</span>
      </div>
      <div class="track">
        <div class="ci" style="left:{lo:.2f}%;width:{max(hi - lo, 0.6):.2f}%;background:{colour};color:{colour};"></div>
        <div class="pt" style="left:calc({point:.2f}% - 1.5px);background:{colour};"></div>
      </div>
    </div>"""


def panel(title: str, body_html: str, icon: str = "") -> None:
    head = f"{icon} {html.escape(title)}" if icon else html.escape(title)
    st.markdown(f'<div class="panel"><h4>{head}</h4>{body_html}</div>', unsafe_allow_html=True)


def caveat(title: str, body: str, bullets: list[str] | None = None) -> None:
    items = "".join(f"<li>{html.escape(b)}</li>" for b in (bullets or []))
    st.markdown(
        f'<div class="caveat"><b>{html.escape(title)}</b><br>{body}'
        f'{f"<ul>{items}</ul>" if items else ""}</div>',
        unsafe_allow_html=True,
    )


def meter(fraction: float) -> None:
    st.markdown(
        f'<div class="meter"><div style="width:{max(0.0, min(1.0, fraction)) * 100:.1f}%"></div></div>',
        unsafe_allow_html=True,
    )
