"""
Phase 3: build the 8 culture scores and check whether they actually work.

There are two different questions here and I kept mixing them up at first:
  - Reliability (Cronbach's alpha): do these 8 questions move together?
  - Validity (factor analysis): do they move together for the reason I think,
    or is it all just one big blob?
A set of questions can pass the first test and fail the second. That is exactly
what happens below, so I report both instead of only the flattering one.

Outputs: results/02_reliability_table.csv, 02_item_statistics.csv,
         02_factor_loadings.csv, data/processed/construct_scores_SYNTHETIC.parquet
"""

import numpy as np
import pandas as pd
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity

import config

# Standard psychometric rule of thumb: an item that correlates below 0.30 with
# the rest of its own scale is not measuring the same thing as its neighbours.
MIN_ITEM_TOTAL_CORRELATION = 0.30

# A respondent needs to have answered at least half of a construct's items
# before a mean score for that construct means anything.
MIN_ANSWERED_SHARE_FOR_SCORE = 0.50


def cronbach_alpha(item_scores):
    """
    Cronbach's alpha. I wrote it out by hand instead of calling a library so I
    could test it against an example I worked out on paper.

    alpha = k/(k-1) * (1 - sum of question variances / variance of the total)

    In plain words: if the questions all measure the same thing, the total
    score swings much more than any single question does, so the fraction gets
    small and alpha goes up towards 1. If the questions are unrelated, the
    total variance is just the sum of the parts, the fraction is 1, and alpha
    drops to 0.
    """
    complete = item_scores.dropna()
    n_items = complete.shape[1]
    if n_items < 2 or len(complete) < 3:
        return np.nan
    item_variances = complete.var(axis=0, ddof=1).sum()
    total_variance = complete.sum(axis=1).var(ddof=1)
    return (n_items / (n_items - 1)) * (1 - item_variances / total_variance)


def item_statistics(item_scores):
    """
    For each question: how well it correlates with the OTHER questions in its
    group, and what alpha would be if I dropped it.

    The correlation has to be against the sum of the other questions, not a
    total that includes the question itself. Correlating something with itself
    always looks good, so that would just be cheating.
    """
    complete = item_scores.dropna()
    rows = []
    for item in item_scores.columns:
        others = complete.drop(columns=[item])
        rows.append({
            "item": item,
            "n_used": len(complete),
            "mean": round(float(complete[item].mean()), 3),
            "sd": round(float(complete[item].std()), 3),
            "item_total_corr": round(float(complete[item].corr(others.sum(axis=1))), 3),
            "alpha_if_deleted": round(float(cronbach_alpha(others)), 3),
        })
    return pd.DataFrame(rows)


def review_construct(survey_responses, construct):
    """Run the reliability check for one construct and decide which items to keep."""
    items = config.construct_items(construct)
    statistics = item_statistics(survey_responses[items])
    alpha_before = cronbach_alpha(survey_responses[items])

    # An item is dropped only if it fails BOTH tests: it correlates weakly with
    # its own scale AND removing it actually improves alpha. Requiring both
    # stops us from chasing alpha upwards by deleting perfectly good items.
    weak = statistics["item_total_corr"] < MIN_ITEM_TOTAL_CORRELATION
    helps_to_remove = statistics["alpha_if_deleted"] > alpha_before
    dropped_items = statistics.loc[weak & helps_to_remove, "item"].tolist()
    retained_items = [item for item in items if item not in dropped_items]

    alpha_after = cronbach_alpha(survey_responses[retained_items])
    statistics.insert(0, "construct", construct)
    statistics["decision"] = np.where(statistics["item"].isin(dropped_items), "DROPPED", "kept")

    summary = {
        "construct": construct,
        "n_items_start": len(items),
        "n_items_retained": len(retained_items),
        "dropped_items": ", ".join(dropped_items) if dropped_items else "none",
        "alpha_before": round(float(alpha_before), 3),
        "alpha_after": round(float(alpha_after), 3),
        "mean_item_total_corr": round(
            float(statistics.loc[statistics["decision"] == "kept", "item_total_corr"].mean()), 3),
        "n_complete_cases_used": int(len(survey_responses[items].dropna())),
    }
    print(f"   {construct:14s} alpha {alpha_before:.3f} -> {alpha_after:.3f} "
          f"({len(retained_items)}/{len(items)} items kept)")
    return summary, statistics, retained_items


def impute_for_factor_analysis(survey_responses, item_columns):
    """
    Factor analysis will not run with blanks, so I fill each gap with that
    person's average on the other questions in the same group.

    Important: I only do this for the factor analysis. Alpha above is computed
    on complete cases only, because filling a blank using the person's own
    other answers would make the questions look more consistent with each other
    than they really are.
    """
    filled = survey_responses[item_columns].copy()
    for construct in config.CONSTRUCTS:
        construct_columns = [c for c in config.construct_items(construct) if c in item_columns]
        person_means = filled[construct_columns].mean(axis=1)
        for column in construct_columns:
            filled[column] = filled[column].fillna(person_means)
    return filled.fillna(filled.mean())


