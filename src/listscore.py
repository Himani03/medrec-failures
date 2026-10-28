"""Whole-list scoring: compare EVERY drug the model returned against the note.

The target scorer (score.py) only asks "is the one target drug there?". That
misses the other way a list can be wrong: drugs the model ADDS. This module
looks at each returned entry and asks where in the note it came from.

For each returned medication we record one of:
  med_section     the name appears in the note's medication section (expected)
  other:<SECTION> the name appears only in another section, e.g. other:ALLERGIES
  not_in_note     the name appears nowhere in the note (invented)

We also count omissions: lexicon drugs in the medication section that the
model left out. Drug names outside the small lexicon are matched by their
first word, so this is a screening tool, and flagged cases are reviewed by hand.
"""
import re

from drugs import ALIAS, canonical, find_alias
from prepare_data import SECTION_HEADER, find_med_section

# Words showing the model kept a drug only as inactive (stopped, held, or an allergy).
STOP_WORDS = re.compile(r"\b(discontinu\w*|stop\w*|held|hold|d/c|dc'?d|ceased?|allerg\w*|avoid\w*)\b", re.IGNORECASE)
GENERIC_WORDS = {"vitamin", "multivitamin", "baby", "enteric", "coated", "extended", "release",
                 "tablet", "tablets", "oral", "daily", "the", "of", "and", "with", "iv", "po"}


def sections(text: str):
    """List of (header, start, end) for every ALL-CAPS section in the note."""
    heads = [(m.group(1).strip(), m.start(1), m.end()) for m in SECTION_HEADER.finditer(text)]
    out = []
    for i, (name, start, _) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else len(text)
        out.append((name, start, end))
    return out


def section_at(text: str, pos: int):
    for name, start, end in sections(text):
        if start <= pos < end:
            return name
    return "PREAMBLE"


def name_keys(name: str):
    """Search keys for a returned drug name: its lexicon aliases if known,
    otherwise its first meaningful word (e.g. 'Milk of Magnesia' -> 'milk')."""
    generic = canonical(name)
    if generic:
        return generic, [a for a, g in ALIAS.items() if g == generic]
    words = [w for w in re.findall(r"[a-z][a-z\-]{2,}", name.lower()) if w not in GENERIC_WORDS]
    return None, words[:1]


def locate(text: str, keys, med_span):
    """Where do the keys occur in the note? Returns 'med_section',
    'other:<SECTION>' (first hit outside the med section), or 'not_in_note'."""
    hits = [m.start() for k in keys for m in find_alias(k, text)]
    if not hits:
        return "not_in_note"
    if med_span and any(med_span[0] <= h < med_span[1] for h in hits):
        return "med_section"
    return "other:" + section_at(text, min(hits))


def marked_stopped(entry: dict) -> bool:
    """The model kept the drug but annotated it as stopped (e.g. frequency='discontinued')."""
    return any(STOP_WORDS.search(str(v)) for k, v in entry.items() if k != "name")


def score_list(note_text: str, medications: list):
    med = find_med_section(note_text)
    med_span = (med[1], med[2]) if med else None
    med_text = note_text[med_span[0]:med_span[1]] if med_span else ""
    expected = {g for a, g in ALIAS.items() if any(find_alias(a, med_text))}

    entries, returned_generics = [], set()
    for m in medications:
        if not isinstance(m, dict) or not str(m.get("name", "")).strip():
            continue
        name = str(m["name"]).strip()
        generic, keys = name_keys(name)
        where = locate(note_text, keys, med_span) if keys else "not_in_note"
        if generic:
            returned_generics.add(generic)
        entries.append({"name": name, "generic": generic, "where": where,
                        "marked_stopped": marked_stopped(m)})
    return {
        "entries": entries,
        "extras": [e for e in entries if e["where"] != "med_section" and not e["marked_stopped"]],
        "omitted": sorted(expected - returned_generics),
        "n_expected_lexicon": len(expected),
    }
