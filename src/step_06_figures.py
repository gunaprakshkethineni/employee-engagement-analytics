"""
Phase 7a: the charts.

I rebuilt these around the questions a management team would actually ask,
rather than around the statistics I ran. Each one answers one question:

  1. Where do we stand today?
  2. What should we fix first?
  3. Where is the problem?
  4. What is it costing us?
  5. Which units need attention?
  6. Does any of this reach the P&L?

The method charts (reliability, scree plot, loadings, residual diagnostics) are
gone. The numbers behind them are still in results/*.csv and written up in
EXPLAINER.md, which is where a technical reviewer would look anyway.

Everything here is an association, not proof of cause, and the small print on
each chart says so where it matters.

Outputs: results/figures/*.png
"""

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy import stats

import config
import plot_style as style

# Someone scoring below the midpoint of the satisfaction scale. The scale
# includes "I rarely think about leaving", so a low score is the closest thing
# to a flight-risk signal this survey can give me.
AT_RISK_THRESHOLD = 3.0

# "Favourable" is the standard engagement-survey convention: the share of
# people who picked 4 or 5 out of 5.
FAVOURABLE_THRESHOLD = 4


def load(name, **kwargs):
    """Read one of the result tables written by an earlier phase."""
    return pd.read_csv(config.RESULTS_DIR / name, **kwargs)


def favourable_rates(scores):
    """Share of employees scoring 4 or 5 on each topic, as a percentage."""
    return (scores[config.CONSTRUCTS] >= FAVOURABLE_THRESHOLD).mean() * 100


def impact_on_satisfaction():
    """
    How much satisfaction moves per 1 point of each topic, from the regression.

    These are the plain (unstandardised) coefficients, so they are already in
    the units a manager thinks in: points on the same 1-5 scale.
    """
    table = load("04_regression_table.csv").set_index("term")
    return table.loc[config.CONSTRUCTS, "coefficient"]


def plot_where_we_stand(scores):
    """Question 1: how are we doing on each topic right now?"""
    favourable = favourable_rates(scores).sort_values()
    overall = (scores["satisfaction"] >= FAVOURABLE_THRESHOLD).mean() * 100

    figure, axis = plt.subplots(figsize=(10, 5.6))
    axis.barh(favourable.index, favourable.to_numpy(), color=style.PRIMARY, height=0.6)
    for topic, value in favourable.items():
        axis.text(value - 0.7, topic, f"{value:.0f}%", va="center", ha="right",
                  fontsize=10.5, color="white")

    axis.set_xlim(0, 100)
    axis.set_ylim(-0.6, len(favourable) - 0.4)
    style.bare_axis(axis)

    style.add_header(
        figure, "Where we stand today",
        f"Only about a third of employees rate most topics favourably. Pride and development "
        f"are strongest at {favourable.max():.0f}%, respect weakest at {favourable.min():.0f}%. "
        f"Overall satisfaction is favourable for {overall:.0f}%.",
        f"share scoring 4 or 5 out of 5  ·  n = {len(scores):,} employees")
    return style.save(figure, "01_where_we_stand.png")


