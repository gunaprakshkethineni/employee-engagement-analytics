"""
Phase 2: clean the data and write down every change I make.

The order of these steps matters and it is easy to get wrong. I have to find
the straight-liners BEFORE reverse-coding, not after. Someone who ticks 4 for
all 68 questions has zero variance in the raw file, so they stand out. But if I
flip the six reverse questions first, their 4s turn into 2s, they suddenly look
like they varied their answers, and they slip past the filter.

Output: data/processed/survey_clean_SYNTHETIC.parquet, results/01_cleaning_log.csv
"""

import numpy as np
import pandas as pd

import config

# A respondent whose answers barely vary across 68 questions is not answering
# the questions. 0.30 is roughly "used at most two adjacent scale points".
STRAIGHT_LINE_SD_THRESHOLD = 0.30

# Someone who skipped more than a third of the questionnaire cannot be scored
# reliably on eight constructs, so they are removed rather than patched up.
MAX_MISSING_SHARE_PER_PERSON = 0.30


def reverse_code(answers, scale_min=config.LIKERT_MIN, scale_max=config.LIKERT_MAX):
    """
    Flip a negatively worded question so high always means good.

    On a 1-5 scale the flip is (1 + 5) - answer, so 1 becomes 5 and 4 becomes 2.
    If I skip this, a question like "management hides bad news" correlates the
    wrong way with the rest of its group and drags Cronbach's alpha down.
    """
    return (scale_min + scale_max) - answers


def log_step(cleaning_log, step_name, affected, unit, rows_remaining, total_reference, note):
    """Append one row to the cleaning log so every change is traceable."""
    cleaning_log.append({
        "step": step_name,
        "affected": affected,
        "unit": unit,
        "pct_affected": round(100 * affected / total_reference, 2) if total_reference else 0.0,
        "rows_remaining": rows_remaining,
        "note": note,
    })
    print(f"   {step_name}: {affected} {unit} affected, {rows_remaining} rows remaining")


def drop_duplicate_submissions(survey_responses, cleaning_log):
    """Someone hitting submit twice creates identical rows; keep the first."""
    before = len(survey_responses)
    survey_responses = survey_responses.drop_duplicates(subset="respondent_id", keep="first")
    removed = before - len(survey_responses)
    log_step(cleaning_log, "Drop duplicate respondent_id rows", removed, "rows",
             len(survey_responses), before,
             "Identical resubmissions; keeping the first occurrence.")
    return survey_responses.reset_index(drop=True)


def tidy_demographic_text(survey_responses, cleaning_log):
    """Strip stray whitespace and fix casing so 'OPERATIONS' and 'Operations' merge."""
    canonical = {}
    for column in config.DEMOGRAPHIC_COLS:
        for value in survey_responses[column].dropna().unique():
            canonical.setdefault(column, {})[str(value).strip().upper()] = None

    changed = 0
    for column in config.DEMOGRAPHIC_COLS:
        original = survey_responses[column].astype(str)
        # Map every variant back to the most common spelling of that label.
        stripped = original.str.strip()
        lookup = (stripped.groupby(stripped.str.upper()).agg(lambda s: s.mode().iloc[0]))
        cleaned = stripped.str.upper().map(lookup)
        changed += int((cleaned != original).sum())
        survey_responses[column] = cleaned

    log_step(cleaning_log, "Standardise demographic category text", changed, "cells",
             len(survey_responses), len(survey_responses),
             "Whitespace and upper-case variants collapsed onto the majority spelling.")
    return survey_responses


def blank_out_of_scale_answers(survey_responses, cleaning_log):
    """
    Any answer outside 1-5 is not a real response - it is a broken export or a
    'prefer not to say' code that leaked through. Treating a 99 as a number
    would wreck every mean, so these become missing rather than being kept.
    """
    item_columns = config.all_item_columns()
    values = survey_responses[item_columns]
    in_scale = values.ge(config.LIKERT_MIN) & values.le(config.LIKERT_MAX)
    out_of_scale = values.notna() & ~in_scale
    affected = int(out_of_scale.sum().sum())

    survey_responses[item_columns] = values.where(in_scale)
    offenders = out_of_scale.sum()
    offenders = offenders[offenders > 0].to_dict()
    log_step(cleaning_log, "Set out-of-scale answers to missing", affected, "values",
             len(survey_responses), values.size,
             f"Values outside 1-5 found in: {offenders}. Recoded to missing, not to a number.")
    return survey_responses


