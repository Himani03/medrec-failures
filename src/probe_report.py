"""Broad probe report: what goes wrong when the model lists meds from REAL notes?

Reads results/baseline/<model>.jsonl (unchanged MTSamples notes, no synthetic
edits) and counts every kind of list error the whole-list scorer can see.

Usage:
    python src/probe_report.py --model qwen2.5:7b
"""
import argparse
import json
from collections import Counter

import re

from config import BASE_NOTES, RESULTS_DIR, fname
from listscore import sections
from stats import wilson_ci

NOT_DRUGS = set("""no known drug drugs allergies allergy allergic none nkda denies denied patient states
causes caused cause rash hives itching swelling throat unknown reaction intolerance medications
medication which with that have also seafood shellfish shrimp latex tape adhesive adhesives dye iodine
contrast nausea vomiting multiple over counter higher doses this when kidneys x-rays sea food
she he his her the and to of are is has had was were on in at for""".split())


def real_allergens(text):
    """Drug-like words in the note's ALLERGIES section (screening; hits are hand-checked)."""
    words = set()
    for name, start, end in sections(text):
        if "ALLERG" in name:
            words |= {w for w in re.findall(r"[a-z][a-z\-]{3,}", text[start:end].lower()) if w not in NOT_DRUGS}
    return words


def pct(k, n):
    lo, hi = wilson_ci(k, n)
    return f"{k}/{n} = {k / n:.0%} (95% CI {lo:.0%}–{hi:.0%})" if n else "0/0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    args = ap.parse_args()
    rows = [json.loads(line) for line in open(RESULTS_DIR / "baseline" / f"{fname(args.model)}.jsonl")]
    valid = [r for r in rows if r["outcome"] != "invalid_output"]

    where = Counter()
    notes_with = Counter()
    examples = {}
    for r in valid:
        seen = set()
        for e in r["extras"]:
            kind = e["where"].split(":")[0] if not e["where"].startswith("other:") else e["where"]
            where[kind] += 1
            seen.add(kind)
            examples.setdefault(kind, []).append((r["note_id"], e["name"]))
        for kind in seen:
            notes_with[kind] += 1

    n = len(valid)
    lines = [f"# Broad probe on real notes: {args.model}\n",
             f"Notes: {len(rows)}, valid JSON: {len(valid)}.\n",
             f"- Target drug (picked from the medication section) missing: "
             f"{pct(sum(r['outcome'] != 'listed' for r in valid), n)}",
             f"- Notes with at least one lexicon drug omitted: {pct(sum(bool(r['omitted']) for r in valid), n)}",
             f"- Notes with at least one extra drug (not from the medication section): "
             f"{pct(sum(bool(r['extras']) for r in valid), n)}\n",
             "## Where extra drugs came from\n",
             "| Source of extra drug | Entries | Notes affected | Examples |", "|---|---:|---:|---|"]
    for kind, count in where.most_common():
        ex = "; ".join(f"{name} ({nid})" for nid, name in examples[kind][:4])
        lines.append(f"| {kind} | {count} | {notes_with[kind]} | {ex} |")
    notes = {n["note_id"]: n for n in map(json.loads, open(BASE_NOTES))}
    with_allergy, leaks = 0, []
    for r in valid:
        allergens = real_allergens(notes[r["note_id"]]["text"])
        if not allergens:
            continue
        with_allergy += 1
        hit = [e["name"] for e in r["entries"] if not e["marked_stopped"]
               and set(re.findall(r"[a-z][a-z\-]{3,}", e["name"].lower())) & allergens]
        if hit:
            leaks.append((r["note_id"], hit))
    lines += ["\n## Real allergies: does an allergen appear on the active list? (real notes, no edits)\n",
              f"Notes with a drug-like word in ALLERGIES: {with_allergy}. "
              f"Allergen on active list: {pct(len(leaks), with_allergy)}.\n"]
    lines += [f"- `{nid}`: {', '.join(h)}" for nid, h in leaks]
    out = RESULTS_DIR / f"probe_{fname(args.model)}.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
