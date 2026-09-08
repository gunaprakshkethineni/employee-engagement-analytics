"""
Phase 6: is culture linked to Return on Sales at business unit level?

This is the weakest part of the project and I would rather say that up front
than have someone find it. Three things go wrong as soon as I average people
into unit scores:

  1. My sample drops from ~4,850 people to 24 units. You cannot establish much
     with 24 points.
  2. Ecological fallacy: a relationship between unit AVERAGES says nothing
     about individual people. Units with better average culture might be more
     profitable even if, inside every single unit, culture and performance are
     completely unrelated.
  3. It is just a correlation, measured at one point in time. Profitable units
     can afford to treat people better - that explanation fits my data just as
     well as the one I would prefer.

Before averaging anything I use ICC to check whether averaging is even a fair
thing to do. Outputs: results/05_ros_analysis.md, 05_unit_level_data.csv,
05_ros_correlations.csv, 05_icc_table.csv
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests

import config

# With 24 units, a regression can support roughly one or two predictors before
# it is fitting noise. The usual rule of thumb is 10-15 observations each.
MIN_OBSERVATIONS_PER_PREDICTOR = 10


def compute_icc(construct_scores, construct, group_column="business_unit"):
    """
    ICC (intraclass correlation): is a unit's average score actually meaningful?

    ICC(1) is how much of one person's score is explained by which unit they
    work in. ICC(2) is how reliable the unit AVERAGE is, and that is the one I
    care about here, because unit averages are what I correlate with ROS. If
    ICC(2) is below about 0.70 the averages are too noisy to trust.
    """
    usable = construct_scores[[construct, group_column]].dropna()
    groups = [g[construct].to_numpy() for _, g in usable.groupby(group_column)]
    n_groups = len(groups)
    grand_mean = usable[construct].mean()
    average_group_size = len(usable) / n_groups

    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_within = sum(((g - g.mean()) ** 2).sum() for g in groups)
    mean_square_between = ss_between / (n_groups - 1)
    mean_square_within = ss_within / (len(usable) - n_groups)

    icc1 = ((mean_square_between - mean_square_within)
            / (mean_square_between + (average_group_size - 1) * mean_square_within))
    icc2 = (mean_square_between - mean_square_within) / mean_square_between
    return {"construct": construct, "icc1": round(float(icc1), 4),
            "icc2": round(float(icc2), 4),
            "mean_group_size": round(average_group_size, 1),
            "aggregation_defensible": bool(icc2 >= 0.70)}


def aggregate_to_units(construct_scores, unit_table):
    """Average each construct within business unit and join the ROS figures on."""
    columns = config.CONSTRUCTS + ["satisfaction"]
    unit_means = construct_scores.groupby("business_unit")[columns].mean().reset_index()
    unit_means["n_respondents"] = construct_scores.groupby(
        "business_unit").size().to_numpy()

    # A single overall culture index. With 24 units there is no room to put
    # eight correlated predictors in one model, so they are collapsed into one.
    unit_means["culture_index"] = unit_means[config.CONSTRUCTS].mean(axis=1)
    merged = unit_means.merge(unit_table, on="business_unit", how="inner")
    print(f"   aggregated to {len(merged)} business units "
          f"(median {int(merged['n_respondents'].median())} respondents each)")
    return merged


def correlate_with_ros(unit_data):
    """
    Correlate each averaged construct with ROS, and give confidence intervals.

    The confidence intervals are the whole point of this table. With only 24
    units, a correlation of 0.45 has an interval running from about 0.05 to
    0.72. That means the result is consistent with "barely anything" and "quite
    strong" at the same time, which is worth being honest about.
    """
    rows = []
    for construct in config.CONSTRUCTS + ["culture_index", "satisfaction"]:
        r, p = stats.pearsonr(unit_data[construct], unit_data["return_on_sales_pct"])
        # Fisher z transform gives a symmetric interval for a correlation.
        n = len(unit_data)
        z = np.arctanh(r)
        margin = 1.96 / np.sqrt(n - 3)
        rows.append({"construct": construct, "n_units": n, "pearson_r": round(float(r), 3),
                     "r_ci_low": round(float(np.tanh(z - margin)), 3),
                     "r_ci_high": round(float(np.tanh(z + margin)), 3),
                     "p_raw": float(p)})
    table = pd.DataFrame(rows)
    _, p_adjusted, _, _ = multipletests(table["p_raw"], alpha=0.05, method="fdr_bh")
    table["p_adjusted_bh"] = p_adjusted
    table["significant_after_correction"] = table["p_adjusted_bh"] < 0.05
    return table.sort_values("pearson_r", ascending=False)


def add_unit_confidence_intervals(construct_scores, unit_data):
    """
    Work out how precisely each unit's culture score is measured.

    A unit mean is just an average of a few hundred people, so it has its own
    error bar: standard error = standard deviation / square root of how many
    people answered. Without this you end up ranking units by differences that
    are smaller than the noise, which is the whole trap I want to avoid.
    """
    per_person = construct_scores.copy()
    per_person["culture_index"] = per_person[config.CONSTRUCTS].mean(axis=1)
    spread = per_person.groupby("business_unit")["culture_index"].agg(["std", "count"])
    spread["standard_error"] = spread["std"] / np.sqrt(spread["count"])

    unit_data = unit_data.merge(
        spread[["std", "standard_error"]].rename(
            columns={"std": "culture_index_sd", "standard_error": "culture_index_se"}),
        on="business_unit", how="left")
    unit_data["culture_ci_low"] = (unit_data["culture_index"]
                                   - 1.96 * unit_data["culture_index_se"])
    unit_data["culture_ci_high"] = (unit_data["culture_index"]
                                    + 1.96 * unit_data["culture_index_se"])
    return unit_data


def leave_one_out_correlations(unit_data):
    """
    Drop each unit in turn and see what the culture-ROS correlation becomes.

    With 24 points I cannot just report one correlation and move on. If taking
    out a single unit moves the answer a long way, the answer was never really
    about culture - it was about that one unit. This gives me all 24 versions
    so I can show the spread rather than describe it.
    """
    full_r, _ = stats.pearsonr(unit_data["culture_index"],
                               unit_data["return_on_sales_pct"])
    rows = []
    for position in range(len(unit_data)):
        remaining = unit_data.drop(unit_data.index[position])
        r, p = stats.pearsonr(remaining["culture_index"],
                              remaining["return_on_sales_pct"])
        rows.append({
            "unit_removed": unit_data.iloc[position]["business_unit"],
            "r_without_unit": round(float(r), 4),
            "p_without_unit": float(p),
            "still_significant": bool(p < 0.05),
            "r_all_units": round(float(full_r), 4),
            "shift_from_full": round(float(r - full_r), 4),
        })
    return pd.DataFrame(rows).sort_values("r_without_unit").reset_index(drop=True)


def model_ros(unit_data):
    """
    Regress ROS on the culture index, then check whether unit size explains it
    away. Two models is the most 24 observations can honestly support.
    """
    outcome = unit_data["return_on_sales_pct"]
    simple = sm.OLS(outcome, sm.add_constant(unit_data[["culture_index"]])).fit()

    with_controls = unit_data[["culture_index"]].copy()
    with_controls["log_headcount"] = np.log(unit_data["n_respondents"])
    controlled = sm.OLS(outcome, sm.add_constant(with_controls)).fit()
    return simple, controlled


def influence_check(unit_data, simple_model):
    """
    With only 24 points, one odd unit can create the whole relationship, or
    wipe it out. So I find the most influential unit, take it out, and see how
    far the correlation moves.
    """
    influence = simple_model.get_influence()
    cooks_distance = influence.cooks_distance[0]
    worst_position = int(np.argmax(cooks_distance))
    worst_unit = unit_data.iloc[worst_position]["business_unit"]

    full_r, _ = stats.pearsonr(unit_data["culture_index"], unit_data["return_on_sales_pct"])
    without = unit_data.drop(unit_data.index[worst_position])
    reduced_r, reduced_p = stats.pearsonr(without["culture_index"],
                                          without["return_on_sales_pct"])
    return {"most_influential_unit": worst_unit,
            "max_cooks_distance": round(float(cooks_distance[worst_position]), 3),
            "r_all_units": round(float(full_r), 3),
            "r_without_that_unit": round(float(reduced_r), 3),
            "p_without_that_unit": float(reduced_p)}


def write_report(unit_data, icc_table, correlations, simple, controlled, influence):
    """Write the ROS findings with the caveats in the body, not in a footnote."""
    culture_r = correlations.loc[correlations["construct"] == "culture_index"].iloc[0]
    weakest_icc = icc_table["icc2"].min()

    lines = [f"# Culture and Return on Sales - {config.DATA_LABEL}", "",
             f"> **{config.DATA_LABEL}** - generated data. The ROS figures were simulated to "
             "be correlated with, but not determined by, unit culture.", "",
             "## Read this before the numbers", "",
             f"Everything in this section rests on **{len(unit_data)} business units**. That is "
             "the entire sample size for this phase. The individual-level analysis had ~4,850 "
             "observations; this has 24. Conclusions here are indicative at best and the "
             "confidence intervals below are wide enough to say so.", "",
             "Three specific limitations apply and none of them is fixable with this data:", "",
             "1. **Ecological fallacy.** These are relationships between unit AVERAGES. They "
             "do not license any statement about individual employees. A unit-level "
             "correlation can exist while the individual-level correlation inside every unit "
             "is zero, or even runs the other way (Simpson's paradox).",
             "2. **No causal claim is possible.** The data are cross-sectional and observational. "
             "'Better culture raises ROS' and 'profitable units can afford better conditions' "
             "predict this correlation equally well, and nothing here separates them. A "
             "credible causal design would need culture measured before the profit period, "
             "several waves, and unit fixed effects.",
             "3. **Common source.** Culture is self-reported by the same people whose unit is "
             "being scored, so shared mood or local reporting norms can move both.", "",
             "## 1. Is aggregating individuals into unit scores even legitimate?", "",
             "ICC(2) is the reliability of a unit mean. Below ~0.70 the unit averages are too "
             "noisy to correlate with anything.", "",
             icc_table.to_markdown(index=False), "",
             (f"Lowest ICC(2) is {weakest_icc:.2f}. " +
              ("All constructs clear the 0.70 bar, so aggregation is defensible - largely "
               "because each unit has ~200 respondents, which averages out a lot of individual "
               "noise." if weakest_icc >= 0.70 else
               "At least one construct falls below 0.70, so its unit means should be treated "
               "as unreliable and its ROS correlation discounted accordingly.")), "",
             "## 2. Correlations with ROS", "",
             correlations.round({"p_raw": 4, "p_adjusted_bh": 4}).to_markdown(index=False), "",
             "Note the width of every confidence interval. That width, not the point estimate, "
             "is the honest summary of what 24 units can tell you.", "",
             "## 3. Regression on the culture index", "",
             f"- ROS ~ culture index: R squared = **{simple.rsquared:.3f}**, "
             f"slope = {simple.params['culture_index']:.2f} ROS points per 1.0 Likert point, "
             f"p = {simple.pvalues['culture_index']:.4f}",
             f"- Adding log headcount as a control: R squared = **{controlled.rsquared:.3f}**, "
             f"culture slope = {controlled.params['culture_index']:.2f}, "
             f"p = {controlled.pvalues['culture_index']:.4f}", "",
             f"Only one predictor is used at a time because {len(unit_data)} observations "
             f"support roughly {len(unit_data) // MIN_OBSERVATIONS_PER_PREDICTOR} predictors. "
             "Putting all eight correlated constructs in a 24-row regression would produce "
             "confident-looking coefficients that are pure noise.", "",
             "## 4. Is it driven by one unit?", "",
             f"The most influential unit is **{influence['most_influential_unit']}** "
             f"(Cook's distance {influence['max_cooks_distance']}). Removing it moves the "
             f"culture-ROS correlation from **r = {influence['r_all_units']}** to "
             f"**r = {influence['r_without_that_unit']}** "
             f"(p = {influence['p_without_that_unit']:.4f}).", "",
             ("That is a large shift for a single data point, which is itself the finding: "
              "the relationship is not robust." if abs(influence['r_all_units'] -
                                                       influence['r_without_that_unit']) > 0.10
              else "The relationship survives removal of the most influential unit, which is "
                   "mildly reassuring but does not rescue it from the sample size."), "",
             "## 5. What can honestly be said", "",
             f"Units with better-rated culture tend to report higher ROS (r = "
             f"{culture_r['pearson_r']}, 95% CI {culture_r['r_ci_low']} to "
             f"{culture_r['r_ci_high']}). The direction is consistent with the literature. "
             "The magnitude is not established, the mechanism is not established, and the "
             "direction of causality is not established. This phase is a hypothesis worth "
             "testing properly, not a result.", ""]
    (config.RESULTS_DIR / "05_ros_analysis.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    print("PHASE 6: business unit ROS link")
    config.ensure_dirs()
    construct_scores = pd.read_parquet(config.CONSTRUCT_SCORE_FILE)
    unit_table = pd.read_csv(config.RAW_UNIT_FILE)

    icc_table = pd.DataFrame([compute_icc(construct_scores, c) for c in config.CONSTRUCTS])
    print(f"   ICC(2) range {icc_table['icc2'].min():.2f} to {icc_table['icc2'].max():.2f} "
          f"({'aggregation defensible' if icc_table['icc2'].min() >= 0.70 else 'CHECK: some unreliable'})")

    unit_data = aggregate_to_units(construct_scores, unit_table)
    unit_data = add_unit_confidence_intervals(construct_scores, unit_data)
    correlations = correlate_with_ros(unit_data)
    simple, controlled = model_ros(unit_data)
    influence = influence_check(unit_data, simple)
    print(f"   culture index vs ROS: r = "
          f"{correlations.loc[correlations['construct'] == 'culture_index', 'pearson_r'].iloc[0]:.3f}, "
          f"R2 = {simple.rsquared:.3f} on {len(unit_data)} units")
    print(f"   dropping the most influential unit moves r to {influence['r_without_that_unit']:.3f}")

    leave_one_out = leave_one_out_correlations(unit_data)
    still_significant = int(leave_one_out["still_significant"].sum())
    print(f"   leave-one-out: r ranges {leave_one_out['r_without_unit'].min():.3f} to "
          f"{leave_one_out['r_without_unit'].max():.3f}; significant in "
          f"{still_significant} of {len(leave_one_out)} versions")

    unit_data.insert(0, "data_label", config.DATA_LABEL)
    unit_data.to_csv(config.RESULTS_DIR / "05_unit_level_data.csv", index=False)
    correlations.to_csv(config.RESULTS_DIR / "05_ros_correlations.csv", index=False)
    icc_table.to_csv(config.RESULTS_DIR / "05_icc_table.csv", index=False)
    pd.DataFrame([influence]).to_csv(config.RESULTS_DIR / "05_influence_check.csv", index=False)
    leave_one_out.to_csv(config.RESULTS_DIR / "05_leave_one_out.csv", index=False)
    write_report(unit_data, icc_table, correlations, simple, controlled, influence)
    print("   ROS analysis complete\n")


if __name__ == "__main__":
    main()