def plot_priority_matrix(scores):
    """
    Question 2: what should we fix first?

    Two things decide priority: how much a topic moves satisfaction, and how
    badly we are doing on it. A topic can be important and already fine, which
    means protect it rather than invest in it.
    """
    favourable = favourable_rates(scores)
    impact = impact_on_satisfaction()
    average_favourable = favourable.mean()
    average_impact = impact.mean()

    figure, axis = plt.subplots(figsize=(10.5, 6.8))
    axis.set_xlim(favourable.min() - 3, favourable.max() + 4)
    axis.set_ylim(0, impact.max() * 1.18)
    left, right = axis.get_xlim()
    top = axis.get_ylim()[1]

    # Shade only the one quadrant that carries an instruction: topics that
    # matter more than average and score worse than average. Drawn as a single
    # rectangle rather than overlapping spans, which left a tint everywhere.
    axis.add_patch(plt.Rectangle((left, average_impact),
                                 average_favourable - left, top - average_impact,
                                 facecolor=style.PRIMARY_SOFT, alpha=0.22,
                                 edgecolor="none", zorder=0))

    axis.scatter(favourable, impact, s=110, color=style.PRIMARY,
                 edgecolors="white", linewidth=1.4, zorder=4)

    # Nudge a label below its point when it would sit on top of a neighbour.
    placed = []
    for topic in impact.sort_values(ascending=False).index:
        offset = 13
        for other_x, other_y, other_offset in placed:
            if (abs(impact[topic] - other_y) < 0.016
                    and abs(favourable[topic] - other_x) < 3.0
                    and other_offset > 0):
                offset = -22
        axis.annotate(topic, (favourable[topic], impact[topic]), xytext=(0, offset),
                      textcoords="offset points", ha="center", fontsize=10.5,
                      color=style.INK, zorder=5)
        placed.append((favourable[topic], impact[topic], offset))

    axis.axhline(average_impact, color=style.MUTED, linewidth=1.1,
                 linestyle=(0, (5, 4)), zorder=3)
    axis.axvline(average_favourable, color=style.MUTED, linewidth=1.1,
                 linestyle=(0, (5, 4)), zorder=3)
    axis.text(left + 0.4, top * 0.985, "ACT HERE\nmatters more, scores worse",
              fontsize=10, color=style.PRIMARY, va="top", fontweight="semibold", zorder=5)
    axis.text(right - 0.4, top * 0.985, "PROTECT\nmatters more, already strong",
              fontsize=10, color=style.MUTED, va="top", ha="right", zorder=5)

    axis.set_xlabel("how we score today (% favourable)")
    axis.set_ylabel("effect on satisfaction (points per 1 point)")
    style.clean_axis(axis, grid_axis=None)

    # Ordered by impact so the headline names the biggest lever first.
    act = [c for c in impact.sort_values(ascending=False).index
           if impact[c] > average_impact and favourable[c] < average_favourable]
    style.add_header(
        figure, "What to fix first",
        f"{' and '.join(act).capitalize()} have the largest effect on satisfaction and are "
        "among the weakest scores, so they are where to start. Pride matters just as much but "
        "is already strong - that one is worth protecting, not fixing.",
        "effect sizes from the regression, holding the other topics and demographics constant")
    return style.save(figure, "02_what_to_fix_first.png")


def plot_site_gaps(scores):
    """
    Question 3: where is the problem?

    Plotted as the gap from the company average rather than the raw score. A
    grid of numbers all around 3.5 tells you nothing; a grid of gaps tells you
    where to go.
    """
    site_means = scores.groupby("location")[config.CONSTRUCTS].mean()
    gaps = site_means - scores[config.CONSTRUCTS].mean()
    gaps = gaps.loc[gaps.mean(axis=1).sort_values(ascending=False).index]

    limit = float(np.abs(gaps.to_numpy()).max())
    figure, axis = plt.subplots(figsize=(11, 5.2))
    image = axis.imshow(gaps.to_numpy(dtype=float), cmap=style.DIVERGING,
                        vmin=-limit, vmax=limit, aspect="auto")

    for row in range(gaps.shape[0]):
        for column in range(gaps.shape[1]):
            value = gaps.iloc[row, column]
            axis.text(column, row, f"{value:+.2f}", ha="center", va="center",
                      fontsize=9.5,
                      color="white" if abs(value) > 0.62 * limit else style.INK)

    axis.set_xticks(range(gaps.shape[1]), gaps.columns, rotation=30, ha="right", fontsize=10)
    axis.set_yticks(range(gaps.shape[0]), gaps.index, fontsize=10.5)
    axis.tick_params(length=0, pad=4)
    for spine in axis.spines.values():
        spine.set_visible(False)

    worst = gaps.stack().idxmin()
    lowest_site = gaps.mean(axis=1).idxmin()
    style.add_header(
        figure, "Where the problem sits",
        f"{worst[0]} is {abs(gaps.stack().min()):.2f} points below the company average on "
        f"{worst[1]} and {abs(gaps.loc[worst[0], 'leadership']):.2f} below on leadership. "
        f"{lowest_site} staff are slightly below average on almost everything. "
        "Every other gap is small.",
        "difference from the company average, in points on the 1-5 scale")
    return style.save(figure, "03_where_the_problem_sits.png")


