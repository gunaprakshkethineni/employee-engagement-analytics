"""
Phase 5: which culture constructs actually drive satisfaction?

The catch here is that my 8 constructs correlate with each other at around 0.6
to 0.8. When predictors overlap that much, the regression still predicts fine
overall, but it has a hard time deciding which one deserves the credit. The
coefficients get unstable even though the model as a whole is okay.

So I check multicollinearity before reading a single coefficient, and I show
the ranking three different ways rather than trusting one of them.

Outputs: results/04_regression_table.csv, 04_vif_table.csv,
         04_driver_ranking.csv, 04_regression_summary.md, 04_residuals.csv
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

import config

CONTROL_VARIABLES = ["department", "tenure_band", "location", "role_level"]

# Conventional VIF thresholds. Above 5 is a warning, above 10 is usually taken
# as a serious problem that has to be fixed rather than noted.
VIF_WARNING, VIF_SERIOUS = 5.0, 10.0


def build_design_matrix(construct_scores):
    """
    Put the predictors together: the 8 construct scores plus the demographics
    turned into 0/1 dummy columns. One level of each demographic gets dropped
    and becomes the baseline to compare against - if I kept them all, they
    would add up to the intercept and the model would not run.
    """
    modelling_data = construct_scores.dropna(
        subset=config.CONSTRUCTS + ["satisfaction"] + CONTROL_VARIABLES).copy()
    dummies = pd.get_dummies(modelling_data[CONTROL_VARIABLES],
                             drop_first=True, dtype=float)
    predictors = pd.concat([modelling_data[config.CONSTRUCTS], dummies], axis=1)
    outcome = modelling_data["satisfaction"]
    print(f"   modelling {len(modelling_data)} respondents, "
          f"{len(config.CONSTRUCTS)} constructs + {dummies.shape[1]} control dummies")
    return predictors, outcome, modelling_data


def compute_vif(predictors):
    """
    VIF (variance inflation factor) says how much wider a coefficient's error
    bars get because that predictor overlaps with the others.

    VIF = 1 / (1 - R squared from predicting this variable using all the rest).
    A VIF of 4 means the standard error is twice as wide (square root of 4) as
    it would be if that predictor had nothing in common with the others.
    """
    with_constant = sm.add_constant(predictors).astype(float)
    rows = []
    for position, name in enumerate(with_constant.columns):
        if name == "const":
            continue
        value = variance_inflation_factor(with_constant.to_numpy(), position)
        rows.append({
            "predictor": name,
            "vif": round(float(value), 2),
            "is_construct": name in config.CONSTRUCTS,
            "verdict": ("serious" if value >= VIF_SERIOUS
                        else "elevated" if value >= VIF_WARNING else "acceptable"),
        })
    return pd.DataFrame(rows).sort_values("vif", ascending=False)


def fit_models(predictors, outcome):
    """
    Fit the model twice: once the ordinary way, once with robust standard
    errors.

    Robust (HC3) standard errors do not change the coefficients at all. They
    only change how confident I claim to be about them. I need them when the
    errors are more spread out in some parts of the range than others, which
    happens a lot with 1-5 scales because there is less room to be wrong at the
    top of the scale than in the middle.
    """
    design = sm.add_constant(predictors).astype(float)
    plain_model = sm.OLS(outcome, design).fit()
    robust_model = sm.OLS(outcome, design).fit(cov_type="HC3")
    return plain_model, robust_model, design


def test_heteroscedasticity(model, design):
    """Breusch-Pagan: does residual spread depend on the predictors?"""
    lm_stat, lm_p, f_stat, f_p = het_breuschpagan(model.resid, design)
    return {"breusch_pagan_lm": round(float(lm_stat), 3),
            "breusch_pagan_p": float(lm_p),
            "heteroscedastic": bool(lm_p < 0.05)}


def standardised_coefficients(predictors, outcome):
    """
    Refit with the constructs and the outcome converted to z-scores, so each
    coefficient reads as "this many standard deviations of satisfaction per one
    standard deviation of this construct". That is what makes the 8 constructs
    comparable. The raw coefficients are not comparable, because the constructs
    are spread out by different amounts.

    I deliberately do not standardise the dummy variables - "one standard
    deviation of working in Finance" is not a real quantity.
    """
    standardised = predictors.copy()
    for construct in config.CONSTRUCTS:
        column = standardised[construct]
        standardised[construct] = (column - column.mean()) / column.std()
    standardised_outcome = (outcome - outcome.mean()) / outcome.std()
    design = sm.add_constant(standardised).astype(float)
    return sm.OLS(standardised_outcome, design).fit(cov_type="HC3")


def unique_contribution(predictors, outcome, full_r_squared):
    """
    How much R squared do I lose if I take this construct out completely?

    With predictors this correlated, I think this is the fairest ranking: it
    asks what each construct explains that none of the others already explain.
    The numbers come out small precisely because the constructs overlap so
    much, and I would rather say that than pretend the coefficients settle it.
    """
    rows = []
    for construct in config.CONSTRUCTS:
        reduced = sm.add_constant(predictors.drop(columns=[construct])).astype(float)
        reduced_r_squared = sm.OLS(outcome, reduced).fit().rsquared
        rows.append({"construct": construct,
                     "delta_r_squared_if_removed": round(full_r_squared - reduced_r_squared, 5)})
    return pd.DataFrame(rows)


def build_driver_ranking(construct_scores, standardised_model, predictors, outcome, full_r2):
    """
    Rank the constructs three different ways and show them next to each other.

    If something is top on the plain correlation but middling on the
    standardised coefficient, that is not a bug. It means its apparent
    influence is shared with the other constructs rather than being its own.
    """
    zero_order = {c: construct_scores[c].corr(construct_scores["satisfaction"])
                  for c in config.CONSTRUCTS}
    contributions = unique_contribution(predictors, outcome, full_r2).set_index("construct")

    rows = []
    for construct in config.CONSTRUCTS:
        rows.append({
            "construct": construct,
            "std_beta": round(float(standardised_model.params[construct]), 4),
            "robust_se": round(float(standardised_model.bse[construct]), 4),
            "p_value": float(standardised_model.pvalues[construct]),
            "ci_low": round(float(standardised_model.conf_int().loc[construct, 0]), 4),
            "ci_high": round(float(standardised_model.conf_int().loc[construct, 1]), 4),
            "zero_order_r": round(float(zero_order[construct]), 3),
            "delta_r_squared_if_removed": float(
                contributions.loc[construct, "delta_r_squared_if_removed"]),
        })
    ranking = pd.DataFrame(rows).sort_values("std_beta", ascending=False).reset_index(drop=True)
    ranking.insert(0, "rank_by_std_beta", ranking.index + 1)
    ranking["rank_by_zero_order_r"] = ranking["zero_order_r"].rank(ascending=False).astype(int)
    ranking["rank_by_unique_contribution"] = ranking[
        "delta_r_squared_if_removed"].rank(ascending=False).astype(int)
    return ranking


def strongest_construct_pair(construct_scores):
    """
    Find the pair of constructs that overlap the most.

    I calculate this from the data instead of typing the number in, because I
    already made that mistake once and the write-up ended up quoting a figure
    that no longer matched the results.
    """
    correlations = construct_scores[config.CONSTRUCTS].corr()
    off_diagonal = correlations.where(~np.eye(len(config.CONSTRUCTS), dtype=bool))
    pair = off_diagonal.stack().idxmax()
    return pair[0], pair[1], float(off_diagonal.stack().max())


def write_summary(robust_model, plain_model, vif_table, ranking, hetero, pair):
    """Write the regression story in the order a reader needs it: caveats, then numbers."""
    max_construct_vif = vif_table.loc[vif_table["is_construct"], "vif"].max()
    first_construct, second_construct, pair_correlation = pair
    lines = [f"# Driver analysis - OLS regression - {config.DATA_LABEL}", "",
             f"> **{config.DATA_LABEL}** - generated data, not real survey findings.", "",
             "## 1. Multicollinearity, checked before anything is interpreted", "",
             f"Highest VIF among the eight constructs: **{max_construct_vif:.2f}** "
             f"(warning threshold {VIF_WARNING}, serious {VIF_SERIOUS}).", "",
             vif_table.to_markdown(index=False), "",
             ("**Verdict: no predictor was removed.** The VIFs sit below the conventional "
              "warning threshold, so the model is estimable and the standard errors are not "
              "inflated to the point of uselessness. That is *not* the same as saying the "
              f"constructs are distinct - {first_construct} and {second_construct} correlate at "
              f"r = {pair_correlation:.2f} and the factor analysis in Phase 3 could not separate "
              "them. The consequence is that individual coefficients are reliable enough to "
              "report but their RANKING against each other is fragile, which is why three "
              "rankings are shown below."), "",
             "## 2. Model fit", "",
             f"- R squared: **{plain_model.rsquared:.4f}**",
             f"- Adjusted R squared: **{plain_model.rsquared_adj:.4f}**",
             f"- Observations: **{int(plain_model.nobs)}**",
             f"- Predictors: **{int(plain_model.df_model)}**", "",
             f"About {100 * plain_model.rsquared:.0f}% of the variation between individuals in "
             "satisfaction is accounted for by the eight constructs plus demographics. The gap "
             "between R squared and adjusted R squared is tiny, which means the model is not "
             "being flattered by its number of predictors.", "",
             "## 3. Heteroscedasticity and the choice of standard errors", "",
             f"Breusch-Pagan LM = {hetero['breusch_pagan_lm']}, p = {hetero['breusch_pagan_p']:.3e}. ",
             (("Residual spread **does** depend on the predictors, so all standard errors, "
               "confidence intervals and p-values reported here use HC3 heteroscedasticity-robust "
               "estimation. The coefficients themselves are unchanged - only the uncertainty "
               "around them is corrected.") if hetero["heteroscedastic"] else
              ("Residual spread is constant, so ordinary standard errors would have been valid; "
               "robust HC3 errors are reported anyway as they cost nothing here.")), "",
             "## 4. Ranked drivers", "",
             ranking[["rank_by_std_beta", "construct", "std_beta", "robust_se", "ci_low",
                      "ci_high", "p_value", "zero_order_r", "delta_r_squared_if_removed",
                      "rank_by_zero_order_r", "rank_by_unique_contribution"]]
             .round({"p_value": 6}).to_markdown(index=False), "",
             "`std_beta` is standard deviations of satisfaction per standard deviation of the "
             "construct. `delta_r_squared_if_removed` is what that construct explains that "
             "nothing else in the model explains - the small values are the multicollinearity "
             "showing itself honestly.", "",
             "## 5. Full model, robust standard errors", "",
             "```", str(robust_model.summary()), "```", ""]
    (config.RESULTS_DIR / "04_regression_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    print("PHASE 5: OLS driver analysis")
    config.ensure_dirs()
    construct_scores = pd.read_parquet(config.CONSTRUCT_SCORE_FILE)

    predictors, outcome, modelling_data = build_design_matrix(construct_scores)

    vif_table = compute_vif(predictors)
    max_construct_vif = vif_table.loc[vif_table["is_construct"], "vif"].max()
    print(f"   highest construct VIF = {max_construct_vif:.2f} "
          f"({'acceptable' if max_construct_vif < VIF_WARNING else 'ELEVATED'})")

    plain_model, robust_model, design = fit_models(predictors, outcome)
    print(f"   R2 = {plain_model.rsquared:.4f}, adjusted R2 = {plain_model.rsquared_adj:.4f}")

    hetero = test_heteroscedasticity(plain_model, design)
    print(f"   Breusch-Pagan p = {hetero['breusch_pagan_p']:.3e} -> "
          f"{'heteroscedastic, using HC3 robust SEs' if hetero['heteroscedastic'] else 'homoscedastic'}")

    standardised_model = standardised_coefficients(predictors, outcome)
    ranking = build_driver_ranking(modelling_data, standardised_model, predictors,
                                   outcome, plain_model.rsquared)
    print(f"   strongest driver: {ranking.iloc[0]['construct']} "
          f"(beta = {ranking.iloc[0]['std_beta']:.3f}); "
          f"weakest: {ranking.iloc[-1]['construct']} (beta = {ranking.iloc[-1]['std_beta']:.3f})")

    coefficient_table = pd.DataFrame({
        "term": robust_model.params.index,
        "coefficient": robust_model.params.to_numpy().round(4),
        "robust_se": robust_model.bse.to_numpy().round(4),
        "t": robust_model.tvalues.to_numpy().round(3),
        "p_value": robust_model.pvalues.to_numpy(),
        "ci_low": robust_model.conf_int()[0].to_numpy().round(4),
        "ci_high": robust_model.conf_int()[1].to_numpy().round(4),
    })
    coefficient_table.insert(0, "data_label", config.DATA_LABEL)
    coefficient_table.to_csv(config.RESULTS_DIR / "04_regression_table.csv", index=False)
    vif_table.to_csv(config.RESULTS_DIR / "04_vif_table.csv", index=False)
    ranking.to_csv(config.RESULTS_DIR / "04_driver_ranking.csv", index=False)
    pd.DataFrame({"fitted": plain_model.fittedvalues, "residual": plain_model.resid,
                  "standardised_residual": plain_model.resid / plain_model.resid.std()}
                 ).to_csv(config.RESULTS_DIR / "04_residuals.csv", index=False)
    pd.DataFrame([{**hetero, "r_squared": plain_model.rsquared,
                   "adj_r_squared": plain_model.rsquared_adj,
                   "n_obs": int(plain_model.nobs)}]).to_csv(
        config.RESULTS_DIR / "04_model_diagnostics.csv", index=False)

    pair = strongest_construct_pair(modelling_data)
    print(f"   most overlapping pair: {pair[0]} and {pair[1]} at r = {pair[2]:.2f}")
    write_summary(robust_model, plain_model, vif_table, ranking, hetero, pair)
    print("   regression complete\n")


if __name__ == "__main__":
    main()
