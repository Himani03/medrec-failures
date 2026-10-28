"""Make a hand-review sheet: a random sample of scored cases, errors and non-errors.

The reviewer sees the inserted sentence, the target, the model's raw answer
and the automatic label, and records whether the label is right. Agreement
between the automatic label and the reviewer is reported in the write-up.

Usage:
    python src/review_sample.py --experiment stop_instruction --model qwen2.5:3b --per-arm 6
Output:
    review/<experiment>_<model>.csv
"""
import argparse
import csv
import json
import random

from config import ROOT, RESULTS_DIR, SEED, fname


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--per-arm", type=int, default=6, help="cases per arm (half errors, half not, when possible)")
    args = ap.parse_args()
    rows = [json.loads(line) for line in open(RESULTS_DIR / args.experiment / f"{fname(args.model)}.jsonl")]
    rng = random.Random(SEED)

    by_arm = {}
    for r in rows:
        by_arm.setdefault((r["condition"], r["position"], r["prompt"]), []).append(r)
    picked = []
    for arm, arm_rows in sorted(by_arm.items()):
        errors = [r for r in arm_rows if r["error"]]
        fine = [r for r in arm_rows if not r["error"]]
        k = min(len(errors), args.per_arm // 2)
        picked += rng.sample(errors, k) + rng.sample(fine, min(len(fine), args.per_arm - k))

    out = ROOT / "review" / f"{args.experiment}_{fname(args.model)}.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["note_id", "arm", "target", "inserted_sentence", "model_raw_answer",
                    "auto_outcome", "auto_error", "reviewer_agrees (y/n)", "reviewer_note"])
        for r in picked:
            w.writerow([r["note_id"], f"{r['condition']}/{r['position']}/{r['prompt']}", r["target"]["surface"],
                        r["added_sentence"], r["raw_response"], r["outcome"], r["error"], "", ""])
    print(f"{len(picked)} cases -> {out}")


if __name__ == "__main__":
    main()
