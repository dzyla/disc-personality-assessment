"""DISC narrative, written to respect the confidence in the numbers."""

from __future__ import annotations

from ..scoring.disc import STYLE_NAMES

PRIMARY = {
    "D": "Your core operating mode is proactive and resolute. You are energised by clearing obstacles, taking initiative and driving to a tangible result, and you want the authority to decide without waiting for permission.",
    "I": "Your core operating mode is expressive and relational. You think out loud, build momentum through people, and do your best work where there is dialogue, visible enthusiasm and shared credit.",
    "S": "Your core operating mode is patient and dependable. You build trust that lasts, hold a steady pace through long work, and act as the part of a team that other people plan around.",
    "C": "Your core operating mode is analytical and exacting. You take problems apart, want decisions grounded in something checkable, and take real satisfaction in work that holds up under scrutiny.",
}

BLEND = {
    "D-I": "Your influence adds persuasion to the drive: you pull people with you rather than only pushing.",
    "D-S": "Your steadiness tempers the drive with patience, so momentum arrives without leaving people behind.",
    "D-C": "Your conscientiousness makes the drive precise: you want speed <i>and</i> a defensible answer.",
    "I-D": "Your dominance turns enthusiasm into delivery — you move from the idea to the doing faster than most.",
    "I-S": "Your steadiness gives the warmth depth: people experience you as genuinely interested, not just sociable.",
    "I-C": "Your conscientiousness anchors the enthusiasm, so what you propose tends to survive contact with the detail.",
    "S-D": "Your dominance gives the patience a spine: when it matters you will hold a line.",
    "S-I": "Your influence makes the steadiness sociable — you are the person who keeps a group connected.",
    "S-C": "Your conscientiousness makes the reliability exact: things you own do not get dropped.",
    "C-D": "Your dominance turns analysis into argument: you do not just find the flaw, you press for the fix.",
    "C-I": "Your influence lets you translate the analysis for people who will never read it.",
    "C-S": "Your steadiness makes the rigour sustainable — thorough, and still there in month nine.",
}

BLIND_SPOT = {
    "D": "Dominance is your lowest dimension. You look for agreement before acting, which reads as collaborative right up until a decision needs an owner and nobody claims it. The cost lands on whoever eventually does.",
    "I": "Influence is your lowest dimension. You let the work speak, which is honourable and unreliable: people who never hear from you form their view of your work from someone else's account of it.",
    "S": "Steadiness is your lowest dimension. You move on quickly, and the people who needed the previous plan to hold are still working to it. The change is rarely the problem; the notice is.",
    "C": "Conscientiousness is your lowest dimension. You act on the gist, which is fast and occasionally expensive. The detail you skipped tends to reappear as someone else's emergency.",
}

# Written from the other person's point of view on purpose. The point is what
# you are like to work with, not what you intend.
FRICTION = {
    "D": [
        ("high S", "Decisions arrive already made and they are expected to absorb the change. What helps: the reasoning, and a day's notice before it is final."),
        ("high C", "Your speed reads as not having checked. What helps: saying what you did check, and what you consciously chose not to."),
    ],
    "I": [
        ("high C", "Your energy reads as a claim that has not been evidenced yet. What helps: putting the specifics in writing before you pitch."),
        ("high D", "Discussion feels like delay when they wanted a decision. What helps: leading with the recommendation, then the reasoning."),
    ],
    "S": [
        ("high D", "Your caution reads as resistance. What helps: naming what you need in order to move, rather than what worries you."),
        ("high I", "Your reserve reads as disapproval. What helps: saying the positive part out loud; they cannot infer it."),
    ],
    "C": [
        ("high I", "Your questions land as scepticism about them personally. What helps: separating the challenge to the claim from your view of the person."),
        ("high D", "Your thoroughness reads as an unwillingness to commit. What helps: giving a provisional answer with its confidence attached."),
    ],
}

