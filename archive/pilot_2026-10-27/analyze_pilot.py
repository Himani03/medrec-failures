"""Summarize scored runs and make simple error-rate figures."""
import argparse
import json
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import FIGURES_DIR, RESULTS_DIR
from stats import mcnemar_exact, wilson_ci


CONTROL = ("continue", "late", "extract")
LABELS = {
    ("continue", "late", "extract"): "Continue control",
    ("discontinue", "late", "extract"): "Discontinue, late",
    ("discontinue", "early", "extract"): "Discontinue, early",
    ("discontinue", "middle", "extract"): "Discontinue, middle",
    ("discontinue", "late", "extract_careful"): "Explicit checklist prompt",
    ("discontinue", "late", "probe_stopped"): "Direct stop question",
}


def load_rows(model_filter=None):
    data = defaultdict(lambda: defaultdict(dict))
    for path in sorted(RESULTS_DIR.glob("*/*.jsonl")):
        if path.parent.name == "cache":
            continue
        for line in path.open():
            row = json.loads(line)
            if model_filter and row["model"] != model_filter:
                continue
            arm = (row["condition"], row["position"], row["prompt"])
            data[row["model"]][arm][row["note_id"]] = row
    return data


def valid_notes(arms):
    return {note_id for note_id, row in arms.get(CONTROL, {}).items() if not row["error"]}


def arm_stats(rows, notes):
    scored = [rows[note_id] for note_id in notes if note_id in rows]
    errors = sum(row["error"] for row in scored)
    all_errors = sum(row["error"] for row in rows.values())
    low, high = wilson_ci(errors, len(scored))
    return {"n": len(scored), "errors": errors,
            "rate": errors / len(scored) if scored else 0,
            "all_n": len(rows), "all_errors": all_errors,
            "low": low, "high": high,
            "outcomes": Counter(row["outcome"] for row in scored)}


def paired(rows_a, rows_b, notes):
    shared = [note_id for note_id in notes if note_id in rows_a and note_id in rows_b]
    a_only = sum(rows_a[n]["error"] and not rows_b[n]["error"] for n in shared)
    b_only = sum(rows_b[n]["error"] and not rows_a[n]["error"] for n in shared)
    return len(shared), a_only, b_only, mcnemar_exact(a_only, b_only)


def make_figure(stats, title, path):
    labels = [LABELS[arm] for arm in stats]
    values = [item["rate"] * 100 for item in stats.values()]
    lower = [(item["rate"] - item["low"]) * 100 for item in stats.values()]
    upper = [(item["high"] - item["rate"]) * 100 for item in stats.values()]
    fig, ax = plt.subplots(figsize=(7.5, 0.6 * len(labels) + 1.3))
    y = list(range(len(labels)))[::-1]
    ax.barh(y, values, color="#e87542", xerr=[lower, upper], capsize=3)
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Target-medication error rate (95% Wilson CI)")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.grid(axis="x", color="#dddddd")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def analyze_model(model, arms):
    notes = valid_notes(arms)
    control = arms.get(CONTROL, {})
    lines = [f"# Results: {model}\n",
             "These are controlled stress tests on MTSamples transcriptions with synthetic PLAN instructions. "
             "They do not estimate error prevalence in real discharge workflows.\n",
             f"The model listed the target in the continue control on **{len(notes)} / {len(control)}** notes. "
             "Error rates below use notes with a correct control response.\n",
             "## Error rates\n",
             "| Arm | Eligible n | Eligible errors | Eligible rate (95% CI) | All cases errors/n | Outcomes |",
             "|---|---:|---:|---:|---:|---|"]

    stats = {}
    for arm, label in LABELS.items():
        if arm not in arms:
            continue
        result = arm_stats(arms[arm], notes)
        stats[arm] = result
        outcomes = ", ".join(f"{key}: {value}" for key, value in result["outcomes"].most_common())
        lines.append(f"| {label} | {result['n']} | {result['errors']} | "
                     f"{result['rate']:.1%} ({result['low']:.1%}–{result['high']:.1%}) | "
                     f"{result['all_errors']}/{result['all_n']} | {outcomes} |")

    lines.append("\n## Paired comparisons (exact McNemar test)\n")
    lines.extend(["| Comparison | n | A only wrong | B only wrong | p |", "|---|---:|---:|---:|---:|"])
    comparisons = [
        ("Early vs late", ("discontinue", "early", "extract"), ("discontinue", "late", "extract")),
        ("Middle vs late", ("discontinue", "middle", "extract"), ("discontinue", "late", "extract")),
        ("Checklist prompt vs default", ("discontinue", "late", "extract_careful"), ("discontinue", "late", "extract")),
    ]
    for label, arm_a, arm_b in comparisons:
        if arm_a in arms and arm_b in arms:
            n, a_only, b_only, p = paired(arms[arm_a], arms[arm_b], notes)
            lines.append(f"| {label} | {n} | {a_only} | {b_only} | {p:.3g} |")

    control_rows = list(control.values())
    dose_rows = [row for row in control_rows if row.get("dose_error") is not None]
    dose_errors = sum(row["dose_error"] for row in dose_rows)
    lines.append("\n## Target dose and unit in the continue control\n")
    lines.append(
        f"Among {len(dose_rows)} controls where the target was listed and its dose could be scored, "
        f"{dose_errors} had a dose or unit mismatch. A missing target is counted in the medication "
        "status analysis instead. Frequency and the rest of the medication list are not scored.\n"
    )

    task = ("discontinue", "late", "extract")
    probe = ("discontinue", "late", "probe_stopped")
    if task in arms and probe in arms:
        failed = [n for n in notes if n in arms[task] and arms[task][n]["error"] and n in arms[probe]]
        knew = sum(not arms[probe][n]["error"] for n in failed)
        lines.append(f"\nOn {knew} of {len(failed)} failed late-plan cases with a probe result, "
                     "the model answered the direct stop question correctly.\n")

    lines.append("## Example errors\n")
    for arm in [("discontinue", "late", "extract"),
                ("discontinue", "early", "extract"),
                ("discontinue", "middle", "extract")]:
        for note_id, row in arms.get(arm, {}).items():
            if note_id in notes and row["error"]:
                lines.append(f"- `{note_id}` at {row['position']}: {row['outcome']}; "
                             f"inserted instruction: {row['added_sentence']}")
                break

    FIGURES_DIR.mkdir(exist_ok=True)
    plan_stats = {arm: result for arm, result in stats.items()
                  if arm in (CONTROL, ("discontinue", "late", "extract"))}
    position_stats = {arm: result for arm, result in stats.items()
                      if arm in [("discontinue", "early", "extract"),
                                 ("discontinue", "middle", "extract"),
                                 ("discontinue", "late", "extract")]}
    if len(plan_stats) > 1:
        make_figure(plan_stats, "Plan application: target should be removed", FIGURES_DIR / f"{model}_plan_application.png")
    if len(position_stats) > 1:
        make_figure(position_stats, "Position sensitivity: same instruction, different location", FIGURES_DIR / f"{model}_position_sensitivity.png")

    output = RESULTS_DIR / f"summary_{model}.md"
    output.write_text("\n".join(lines) + "\n")
    print(f"{model}: summary -> {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="only analyze this model tag")
    args = parser.parse_args()
    data = load_rows(args.model)
    if not data:
        print("No results found. Run src/run.py first.")
    for model, arms in data.items():
        analyze_model(model, arms)


if __name__ == "__main__":
    main()
