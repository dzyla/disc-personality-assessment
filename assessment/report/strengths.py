"""Strengths narrative: every theme reported with its cost, not only its upside."""

from __future__ import annotations


def narrative(result, themes: dict) -> dict:
    s = result.summary
    top, tied = s["top"], s["tied_with_fifth"]

    if tied:
        names = ", ".join(tied[:4]) + ("…" if len(tied) > 4 else "")
        tie_note = (
            f"<b>{len(tied)} other theme{'s' if len(tied) != 1 else ''} scored level with your fifth</b> "
            f"({names}). At this length the boundary of your top five is arbitrary; the themes above "
            f"are a cluster, not a ranking. The deep variant of this module separates them further."
        )
    else:
        tie_note = "Your top five separate cleanly from the rest — the boundary is real, not an artefact of where the list was cut."

    def card(name: str) -> dict:
        theme = themes[name]
        return {
            "name": name,
            "domain": theme["domain"],
            "colour": theme["badge_color"],
            "tagline": theme["tagline"],
            "description": theme["description"],
            "action": theme["action_tip"],
            "shadow": theme["shadow"],
            "overuse": theme["overuse"],
            "win_rate": s["win_rates"][name],
            "wins": s["wins"][name],
            "exposure": s["exposure"][name],
            "evidence": [e for e in result.detail["evidence"][name] if e["chosen"]][:4],
        }

    bottom = [
        {
            "name": name,
            "domain": themes[name]["domain"],
            "tagline": themes[name]["tagline"],
            "win_rate": s["win_rates"][name],
            "exposure": s["exposure"][name],
        }
        for name in reversed(s["bottom"])
    ]

    return {
        "tie_note": tie_note,
        "top": [card(n) for n in top],
        "supporting": [
            {"name": n, "domain": themes[n]["domain"], "tagline": themes[n]["tagline"],
             "win_rate": s["win_rates"][n]}
            for n in s["supporting"]
        ],
        "bottom": bottom,
        "bottom_note": (
            "These came last not because you are bad at them but because you did not choose them "
            "when something else was on offer. They are what you systematically deprioritise — which "
            "is exactly where a team will feel your absence."
        ),
        "domains": s["domain_percentages"],
    }
