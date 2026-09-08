# Driver analysis - OLS regression - SYNTHETIC DATA

> **SYNTHETIC DATA** - generated data, not real survey findings.

## 1. Multicollinearity, checked before anything is interpreted

Highest VIF among the eight constructs: **2.98** (warning threshold 5.0, serious 10.0).

| predictor                 |   vif | is_construct   | verdict    |
|:--------------------------|------:|:---------------|:-----------|
| leadership                |  2.98 | True           | acceptable |
| credibility               |  2.92 | True           | acceptable |
| wellbeing                 |  2.48 | True           | acceptable |
| fairness                  |  2.47 | True           | acceptable |
| pride                     |  2.45 | True           | acceptable |
| camaraderie               |  2.41 | True           | acceptable |
| development               |  2.41 | True           | acceptable |
| respect                   |  2.3  | True           | acceptable |
| location_Hamburg          |  2.12 | False          | acceptable |
| location_Pune             |  2.05 | False          | acceptable |
| location_Chennai          |  2.04 | False          | acceptable |
| location_Remote           |  1.78 | False          | acceptable |
| location_Rostock          |  1.78 | False          | acceptable |
| tenure_band_5-10 years    |  1.53 | False          | acceptable |
| tenure_band_3-5 years     |  1.49 | False          | acceptable |
| department_Operations     |  1.47 | False          | acceptable |
| tenure_band_10+ years     |  1.43 | False          | acceptable |
| department_Service        |  1.38 | False          | acceptable |
| tenure_band_<1 year       |  1.36 | False          | acceptable |
| department_Supply Chain   |  1.32 | False          | acceptable |
| department_Sales          |  1.3  | False          | acceptable |
| department_Finance        |  1.18 | False          | acceptable |
| department_HR             |  1.16 | False          | acceptable |
| role_level_Manager        |  1.07 | False          | acceptable |
| role_level_Team lead      |  1.07 | False          | acceptable |
| role_level_Senior manager |  1.04 | False          | acceptable |

**Verdict: no predictor was removed.** The VIFs sit below the conventional warning threshold, so the model is estimable and the standard errors are not inflated to the point of uselessness. That is *not* the same as saying the constructs are distinct - credibility and leadership correlate at r = 0.76 and the factor analysis in Phase 3 could not separate them. The consequence is that individual coefficients are reliable enough to report but their RANKING against each other is fragile, which is why three rankings are shown below.

## 2. Model fit

- R squared: **0.4741**
- Adjusted R squared: **0.4712**
- Observations: **4846**
- Predictors: **26**

About 47% of the variation between individuals in satisfaction is accounted for by the eight constructs plus demographics. The gap between R squared and adjusted R squared is tiny, which means the model is not being flattered by its number of predictors.

## 3. Heteroscedasticity and the choice of standard errors

Breusch-Pagan LM = 127.671, p = 2.216e-15. 
Residual spread **does** depend on the predictors, so all standard errors, confidence intervals and p-values reported here use HC3 heteroscedasticity-robust estimation. The coefficients themselves are unchanged - only the uncertainty around them is corrected.

## 4. Ranked drivers

|   rank_by_std_beta | construct   |   std_beta |   robust_se |   ci_low |   ci_high |   p_value |   zero_order_r |   delta_r_squared_if_removed |   rank_by_zero_order_r |   rank_by_unique_contribution |
|-------------------:|:------------|-----------:|------------:|---------:|----------:|----------:|---------------:|-----------------------------:|-----------------------:|------------------------------:|
|                  1 | leadership  |     0.183  |      0.0188 |   0.1462 |    0.2197 |  0        |          0.591 |                      0.01124 |                      1 |                             2 |
|                  2 | fairness    |     0.1724 |      0.0171 |   0.1389 |    0.2059 |  0        |          0.585 |                      0.01203 |                      2 |                             1 |
|                  3 | pride       |     0.1453 |      0.0166 |   0.1128 |    0.1778 |  0        |          0.572 |                      0.00862 |                      3 |                             3 |
|                  4 | credibility |     0.0929 |      0.0182 |   0.0573 |    0.1285 |  0        |          0.572 |                      0.00295 |                      3 |                             5 |
|                  5 | respect     |     0.0872 |      0.0165 |   0.0547 |    0.1196 |  0        |          0.541 |                      0.0033  |                      5 |                             4 |
|                  6 | development |     0.0586 |      0.0168 |   0.0258 |    0.0915 |  0.00047  |          0.535 |                      0.00142 |                      6 |                             6 |
|                  7 | wellbeing   |     0.0478 |      0.0171 |   0.0143 |    0.0814 |  0.005174 |          0.531 |                      0.00092 |                      8 |                             7 |
|                  8 | camaraderie |     0.0385 |      0.0166 |   0.006  |    0.071  |  0.0204   |          0.534 |                      0.00061 |                      7 |                             8 |

