# Culture and Return on Sales - SYNTHETIC DATA

> **SYNTHETIC DATA** - generated data. The ROS figures were simulated to be correlated with, but not determined by, unit culture.

## Read this before the numbers

Everything in this section rests on **24 business units**. That is the entire sample size for this phase. The individual-level analysis had ~4,850 observations; this has 24. Conclusions here are indicative at best and the confidence intervals below are wide enough to say so.

Three specific limitations apply and none of them is fixable with this data:

1. **Ecological fallacy.** These are relationships between unit AVERAGES. They do not license any statement about individual employees. A unit-level correlation can exist while the individual-level correlation inside every unit is zero, or even runs the other way (Simpson's paradox).
2. **No causal claim is possible.** The data are cross-sectional and observational. 'Better culture raises ROS' and 'profitable units can afford better conditions' predict this correlation equally well, and nothing here separates them. A credible causal design would need culture measured before the profit period, several waves, and unit fixed effects.
3. **Common source.** Culture is self-reported by the same people whose unit is being scored, so shared mood or local reporting norms can move both.

## 1. Is aggregating individuals into unit scores even legitimate?

ICC(2) is the reliability of a unit mean. Below ~0.70 the unit averages are too noisy to correlate with anything.

| construct   |   icc1 |   icc2 |   mean_group_size | aggregation_defensible   |
|:------------|-------:|-------:|------------------:|:-------------------------|
| credibility | 0.1127 | 0.9625 |             202.1 | True                     |
| respect     | 0.11   | 0.9615 |             202.1 | True                     |
| fairness    | 0.1172 | 0.9641 |             202.1 | True                     |
| pride       | 0.1076 | 0.9606 |             202.1 | True                     |
| camaraderie | 0.1064 | 0.9601 |             202.1 | True                     |
| leadership  | 0.1147 | 0.9632 |             202.1 | True                     |
| development | 0.1115 | 0.9621 |             202.1 | True                     |
| wellbeing   | 0.1136 | 0.9628 |             202.1 | True                     |

Lowest ICC(2) is 0.96. All constructs clear the 0.70 bar, so aggregation is defensible - largely because each unit has ~200 respondents, which averages out a lot of individual noise.

## 2. Correlations with ROS

| construct     |   n_units |   pearson_r |   r_ci_low |   r_ci_high |   p_raw |   p_adjusted_bh | significant_after_correction   |
|:--------------|----------:|------------:|-----------:|------------:|--------:|----------------:|:-------------------------------|
| camaraderie   |        24 |       0.469 |      0.081 |       0.734 |  0.0208 |          0.0439 | True                           |
| fairness      |        24 |       0.465 |      0.076 |       0.731 |  0.0219 |          0.0439 | True                           |
| respect       |        24 |       0.455 |      0.063 |       0.725 |  0.0254 |          0.0439 | True                           |
| culture_index |        24 |       0.448 |      0.055 |       0.721 |  0.0281 |          0.0439 | True                           |
| leadership    |        24 |       0.445 |      0.05  |       0.719 |  0.0295 |          0.0439 | True                           |
| credibility   |        24 |       0.441 |      0.046 |       0.717 |  0.031  |          0.0439 | True                           |
| pride         |        24 |       0.434 |      0.037 |       0.713 |  0.034  |          0.0439 | True                           |
| development   |        24 |       0.427 |      0.029 |       0.708 |  0.0374 |          0.0439 | True                           |
| wellbeing     |        24 |       0.423 |      0.023 |       0.706 |  0.0395 |          0.0439 | True                           |
| satisfaction  |        24 |       0.381 |     -0.026 |       0.68  |  0.0662 |          0.0662 | False                          |

Note the width of every confidence interval. That width, not the point estimate, is the honest summary of what 24 units can tell you.

## 3. Regression on the culture index

- ROS ~ culture index: R squared = **0.201**, slope = 3.16 ROS points per 1.0 Likert point, p = 0.0281
- Adding log headcount as a control: R squared = **0.216**, culture slope = 3.22, p = 0.0284

Only one predictor is used at a time because 24 observations support roughly 2 predictors. Putting all eight correlated constructs in a 24-row regression would produce confident-looking coefficients that are pure noise.

## 4. Is it driven by one unit?

The most influential unit is **BU17** (Cook's distance 0.374). Removing it moves the culture-ROS correlation from **r = 0.448** to **r = 0.35** (p = 0.1018).

The relationship survives removal of the most influential unit, which is mildly reassuring but does not rescue it from the sample size.

## 5. What can honestly be said

Units with better-rated culture tend to report higher ROS (r = 0.448, 95% CI 0.055 to 0.721). The direction is consistent with the literature. The magnitude is not established, the mechanism is not established, and the direction of causality is not established. This phase is a hypothesis worth testing properly, not a result.
