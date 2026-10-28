"""Summarize the failure-1 experiment (stop instruction) and draw its figure.

Usage:
    python src/analyze.py --model qwen2.5:3b [--experiment stop_instruction]

Reads results/<experiment>/<model>.jsonl and writes
results/summary_<experiment>_<model>.md and figures/<experiment>_<model>.png.
"""
import argparse
import json
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import FIGURES_DIR, RESULTS_DIR, fname
from stats import mcnemar_exact, wilson_ci

CONTROL = ("continue", "late", "extract")
PROBE = ("discontinue", "late", "probe_stopped")
MAIN = ("discontinue", "late", "extract")
LABELS = {
    CONTROL: "Control: 'Continue X' near end",
    MAIN: "'Discontinue X' near end (main case)",
    ("discontinue", "late", "extract_careful"): "Same + 'check for stops' reminder",
    ("discontinue", "late", "extract_twostep"): "Same, 2 steps: copy stop sentences, then list",
    ("continue", "late", "extract_alt"): "Reworded prompt: control",
    ("discontinue", "late", "extract_alt"): "Reworded prompt: 'Discontinue X' near end",
    ("discontinue", "early", "extract"): "'Discontinue X' near start",
    ("discontinue", "middle", "extract"): "'Discontinue X' in middle",
    ("discontinue", "after_meds", "extract"): "'Discontinue X' right after med list",
    ("discontinue", "inline", "extract"): "'Discontinue X' inside the med entry",
    ("stop", "late", "extract"): "'Stop X' near end",
    ("dc_abbrev", "late", "extract"): "'D/C X' near end",
    PROBE: "Direct question: 'still taking X?'",
}
ALLERGY_MAIN = ("allergy", "after_meds", "extract")
ALLERGY_PROBE = ("allergy", "after_meds", "probe_stopped")
ALLERGY_LABELS = {
    ("family", "after_meds", "extract"): "Control: 'Her husband takes X' (harmless mention)",
    ALLERGY_MAIN: "'ALLERGIES: X.' next to med list (main case)",
    ("allergy", "end", "extract"): "'ALLERGIES: X.' at end of note",
    ("allergy_explicit", "after_meds", "extract"): "'Allergic to X ... Do not give X' next to med list",
    ALLERGY_PROBE: "Direct question: 'should patient take X?'",
}
ALLERGY_COMPARISONS = [
    ("Allergy vs harmless mention", ALLERGY_MAIN, ("family", "after_meds", "extract")),
    ("Near med list vs end of note", ALLERGY_MAIN, ("allergy", "end", "extract")),
    ("Terse vs explicit wording", ALLERGY_MAIN, ("allergy_explicit", "after_meds", "extract")),
]
COMPARISONS = [  # (label, arm A, arm B); both arms run on the same notes
    ("Inside med entry vs near end", ("discontinue", "inline", "extract"), MAIN),
    ("Right after med list vs near end", ("discontinue", "after_meds", "extract"), MAIN),
    ("Near start vs near end", ("discontinue", "early", "extract"), MAIN),
    ("Middle vs near end", ("discontinue", "middle", "extract"), MAIN),
    ("Reminder prompt vs default", ("discontinue", "late", "extract_careful"), MAIN),
    ("Two-step prompt vs default", ("discontinue", "late", "extract_twostep"), MAIN),
    ("'Stop' vs 'Discontinue'", ("stop", "late", "extract"), MAIN),
    ("'D/C' vs 'Discontinue'", ("dc_abbrev", "late", "extract"), MAIN),
]


def load(experiment, model):
    arms = defaultdict(dict)
    for line in open(RESULTS_DIR / experiment / f"{fname(model)}.jsonl"):
        row = json.loads(line)
        arms[(row["condition"], row["position"], row["prompt"])][row["note_id"]] = row
    return arms


# Drugs named in the extraction prompt's format example. qwen2.5:3b sometimes copies
# them into lists (see example_leak), so results are also shown without these targets.
EXAMPLE_DRUGS = {"metoprolol", "aspirin"}


def without_example_drugs(rows, notes):
    return {n for n in notes if n in rows and rows[n]["target"]["generic"] not in EXAMPLE_DRUGS}


