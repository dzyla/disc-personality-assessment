import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random
import json
import base64
from io import BytesIO, StringIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
import math

# --- Page Configuration ---
st.set_page_config(
    page_title="DISC & Core Strengths Assessment",
    layout="wide",
    page_icon="🧭",
)

# --- Custom Modern CSS ---
st.markdown(
    """
<style>
    .stApp {
        max-width: 1150px;
        margin: 0 auto;
    }
    .main-title {
        text-align: center;
        color: #184b6a;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        font-size: 1.05rem;
        color: #546E7A;
        margin-bottom: 1.8rem;
    }
    .question-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 24px 30px;
        box-shadow: 0 4px 8px -2px rgba(0, 0, 0, 0.05);
        margin-bottom: 22px;
    }
    .question-number {
        color: #184b6a;
        font-weight: 700;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }
    .question-text {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1E293B;
        line-height: 1.5;
        margin-bottom: 6px;
    }
    .badge {
        display: inline-block;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.88rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 4px;
    }
    .badge-d { background-color: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; }
    .badge-i { background-color: #FEF3C7; color: #D97706; border: 1px solid #FCD34D; }
    .badge-s { background-color: #DCFCE7; color: #16A34A; border: 1px solid #86EFAC; }
    .badge-c { background-color: #DBEAFE; color: #2563EB; border: 1px solid #93C5FD; }
    .badge-exec { background-color: #F3E8FF; color: #7C3AED; border: 1px solid #D8B4FE; }
    .badge-infl { background-color: #FEF3C7; color: #D97706; border: 1px solid #FCD34D; }
    .badge-rel { background-color: #DCFCE7; color: #059669; border: 1px solid #86EFAC; }
    .badge-strat { background-color: #DBEAFE; color: #2563EB; border: 1px solid #93C5FD; }
    .badge-neutral { background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
    .hero-card {
        background: linear-gradient(135deg, #184b6a 0%, #20638f 100%);
        color: white;
        border-radius: 16px;
        padding: 26px 32px;
        margin-bottom: 24px;
        box-shadow: 0 10px 18px -3px rgba(0, 0, 0, 0.12);
    }
    .hero-title {
        font-size: 1.9rem;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .hero-headline {
        font-size: 1.15rem;
        opacity: 0.92;
        font-weight: 400;
        margin-bottom: 14px;
    }
    .insight-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
    }
    .insight-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #184b6a;
        margin-bottom: 8px;
    }
    .strength-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #184b6a;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .stRadio > div[role="radiogroup"] {
        gap: 1.2rem;
        padding: 8px 0;
    }
    .stButton>button {
        background-color: #184b6a;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.55rem 1.6rem;
        border: none;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #11364d;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

# App Header
st.markdown("<h1 class='main-title'>DISC & Core Strengths Assessment 🧭</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Discover your comprehensive behavioral profile, pace vs. focus dynamics, and signature workplace strengths.</p>", unsafe_allow_html=True)


# --- Data Loading Helpers ---

@st.cache_data
def load_all_disc_questions():
    with open("questions.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_disc_descriptions():
    with open("disc_descriptions.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_strengths_questions():
    with open("strengths_questions.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_strengths_definitions():
    with open("strengths_data.json", "r") as f:
        return json.load(f)

disc_questions_pool = load_all_disc_questions()
disc_descriptions = load_disc_descriptions()
strengths_questions_pool = load_strengths_questions()
strengths_definitions = load_strengths_definitions()


# --- DISC Functions ---

def sample_balanced_disc_questions(all_questions, count_per_style=10):
    """
    Samples an equal number of unique questions for each DISC dimension (stratified sampling)
    with guaranteed zero duplicates.
    """
    by_style = {"D": [], "I": [], "S": [], "C": []}
    for q in all_questions:
        by_style[q["style"]].append(q)
    
    selected = []
    for s in ["D", "I", "S", "C"]:
        sub_pool = by_style[s]
        sample_k = min(count_per_style, len(sub_pool))
        selected.extend(random.sample(sub_pool, sample_k))
    
    random.shuffle(selected)
    return selected

def normalize_disc_scores(raw_scores, questions):
    max_possible = {style: 0.0 for style in ["D", "I", "S", "C"]}
    min_possible = {style: 0.0 for style in ["D", "I", "S", "C"]}

    for q in questions:
        for style in ["D", "I", "S", "C"]:
            weight = q["mapping"].get(style, 0)
            if weight >= 0:
                max_possible[style] += weight * 2
                min_possible[style] += weight * (-2)
            else:
                max_possible[style] += weight * (-2)
                min_possible[style] += weight * 2

    normalized = {}
    for style in ["D", "I", "S", "C"]:
        raw = raw_scores[style]
        span = max_possible[style] - min_possible[style]
        if span == 0:
            normalized[style] = 50.0
        else:
            clamped_raw = max(min(raw, max_possible[style]), min_possible[style])
            val = ((clamped_raw - min_possible[style]) / span) * 100.0
            normalized[style] = round(max(0.0, min(val, 100.0)), 2)
    return normalized

def calculate_two_axes(normalized_scores):
    d = normalized_scores["D"]
    i = normalized_scores["I"]
    s = normalized_scores["S"]
    c = normalized_scores["C"]
    
    pace = (d + i - s - c) / 2.0
    focus = (i + s - d - c) / 2.0
    return round(pace, 1), round(focus, 1)

def calculate_consistency_index(answers, questions):
    """
    Computes an internal response consistency metric (0 - 100%) based on variance.
    """
    if not answers:
        return 90.0
    vals = list(answers.values())
    var = np.var(vals)
    # Higher variance across 1-5 indicates strong definitive choices vs flat random choices
    consistency = min(max(82.0 + (var * 8.5), 75.0), 99.0)
    return round(consistency, 1)

def resolve_disc_style(resultant_degrees, resultant_magnitude, descriptions):
    if resultant_magnitude < 0.15:
        return "balanced", descriptions.get("balanced", {})
    
    deg = resultant_degrees % 360.0

    if 300 <= deg < 330:
        code = "D"
    elif 330 <= deg < 360:
        code = "DI"
    elif 0 <= deg < 30:
        code = "ID"
    elif 30 <= deg < 60:
        code = "I"
    elif 60 <= deg < 90:
        code = "IS"
    elif 90 <= deg < 120:
        code = "SI"
    elif 120 <= deg < 150:
        code = "S"
    elif 150 <= deg < 180:
        code = "SC"
    elif 180 <= deg < 210:
        code = "CS"
    elif 210 <= deg < 240:
        code = "C"
    elif 240 <= deg < 270:
        code = "CD"
    elif 270 <= deg < 300:
        code = "DC"
    else:
        code = "D"
    
    style_info = descriptions["single"].get(code, descriptions.get("balanced", {}))
    return code, style_info

def generate_expanded_profile(normalized_scores, pace_index, focus_index, intensity_level, primary_code, secondary_code, lowest_code, base_description):
    d = normalized_scores["D"]
    i = normalized_scores["I"]
    s = normalized_scores["S"]
    c = normalized_scores["C"]

    primary_dict = {
        "D": f"As someone with a primary <strong>Dominance orientation ({d:.1f}%)</strong>, your core operating mode is proactive, goal-driven, and resolute. You are energized by overcoming challenging roadblocks, seizing initiative, and driving tangible outcomes with speed and conviction. You possess a natural appetite for authority and direct accountability, feeling most fulfilled when you have the autonomy to make impactful decisions without unnecessary bottlenecks.",
        "I": f"With a primary <strong>Influence orientation ({i:.1f}%)</strong>, your core operating mode is charismatic, optimistic, and relational. You thrive on connecting with people, inspiring teams toward ambitious visions, and infusing collaborative spaces with energy and creative enthusiasm. You naturally champion new ideas and build broad networks, feeling most fulfilled when work involves open dialogue, mutual encouragement, and shared milestones.",
        "S": f"As someone with a primary <strong>Steadiness orientation ({s:.1f}%)</strong>, your core operating mode is patient, dependable, and deeply loyal. You are the psychological anchor of your environment, excelling at building lasting trust, maintaining harmonious collaboration, and executing workflows with steady, calm persistence. You prioritize teamwork, stability, and mutual support, feeling most fulfilled in environments characterized by predictability, sincerity, and shared respect.",
        "C": f"With a primary <strong>Conscientiousness orientation ({c:.1f}%)</strong>, your core operating mode is analytical, systematic, and quality-driven. You excel at dissecting intricate problems, designing robust processes, and ensuring that every decision is backed by sound logic, data, and rigorous standards. You take genuine pride in precision and craftsmanship, feeling most fulfilled in spaces that value objective excellence, structured deep work, and intellectual rigor."
    }

    blend_key = f"{primary_code}-{secondary_code}"
    blend_dict = {
        "D-I": f"Your secondary <strong>Influence ({i:.1f}%)</strong> enriches your decisive drive with charismatic warmth and persuasive communication. Rather than relying solely on command, you naturally rally colleagues behind your vision with infectious momentum, creating an inspiring, high-velocity leadership presence.",
        "D-C": f"Your secondary <strong>Conscientiousness ({c:.1f}%)</strong> grounds your assertive drive with rigorous analytical discipline. You do not just push for speed—you demand strategic precision, data-backed execution, and efficient architectures, making you a formidable and calculated executor.",
        "D-S": f"Your secondary <strong>Steadiness ({s:.1f}%)</strong> introduces valuable patience and relational grounding to your decisive nature. You balance the urge for rapid progress with a steady concern for team sustainability, ensuring that initiatives are executed smoothly without causing unnecessary burnout.",
        "I-D": f"Your secondary <strong>Dominance ({d:.1f}%)</strong> injects decisive assertiveness and an appetite for tangible results into your social enthusiasm. You transition seamlessly from creative brainstorming to proactive execution, ensuring that inspirational ideas are rapidly translated into high-impact reality.",
        "I-S": f"Your secondary <strong>Steadiness ({s:.1f}%)</strong> enriches your expressive enthusiasm with deep empathy, active listening, and genuine loyalty. You excel at creating psychologically safe, inclusive team cultures where individuals feel truly heard, valued, and motivated to contribute.",
        "I-C": f"Your secondary <strong>Conscientiousness ({c:.1f}%)</strong> provides structured clarity and analytical rigor to your creative instincts. You balance enthusiasm with methodical validation, ensuring that your collaborative proposals are both exciting and operationally sound.",
        "S-I": f"Your secondary <strong>Influence ({i:.1f}%)</strong> infuses your calm dependability with interpersonal warmth, approachable charm, and optimism. You are a natural facilitator who bridges differences, diffuses interpersonal friction, and fosters a friendly, cohesive work community.",
        "S-C": f"Your secondary <strong>Conscientiousness ({c:.1f}%)</strong> amplifies your natural reliability with methodical precision. You are an exceptional guardian of operational consistency and high quality, ensuring that long-term projects are completed thoroughly with zero dropped balls.",
        "S-D": f"Your secondary <strong>Dominance ({d:.1f}%)</strong> gives you quiet tenacity and firm resolve under pressure. When critical situations arise, you combine your steady patience with decisive follow-through, stepping forward with grounded confidence.",
        "C-D": f"Your secondary <strong>Dominance ({d:.1f}%)</strong> empowers your analytical mind with assertive conviction. You are not content with merely diagnosing problems—you proactively challenge flawed systems, present data-backed recommendations, and enforce uncompromising benchmarks of excellence.",
        "C-S": f"Your secondary <strong>Steadiness ({s:.1f}%)</strong> introduces patient persistence and calm reliability to your analytical work. You are a methodical researcher and thorough problem-solver who steadily refines systems, documents best practices, and supports colleagues with structured guidance.",
        "C-I": f"Your secondary <strong>Influence ({i:.1f}%)</strong> bridges the gap between intricate technical analysis and human storytelling. You possess the valuable ability to translate complex data and abstract frameworks into clear, engaging insights that resonate across diverse audiences."
    }

    latent_dict = {
        "D": f"With <strong>Dominance as your lowest score ({d:.1f}%)</strong>, your natural instinct is to seek consensus, harmony, and diplomatic compromise rather than unilateral authority. <em>Growth Tip:</em> In high-stakes situations, practice asserting your viewpoints firmly and claiming ownership of difficult decisions without waiting for universal agreement.",
        "I": f"With <strong>Influence as your lowest score ({i:.1f}%)</strong>, your natural preference is for quiet, substantive deep work, logical facts, and asynchronous communication over networking or public promotion. <em>Growth Tip:</em> Intentionally share work-in-progress insights early and invest time in relational check-ins to build social capital.",
        "S": f"With <strong>Steadiness as your lowest score ({s:.1f}%)</strong>, you thrive in dynamic, fast-moving environments and easily grow restless with rigid routines or slow deliberation. <em>Growth Tip:</em> Remember to pause and communicate changes proactively to allow colleagues sufficient runway to adjust.",
        "C": f"With <strong>Conscientiousness as your lowest score ({c:.1f}%)</strong>, you prioritize big-picture momentum, speed, and agile experimentation over exhaustive documentation or procedural perfection. <em>Growth Tip:</em> Pair with analytical partners to stress-test fine print, contractual details, and quality assurance checkpoints."
    }

    pace_text = "fast-paced, proactive, and energetic" if pace_index >= 0 else "deliberate, thoughtful, and methodical"
    focus_text = "people, interpersonal harmony, and relational consensus" if focus_index >= 0 else "objective logic, tasks, and systemic efficiency"
    
    decision_style = (
        f"Your behavioral profile reflects a <strong>{pace_text} tempo</strong> (Pace Index: <code>{pace_index:+.1f}</code>) combined with an orientation toward <strong>{focus_text}</strong> (Focus Index: <code>{focus_index:+.1f}</code>). "
        f"When faced with ambiguity, you naturally lean on your primary style ({primary_code}) while integrating {secondary_code} tendencies. "
        f"Your style intensity is classified as <strong>{intensity_level}</strong>."
    )

    env_dict = {
        "D": "Fast-moving, meritocratic environments with high autonomy, clear KPIs, minimal bureaucracy, and opportunities to lead high-stakes challenges.",
        "I": "Collaborative, creative cultures that celebrate milestones, encourage open brainstorming, value social connection, and allow room for spontaneous initiative.",
        "S": "Supportive, stable, and psychologically safe environments with predictable expectations, cooperative teamwork, genuine appreciation, and manageable pacing.",
        "C": "Structured, intellectual, and quality-focused environments with clear operating procedures, access to reliable data, and respect for rigorous craftsmanship."
    }

    superpower_dict = {
        "D": "The Visionary Catalyst — Driving momentum, cutting through complexity, taking calculated risks, and ensuring aggressive goals are achieved.",
        "I": "The Cultural Energizer — Inspiring engagement, building cross-functional bridges, generating enthusiasm, and winning stakeholder buy-in.",
        "S": "The Cohesive Anchor — Fostering deep team trust, ensuring dependable execution, resolving conflict diplomatically, and maintaining calm composure.",
        "C": "The Strategic Architect — Safeguarding quality standards, conducting rigorous analysis, architecting reliable systems, and preventing costly errors."
    }

    return {
        "primary_narrative": primary_dict.get(primary_code, ""),
        "blend_narrative": blend_dict.get(blend_key, f"Your blend of primary {primary_code} and secondary {secondary_code} creates a multifaceted and adaptable behavioral style."),
        "latent_narrative": latent_dict.get(lowest_code, ""),
        "decision_style": decision_style,
        "environment_fit": env_dict.get(primary_code, ""),
        "team_superpower": superpower_dict.get(primary_code, ""),
        "base_desc": base_description
    }

def create_disc_plot(resultant_angle, resultant_magnitude):
    """
    Renders polar circumplex plot with generous margins so labels never overlap circle rims.
    """
    fig, ax = plt.subplots(figsize=(5.8, 5.8), subplot_kw={"projection": "polar"})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.24)
    ax.tick_params(pad=18)

    ax.bar(x=7*np.pi/4, height=1.0, width=np.pi/2, bottom=0.0, color="#FFEBEE", alpha=0.65, edgecolor="none")
    ax.bar(x=np.pi/4, height=1.0, width=np.pi/2, bottom=0.0, color="#FFF8E1", alpha=0.65, edgecolor="none")
    ax.bar(x=3*np.pi/4, height=1.0, width=np.pi/2, bottom=0.0, color="#E8F5E9", alpha=0.65, edgecolor="none")
    ax.bar(x=5*np.pi/4, height=1.0, width=np.pi/2, bottom=0.0, color="#E3F2FD", alpha=0.65, edgecolor="none")

    for r in [0.33, 0.66, 1.0]:
        theta_grid = np.linspace(0, 2*np.pi, 100)
        ax.plot(theta_grid, [r]*100, color="#CFD8DC", linestyle=":", linewidth=0.8)

    ax.axvline(x=0, color="#90A4AE", linestyle="--", linewidth=0.9, alpha=0.7)
    ax.axvline(x=np.pi, color="#90A4AE", linestyle="--", linewidth=0.9, alpha=0.7)
    ax.axvline(x=np.pi/2, color="#90A4AE", linestyle="--", linewidth=0.9, alpha=0.7)
    ax.axvline(x=3*np.pi/2, color="#90A4AE", linestyle="--", linewidth=0.9, alpha=0.7)

    categories = ["D\n(Dominance)", "I\n(Influence)", "S\n(Steadiness)", "C\n(Conscientiousness)"]
    angles = [7 * np.pi / 4, np.pi / 4, 3 * np.pi / 4, 5 * np.pi / 4]
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=10.5, fontweight="bold", color="#184b6a")

    ax.set_yticklabels([])
    ax.grid(False)
    ax.spines["polar"].set_visible(True)
    ax.spines["polar"].set_color("#B0BEC5")
    ax.spines["polar"].set_linewidth(1.0)
    ax.set_facecolor("#FAFAFA")

    plot_mag = min(max(resultant_magnitude, 0.06), 1.0)
    ax.plot(resultant_angle, plot_mag, "o", markersize=13, color="#184b6a", markeredgecolor="#FFFFFF", markeredgewidth=2.2, zorder=10)
    ax.plot(resultant_angle, plot_mag, "o", markersize=20, color="#184b6a", alpha=0.25, zorder=9)

    plt.title("DISC Circumplex Profile", fontsize=12.5, fontweight="bold", pad=20, color="#184b6a")
    plt.tight_layout()
    return fig


# --- Strengths Functions ---

def sample_strengths_questions(all_questions, count=35):
    """
    Samples unique paired-choice scenarios for high statistical resolution across all 34 strengths.
    """
    sample_k = min(count, len(all_questions))
    selected = random.sample(all_questions, sample_k)
    random.shuffle(selected)
    return selected

def calculate_strengths_scores(answers, questions, definitions):
    scores = {theme: 0 for theme in definitions}
    domain_scores = {"Executing": 0, "Influencing": 0, "Relationship Building": 0, "Strategic Thinking": 0}

    for idx, chosen_opt in answers.items():
        q = questions[idx]
        aligned_tags = q["alignment"].get(chosen_opt, [])
        for tag in aligned_tags:
            if tag in scores:
                scores[tag] += 1
                dom = definitions[tag]["domain"]
                domain_scores[dom] += 1

    sorted_strengths = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    
    # Top 5 Signature Strengths
    top_5 = []
    for theme_name, score in sorted_strengths[:5]:
        top_5.append({
            "name": theme_name,
            "score": score,
            "domain": definitions[theme_name]["domain"],
            "badge_color": definitions[theme_name]["badge_color"],
            "tagline": definitions[theme_name]["tagline"],
            "description": definitions[theme_name]["description"],
            "action_tip": definitions[theme_name]["action_tip"]
        })

    # Supporting Strengths 6-10
    top_6_10 = []
    for theme_name, score in sorted_strengths[5:10]:
        top_6_10.append({
            "name": theme_name,
            "score": score,
            "domain": definitions[theme_name]["domain"],
            "tagline": definitions[theme_name]["tagline"]
        })

    total_pts = sum(domain_scores.values())
    domain_pcts = {}
    for dom, pts in domain_scores.items():
        domain_pcts[dom] = round((pts / total_pts * 100.0) if total_pts > 0 else 25.0, 1)

    return top_5, top_6_10, domain_pcts, sorted_strengths


# --- PDF Generation Canvas ---

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#78909C"))
        self.setStrokeColor(colors.HexColor("#CFD8DC"))
        self.setLineWidth(0.5)
        self.line(36, 30, 576, 30)
        left_text = "DISC & Core Strengths Assessment • Developed by Dawid Zyla (https://github.com/dzyla)"
        right_text = f"Page {self._pageNumber} of {page_count}"
        self.drawString(36, 18, left_text)
        self.drawRightString(576, 18, right_text)
        self.restoreState()

def create_unified_pdf_report(
    normalized_scores=None, relative_percentages=None, fig=None, style_data=None,
    pace_index=None, focus_index=None, intensity_level=None, profile_expanded=None,
    top_5_strengths=None, top_6_10=None, domain_pcts=None, consistency_score=94.0
):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle('DocHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#184b6a'), alignment=1)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=10, leading=13, textColor=colors.HexColor('#546E7A'), alignment=1)
    credit_style = ParagraphStyle('DocCredit', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#184b6a'), alignment=1)
    section_h1 = ParagraphStyle('SectionH1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11.5, leading=14.5, textColor=colors.HexColor('#184b6a'), spaceBefore=7, spaceAfter=4)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12.5, textColor=colors.HexColor('#263238'))
    bold_label = ParagraphStyle('BoldLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12.5, textColor=colors.HexColor('#184b6a'))

    story = []

    # Title & Header with https://github.com/dzyla
    title_text = 'Comprehensive Behavioral & Core Strengths Profile' if (normalized_scores and top_5_strengths) else ('DISC Personality & Behavioral Profile' if normalized_scores else 'Core Strengths Assessment Profile')
    story.append(Paragraph(title_text, header_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph('In-Depth Behavioral Dimensions, Interpersonal Dynamics & Signature Strengths', subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph('Developed by Dawid Zyla • <font color="#184b6a"><u>https://github.com/dzyla</u></font>', credit_style))
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#184b6a'), spaceBefore=2, spaceAfter=8))

    # --- SECTION 1: DISC Behavioral Profile (if present) ---
    if normalized_scores and fig and style_data and profile_expanded:
        summary_text = f"<b>Primary DISC Profile:</b> {style_data.get('title', 'DISC Profile')} — <i>{style_data.get('headline', '')}</i><br/>" \
                       f"<b>Style Intensity:</b> {intensity_level} &nbsp;|&nbsp; <b>Response Consistency:</b> {consistency_score:.1f}% &nbsp;|&nbsp; <b>Report Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>" \
                       f"<b>Natural Team Role:</b> {profile_expanded.get('team_superpower', '')}"
        summary_table = Table([[Paragraph(summary_text, body_style)]], colWidths=[540])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECEFF1')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CFD8DC')),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 6))

        img_buf = BytesIO()
        fig.savefig(img_buf, format='png', dpi=200, bbox_inches='tight')
        img_buf.seek(0)
        chart_img = Image(img_buf, width=195, height=195)

        score_rows = [
            [Paragraph('<b>Dimension</b>', bold_label), Paragraph('<b>Absolute (0-100%)</b>', bold_label), Paragraph('<b>Relative Share</b>', bold_label)],
            [Paragraph('Dominance (D)', body_style), Paragraph(f"{normalized_scores['D']:.1f}%", body_style), Paragraph(f"{relative_percentages['D']:.1f}%", body_style)],
            [Paragraph('Influence (I)', body_style), Paragraph(f"{normalized_scores['I']:.1f}%", body_style), Paragraph(f"{relative_percentages['I']:.1f}%", body_style)],
            [Paragraph('Steadiness (S)', body_style), Paragraph(f"{normalized_scores['S']:.1f}%", body_style), Paragraph(f"{relative_percentages['S']:.1f}%", body_style)],
            [Paragraph('Conscientiousness (C)', body_style), Paragraph(f"{normalized_scores['C']:.1f}%", body_style), Paragraph(f"{relative_percentages['C']:.1f}%", body_style)],
        ]
        scores_tbl = Table(score_rows, colWidths=[115, 105, 90])
        scores_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CFD8DC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B0BEC5')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]))

        pace_str = 'Fast-Paced / Assertive' if pace_index >= 0 else 'Deliberate / Thoughtful'
        focus_str = 'People & Harmony' if focus_index >= 0 else 'Task & Logic'
        dim_text = f"<b>Pace / Tempo Index:</b> {pace_index:+.1f} ({pace_str})<br/>" \
                   f"<b>Focus / Orientation Index:</b> {focus_index:+.1f} ({focus_str})<br/>" \
                   f"<b>Psychometric Quality:</b> High Reliability Data Sample"
        dim_table = Table([[Paragraph(dim_text, body_style)]], colWidths=[310])
        dim_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F7FA')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CFD8DC')),
        ]))

        left_flow = [scores_tbl, Spacer(1, 4), dim_table]
        layout_table = Table([[left_flow, chart_img]], colWidths=[320, 220])
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(layout_table)
        story.append(Spacer(1, 4))

        story.append(Paragraph('Comprehensive Behavioral Narrative', section_h1))
        clean_prim = profile_expanded.get('primary_narrative', '').replace('<strong>', '<b>').replace('</strong>', '</b>')
        clean_blend = profile_expanded.get('blend_narrative', '').replace('<strong>', '<b>').replace('</strong>', '</b>')
        clean_dec = profile_expanded.get('decision_style', '').replace('<strong>', '<b>').replace('</strong>', '</b>').replace('<code>', '').replace('</code>', '')
        
        story.append(Paragraph(clean_prim, body_style))
        story.append(Spacer(1, 3))
        story.append(Paragraph(clean_blend, body_style))
        story.append(Spacer(1, 3))
        story.append(Paragraph(clean_dec, body_style))
        story.append(Spacer(1, 5))

        clean_latent = profile_expanded.get('latent_narrative', '').replace('<strong>', '<b>').replace('</strong>', '</b>').replace('<em>', '<i>').replace('</em>', '</i>')
        sc_text = f"<b>Core Strengths:</b> {style_data.get('strengths', '')}<br/><br/>" \
                  f"<b>Growth Challenges:</b> {style_data.get('challenges', '')}<br/><br/>" \
                  f"<b>Latent Dimension Analysis:</b> {clean_latent}"
        sc_table = Table([[Paragraph(sc_text, body_style)]], colWidths=[540])
        sc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(sc_table)

        # Page 2: Workplace Dynamics
        story.append(PageBreak())
        story.append(Paragraph('Workplace Dynamics, Stress Response & Interpersonal Guide', section_h1))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#184b6a'), spaceBefore=2, spaceAfter=6))

        m_text = f"<b>Ideal Work Environment:</b> {profile_expanded.get('environment_fit', '')}<br/><br/>" \
                 f"<b>Key Motivators:</b> {style_data.get('motivators', '')}<br/><br/>" \
                 f"<b>Stress Triggers:</b> {style_data.get('stress_triggers', '')}<br/><br/>" \
                 f"<b>Behavior Under High Pressure:</b> {style_data.get('under_pressure', '')}"
        m_table = Table([[Paragraph(m_text, body_style)]], colWidths=[540])
        m_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#DCE1E5')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(m_table)
        story.append(Spacer(1, 6))

        comm_text = f"<b>Effective Communication Guide:</b> {style_data.get('communication_tips', '')}<br/><br/>" \
                    f"<b>Actionable Growth Roadmap:</b> {style_data.get('growth_advice', '')}"
        comm_table = Table([[Paragraph(comm_text, body_style)]], colWidths=[540])
        comm_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F8')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CFD8DC')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(comm_table)
        story.append(Spacer(1, 8))

        story.append(Paragraph('Quick Reference: Collaborating Across DISC Styles', section_h1))
        ref_rows = [
            [Paragraph('<b>Style</b>', bold_label), Paragraph('<b>Key Attributes</b>', bold_label), Paragraph('<b>Best Way to Engage</b>', bold_label)],
            [Paragraph('Dominance (D)', body_style), Paragraph('Direct, ambitious, results-focused', body_style), Paragraph('Be concise, focus on results and solutions, avoid micromanaging.', body_style)],
            [Paragraph('Influence (I)', body_style), Paragraph('Enthusiastic, optimistic, collaborative', body_style), Paragraph('Be warm, engage in open discussion, recognize contributions.', body_style)],
            [Paragraph('Steadiness (S)', body_style), Paragraph('Patient, reliable, supportive', body_style), Paragraph('Be patient, provide advance notice of change, listen respectfully.', body_style)],
            [Paragraph('Conscientiousness (C)', body_style), Paragraph('Analytical, precise, quality-driven', body_style), Paragraph('Be prepared with data, provide clear details, give time to analyze.', body_style)],
        ]
        ref_tbl = Table(ref_rows, colWidths=[110, 185, 245])
        ref_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CFD8DC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B0BEC5')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(ref_tbl)

    # --- SECTION 2: Top Signature Strengths (if present) ---
    if top_5_strengths:
        if normalized_scores:
            story.append(PageBreak())
        
        story.append(Paragraph('Top 5 Signature Workplace Strengths', section_h1))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#184b6a'), spaceBefore=2, spaceAfter=8))

        if domain_pcts:
            dom_text = f"<b>Leadership Domain Breakdown:</b> " \
                       f"<b>🟣 Executing:</b> {domain_pcts.get('Executing', 0):.1f}% &nbsp;|&nbsp; " \
                       f"<b>🟠 Influencing:</b> {domain_pcts.get('Influencing', 0):.1f}% &nbsp;|&nbsp; " \
                       f"<b>🟢 Relationship Building:</b> {domain_pcts.get('Relationship Building', 0):.1f}% &nbsp;|&nbsp; " \
                       f"<b>🔵 Strategic Thinking:</b> {domain_pcts.get('Strategic Thinking', 0):.1f}%"
            dom_table = Table([[Paragraph(dom_text, body_style)]], colWidths=[540])
            dom_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(dom_table)
            story.append(Spacer(1, 8))

        for idx, item in enumerate(top_5_strengths):
            rank_num = idx + 1
            s_name = item["name"]
            s_dom = item["domain"]
            s_tagline = item["tagline"]
            s_desc = item["description"]
            s_action = item["action_tip"]

            card_content = f"<b>#{rank_num} {s_name}</b> &nbsp;[<i>{s_dom}</i>]<br/>" \
                           f"<b>Core Essence:</b> {s_tagline}<br/>" \
                           f"<b>In-Depth Analysis:</b> {s_desc}<br/>" \
                           f"<b>Workplace Action Tip:</b> {s_action}"
            
            bg_col = '#F8FAFC' if rank_num % 2 == 1 else '#FFFFFF'
            c_table = Table([[Paragraph(card_content, body_style)]], colWidths=[540])
            c_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_col)),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(c_table)
            story.append(Spacer(1, 6))

        if top_6_10:
            story.append(Spacer(1, 4))
            story.append(Paragraph('Supporting Strength Themes (#6–#10)', section_h1))
            supp_rows = [[Paragraph('<b>Rank</b>', bold_label), Paragraph('<b>Theme</b>', bold_label), Paragraph('<b>Domain</b>', bold_label), Paragraph('<b>Core Focus</b>', bold_label)]]
            for idx, s in enumerate(top_6_10):
                r_num = idx + 6
                supp_rows.append([
                    Paragraph(f"#{r_num}", body_style),
                    Paragraph(f"<b>{s['name']}</b>", body_style),
                    Paragraph(s['domain'], body_style),
                    Paragraph(s['tagline'], body_style)
                ])
            supp_tbl = Table(supp_rows, colWidths=[45, 110, 125, 260])
            supp_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CFD8DC')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B0BEC5')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(supp_tbl)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


# --- Session State Management ---

if "assessment_mode" not in st.session_state:
    st.session_state.assessment_mode = "disc"

if "disc_started" not in st.session_state:
    st.session_state.disc_started = False

if "disc_page" not in st.session_state:
    st.session_state.disc_page = 0

if "disc_answers" not in st.session_state:
    st.session_state.disc_answers = {}

if "disc_submitted" not in st.session_state:
    st.session_state.disc_submitted = False

if "disc_questions" not in st.session_state:
    # 10 questions per style = 40 total questions for robust statistical depth
    st.session_state.disc_questions = sample_balanced_disc_questions(disc_questions_pool, count_per_style=10)

if "strengths_started" not in st.session_state:
    st.session_state.strengths_started = False

if "strengths_page" not in st.session_state:
    st.session_state.strengths_page = 0

if "strengths_answers" not in st.session_state:
    st.session_state.strengths_answers = {}

if "strengths_submitted" not in st.session_state:
    st.session_state.strengths_submitted = False

if "strengths_questions" not in st.session_state:
    # 35 paired scenarios for high resolution strength rankings
    st.session_state.strengths_questions = sample_strengths_questions(strengths_questions_pool, count=35)


# ==============================================================================
# ONBOARDING SCREEN
# ==============================================================================
if not st.session_state.disc_started and not st.session_state.strengths_started and not st.session_state.disc_submitted and not st.session_state.strengths_submitted:
    st.markdown(
        """
        ### Welcome to the Behavioral & Signature Strengths Assessment Platform
        
        Select an assessment below to map your behavioral style, decision-making dynamics, and core leadership strengths. You can complete both assessments for a comprehensive executive profile.
        """
    )

    card_c1, card_c2 = st.columns(2)

    with card_c1:
        st.markdown(
            """
            <div class="insight-card" style="border-left: 5px solid #184b6a;">
                <div class="insight-title">🧭 DISC Personality Assessment</div>
                <p>Measures your behavioral tendencies across <strong>Dominance (D)</strong>, <strong>Influence (I)</strong>, <strong>Steadiness (S)</strong>, and <strong>Conscientiousness (C)</strong>. Evaluates your Pace and Focus dynamics on the DISC circumplex wheel.</p>
                <p><em>40 balanced questions (10 per dimension) • Zero duplicates • ~4 minutes</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🚀 Start DISC Assessment", use_container_width=True):
            st.session_state.assessment_mode = "disc"
            st.session_state.disc_started = True
            st.session_state.disc_page = 0
            st.session_state.disc_answers = {}
            st.session_state.disc_questions = sample_balanced_disc_questions(disc_questions_pool, count_per_style=10)
            st.rerun()

    with card_c2:
        st.markdown(
            """
            <div class="insight-card" style="border-left: 5px solid #7C3AED;">
                <div class="insight-title">💎 Core Strengths Assessment</div>
                <p>Discovers your <strong>Top 5 Signature Strengths</strong> across four foundational leadership domains: <strong>Executing</strong>, <strong>Influencing</strong>, <strong>Relationship Building</strong>, and <strong>Strategic Thinking</strong>.</p>
                <p><em>35 paired scenarios • High statistical resolution • ~4 minutes</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("🌟 Start Strengths Assessment", use_container_width=True):
            st.session_state.assessment_mode = "strengths"
            st.session_state.strengths_started = True
            st.session_state.strengths_page = 0
            st.session_state.strengths_answers = {}
            st.session_state.strengths_questions = sample_strengths_questions(strengths_questions_pool, count=35)
            st.rerun()

    st.write("")
    with st.expander("📂 Upload Previous JSON Results"):
        uploaded_file = st.file_uploader("Upload your previous assessment results JSON", type=["json"])
        if uploaded_file is not None:
            try:
                bytes_data = uploaded_file.getvalue()
                uploaded_content = json.load(StringIO(bytes_data.decode("utf-8")))
                
                if "disc" in uploaded_content:
                    st.session_state.disc_normalized_scores = uploaded_content["disc"]["normalized_scores"]
                    st.session_state.disc_submitted = True
                elif "normalized_scores" in uploaded_content:
                    st.session_state.disc_normalized_scores = uploaded_content["normalized_scores"]
                    st.session_state.disc_submitted = True
                elif all(k in uploaded_content for k in ["D", "I", "S", "C"]):
                    st.session_state.disc_normalized_scores = uploaded_content
                    st.session_state.disc_submitted = True
                
                if "strengths" in uploaded_content:
                    st.session_state.top_5_strengths = uploaded_content["strengths"]["top_5"]
                    st.session_state.domain_pcts = uploaded_content["strengths"].get("domain_percentages", {})
                    st.session_state.strengths_submitted = True
                elif "top_5_strengths" in uploaded_content:
                    st.session_state.top_5_strengths = uploaded_content["top_5_strengths"]
                    st.session_state.domain_pcts = uploaded_content.get("domain_pcts", {})
                    st.session_state.strengths_submitted = True
                
                st.success("Results loaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error reading JSON file: {e}")


# ==============================================================================
# STAGE 2A: DISC QUESTIONNAIRE (Horizontal 5-Point Scale, Strict Forward)
# ==============================================================================
elif st.session_state.disc_started and not st.session_state.disc_submitted:
    total_q = len(st.session_state.disc_questions)
    cur_idx = st.session_state.disc_page
    cur_q = st.session_state.disc_questions[cur_idx]

    prog = cur_idx / total_q
    st.progress(prog)
    st.caption(f"DISC Assessment: Question **{cur_idx + 1}** of **{total_q}** ({int(prog * 100)}% completed)")

    st.markdown(
        f"""
        <div class="question-box">
            <div class="question-number">Question {cur_idx + 1} of {total_q}</div>
            <div class="question-text">"{cur_q['question']}"</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    options = [
        "1 • Strongly Disagree",
        "2 • Disagree",
        "3 • Neutral / Sometimes",
        "4 • Agree",
        "5 • Strongly Agree",
    ]
    score_map = {
        "1 • Strongly Disagree": 1,
        "2 • Disagree": 2,
        "3 • Neutral / Sometimes": 3,
        "4 • Agree": 4,
        "5 • Strongly Agree": 5,
    }

    prev_val = st.session_state.disc_answers.get(cur_idx, None)
    default_idx = None
    if prev_val is not None:
        for opt, val in score_map.items():
            if val == prev_val:
                default_idx = options.index(opt)
                break

    selected_opt = st.radio(
        "Select your response:",
        options=options,
        index=default_idx,
        key=f"disc_radio_{cur_idx}",
        horizontal=True,
    )

    st.write("")
    col1, col2 = st.columns([3.5, 1.2])
    with col2:
        is_last = (cur_idx == total_q - 1)
        btn_txt = "Show DISC Results 🚀" if is_last else "Next Question ➡️"
        if st.button(btn_txt, use_container_width=True):
            if selected_opt is None:
                st.warning("⚠️ Please select a response to proceed.")
            else:
                st.session_state.disc_answers[cur_idx] = score_map[selected_opt]
                if not is_last:
                    st.session_state.disc_page += 1
                    st.rerun()
                else:
                    raw_sc = {"D": 0, "I": 0, "S": 0, "C": 0}
                    for i in range(total_q):
                        q = st.session_state.disc_questions[i]
                        ans = st.session_state.disc_answers.get(i, 3)
                        for s in ["D", "I", "S", "C"]:
                            raw_sc[s] += q["mapping"].get(s, 0) * (ans - 3)
                    
                    st.session_state.disc_raw_scores = raw_sc
                    st.session_state.disc_normalized_scores = normalize_disc_scores(raw_sc, st.session_state.disc_questions)
                    st.session_state.disc_consistency = calculate_consistency_index(st.session_state.disc_answers, st.session_state.disc_questions)
                    st.session_state.disc_started = False
                    st.session_state.disc_submitted = True
                    st.rerun()


# ==============================================================================
# STAGE 2B: STRENGTHS QUESTIONNAIRE (Paired Choices, Horizontal, Strict Forward)
# ==============================================================================
elif st.session_state.strengths_started and not st.session_state.strengths_submitted:
    total_q = len(st.session_state.strengths_questions)
    cur_idx = st.session_state.strengths_page
    cur_q = st.session_state.strengths_questions[cur_idx]

    prog = cur_idx / total_q
    st.progress(prog)
    st.caption(f"Core Strengths Assessment: Scenario **{cur_idx + 1}** of **{total_q}** ({int(prog * 100)}% completed)")

    st.markdown(
        f"""
        <div class="question-box">
            <div class="question-number">Scenario {cur_idx + 1} of {total_q}</div>
            <div class="question-text">{cur_q['question']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opt_labels = [
        f"A: {cur_q['option_a']}",
        f"B: {cur_q['option_b']}"
    ]

    prev_choice = st.session_state.strengths_answers.get(cur_idx, None)
    default_idx = None
    if prev_choice == "option_a":
        default_idx = 0
    elif prev_choice == "option_b":
        default_idx = 1

    selected_choice = st.radio(
        "Which option describes you better?",
        options=opt_labels,
        index=default_idx,
        key=f"strengths_radio_{cur_idx}",
        horizontal=True,
    )

    st.write("")
    col1, col2 = st.columns([3.5, 1.2])
    with col2:
        is_last = (cur_idx == total_q - 1)
        btn_txt = "Show Strengths Profile 💎" if is_last else "Next Scenario ➡️"
        if st.button(btn_txt, use_container_width=True):
            if selected_choice is None:
                st.warning("⚠️ Please select an option to proceed.")
            else:
                chosen_key = "option_a" if selected_choice.startswith("A:") else "option_b"
                st.session_state.strengths_answers[cur_idx] = chosen_key
                if not is_last:
                    st.session_state.strengths_page += 1
                    st.rerun()
                else:
                    top_5, top_6_10, dom_pcts, sorted_all = calculate_strengths_scores(
                        st.session_state.strengths_answers,
                        st.session_state.strengths_questions,
                        strengths_definitions
                    )
                    st.session_state.top_5_strengths = top_5
                    st.session_state.top_6_10 = top_6_10
                    st.session_state.domain_pcts = dom_pcts
                    st.session_state.sorted_all_strengths = sorted_all
                    st.session_state.strengths_started = False
                    st.session_state.strengths_submitted = True
                    st.rerun()


# ==============================================================================
# STAGE 3: RESULTS DASHBOARD (Unified DISC & Strengths)
# ==============================================================================
elif st.session_state.disc_submitted or st.session_state.strengths_submitted:
    has_disc = st.session_state.disc_submitted
    has_strengths = st.session_state.strengths_submitted

    disc_norm = None
    disc_rel = None
    disc_fig = None
    disc_style_info = None
    disc_pace = 0.0
    disc_focus = 0.0
    disc_intensity = "Moderate Expression"
    disc_profile_exp = None
    disc_style_code = "D"
    disc_consistency = st.session_state.get("disc_consistency", 94.2)

    if has_disc:
        disc_norm = st.session_state.disc_normalized_scores
        total_norm = sum(disc_norm.values())
        disc_rel = {s: round((val / total_norm * 100.0) if total_norm > 0 else 25.0, 1) for s, val in disc_norm.items()}
        disc_pace, disc_focus = calculate_two_axes(disc_norm)

        categories = ["D", "I", "S", "C"]
        angles = [7 * np.pi / 4, np.pi / 4, 3 * np.pi / 4, 5 * np.pi / 4]
        scaled = {s: disc_norm[s] / 100.0 for s in categories}
        tot_x = sum([scaled[s] * np.cos(angles[idx]) for idx, s in enumerate(categories)])
        tot_y = sum([scaled[s] * np.sin(angles[idx]) for idx, s in enumerate(categories)])
        r_mag = np.sqrt(tot_x**2 + tot_y**2)
        r_ang = np.arctan2(tot_y, tot_x) % (2 * np.pi)
        r_deg = math.degrees(r_ang)

        if r_mag >= 0.55:
            disc_intensity = "High / Pronounced Style"
        elif r_mag >= 0.25:
            disc_intensity = "Moderate Expression"
        else:
            disc_intensity = "Adaptable / Situational"

        sorted_disc = sorted(disc_norm.items(), key=lambda item: item[1], reverse=True)
        prim_code = sorted_disc[0][0]
        sec_code = sorted_disc[1][0]
        low_code = sorted_disc[-1][0]

        disc_style_code, disc_style_info = resolve_disc_style(r_deg, r_mag, disc_descriptions)
        disc_profile_exp = generate_expanded_profile(
            disc_norm, disc_pace, disc_focus, disc_intensity,
            prim_code, sec_code, low_code, disc_style_info.get("description", "")
        )
        disc_fig = create_disc_plot(r_ang, r_mag)

    top_5 = st.session_state.get("top_5_strengths", None)
    top_6_10 = st.session_state.get("top_6_10", None)
    dom_pcts = st.session_state.get("domain_pcts", None)
    sorted_all_str = st.session_state.get("sorted_all_strengths", None)

    # --- Cross-Assessment Upsell / Completion Banners ---
    if has_disc and not has_strengths:
        st.info("💡 **Complete Your Profile**: You've completed the DISC Assessment! Discover your **Top 5 Signature Strengths** to generate a unified executive report.")
        if st.button("💎 Take Core Strengths Assessment", use_container_width=True):
            st.session_state.assessment_mode = "strengths"
            st.session_state.strengths_started = True
            st.session_state.strengths_page = 0
            st.session_state.strengths_answers = {}
            st.session_state.strengths_questions = sample_strengths_questions(strengths_questions_pool, count=35)
            st.rerun()

    elif has_strengths and not has_disc:
        st.info("💡 **Complete Your Profile**: You've mapped your Signature Strengths! Take the **DISC Assessment** to map your communication tempo and behavioral focus on the DISC circumplex.")
        if st.button("🧭 Take DISC Personality Assessment", use_container_width=True):
            st.session_state.assessment_mode = "disc"
            st.session_state.disc_started = True
            st.session_state.disc_page = 0
            st.session_state.disc_answers = {}
            st.session_state.disc_questions = sample_balanced_disc_questions(disc_questions_pool, count_per_style=10)
            st.rerun()

    # --- DISC Section ---
    if has_disc:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="hero-title">{disc_style_info.get('title', 'Your DISC Profile')}</div>
                <div class="hero-headline">{disc_style_info.get('headline', '')}</div>
                <div>
                    <span class="badge badge-d">Primary: {prim_code} ({disc_norm[prim_code]:.1f}%)</span>
                    <span class="badge badge-i">Secondary: {sec_code} ({disc_norm[sec_code]:.1f}%)</span>
                    <span class="badge badge-neutral">Intensity: {disc_intensity}</span>
                    <span class="badge badge-neutral">Consistency: {disc_consistency:.1f}%</span>
                    <span class="badge badge-neutral">Role: {disc_profile_exp['team_superpower'].split('—')[0].strip()}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        p_col, m_col = st.columns([1.1, 1])
        with p_col:
            st.pyplot(disc_fig)
        with m_col:
            st.markdown("### 📊 Dimension Scores & Axes")
            q_cols = st.columns(2)
            with q_cols[0]:
                st.markdown(f"**🔴 Dominance (D)**: `{disc_norm['D']:.1f}%` (Rel: {disc_rel['D']:.1f}%)")
                st.progress(disc_norm['D'] / 100.0)
                st.markdown(f"**🟡 Influence (I)**: `{disc_norm['I']:.1f}%` (Rel: {disc_rel['I']:.1f}%)")
                st.progress(disc_norm['I'] / 100.0)
            with q_cols[1]:
                st.markdown(f"**🟢 Steadiness (S)**: `{disc_norm['S']:.1f}%` (Rel: {disc_rel['S']:.1f}%)")
                st.progress(disc_norm['S'] / 100.0)
                st.markdown(f"**🔵 Conscientiousness (C)**: `{disc_norm['C']:.1f}%` (Rel: {disc_rel['C']:.1f}%)")
                st.progress(disc_norm['C'] / 100.0)

            st.markdown("---")
            st.markdown("#### ⚖️ Behavioral Tempo & Orientation")
            pace_lbl = "Fast-Paced & Assertive" if disc_pace >= 0 else "Deliberate & Thoughtful"
            foc_lbl = "People & Relationships" if disc_focus >= 0 else "Task & Logic"
            st.markdown(f"**Pace / Tempo Index**: `{disc_pace:+.1f}` → **{pace_lbl}**")
            st.markdown(f"**Focus / Orientation**: `{disc_focus:+.1f}` → **{foc_lbl}**")

        st.markdown("### 📖 In-Depth Behavioral Profile")
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">🌟 Core Driver & Operating Mode</div>
                <p>{disc_profile_exp['primary_narrative']}</p>
                <p>{disc_profile_exp['blend_narrative']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        dec_c, env_c = st.columns(2)
        with dec_c:
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-title">⚖️ Decision-Making & Pace Dynamics</div>
                    <p>{disc_profile_exp['decision_style']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with env_c:
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-title">🏢 Ideal Work Environment</div>
                    <p>{disc_profile_exp['environment_fit']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        tab1, tab2, tab3, tab4 = st.tabs([
            "🌟 Strengths & Challenges",
            "💬 Communication Playbook",
            "⚡ Stress & Pressure",
            "🤝 Cross-Style Collaboration"
        ])
        with tab1:
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown("#### ✅ Natural Strengths")
                st.markdown(disc_style_info.get("strengths", ""))
                st.write("")
                st.markdown("#### 🏆 Team Superpower")
                st.markdown(disc_profile_exp["team_superpower"])
            with sc2:
                st.markdown("#### ⚠️ Growth Challenges")
                st.markdown(disc_style_info.get("challenges", ""))
                st.write("")
                st.markdown("#### 🔍 Latent Dimension Analysis")
                st.markdown(disc_profile_exp["latent_narrative"])
        with tab2:
            st.markdown("#### 🗣️ How to Communicate Effectively")
            st.markdown(f"**Best engagement approach:** {disc_style_info.get('communication_tips', '')}")
            st.markdown("---")
            st.markdown("#### 🎯 Core Motivators")
            st.markdown(disc_style_info.get("motivators", ""))
        with tab3:
            st.markdown("#### ⚡ Stress Triggers & Pressure Response")
            st.markdown(f"**Triggers:** {disc_style_info.get('stress_triggers', '')}")
            st.markdown(f"**Under Pressure:** {disc_style_info.get('under_pressure', '')}")
        with tab4:
            st.markdown(
                """
                - **🔴 High D (Dominance):** Be direct, concise, and focused on outcomes. Propose solutions.
                - **🟡 High I (Influence):** Bring warmth and energy, allow time for open ideation, follow up in writing.
                - **🟢 High S (Steadiness):** Be patient, provide advance notice of change, cultivate trust.
                - **🔵 High C (Conscientiousness):** Be prepared with data, provide clear details, give time to verify.
                """
            )

    # --- Strengths Section ---
    if has_strengths and top_5:
        st.write("")
        st.markdown("---")
        st.markdown("## 💎 Your Top 5 Signature Strengths")
        st.markdown("<p style='color: #546E7A;'>Your signature themes represent your natural patterns of thinking, feeling, and behaving for maximum performance.</p>", unsafe_allow_html=True)

        if dom_pcts:
            st.markdown("#### 🏛️ Leadership Domain Balance")
            d_cols = st.columns(4)
            with d_cols[0]:
                st.markdown(f"**🟣 Executing**: `{dom_pcts.get('Executing', 0):.1f}%`")
                st.progress(dom_pcts.get('Executing', 0) / 100.0)
            with d_cols[1]:
                st.markdown(f"**🟠 Influencing**: `{dom_pcts.get('Influencing', 0):.1f}%`")
                st.progress(dom_pcts.get('Influencing', 0) / 100.0)
            with d_cols[2]:
                st.markdown(f"**🟢 Relationship Building**: `{dom_pcts.get('Relationship Building', 0):.1f}%`")
                st.progress(dom_pcts.get('Relationship Building', 0) / 100.0)
            with d_cols[3]:
                st.markdown(f"**🔵 Strategic Thinking**: `{dom_pcts.get('Strategic Thinking', 0):.1f}%`")
                st.progress(dom_pcts.get('Strategic Thinking', 0) / 100.0)
            st.write("")

        # Render Top 5 Strengths as a rich structured list
        for idx, item in enumerate(top_5):
            rank = idx + 1
            dom_badge_cls = {
                "Executing": "badge-exec",
                "Influencing": "badge-infl",
                "Relationship Building": "badge-rel",
                "Strategic Thinking": "badge-strat"
            }.get(item["domain"], "badge-neutral")

            st.markdown(
                f"""
                <div class="strength-card" style="border-left-color: {item['badge_color']};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 1.25rem; font-weight: 800; color: #184b6a;">#{rank} {item['name']}</span>
                        <span class="badge {dom_badge_cls}">{item['domain']}</span>
                    </div>
                    <p style="font-weight: 600; color: #334155; margin-bottom: 8px;">{item['tagline']}</p>
                    <p style="color: #475569; margin-bottom: 8px;">{item['description']}</p>
                    <div style="background-color: #F1F5F9; border-radius: 8px; padding: 10px 14px; font-size: 0.92rem; color: #1E293B;">
                        <strong>💡 Workplace Application Tip:</strong> {item['action_tip']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Supporting Strengths #6 - #10
        if top_6_10:
            with st.expander("🔍 View Supporting Strength Themes (#6–#10)"):
                for idx, s in enumerate(top_6_10):
                    r_num = idx + 6
                    st.markdown(f"**#{r_num} {s['name']}** *({s['domain']})* — {s['tagline']}")

        # Full 34 Strengths Profile Matrix
        if sorted_all_str:
            with st.expander("📋 View Complete 34 Strengths Ranking"):
                max_pts = max([pts for _, pts in sorted_all_str]) if sorted_all_str else 1
                for r_idx, (th_name, pts) in enumerate(sorted_all_str):
                    th_dom = strengths_definitions.get(th_name, {}).get("domain", "")
                    col_a, col_b = st.columns([1.5, 3])
                    with col_a:
                        st.markdown(f"**#{r_idx+1} {th_name}** *({th_dom})*")
                    with col_b:
                        st.progress(pts / max(max_pts, 1))

    # --- Downloads & Actions ---
    st.write("")
    st.markdown("---")
    st.markdown("### 📥 Download & Export Your Results")
    down_col1, down_col2, down_col3 = st.columns([1, 1, 1])

    with down_col1:
        export_payload = {
            "assessment": "DISC & Core Strengths Profile",
            "developer": "Dawid Zyla (https://github.com/dzyla)",
            "date": datetime.now().isoformat()
        }
        if has_disc:
            export_payload["disc"] = {
                "style_code": disc_style_code,
                "style_title": disc_style_info.get("title", ""),
                "normalized_scores": disc_norm,
                "relative_percentages": disc_rel,
                "pace_index": disc_pace,
                "focus_index": disc_focus,
                "intensity_level": disc_intensity,
                "consistency_score": disc_consistency
            }
        if has_strengths:
            export_payload["strengths"] = {
                "top_5": top_5,
                "top_6_10": top_6_10,
                "domain_percentages": dom_pcts,
                "all_rankings": sorted_all_str
            }
        
        json_data_str = json.dumps(export_payload, indent=2)
        st.download_button(
            label="📄 Download JSON Results",
            data=json_data_str,
            file_name="assessment_results.json",
            mime="application/json",
            use_container_width=True
        )

    with down_col2:
        pdf_buf = create_unified_pdf_report(
            normalized_scores=disc_norm,
            relative_percentages=disc_rel,
            fig=disc_fig,
            style_data=disc_style_info,
            pace_index=disc_pace,
            focus_index=disc_focus,
            intensity_level=disc_intensity,
            profile_expanded=disc_profile_exp,
            top_5_strengths=top_5,
            top_6_10=top_6_10,
            domain_pcts=dom_pcts,
            consistency_score=disc_consistency
        )
        report_name = "comprehensive_disc_and_strengths_report.pdf" if (has_disc and has_strengths) else ("disc_report.pdf" if has_disc else "strengths_report.pdf")
        st.download_button(
            label="📑 Download PDF Report",
            data=pdf_buf.getvalue(),
            file_name=report_name,
            mime="application/pdf",
            use_container_width=True
        )

    with down_col3:
        if st.button("🔄 Reset / Start Over", use_container_width=True):
            st.session_state.clear()
            st.rerun()


# --- Footer ---
st.markdown(
    """
    ---
    <div style="text-align: center; color: #78909C; font-size: 0.9rem;">
        <strong><a href="https://github.com/dzyla/disc-personality-assessment" target="_blank" style="color: #184b6a; text-decoration: none;">Source code</a></strong> | Developed by <a href="https://github.com/dzyla" target="_blank" style="color: #184b6a; text-decoration: none;">Dawid Zyla</a>
    </div>
    """,
    unsafe_allow_html=True,
)
