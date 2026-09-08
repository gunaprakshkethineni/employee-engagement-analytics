# EXPLAINER — everything in this project, from zero

**SYNTHETIC DATA.** `data/raw/` was empty when this was rebuilt, so the survey
was generated from an explicit latent-variable model. The statistics are real;
the respondents are not. Lead with that whenever you present it.

---

# 1. The concepts, taught from zero

## 1.1 Why "constructs" exist at all

You cannot measure fairness with one question. Any single question is partly
about fairness and partly about the wording, the reader's mood, and whatever
happened that morning. So you ask eight questions that all circle the same
idea and average them. The random junk in each question partly cancels; the
common signal survives.

That average is a **construct score**. The eight questions are **items**. The
thing they are all supposed to be measuring — fairness — is a **latent
variable**: real, causal, and never directly observed.

## 1.2 Cronbach's alpha — what it actually measures

Alpha asks one question: **do these items move together?**

The formula:

```
alpha = k/(k-1) × (1 − Σ(item variances) / variance of the total score)
```

The intuition sits in that ratio. Suppose eight items are unrelated. Then the
variance of their sum is just the sum of their variances, the ratio is 1, and
alpha is 0. Now suppose they measure the same thing. When one is high the
others are high too, so the *sum* swings much harder than the individual items
do. The total variance balloons, the ratio shrinks, alpha rises toward 1.

**What alpha = 0.80 means.** Roughly: 80% of the variance in the scale score is
shared, systematic variance and 20% is noise. Conventions: 0.70 acceptable,
0.80 good, 0.90 very good.

**Three things alpha is not, all of which get asked:**

1. **Alpha is not validity.** It says the items agree with each other. It says
   nothing about whether they agree about the *right* thing. Eight questions
   about your commute would have a splendid alpha and measure nothing about
   fairness.

2. **Alpha is not unidimensionality.** A scale with two distinct sub-themes
   that happen to correlate can post a high alpha. Proving one dimension needs
   factor analysis — which is exactly why Section 3 of this project exists.

3. **Alpha rises with the number of items.** Add more items of the same quality
   and alpha goes up mechanically. 0.87 on 8 items is respectable; 0.87 on 40
   items would mean the items are individually poor. Pinned down by
   `test_alpha_rises_when_more_good_items_are_added`.

**Alpha above 0.95 is a warning, not a triumph** — it usually means the items
are near-duplicates and the scale is wasting the respondent's time.

## 1.3 Why reverse-coded items exist

Ask 68 questions in a row that are all phrased positively and some people stop
reading and tick 4 all the way down. That is **acquiescence bias**.

The defence is to phrase some items negatively:

> `cred_03`: "Management is honest about the state of the business."
> `cred_04`: "Management hides bad news from staff."

Someone genuinely positive answers 5 then 1. Someone on autopilot answers 4
then 4 — and now contradicts themselves visibly.

Before scoring, negative items must be flipped: `new = (1 + 5) − old`, so 1↔5,
2↔4, 3 stays. Skip this and `cred_04` correlates *negatively* with the rest of
its scale and drags alpha toward zero. In this project six items are reversed:
`cred_04, resp_06, fair_03, camr_08, lead_07, well_05`.

**The subtlety that matters here.** Reverse items come with a cost. In this
data all six sit at **0.42–0.48** on item-total correlation against a median of
**0.66** for normally worded items — only one of the other 57 items falls below
0.50. And the factor analysis found the six form **their own factor**, made
purely of question phrasing. That is a **method factor** — see 1.4.

## 1.4 Factor analysis — what it is doing

Alpha asks "do these items move together?". Factor analysis asks the harder
question: **how many separate things are these 68 items measuring, and which
item measures which?**

The input is the correlation matrix of all items. The method searches for a
small number of unobserved factors that could have produced that pattern of
correlations. Each item gets a **loading** on each factor — a correlation
between the item and the factor. A clean result looks like a block diagram:
each item loads high (>0.5) on one factor and near zero on the rest.

Two choices matter:

- **How many factors?** Theory says 8. The data is consulted separately via
  eigenvalues (how much variance each factor explains).
