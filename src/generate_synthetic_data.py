"""
Makes the fake survey data.

I had no real survey file, so I had to generate one. I did not want to just
fill it with random numbers, because then the reliability and factor analysis
later would be meaningless. So I built it the way the theory says a real survey
works: there are hidden culture factors that people actually feel, and the
questions are noisy clues about them. That way my analysis has to find the
structure itself instead of me just claiming it.

How it works:
  1. Give each person one general "I like it here" score (call it G).
  2. Build 8 culture factors on top of G, so they end up correlated with each
     other. This is what causes the multicollinearity problem later on.
  3. Nudge those factors slightly by business unit and by demographics.
  4. Turn each factor into 8 questions, each a noisy version of it.
  5. Round the scores into 1-5 answers, like a real Likert scale.
  6. Last, mess it up on purpose: reverse-worded questions, people who tick the
     same box all the way down, missing answers, bad codes, duplicate rows and
     untidy text.

None of the later scripts know the true values. Run it with:
    python src/generate_synthetic_data.py
"""

import numpy as np
import pandas as pd

import config

RANDOM_SEED = 20260907
N_RESPONDENTS = 5000
N_BUSINESS_UNITS = 24

# How much each culture factor is driven by the general tendency G. Higher
# means the eight constructs correlate more strongly with one another. 0.80
# reproduces the 0.6-0.7 inter-construct correlations reported in published
# engagement survey work.
GENERAL_FACTOR_WEIGHT = 0.80

# Credibility and leadership are conceptually near-twins ("do I believe the
# people in charge"), so they get extra shared variance on top of G. This is
# deliberate: it gives the regression a genuine multicollinearity problem to
# detect and talk about rather than a textbook-clean one.
TWIN_CONSTRUCTS = ("credibility", "leadership")
TWIN_EXTRA_WEIGHT = 0.45

# Two items are built as near-duds - they barely reflect the construct they are
# filed under, the way a badly worded question really does behave. This gives
# the reliability step something genuine to catch and remove.
WEAK_ITEMS = {"devl_04": 0.15, "resp_02": 0.18}

# How strongly each culture factor really drives satisfaction. The analysis
# will NOT recover these cleanly, because the factors are correlated and
# measured with error - which is exactly the point.
TRUE_SATISFACTION_WEIGHTS = {
    "leadership": 0.34,
    "fairness": 0.26,
    "pride": 0.22,
    "credibility": 0.12,
    "respect": 0.09,
    "wellbeing": 0.08,
    "development": 0.05,
    "camaraderie": 0.03,
}

DEPARTMENTS = ["Engineering", "Operations", "Service", "Supply Chain",
               "Sales", "Finance", "HR"]
TENURE_BANDS = ["<1 year", "1-3 years", "3-5 years", "5-10 years", "10+ years"]
LOCATIONS = ["Hamburg", "Rostock", "Pune", "Chennai", "Aarhus", "Remote"]
ROLE_LEVELS = ["Individual contributor", "Team lead", "Manager", "Senior manager"]

# Likert cut points applied to a standardised score. Shifted left of centre so
# the answer distribution leans positive, as engagement survey data really does.
LIKERT_CUTS = [-1.8, -1.0, -0.2, 0.65]


def standardise(values):
    """Rescale to mean 0, sd 1 so every latent score is on the same footing."""
    return (values - values.mean()) / values.std()


def to_likert(latent_scores, rng):
    """Chop a continuous score into 1-5 categories at fixed cut points."""
    return np.digitize(standardise(latent_scores), LIKERT_CUTS) + 1


def draw_demographics(rng):
    """Assign each respondent to a business unit and the usual HR categories."""
    unit_sizes = rng.dirichlet(np.ones(N_BUSINESS_UNITS) * 12) * N_RESPONDENTS
    unit_ids = np.repeat(np.arange(N_BUSINESS_UNITS), np.maximum(1, unit_sizes.astype(int)))
    unit_ids = np.resize(unit_ids, N_RESPONDENTS)
    rng.shuffle(unit_ids)

    people = pd.DataFrame({
        "respondent_id": [f"R{i:05d}" for i in range(1, N_RESPONDENTS + 1)],
        "business_unit": [f"BU{u + 1:02d}" for u in unit_ids],
        "department": rng.choice(DEPARTMENTS, N_RESPONDENTS,
                                 p=[0.26, 0.22, 0.16, 0.12, 0.11, 0.07, 0.06]),
        "tenure_band": rng.choice(TENURE_BANDS, N_RESPONDENTS,
                                  p=[0.14, 0.24, 0.20, 0.24, 0.18]),
        "location": rng.choice(LOCATIONS, N_RESPONDENTS,
                               p=[0.22, 0.14, 0.21, 0.17, 0.13, 0.13]),
        "role_level": rng.choice(ROLE_LEVELS, N_RESPONDENTS,
                                 p=[0.62, 0.20, 0.13, 0.05]),
    })
    people["unit_index"] = unit_ids
    return people