def plot_risk_gradient(scores):
    """
    Question 4: what is it costing us?

    The clearest business consequence in the data. It is still a correlation -
    unhappy people may rate their manager harshly rather than the other way
    round - and the small print says so.
    """
    at_risk = scores["satisfaction"] < AT_RISK_THRESHOLD
    bands = pd.cut(scores["leadership"], [0, 2, 2.5, 3, 3.5, 4, 5],
                   labels=["2.0 or below", "2.0-2.5", "2.5-3.0",
                           "3.0-3.5", "3.5-4.0", "4.0-5.0"])
    summary = pd.DataFrame({"at_risk": at_risk, "band": bands}).dropna()
    summary = summary.groupby("band", observed=True)["at_risk"].agg(["mean", "size"])
    summary["mean"] *= 100

    figure, axis = plt.subplots(figsize=(10.5, 5.8))
    axis.bar(range(len(summary)), summary["mean"], color=style.PRIMARY, width=0.62)
    for position, row in enumerate(summary.itertuples()):
        axis.text(position, row.mean + 1.6, f"{row.mean:.0f}%", ha="center",
                  fontsize=11.5, color=style.INK)

    # Headcount goes into the tick label rather than floating under the bar,
    # where it collided with the axis text.
    axis.set_xticks(range(len(summary)),
                    [f"{band}\n{count:,} people" for band, count
                     in zip(summary.index, summary["size"])], fontsize=10)
    axis.set_ylim(0, summary["mean"].max() * 1.18)
    axis.set_xlabel("how the employee rates leadership")
    axis.set_ylabel("% at risk")
    style.clean_axis(axis, grid_axis="y")

    ratio = summary["mean"].iloc[0] / summary["mean"].iloc[-1]
    style.add_header(
        figure, "What weak leadership costs",
        f"{summary['mean'].iloc[0]:.0f}% of employees who rate leadership 2 or below are at "
        f"risk, against {summary['mean'].iloc[-1]:.0f}% of those rating it 4 or above - about "
        f"{ratio:.0f} times the rate. This is the strongest business signal in the survey.",
        "'at risk' = overall satisfaction below 3.0 out of 5, which includes intention to "
        "leave  ·  an association, not proof of cause")
    return style.save(figure, "04_what_weak_leadership_costs.png")


def plot_units_at_risk(scores):
    """
    Question 5: which units need attention?

    Percentages alone hide the size of the problem, so the number of people
    behind each percentage is on the chart too. A 37% rate in a small unit is a
    different decision from a 30% rate in a large one.
    """
    at_risk = scores.assign(at_risk=scores["satisfaction"] < AT_RISK_THRESHOLD)
    summary = at_risk.groupby("business_unit").agg(
        rate=("at_risk", "mean"), headcount=("at_risk", "size"),
        people=("at_risk", "sum"))
    summary["rate"] *= 100
    summary = summary.sort_values("rate")
    company_rate = 100 * at_risk["at_risk"].mean()

    figure, axis = plt.subplots(figsize=(10, 8.5))
    worst_five = summary["rate"] >= summary["rate"].nlargest(5).min()
    axis.barh(summary.index, summary["rate"],
              color=np.where(worst_five, style.PRIMARY, style.NEUTRAL), height=0.62)
    for unit, row in summary.iterrows():
        axis.text(row["rate"] + 0.6, unit, f"{row['rate']:.0f}%   {int(row['people'])} people",
                  va="center", fontsize=9.5, color=style.INK)

    axis.axvline(company_rate, color=style.INK, linewidth=1.2)
    axis.text(company_rate, len(summary) - 0.3, f"company {company_rate:.0f}%",
              ha="center", va="bottom", fontsize=9.5, color=style.MUTED)
    axis.set_xlim(0, summary["rate"].max() * 1.28)
    axis.set_ylim(-0.7, len(summary) + 0.3)
    axis.set_xlabel("% of employees at risk")
    style.clean_axis(axis, grid_axis="x")

    top_five_people = int(summary.nlargest(5, "rate")["people"].sum())
    style.add_header(
        figure, "Which units need attention",
        f"At-risk rates run from {summary['rate'].min():.0f}% to {summary['rate'].max():.0f}% "
        f"across the {len(summary)} units. The five worst units alone account for "
        f"{top_five_people} at-risk employees - that is where an intervention would reach the "
        "most people.",
        "'at risk' = overall satisfaction below 3.0 out of 5")
    return style.save(figure, "05_which_units_need_attention.png")


