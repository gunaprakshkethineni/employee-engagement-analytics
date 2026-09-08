"""
Shared look and feel for all the charts, so they match.

The style is deliberately plain: title, one line of plain English saying what
the chart shows, then the small print, then the data. No arrows or boxes drawn
on top of anything.

Nothing in this file changes a number - it is all just appearance.
"""

import textwrap

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import config

# Near-black text, one blue for data, greys for everything structural.
INK = "#111827"
MUTED = "#6B7280"
FAINT = "#9CA3AF"
LINE = "#E8EBEF"
PRIMARY = "#3B6FB0"
PRIMARY_SOFT = "#AFC7E0"
NEUTRAL = "#D3D8DE"
CANVAS = "#FFFFFF"

# Sequential blue for correlations, which are all positive here.
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "project_sequential", ["#FFFFFF", "#C7D8EA", "#7BA3CB", "#3B6FB0", "#1E4372"])

# Muted diverging map for factor loadings, where the sign carries meaning.
DIVERGING = LinearSegmentedColormap.from_list(
    "project_diverging", ["#8C4A1F", "#D8A67F", "#FFFFFF", "#7BA3CB", "#1E4372"])

FIGURE_DPI = 200


def apply_house_style():
    """Set the matplotlib defaults once, so no chart has to repeat them."""
    mpl.rcParams.update({
        "figure.facecolor": CANVAS,
        "axes.facecolor": CANVAS,
        "savefig.facecolor": CANVAS,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Calibri", "DejaVu Sans"],
        "font.size": 10.5,
        "text.color": INK,
        "axes.labelcolor": MUTED,
        "axes.labelsize": 10.5,
        "axes.titlesize": 11,
        "axes.titlecolor": INK,
        "axes.edgecolor": LINE,
        "axes.linewidth": 1.0,
        "axes.grid": False,
        "grid.color": LINE,
        "grid.linewidth": 1.0,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.frameon": False,
        "legend.fontsize": 10,
    })


def clean_axis(axis, grid_axis="x"):
    """Drop the chart junk: no box, one faint grid direction, grid behind data."""
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color(LINE)
    axis.tick_params(length=0, pad=6)
    if grid_axis:
        axis.grid(axis=grid_axis, color=LINE, linewidth=1.0)
        axis.set_axisbelow(True)


def bare_axis(axis):
    """
    Strip an axis to nothing but its category labels.

    Used where every bar is labelled with its own value: the gridlines and the
    numeric axis are then pure decoration, and removing them is what makes the
    chart read as clean rather than busy.
    """
    for side in ("top", "right", "bottom", "left"):
        axis.spines[side].set_visible(False)
    axis.tick_params(length=0, pad=8)
    axis.set_xticks([])
    axis.grid(False)


def add_header(figure, title, finding, note, top=0.965):
    """
    Three things at the top of every chart:
      1. what the chart is
      2. what it shows, in plain words - no stats jargon, because whoever is
         reading it might not have done a stats course
      3. the small print: definitions, method, sample size

    The finding gets wrapped to fit the figure width, otherwise a long sentence
    just runs off the right-hand edge. How far down the small print goes then
    depends on how many lines the wrap produced, and save() reads the same
    number so the plot never collides with the text.
    """
    height = figure.get_figheight()
    characters_per_line = max(40, int((figure.get_figwidth() - 0.3) / 0.079))
    finding_lines = textwrap.wrap(finding, characters_per_line) or [""]

    title_gap = 0.30 / height
    line_height = 0.235 / height

    figure.text(0.012, top, title, fontsize=16, fontweight="semibold",
                color=INK, ha="left", va="top")
    figure.text(0.012, top - title_gap, "\n".join(finding_lines), fontsize=11.5,
                color=INK, ha="left", va="top", linespacing=1.45)
    figure.text(0.012, top - title_gap - len(finding_lines) * line_height, note,
                fontsize=9.5, color=FAINT, ha="left", va="top")

    # Remember how much vertical space the header used, in figure fractions.
    figure.header_bottom = top - title_gap - len(finding_lines) * line_height - 0.35 / height


def save(figure, filename, left=0.0):
    """
    Save the chart, keeping the plot below whatever space the header used.

    add_header works out where it finished and leaves the answer on the figure,
    so I do not have to guess a different margin for every chart. `left` widens
    the gutter for charts that put labels in the margin.

    Returns the filename so a notebook can pick the chart up and display it.
    """
    path = config.FIGURES_DIR / filename
    top = getattr(figure, "header_bottom", 0.88)
    figure.tight_layout(rect=(left, 0.02, 1, top))
    figure.savefig(path, dpi=FIGURE_DPI, facecolor=CANVAS)
    plt.close(figure)
    print(f"   wrote figures/{filename}")
    return filename