def flag_and_drop_straight_liners(survey_responses, cleaning_log):
    """
    Find people who ticked essentially one column all the way down.

    This is done on the raw, un-reversed answers on purpose - see the module
    docstring. Their answers carry no information about differences between
    constructs, so they would flatten every construct correlation towards zero.
    """
    item_columns = config.all_item_columns()
    within_person_sd = survey_responses[item_columns].std(axis=1)
    is_straight_liner = within_person_sd < STRAIGHT_LINE_SD_THRESHOLD

    before = len(survey_responses)
    survey_responses = survey_responses.loc[~is_straight_liner].copy()
    log_step(cleaning_log, "Drop straight-lining respondents", int(is_straight_liner.sum()),
             "rows", len(survey_responses), before,
             f"Within-person SD across {len(item_columns)} items below "
             f"{STRAIGHT_LINE_SD_THRESHOLD}. Detected on RAW answers, before reverse-coding.")
    return survey_responses.reset_index(drop=True)


def apply_reverse_coding(survey_responses, cleaning_log):
    """Flip the six negatively worded items so all items point the same way."""
    for item in config.REVERSE_ITEMS:
        survey_responses[item] = reverse_code(survey_responses[item])
    affected = int(survey_responses[config.REVERSE_ITEMS].notna().sum().sum())
    log_step(cleaning_log, "Reverse-code negatively worded items", affected, "values",
             len(survey_responses), survey_responses[config.all_item_columns()].size,
             f"Items flipped: {', '.join(config.REVERSE_ITEMS)}. "
             "Formula (1+5)-answer so high = favourable for every item.")
    return survey_responses


def drop_heavy_non_responders(survey_responses, cleaning_log):
    """Remove people who left more than 30% of the questionnaire blank."""
    item_columns = config.all_item_columns()
    missing_share = survey_responses[item_columns].isna().mean(axis=1)
    too_incomplete = missing_share > MAX_MISSING_SHARE_PER_PERSON

    before = len(survey_responses)
    survey_responses = survey_responses.loc[~too_incomplete].copy()
    log_step(cleaning_log, "Drop respondents missing >30% of items",
             int(too_incomplete.sum()), "rows", len(survey_responses), before,
             "Too little data to score eight constructs for these respondents.")
    return survey_responses.reset_index(drop=True)


def record_missing_data_policy(survey_responses, cleaning_log):
    """
    Record how I handled missing answers, and why.

    Dropping every row that has any missing answer is the easy default. I
    wanted to show the actual number rather than quietly avoid it, because it
    turns out that choice would throw away most of my sample.
    """
    item_columns = config.all_item_columns()
    complete_rows = int(survey_responses[item_columns].notna().all(axis=1).sum())
    retained_share = 100 * complete_rows / len(survey_responses)
    remaining_missing = int(survey_responses[item_columns].isna().sum().sum())

    log_step(cleaning_log, "Missing-data policy: available-item scoring (NOT listwise)",
             remaining_missing, "values", len(survey_responses),
             survey_responses[item_columns].size,
             f"Listwise deletion across all {len(item_columns)} items would keep only "
             f"{complete_rows} respondents ({retained_share:.1f}%). Missingness is thinly "
             "spread, so scores are the mean of ANSWERED items where >=50% of a "
             "construct's items were answered.")
    return survey_responses


def verify_scale_bounds(survey_responses):
    """Final assertion: after cleaning, every answer must sit inside 1-5 or be missing."""
    values = survey_responses[config.all_item_columns()]
    observed_min = np.nanmin(values.to_numpy(dtype=float))
    observed_max = np.nanmax(values.to_numpy(dtype=float))
    assert observed_min >= config.LIKERT_MIN, f"value below scale: {observed_min}"
    assert observed_max <= config.LIKERT_MAX, f"value above scale: {observed_max}"
    print(f"   scale check passed: all answers within [{observed_min:.0f}, {observed_max:.0f}]")


def main():
    print("PHASE 2: cleaning")
    config.ensure_dirs()
    survey_responses = pd.read_csv(config.RAW_SURVEY_FILE)
    starting_rows = len(survey_responses)
    print(f"   starting from {starting_rows} raw rows")

    cleaning_log = []
    survey_responses = drop_duplicate_submissions(survey_responses, cleaning_log)
    survey_responses = tidy_demographic_text(survey_responses, cleaning_log)
    survey_responses = blank_out_of_scale_answers(survey_responses, cleaning_log)
    survey_responses = flag_and_drop_straight_liners(survey_responses, cleaning_log)
    survey_responses = apply_reverse_coding(survey_responses, cleaning_log)
    survey_responses = drop_heavy_non_responders(survey_responses, cleaning_log)
    survey_responses = record_missing_data_policy(survey_responses, cleaning_log)
    verify_scale_bounds(survey_responses)

    log_table = pd.DataFrame(cleaning_log)
    log_table.insert(0, "data_label", config.DATA_LABEL)
    log_table.to_csv(config.RESULTS_DIR / "01_cleaning_log.csv", index=False)
    survey_responses.to_parquet(config.CLEAN_SURVEY_FILE, index=False)

    kept = 100 * len(survey_responses) / starting_rows
    print(f"   kept {len(survey_responses)} of {starting_rows} rows ({kept:.1f}%)")
    print("   cleaning complete\n")


if __name__ == "__main__":
    main()
