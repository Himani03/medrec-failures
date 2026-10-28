"""Score whether the model keeps or removes the one target medication."""
import json
import re

from drugs import canonical
from listscore import marked_stopped, score_list


DOSE_PATTERN = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>mcg|μg|ug|mg|g|units?|meq|ml)\b",
    re.IGNORECASE,
)


def parse_json(raw: str):
    """Parse JSON output, including a response wrapped in a code fence."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def as_entries(medications: list):
    """Accept either compact strings ("Lopressor 50 mg") or dicts with a name."""
    return [{"name": m, "raw": m} if isinstance(m, str) else m for m in medications]


def find_target(medications: list, target: dict):
    for medication in medications:
        if not isinstance(medication, dict):
            continue
        name = str(medication.get("name", ""))
        if canonical(name) == target["generic"] or target["surface"].lower() in name.lower():
            return medication
    return None


def normalize_dose(value, unit=""):
    """Return a comparable (amount, unit) pair, or None if dose is unknown."""
    text = str(value or "").strip()
    unit = str(unit or "").strip()
    match = DOSE_PATTERN.search(text)
    if match:
        text = match.group("value")
        unit = match.group("unit")
    if not re.fullmatch(r"\d+(?:\.\d+)?", text) or not unit:
        return None

    amount = float(text)
    normalized_unit = unit.lower().replace("μ", "u")
    if normalized_unit in {"ug", "mcg"}:
        return (amount / 1000, "mg")
    if normalized_unit == "g":
        return (amount * 1000, "mg")
    if normalized_unit in {"unit", "units"}:
        normalized_unit = "unit"
    elif normalized_unit in {"ml", "meq", "mg"}:
        pass
    else:
        return None
    return (amount, normalized_unit)


def reported_dose(entry):
    """Read dose fields, with a fallback for models that put dose in the name."""
    dose = entry.get("dose", "")
    unit = entry.get("unit", "")
    if not dose:
        match = DOSE_PATTERN.search(str(entry.get("name", "")))
        if match:
            dose, unit = match.group("value"), match.group("unit")
    elif not unit:
        match = DOSE_PATTERN.search(str(dose))
        if match:
            dose, unit = match.group("value"), match.group("unit")
    return dose, unit


def score_extraction(case: dict, raw: str) -> dict:
    parsed = parse_json(raw)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("medications"), list):
        return {"outcome": "invalid_output", "error": True, "entries": [], "extras": [], "omitted": [],
                "n_returned": 0, "dose_error": None, "reported_dose": None, "reported_unit": None}

    parsed["medications"] = as_entries(parsed["medications"])
    entry = find_target(parsed["medications"], case["target"])
    # A drug returned but annotated "discontinued"/"held" is not on the ACTIVE list.
    stopped_note = entry is not None and marked_stopped(entry)
    listed = entry is not None and not stopped_note
    if case["expected"] == "listed":
        outcome, error = ("listed", False) if listed else (
            ("marked_stopped", True) if stopped_note else ("dropped", True))
    else:
        outcome, error = ("still_listed", True) if listed else (
            ("marked_stopped", False) if stopped_note else ("removed", False))
    dose_error = None
    dose, unit = reported_dose(entry) if entry else (None, None)
    if case["expected"] == "listed" and entry:
        expected = normalize_dose(case["target"]["dose_value"], case["target"]["dose_unit"])
        reported = normalize_dose(dose, unit)
        dose_error = expected is None or reported != expected
    whole = score_list(case["text"], parsed["medications"])
    return {
        "outcome": outcome,
        "error": error,
        "n_returned": len(whole["entries"]),
        "entries": whole["entries"],
        "extras": whole["extras"],
        "omitted": whole["omitted"],
        "dose_error": dose_error,
        "reported_dose": dose,
        "reported_unit": unit,
    }


def score_probe(case: dict, raw: str, prompt_name: str) -> dict:
    parsed = parse_json(raw) or {}
    answer = str(parsed.get("answer", "")).lower().strip()
    correct = answer == "no"
    return {"outcome": answer or "invalid_output", "error": not correct, "reported_dose": None}


def score(case: dict, raw: str, prompt_name: str) -> dict:
    if prompt_name.startswith("probe"):
        return score_probe(case, raw, prompt_name)
    return score_extraction(case, raw)
