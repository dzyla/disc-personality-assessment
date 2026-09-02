"""Matplotlib figures, styled to match the page and reused by the PDF."""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from assessment.scoring.disc import STYLE_ANGLES  # noqa: E402

from . import components as ui  # noqa: E402

LABELS = {
    "D": "D  Dominance",
    "I": "I  Influence",
    "S": "S  Steadiness",
    "C": "C  Conscientiousness",
}


def _resultant(normalized: dict[str, float]) -> tuple[float, float]:
    x = sum(normalized[s] / 100.0 * math.cos(STYLE_ANGLES[s]) for s in "DISC")
    y = sum(normalized[s] / 100.0 * math.sin(STYLE_ANGLES[s]) for s in "DISC")
    return math.atan2(y, x) % (2 * math.pi), math.hypot(x, y)


def circumplex(normalized: dict[str, float], adaptive: dict[str, float] | None = None):
    fig, ax = plt.subplots(figsize=(5.4, 5.4), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(ui.PAPER)
    ax.set_facecolor("#FFFFFF")
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.0)

    for style, angle in STYLE_ANGLES.items():
        ax.bar(x=angle, height=1.0, width=np.pi / 2, bottom=0.0,
               color=ui.STYLE_COLOURS[style], alpha=0.07, edgecolor="none")

    grid = np.linspace(0, 2 * np.pi, 180)
    for radius in (0.25, 0.5, 0.75):
        ax.plot(grid, [radius] * len(grid), color=ui.RULE, linewidth=0.7, zorder=1)
    ax.plot(grid, [1.0] * len(grid), color="#C3CDD7", linewidth=1.0, zorder=2)
    for angle in (0, np.pi / 2, np.pi, 3 * np.pi / 2):
        ax.plot([angle, angle], [0, 1.0], color=ui.RULE, linewidth=0.7, zorder=1)

    ax.set_xticks(list(STYLE_ANGLES.values()))
    ax.set_xticklabels([LABELS[s] for s in STYLE_ANGLES], fontsize=8.5, color=ui.SLATE)
    ax.tick_params(pad=11)
    ax.set_yticklabels([])
    ax.grid(False)
    ax.spines["polar"].set_visible(False)

    angle, magnitude = _resultant(normalized)
    radius = min(max(magnitude, 0.05), 1.0)

    if adaptive is not None:
        a_angle, a_magnitude = _resultant(adaptive)
        a_radius = min(max(a_magnitude, 0.05), 1.0)
        ax.annotate(
            "", xy=(a_angle, a_radius), xytext=(angle, radius),
            arrowprops={"arrowstyle": "-|>", "color": ui.SLATE, "linewidth": 1.2,
                        "linestyle": (0, (3, 2)), "shrinkA": 6, "shrinkB": 6},
        )
        ax.plot(a_angle, a_radius, "o", markersize=10, markerfacecolor="#FFFFFF",
                markeredgecolor=ui.SIGNAL, markeredgewidth=2.0, zorder=10)
        ax.annotate("at work", xy=(a_angle, a_radius), xytext=(6, -14),
                    textcoords="offset points", fontsize=8, color=ui.SLATE)
        ax.annotate("natural", xy=(angle, radius), xytext=(6, 8),
                    textcoords="offset points", fontsize=8, color=ui.SLATE)

    ax.plot(angle, radius, "o", markersize=11, color=ui.SIGNAL,
            markeredgecolor="#FFFFFF", markeredgewidth=1.8, zorder=11)

    fig.tight_layout()
    return fig
