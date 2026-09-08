"""
Tests for the bits of logic that would quietly ruin everything downstream if I
got them wrong: reverse-coding, Cronbach's alpha and construct scoring. I also
test eta squared, because the whole ANOVA write-up depends on it.

Every expected number here is either worked out by hand in the comments, or it
is a case where the answer has to be obvious (identical questions must give
alpha = 1). I did not want to just check my code against a library, because
that only proves the two agree - not that either one is right. So the hand
calculations come first and the library check comes last.
"""

import numpy as np
import pandas as pd
import pytest

import config
from step_01_clean import reverse_code, STRAIGHT_LINE_SD_THRESHOLD
from step_02_constructs import cronbach_alpha, item_statistics, score_constructs
from step_03_anova import eta_squared


@pytest.fixture
def hand_worked_scale():
    """
    Three items, four people. Worked through by hand in the test below so the
    expected alpha does not depend on any library.
    """
    return pd.DataFrame({
        "a": [1, 2, 4, 5],
        "b": [1, 3, 4, 5],
        "c": [2, 2, 5, 4],
    })


@pytest.fixture
def mixed_direction_scale():
    """
    Four items measuring the same thing, but the last is worded negatively:
    people who answer 5 to the first three answer 1 to the last.
    """
    return pd.DataFrame({
        "q1": [1, 2, 3, 4, 5, 2, 4],
        "q2": [1, 2, 3, 4, 5, 3, 4],
        "q3": [2, 2, 3, 4, 5, 2, 5],
        "q4_reversed": [5, 4, 3, 2, 1, 4, 2],
    })


# ---------------------------------------------------------------------------
# Reverse coding
# ---------------------------------------------------------------------------

def test_reverse_code_flips_the_scale_end_to_end():
    """On a 1-5 scale, 1 must become 5 and 5 must become 1."""
    answers = pd.Series([1, 2, 3, 4, 5])
    assert reverse_code(answers).tolist() == [5, 4, 3, 2, 1]


def test_reverse_code_leaves_the_midpoint_alone():
    """3 is the midpoint of 1-5, so reversing must not move it."""
    assert reverse_code(pd.Series([3])).iloc[0] == 3


def test_reverse_code_applied_twice_returns_the_original():
    """Reversing is its own inverse - a useful guard against double-recoding."""
    answers = pd.Series([1, 2, 3, 4, 5])
    assert reverse_code(reverse_code(answers)).tolist() == answers.tolist()


def test_reverse_code_keeps_missing_values_missing():
    """A skipped question must stay skipped, not become a number."""
    reversed_answers = reverse_code(pd.Series([1.0, np.nan, 5.0]))
    assert reversed_answers.isna().sum() == 1
    assert reversed_answers.tolist()[0] == 5.0


def test_every_configured_reverse_item_exists_in_the_questionnaire():
    """Guards against a typo in config silently recoding nothing."""
    for item in config.REVERSE_ITEMS:
        assert item in config.ITEM_TEXT, f"{item} is not a real item"


# ---------------------------------------------------------------------------
# Cronbach's alpha
# ---------------------------------------------------------------------------

def test_cronbach_alpha_matches_the_hand_worked_example(hand_worked_scale):
    """
    Worked by hand, sample variances (ddof=1):
      item variances: a = 10/3 = 3.33333, b = 8.75/3 = 2.91667, c = 6.75/3 = 2.25
      sum of item variances = 8.5
      totals per person = 4, 7, 13, 14 -> variance = 69/3 = 23
      alpha = 3/2 * (1 - 8.5/23) = 1.5 * 0.6304348 = 0.9456522
    """
    assert cronbach_alpha(hand_worked_scale) == pytest.approx(0.9456522, abs=1e-6)


def test_alpha_is_one_when_items_are_identical():
    """If every item is a perfect copy, the scale is perfectly consistent."""
    identical = pd.DataFrame({"a": [1, 2, 3, 4], "b": [1, 2, 3, 4], "c": [1, 2, 3, 4]})
    assert cronbach_alpha(identical) == pytest.approx(1.0, abs=1e-9)


def test_alpha_collapses_when_items_are_unrelated():
    """
    Independent noise items share nothing, so alpha must sit near zero. It can
    go slightly negative by chance, which is why the bound is -0.2 not 0.
    """
    rng = np.random.default_rng(7)
    noise = pd.DataFrame(rng.normal(size=(400, 5)), columns=list("abcde"))
    assert -0.2 < cronbach_alpha(noise) < 0.2


