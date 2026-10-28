"""Step 1: build the pool of source transcription samples from MTSamples.

For every unique transcription we:
  1. restore line breaks (the Kaggle CSV encodes them as commas),
  2. find the medication section (e.g. "MEDICATIONS:", "DISCHARGE MEDICATIONS:"),
  3. find drugs from our lexicon that are written WITH a dose in that section,
  4. pick ONE target drug per note at random (seeded).

One target per note means every test pair later comes from a different real
note, so the pairs are statistically independent.

Usage:
    python src/prepare_data.py
Output:
    data/base_notes.jsonl   (one JSON object per usable note)
"""
import json
import random
import re
from collections import Counter

import pandas as pd

from config import BASE_NOTES, RAW_CSV, SEED
from drugs import ALIAS, find_alias

# Medication section headers, most specific first.
MED_HEADERS = [
    "DISCHARGE MEDICATIONS", "CURRENT MEDICATIONS", "HOME MEDICATIONS",
    "MEDICATIONS AT HOME", "OUTPATIENT MEDICATIONS", "MEDICATIONS", "MEDICATION",
]

SECTION_HEADER = re.compile(r"(?:^|\n\n)([A-Z][A-Z0-9 /&\-\(\)]{2,60}):")
DOSE = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|units?|meq|ml)\b", re.IGNORECASE)
ALREADY_STOPPED = re.compile(
    r"\b(hold|held|discontinu\w*|stop\w*|d/c|dc'd|cease\w*)\b", re.IGNORECASE
)
MAX_NOTE_CHARS = 12_000


# ---------------------------------------------------------------- cleaning --

def clean_text(raw: str) -> str:
    """Turn the comma-encoded CSV text back into readable sections."""
    text = str(raw)
    text = re.sub(r",\s*([A-Z][A-Z0-9 /&\-\(\)]{2,60}:)", r"\n\n\1", text)  # new section
    text = re.sub(r":\s*,+\s*", ": ", text)       # "HEADER: , body" -> "HEADER: body"
    text = re.sub(r",{2,}", "\n", text)           # ",," was a line break
    text = re.sub(r"\.,(?=\S)", ".\n", text)      # ".," was a line break
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def find_med_section(text: str):
    """Return (header, body_start, body_end) of the medication section, or None."""
    headers = [(m.group(1).strip(), m.start(1), m.end()) for m in SECTION_HEADER.finditer(text)]
    spans = {}
    for i, (name, _, body_start) in enumerate(headers):
        body_end = headers[i + 1][1] if i + 1 < len(headers) else len(text)
        spans.setdefault(name, (body_start, body_end))

    for name in MED_HEADERS:
        if name in spans:
            return (name, *spans[name])
    return None


# -------------------------------------------------------- target selection --

def dosed_drugs(section: str):
    """Drugs from the lexicon that are followed by a dose (e.g. '25 mg')
    within 40 characters, one entry per generic drug."""
    found = {}
    for alias, generic in ALIAS.items():
        for match in find_alias(alias, section):
            after = section[match.end(): match.end() + 40]
            dose = DOSE.search(after)
            if not dose or re.search(r"[;\n]", after[: dose.start()]):
                continue
            candidate = {
                "generic": generic,
                "surface": section[match.start(): match.end()],  # as written in note
                "dose_value": dose.group(1),
                "dose_unit": dose.group(2).lower(),
                "position": match.start(),
            }
            if generic not in found or candidate["position"] < found[generic]["position"]:
                found[generic] = candidate
    return sorted(found.values(), key=lambda c: c["position"])


def already_stopped_somewhere(text: str, surface: str) -> bool:
    """True if any sentence mentioning the drug already says hold/stop."""
    sentences = re.findall(r"[^.\n]*" + re.escape(surface) + r"[^.\n]*", text, re.IGNORECASE)
    return any(ALREADY_STOPPED.search(s) for s in sentences)


# -------------------------------------------------------------------- main --

def build_base_notes():
    rng = random.Random(SEED)
    df = pd.read_csv(RAW_CSV).dropna(subset=["transcription"])
    df = df.drop_duplicates(subset=["transcription"])

    notes, skipped = [], Counter()
    for idx, row in df.iterrows():
        text = clean_text(row["transcription"])
        if len(text) > MAX_NOTE_CHARS:
            skipped["too long"] += 1
            continue

        section = find_med_section(text)
        if section is None:
            skipped["no medication section"] += 1
            continue
        header, start, end = section

        drugs = dosed_drugs(text[start:end])
        if len(drugs) < 2:
            skipped["fewer than 2 dosed drugs"] += 1
            continue

        candidates = [d for d in drugs if not already_stopped_somewhere(text, d["surface"])]
        if not candidates:
            skipped["all drugs already stopped in note"] += 1
            continue

        target = rng.choice(candidates)
        notes.append({
            "note_id": f"mts_{idx}",
            "specialty": str(row["medical_specialty"]).strip(),
            "sample_name": str(row["sample_name"]).strip(),
            "text": text,
            "n_chars": len(text),
            "med_header": header,
            "med_section_end": end,
            "meds_in_section": [d["generic"] for d in drugs],
            "target": {k: target[k] for k in ("generic", "surface", "dose_value", "dose_unit")},
        })

    BASE_NOTES.parent.mkdir(parents=True, exist_ok=True)
    with open(BASE_NOTES, "w") as f:
        for note in notes:
            f.write(json.dumps(note) + "\n")

    print(f"Unique transcriptions: {len(df)}")
    print(f"Usable base notes:     {len(notes)}  -> {BASE_NOTES}")
    for reason, count in skipped.most_common():
        print(f"  skipped ({reason}): {count}")


if __name__ == "__main__":
    build_base_notes()