def listed_twice(note_ids):
    """Notes where the target drug (any of its names) appears with a dose more than once,
    e.g. an admission list and a discharge list. A stop instruction there is ambiguous."""
    import re
    from config import BASE_NOTES
    from drugs import ALIAS, find_alias
    from prepare_data import DOSE
    out = set()
    for n in map(json.loads, open(BASE_NOTES)):
        if n["note_id"] not in note_ids:
            continue
        g, text = n["target"]["generic"], n["text"]
        hits = [m.end() for a, gg in ALIAS.items() if gg == g for m in find_alias(a, text)]
        if sum(bool(DOSE.match(text[h:h + 15].lstrip(" ,"))) for h in hits) > 1:
            out.add(n["note_id"])
    return out


def rate(rows, notes):
    scored = [rows[n] for n in notes if n in rows]
    k = sum(r["error"] for r in scored)
    lo, hi = wilson_ci(k, len(scored))
    return {"n": len(scored), "k": k, "rate": k / len(scored) if scored else 0.0, "lo": lo, "hi": hi,
            "outcomes": Counter(r["outcome"] for r in scored)}


def paired(a, b, notes):
    shared = [n for n in notes if n in a and n in b]
    a_only = sum(a[n]["error"] and not b[n]["error"] for n in shared)
    b_only = sum(b[n]["error"] and not a[n]["error"] for n in shared)
    return len(shared), a_only, b_only, mcnemar_exact(a_only, b_only)