def test_alpha_rises_when_more_good_items_are_added():
    """
    Alpha depends on scale LENGTH as well as item quality - the property that
    makes a high alpha on a 20-item scale much less impressive than on a
    4-item one. This test pins that behaviour down.
    """
    rng = np.random.default_rng(11)
    truth = rng.normal(size=600)
    items = {f"i{n}": truth + rng.normal(scale=1.0, size=600) for n in range(10)}
    frame = pd.DataFrame(items)
    assert cronbach_alpha(frame[["i0", "i1", "i2"]]) < cronbach_alpha(frame)


def test_alpha_is_undefined_for_a_single_item():
    """One item cannot be internally consistent with itself."""
    assert np.isnan(cronbach_alpha(pd.DataFrame({"only": [1, 2, 3, 4]})))


def test_alpha_is_wrecked_by_an_unreversed_item(mixed_direction_scale):
    """
    The reason reverse-coding is not optional: leaving one negatively worded
    item unflipped drags alpha down hard, and flipping it restores the scale.
    """
    alpha_before = cronbach_alpha(mixed_direction_scale)
    recoded = mixed_direction_scale.copy()
    recoded["q4_reversed"] = reverse_code(recoded["q4_reversed"])
    alpha_after = cronbach_alpha(recoded)
    assert alpha_before < 0.5
    assert alpha_after > 0.90
    assert alpha_after > alpha_before


def test_alpha_matches_pingouin_on_the_hand_worked_case(hand_worked_scale):
    """Cross-check against an independent implementation, after the hand cases."""
    pingouin = pytest.importorskip("pingouin")
    library_alpha = pingouin.cronbach_alpha(data=hand_worked_scale)[0]
    assert cronbach_alpha(hand_worked_scale) == pytest.approx(library_alpha, abs=1e-6)


# ---------------------------------------------------------------------------
# Item statistics
# ---------------------------------------------------------------------------

def test_alpha_if_deleted_equals_alpha_of_the_remaining_items(hand_worked_scale):
    """The alpha_if_deleted column must be exactly alpha without that item."""
    statistics = item_statistics(hand_worked_scale).set_index("item")
    expected = cronbach_alpha(hand_worked_scale[["b", "c"]])
    assert statistics.loc["a", "alpha_if_deleted"] == pytest.approx(round(expected, 3), abs=1e-3)


def test_item_total_correlation_excludes_the_item_itself(hand_worked_scale):
    """
    The correlation must be against the sum of the OTHER items. Correlating an
    item with a total that contains it inflates the number for free.
    """
    statistics = item_statistics(hand_worked_scale).set_index("item")
    corrected = hand_worked_scale["a"].corr(hand_worked_scale[["b", "c"]].sum(axis=1))
    inflated = hand_worked_scale["a"].corr(hand_worked_scale.sum(axis=1))
    assert statistics.loc["a", "item_total_corr"] == pytest.approx(round(corrected, 3), abs=1e-3)
    assert corrected < inflated


def test_a_junk_item_shows_a_low_item_total_correlation():
    """The detection rule that drove the devl_04 decision must actually work."""
    rng = np.random.default_rng(3)
    truth = rng.normal(size=500)
    frame = pd.DataFrame({
        "good1": truth + rng.normal(scale=0.5, size=500),
        "good2": truth + rng.normal(scale=0.5, size=500),
        "good3": truth + rng.normal(scale=0.5, size=500),
        "junk": rng.normal(size=500),
    })
    statistics = item_statistics(frame).set_index("item")
    assert statistics.loc["junk", "item_total_corr"] < 0.30
    assert statistics.loc["good1", "item_total_corr"] > 0.60
    assert statistics.loc["junk", "alpha_if_deleted"] > cronbach_alpha(frame)


# ---------------------------------------------------------------------------
# Construct scoring
# ---------------------------------------------------------------------------

@pytest.fixture
def tiny_survey():
    """
    Three respondents on one construct's items, with hand-set answers:
      - person A answered everything
      - person B answered half (still scoreable)
      - person C answered one item out of eight (must NOT be scored)
    """
    items = config.construct_items("credibility")
    rows = {
        "respondent_id": ["A", "B", "C"],
        "department": ["Engineering"] * 3,
        "tenure_band": ["1-3 years"] * 3,
        "location": ["Hamburg"] * 3,
        "role_level": ["Team lead"] * 3,
        "business_unit": ["BU01"] * 3,
    }
    answers = {
        items[0]: [4, 5, 3],
        items[1]: [4, 3, np.nan],
        items[2]: [2, 4, np.nan],
        items[3]: [2, 4, np.nan],
        items[4]: [4, np.nan, np.nan],
        items[5]: [4, np.nan, np.nan],
        items[6]: [4, np.nan, np.nan],
        items[7]: [4, np.nan, np.nan],
    }
    frame = pd.DataFrame({**rows, **answers})
    # The other seven constructs are filled with a flat 3 so that
    # score_constructs, which scores all eight, has the columns it expects.
    for construct in config.CONSTRUCTS:
        if construct == "credibility":
            continue
        for item in config.construct_items(construct):
            frame[item] = [3, 3, 3]
    for item in sorted(config.SATISFACTION_ITEMS):
        frame[item] = [5, 4, 3]
    return frame