def draw_latent_factors(people, rng):
    """
    Build the eight unobserved culture factors.

    Each factor = shared general tendency + its own unique part + a business
    unit offset + small demographic shifts. The demographic shifts are kept
    deliberately small, so that later the p-values will be tiny (n=5000) while
    the effect sizes stay modest - the exact tension the analysis has to explain.
    """
    general_tendency = rng.normal(0, 1, len(people))
    twin_component = rng.normal(0, 1, len(people))
    unit_offsets = rng.normal(0, 0.42, N_BUSINESS_UNITS)

    factors = pd.DataFrame(index=people.index)

    for construct in config.CONSTRUCTS:
        # The weights are chosen so that every factor has variance 1 before the
        # unit offset is added; that keeps the twin pair from simply being
        # noisier than the rest rather than more correlated.
        twin_weight = TWIN_EXTRA_WEIGHT if construct in TWIN_CONSTRUCTS else 0.0
        unique_weight = np.sqrt(max(0.0, 1 - GENERAL_FACTOR_WEIGHT ** 2 - twin_weight ** 2))
        factors[construct] = (GENERAL_FACTOR_WEIGHT * general_tendency
                              + twin_weight * twin_component
                              + unique_weight * rng.normal(0, 1, len(people))
                              + unit_offsets[people["unit_index"].to_numpy()])

    # Demographic structure that the ANOVA is meant to find. One site is a
    # genuine problem site; the rest are nudges.
    site_wellbeing = {"Hamburg": 0.10, "Rostock": -0.06, "Pune": 0.18,
                      "Chennai": -0.42, "Aarhus": 0.22, "Remote": -0.02}
    site_leadership = {"Hamburg": 0.06, "Rostock": -0.10, "Pune": 0.12,
                       "Chennai": -0.26, "Aarhus": 0.14, "Remote": -0.08}
    dept_development = {"Engineering": 0.16, "Operations": -0.14, "Service": -0.10,
                        "Supply Chain": -0.04, "Sales": 0.06, "Finance": 0.08, "HR": 0.20}
    tenure_pride = {"<1 year": 0.24, "1-3 years": 0.04, "3-5 years": -0.14,
                    "5-10 years": -0.08, "10+ years": 0.10}
    role_fairness = {"Individual contributor": -0.08, "Team lead": 0.02,
                     "Manager": 0.14, "Senior manager": 0.28}

    factors["wellbeing"] += people["location"].map(site_wellbeing).to_numpy()
    factors["leadership"] += people["location"].map(site_leadership).to_numpy()
    factors["development"] += people["department"].map(dept_development).to_numpy()
    factors["pride"] += people["tenure_band"].map(tenure_pride).to_numpy()
    factors["fairness"] += people["role_level"].map(role_fairness).to_numpy()

    return factors.apply(standardise), unit_offsets


def draw_item_responses(factors, rng):
    """
    Turn latent factors into 64 Likert items.

    Each item loads mainly on its own construct. Every item also picks up a
    small per-respondent "response style" term (some people just tick high),
    which is what common method bias looks like in real single-source data.
    Reverse-worded items load negatively, so the raw file needs recoding.
    """
    n = len(factors)
    response_style = rng.normal(0, 0.26, n)
    responses = {}

    for construct in config.CONSTRUCTS:
        for item in config.construct_items(construct):
            loading = WEAK_ITEMS.get(item, rng.uniform(0.58, 0.75))
            latent = loading * factors[construct].to_numpy()

            # A couple of items also bleed onto a neighbouring construct, so the
            # factor analysis sees realistic cross-loadings rather than a
            # suspiciously perfect simple structure.
            if item in ("well_08", "camr_06", "fair_07"):
                neighbour = rng.choice([c for c in config.CONSTRUCTS if c != construct])
                latent = latent + 0.26 * factors[neighbour].to_numpy()

            if item in config.REVERSE_ITEMS:
                latent = -latent

            latent = latent + response_style + rng.normal(0, 0.62, n)
            responses[item] = to_likert(latent, rng)

    return pd.DataFrame(responses, index=factors.index), response_style


def draw_satisfaction(factors, people, response_style, rng):
    """Build the 4-item outcome scale as a weighted mix of the true factors."""
    signal = np.zeros(len(factors))
    for construct, weight in TRUE_SATISFACTION_WEIGHTS.items():
        signal += weight * factors[construct].to_numpy()

    role_bonus = people["role_level"].map(
        {"Individual contributor": -0.05, "Team lead": 0.03,
         "Manager": 0.10, "Senior manager": 0.20}).to_numpy()
    signal = signal + role_bonus
    signal = standardise(signal) + rng.normal(0, 0.95, len(factors))

    satisfaction = {}
    for item in sorted(config.SATISFACTION_ITEMS):
        latent = 0.76 * standardise(signal) + response_style + rng.normal(0, 0.55, len(factors))
        satisfaction[item] = to_likert(latent, rng)
    return pd.DataFrame(satisfaction, index=factors.index)


