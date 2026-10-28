"""Edge cases for every step that turns a model answer into a number.

If any of these break, a reported rate could be wrong, so they run before
any analysis (see run_all.sh). Grouped by pipeline step.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import BASE_NOTES
from drugs import canonical, find_alias
from listscore import score_list
from perturb import ALLERGENS, build_case, pick_allergen
from prepare_data import already_stopped_somewhere, find_med_section
from score import parse_json, score_extraction, score_probe
from stats import mcnemar_exact, wilson_ci

NOTE = {
    "note_id": "test_1",
    "text": "HISTORY: Hypertension.\n\nMEDICATIONS: Lopressor 50 mg b.i.d., aspirin 81 mg daily, "
            "Synthroid 88 mcg daily.\n\nALLERGIES: Sulfa.\n\nPLAN: Follow up in 2 weeks.",
    "med_header": "MEDICATIONS",
    "target": {"generic": "metoprolol", "surface": "Lopressor", "dose_value": "50", "dose_unit": "mg"},
}
NOTE["med_section_end"] = NOTE["text"].index("\n\nALLERGIES")


def meds(*names):
    return json.dumps({"medications": list(names)})


# ---------------------------------------------------------------- drug names --

class TestDrugNames:
    def test_brand_and_generic_map_to_same_drug(self):
        assert canonical("Lopressor") == canonical("metoprolol tartrate 25 mg") == "metoprolol"

    def test_longest_alias_wins(self):
        assert canonical("Toprol XL 25 mg daily") == "metoprolol"

    def test_unknown_drug_is_none_not_a_guess(self):
        assert canonical("Milk of Magnesia") is None

    def test_whole_word_only(self):
        assert not list(find_alias("asa", "nasal spray"))  # 'asa' (aspirin) inside 'nasal'
        assert list(find_alias("asa", "ASA 81 mg"))


# ----------------------------------------------------------- parsing output --

class TestParsing:
    def test_code_fence_is_stripped(self):
        assert parse_json('```json\n{"medications": []}\n```') == {"medications": []}

    def test_text_around_json_is_ignored(self):
        assert parse_json('Here you go: {"medications": ["aspirin"]} hope this helps') == {"medications": ["aspirin"]}

    def test_broken_json_is_an_error_not_a_pass(self):
        case = build_case(NOTE, "discontinue", "late")
        result = score_extraction(case, '{"medications": ["Lopressor 50 mg"')
        assert result["outcome"] == "invalid_output" and result["error"] is True

    def test_wrong_shape_is_an_error(self):
        case = build_case(NOTE, "continue", "late")
        assert score_extraction(case, '{"meds": "Lopressor"}')["outcome"] == "invalid_output"


# ------------------------------------------------------- target-drug scoring --

class TestTargetScoring:
    def test_compact_strings_and_dicts_score_the_same(self):
        case = build_case(NOTE, "discontinue", "late")
        a = score_extraction(case, meds("Lopressor 50 mg", "aspirin 81 mg"))
        b = score_extraction(case, json.dumps({"medications": [{"name": "Lopressor", "dose": "50"}]}))
        assert a["outcome"] == b["outcome"] == "still_listed"

    def test_generic_name_counts_as_the_brand_target(self):
        case = build_case(NOTE, "discontinue", "late")
        assert score_extraction(case, meds("metoprolol 50 mg"))["outcome"] == "still_listed"

    def test_removed_is_correct(self):
        case = build_case(NOTE, "discontinue", "late")
        result = score_extraction(case, meds("aspirin 81 mg"))
        assert result["outcome"] == "removed" and result["error"] is False

    def test_kept_but_marked_discontinued_is_not_active(self):
        case = build_case(NOTE, "discontinue", "late")
        result = score_extraction(case, meds("Lopressor 50 mg (discontinued)", "aspirin 81 mg"))
        assert result["outcome"] == "marked_stopped" and result["error"] is False

    def test_marked_discontinued_in_control_is_an_error(self):
        case = build_case(NOTE, "continue", "late")
        assert score_extraction(case, meds("Lopressor 50 mg - stopped"))["error"] is True

    def test_dropped_in_control_is_an_error(self):
        case = build_case(NOTE, "continue", "late")
        assert score_extraction(case, meds("aspirin 81 mg"))["outcome"] == "dropped"

    def test_dose_inside_compact_string_is_checked(self):
        case = build_case(NOTE, "continue", "late")
        assert score_extraction(case, meds("Lopressor 50 mg"))["dose_error"] is False
        assert score_extraction(case, meds("Lopressor 25 mg"))["dose_error"] is True

    def test_empty_list_in_control_is_dropped(self):
        case = build_case(NOTE, "continue", "late")
        assert score_extraction(case, meds())["outcome"] == "dropped"


class TestProbeScoring:
    @pytest.mark.parametrize("raw,error", [
        ('{"answer": "no"}', False),
        ('{"answer": "No"}', False),
        ('{"answer": "yes"}', True),
        ('{"answer": "unclear"}', True),
        ("not json", True),
    ])
    def test_only_a_clear_no_is_correct(self, raw, error):
        assert score_probe({}, raw, "probe_stopped")["error"] is error


# ----------------------------------------------------- whole-list scoring --

class TestWholeList:
    def test_extra_from_allergy_section_and_invented_drug_are_flagged(self):
        out = score_list(NOTE["text"], [{"name": n} for n in ["Lopressor", "aspirin", "Synthroid", "Sulfa", "Lipitor"]])
        where = {e["name"]: e["where"] for e in out["extras"]}
        assert where == {"Sulfa": "other:ALLERGIES", "Lipitor": "not_in_note"}
        assert out["omitted"] == []

    def test_omitted_drug_is_reported(self):
        out = score_list(NOTE["text"], [{"name": "Lopressor"}])
        assert out["omitted"] == ["aspirin", "levothyroxine"]

    def test_allergy_annotation_is_not_an_extra(self):
        out = score_list(NOTE["text"], [{"name": "Sulfa (allergy)", "raw": "Sulfa (allergy)"}])
        assert out["extras"] == []


# ------------------------------------------------------- synthetic edits --

class TestPerturbations:
    def test_original_is_untouched(self):
        assert build_case(NOTE, "original", "none")["text"] == NOTE["text"]

    def test_only_one_sentence_is_added(self):
        for pos in ["early", "middle", "late", "after_meds", "inline"]:
            text = build_case(NOTE, "discontinue", pos)["text"]
            assert text.count("Discontinue Lopressor.") == 1
            assert text.replace("PLAN: Discontinue Lopressor.", "").replace("( )", "").count("Lopressor") == 1

    def test_inline_sits_right_after_the_target_entry(self):
        text = build_case(NOTE, "discontinue", "inline")["text"]
        assert "Lopressor 50 mg b.i.d. (PLAN: Discontinue Lopressor.)" in text

    def test_after_meds_sits_right_after_the_med_section(self):
        text = build_case(NOTE, "discontinue", "after_meds")["text"]
        assert "88 mcg daily.\n\nPLAN: Discontinue Lopressor." in text

    def test_control_and_case_differ_only_in_the_verb(self):
        a = build_case(NOTE, "continue", "late")["text"]
        b = build_case(NOTE, "discontinue", "late")["text"]
        assert a.replace("Continue Lopressor at the current dose.", "X") == b.replace("Discontinue Lopressor.", "X")

    def test_allergy_case_replaces_real_allergy_and_uses_a_new_drug(self):
        case = build_case(NOTE, "allergy", "after_meds")
        drug = case["target"]["surface"]
        assert drug in ALLERGENS and drug.lower() not in NOTE["text"].lower()
        assert "Sulfa" not in case["text"] and case["text"].count("ALLERGIES:") == 1

    def test_allergen_choice_is_deterministic(self):
        assert pick_allergen(NOTE) == pick_allergen(dict(NOTE))

    def test_allergy_leak_is_scored_as_an_error(self):
        case = build_case(NOTE, "allergy", "after_meds")
        drug = case["target"]["surface"]
        assert score_extraction(case, meds("Lopressor 50 mg", f"{drug} 500 mg"))["error"] is True
        assert score_extraction(case, meds("Lopressor 50 mg", f"{drug} (allergy)"))["error"] is False


# ------------------------------------------------------------ statistics --

class TestStats:
    def test_wilson_known_value(self):
        lo, hi = wilson_ci(5, 10)
        assert round(lo, 3) == 0.237 and round(hi, 3) == 0.763

    def test_wilson_edges_stay_in_range(self):
        assert wilson_ci(0, 10)[0] == 0.0 and wilson_ci(10, 10)[1] == 1.0 and wilson_ci(0, 0) == (0.0, 0.0)

    def test_mcnemar(self):
        assert mcnemar_exact(0, 0) == 1.0
        assert round(mcnemar_exact(8, 0), 4) == 0.0078  # 8 disagreements all one way


# -------------------------------------------- the real data we built on --

class TestRealNotes:
    notes = [json.loads(line) for line in open(BASE_NOTES)]

    def test_every_target_is_in_its_med_section_with_its_dose(self):
        for n in self.notes:
            header, start, end = find_med_section(n["text"])
            section = n["text"][start:end].lower()
            assert n["target"]["surface"].lower() in section, n["note_id"]
            assert n["target"]["dose_value"] in section, n["note_id"]

    def test_no_target_is_already_stopped_in_the_real_note(self):
        assert not any(already_stopped_somewhere(n["text"], n["target"]["surface"]) for n in self.notes)

    def test_note_ids_are_unique(self):
        assert len({n["note_id"] for n in self.notes}) == len(self.notes)


# ------------------------------------------------- list-position edits --

class TestReorder:
    LONG = dict(NOTE, text="MEDICATIONS: 1. Lopressor 50 mg daily.\n2. Aspirin 81 mg daily.\n3. Lasix 20 mg daily.\n"
                           "4. Zocor 20 mg daily.\n\nPLAN: Follow up.")

    def test_target_moves_to_first_and_last_and_nothing_is_lost(self):
        from perturb import move_target
        last = move_target(self.LONG, "last")
        assert "4. Lopressor 50 mg daily." in last and "1. Aspirin 81 mg daily." in last
        assert move_target(self.LONG, "first").count("Lopressor") == 1
        for drug in ["Aspirin", "Lasix", "Zocor", "PLAN: Follow up."]:
            assert drug in last

    def test_comma_list_keeps_lead_in_and_entries(self):
        from perturb import move_target
        note = dict(NOTE, text="MEDICATIONS: His medications are Lopressor 50 mg daily, aspirin 81 mg, "
                               "Lasix 20 mg, and Zocor 20 mg.\n\nPLAN: Follow up.")
        out = move_target(note, "last")
        assert "His medications are aspirin 81 mg, Lasix 20 mg, Zocor 20 mg, and Lopressor 50 mg daily." in out

    def test_unsplittable_list_is_skipped_not_mangled(self):
        from perturb import move_target
        short = dict(NOTE, text="MEDICATIONS: Lopressor 50 mg and aspirin.\n\nPLAN: Follow up.")
        assert move_target(short, "first") is None


def test_allergen_is_not_already_in_note_under_a_brand_name():
    note = dict(NOTE, note_id="brand_check", text=NOTE["text"].replace("aspirin 81 mg daily", "Aleve 220 mg daily"))
    for i in range(30):  # many ids so every allergen gets a chance to be picked
        assert pick_allergen(dict(note, note_id=f"id{i}")) != "naproxen"
