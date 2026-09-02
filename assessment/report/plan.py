"""Three experiments for the coming week, derived from this profile rather than
from generic advice. Each one is small enough to actually run and specific
enough to be wrong."""

from __future__ import annotations

from ..scoring.disc import STYLE_NAMES

BLIND_SPOT_EXPERIMENT = {
    "D": ("Own one decision outright",
          "Pick a decision this week that is genuinely yours and make it without seeking agreement first. "
          "Announce it afterwards with your reasoning. Notice whether the disagreement you were avoiding actually arrives."),
    "I": ("Send one unsolicited update",
          "Pick someone who would not otherwise see your work in progress and send them a short update on it. "
          "You are testing whether visibility costs you anything, or only feels like it should."),
    "S": ("Give notice before the next change",
          "Before your next change of plan, tell the two people most affected a day early and ask what it breaks for them. "
          "The change is rarely the problem; the notice is."),
    "C": ("Decide once without checking",
          "Take one decision you would normally research and make it on what you already know. Write down what you "
          "would have checked. At the end of the week, see whether it would have changed the answer."),
}

STRESS_EXPERIMENT = {
    "push": ("Put one day between pressure and action",
             "Next time the load spikes, wait a full day before acting on the first plan you form. Keep the plan; "
             "compare it with the one you have a day later."),
    "perform": ("Say the unflattering accurate thing",
                "In your next tense meeting, say one thing that is accurate and not reassuring. Notice whether the room "
                "handles it better than you expected."),
    "accommodate": ("Say no once, in the moment",
                    "Decline one thing this week that you would normally absorb, and decline it at the time rather than "
                    "resenting it later. One sentence, no justification."),
    "retreat": ("Set a decide-by date out loud",
                "The next time you want more data, pick the date you will decide without it and tell someone that date. "
                "The commitment is the point."),
}


def build(disc_result, strengths_narrative, stress_result, strain, motivator_result) -> list[dict]:
    experiments: list[dict] = []

    if disc_result is not None:
        lowest = disc_result.summary["lowest"]
        title, body = BLIND_SPOT_EXPERIMENT[lowest]
        experiments.append({
            "title": title,
            "why": f"{STYLE_NAMES[lowest]} is your lowest dimension.",
            "body": body,
        })

    if strengths_narrative and strengths_narrative["top"]:
        top = strengths_narrative["top"][0]
        experiments.append({
            "title": f"Catch {top['name']} overshooting",
            "why": f"{top['name']} is your leading theme, and every leading theme has a version that costs you.",
            "body": (
                f"{top['overuse']} Watch for one instance of that this week and write down what it cost. "
                f"You are not trying to stop doing it — you are trying to notice it while it is happening."
            ),
        })

    if stress_result is not None:
        mode = stress_result.summary["dominant"]
        title, body = STRESS_EXPERIMENT[mode]
        experiments.append({
            "title": title,
            "why": f"Your dominant pressure mode is {mode}.",
            "body": body,
        })
    elif strain is not None and strain["band"] in ("high", "moderate"):
        largest = strain["largest"]
        experiments.append({
            "title": f"Find where the {STYLE_NAMES[largest]} stretch happens",
            "why": f"Your work profile sits {abs(strain['shifts'][largest]['delta']):.0f} points from your natural one on {STYLE_NAMES[largest]}.",
            "body": (
                "Identify the single recurring meeting where that stretch is largest. Change one thing about how you "
                "run it — who speaks first, how it is prepared, or whether you need to be in it at all."
            ),
        })
    elif motivator_result is not None:
        top = motivator_result.summary["top"][0]
        experiments.append({
            "title": f"Buy yourself more {top}",
            "why": f"{top} was the driver you traded for most consistently.",
            "body": (
                f"Name one concrete change to next week that would give you measurably more {top.lower()}. "
                f"Not a plan for the year — one change, next week, that you can make yourself."
            ),
        })

    return experiments[:3]
