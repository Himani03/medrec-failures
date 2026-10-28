"""Extra finding: does the model copy drugs from the prompt's format example into real lists?

Same 148 real notes, three prompts that differ only in the format example:
  extract       example "Lopressor 50 mg", "aspirin 81 mg"
  extract_swap  example "Lasix 40 mg", "Zocor 20 mg"
  extract_noex  no example
For each, count notes where the output contains a lexicon drug that appears
nowhere in the note (an invented drug), and which drugs those are.

Usage:
    python src/leak_report.py --model qwen2.5:3b
"""
import argparse
import json
from collections import Counter

from config import RESULTS_DIR, fname
from stats import mcnemar_exact, wilson_ci

PROMPTS = [("extract", "Example: Lopressor 50 mg, aspirin 81 mg"),
           ("extract_swap", "Example: Lasix 40 mg, Zocor 20 mg"),
           ("extract_noex", "No example")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    args = ap.parse_args()
    rows = {}
    for line in open(RESULTS_DIR / "example_leak" / f"{fname(args.model)}.jsonl"):
        r = json.loads(line)
        rows.setdefault(r["prompt"], {})[r["note_id"]] = r
    notes = set.intersection(*(set(v) for v in rows.values()))

    out = [f"# example_leak: {args.model}\n",
           "[real] 148 unedited MTSamples notes. Only the format example in the prompt changes. "
           "'Invented' = a lexicon drug in the output that appears nowhere in the note.\n",
           "| Prompt | Notes with an invented drug | Rate (95% CI) | Invented drugs (count) | Target drug missing |",
           "|---|---:|---:|---|---:|"]
    invented = {}
    for prompt, label in PROMPTS:
        rr = rows[prompt]
        inv = {n: [e["generic"] for e in rr[n]["extras"] if e["generic"] and e["where"] == "not_in_note"]
               for n in notes}
        invented[prompt] = {n for n, v in inv.items() if v}
        k = len(invented[prompt])
        lo, hi = wilson_ci(k, len(notes))
        drugs = Counter(g for v in inv.values() for g in set(v)).most_common(5)
        missing = sum(rr[n]["error"] for n in notes)
        out.append(f"| {label} | {k}/{len(notes)} | {k / len(notes):.0%} ({lo:.0%}–{hi:.0%}) | "
                   f"{', '.join(f'{g} ({c})' for g, c in drugs) or 'none'} | {missing}/{len(notes)} |")
    a, b = invented["extract"], invented["extract_noex"]
    out.append(f"\nPaired, default example vs no example: invented only with example {len(a - b)}, "
               f"only without {len(b - a)}, exact McNemar p = {mcnemar_exact(len(a - b), len(b - a)):.3g}.")
    (RESULTS_DIR / f"summary_example_leak_{fname(args.model)}.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
