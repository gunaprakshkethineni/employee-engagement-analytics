# Decisions log — SYNTHETIC DATA

Every judgement call made in this project, the alternatives that were rejected,
and the reasoning. The soft spots are marked **⚠ SOFT SPOT** so you know where
you are exposed before an interviewer finds it.

---

## D0. Data is synthetic, and that is the biggest limitation of all

`data/raw/` was empty when the rebuild started, so there was no real survey to
analyse. Two options:

- **Rejected:** fabricate plausible-looking summary numbers to match the
  original project description. That would be dishonest and unpresentable.
- **Chosen:** generate the data from an explicit latent-variable model
  (`src/generate_synthetic_data.py`) and mark every output `SYNTHETIC DATA`.

The generator builds eight latent culture factors first and then produces
Likert items as noisy indicators of them, so reliability and factor structure
have to be *discovered* by the analysis rather than being written in by hand.

**⚠ SOFT SPOT.** The analysis is real; the data is not. Say this in the first
30 seconds of any conversation about it. Anything you claim about employee
behaviour is a claim about the generator, not about employees. What the project
demonstrates is method, not findings.

---

## D1. Virtual environment lives outside the project folder

`pip install` succeeded inside the project but `import matplotlib` then failed
with `ImportError: DLL load failed while importing _imaging: The filename or
extension is too long`. The project sits at a deep Windows path and the
resulting `site-packages` path exceeded the Windows `MAX_PATH` limit.

- **Rejected:** enabling Windows long-path support — a system-wide registry
  change, not mine to make on someone else's machine.
- **Chosen:** create the environment at `C:\Users\gunar\.venvs\gptw`.

`requirements.txt` is unaffected; only the environment's location moved. Move
the project to a shorter path and `python -m venv .venv` will work normally.

## D2. scikit-learn pinned below 1.8

`factor_analyzer` 0.5.1 calls `check_array(..., force_all_finite=...)`, which
scikit-learn removed in 1.8. Pinned to `scikit-learn<1.8` rather than patching
a library. A deprecation warning is emitted and is harmless.

---

## D3. Straight-liners are detected BEFORE reverse-coding

This is the ordering decision that is easiest to get wrong and hardest to spot
afterwards. A respondent who ticks 4 for all 68 items has zero variance in the
raw file. Reverse-code first and their six reverse items become 2 — they now
have a within-person SD of about 0.5 and sail through any variance filter.

Order used: drop duplicates → tidy text → blank out-of-scale → **detect
straight-liners** → reverse-code → drop heavy non-responders.

Locked down by `test_straight_liners_must_be_detected_before_reverse_coding`.
150 of 5,000 respondents (3.0%) were removed.

**Threshold: within-person SD < 0.30.** Arbitrary but defensible — roughly
"used at most two adjacent scale points across 68 questions". A stricter 0.50
would also have caught genuine but consistent respondents.

## D4. Out-of-range values become missing, not numbers

42 values of `6` in `fair_01` and 27 values of `99` in `well_02`. The `99` is
almost certainly a "prefer not to say" code that leaked through an export.

- **Rejected:** clipping to the scale (a 99 is not a 5).
- **Rejected:** dropping those respondents entirely (loses 69 valid answers to
  fix 69 invalid ones).
- **Chosen:** recode to missing and let the missing-data policy handle them.

## D5. Available-item scoring, not listwise deletion or imputation

The single most consequential cleaning decision, and the numbers make it easy.

Missingness is only 2.7% of cells, but it is spread thinly across 68 items, so
almost every respondent has *something* missing. **Listwise deletion across all
68 items would have retained 792 of 4,850 respondents — 16.3%.** That is a
catastrophic loss, and the survivors would be systematically different people
(fast, complete, engaged responders).

- **Rejected: listwise deletion.** Throws away 84% of the sample.
- **Rejected: multiple imputation (MICE).** Statistically the best answer and
  the honest thing to say if pushed. Not used because the analysis is built on
  scale means, where available-item scoring is standard practice and the two
  agree closely at 2.7% missingness. It also adds pooling machinery across
  imputed datasets to every downstream ANOVA and regression.
- **Rejected: mean imputation at item level.** Invents variance that is not
  there and shrinks standard errors dishonestly.
- **Chosen:** a construct score is the mean of the items that person actually
  answered, provided they answered **at least 50%** of that construct's items.

**⚠ SOFT SPOT.** This assumes data are Missing At Random. Missingness rises
steadily down the questionnaire, which is consistent with fatigue rather than
content-related non-response, but it was not formally tested. If people skipped
the wellbeing items *because* they felt burnt out, wellbeing scores are biased
upward and nothing here would reveal it.

## D6. Imputation IS used, but only for the factor analysis

EFA needs a complete matrix. Gaps were filled with the respondent's own mean on
the other items of the same construct — but only for that step.

Cronbach's alpha is computed on **complete cases within each construct**
(3,526–4,339 respondents depending on construct). Filling a gap with a value
derived from the person's other answers in the same scale would make the scale
look more internally consistent than it is. Keeping the two steps on different
data is deliberate.

