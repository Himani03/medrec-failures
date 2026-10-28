"""Insert one controlled medication instruction into a source transcription."""
import hashlib
import re


SENTENCES = {
    "continue": "Continue {drug} at the current dose.",
    "discontinue": "Discontinue {drug}.",
    "stop": "Stop {drug}.",                 # phrasing variant
    "dc_abbrev": "D/C {drug}.",             # common clinical abbreviation
}
EXPECTED = {"reorder": "listed", "allergy": "removed", "allergy_explicit": "removed", "family": "removed",
            "original": "listed", "continue": "listed", "discontinue": "removed",
            "stop": "removed", "dc_abbrev": "removed"}
POSITION_FRACTIONS = {"early": 0.1, "middle": 0.5, "late": 0.9}


def make_sentence(condition: str, target: dict) -> str:
    return SENTENCES[condition].format(drug=target["surface"])


def insert_sentence(text: str, sentence: str, position: str) -> str:
    """Place the same PLAN sentence at an early, middle, or late paragraph."""
    if position not in POSITION_FRACTIONS:
        raise ValueError(f"unknown position: {position}")

    target = round(len(text) * POSITION_FRACTIONS[position])
    breaks = [match.end() for match in re.finditer(r"\n+", text)]
    if not breaks:
        breaks = [match.end() for match in re.finditer(r"\s+", text)]
    cut = min(breaks, key=lambda point: abs(point - target)) if breaks else target
    return text[:cut].rstrip() + "\n\nPLAN: " + sentence + "\n\n" + text[cut:].lstrip()


def insert_near_target(note: dict, sentence: str, where: str) -> str:
    """Place the instruction next to the drug instead of at a fraction of the note.
    after_meds: its own paragraph right after the medication section ends.
    inline:     directly after the target's entry inside the medication section."""
    text = note["text"]
    if where == "after_meds":
        cut = note["med_section_end"]
        return text[:cut].rstrip() + "\n\nPLAN: " + sentence + "\n\n" + text[cut:].lstrip()
    # find the entry start inside the medication section, then the end of that entry
    med_start = text.rfind(note["med_header"], 0, note["med_section_end"])
    start = text.lower().find(note["target"]["surface"].lower(), med_start)
    stop = re.search(r"[,;\n]|\.(\s|$)", text[start + len(note["target"]["surface"]):])
    cut = start + len(note["target"]["surface"]) + (stop.start() if stop else 0)
    return text[:cut] + " (PLAN: " + sentence + ")" + text[cut:]


# Failure 2 probe: a drug the patient must NOT take is named only outside the med list.
ALLERGENS = ["penicillin", "amoxicillin", "codeine", "morphine", "lisinopril",
             "ciprofloxacin", "cephalexin", "ibuprofen", "Bactrim", "naproxen"]
MENTIONS = {
    "allergy": "ALLERGIES: {drug}.",                                        # terse, as notes usually write it
    "allergy_explicit": "ALLERGIES: The patient is allergic to {drug}, which causes hives. Do not give {drug}.",
    "family": "FAMILY HISTORY: Her husband takes {drug}.",                   # same drug, harmless role
}
ALLERGY_SECTION = re.compile(r"(?:^|\n\n)ALLERG[A-Z /]*:.*?(?=\n\n[A-Z][A-Z0-9 /&\-\(\)]{2,60}:|\Z)", re.DOTALL)


def pick_allergen(note: dict) -> str:
    """Deterministic per note: an allergen not already mentioned anywhere in it."""
    from drugs import ALIAS, find_alias
    text = note["text"].lower()

    def named(drug):  # the drug or any of its brand names, as a whole word
        generic = ALIAS.get(drug.lower(), drug.lower())
        return any(any(find_alias(a, text)) for a, g in list(ALIAS.items()) + [(drug.lower(), generic)] if g == generic)
    pool = [d for d in ALLERGENS if not named(d)]
    return pool[int(hashlib.md5(note["note_id"].encode()).hexdigest(), 16) % len(pool)]