- **Rotation.** The raw solution is mathematically arbitrary — rotation spins
  the axes to a more interpretable position. **Varimax** forces factors to be
  uncorrelated. **Oblimin** allows them to correlate. This project uses
  **oblimin**, because culture constructs plainly correlate (r = 0.60–0.76) and
  forcing them apart would answer a question nobody asked.

**What it found here, and it is not flattering:**

- First eigenvalue **23.85**, second **2.19**. One enormous general factor — a
  **halo effect**. People who like their employer like *everything* about it.
- Credibility and leadership **cannot be separated** — both load on factor F1,
  and they correlate at r = 0.76. That is a failure of **discriminant
  validity**: the eight scales are reliable but they are not eight distinct
  things.
- **F8 is made entirely of the six reverse-worded items** (mean loading 0.46;
  no normally worded item exceeds 0.23). It is a factor about grammar, not
  about the workplace.

Reported as found. Overclaiming here is what an interviewer is hunting for.

## 1.5 Eta squared — what a p-value cannot tell you

A **p-value** answers: "if there were truly no difference between these groups,
how surprising would this data be?" It says nothing about size.

The problem is that p-values depend on sample size. Any difference, however
microscopic, becomes "significant" with enough data. At n ≈ 4,850 this analysis
could detect a gap of a few hundredths of a scale point — far below anything
worth acting on.

**Eta squared** answers the question you actually care about: **what fraction
of the variation in this construct is explained by the grouping?**

```
eta² = between-group variation / total variation
```

Conventions: 0.01 small, 0.06 medium, 0.14 large.

**This project is a clean demonstration.** 24 ANOVAs were run. The largest
effect in the entire set is wellbeing by location at **eta² = 0.032** — location
explains 3.2% of the variation in wellbeing. **20 of the 24 tests have eta²
below 0.01**, i.e. negligible.

Worth being precise here, because it is easy to overclaim: in this data the two
measures happen to *agree*. Only 4 tests are significant at p < 0.05 (19 have
p > 0.10, median p = 0.61), and they are the same 4 that clear the effect-size
bar. The demographic differences are genuinely near zero, so significance never
had the chance to mislead.

What the p-values still cannot do is rank importance. Across the 24 tests they
span roughly **30 orders of magnitude** while every effect size sits below
0.035. A p-value of 1e-31 and one of 1e-10 sound worlds apart and differ by
0.02 of explained variance. That is the lesson: p answers "is it zero?", eta
squared answers "does it matter?", and only the second is a business question.

## 1.6 VIF — what multicollinearity actually breaks

When predictors correlate with each other, regression struggles to apportion
credit between them. If leadership and credibility move together, the data
cannot say which one moved satisfaction.

**VIF (Variance Inflation Factor)** quantifies it:

```
VIF_j = 1 / (1 − R²_j)
```

where R²_j comes from regressing predictor *j* on all the other predictors. A
VIF of 4 means that coefficient's standard error is √4 = 2× wider than if the
predictor were independent. Conventions: above 5 is a warning, above 10
serious.

**What multicollinearity does NOT do:** it does not bias the coefficients, and
it does not hurt prediction. OLS is still unbiased. What it destroys is
*stability* — small changes in the data can reshuffle the ranking.

**Here:** highest construct VIF is **2.98** (leadership). Below the warning
line, so nothing was removed. But — and this is the honest part — VIF being
acceptable does *not* mean the constructs are distinct. r = 0.76 between
credibility and leadership is still r = 0.76. Which is why the driver ranking
is reported three different ways instead of one.

## 1.7 R squared — what it does and does not mean

R² is the share of variance in the outcome that the model accounts for. Here,
**R² = 0.474**: the model explains 47.4% of the differences between individuals
in satisfaction.

**What it does not mean:**

- **It is not a measure of correctness.** A model can have a high R² and be
  causally backwards.
- **It is not comparable across fields.** In turbine power-curve modelling R² of
  0.99 is routine, because the physics is deterministic and the noise is
  instrumentation. In cross-sectional human survey data, 0.30–0.50 is typical.
  The same number means opposite things in the two settings.
- **It is in-sample.** It can only rise when you add predictors, even useless
  ones. **Adjusted R²** penalises predictor count: here 0.471 versus 0.474, a
  gap of 0.003, which says the model is not being flattered by its 26 terms.
- **It says nothing about whether the effects are large enough to act on.**

---

# 2. The code, file by file

