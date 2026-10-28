"""Small checks for the controlled cases and target-medication scoring."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from drugs import canonical
from perturb import build_case
from score import score_extraction


NOTE = {
    "note_id": "test_1",
    "text": "HISTORY: Hypertension.\n\nMEDICATIONS: Lopressor 50 mg b.i.d., aspirin 81 mg daily.\n\n"
            "ALLERGIES: None.\n\nPLAN: Follow up in 2 weeks.",
    "target": {"generic": "metoprolol", "surface": "Lopressor", "dose_value": "50", "dose_unit": "mg"},
}


def test_brand_maps_to_generic():
    assert canonical("Toprol XL 25 mg") == "metoprolol"
    assert canonical("Coumadin") == "warfarin"
    assert canonical("vitamin D") is None


def test_same_instruction_can_be_moved_across_note():
    early = build_case(NOTE, "discontinue", "early")
    middle = build_case(NOTE, "discontinue", "middle")
    late = build_case(NOTE, "discontinue", "late")
    positions = [case["text"].index("PLAN: Discontinue") for case in (early, middle, late)]
    assert positions == sorted(positions)
    assert {case["added_sentence"] for case in (early, middle, late)} == {"Discontinue Lopressor."}


def test_continue_control_and_discontinue_case_have_expected_labels():
    control = build_case(NOTE, "continue", "late")
    stopped = build_case(NOTE, "discontinue", "late")
    assert control["expected"] == "listed"
    assert stopped["expected"] == "removed"


def test_target_medication_scoring():
    case = build_case(NOTE, "discontinue", "late")
    still_listed = '{"medications": [{"name": "Lopressor", "dose": "50 mg", "frequency": "bid"}]}'
    removed = '{"medications": [{"name": "aspirin", "dose": "81 mg", "frequency": "daily"}]}'
    assert score_extraction(case, still_listed)["outcome"] == "still_listed"
    assert score_extraction(case, removed)["error"] is False


def test_stopped_annotation_counts_as_removed():
    case = build_case(NOTE, "discontinue", "late")
    annotated = '{"medications": [{"name": "Lopressor", "dose": "50", "unit": "mg", "frequency": "discontinued"}]}'
    result = score_extraction(case, annotated)
    assert result["outcome"] == "marked_stopped" and result["error"] is False


def test_extra_drug_from_allergy_section_is_flagged():
    note = dict(NOTE, text=NOTE["text"].replace("ALLERGIES: None.", "ALLERGIES: Penicillin."))
    case = build_case(note, "original", "none")
    raw = '{"medications": [{"name": "Lopressor"}, {"name": "aspirin"}, {"name": "Penicillin"}, {"name": "Lipitor"}]}'
    extras = {e["name"]: e["where"] for e in score_extraction(case, raw)["extras"]}
    assert extras == {"Penicillin": "other:ALLERGIES", "Lipitor": "not_in_note"}
