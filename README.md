# Work style, measured

A Streamlit assessment that maps how you work — DISC behavioural style, working
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
| **Working strengths** | 72 or 132 | 24 strengths in three domains, ranked by win rate, each with its cost |
| **DISC — work style** | 40 | The same items answered for your job; the gap is your strain index |
| **Under pressure** | 20 | Four pressure modes: push, perform, accommodate, retreat |
| **What drives you** | 28 | Eight motivators in a complete round robin |

The core alone is 112 questions and about fifteen minutes; everything at once is 200.
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
- **Blind spots** — your lowest dimension and the strengths you consistently pass
  over, framed as what a team will feel the absence of.
- **The cost of each strength** — what your leading strengths look like to someone
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

- **One style per item.** Each DISC item counts toward its own style only. Scoring
  no longer builds in correlations between styles; any that remain come from how
  people answered, or from wording that hasn't yet been tested on real responses.
- **Reverse-keyed items.** Half of each style's items are worded the other way, so
  agreeing with everything is detectable rather than flattering.
- **A consistency check that can fail.** Forward/reverse agreement, split-half
  profile stability and straight-lining produce a High / Moderate / Low verdict,
  and a Low verdict hedges the whole report rather than adding a footnote.
- **Confidence bands.** Dimension scores carry a standard error, and the app only
  claims one dimension leads another when the gap survives a test against both
  errors.
- **Exactly balanced strengths.** Strengths are scored on how often they were chosen
  out of how often they were offered, and every strength is offered exactly as
  often as every other. Each option counts for one strength only.
- **Honest ties.** When the sixth strength cannot be separated from the ones below
  it, the report calls them a cluster. At these lengths that is the usual result.

This is a self-report tool for reflection, not a clinical or hiring tool. **It has
not been validated.** The items were largely AI-written, no response data has been
analysed, and it has not been compared with any other instrument. The figures in
the code's checks come from simulation, not from people. See
[docs/PROVENANCE.md](docs/PROVENANCE.md) for how it was made and what that means
for reuse.

## Your data

The app doesn't save your answers in any database. If you use a hosted copy, they
do pass through that host while the session runs, and the page loads web fonts from
Google. To avoid both, run it locally. The JSON export holds your answers, so you can
resume a partial run, add a module later, and compare a future take against this
one — with movements smaller than the measurement error reported as noise rather
than change. Exports from earlier question libraries still load, and their scores
are kept for reference, but those answers can't be rescored or compared directly.

## Layout

```
disc_style.py     entry point
app/              Streamlit shell: picker, runner, results, PDF, styling
assessment/       pure scoring and reporting, no Streamlit import
data/             item pools: 320 DISC, 276 strengths, 40 stress, 28 motivator
tests/            pytest — scoring, reliability, sampling, headless app runs
```

`assessment/` never imports Streamlit, so the scoring is testable on its own.

```bash
pytest            # 69 tests
```

Adding a lens means adding a data file, a scorer, and one entry in
`assessment/registry.py` — the picker, the questionnaire, the report and the
export all read from that table. The data-integrity tests will refuse a pool with
tags that resolve to nothing or strengths that can never be offered.

MIT licensed. Built by [Dawid Zyla](https://github.com/dzyla) ·
[source](https://github.com/dzyla/disc-personality-assessment)
