# Employee Engagement and Performance Analytics

A psychometric and regression analysis of a Great Place To Work–style
engagement survey: 5,000 respondents, 68 Likert items, 8 culture constructs,
and a business-unit profitability link.

---

## The question

1. Do the 68 survey items reliably measure 8 distinct culture constructs?
2. Which constructs are most strongly associated with overall employee
   satisfaction, once they are all considered together?
3. Do satisfaction and culture differ meaningfully across departments, tenure
   bands and sites — meaningfully, not just detectably?
4. Is unit-level culture related to unit-level Return on Sales?

## The data

| | |
|---|---|
| Source | **Synthetic** — generated, not collected |
| Raw rows | 5,012 (5,000 respondents + 12 duplicate submissions) |
| Analysed rows | 4,850 after cleaning (96.8% retained) |
| Items | 64 culture items (8 constructs × 8) + 4 satisfaction items |
| Scale | 1–5 Likert, 6 items reverse-worded |
| Demographics | department, tenure band, location, role level, business unit |
| Business units | 24, each with a Return on Sales figure |

The generator builds 8 correlated latent culture factors first, then produces
each item as a weak, noisy indicator of one factor. Reliability and factor
structure therefore have to be *discovered* by the analysis rather than being
written in by hand. It also injects the mess a real export contains:
straight-liners, missingness that rises with survey fatigue, out-of-range
codes, duplicate rows and untidy category labels.

## The method

| Phase | What it does | Output |
|---|---|---|
| 0 | Generate synthetic survey from a latent-factor model | `data/raw/` |
| 1 | Profile the raw file before touching it | `results/00_data_profile.md` |
| 2 | Clean: duplicates, out-of-range, straight-liners, reverse-coding, missingness | `results/01_cleaning_log.csv` |
| 3 | Cronbach's α, item-total correlations, α-if-deleted, EFA with oblimin rotation, construct scoring | `results/02_*.csv` |
| 4 | 24 one-way ANOVAs with Levene checks, Welch fallback, η², Tukey HSD, BH correction | `results/03_*.csv`, `03_anova_summary.md` |
| 5 | OLS driver model: VIF, standardised β, Breusch–Pagan, HC3 robust SEs, ΔR² | `results/04_*.csv`, `04_regression_summary.md` |
| 6 | ICC, unit-level aggregation, ROS correlations, influence check | `results/05_*.csv`, `05_ros_analysis.md` |
| 7 | 6 business charts, 3 Power BI exports, 23 pytest tests | `results/figures/`, `results/powerbi_*.csv` |

### The charts

Each chart has a plain title, one line underneath saying what it shows in
normal English, and a line of small print giving the definition and the sample
size, so any single one of them can go on a slide and still make sense on its
own.

Each chart answers one question a management team would actually ask, in the
order you would walk through them. The statistical evidence behind them lives in
`results/*.csv` and in `EXPLAINER.md`, not on the charts.

| # | Chart | The question it answers | What it shows |
|---|---|---|---|
| 01 | where we stand today | how are we doing? | only ~a third rate most topics favourably; respect weakest at 31% |
| 02 | what to fix first | where do we start? | leadership and fairness: biggest effect, weakest scores |
| 03 | where the problem sits | which sites? | Chennai −0.27 on wellbeing, −0.15 on leadership |
| 04 | what weak leadership costs | what is it costing us? | 73% at risk under weak leadership vs 4% under strong |
| 05 | which units need attention | who do we go to first? | at-risk rates 9%–37%; five units hold 342 at-risk people |
| 06 | does culture reach the P&L? | does it show up in money? | r = 0.45 across 24 units — a signal to test, not a proven link |

## The results

**Reliability — all eight scales hold together.** Cronbach's α ranges from
**0.850 (respect) to 0.893 (pride)**; the satisfaction outcome scale is 0.872.
One item was dropped (`devl_04`, item-total r = 0.291), raising development's α
from 0.869 to 0.888.

**But factor analysis qualifies that.** The eight constructs collapse onto
**seven** distinct factors — credibility and leadership are indistinguishable
(r = 0.76). The first eigenvalue is 23.85 against a second of 2.19, a dominant
halo factor. An eighth factor turns out to be a **method artefact** made
entirely of the six reverse-worded items.

**Drivers of satisfaction — R² = 0.474, adjusted R² = 0.471** (n = 4,846, HC3
robust standard errors):

| Rank | Construct | Std. β | Simple r | ΔR² if removed |
|---|---|---|---|---|
| 1 | leadership | 0.183 | 0.591 | 0.0112 |
| 2 | fairness | 0.172 | 0.585 | 0.0120 |
| 3 | pride | 0.145 | 0.572 | 0.0086 |
| 4 | credibility | 0.093 | 0.572 | 0.0030 |
| 5 | respect | 0.087 | 0.541 | 0.0033 |
| 6 | development | 0.059 | 0.535 | 0.0014 |
| 7 | wellbeing | 0.048 | 0.531 | 0.0009 |
| 8 | camaraderie | 0.039 | 0.534 | 0.0006 |