def run_factor_analysis(survey_responses, retained_by_construct):
    """
    Factor analysis: does the data actually agree with my 8-construct theory,
    or did I just impose that structure on it?

    I used oblimin rotation instead of varimax. Varimax forces the factors to
    be uncorrelated, and the culture constructs here obviously are correlated,
    so varimax would be answering a question I did not ask. Oblimin lets them
    correlate.
    """
    item_columns = [item for construct in config.CONSTRUCTS
                    for item in retained_by_construct[construct]]
    analysis_data = impute_for_factor_analysis(survey_responses, item_columns)

    # Sanity checks that factor analysis is even appropriate for this matrix.
    _, bartlett_p = calculate_bartlett_sphericity(analysis_data)
    _, kmo_overall = calculate_kmo(analysis_data)
    print(f"   KMO = {kmo_overall:.3f}, Bartlett p = {bartlett_p:.3g}")

    # How many factors does the DATA suggest, before theory is imposed?
    unrotated = FactorAnalyzer(n_factors=len(item_columns), rotation=None, method="principal")
    unrotated.fit(analysis_data)
    eigenvalues, _ = unrotated.get_eigenvalues()
    n_above_one = int((eigenvalues > 1).sum())
    print(f"   eigenvalues above 1: {n_above_one} (theory says {len(config.CONSTRUCTS)})")

    analyzer = FactorAnalyzer(n_factors=len(config.CONSTRUCTS), rotation="oblimin",
                              method="minres")
    analyzer.fit(analysis_data)
    loadings = pd.DataFrame(analyzer.loadings_, index=item_columns,
                            columns=[f"F{i + 1}" for i in range(len(config.CONSTRUCTS))])
    loadings.insert(0, "intended_construct",
                    [config.item_to_construct()[item] for item in item_columns])

    variance = analyzer.get_factor_variance()
    variance_table = pd.DataFrame({
        "factor": loadings.columns[1:],
        "ss_loadings": np.round(variance[0], 3),
        "prop_variance": np.round(variance[1], 3),
        "cumulative_variance": np.round(variance[2], 3),
    })
    return loadings, variance_table, eigenvalues, n_above_one, kmo_overall, bartlett_p


def check_structure_matches_theory(loadings):
    """
    For each item, find the factor it loads on most strongly and check whether
    the items of a construct agree with each other. If every construct's items
    pile onto the same factor, the eight constructs are not distinguishable.
    """
    factor_columns = [c for c in loadings.columns if c.startswith("F")]
    dominant = loadings[factor_columns].abs().idxmax(axis=1)
    rows = []
    for construct in config.CONSTRUCTS:
        mask = loadings["intended_construct"] == construct
        assignment = dominant[mask]
        top_factor = assignment.mode().iloc[0]
        rows.append({
            "construct": construct,
            "n_items": int(mask.sum()),
            "modal_factor": top_factor,
            "n_items_on_modal_factor": int((assignment == top_factor).sum()),
            "share_agreeing": round(float((assignment == top_factor).mean()), 2),
            "max_abs_loading": round(float(loadings.loc[mask, factor_columns].abs().max().max()), 3),
        })
    table = pd.DataFrame(rows)
    distinct_factors = table["modal_factor"].nunique()
    print(f"   the 8 constructs map onto {distinct_factors} distinct factors")
    return table, distinct_factors


def check_reverse_wording_method_factor(loadings):
    """
    Check whether one factor is made up of only the reverse-worded questions.

    If it is, that factor is about how the questions were written, not about
    the workplace. Some people do not fully notice the switch from "management
    is honest" to "management hides bad news", so the negative questions end up
    sharing something with each other purely because of the wording.

    Worth catching, because it makes it look like there are more factors than
    there really are, and it explains why those six questions have the weakest
    correlations with the rest of their group.
    """
    factor_columns = [c for c in loadings.columns if c.startswith("F")]
    reverse_present = [i for i in config.REVERSE_ITEMS if i in loadings.index]
    normal_items = loadings.index.difference(reverse_present)

    rows = []
    for factor in factor_columns:
        reverse_mean = loadings.loc[reverse_present, factor].abs().mean()
        normal_max = loadings.loc[normal_items, factor].abs().max()
        rows.append({
            "factor": factor,
            "mean_abs_loading_reverse_items": round(float(reverse_mean), 3),
            "max_abs_loading_normal_items": round(float(normal_max), 3),
            "is_reverse_wording_method_factor": bool(reverse_mean > 0.35
                                                     and reverse_mean > 2 * normal_max),
        })
    table = pd.DataFrame(rows)
    flagged = table.loc[table["is_reverse_wording_method_factor"], "factor"].tolist()
    if flagged:
        print(f"   METHOD FACTOR DETECTED on {', '.join(flagged)}: the reverse-worded "
              f"items form their own factor (mean loading "
              f"{table.loc[table['factor'] == flagged[0], 'mean_abs_loading_reverse_items'].iloc[0]:.2f} "
              f"vs {table.loc[table['factor'] == flagged[0], 'max_abs_loading_normal_items'].iloc[0]:.2f} "
              "for any normally worded item)")
    else:
        print("   no reverse-wording method factor detected")
    return table