`std_beta` is standard deviations of satisfaction per standard deviation of the construct. `delta_r_squared_if_removed` is what that construct explains that nothing else in the model explains - the small values are the multicollinearity showing itself honestly.

## 5. Full model, robust standard errors

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:           satisfaction   R-squared:                       0.474
Model:                            OLS   Adj. R-squared:                  0.471
Method:                 Least Squares   F-statistic:                     184.8
Date:                Mon, 07 Sep 2026   Prob (F-statistic):               0.00
Time:                        11:41:16   Log-Likelihood:                -4995.9
No. Observations:                4846   AIC:                         1.005e+04
Df Residuals:                    4819   BIC:                         1.022e+04
Df Model:                          26                                         
Covariance Type:                  HC3                                         
=============================================================================================
                                coef    std err          z      P>|z|      [0.025      0.975]
---------------------------------------------------------------------------------------------
const                         0.2262      0.065      3.454      0.001       0.098       0.355
credibility                   0.1099      0.021      5.112      0.000       0.068       0.152
respect                       0.1063      0.020      5.270      0.000       0.067       0.146
fairness                      0.1986      0.020     10.077      0.000       0.160       0.237
pride                         0.1621      0.018      8.766      0.000       0.126       0.198
camaraderie                   0.0445      0.019      2.319      0.020       0.007       0.082
leadership                    0.2111      0.022      9.752      0.000       0.169       0.253
development                   0.0645      0.018      3.497      0.000       0.028       0.101
wellbeing                     0.0549      0.020      2.796      0.005       0.016       0.093
department_Finance            0.0201      0.043      0.471      0.638      -0.064       0.104
department_HR                -0.0643      0.047     -1.368      0.171      -0.156       0.028
department_Operations         0.0343      0.029      1.182      0.237      -0.023       0.091
department_Sales             -0.0431      0.036     -1.213      0.225      -0.113       0.027
department_Service            0.0105      0.031      0.342      0.733      -0.050       0.071
department_Supply Chain       0.0475      0.034      1.417      0.157      -0.018       0.113
tenure_band_10+ years         0.0248      0.031      0.799      0.424      -0.036       0.086
tenure_band_3-5 years         0.0174      0.030      0.585      0.558      -0.041       0.076
tenure_band_5-10 years        0.0162      0.028      0.573      0.567      -0.039       0.072
tenure_band_<1 year           0.0229      0.034      0.675      0.500      -0.044       0.089
location_Chennai              0.0408      0.037      1.115      0.265      -0.031       0.113
location_Hamburg              0.0419      0.034      1.237      0.216      -0.025       0.108
location_Pune                -0.0080      0.034     -0.232      0.817      -0.076       0.060
location_Remote               0.0196      0.038      0.514      0.607      -0.055       0.094
location_Rostock             -0.0190      0.038     -0.501      0.616      -0.093       0.055
role_level_Manager            0.1121      0.029      3.836      0.000       0.055       0.169
role_level_Senior manager     0.2095      0.049      4.269      0.000       0.113       0.306
role_level_Team lead          0.0430      0.025      1.747      0.081      -0.005       0.091
==============================================================================
Omnibus:                       45.143   Durbin-Watson:                   1.940
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               46.294
Skew:                          -0.239   Prob(JB):                     8.86e-11
Kurtosis:                       2.973   Cond. No.                         82.6
==============================================================================

Notes:
[1] Standard Errors are heteroscedasticity robust (HC3)
```
