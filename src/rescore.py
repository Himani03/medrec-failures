"""Re-score saved runs with the current scorer, without calling any model.

Every result row keeps the model's raw response, so when the scorer changes
we rebuild each case from the source note and score the raw text again.

Usage:
    python src/rescore.py            # all experiments, all models
"""
import json

from config import BASE_NOTES, RESULTS_DIR
from perturb import build_case
from score import score


def main():
    notes = {n["note_id"]: n for n in map(json.loads, open(BASE_NOTES))}
    for path in sorted(RESULTS_DIR.glob("*/*.jsonl")):
        if path.parent.name == "cache":
            continue
        rows = [json.loads(line) for line in path.open()]
        for row in rows:
            note = notes.get(row["note_id"])
            if note is None:
                continue
            case = build_case(note, row["condition"], row["position"])
            row.update(score(case, row["raw_response"], row["prompt"]))
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        print(f"rescored {len(rows):4d} rows  {path.relative_to(RESULTS_DIR)}")


if __name__ == "__main__":
    main()
