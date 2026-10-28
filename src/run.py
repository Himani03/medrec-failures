"""Step 3: run an experiment against a model and save scored results.

Examples:
    python src/run.py --experiment discovery --provider mock
    python src/run.py --experiment plan_application --provider gemini --model gemini-3.8-flash
    python src/run.py --experiment position_sensitivity --provider ollama --model LOCAL_MODEL
    python src/run.py --experiment discovery --provider mock      # no API key needed

Results go to results/<experiment>/<model_tag>.jsonl (one row per test case).
Responses are cached, so rerunning an identical prompt reuses its response.
"""
import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor

from config import BASE_NOTES, DEFAULT_MODEL, DEFAULT_PROVIDER, RESULTS_DIR, SEED, fname
from experiments import EXPERIMENTS
from llm import call_model
from perturb import build_case, move_target
from prompts import render
from score import score


def load_notes(n: int, longest: bool = False):
    """Select a reproducible sample, optionally from the longest source notes."""
    notes = [json.loads(line) for line in open(BASE_NOTES)]
    if longest:
        return sorted(notes, key=lambda note: note["n_chars"], reverse=True)[:n]
    random.Random(SEED).shuffle(notes)
    return notes[:n]


def model_tag(provider, model):
    tag = model if provider != "mock" else "mock"
    return tag


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--experiment", required=True, choices=EXPERIMENTS)
    ap.add_argument("--provider", default=DEFAULT_PROVIDER,
                    choices=["gemini", "openai", "anthropic", "ollama", "mock"])
    ap.add_argument("--tag", help="name for the results file, e.g. a rerun (default: model name)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--n", type=int, help="number of base notes (default: set per experiment)")
    ap.add_argument("--rpm", type=float, default=0,
                    help="maximum requests per minute per worker; 0 = no limit")
    ap.add_argument("--workers", type=int, default=1,
                    help="number of parallel requests")
    args = ap.parse_args()

    exp = EXPERIMENTS[args.experiment]
    notes = load_notes(args.n or exp["n_notes"], longest=args.experiment == "position_sensitivity")
    if any(arm[0] == "reorder" for arm in exp["arms"]):
        notes = [n for n in notes if move_target(n, "first")]  # list must split cleanly
    tag = args.tag or model_tag(args.provider, args.model)
    min_interval = 60 / args.rpm if args.rpm else 0

    out_dir = RESULTS_DIR / args.experiment
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{fname(tag)}.jsonl"

    total = len(notes) * len(exp["arms"])
    print(f"{args.experiment}: {exp['description']}")
    print(f"model={tag}  notes={len(notes)}  arms={len(exp['arms'])}  calls={total}\n")

    # One job per (note, arm), note by note, so a partial run still gives
    # complete paired sets. Interrupted runs resume from the cache.
    jobs = [(build_case(note, condition, position), prompt_name)
            for note in notes for condition, position, prompt_name in exp["arms"]]

    def run_job(job):
        case, prompt_name = job
        raw = call_model(render(prompt_name, case), args.provider, args.model,
                         None, min_interval)
        return {
            "experiment": args.experiment, "model": tag, "prompt": prompt_name,
            **{k: v for k, v in case.items() if k != "text"},
            **score(case, raw, prompt_name), "raw_response": raw,
        }

    # Run jobs in parallel threads; results come back in the original order.
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, row in enumerate(pool.map(run_job, jobs), start=1):
            rows.append(row)
            if i % 25 == 0 or i == total:
                print(f"  {i}/{total} calls done")

    # Per-arm summary in the terminal.
    print()
    for condition, position, prompt_name in exp["arms"]:
        arm_rows = [r for r in rows if (r["condition"], r["position"], r["prompt"])
                    == (condition, position, prompt_name)]
        errors = sum(r["error"] for r in arm_rows)
        print(f"  {condition:>14} @ {position:<8} [{prompt_name:<15}] errors {errors}/{len(arm_rows)}")

    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"\nSaved {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