def score_constructs(survey_responses, retained_by_construct):
    """
    A person's score for a construct is just the average of the questions they
    answered.

    I used averages rather than factor scores. An average stays on the original
    1-5 scale, so "3.8 on fairness" means something to a manager and can be
    compared with next year's survey. Factor scores use weights calculated from
    this particular sample, so they would change every time the survey is run
    and year-on-year comparison would stop making sense. When alpha is high the
    two approaches correlate above 0.95 anyway, so I lose very little.
    """
    construct_scores = survey_responses[["respondent_id"] + config.DEMOGRAPHIC_COLS].copy()
    for construct in config.CONSTRUCTS:
        items = retained_by_construct[construct]
        answered_share = survey_responses[items].notna().mean(axis=1)
        mean_score = survey_responses[items].mean(axis=1)
        construct_scores[construct] = mean_score.where(
            answered_share >= MIN_ANSWERED_SHARE_FOR_SCORE)

    satisfaction_items = sorted(config.SATISFACTION_ITEMS)
    answered_share = survey_responses[satisfaction_items].notna().mean(axis=1)
    construct_scores["satisfaction"] = survey_responses[satisfaction_items].mean(axis=1).where(
        answered_share >= MIN_ANSWERED_SHARE_FOR_SCORE)
    return construct_scores


def main():
    print("PHASE 3: reliability, factor structure and construct scores")
    config.ensure_dirs()
    survey_responses = pd.read_parquet(config.CLEAN_SURVEY_FILE)

    summaries, all_statistics, retained_by_construct = [], [], {}
    for construct in config.CONSTRUCTS:
        summary, statistics, retained = review_construct(survey_responses, construct)
        summaries.append(summary)
        all_statistics.append(statistics)
        retained_by_construct[construct] = retained

    # The outcome scale gets the same treatment - a shaky outcome would
    # undermine every regression that follows.
    satisfaction_items = sorted(config.SATISFACTION_ITEMS)
    summaries.append({
        "construct": "satisfaction (outcome)",
        "n_items_start": len(satisfaction_items),
        "n_items_retained": len(satisfaction_items),
        "dropped_items": "none",
        "alpha_before": round(float(cronbach_alpha(survey_responses[satisfaction_items])), 3),
        "alpha_after": round(float(cronbach_alpha(survey_responses[satisfaction_items])), 3),
        "mean_item_total_corr": round(float(
            item_statistics(survey_responses[satisfaction_items])["item_total_corr"].mean()), 3),
        "n_complete_cases_used": int(len(survey_responses[satisfaction_items].dropna())),
    })

    reliability_table = pd.DataFrame(summaries)
    reliability_table.insert(0, "data_label", config.DATA_LABEL)
    reliability_table.to_csv(config.RESULTS_DIR / "02_reliability_table.csv", index=False)
    pd.concat(all_statistics).to_csv(config.RESULTS_DIR / "02_item_statistics.csv", index=False)

    loadings, variance_table, eigenvalues, n_above_one, kmo, bartlett_p = run_factor_analysis(
        survey_responses, retained_by_construct)
    structure_table, distinct_factors = check_structure_matches_theory(loadings)
    method_factor_table = check_reverse_wording_method_factor(loadings)

    loadings.round(3).to_csv(config.RESULTS_DIR / "02_factor_loadings.csv", index_label="item")
    method_factor_table.to_csv(config.RESULTS_DIR / "02_method_factor_check.csv", index=False)
    variance_table.to_csv(config.RESULTS_DIR / "02_factor_variance.csv", index=False)
    structure_table.to_csv(config.RESULTS_DIR / "02_structure_check.csv", index=False)
    pd.DataFrame({"component": range(1, len(eigenvalues) + 1),
                  "eigenvalue": np.round(eigenvalues, 3)}).to_csv(
        config.RESULTS_DIR / "02_eigenvalues.csv", index=False)

    construct_scores = score_constructs(survey_responses, retained_by_construct)
    construct_scores.to_parquet(config.CONSTRUCT_SCORE_FILE, index=False)
    print(f"   scored {len(construct_scores)} respondents on "
          f"{len(config.CONSTRUCTS)} constructs + satisfaction")
    print("   construct building complete\n")

    return {"kmo": kmo, "bartlett_p": bartlett_p, "n_eigen_above_one": n_above_one,
            "distinct_factors": distinct_factors}


if __name__ == "__main__":
    main()
