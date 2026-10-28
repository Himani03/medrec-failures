"""Draw the pipeline diagram (figures/workflow.png) used in the README, write-up and slides.

Usage:
    python src/workflow_figure.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from config import FIGURES_DIR

STEPS = [
    ("1. Real notes", "148 MTSamples notes\nwith a medication list\n+ 1 target drug each", "#e8eef5"),
    ("2. Edit one thing", "add 'Continue X' or\n'Discontinue X', or\nmove X to top/bottom", "#fdf0e6"),
    ("3. Ask the model", "\"List every medication\nthe patient should take\nafter this visit\"", "#e8eef5"),
    ("4. Score", "Is X on the active list?\n(rule-based, 48 unit\ntests, hand-checked)", "#e8eef5"),
    ("5. Compare", "same notes, two versions:\nerror rate + 95% CI,\nMcNemar paired test", "#eaf4ea"),
]


def main():
    fig, ax = plt.subplots(figsize=(13, 3.6))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 3.6)
    ax.axis("off")
    w, h, y = 2.2, 1.9, 0.75
    for i, (title, body, color) in enumerate(STEPS):
        x = 0.25 + i * 2.55
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.12",
                                    facecolor=color, edgecolor="#5b6770", linewidth=1.2))
        ax.text(x + w / 2, y + h - 0.32, title, ha="center", va="center", fontsize=11, fontweight="bold")
        ax.text(x + w / 2, y + h / 2 - 0.25, body, ha="center", va="center", fontsize=9.2, linespacing=1.35)
        if i < len(STEPS) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.03, y + h / 2), (x + 2.55 - 0.03, y + h / 2),
                                         arrowstyle="-|>", mutation_scale=18, color="#5b6770", linewidth=1.5))
    ax.text(0.25, 3.25, "How the experiment works", fontsize=13, fontweight="bold")
    ax.text(0.25, 0.3, "Example: same note twice, \"PLAN: Continue Lopressor\" vs \"PLAN: Discontinue Lopressor\". "
            "If the model keeps Lopressor only in the second, the stop instruction was not applied.",
            fontsize=9.5, color="#3d4850", style="italic")
    ax.text(0.25 + 2 * 2.55 + 1.1, 2.83, "models: qwen2.5:3b (local), gpt-5.4-mini (API)", fontsize=9, color="#3d4850",
            ha="center")
    FIGURES_DIR.mkdir(exist_ok=True)
    fig.savefig(FIGURES_DIR / "workflow.png", dpi=180, bbox_inches="tight")
    print(FIGURES_DIR / "workflow.png")


if __name__ == "__main__":
    main()
