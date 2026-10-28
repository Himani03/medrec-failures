"""Experiments are lists of (condition, position, prompt) arms.

Every arm uses the same notes, allowing paired comparisons.
"""

EXPERIMENTS = {
    "baseline": {
        "description": "Broad probe: extract the list from each real note, unchanged.",
        "n_notes": 148,
        "arms": [("original", "none", "extract")],
    },
    "stop_instruction": {
        "description": "Failure 1: is a stop instruction applied? Controls, probes, and placement.",
        "n_notes": 100,
        "arms": [
            ("continue", "late", "extract"),            # control: same sentence shape, drug stays
            ("discontinue", "late", "extract"),         # main case
            ("discontinue", "late", "probe_stopped"),   # does the model understand the instruction?
            ("discontinue", "late", "extract_careful"), # does an explicit reminder fix it?
            ("discontinue", "late", "extract_twostep"), # find stops first, then list: does separating steps fix it?
            ("continue", "late", "extract_alt"),        # robustness: reworded prompt, control
            ("discontinue", "late", "extract_alt"),     # robustness: reworded prompt, main case
            ("discontinue", "early", "extract"),        # placement tests (mechanism)
            ("discontinue", "middle", "extract"),
            ("discontinue", "after_meds", "extract"),
            ("discontinue", "inline", "extract"),
        ],
    },
    "example_leak": {
        "description": "Extra finding: does the model copy drugs from the prompt's format example into real lists?",
        "n_notes": 148,
        "arms": [
            ("original", "none", "extract"),        # example: Lopressor 50 mg, aspirin 81 mg
            ("original", "none", "extract_swap"),   # example: Lasix 40 mg, Zocor 20 mg
            ("original", "none", "extract_noex"),   # no example
        ],
    },
    "list_position": {
        "description": "Failure 2: is a real active drug dropped more often when it sits late in a long list?",
        "n_notes": 148,
        "arms": [
            ("original", "none", "extract"),   # the real note (same prompt as baseline, reused from cache)
            ("reorder", "first", "extract"),   # same note, target entry moved to the top of the list
            ("reorder", "last", "extract"),    # same note, target entry moved to the bottom
        ],
    },
    "list_position_noex": {
        "description": "Failure 2 mechanism: same top/bottom test with no format example in the prompt.",
        "n_notes": 148,
        "arms": [
            ("original", "none", "extract_noex"),
            ("reorder", "first", "extract_noex"),
            ("reorder", "last", "extract_noex"),
        ],
    },
    "allergy_leak": {
        "description": "Failure 2 probe: is a drug named only as an allergy put on the active list?",
        "n_notes": 100,
        "arms": [
            ("allergy", "after_meds", "extract"),          # terse allergy line next to the med list
            ("allergy", "end", "extract"),                 # same line, far from the med list
            ("allergy_explicit", "after_meds", "extract"), # relation spelled out
            ("family", "after_meds", "extract"),           # same drug, harmless role: any mention leaks?
            ("allergy", "after_meds", "probe_stopped"),    # does the model know not to take it?
        ],
    },
    "discovery": {
        "description": "Pilot: do models apply a medication plan instruction?",
        "n_notes": 60,
        "arms": [
            ("continue", "late", "extract"),
            ("discontinue", "late", "extract"),
            ("discontinue", "early", "extract"),
            ("discontinue", "middle", "extract"),
        ],
    },
    "plan_application": {
        "description": "Test whether a discontinued medication remains listed.",
        "n_notes": 100,
        "arms": [
            ("continue", "late", "extract"),
            ("discontinue", "late", "extract"),
            ("discontinue", "late", "extract_careful"),
            ("discontinue", "late", "probe_stopped"),
        ],
    },
    "position_sensitivity": {
        "description": "Test whether the same stop instruction behaves differently by position.",
        "n_notes": 100,
        "arms": [
            ("continue", "late", "extract"),
            ("discontinue", "early", "extract"),
            ("discontinue", "middle", "extract"),
            ("discontinue", "late", "extract"),
        ],
    },
    "mechanism": {
        "description": "Mechanism probes for plan application.",
        "n_notes": 100,
        "arms": [
            ("continue", "late", "extract"),
            ("discontinue", "late", "probe_stopped"),
            ("discontinue", "late", "extract_careful"),
        ],
    },
}
