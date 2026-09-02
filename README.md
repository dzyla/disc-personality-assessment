# Work style, measured

A Streamlit assessment that maps how you work — DISC behavioural style, signature
strengths, pressure response and motivators — and reports every number with its
uncertainty, including when two results are too close to tell apart.

```bash
pip install -r requirements.txt
streamlit run disc_style.py
```

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

Questions come one per screen and advance only on a deliberate click. There is no
back button.

Completing more than one module unlocks comparisons a single lens cannot make:
where your strengths pull against your behavioural default, whether you become
more or less yourself under load, and whether the role is paying you in the
currency you actually chose.

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
- **Evidence for every claim.** Each statement in the report expands to show the
  items and answers that produced it.

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
data/             item pools and descriptions
tests/            pytest — scoring, reliability, sampling, headless app runs
```

```bash
pytest
```

Built by [Dawid Zyla](https://github.com/dzyla) ·
[source](https://github.com/dzyla/disc-personality-assessment)