def figure(stats, model, path, labels=LABELS, control=CONTROL, main=MAIN, probe=PROBE,
           title="Failure 1: stop instruction not applied",
           xlabel="control: drug wrongly dropped; all other rows: stopped drug still on active list"):
    order = [arm for arm in labels if arm in stats and arm != probe]
    vals = [stats[a]["rate"] * 100 for a in order]
    err = [[(stats[a]["rate"] - stats[a]["lo"]) * 100 for a in order],
           [(stats[a]["hi"] - stats[a]["rate"]) * 100 for a in order]]
    colors = ["#8a8a8a" if a == control else "#c0392b" if a == main else "#e8a27c" for a in order]
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(order) + 1.6))
    y = list(range(len(order)))[::-1]
    ax.barh(y, vals, xerr=err, color=colors, capsize=3)
    for yi, a in zip(y, order):
        ax.text(min(stats[a]["hi"] * 100 + 2, 90), yi, f"{stats[a]['k']}/{stats[a]['n']}", va="center", fontsize=8)
    ax.set_yticks(y, [labels[a] for a in order], fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of notes wrong (bars: 95% Wilson CI)\n" + xlabel, fontsize=8)
    ax.set_title(f"{title} ({model})", loc="left", fontweight="bold", fontsize=10)
    ax.grid(axis="x", color="#e5e5e5")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--experiment", default="stop_instruction")
    args = ap.parse_args()
    if args.experiment == "allergy_leak":
        return analyze_allergy(args.model)
    if args.experiment in ("list_position", "list_position_noex"):
        return analyze_list_position(args.model, args.experiment)
    arms = load(args.experiment, args.model)
    control = arms[CONTROL]
    eligible = {n for n, r in control.items() if not r["error"]}

    out = [f"# {args.experiment}: {args.model}\n",
           "Real MTSamples notes with ONE synthetic plan sentence inserted. A controlled stress test, "
           "not a real-world prevalence estimate.\n",
           f"Notes run: {len(control)}. The control listed the target correctly on **{len(eligible)}**; "
           "rates below use those eligible notes (the model could find and list the drug).\n",
           "| Arm | Errors / eligible | Rate (95% CI) | Outcomes | Errors / all notes |",
           "|---|---:|---:|---|---:|"]
    stats = {}
    for arm, label in LABELS.items():
        if arm not in arms:
            continue
        s = stats[arm] = rate(arms[arm], eligible)
        full = rate(arms[arm], set(control))
        oc = ", ".join(f"{k}: {v}" for k, v in s["outcomes"].most_common())
        out.append(f"| {label} | {s['k']}/{s['n']} | {s['rate']:.0%} ({s['lo']:.0%}–{s['hi']:.0%}) | {oc} "
                   f"| {full['k']}/{full['n']} |")

    alt_c, alt_m = arms.get(("continue", "late", "extract_alt")), arms.get(("discontinue", "late", "extract_alt"))
    if alt_c and alt_m:
        alt_elig = {n for n, r in alt_c.items() if not r["error"]}
        a = rate(alt_m, alt_elig)
        out.append(f"\nRobustness, reworded prompt (own control as eligibility): control correct on {len(alt_elig)}/"
                   f"{len(alt_c)}; stopped drug still listed {a['k']}/{a['n']} = {a['rate']:.0%} "
                   f"({a['lo']:.0%}–{a['hi']:.0%}).")
    clean_ex = without_example_drugs(arms[MAIN], eligible)
    ex_main, ex_ctrl = rate(arms[MAIN], clean_ex), rate(arms[CONTROL], clean_ex)
    out.append(f"\nSensitivity: excluding targets named in the prompt example (metoprolol, aspirin): control "
               f"{ex_ctrl['k']}/{ex_ctrl['n']}, main case {ex_main['k']}/{ex_main['n']} = {ex_main['rate']:.0%} "
               f"({ex_main['lo']:.0%}–{ex_main['hi']:.0%}).")
    twice = listed_twice(eligible)
    clean = rate(arms[MAIN], eligible - twice)
    out.append(f"\nSensitivity: excluding {len(twice)} notes where the drug is listed with a dose twice "
               f"(e.g. admission and discharge lists), main-case rate = {clean['k']}/{clean['n']} = "
               f"{clean['rate']:.0%} ({clean['lo']:.0%}–{clean['hi']:.0%}).")
    out += ["\n## Paired comparisons on the same notes (exact McNemar test)\n",
            "| Comparison | Notes | Only A wrong | Only B wrong | p |", "|---|---:|---:|---:|---:|"]
    for label, a, b in COMPARISONS:
        if a in arms and b in arms:
            n, ao, bo, p = paired(arms[a], arms[b], eligible)
            out.append(f"| {label} | {n} | {ao} | {bo} | {p:.3g} |")

    probe = arms.get(PROBE, {})
    failed = sorted(n for n in eligible if n in arms[MAIN] and arms[MAIN][n]["error"] and n in probe)
    knew = [n for n in failed if not probe[n]["error"]]
    out.append(f"\n**Knows but does not apply:** of {len(failed)} notes where the stopped drug stayed on the "
               f"list, the model answered the direct question correctly ('no') on {len(knew)}.\n")
    two = arms.get(("discontinue", "late", "extract_twostep"), {})
    if two:
        from score import parse_json
        t_fail = [n for n in eligible if n in two and two[n]["error"]]
        quoted = [n for n in t_fail if two[n]["target"]["surface"].lower() in
                  " ".join(map(str, (parse_json(two[n]["raw_response"]) or {}).get("stop_instructions", []))).lower()]
        out.append(f"**Contradicts itself in one answer (two-step prompt, drug never named in the prompt):** of "
                   f"{len(t_fail)} two-step failures, the model copied the 'Discontinue X' sentence in step 1 and still "
                   f"listed X in step 2 on {len(quoted)}.\n")
    out.append("## Main-case errors (first 8)\n")
    for n in failed[:8]:
        r = arms[MAIN][n]
        out.append(f"- `{n}`: '{r['added_sentence']}' -> still listed; direct question answer: {probe[n]['outcome']}")
    (RESULTS_DIR / f"summary_{args.experiment}_{fname(args.model)}.md").write_text("\n".join(out) + "\n")
    FIGURES_DIR.mkdir(exist_ok=True)
    figure(stats, args.model, FIGURES_DIR / f"{args.experiment}_{fname(args.model)}.png")
    print("\n".join(out))


def natural_position(model):
    """[real] From unedited notes: is each lexicon drug in the med list omitted, by its place in the list?"""
    from config import BASE_NOTES
    from drugs import ALIAS, find_alias
    from perturb import split_med_list
    from prepare_data import find_med_section
    notes = {n["note_id"]: n for n in map(json.loads, open(BASE_NOTES))}
    by_third, by_length = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for line in open(RESULTS_DIR / "baseline" / f"{fname(model)}.jsonl"):
        r = json.loads(line)
        if r["outcome"] == "invalid_output":
            continue
        text = notes[r["note_id"]]["text"]
        _, start, end = find_med_section(text)
        _, entries, _ = split_med_list(text[start:end])
        if len(entries) < 3:
            continue
        size = "3-5" if len(entries) <= 5 else "6-10" if len(entries) <= 10 else "11+"
        seen = set()
        for i, entry in enumerate(entries):
            for alias, generic in ALIAS.items():
                if generic not in seen and any(find_alias(alias, entry)):
                    seen.add(generic)
                    third = ["first third", "middle third", "last third"][min(2, 3 * i // len(entries))]
                    dropped = generic in r["omitted"]
                    for table, key in ((by_third, third), (by_length, size)):
                        table[key][0] += dropped
                        table[key][1] += 1
    return by_third, by_length


def analyze_list_position(model, experiment="list_position"):
    arms = load(experiment, model)
    prompt = "extract_noex" if experiment.endswith("noex") else "extract"
    orig, first, last = (arms[("original", "none", prompt)], arms[("reorder", "first", prompt)],
                         arms[("reorder", "last", prompt)])
    notes = set(first) & set(last) & set(orig)
    out = [f"# {experiment}: {model} (prompt: {prompt})\n",
           "Real MTSamples notes. In the edited arms, the target drug's own entry is moved to the top or the "
           "bottom of the same medication list; nothing else changes. Error = target drug missing from the list.\n",
           "| Arm | Dropped / notes | Rate (95% CI) |", "|---|---:|---:|"]
    stats = {}
    for key, label, rows in (("first", "Target moved to TOP of list [synthetic edit]", first),
                             ("orig", "Target where the note put it [real]", orig),
                             ("last", "Target moved to BOTTOM of list [synthetic edit]", last)):
        st = stats[key] = rate(rows, notes)
        out.append(f"| {label} | {st['k']}/{st['n']} | {st['rate']:.0%} ({st['lo']:.0%}–{st['hi']:.0%}) |")
    clean = without_example_drugs(last, notes)
    n, ao, bo, p = paired(last, first, clean)
    out.append(f"\nSensitivity, excluding targets named in the prompt example: bottom {rate(last, clean)['k']}/{n}, "
               f"top {rate(first, clean)['k']}/{n}, only-bottom {ao} vs only-top {bo}, p = {p:.3g}.")
    out += ["\n| Paired comparison | Notes | Only A dropped | Only B dropped | p |", "|---|---:|---:|---:|---:|"]
    for label, a, b in (("Bottom vs top", last, first), ("Bottom vs original", last, orig),
                        ("Top vs original", first, orig)):
        n, ao, bo, p = paired(a, b, notes)
        out.append(f"| {label} | {n} | {ao} | {bo} | {p:.3g} |")

    has_baseline = (RESULTS_DIR / "baseline" / f"{fname(model)}.jsonl").exists()
    by_third, by_length = natural_position(model) if has_baseline and prompt == "extract" else (defaultdict(lambda: [0, 0]),) * 2
    out += ["\n## [real] Every lexicon drug in the unedited notes: omitted by place in list\n",
            "| Place in list | Omitted / drugs | Rate (95% CI) |", "|---|---:|---:|"]
    nat = {}
    for key in ("first third", "middle third", "last third"):
        k, n = by_third[key]
        lo, hi = wilson_ci(k, n)
        nat[key] = {"k": k, "n": n, "rate": k / n if n else 0, "lo": lo, "hi": hi}
        out.append(f"| {key} | {k}/{n} | {k / max(n, 1):.0%} ({lo:.0%}–{hi:.0%}) |")
    out += ["\n| List length (entries) | Omitted / drugs | Rate (95% CI) |", "|---|---:|---:|"]
    for key in ("3-5", "6-10", "11+"):
        k, n = by_length[key]
        lo, hi = wilson_ci(k, n)
        out.append(f"| {key} | {k}/{n} | {k / max(n, 1):.0%} ({lo:.0%}–{hi:.0%}) |")

    examples = sorted(n for n in notes if last[n]["error"] and not first[n]["error"])
    out.append(f"\n## Same drug kept at the top but dropped at the bottom ({len(examples)} notes)\n")
    out += [f"- `{n}`: {last[n]['target']['surface']}" for n in examples[:8]]
    (RESULTS_DIR / f"summary_{experiment}_{fname(model)}.md").write_text("\n".join(out) + "\n")

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [1, 1]})
    for ax, data, keys, labels, title in (
        (axes[0], stats, ["first", "orig", "last"], ["Moved to top", "Original place", "Moved to bottom"],
         "Same drug, same note, moved [synthetic edit]"),
        (axes[1], nat, ["first third", "middle third", "last third"], ["First third", "Middle third", "Last third"],
         "All lexicon drugs, unedited notes [real]")):
        vals = [data[k]["rate"] * 100 for k in keys]
        err = [[(data[k]["rate"] - data[k]["lo"]) * 100 for k in keys], [(data[k]["hi"] - data[k]["rate"]) * 100 for k in keys]]
        ax.bar(range(3), vals, yerr=err, capsize=4, color=["#7fb3d5", "#8a8a8a", "#c0392b"])
        for i, k in enumerate(keys):
            ax.text(i, data[k]["hi"] * 100 + 1.5, f"{data[k]['k']}/{data[k]['n']}", ha="center", fontsize=8)
        ax.set_xticks(range(3), labels, fontsize=9)
        ax.set_ylabel("% dropped from active list", fontsize=9)
        ax.set_ylim(0, max(60, max(data[k]["hi"] for k in keys) * 100 + 10))
        ax.set_title(title, fontsize=9, loc="left")
        ax.grid(axis="y", color="#e5e5e5")
        ax.set_axisbelow(True)
    fig.suptitle(f"Failure 2: the first drug in a medication list is silently dropped ({model})", x=0.01, ha="left",
                 fontweight="bold", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{experiment}_{fname(model)}.png", dpi=180)
    plt.close(fig)
    print("\n".join(out))


def analyze_allergy(model):
    arms = load("allergy_leak", model)
    notes = set(arms[ALLERGY_MAIN])
    out = [f"# allergy_leak: {model}\n",
           "Real MTSamples notes; the real allergy section is removed and ONE synthetic line naming a drug "
           "that appears nowhere else in the note is inserted. Error = that drug is on the active list "
           "(entries the model labels as an allergy or 'avoid' are not counted as active).\n",
           "| Arm | Errors / notes | Rate (95% CI) | Outcomes |", "|---|---:|---:|---|"]
    stats = {}
    for arm, label in ALLERGY_LABELS.items():
        if arm in arms:
            s = stats[arm] = rate(arms[arm], notes)
            oc = ", ".join(f"{k}: {v}" for k, v in s["outcomes"].most_common())
            out.append(f"| {label} | {s['k']}/{s['n']} | {s['rate']:.0%} ({s['lo']:.0%}–{s['hi']:.0%}) | {oc} |")
    out += ["\n## Paired comparisons on the same notes (exact McNemar test)\n",
            "| Comparison | Notes | Only A wrong | Only B wrong | p |", "|---|---:|---:|---:|---:|"]
    for label, a, b in ALLERGY_COMPARISONS:
        if a in arms and b in arms:
            n, ao, bo, p = paired(arms[a], arms[b], notes)
            out.append(f"| {label} | {n} | {ao} | {bo} | {p:.3g} |")
    probe = arms.get(ALLERGY_PROBE, {})
    failed = sorted(n for n in notes if arms[ALLERGY_MAIN][n]["error"] and n in probe)
    knew = [n for n in failed if not probe[n]["error"]]
    out.append(f"\n**Knows but does not apply:** of {len(failed)} notes where the allergen was put on the "
               f"active list, the model answered 'no' to 'should the patient take X?' on {len(knew)}.\n")
    two = arms.get(("discontinue", "late", "extract_twostep"), {})
    if two:
        from score import parse_json
        t_fail = [n for n in eligible if n in two and two[n]["error"]]
        quoted = [n for n in t_fail if two[n]["target"]["surface"].lower() in
                  " ".join(map(str, (parse_json(two[n]["raw_response"]) or {}).get("stop_instructions", []))).lower()]
        out.append(f"**Contradicts itself in one answer (two-step prompt, drug never named in the prompt):** of "
                   f"{len(t_fail)} two-step failures, the model copied the 'Discontinue X' sentence in step 1 and still "
                   f"listed X in step 2 on {len(quoted)}.\n")
    out.append("## Main-case errors (first 8)\n")
    for n in failed[:8]:
        r = arms[ALLERGY_MAIN][n]
        hit = [e["name"] for e in r.get("entries", []) if r["target"]["surface"].lower() in e["name"].lower()]
        out.append(f"- `{n}`: '{r['added_sentence']}' -> listed as {hit}; direct answer: {probe[n]['outcome']}")
    (RESULTS_DIR / f"summary_allergy_leak_{fname(model)}.md").write_text("\n".join(out) + "\n")
    figure(stats, model, FIGURES_DIR / f"allergy_leak_{fname(model)}.png", ALLERGY_LABELS,
           ("family", "after_meds", "extract"), ALLERGY_MAIN, ALLERGY_PROBE,
           "Failure 2: allergen put on active med list", "every row: the named drug wrongly on the active list")
    print("\n".join(out))


if __name__ == "__main__":
    main()
