"""Two-panel story figure for Failure 1 (figures/failure1_story.png).

Left: control vs discontinue for each model/prompt (is it the instruction?).
Right: the same stop sentence at different places (mechanism).

Usage:
    python src/fig_failure1.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze import CONTROL, MAIN, load, rate
from config import FIGURES_DIR


def eligible(arms, control=CONTROL):
    return {n for n, r in arms[control].items() if not r["error"]}


def bar(ax, y, s, color):
    ax.barh(y, s["rate"] * 100, color=color, height=0.62,
            xerr=[[(s["rate"] - s["lo"]) * 100], [(s["hi"] - s["rate"]) * 100]], capsize=3, ecolor="#333333")
    ax.text(s["hi"] * 100 + 2, y, f"{s['k']}/{s['n']}", va="center", fontsize=8.5)


def main():
    q, g = load("stop_instruction", "qwen2.5:3b"), load("stop_instruction", "gpt-5.4-mini")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.4))

    alt_c, alt_m = ("continue", "late", "extract_alt"), ("discontinue", "late", "extract_alt")
    rows = [
        ("qwen 3b · 'Continue X' (control)", rate(q[CONTROL], eligible(q)), "#9aa3ad"),
        ("qwen 3b · 'Discontinue X'", rate(q[MAIN], eligible(q)), "#c0392b"),
        ("qwen 3b, reworded prompt · control", rate(q[alt_c], eligible(q, alt_c)), "#9aa3ad"),
        ("qwen 3b, reworded prompt · 'Discontinue X'", rate(q[alt_m], eligible(q, alt_c)), "#c0392b"),
        ("gpt-5.4-mini · control", rate(g[CONTROL], eligible(g)), "#9aa3ad"),
        ("gpt-5.4-mini · 'Discontinue X'", rate(g[MAIN], eligible(g)), "#e08b7d"),
    ]
    for i, (label, s, c) in enumerate(rows):
        bar(a1, len(rows) - 1 - i, s, c)
    a1.set_yticks(range(len(rows))[::-1], [r[0] for r in rows], fontsize=9)
    a1.set_title("Is it the instruction? One word changed", loc="left", fontsize=10, fontweight="bold")

    el = eligible(q)
    places = [
        ("Near start of note (before the med list)", ("discontinue", "early", "extract"), "#2e6f95"),
        ("Inside the drug's own line in the list", ("discontinue", "inline", "extract"), "#2e6f95"),
        ("Right after the med list", ("discontinue", "after_meds", "extract"), "#c0392b"),
        ("Middle of note (after the list)", ("discontinue", "middle", "extract"), "#c0392b"),
        ("Near end of note (main case)", MAIN, "#c0392b"),
    ]
    for i, (label, arm, c) in enumerate(places):
        bar(a2, len(places) - 1 - i, rate(q[arm], el), c)
    a2.set_yticks(range(len(places))[::-1], [p[0] for p in places], fontsize=9)
    a2.set_title("Why? Same sentence, moved (qwen 3b)", loc="left", fontsize=10, fontweight="bold")
    a2.text(79, 3.55, "blue = stop read before / at the drug", ha="right", va="center", fontsize=8, color="#2e6f95")
    a2.text(79, 1.5, "red = stop comes after the list", ha="right", va="center", fontsize=8, color="#c0392b")

    for ax in (a1, a2):
        ax.set_xlim(0, 80)
        ax.set_xlabel("% of notes where the stopped drug stays on the list\n(control: drug wrongly dropped) · 95% CI",
                      fontsize=8.5)
        ax.grid(axis="x", color="#e5e5e5")
        ax.set_axisbelow(True)
    fig.suptitle("Failure 1: “Discontinue X” is understood but not applied", x=0.01, ha="left",
                 fontweight="bold", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "failure1_story.png", dpi=180)
    print(FIGURES_DIR / "failure1_story.png")


if __name__ == "__main__":
    main()
