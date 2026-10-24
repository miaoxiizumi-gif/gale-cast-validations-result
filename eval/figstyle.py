"""Shared style for the paper figures (amendment A2): palette, provenance footer, PNG (300 DPI) + SVG export."""
from __future__ import annotations

import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# validated categorical order (dataviz validator, light surface #fcfcfb): W1, persistence, climatology
W1C, PERC, CLIMC = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
OBS = INK  # observations are drawn in ink, never in a series colour
METHOD = {"W1": ("W1", W1C, "o", "-"), "persistence": ("Persistence", PERC, "s", "--"),
          "climatology": ("Climatology", CLIMC, "^", ":")}
plt.rcParams.update({"font.size": 9.5, "font.family": "DejaVu Sans", "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "svg.fonttype": "none",
                     "axes.titlesize": 10, "axes.titleweight": "semibold", "legend.frameon": False})

EVIDENCE = {
    "A": "Evidence A: website historical scorecard cases (overall evidence)",
    "B": "Evidence B: training-consistent retrospective benchmark (overall evidence)",
    "C": "Evidence C: SELECTED SUCCESSFUL CASE, chosen retrospectively for illustration; not representative of all dates",
}


def title(fig, main: str, sub: str):
    fig.suptitle(main, x=0.01, y=0.995, ha="left", va="top", fontsize=12, fontweight="bold", color=INK)
    fig.text(0.01, 0.955, sub, ha="left", va="top", fontsize=9, color=INK2)


def footer(fig, lines: list[str], width: int = 150):
    txt = "\n".join(textwrap.fill(l, width) for l in lines)
    fig.text(0.01, 0.005, txt, ha="left", va="bottom", fontsize=7.2, color=INK2, linespacing=1.35)


def save(fig, out_dir, name: str) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", dpi=300)
    fig.savefig(out_dir / f"{name}.svg")
    plt.close(fig)
    return [f"{name}.png", f"{name}.svg"]