ENVIRONMENT = {
    "D": "Fast-moving and meritocratic, with real autonomy, visible measures, and little between a decision and its consequence.",
    "I": "Collaborative and vocal, where ideas get aired early, contribution is acknowledged out loud, and work is done with people rather than beside them.",
    "S": "Stable and considerate, with predictable expectations, enough notice before change, and colleagues who stay long enough to build trust.",
    "C": "Structured and rigorous, with access to reliable information, time to do the work properly, and respect for craftsmanship.",
}

HEDGES = {
    "High": ("Your answers were internally consistent, so the profile below can be read at face value.", ""),
    "Moderate": ("Your answers were broadly consistent. Treat the shape as reliable and the exact numbers as approximate.", "on balance, "),
    "Low": ("Your answers did not hold together well enough to support a confident profile. What follows is the best reading of them, but treat every claim below as a question to check rather than a finding.", "on this evidence, and tentatively, "),
}


def narrative(result, confidence: dict, descriptions: dict) -> dict:
    s = result.summary
    norm, se = s["normalized"], s["standard_error"]
    primary, secondary, lowest = s["primary"], s["secondary"], s["lowest"]
    level = confidence["level"]
    caveat, hedge = HEDGES[level]

    style_info = descriptions["single"].get(s["style_code"], descriptions.get("balanced", {}))

    sep = result.detail["primary_vs_secondary"]
    if sep["separated"]:
        order_claim = (
            f"{STYLE_NAMES[primary]} is {hedge}your leading dimension at "
            f"<b>{norm[primary]:.0f} ± {se[primary]:.0f}</b>, clear of "
            f"{STYLE_NAMES[secondary]} at <b>{norm[secondary]:.0f} ± {se[secondary]:.0f}</b>."
        )
    else:
        order_claim = (
            f"{STYLE_NAMES[primary]} ({norm[primary]:.0f} ± {se[primary]:.0f}) and "
            f"{STYLE_NAMES[secondary]} ({norm[secondary]:.0f} ± {se[secondary]:.0f}) are "
            f"<b>too close to separate</b> at this length — the {sep['difference']:.0f}-point gap "
            f"is inside the measurement error. Read them as a blend rather than a ranking; "
            f"neither one is your “real” style."
        )

    claims = [
        {
            "title": "How you operate",
            "text": PRIMARY[primary],
            "evidence": result.detail["evidence"][primary],
        },
        {
            "title": "The blend",
            "text": BLEND.get(f"{primary}-{secondary}", "Your two leading dimensions combine into a genuinely mixed style."),
            "evidence": result.detail["evidence"][secondary],
        },
        {
            "title": "Your blind spot",
            "text": BLIND_SPOT[lowest],
            "evidence": result.detail["evidence"][lowest],
        },
    ]

    pace_word = "fast and proactive" if s["pace"] >= 0 else "deliberate and measured"
    focus_word = "people and relationships" if s["focus"] >= 0 else "tasks and logic"

    return {
        "confidence_caveat": caveat,
        "order_claim": order_claim,
        "separated": sep["separated"],
        "title": style_info.get("title", "Your DISC profile"),
        "headline": style_info.get("headline", ""),
        "claims": claims,
        "tempo": (
            f"Your tempo reads as <b>{pace_word}</b> (pace {s['pace']:+.0f}) with attention on "
            f"<b>{focus_word}</b> (focus {s['focus']:+.0f}). Style intensity: <b>{s['intensity'].lower()}</b>."
        ),
        "environment": ENVIRONMENT[primary],
        "friction": FRICTION[primary],
        "strengths": style_info.get("strengths", ""),
        "challenges": style_info.get("challenges", ""),
        "communication": style_info.get("communication_tips", ""),
        "motivators": style_info.get("motivators", ""),
        "stress_triggers": style_info.get("stress_triggers", ""),
        "under_pressure": style_info.get("under_pressure", ""),
    }
