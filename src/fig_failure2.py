"""Story figure for Failure 2 (figures/failure2_story.png): drop rate by list position,
with vs without the prompt's format example, same 134 real notes.

Usage:
    python src/fig_failure2.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze import load, rate
from config import FIGURES_DIR

POSITIONS = [(("reorder", "first"), "Drug moved to\nTOP of list"), (("original", "none"), "Drug where the\nnote put it"),
             (("reorder", "last"), "Drug moved to\nBOTTOM of list")]


def main():
    with_ex, no_ex = load("list_position", "qwen2.5:3b"), load("list_position_noex", "qwen2.5:3b")
    notes = set(with_ex[("reorder", "first", "extract")])
    fig, ax = plt.subplots(figsize=(9, 4.2))
    width = 0.36
    for j, (arms, prompt, label, color) in enumerate(
            ((with_ex, "extract", "Prompt WITH format example (“Lopressor 50 mg”, “aspirin 81 mg”)", "#c0392b"),
             (no_ex, "extract_noex", "Same prompt, example removed", "#2e6f95"))):
        for i, ((cond, pos), _) in enumerate(POSITIONS):
            s = rate(arms[(cond, pos, prompt)], notes)
            x = i + (j - 0.5) * width
            ax.bar(x, s["rate"] * 100, width, color=color, label=label if i == 0 else None,
                   yerr=[[(s["rate"] - s["lo"]) * 100], [(s["hi"] - s["rate"]) * 100]], capsize=3, ecolor="#333333")
            ax.text(x, s["hi"] * 100 + 1.2, f"{s['k']}/{s['n']}", ha="center", fontsize=8.5)
    ax.set_xticks(range(3), [p[1] for p in POSITIONS], fontsize=9.5)
    ax.set_ylabel("% of notes: active drug missing from list", fontsize=9)
    ax.set_ylim(0, 50)
    ax.legend(fontsize=8.5, loc="upper right", frameon=False)
    ax.grid(axis="y", color="#e5e5e5")
    ax.set_axisbelow(True)
    ax.set_title("Failure 2: the prompt’s example pushes out the patient’s first drug (qwen 3b, same 134 real notes)",
                 loc="left", fontsize=10.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "failure2_story.png", dpi=180)
    print(FIGURES_DIR / "failure2_story.png")


if __name__ == "__main__":
    main()