Run everything with `python run_all.py --regenerate`. Takes about 8 seconds.

### `src/config.py`
The questionnaire, in one place: 64 culture items across 8 constructs, 4
satisfaction items, which 6 items are reverse-worded, the wording of every
question, the demographic columns and all file paths. No analysis script
hard-codes a column name; they all ask this file.

### `src/generate_synthetic_data.py`  *(Phase 0)*
Builds the data the way theory says it is built, so that the psychometrics have
to be *discovered* rather than asserted:

1. One general "good place to work" tendency **G** per person.
2. Eight culture factors hanging off G (weight 0.80), which is what makes them
   correlate. Credibility and leadership get an extra shared component — the
   planted discriminant-validity problem.
3. Business-unit offsets and small demographic shifts.
4. Each item = a weak loading (0.58–0.75) on its factor + a per-respondent
   **response-style** term + noise, then chopped into 1–5 categories.
   `devl_04` and `resp_02` are built as near-duds (loadings 0.15 and 0.18).
5. Reverse items are generated with a negative loading, so the raw file
   genuinely needs recoding.
6. Real-survey mess added last: 150 straight-liners, 2.6% missing rising down
   the questionnaire, 42 out-of-range `6`s, 27 `99`s, 12 duplicate rows, 60
   untidy department labels.
7. A 24-unit table where ROS is *correlated with but not determined by* unit
   culture.

### `src/step_00_profile.py`  *(Phase 1)* → `results/00_data_profile.md`
Describes the raw file before anything is touched: 5,012 rows × 74 columns,
answer distribution, missingness per item, demographic breakdowns, a data
dictionary, and a data-quality table that finds all six planted problems.
Profiling *before* cleaning matters — clean first and you can no longer tell
whether a problem was in the data or created by your own code.

### `src/step_01_clean.py`  *(Phase 2)* → `results/01_cleaning_log.csv`
Seven logged steps. The one to understand is the **ordering**: straight-liners
are detected on the **raw** answers, *before* reverse-coding. Someone who ticks
4 down the page has zero variance in the raw file; flip their six reverse items
to 2 first and they suddenly look thoughtful. 150 caught (3.0%).

`reverse_code()` lives here and is unit-tested.

Also here: the missing-data decision. Listwise deletion across 68 items would
have kept **792 of 4,850 respondents (16.3%)**, so construct scores are the mean
of *answered* items given ≥50% of a construct was answered. 4,850 rows survive.

### `src/step_02_constructs.py`  *(Phase 3)* → reliability + loadings
The psychometric core.

- `cronbach_alpha()` — written out longhand so it can be hand-checked in tests,
  then cross-validated against `pingouin`.
- `item_statistics()` — corrected item-total correlations (item vs the sum of
  the *other* items) and alpha-if-deleted.
- `review_construct()` — drops an item only if it fails **both** tests
  (item-total < 0.30 **and** alpha improves). One item dropped: `devl_04`.
- `run_factor_analysis()` — KMO, Bartlett, eigenvalues, then oblimin EFA.
- `check_structure_matches_theory()` — finds the 8 constructs collapse to 7.
- `check_reverse_wording_method_factor()` — detects F8 automatically.
- `score_constructs()` — mean scoring, with the reasoning in the docstring.

### `src/step_03_anova.py`  *(Phase 4)* → `results/03_anova_summary.md`
8 constructs × 3 groupings = 24 tests. Levene's test first; 3 cases failed and
switched to Welch. Eta squared computed longhand and unit-tested. Benjamini–
Hochberg FDR across all 24. Tukey HSD on the 4 that survive (61 pairwise
comparisons).

### `src/step_04_regression.py`  *(Phase 5)* → `results/04_regression_summary.md`
VIF **before** any coefficient is read. Then OLS with HC3 robust standard
errors (Breusch–Pagan p = 2.2e-15). Standardised betas for the constructs, raw
for the dummies. `unique_contribution()` refits the model eight times, dropping
one construct each time, to measure what each explains that nothing else does.

### `src/step_05_ros.py`  *(Phase 6)* → `results/05_ros_analysis.md`
ICC first — is averaging 200 people into a unit score even legitimate? Then
correlations with Fisher-z confidence intervals, a single-predictor regression,
and a Cook's-distance influence check that turns out to matter a great deal.

