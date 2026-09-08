"""
Settings and the questionnaire definition, all in one place.

Everything describing the survey itself lives here: what the questions are,
which construct each one is supposed to measure, which ones are worded
negatively, and where the files go. Doing it this way means none of the
analysis scripts have to hard-code a list of column names, so if I change a
question I only change it here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

RAW_SURVEY_FILE = RAW_DIR / "survey_responses_SYNTHETIC.csv"
RAW_UNIT_FILE = RAW_DIR / "business_unit_ros_SYNTHETIC.csv"
CLEAN_SURVEY_FILE = PROCESSED_DIR / "survey_clean_SYNTHETIC.parquet"
CONSTRUCT_SCORE_FILE = PROCESSED_DIR / "construct_scores_SYNTHETIC.parquet"

# Marker stamped onto every output so synthetic results can never be mistaken
# for findings from a real survey.
DATA_LABEL = "SYNTHETIC DATA"

# ---------------------------------------------------------------------------
# The measurement model: 8 culture constructs, 8 items each = 64 items.
# Plus a separate 4-item overall satisfaction scale used as the outcome.
#
# The short text is only a label so the data dictionary reads like a real
# questionnaire; the analysis never parses it.
# ---------------------------------------------------------------------------
LIKERT_MIN = 1
LIKERT_MAX = 5

CONSTRUCTS = [
    "credibility",
    "respect",
    "fairness",
    "pride",
    "camaraderie",
    "leadership",
    "development",
    "wellbeing",
]

CONSTRUCT_PREFIX = {
    "credibility": "cred",
    "respect": "resp",
    "fairness": "fair",
    "pride": "prid",
    "camaraderie": "camr",
    "leadership": "lead",
    "development": "devl",
    "wellbeing": "well",
}

ITEMS_PER_CONSTRUCT = 8

ITEM_TEXT = {
    # credibility - do people believe what management tells them
    "cred_01": "Management keeps me informed about important issues.",
    "cred_02": "Management's actions match its words.",
    "cred_03": "Management is honest about the state of the business.",
    "cred_04": "Management hides bad news from staff.",           # reverse
    "cred_05": "I can ask management a direct question and get a straight answer.",
    "cred_06": "Management delivers on the promises it makes.",
    "cred_07": "Communication from senior leaders is clear.",
    "cred_08": "I trust the information I receive from management.",
    # respect - are people treated as adults and supported
    "resp_01": "I am treated as a full member of the team regardless of my position.",
    "resp_02": "I am given the equipment and resources to do my job well.",
    "resp_03": "My manager recognises good work.",
    "resp_04": "My contribution is valued here.",
    "resp_05": "I am involved in decisions that affect my work.",
    "resp_06": "People here are treated as a number rather than a person.",  # reverse
    "resp_07": "Training is available when I need it to do my job.",
    "resp_08": "My manager takes an interest in me as a person.",
    # fairness - equity, impartiality, justice
    "fair_01": "People here are paid fairly for the work they do.",
    "fair_02": "Promotions go to those who best deserve them.",
    "fair_03": "Favouritism decides who gets ahead here.",         # reverse
    "fair_04": "Everyone has a fair chance at recognition.",
    "fair_05": "People are treated fairly regardless of their background.",
    "fair_06": "Performance is judged on objective criteria.",
    "fair_07": "If I were treated unfairly I could raise it and be heard.",
    "fair_08": "Workload is shared fairly across the team.",
    # pride - in the work, the team and the company
    "prid_01": "I am proud to tell others I work here.",
    "prid_02": "My work has meaning; it is not 'just a job'.",
    "prid_03": "I am proud of what we accomplish as a team.",
    "prid_04": "I feel I make a difference here.",
    "prid_05": "This organisation contributes something positive.",
    "prid_06": "I would recommend this company as a place to work.",
    "prid_07": "I am proud of the quality of what we produce.",
    "prid_08": "People here are willing to give extra to get the job done.",
    # camaraderie - the social fabric
    "camr_01": "People here care about each other.",
    "camr_02": "I can be myself at work.",
    "camr_03": "There is a sense of 'family' or team in my group.",
    "camr_04": "We celebrate successes together.",
    "camr_05": "New colleagues are made to feel welcome.",
    "camr_06": "People cooperate rather than compete destructively.",
    "camr_07": "I can rely on my colleagues when I need help.",
    "camr_08": "People here keep to themselves and do not help each other.",  # reverse
    # leadership - the direct management relationship and direction setting
    "lead_01": "My manager sets a clear direction for the team.",
    "lead_02": "My manager gives me useful feedback.",
    "lead_03": "Senior leadership has a clear vision for the company.",
    "lead_04": "My manager is competent at running the team.",
    "lead_05": "Decisions are made at the right speed here.",
    "lead_06": "My manager supports me when things go wrong.",
    "lead_07": "Leadership here avoids difficult decisions.",      # reverse
    "lead_08": "I have confidence in the leadership of this company.",
    # development - growth, learning, career
    "devl_01": "I have opportunities to learn and grow here.",
    "devl_02": "I can see a career path for myself here.",
    "devl_03": "My skills are developed, not just used.",
    "devl_04": "I am given challenging work that stretches me.",
    "devl_05": "My manager discusses my development with me.",
    "devl_06": "Internal moves and promotions are genuinely possible.",
    "devl_07": "The training I receive is of good quality.",
    "devl_08": "I am encouraged to take on new responsibilities.",
    # wellbeing - workload, balance, psychological safety
    "well_01": "I can balance my work and personal life.",
    "well_02": "My workload is manageable.",
    "well_03": "I can take time off when I need it.",
    "well_04": "This is a psychologically healthy place to work.",
    "well_05": "I often feel burnt out by my work.",               # reverse
    "well_06": "Stress here is at a reasonable level.",
    "well_07": "People are encouraged to switch off outside working hours.",
    "well_08": "I feel safe raising a concern without fear of consequences.",
}

# Negatively worded items. Real surveys include these to break the habit of
# ticking the same box down the page; they must be flipped before scoring or
# they will drag their construct's reliability down.
REVERSE_ITEMS = [
    "cred_04",
    "resp_06",
    "fair_03",
    "camr_08",
    "lead_07",
    "well_05",
]

# Outcome scale: overall satisfaction. Deliberately kept OUT of the 8 culture
# constructs so the regression is not predicting a variable from itself.
SATISFACTION_ITEMS = {
    "sat_01": "Overall, I am satisfied working here.",
    "sat_02": "Taking everything into account, this is a great place to work.",
    "sat_03": "I rarely think about leaving this organisation.",
    "sat_04": "I would still choose to join this company if deciding today.",
}

DEMOGRAPHIC_COLS = [
    "department",
    "tenure_band",
    "location",
    "role_level",
    "business_unit",
]


def construct_items(construct):
    """Return the list of item ids that are *intended* to measure a construct."""
    prefix = CONSTRUCT_PREFIX[construct]
    return [f"{prefix}_{i:02d}" for i in range(1, ITEMS_PER_CONSTRUCT + 1)]


def all_item_columns():
    """Every Likert item in the questionnaire, culture items then satisfaction."""
    items = []
    for construct in CONSTRUCTS:
        items.extend(construct_items(construct))
    items.extend(sorted(SATISFACTION_ITEMS))
    return items


def item_to_construct():
    """Mapping item id -> intended construct (satisfaction items map to 'satisfaction')."""
    mapping = {}
    for construct in CONSTRUCTS:
        for item in construct_items(construct):
            mapping[item] = construct
    for item in SATISFACTION_ITEMS:
        mapping[item] = "satisfaction"
    return mapping


def ensure_dirs():
    """Create the output folders if a fresh clone does not have them yet."""
    for folder in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
