# DISC & Strengths Assessment — Expansion Design

Date: 2026-09-01

## Goal

Expand the Streamlit assessment into a modular self-knowledge tool whose numbers
are defensible. Three approved directions: trustworthy measurement, more lenses
on work style, and results that are actionable and evidence-backed.

Constraints agreed with the user:

- Streamlit stays. Vertical, one item per screen, explicit click to advance.
- **Strictly forward.** No back button.
- Modular: a core path plus opt-in add-on modules.
- No server. Portable JSON export/import is the only persistence.
- Honest tone: name costs and blind spots; every claim traceable to answers.

## Problems in the current app (audited, not assumed)

1. `calculate_consistency_index` is `82 + variance*8.5` clamped to 75-99. It
   cannot report inconsistency; it rewards use of the scale ends. Displayed as
   a hard percentage in the hero card and PDF.
2. `strengths_questions.json` exposure ranges 1-41 across the 34 themes
   (`Discipline` 41, `Connectedness` 9). Top-5 is substantially an artifact of
   which items were drawn.
3. Three tags in the strengths pool resolve to no theme (`Adaptable`,
   `Problem-Solver`, `Relational`, items 59/74/111/185). `calculate_strengths_scores`
   silently drops them via `if tag in scores`.
4. 316 of 400 options carry 2-3 tags, so a single click awards 1-3 points.
5. All 240 DISC items have own-style weight +2. No reverse keying, so
   acquiescent responding is undetectable.
6. Single 1338-line module, no tests, per-session resampling makes retakes
   incomparable.

## Architecture

`disc_style.py` remains the entry point (a shim) so `streamlit run disc_style.py`
keeps working.

    app/          Streamlit shell: state, picker, runner, results, components, pdf
    assessment/   Pure, no Streamlit import: registry, items, scoring/, report/
    data/         Item pools and descriptions
    tests/        pytest

A lens is declared as a `Module` (id, kind, item_type, est_minutes, depends_on,
variants, build_items, score, render). The runner keeps one flat queue of
`(module_id, item_index)` and renders one item per screen. Today's six
interacting booleans collapse to a queue position plus a set of completed
module ids, which is what makes resume and later add-ons possible.

## Measurement

- **Reverse-keyed DISC items.** Every item gains `keyed: +1|-1`; ~24 new
  reverse-keyed items (6 per dimension). Scoring flips the response
  (`6 - r`) before applying the mapping.
- **Real consistency**, replacing the fabricated index:
  - *Acquiescence*: per dimension, `1 - |mean(fwd_raw) + mean(rev_raw) - 6| / 4`.
  - *Internal consistency*: Cronbach's alpha per dimension over own-style items.
  - *Straight-lining*: longest identical run, plus overall response SD.
  Reported as High/Moderate/Low with the numbers shown. It must be able to
  return a bad verdict.
- **Confidence bands.** Per-dimension standard error from item-level variance,
  scaled to the 0-100 range. Primary vs secondary is asserted only when the
  difference passes a two-sided test on `SE_diff = sqrt(SEa^2 + SEb^2)`.
  Retires `Consistency: 94.2%` and `Rel: 23.4%`.
- **Strengths.** Score = wins / exposures (win rate), so exposure is no longer a
  confound and multi-tag options stop inflating. Stratified selection targets
  equal exposure. Top-5 claimed only when #5 and #6 separate, else a cluster.
- **Deterministic retakes.** Seed and item ids stored in the export.

## Modules

Core: `disc_natural` (40 items, mixed keying), `strengths_core`
(35 standard / 60 deep, stratified forced choice).

Add-ons: `disc_adaptive` (same 40 stems under a work frame; strain index),
`stress_profile` (~20 items, four pressure modes), `motivators`
(~24 items, eight drivers).

Dropped on YAGNI grounds: a separate environment-fit module (derived section
instead) and a values module (overlaps motivators).

## Report

Per-module sections plus integration sections that unlock with 2+ modules:
DISC x Strengths (reinforcement and conflict), Strain x Stress, Motivators x
Adaptive. Honesty mechanics: "Why this?" evidence expanders citing item ids and
answers; shadow/overuse text per strength theme; blind-spot section from lowest
dimension and bottom themes; friction map written from the other side's point of
view; hedged prose generated when confidence is low; a closing three-experiment
Monday plan.

## Persistence

    {"schema_version": 2, "created", "seed",
     "modules": {"<id>": {"item_ids", "answers", "scores", "reliability"}},
     "history": [{"date", "modules": {summary scores}}]}

v1 exports are detected and migrated into `history`, flagged as lacking
item-level evidence. Resume restores the queue. Retake comparison reports drift
and states when a move is smaller than the confidence band.

## Tests

Data integrity (tags resolve, themes reachable, exposure balance, keying
present, no duplicate stems); DISC scoring (known vectors, all-5s and all-1s
must yield low confidence, reverse items flip); strengths scoring (win rate is
exposure-invariant); reliability (straight-lining, alpha on synthetic
responders); sampling determinism.

Sequencing: measurement fixes and their tests land before new content.
