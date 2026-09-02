# Work style, measured

A Streamlit assessment that maps how you work — DISC behavioural style, signature
strengths, pressure response and motivators — and reports every number with its
uncertainty, including when two results are too close to tell apart.

```bash
pip install -r requirements.txt
streamlit run disc_style.py
```

Python 3.10 or newer. No account, no server, no database.

## What it does

You pick which lenses you want. Two are core, three are optional, and each states
its cost up front:

| Module | Items | What it gives you |
|---|---|---|
| **DISC — natural style** | 40 | Your behavioural profile off duty, with confidence bands |
| **Signature strengths** | 35 or 60 | 34 themes ranked by win rate, each with its cost |
| **DISC — work style** | 40 | The same items answered for your job; the gap is your strain index |
| **Under pressure** | 20 | Four pressure modes: push, perform, accommodate, retreat |
| **What drives you** | 28 | Eight motivators in a complete round robin |

The core alone is about 75 questions and ten minutes; everything at once is 163.
Questions come one per screen and advance only on a deliberate click. There is no
back button.

Completing more than one module unlocks comparisons a single lens cannot make:
where your strengths pull against your behavioural default, whether you become
more or less yourself under load, and whether the role is paying you in the
currency you actually chose.

## What you get back

A report on screen and as a PDF, containing:

- Your profile on the DISC circumplex, with the at-work position overlaid if you
  took that module.
- **Blind spots** — your lowest dimension and the themes you consistently pass
  over, framed as what a team will feel the absence of.
- **The cost of each strength** — what your leading themes look like to someone
  who does not share them, and the point at which each tips into a liability.
- **A friction map** — who finds you hardest to work with, written from their
  side rather than yours.
- **Three experiments** for the coming week, derived from your own results.
- An expandable trail of evidence behind every claim: the items you saw and the
  answers you gave.

It is written to be useful rather than flattering. If your answers do not support
a confident reading, the report says so and hedges accordingly instead of
asserting a profile anyway.

## Measurement

The point of this version is that the numbers mean something.

- **Reverse-keyed items.** Items are worded in both directions, so agreeing with
  everything is detectable rather than flattering.
- **A consistency check that can fail.** Forward/reverse agreement, split-half
  profile stability and straight-lining produce a High / Moderate / Low verdict,
  and a Low verdict hedges the whole report rather than adding a footnote.
- **Confidence bands.** Dimension scores carry a standard error, and the app only
  claims one dimension leads another when the gap survives a test against both
  errors.
- **Exposure-balanced strengths.** Themes are scored on how often they were chosen
  out of how often they were offered, and items are drawn so every theme is
  offered a comparable number of times. Rank no longer depends on how often the
  question pool happened to mention a theme.
- **Honest ties.** When the fifth and sixth themes cannot be separated, the report
  says they are a cluster rather than pretending the cut-off is meaningful.

This is a self-report instrument, not a clinical or hiring tool. It measures how
you describe yourself today, which is worth knowing and is not the same thing as
how you behave.

## Your data

Nothing is stored on a server. The JSON export holds your answers, so you can
resume a partial run, add a module later, and compare a future take against this
one — with movements smaller than the measurement error reported as noise rather
than change. Exports from the previous version still load and are kept for
comparison.

## Layout

```
disc_style.py     entry point
app/              Streamlit shell: picker, runner, results, PDF, styling
assessment/       pure scoring and reporting, no Streamlit import
data/             item pools: 264 DISC, 200 strengths, 40 stress, 28 motivator
tests/            pytest — scoring, reliability, sampling, headless app runs
```

`assessment/` never imports Streamlit, so the scoring is testable on its own.

```bash
pytest            # 53 tests
```

Adding a lens means adding a data file, a scorer, and one entry in
`assessment/registry.py` — the picker, the questionnaire, the report and the
export all read from that table. The data-integrity tests will refuse a pool with
tags that resolve to nothing or themes that can never be offered.

MIT licensed. Built by [Dawid Zyla](https://github.com/dzyla) ·
[source](https://github.com/dzyla/disc-personality-assessment)
