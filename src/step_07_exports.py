"""
Phase 7b - flat exports for Power BI, and the synthetic-data guarantee.

Power BI wants one row per observation, no merged headers and no multi-level
indexes. Three files are written: a wide respondent table for detail, a long
table so 'construct' can be used as a slicer rather than eight separate
measures, and the business unit summary.

Outputs: results/powerbi_*.csv
"""

import pandas as pd

import config


def export_for_power_bi(construct_scores, unit_data):
    """Write the three flat tables."""
    unit_columns = ["business_unit", "return_on_sales_pct", "region",
                    "revenue_musd", "headcount"]
    respondent_level = construct_scores.merge(unit_data[unit_columns],
                                              on="business_unit", how="left")
    respondent_level.insert(0, "data_label", config.DATA_LABEL)
    respondent_level.to_csv(config.RESULTS_DIR / "powerbi_respondent_scores.csv", index=False)

    long_format = construct_scores.melt(
        id_vars=["respondent_id"] + config.DEMOGRAPHIC_COLS,
        value_vars=config.CONSTRUCTS + ["satisfaction"],
        var_name="construct", value_name="score").dropna(subset=["score"])
    long_format.insert(0, "data_label", config.DATA_LABEL)
    long_format.to_csv(config.RESULTS_DIR / "powerbi_construct_scores_long.csv", index=False)

    unit_data.to_csv(config.RESULTS_DIR / "powerbi_unit_summary.csv", index=False)

    print(f"   Power BI exports: {len(respondent_level)} respondent rows, "
          f"{len(long_format)} long rows, {len(unit_data)} unit rows")


def stamp_synthetic_marker_on_every_table():
    """
    Make sure every exported table says it is synthetic data.

    Most tables already get a data_label column when they are written, but if
    someone pulls a single CSV out of results/ and drops it into a slide, it
    would have no warning on it at all. So this goes through the folder and
    adds the column to anything that is missing it.
    """
    stamped = 0
    for path in sorted(config.RESULTS_DIR.glob("*.csv")):
        table = pd.read_csv(path)
        if "data_label" in table.columns:
            continue
        table.insert(0, "data_label", config.DATA_LABEL)
        table.to_csv(path, index=False)
        stamped += 1
    total = len(list(config.RESULTS_DIR.glob("*.csv")))
    print(f"   stamped '{config.DATA_LABEL}' onto {stamped} further tables "
          f"({total} CSVs now all marked)")


def main():
    print("PHASE 7b: Power BI exports")
    config.ensure_dirs()
    construct_scores = pd.read_parquet(config.CONSTRUCT_SCORE_FILE)
    unit_data = pd.read_csv(config.RESULTS_DIR / "05_unit_level_data.csv")

    export_for_power_bi(construct_scores, unit_data)
    stamp_synthetic_marker_on_every_table()
    print("   exports complete\n")


if __name__ == "__main__":
    main()
