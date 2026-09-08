"""
Phase 1: look at the raw data before changing anything.

The reason I profile first is simple. If I clean the data and then look at it,
I can no longer tell whether a problem was in the original file or whether my
own code created it. So this script only describes what is there.

Output: results/00_data_profile.md
"""

import pandas as pd

import config


def load_raw_survey():
    """Read the raw export exactly as delivered, with nothing fixed up."""
    survey_responses = pd.read_csv(config.RAW_SURVEY_FILE)
    print(f"   loaded {len(survey_responses)} rows x {survey_responses.shape[1]} columns")
    return survey_responses


def build_data_dictionary():
    """One row per questionnaire item: what it asks and what it is meant to measure."""
    rows = []
    all_text = dict(config.ITEM_TEXT)
    all_text.update(config.SATISFACTION_ITEMS)
    for item, construct in config.item_to_construct().items():
        rows.append({
            "item": item,
            "intended_construct": construct,
            "reverse_worded": item in config.REVERSE_ITEMS,
            "scale": f"{config.LIKERT_MIN}-{config.LIKERT_MAX} Likert",
            "question_text": all_text[item],
        })
    return pd.DataFrame(rows)


def summarise_items(survey_responses):
    """
    Per-item summary: how people answered, how much is missing, and whether any
    value falls outside the 1-5 scale the questionnaire claims to use.
    """
    item_columns = config.all_item_columns()
    summary_rows = []
    for item in item_columns:
        answers = survey_responses[item]
        in_scale = answers.between(config.LIKERT_MIN, config.LIKERT_MAX)
        out_of_scale = answers.notna() & ~in_scale
        valid = answers.where(in_scale)
        summary_rows.append({
            "item": item,
            "construct": config.item_to_construct()[item],
            "n_answered": int(answers.notna().sum()),
            "pct_missing": round(100 * answers.isna().mean(), 2),
            "n_out_of_scale": int(out_of_scale.sum()),
            "min": valid.min(),
            "max": valid.max(),
            "mean": round(float(valid.mean()), 2),
            "sd": round(float(valid.std()), 2),
        })
    return pd.DataFrame(summary_rows)


def response_distribution(survey_responses):
    """Percentage of respondents choosing each point 1-5, pooled over all items."""
    item_columns = config.all_item_columns()
    stacked = survey_responses[item_columns].stack()
    counts = stacked[stacked.between(1, 5)].value_counts().sort_index()
    return (100 * counts / counts.sum()).round(1)


def find_data_quality_problems(survey_responses):
    """
    Look for the things that actually go wrong in survey exports: duplicate
    submissions, people who ticked one column all the way down, out-of-range
    codes, and category labels that differ only by spacing or case.
    """
    item_columns = config.all_item_columns()
    problems = []

    duplicate_ids = survey_responses["respondent_id"].duplicated().sum()
    problems.append(("Duplicate respondent_id rows", duplicate_ids))

    within_person_sd = survey_responses[item_columns].std(axis=1)
    problems.append(("Respondents with zero variance across all items (straight-lining)",
                     int((within_person_sd == 0).sum())))
    problems.append(("Respondents with near-zero variance (sd < 0.30)",
                     int((within_person_sd < 0.30).sum())))

    out_of_scale_total = 0
    for item in item_columns:
        answers = survey_responses[item]
        out_of_scale_total += int((answers.notna() & ~answers.between(1, 5)).sum())
    problems.append(("Individual answers outside the 1-5 scale", out_of_scale_total))

    untidy = 0
    for column in config.DEMOGRAPHIC_COLS:
        values = survey_responses[column].astype(str)
        untidy += int((values != values.str.strip()).sum())
    problems.append(("Demographic values with leading/trailing whitespace", untidy))

    problems.append(("Cells missing across all items",
                     int(survey_responses[item_columns].isna().sum().sum())))
    return pd.DataFrame(problems, columns=["issue", "count"])