The simple correlations are all ~0.53–0.59 — indistinguishable. Only the
multivariate model separates the constructs. And the best one uniquely explains
just 1.2% of the variance; the rest is shared. **Leadership, fairness and pride
form a top tier; the order within that tier is not resolvable with this data.**

**Group differences — small.** Of 24 ANOVAs, 4 survive Benjamini–Hochberg
correction, and those same 4 are the only ones reaching even a *small* effect
size. **20 of 24 have η² < 0.01 (negligible)**, and those same 20 are also not
significant — here the two measures agree. What the p-values cannot tell you is
magnitude: they span some 30 orders of magnitude while every effect size sits
below 0.035. The largest effect anywhere is wellbeing by location (η² = 0.032,
i.e. 3.2% of the variance): Chennai sits 0.44 Likert points below Aarhus.

**ROS link — weak and fragile.** Culture index vs ROS: r = 0.448 (p = 0.028)
across 24 units, but the 95% CI runs **0.055 to 0.721**. A full leave-one-out
check makes the fragility concrete: r moves between **0.350 and 0.533** depending
on which single unit is dropped, and removing any one of **4 units** takes the
result below p < 0.05.

## Limitations

These are stated at length in [`results/decisions_log.md`](results/decisions_log.md)
and section 4 of [`results/EXPLAINER.md`](results/EXPLAINER.md). In short:

1. **The data is synthetic.** The methods are real; the findings are not
   findings about people.
2. **Common method bias.** Predictors and outcome come from the same person, on
   the same form, at the same moment. Shared mood or response style inflates
   the relationship. The huge first eigenvalue is direct evidence of it.
   **R² = 0.474 is an upper bound, not an estimate.**
3. **No causal claim is possible.** Cross-sectional, observational, single
   wave. "Driver" is used in the associational sense only; reverse causality
   fits the data equally well.
4. **Clustering is ignored.** Respondents are nested in 24 business units and
   ICC(1) = 0.11, so observations are not independent. The reported standard
   errors are somewhat too small. A mixed-effects model or cluster-robust
   errors would fix this — a genuine omission.
5. **Discriminant validity fails.** The eight constructs are reliable but not
   eight distinct things, so the lower half of the driver ranking should be
   read as approximately tied.
6. **The ROS analysis rests on n = 24**, is vulnerable to the ecological
   fallacy, and cannot distinguish which construct matters. It is a hypothesis,
   not a result.
7. **Missing At Random is assumed, not tested.** If people skipped wellbeing
   items *because* they were burnt out, wellbeing is biased upward and nothing
   here would show it.

## Running it

```bash
pip install -r requirements.txt
python run_all.py --regenerate
python -m pytest tests -q
```

The full pipeline runs in about 13 seconds and is deterministic (seed
20260907). Each stage can also be run on its own from `src/`, since every stage
reads what the previous one wrote.

> **Two environment notes.** `scikit-learn` is pinned below 1.8 because
> `factor_analyzer` 0.5.1 uses an argument removed in that version. And if
> `import matplotlib` ever fails with `DLL load failed while importing
> _imaging: The filename or extension is too long`, the project has been moved
> somewhere too deep for the Windows `MAX_PATH` limit — keep it near the drive
> root.

## Layout

```
src/
  config.py                    questionnaire definition and file paths
  generate_synthetic_data.py   Phase 0 - the data generator
  step_00_profile.py           Phase 1 - profiling
  step_01_clean.py             Phase 2 - cleaning and reverse-coding
  step_02_constructs.py        Phase 3 - alpha, EFA, construct scoring
  step_03_anova.py             Phase 4 - group differences
  step_04_regression.py        Phase 5 - driver model
  step_05_ros.py               Phase 6 - business outcome link
  plot_style.py                shared chart palette and layout helpers
  step_06_figures.py           Phase 7a - the nine presentation charts
  step_07_exports.py           Phase 7b - Power BI exports
tests/
  test_analysis_steps.py       23 tests, hand-checked expected values
results/
  EXPLAINER.md                 concepts, code walkthrough, results, interview Q&A
  decisions_log.md             every judgement call and its alternatives
  00_data_profile.md           ... through 05_ros_analysis.md
  figures/                     6 charts
  powerbi_*.csv                flat exports for Power BI
run_all.py                     runs the whole pipeline
employee_engagement_analysis.ipynb   the narrative write-up, 12 sections
```

### Start here

- **[`employee_engagement_analysis.ipynb`](employee_engagement_analysis.ipynb)** —
  the whole project as one narrative notebook, in 12 sections with the six
  charts and the findings. Outputs are saved, so it reads without running it.
  This is the one to open first.

- **[`results/EXPLAINER.md`](results/EXPLAINER.md)** — the concepts from zero, a
  file-by-file code walkthrough, the results, the four weakest assumptions, and
  twelve interview questions with answers.
- **[`results/decisions_log.md`](results/decisions_log.md)** — every judgement
  call, with the soft spots marked.