def add_real_world_mess(survey, rng):
    """
    Break the clean data in the ways real survey exports are broken.

    Each of these is something the cleaning stage has to detect and log:
    straight-lining, missingness, out-of-range codes, duplicate submissions
    and untidy free-text categories.
    """
    item_cols = config.all_item_columns()

    # Straight-liners: ~3% of people tick one column all the way down.
    straight_liners = rng.choice(survey.index, size=int(0.03 * len(survey)), replace=False)
    for row in straight_liners:
        survey.loc[row, item_cols] = rng.choice([4, 4, 5, 3])
    print(f"   injected {len(straight_liners)} straight-lining respondents")

    # Missing answers: a low baseline everywhere, rising towards the end of the
    # questionnaire because people get tired and abandon it.
    for position, item in enumerate(item_cols):
        rate = 0.012 + 0.030 * (position / len(item_cols))
        blanks = rng.random(len(survey)) < rate
        survey.loc[blanks, item] = np.nan
    print(f"   injected missing values; overall {survey[item_cols].isna().mean().mean():.1%}")

    # Out-of-range codes that survived a bad export: a 6 that should not exist,
    # and 99 used as "prefer not to say".
    survey.loc[rng.choice(survey.index, 42, replace=False), "fair_01"] = 6
    survey.loc[rng.choice(survey.index, 27, replace=False), "well_02"] = 99
    print("   injected 42 values of 6 in fair_01 and 27 values of 99 in well_02")

    # Untidy category text: stray whitespace and casing, as if typed by hand.
    messy_rows = rng.choice(survey.index, 60, replace=False)
    survey.loc[messy_rows, "department"] = " " + survey.loc[messy_rows, "department"].str.upper()

    # A dozen duplicated submissions (someone hit submit twice).
    duplicates = survey.loc[rng.choice(survey.index, 12, replace=False)].copy()
    survey = pd.concat([survey, duplicates], ignore_index=True)
    print(f"   appended {len(duplicates)} duplicate rows; file now has {len(survey)} rows")
    return survey


def build_unit_table(people, factors, unit_offsets, rng):
    """
    Business-unit Return on Sales.

    ROS is built to be *correlated with* culture, not determined by it: a unit's
    culture offset explains part of it and unrelated commercial noise explains
    the rest. That keeps the later ROS analysis honest - the relationship is
    real but weak, which is what the write-up has to say.
    """
    units = sorted(people["business_unit"].unique())
    headcount = people["business_unit"].value_counts().reindex(units).to_numpy()
    culture_offset = unit_offsets[[int(u[2:]) - 1 for u in units]]

    return_on_sales = 7.5 + 2.6 * culture_offset + rng.normal(0, 2.4, len(units))
    return pd.DataFrame({
        "business_unit": units,
        "headcount": headcount,
        "region": rng.choice(["EMEA", "APAC", "AMER"], len(units), p=[0.5, 0.35, 0.15]),
        "revenue_musd": np.round(np.abs(rng.normal(120, 55, len(units))) + 20, 1),
        "return_on_sales_pct": np.round(return_on_sales, 2),
    })


def main():
    print(f"Generating {config.DATA_LABEL} survey (seed={RANDOM_SEED})")
    config.ensure_dirs()
    rng = np.random.default_rng(RANDOM_SEED)

    people = draw_demographics(rng)
    print(f"   {len(people)} respondents across {N_BUSINESS_UNITS} business units")

    factors, unit_offsets = draw_latent_factors(people, rng)
    print(f"   built {len(config.CONSTRUCTS)} latent culture factors")

    items, response_style = draw_item_responses(factors, rng)
    satisfaction = draw_satisfaction(factors, people, response_style, rng)
    print(f"   generated {items.shape[1]} culture items + {satisfaction.shape[1]} satisfaction items")

    survey = pd.concat(
        [people.drop(columns=["unit_index"]), items, satisfaction], axis=1)
    survey = add_real_world_mess(survey, rng)

    units = build_unit_table(people, factors, unit_offsets, rng)

    survey.to_csv(config.RAW_SURVEY_FILE, index=False)
    units.to_csv(config.RAW_UNIT_FILE, index=False)
    print(f"   wrote {config.RAW_SURVEY_FILE.name} and {config.RAW_UNIT_FILE.name}")
    print("Done.")


if __name__ == "__main__":
    main()