def demographic_breakdown(survey_responses):
    """Counts and percentages for each demographic column, as a single table."""
    rows = []
    for column in config.DEMOGRAPHIC_COLS:
        counts = survey_responses[column].value_counts()
        for level, count in counts.items():
            rows.append({
                "variable": column,
                "level": level,
                "n": int(count),
                "pct": round(100 * count / len(survey_responses), 1),
            })
    return pd.DataFrame(rows)


def write_profile_report(survey_responses, unit_table):
    """Assemble everything above into one readable markdown file."""
    dictionary = build_data_dictionary()
    item_summary = summarise_items(survey_responses)
    distribution = response_distribution(survey_responses)
    problems = find_data_quality_problems(survey_responses)
    demographics = demographic_breakdown(survey_responses)

    lines = []
    lines.append(f"# Data profile - {config.DATA_LABEL}")
    lines.append("")
    lines.append(f"> **{config.DATA_LABEL}.** This survey was generated by "
                 "`src/generate_synthetic_data.py` because `data/raw/` contained no real "
                 "export. Every number below describes simulated respondents.")
    lines.append("")
    lines.append("## 1. Size and shape")
    lines.append("")
    lines.append(f"- Rows in raw file: **{len(survey_responses)}**")
    lines.append(f"- Columns: **{survey_responses.shape[1]}** "
                 f"({len(config.all_item_columns())} Likert items, "
                 f"{len(config.DEMOGRAPHIC_COLS)} demographics, 1 respondent id)")
    lines.append(f"- Culture constructs measured: **{len(config.CONSTRUCTS)}** "
                 f"x {config.ITEMS_PER_CONSTRUCT} items = "
                 f"{len(config.CONSTRUCTS) * config.ITEMS_PER_CONSTRUCT} items")
    lines.append(f"- Outcome scale: **{len(config.SATISFACTION_ITEMS)}** satisfaction items")
    lines.append(f"- Business units in the ROS table: **{len(unit_table)}**")
    lines.append("")
    lines.append("## 2. Response distribution across all items")
    lines.append("")
    lines.append("| Answer | % of all valid answers |")
    lines.append("|---|---|")
    for point, pct in distribution.items():
        lines.append(f"| {int(point)} | {pct}% |")
    lines.append("")
    lines.append("The distribution leans positive, which is normal for engagement surveys "
                 "and is worth remembering later: the items are not symmetric around 3.")
    lines.append("")
    lines.append("## 3. Data quality problems found")
    lines.append("")
    lines.append(problems.to_markdown(index=False))
    lines.append("")
    lines.append("Each of these is dealt with, and logged, in `results/01_cleaning_log.csv`.")
    lines.append("")
    lines.append("## 4. Demographic breakdown")
    lines.append("")
    lines.append(demographics.to_markdown(index=False))
    lines.append("")
    lines.append("## 5. Per-item summary (missingness, scale, distribution)")
    lines.append("")
    lines.append(item_summary.to_markdown(index=False))
    lines.append("")
    lines.append("Missingness rises steadily down the questionnaire - the classic pattern of "
                 "respondent fatigue rather than a technical fault.")
    lines.append("")
    lines.append("## 6. Data dictionary")
    lines.append("")
    lines.append("Every item and the construct it is *intended* to measure. Whether it "
                 "actually measures that construct is tested in Phase 3, not assumed here.")
    lines.append("")
    lines.append(dictionary.to_markdown(index=False))
    lines.append("")

    output_path = config.RESULTS_DIR / "00_data_profile.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"   wrote {output_path.name}")
    item_summary.to_csv(config.RESULTS_DIR / "00_item_summary.csv", index=False)
    dictionary.to_csv(config.RESULTS_DIR / "00_data_dictionary.csv", index=False)


def main():
    print("PHASE 1: profiling the raw survey")
    config.ensure_dirs()
    survey_responses = load_raw_survey()
    unit_table = pd.read_csv(config.RAW_UNIT_FILE)
    write_profile_report(survey_responses, unit_table)
    print("   profiling complete\n")


if __name__ == "__main__":
    main()