### `src/plot_style.py` + `src/step_06_figures.py`  *(Phase 7a)* → 6 charts
`plot_style.py` holds the shared look — colours, spacing, the header block — so
the six charts match each other instead of looking like six separate notebook
outputs. Each chart gets three lines at the top: what it is, what it shows in
plain English, and the small print (definitions, sample size, and the causal
caveat where one is needed).

The charts are built around business questions rather than around the
statistics: where we stand, what to fix first, where the problem sits, what weak
leadership costs, which units need attention, and whether any of it reaches the
P&L. The method evidence — reliability, the factor structure, the residual
diagnostics — is not charted any more. It lives in `results/*.csv` and in
sections 1 and 3 of this document, which is where a technical reviewer looks
anyway.

Two definitions the charts rely on, both standard in engagement survey work:

- **Favourable** = the share of people scoring 4 or 5 out of 5 on a topic.
- **At risk** = overall satisfaction below 3.0 out of 5. The satisfaction scale
  includes "I rarely think about leaving", so a low score is the closest thing
  this survey has to a flight-risk signal. It is a proxy, not observed turnover,
  and chart 04 says so on its face.

### `src/step_07_exports.py`  *(Phase 7b)* → 3 Power BI CSVs
A wide respondent table, a long table so `construct` works as a slicer, and the
unit summary. It finishes by sweeping `results/` and stamping the synthetic
marker onto any CSV that does not already carry it.

### `tests/test_analysis_steps.py`
23 tests, all passing. Expected values are worked out by hand in the comments
(the alpha example is computed line by line) rather than copied from a library,
because comparing two implementations only proves they agree. Includes a test
that pins down the straight-liner ordering decision.

---

# 3. The results

## 3.1 Reliability — all eight scales hold together

| Construct | Items | Cronbach's α |
|---|---|---|
| pride | 8 | **0.893** |
| development | 7 (`devl_04` dropped) | **0.888** |
| fairness | 8 | 0.882 |
| camaraderie | 8 | 0.880 |
| wellbeing | 8 | 0.879 |
| leadership | 8 | 0.878 |
| credibility | 8 | 0.867 |
| respect | 8 | 0.850 |
| *satisfaction (outcome)* | 4 | 0.872 |

All above 0.80. One item removed: `devl_04` ("challenging work"), item-total
r = 0.291, and development's alpha rose 0.869 → 0.888.

**But the factor analysis qualifies this.** Reliable ≠ distinct:
- 8 constructs collapse onto **7 factors**; credibility and leadership are
  indistinguishable (r = 0.76).
- First eigenvalue 23.85 vs second 2.19 — one dominant halo factor.
- F8 is a reverse-wording method factor.

## 3.2 Drivers of satisfaction

**R² = 0.474, adjusted R² = 0.471, n = 4,846**, HC3 robust standard errors.

| Rank | Construct | Std. β | 95% CI | Simple r | ΔR² if removed |
|---|---|---|---|---|---|
| 1 | leadership | **0.183** | 0.146 – 0.220 | 0.591 | 0.0112 |
| 2 | fairness | **0.172** | 0.139 – 0.206 | 0.585 | **0.0120** |
| 3 | pride | **0.145** | 0.113 – 0.178 | 0.572 | 0.0086 |
| 4 | credibility | 0.093 | 0.057 – 0.129 | 0.572 | 0.0030 |
| 5 | respect | 0.087 | 0.055 – 0.120 | 0.541 | 0.0033 |
| 6 | development | 0.059 | 0.026 – 0.092 | 0.535 | 0.0014 |
| 7 | wellbeing | 0.048 | 0.014 – 0.081 | 0.531 | 0.0009 |
| 8 | camaraderie | 0.039 | 0.006 – 0.071 | 0.534 | 0.0006 |

**The most important thing on this table is the two right-hand columns.**

The simple correlations are all between 0.53 and 0.59 — essentially identical.
Looked at one at a time, every construct appears to be an equally powerful
driver. That is the halo. Only the multivariate model separates them, spreading
β from 0.183 down to 0.039.

And the ΔR² column undercuts even that: **the best construct uniquely explains
1.2% of the variance.** The other 46% is shared between all eight. That is
multicollinearity being honest, and it is why leadership ranks 1st by β but 2nd
by unique contribution while fairness does the reverse.

