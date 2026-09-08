# Group differences (ANOVA) - SYNTHETIC DATA

> **SYNTHETIC DATA** - generated data, not real survey findings.

## How to read this

Every test below runs on about 4,850 respondents. At that sample size a test can detect a difference far too small to act on, so a p-value on its own does not tell you whether anything matters. **Read the eta squared column first.** It is the share of the variation in a construct explained by the grouping: 0.01 is small, 0.06 medium, 0.14 large.

24 omnibus tests were run, so p-values are corrected with Benjamini-Hochberg FDR at alpha = 0.05.

## Omnibus tests, ranked by effect size

| construct   | grouping    | test_used     |   eta_squared | effect_size_label   |   p_raw |   p_adjusted_bh | significant_after_correction   |
|:------------|:------------|:--------------|--------------:|:--------------------|--------:|----------------:|:-------------------------------|
| wellbeing   | location    | One-way ANOVA |        0.032  | small               | 0       |         0       | True                           |
| leadership  | location    | One-way ANOVA |        0.0145 | small               | 0       |         0       | True                           |
| pride       | tenure_band | One-way ANOVA |        0.0126 | small               | 0       |         0       | True                           |
| development | department  | Welch ANOVA   |        0.0121 | small               | 0       |         0       | True                           |
| credibility | department  | One-way ANOVA |        0.0021 | negligible          | 0.11488 |         0.39484 | False                          |
| development | location    | One-way ANOVA |        0.0019 | negligible          | 0.09764 |         0.39484 | False                          |
| respect     | location    | Welch ANOVA   |        0.0018 | negligible          | 0.11516 |         0.39484 | False                          |
| credibility | location    | One-way ANOVA |        0.0012 | negligible          | 0.34694 |         0.97699 | False                          |
| leadership  | department  | One-way ANOVA |        0.0011 | negligible          | 0.5019  |         0.97699 | False                          |
| pride       | location    | One-way ANOVA |        0.0011 | negligible          | 0.3938  |         0.97699 | False                          |
| pride       | department  | Welch ANOVA   |        0.0009 | negligible          | 0.63885 |         0.97699 | False                          |
| camaraderie | location    | One-way ANOVA |        0.0008 | negligible          | 0.58117 |         0.97699 | False                          |
| fairness    | department  | One-way ANOVA |        0.0008 | negligible          | 0.68443 |         0.97699 | False                          |
| camaraderie | department  | One-way ANOVA |        0.0007 | negligible          | 0.75097 |         0.97699 | False                          |
| wellbeing   | department  | One-way ANOVA |        0.0006 | negligible          | 0.82786 |         0.97699 | False                          |
| credibility | tenure_band | One-way ANOVA |        0.0006 | negligible          | 0.58033 |         0.97699 | False                          |
| wellbeing   | tenure_band | One-way ANOVA |        0.0005 | negligible          | 0.67893 |         0.97699 | False                          |
| fairness    | location    | One-way ANOVA |        0.0005 | negligible          | 0.78194 |         0.97699 | False                          |
| respect     | department  | One-way ANOVA |        0.0004 | negligible          | 0.90696 |         0.97699 | False                          |
| leadership  | tenure_band | One-way ANOVA |        0.0004 | negligible          | 0.78219 |         0.97699 | False                          |
| fairness    | tenure_band | One-way ANOVA |        0.0003 | negligible          | 0.82853 |         0.97699 | False                          |
| respect     | tenure_band | One-way ANOVA |        0.0002 | negligible          | 0.93628 |         0.97699 | False                          |
| camaraderie | tenure_band | One-way ANOVA |        0.0002 | negligible          | 0.91001 |         0.97699 | False                          |
| development | tenure_band | One-way ANOVA |        0.0001 | negligible          | 0.98285 |         0.98285 | False                          |

## What actually matters

- **wellbeing by location**: eta squared = 0.032 (small), One-way ANOVA, adjusted p = 7.56e-31.
- **leadership by location**: eta squared = 0.015 (small), One-way ANOVA, adjusted p = 9.24e-13.
- **pride by tenure_band**: eta squared = 0.013 (small), One-way ANOVA, adjusted p = 1.13e-11.
- **development by department**: eta squared = 0.012 (small), Welch ANOVA, adjusted p = 2.20e-10.

20 of 24 tests have a negligible effect size (eta squared < 0.01). Only 4 are statistically significant at p < 0.05, and they are the same 4 that reach even a small effect size, so here the two measures agree.

What the p-values still cannot tell you is how much anything matters. Across these tests they span roughly 30 orders of magnitude, while every effect size sits below 0.032. The largest difference found anywhere explains 3.2% of the variation in a construct - real, worth one targeted intervention, and nothing like as dramatic as a p-value of 1e-31 sounds.

## Tukey HSD post-hoc

37 of 61 pairwise comparisons are significant. The 15 largest mean differences:

| construct   | grouping    | group1      | group2       |   meandiff |   p-adj |   lower |   upper |
|:------------|:------------|:------------|:-------------|-----------:|--------:|--------:|--------:|
| wellbeing   | location    | Aarhus      | Chennai      |    -0.4414 |  0      | -0.5621 | -0.3207 |
| wellbeing   | location    | Chennai     | Pune         |     0.4041 |  0      |  0.2964 |  0.5118 |
| wellbeing   | location    | Chennai     | Hamburg      |     0.3038 |  0      |  0.1983 |  0.4094 |
| pride       | tenure_band | 3-5 years   | <1 year      |     0.2687 |  0      |  0.1541 |  0.3833 |
| leadership  | location    | Aarhus      | Chennai      |    -0.2657 |  0      | -0.3869 | -0.1446 |
| pride       | tenure_band | 5-10 years  | <1 year      |     0.2635 |  0      |  0.152  |  0.375  |
| development | department  | HR          | Operations   |    -0.2585 |  0.0001 | -0.4267 | -0.0904 |
| leadership  | location    | Chennai     | Pune         |     0.2543 |  0      |  0.1462 |  0.3624 |
| development | department  | HR          | Supply Chain |    -0.2503 |  0.0008 | -0.4299 | -0.0706 |
| wellbeing   | location    | Aarhus      | Remote       |    -0.2466 |  0      | -0.3742 | -0.119  |
| wellbeing   | location    | Chennai     | Rostock      |     0.2208 |  0      |  0.1006 |  0.3409 |
| wellbeing   | location    | Aarhus      | Rostock      |    -0.2206 |  0      | -0.3484 | -0.0929 |
| leadership  | location    | Aarhus      | Remote       |    -0.2127 |  0      | -0.3408 | -0.0846 |
| development | department  | Engineering | Operations   |    -0.2115 |  0      | -0.3164 | -0.1066 |
| wellbeing   | location    | Pune        | Remote       |    -0.2093 |  0      | -0.3246 | -0.0939 |

Mean differences are in Likert points on the original 1-5 scale, which makes them directly interpretable: a difference of 0.30 is under a third of one scale point.