---

## D7. Items are dropped only if they fail TWO tests

Rule: drop if corrected item-total correlation < 0.30 **AND** alpha rises when
the item is removed.

Requiring both conditions matters. Four of the six reverse-worded items have
`alpha_if_deleted` above the current alpha — deleting them would raise alpha —
but their item-total correlations are 0.42–0.48, comfortably acceptable. A
one-condition rule would have quietly deleted the reverse items and produced a
scale with no protection against acquiescence at all, while reporting a *higher*
alpha as evidence of a job well done. Chasing alpha upwards by deletion is how
you end up with eight near-identical items and a meaningless 0.95.

**Result: one item dropped.** `devl_04` ("I am given challenging work that
stretches me"), item-total r = 0.291. Development alpha rose 0.869 → 0.888.

**⚠ SOFT SPOT: `resp_02` was kept at r = 0.313.** "I am given the equipment and
resources to do my job well" scrapes over a threshold that is itself a
convention, not a law. It is arguably a facilities question rather than a
respect question. Removing it would raise respect's alpha from 0.850 to 0.864.
It was kept because the rule was fixed before looking at the results, and
moving a threshold after seeing which items it catches is exactly the kind of
flexibility that makes results unreproducible. Be ready to say that.

## D8. Oblique (oblimin) rotation, not varimax

Varimax forces the extracted factors to be uncorrelated. The eight culture
constructs correlate at r = 0.60–0.76 in this data, so forcing orthogonality
would answer a question nobody asked and would smear the real structure.
Oblimin lets factors correlate.

## D9. Eight factors extracted because theory says eight — and the data disagrees

The scree/eigenvalue evidence does not support eight clean factors:

- The **first eigenvalue is 23.85**; the second is 2.19. That is a dominant
  general factor — a halo. People who like one thing about their employer like
  everything about it.
- Nine eigenvalues exceed 1, not eight.
- **The eight constructs map onto only seven distinct factors.** Credibility
  and leadership both load on F1 (loadings 0.40–0.61); nothing separates them.
  They correlate at r = 0.76.
- **F8 is a method factor, not a culture factor.** All six reverse-worded items
  load on it at 0.43–0.49, while no normally worded item exceeds 0.23. It
  reflects question phrasing, not anything about the workplace. Detected
  automatically by `check_reverse_wording_method_factor`.

**This is reported as a failure of discriminant validity, not smoothed over.**
The eight constructs are internally reliable but they are not eight distinct
things. Practically, "credibility" and "leadership" should probably be one
construct.

## D10. Mean scores, not factor scores

- A mean is on the original 1–5 scale, so "3.8 on fairness" is directly
  interpretable and comparable across departments and future survey waves.
- Factor scores use sample-specific weights that change every time the survey is
  re-run, which makes year-on-year tracking meaningless.
- At alpha ≈ 0.87 the two correlate above 0.95, so little is lost.

---

## D11. Benjamini–Hochberg FDR, not Bonferroni

24 omnibus tests were run. At p < 0.05 each, roughly one false positive is
expected by chance.

- **Rejected: Bonferroni.** Controls the probability of *any* false positive.
  Very conservative; would hide real but modest group differences.
- **Rejected: no correction.** Indefensible with 24 tests.
- **Chosen: BH**, controlling the expected *proportion* of false findings at 5%.

Outcome: 4 of 24 survive correction — and those are the same 4 that reach even
a small effect size, which is reassuring.

## D12. Test choice is driven by Levene, not by preference

Levene's test rejected equal variances in 3 of 24 cases; those 3 used **Welch's
ANOVA**. The remaining 21 used classic one-way ANOVA. Kruskal–Wallis was
implemented as a fallback for cases that were both heteroscedastic and badly
non-normal, and no case triggered it.

**On normality:** at n ≈ 4,850 a normality test rejects on trivial deviations,
so `normaltest` p-values were recorded but not used as the decision rule.
Residual skew and kurtosis were used instead, and with large roughly balanced
groups the F test is robust to mild non-normality by the central limit theorem.

**⚠ SOFT SPOT.** Deciding which test to run based on a preliminary test of
assumptions is itself a two-stage procedure whose true error rate is not
exactly 5%. Some statisticians argue for simply always using Welch. That
critique is correct and the practical difference here is negligible — the
Welch and classic p-values agree in every case.

## D13. Effect sizes lead, p-values follow

**20 of 24 tests have eta squared below 0.01 (negligible).** The largest effect
in the entire ANOVA is wellbeing by location at eta squared = 0.032 — location
explains 3.2% of the variation in wellbeing. Real, worth acting on, and nowhere
near what "p < 0.0000000001" sounds like.

**Correction worth carrying into the interview.** An earlier draft of this log
said significance was "nearly automatic" at this sample size. That is the
textbook worry but it is not what happened here: only 4 of the 24 tests reach
p < 0.05, 19 have p > 0.10, and the median p-value is 0.61. The demographic
differences are genuinely near zero. The two measures agree in this data. What
p-values still cannot do is rank importance — they span 30 orders of magnitude
across these tests while every effect size sits below 0.035.

---

## D14. Multicollinearity: checked, reported, nothing removed

Highest VIF among the constructs is **2.98** (leadership), against conventional
thresholds of 5 (warning) and 10 (serious). No predictor was dropped.

The honest nuance: VIF being acceptable does **not** mean the constructs are
distinct. Credibility and leadership correlate at 0.76 and the factor analysis
could not separate them. The consequence is not biased coefficients — OLS is
still unbiased — but an unstable *ranking*. Alternatives considered:

- **Rejected: dropping one of the correlated pair.** Would inflate the survivor's
  coefficient with the dropped construct's variance and mislead more.
- **Rejected: ridge regression / PCA on the constructs.** Solves the instability
  by destroying the interpretability that is the entire point of a driver table.
- **Chosen: report three rankings side by side** — standardised beta, zero-order
  correlation, and ΔR² when the construct is removed — and let the disagreement
  between them be the finding.

**⚠ SOFT SPOT.** The three rankings do disagree. Leadership is 1st by beta but
2nd by unique contribution; fairness is the reverse. Do not claim leadership is
*the* top driver. Claim that leadership, fairness and pride form a top tier
clearly separated from camaraderie and wellbeing, and that within the top tier
the order is not resolvable with this data.

## D15. HC3 robust standard errors

Breusch–Pagan: LM = 127.7, p = 2.2e-15. Residual spread genuinely varies with
fitted values — expected with a bounded 1–5 outcome, because there is less room
to be wrong near the top of the scale than in the middle (visible as the
inverted-U in the scale-location plot).

HC3 changes no coefficient; it corrects the uncertainty around them. HC3 rather
than HC0 because it performs better in finite samples.

## D16. Standardised coefficients for constructs, raw for dummies

Constructs and the outcome are z-scored so the eight are comparable. Dummy
variables are deliberately *not* standardised — "a standard deviation of being
in Finance" is not a meaningful quantity.

## D17. Satisfaction is a separate 4-item scale, not one of the eight constructs

If the outcome were built from the same items as the predictors, the regression
would be partly predicting a variable from itself. Satisfaction uses four
dedicated items (alpha = 0.872).

**⚠ SOFT SPOT — this is the criticism most likely to land.** Predictors and
outcome still come from the same person, on the same form, at the same moment.
Someone in a bad mood marks everything down, which manufactures correlation
between predictor and outcome out of nothing. This is **common method bias**,
and it is visible in this data: the first eigenvalue of 23.85 is exactly what a
strong shared response tendency looks like. R² = 0.474 is therefore an
**upper bound** on the true relationship. The fix is a different outcome
source — retention records, absence data, manager ratings — which this design
does not have.

---

## D18. ROS: one predictor at a time on 24 units

Eight correlated constructs cannot go into a 24-row regression. A single
`culture_index` (mean of the eight) was used instead, plus log headcount as a
robustness check.

## D19. ICC computed before aggregating

ICC(2) is 0.96 for all eight constructs, so unit means are reliable — mostly
because each unit has around 200 respondents. Worth noting that ICC(1) is only
0.11: which unit you work in explains 11% of an *individual's* score. The unit
means are trustworthy; the units are not very different from each other.

## D20. The ROS result is reported as fragile, because it is

- r = 0.448 between culture index and ROS, 95% CI **0.055 to 0.721**. The
  interval spans "almost nothing" to "quite strong".
- **Removing one unit (BU17, Cook's distance 0.374) moves r from 0.448 to
  0.350 and p from 0.028 to 0.102** — from significant to not significant.
- All eight constructs correlate with ROS at 0.42–0.47. They are statistically
  indistinguishable, so this data cannot say *which* aspect of culture matters.

**⚠ SOFT SPOT — the weakest claim in the project.** With n = 24 this is a
hypothesis, not a result. Say so before you are asked. Ecological fallacy,
cross-sectional design, and reverse causality (profitable units can afford to
treat people well) all apply and none is addressed by the design.

---

## Things I was unsure about and would change with more time

1. **Multiple imputation** instead of available-item scoring, to test whether
   the MAR assumption is doing any work (D5).
2. **Confirmatory factor analysis** with fit indices (CFI, RMSEA, SRMR) rather
   than EFA, plus an explicit test of whether credibility and leadership are
   one factor or two. EFA describes; CFA tests (D9).
3. **A marker-variable or CFA method factor** to estimate how much of the
   correlation is common method bias rather than just noting it (D17).
4. **Cross-validation of R²**, since 0.474 is in-sample and will shrink out of
   sample — though with n = 4,846 and 26 predictors the shrinkage is small
   (adjusted R² = 0.471 says as much).
5. **A multilevel model** (respondents nested in business units) instead of
   ignoring clustering. ICC(1) = 0.11 means the standard errors in the
   individual-level regression are somewhat too small. This is a real
   omission — see the weakest-assumptions section of `EXPLAINER.md`.