**The defensible claim:** leadership, fairness and pride form a top tier clearly
separated from wellbeing and camaraderie. Within the top tier, this data cannot
resolve the order.

**Controls:** role level matters (senior managers +0.21 points, p < 0.0001).
Location dummies are all non-significant *once the constructs are in the model*
— site differences in satisfaction run **through** wellbeing and leadership
rather than around them.

## 3.3 Group differences that matter

24 tests; 4 survive BH correction, and those same 4 are the only ones reaching
even a small effect size.

| Construct × Grouping | Test | η² | Size |
|---|---|---|---|
| wellbeing × location | one-way ANOVA | **0.032** | small |
| leadership × location | one-way ANOVA | 0.015 | small |
| pride × tenure band | one-way ANOVA | 0.013 | small |
| development × department | **Welch** ANOVA | 0.012 | small |

**20 of 24 are negligible (η² < 0.01).** Nothing anywhere reaches "medium".

Tukey HSD, in Likert points on the original 1–5 scale:

- **Chennai is the problem site for wellbeing**: 0.44 below Aarhus, 0.40 below
  Pune, 0.30 below Hamburg (all p < 0.0001). It also trails on leadership
  (0.27 below Aarhus).
- **Honeymoon effect on pride**: employees under 1 year score 0.27 above those
  at 3–5 years.
- **Development**: Operations sits 0.26 below HR.

Even the biggest of these is under half a scale point. Real, actionable,
and nothing like as dramatic as the p-values suggest.

## 3.4 The ROS link — weak and fragile

- ICC(2) = 0.96 → unit means are reliable, so aggregating is legitimate.
  (ICC(1) = 0.11 → which unit you're in explains 11% of an individual's score.)
- Culture index vs ROS: **r = 0.448, R² = 0.201, p = 0.028, n = 24**.
  Slope ≈ 3.2 ROS points per Likert point.
- **95% CI on r: 0.055 to 0.721.** Compatible with "almost nothing" and "quite
  strong" simultaneously.