def mention_case_text(note: dict, condition: str, position: str):
    drug = pick_allergen(note)
    text = ALLERGY_SECTION.sub("", note["text"])           # drop the real allergy section
    line = MENTIONS[condition].format(drug=drug)
    if position == "after_meds":
        med_start = text.find(note["med_header"])
        nxt = re.search(r"\n\n[A-Z][A-Z0-9 /&\-\(\)]{2,60}:", text[med_start + len(note["med_header"]) + 1:])
        cut = med_start + len(note["med_header"]) + 1 + nxt.start() if nxt else len(text)
    else:  # "end"
        cut = len(text)
    return drug, text[:cut].rstrip() + "\n\n" + line + "\n\n" + text[cut:].lstrip()


# Failure 2: does a drug's place in the medication list decide whether it is dropped?
NUMBERED = re.compile(r"(?:^|\n)\s*\d+\.\s")
LEAD_IN = re.compile(r"^\s*(?:(?:include,\s*|(?:his|her|the patient's)?\s*medications?\s*(?:include|are)?:?,?\s*)?)",
                     re.IGNORECASE)


def split_med_list(body: str):
    """Split a medication section body into (lead_in, entries, numbered)."""
    if NUMBERED.search(body):
        first = re.search(r"\b1\.\s", body)
        lead, rest = (body[:first.start()].strip() + " ", body[first.start():]) if first else ("", body)
        parts = re.split(r"\n\s*(?=\d+\.\s)", rest.strip())
        return lead.lstrip(), [re.sub(r"^\d+\.\s*", "", e).strip() for e in parts if e.strip()], True
    lead = LEAD_IN.match(body).group(0)
    rest = body[len(lead):].strip().rstrip(".")
    return lead, [e.strip() for e in re.split(r",\s*(?:and\s+)?|;\s*", rest) if e.strip()], False


def move_target(note: dict, where: str):
    """Move the target's entry to the first or last place in its medication list.
    Returns None when the list cannot be split cleanly (those notes are skipped)."""
    from prepare_data import find_med_section
    _, start, end = find_med_section(note["text"])
    body = note["text"][start:end]
    lead, entries, numbered = split_med_list(body)
    surface, dose = note["target"]["surface"].lower(), note["target"]["dose_value"]
    hits = [i for i, e in enumerate(entries) if surface in e.lower()]
    if len(entries) < 3 or len(hits) != 1 or dose not in entries[hits[0]]:
        return None
    entry = entries.pop(hits[0])
    entries = [entry] + entries if where == "first" else entries + [entry]
    if numbered:
        new = " " + lead + "\n".join(f"{i}. {e}" for i, e in enumerate(entries, 1))
    else:
        new = " " + lead + ", ".join(entries[:-1]) + ", and " + entries[-1] + "."
    return note["text"][:start] + new + "\n\n" + note["text"][end:].lstrip()


def build_case(note: dict, condition: str, position: str = "late") -> dict:
    target = note["target"]
    if condition == "original":  # the real note, unchanged
        sentence, text = "", note["text"]
    elif condition == "reorder":
        sentence, text = f"(target moved to {position} of med list)", move_target(note, position)
    elif condition in MENTIONS:
        drug, text = mention_case_text(note, condition, position)
        sentence = MENTIONS[condition].format(drug=drug)
        target = {"generic": drug.lower(), "surface": drug, "dose_value": "", "dose_unit": ""}
    elif position in ("after_meds", "inline"):
        sentence = make_sentence(condition, note["target"])
        text = insert_near_target(note, sentence, position)
    else:
        sentence = make_sentence(condition, note["target"])
        text = insert_sentence(note["text"], sentence, position)
    return {
        "case_id": f"{note['note_id']}__{condition}__{position}",
        "note_id": note["note_id"],
        "condition": condition,
        "position": position,
        "expected": EXPECTED[condition],
        "added_sentence": sentence,
        "target": target,
        "position_fraction": POSITION_FRACTIONS.get(position),
        "n_chars": len(text),
        "text": text,
    }