def test_construct_score_is_the_mean_of_the_answered_items(tiny_survey):
    """Person A answered 4,4,2,2,4,4,4,4 -> mean 3.5."""
    retained = {c: config.construct_items(c) for c in config.CONSTRUCTS}
    scores = score_constructs(tiny_survey, retained)
    assert scores.loc[0, "credibility"] == pytest.approx(3.5)


def test_partial_responses_are_still_scored_above_the_threshold(tiny_survey):
    """Person B answered 4 of 8 items (5,3,4,4) -> exactly 50%, mean 4.0."""
    retained = {c: config.construct_items(c) for c in config.CONSTRUCTS}
    scores = score_constructs(tiny_survey, retained)
    assert scores.loc[1, "credibility"] == pytest.approx(4.0)


def test_too_few_answers_produce_no_score_rather_than_a_misleading_one(tiny_survey):
    """Person C answered 1 of 8 items. A 'score' of 3.0 from one answer would lie."""
    retained = {c: config.construct_items(c) for c in config.CONSTRUCTS}
    scores = score_constructs(tiny_survey, retained)
    assert pd.isna(scores.loc[2, "credibility"])


def test_dropped_items_are_excluded_from_the_score(tiny_survey):
    """If an item is dropped for poor reliability it must not reach the mean."""
    items = config.construct_items("credibility")
    retained = {c: config.construct_items(c) for c in config.CONSTRUCTS}
    retained["credibility"] = [i for i in items if i != items[2]]  # drop the '2' answer
    scores = score_constructs(tiny_survey, retained)
    assert scores.loc[0, "credibility"] == pytest.approx((4 + 4 + 2 + 4 + 4 + 4 + 4) / 7)


def test_scores_stay_inside_the_original_likert_range(tiny_survey):
    """A mean of 1-5 values can never leave 1-5; catches a scoring sign error."""
    retained = {c: config.construct_items(c) for c in config.CONSTRUCTS}
    scores = score_constructs(tiny_survey, retained)
    credibility = scores["credibility"].dropna()
    assert credibility.between(config.LIKERT_MIN, config.LIKERT_MAX).all()


# ---------------------------------------------------------------------------
# Effect size and the straight-lining ordering decision
# ---------------------------------------------------------------------------

def test_eta_squared_matches_a_hand_worked_example():
    """
    Groups [1,2,3] and [4,5,6]. Grand mean 3.5.
      SS between = 3*(2-3.5)^2 + 3*(5-3.5)^2 = 6.75 + 6.75 = 13.5
      SS total   = 6.25+2.25+0.25+0.25+2.25+6.25 = 17.5
      eta squared = 13.5/17.5 = 0.7714286
    """
    groups = [np.array([1, 2, 3]), np.array([4, 5, 6])]
    assert eta_squared(groups) == pytest.approx(0.7714286, abs=1e-6)


def test_eta_squared_is_zero_when_groups_have_the_same_mean():
    """No between-group signal must give exactly zero explained variance."""
    groups = [np.array([1, 2, 3]), np.array([3, 2, 1])]
    assert eta_squared(groups) == pytest.approx(0.0, abs=1e-12)


def test_straight_liners_must_be_detected_before_reverse_coding():
    """
    The ordering decision in Phase 2, pinned down as a test.

    A respondent who ticks 4 for all eight items has zero variance in the raw
    file. Reverse-code first and their reversed items become 2, giving them
    apparent variance and hiding them from the filter.
    """
    items = config.construct_items("credibility")
    straight_liner = pd.DataFrame({item: [4] for item in items})

    raw_spread = straight_liner.std(axis=1).iloc[0]
    recoded = straight_liner.copy()
    recoded[items[3]] = reverse_code(recoded[items[3]])
    recoded_spread = recoded.std(axis=1).iloc[0]

    assert raw_spread < STRAIGHT_LINE_SD_THRESHOLD, "should be caught on raw answers"
    assert recoded_spread > STRAIGHT_LINE_SD_THRESHOLD, "would be missed after recoding"