- **Removing one unit (BU17, Cook's D = 0.374) moves r to 0.350 and p to
  0.102** — from significant to not.
- The full leave-one-out check (`results/05_leave_one_out.csv`, chart 15) shows
  that is not a one-unit quirk: r ranges from **0.350 to 0.533** across the 24
  versions, and **4 of the 24** drop below p < 0.05.
- All eight constructs correlate with ROS at 0.42–0.47, statistically
  indistinguishable. This data cannot say *which* aspect of culture matters.

**Verdict: a hypothesis worth testing properly, not a result.**

---

# 4. The four weakest assumptions

### 1. Common method bias — predictors and outcome come from the same person, at the same moment, on the same form
Someone in a bad mood marks everything down, manufacturing correlation between
predictor and outcome out of nothing. The evidence is in the data: a first
eigenvalue of 23.85 against a second of 2.19 is what a strong shared response
tendency looks like. **R² = 0.474 is an upper bound**, not an estimate. The fix
requires an outcome from a different source — retention records, absence data,
manager ratings — which this design does not have. *This is the most serious
weakness in the individual-level analysis.*

### 2. No causal identification whatsoever
Cross-sectional, observational, single wave. "Better leadership raises
satisfaction" and "satisfied people rate their leaders more generously" predict
this data equally well and nothing here separates them. Every result is a
statement about association. **Never say "driver" in an interview without
immediately saying "in the associational sense".**

### 3. Clustering is ignored
Respondents are nested inside 24 business units, and ICC(1) = 0.11 means 11% of
an individual's score is explained by their unit. Observations within a unit are
not independent, which is what OLS standard errors assume. The effective sample
size is smaller than 4,846, so **the standard errors in Section 3.2 are somewhat
too small and the confidence intervals somewhat too narrow**. A multilevel
(mixed-effects) model with random intercepts by unit, or cluster-robust standard
errors, would fix it. This is a genuine omission — own it before it is found.

### 4. The eight constructs are not eight distinct constructs
Reliability is fine; discriminant validity is not. Credibility and leadership
correlate at 0.76 and load on the same factor. Reporting a ranked driver table
of eight constructs implies a separation the measurement model does not
support. Everything below the top tier of the ranking should be read as
approximately tied.

*(Honourable mentions: Missing At Random is assumed but untested; the ROS
analysis carries its own set of limitations documented in `05_ros_analysis.md`.)*

---

# 5. Twelve questions a rigorous interviewer will ask

**Q1. Your alphas are all around 0.87. Doesn't that just mean you asked the same question eight times?**

Partly, and that is the right instinct. Alpha rises mechanically with scale
length, so 0.87 on 8 items is respectable rather than remarkable — the same
alpha on 40 items would signal weak individual items. What stops it being pure
redundancy is that mean inter-item correlations sit between 0.41 and 0.53, not
0.9 — the items overlap without being paraphrases. But
the real answer is that alpha was not treated as sufficient: the factor analysis
was run precisely to test whether the scales are distinct, and it found they are
not entirely — credibility and leadership collapse into one factor. I report
that rather than resting on the alphas.

**Q2. You call them "drivers". Can you actually claim causality?**

No, and the word is doing work it hasn't earned. The design is cross-sectional,
observational and single-wave. Reverse causality is entirely plausible —
satisfied employees may simply rate their managers more generously. There is
also no control for anything unmeasured that moves both: a competent site
manager could raise leadership scores and satisfaction independently.

To make a causal claim I would need culture measured at t1 and satisfaction at
t2, several waves, unit fixed effects to absorb time-invariant differences, and
ideally something exogenous — a reorganisation, a policy rollout that hit some
units and not others. What I have supports "leadership perceptions are the
strongest correlate of satisfaction in this data, conditional on the others".

**Q3. Your constructs correlate at 0.76. How can you rank them as separate drivers?**

Carefully, and with three rankings rather than one. VIF is 2.98 at worst, below
the conventional threshold of 5, so the model is estimable and standard errors
are not catastrophically inflated — OLS remains unbiased. But an acceptable VIF
does not make r = 0.76 disappear.

So I report standardised β, the zero-order correlation, and ΔR² when each
construct is dropped. They disagree: leadership is 1st by β but 2nd by unique
contribution. That disagreement is the finding. My claim is that leadership,
fairness and pride form a top tier separated from camaraderie and wellbeing —
not that leadership is precisely first. I deliberately did not drop one of the
correlated pair, because that would load the survivor's coefficient with the
dropped construct's variance and mislead more confidently.

**Q4. All your data comes from one questionnaire filled in by one person. What does that do to your results?**

It inflates them, and I can show it. This is common method bias: predictors and
outcome share a source, so anything affecting how a person responds in general —
mood, acquiescence, loyalty — creates correlation between them that has nothing
to do with the constructs.

The evidence is in the factor analysis. A first eigenvalue of 23.85 against a
second of 2.19 is a dominant general factor. Some of that is real (culture
genuinely is coherent); some is method. Nothing in this design separates the
two. So R² = 0.474 is an upper bound. To bound the bias properly I would need a
marker variable theoretically unrelated to culture, or a CFA with an explicit
method factor, or — best — an outcome from a different source such as actual
turnover.

**Q5. R² of 0.47 — is that good?**

The question has no answer without a field. For cross-sectional self-report
survey data predicting an attitude, 0.30–0.50 is typical, so 0.47 is
unremarkable in a good way. For a turbine power curve it would mean the model
was broken.

More usefully, 0.47 is not the interesting number. Adjusted R² is 0.471 against
0.474, so the model is not inflated by its 26 predictors. And R² tells you
nothing about whether individual effects are large enough to act on — the
largest standardised β is 0.183, meaning a full standard deviation improvement
in leadership perception moves satisfaction by less than a fifth of a standard
deviation. That is the number a business should be told, not the R².

**Q6. Is the ROS link meaningful at all?**

Barely, and I would not build a business case on it. r = 0.448 sounds
respectable until you look at the confidence interval: 0.055 to 0.721 on 24
units. And the influence check is worse — removing the single most influential
unit moves r to 0.350 and p from 0.028 to 0.102. One data point out of 24 flips
the result from significant to not.

There is also an ecological fallacy risk: this is a relationship between unit
averages, which licenses no statement about individuals — the within-unit
relationship could be zero or negative. And even taken at face value, causality
runs at least as plausibly the other way: profitable units can afford better
staffing, equipment and training.

The direction matches the published literature, which is mild support. That is
the whole claim.

**Q7. Why average items rather than use factor scores?**

Interpretability and stability. A mean stays on the original 1–5 scale, so "3.8
on fairness" means something to a manager and is comparable to next year's
score. Factor scores use sample-specific weights that change every time the
survey is re-run, so year-on-year tracking becomes incoherent. At α ≈ 0.87 the
two correlate above 0.95, so the cost is negligible.

The honest caveat: mean scoring implicitly assumes all items are equally good
indicators, which the loadings show they are not (they range 0.4–0.65). Factor
scores would weight them properly. I traded a small amount of precision for
usability, deliberately.

**Q8. You ran 24 ANOVAs. How did you handle the multiple comparisons problem?**

Benjamini–Hochberg FDR at 5% across all 24 omnibus tests, plus Tukey HSD within
each significant test, which carries its own built-in correction for pairwise
comparisons.

I chose BH over Bonferroni deliberately. Bonferroni controls the probability of
*any* false positive and would be very conservative across 24 tests, hiding real
but modest differences — the wrong trade for exploratory survey work. BH
controls the expected *proportion* of false discoveries.

In practice it barely mattered: 4 tests survive correction, and they are exactly
the 4 that reach even a small effect size. That agreement is reassuring.

**Q9. With n = 4,850 everything must have come out significant. How do you know any of it is real?**

Actually it did not, and that is worth stating plainly because it is the
opposite of what people expect. Only **4 of the 24 tests reach p < 0.05**. 19
have p > 0.10 and the median p-value is 0.61. The demographic differences in
this data are genuinely close to zero, so the large sample never got the chance
to manufacture false findings.

Where the large n does bite is precision, not false positives: at this size I
could detect a gap of 0.05 Likert points, which no organisation could act on. So
I lead with eta squared. 20 of 24 tests are negligible (η² < 0.01), and the four
that are significant are the same four that clear the effect-size bar.

The part that still needs care is that p-values cannot rank importance. Across
these tests they span about 30 orders of magnitude while every effect size sits
below 0.035. My summary: one site-level wellbeing issue worth a real
intervention (η² = 0.032, Chennai 0.44 points below Aarhus), and everything else
too small to act on.

**Q10. You dropped one item. Why that one, and did you fish for a better alpha?**

`devl_04` was dropped: corrected item-total correlation 0.291, and development's
alpha rose from 0.869 to 0.888.

The rule was set before looking — drop only if item-total < 0.30 **and** alpha
improves. Requiring both conditions is the guard against fishing. Four of the
six reverse-worded items would have raised alpha if deleted, but their
item-total correlations are 0.42–0.48, so they stayed. A one-condition rule
would have quietly stripped every reverse item and reported a higher alpha as a
success, while removing the scale's only protection against acquiescence.

Where I am exposed: `resp_02` scraped through at 0.313. Removing it would raise
respect's alpha from 0.850 to 0.864, and it is arguably a facilities question
rather than a respect question. I kept it because moving a threshold after
seeing which items it catches is exactly the flexibility that makes results
irreproducible. It is a judgement call and it is documented in the decisions
log.

**Q11. Your respondents are nested in 24 business units. Does that break your regression?**

It doesn't break it, but it does make my standard errors too small, and this is
the omission I would fix first. ICC(1) is 0.11, so 11% of an individual's score
is explained by their unit. Observations within a unit are therefore not
independent — which is precisely what OLS standard errors assume. My effective
sample size is smaller than 4,846, so the confidence intervals in the driver
table are somewhat too narrow.

The fix is a mixed-effects model with random intercepts by business unit, or
cluster-robust standard errors clustered on unit. The coefficients would barely
move; the uncertainty would widen. It would not change the ranking, which is
why I reported the result — but it is a real methodological gap, not a
rounding detail.

**Q12. Your factor analysis found an eighth factor made only of reverse-worded items. What is that?**

A method factor — an artefact of question phrasing rather than anything about
the workplace. All six reverse items load on F8 at 0.43–0.49, and no normally
worded item exceeds 0.23. It happens because some respondents don't fully
process the polarity switch, so the negative items share variance for a purely
linguistic reason.

It has three consequences I report: it inflates the apparent number of factors
(9 eigenvalues above 1, not 8); it explains why those six items have the weakest
item-total correlations in their scales; and it means the reverse items are
measuring slightly different things from their neighbours even after recoding.
The code detects it automatically rather than leaving it to be noticed —
`check_reverse_wording_method_factor()` in `step_02_constructs.py`.

The trade-off is real: reverse items cost measurement precision and buy
protection against straight-lining. Given that 150 respondents were caught
straight-lining, I would keep them, but I would reword them to avoid negation
("Management is slow to share bad news" rather than "hides bad news").

---

# 6. Where all of this reappears in turbine fleet performance

The subject matter is different; the statistical problems are largely the same.
Concretely, mapping each method onto the job:

### Regression → power curve deviation and AEP loss attribution
Modelling actual power against wind speed, air density, turbulence intensity,
yaw misalignment, blade pitch and ambient temperature is the same OLS problem
in a different costume. The interpretation shifts, though: R² of 0.47 would be a
broken model there, because the physics is close to deterministic. What carries
over exactly is the **standardised coefficient** logic — ranking which
operational variable moves output most, in comparable units.

### Multicollinearity → it is worse in turbine data, not better
Wind speed, turbulence intensity and air density are mutually correlated;
turbulence and wake exposure are near-proxies for each other; nacelle
anemometer readings are contaminated by the rotor they sit behind. Regressing
power on all of them produces coefficients that reshuffle between months. The
ΔR²-when-dropped approach I used here is directly transferable, as is the
discipline of checking VIF *before* interpreting anything.

### ANOVA and effect sizes → comparing turbines across a fleet
"Does turbine model A underperform model B?" is a one-way ANOVA with turbines
as observations. And the sample-size trap is identical but sharper: 10-minute
SCADA data gives ~52,000 observations per turbine per year, so **everything is
significant**. The question that matters is η²-shaped: does the site explain
enough variance in capacity factor to justify a retrofit? A statistically
overwhelming 0.2% AEP difference may not clear the cost of a technician visit;
a marginally significant 3% difference certainly does. Effect size *is* the
business case.

### Assumption checking → the same checks, different failure modes
- **Heteroscedasticity**: power output variance grows with wind speed and
  explodes near rated. This is my Breusch–Pagan situation, more extreme.
  Robust standard errors are the same answer.
- **Non-normal residuals**: curtailment and downtime create a spike at zero
  power — a censored outcome, not a mild deviation. That needs a different model
  (a two-part or Tobit approach), not just robust errors.
- **The one that has no analogue here, and it is the big one**: SCADA data is a
  **time series**. Consecutive 10-minute records are heavily autocorrelated, so
  the effective sample size is a small fraction of the nominal one and naive
  standard errors are wildly optimistic. It is structurally the same error as my
  ignored clustering — non-independent observations treated as independent —
  which is why I flagged that as a weakness rather than hiding it. The remedies
  (Newey–West standard errors, block bootstrapping, aggregating to daily) are
  the time-series cousins of cluster-robust errors.

### ICC and nesting → turbines within sites, sites within regions
Turbines on one site share wind resource, terrain and maintenance crew. That is
exactly respondents nested in business units, and ICC quantifies how much of a
turbine's performance is a site effect rather than a turbine effect — which is
the difference between a fleet-wide design issue and a local one. Mixed-effects
models with random intercepts by site are the standard tool, and are precisely
what I said I would add to this project.

### Reliability and measurement error → sensor calibration
Cronbach's alpha is a measurement-error question: how much of what I recorded is
signal? The turbine analogue is anemometer drift, icing, and nacelle transfer
function error. The consequence is the same and is routinely forgotten:
**measurement error in a predictor attenuates its regression coefficient toward
zero**. A poorly calibrated sensor makes a real effect look weak. Redundant
sensors averaged together are the engineering version of averaging eight items
into a construct score, and for the same reason.

### Signal versus noise → the through-line
The core discipline in this project was refusing to report significance as
importance, and reporting the halo effect and the fragile ROS link rather than
smoothing them. Fleet performance analysis rewards the same instinct: an
underperformance flag has to survive normalisation for wind resource, air
density, wake position, curtailment and availability before it means anything.
Most apparent underperformance is a covariate you have not adjusted for.
Knowing which conclusions your data cannot support is the transferable skill —
and it is the one I would bring to a turbine fleet.