def plot_culture_vs_profit(unit_data):
    """
    Question 6: does any of this reach the P&L?

    The weakest claim in the project and the chart says so. 24 units is not
    enough to prove anything, and profitable units can afford to treat people
    well just as easily as good treatment can drive profit.
    """
    figure, axis = plt.subplots(figsize=(10, 6.4))
    median_culture = unit_data["culture_index"].median()
    median_ros = unit_data["return_on_sales_pct"].median()

    below_both = ((unit_data["culture_index"] < median_culture)
                  & (unit_data["return_on_sales_pct"] < median_ros))

    axis.axvline(median_culture, color=style.MUTED, linewidth=1.1, linestyle=(0, (5, 4)))
    axis.axhline(median_ros, color=style.MUTED, linewidth=1.1, linestyle=(0, (5, 4)))
    axis.scatter(unit_data.loc[~below_both, "culture_index"],
                 unit_data.loc[~below_both, "return_on_sales_pct"],
                 s=90, color=style.NEUTRAL, edgecolors="white", linewidth=1.3, zorder=3)
    axis.scatter(unit_data.loc[below_both, "culture_index"],
                 unit_data.loc[below_both, "return_on_sales_pct"],
                 s=90, color=style.PRIMARY, edgecolors="white", linewidth=1.3, zorder=4)

    correlation, p_value = stats.pearsonr(unit_data["culture_index"],
                                          unit_data["return_on_sales_pct"])
    axis.set_xlabel("business unit culture score (1-5)")
    axis.set_ylabel("Return on Sales (%)")
    axis.text(axis.get_xlim()[0] + 0.01, axis.get_ylim()[0] + 0.25,
              f"{int(below_both.sum())} units below average on both",
              fontsize=10, color=style.PRIMARY, fontweight="semibold")
    style.clean_axis(axis, grid_axis=None)

    style.add_header(
        figure, "Does culture reach the P&L?",
        f"Units with stronger culture do tend to be more profitable (r = {correlation:.2f}, "
        f"p = {p_value:.3f}), and {int(below_both.sum())} units sit below average on both. But "
        f"this rests on {len(unit_data)} units, and profitable units can equally afford to "
        "treat people well. Treat it as a signal to test, not a proven link.",
        f"one point per business unit  ·  n = {len(unit_data)} units  ·  correlation only, "
        "no causal claim")
    return style.save(figure, "06_does_culture_reach_the_pl.png")


def main():
    print("PHASE 7a: charts")
    config.ensure_dirs()
    style.apply_house_style()

    scores = pd.read_parquet(config.CONSTRUCT_SCORE_FILE)
    unit_data = load("05_unit_level_data.csv")

    plot_where_we_stand(scores)
    plot_priority_matrix(scores)
    plot_site_gaps(scores)
    plot_risk_gradient(scores)
    plot_units_at_risk(scores)
    plot_culture_vs_profit(unit_data)
    print("   charts complete\n")


if __name__ == "__main__":
    main()
