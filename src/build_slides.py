"""Build the 5-minute talk deck (slides.pptx) from the figures and final numbers.

Usage:
    python src/build_slides.py
"""
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from config import FIGURES_DIR, ROOT

NAVY, CREAM, RED, GREY, BLUE = (RGBColor(0x14, 0x21, 0x3D), RGBColor(0xFB, 0xFB, 0xF8),
                                RGBColor(0xC0, 0x39, 0x2B), RGBColor(0x4A, 0x55, 0x68), RGBColor(0x2E, 0x6F, 0x95))
FONT = "Arial"

# Every number on the slides; keep in sync with results/summary_*.md
N = {
    "f1_ctrl": "0/50", "f1_main": "21/50 (42%)", "f1_knew": "16 of 21",
    "f1_before": "11/50 (22%)", "f1_inline": "10/50 (20%)", "f1_after": "36–44%",
    "f1_gpt": "3/50 (6%)", "f1_gpt_probe": "50/50",
    "f1_twostep": "18/50 (36%), no better, yet in 11 of 18 failures it wrote “Discontinue X” in step 1 and still listed X in step 2", "f1_alt": "control 0/57 vs discontinue 27/57 (47%)",
    "f2_top": "42/134 (31%)", "f2_bottom": "22/134 (16%)", "f2_p": "p = 0.003",
    "f2_real": "33/147 (22%)", "f2_noex": "top 21/134 (16%) vs bottom 20/134 (15%), p = 1.0", "leak": "invented drug in 15/148 real notes with the Lopressor/aspirin example vs 0/148 with no example (p < 0.001); a Lasix/Zocor example produced 2/148, neither Lasix nor Zocor, so copying depends on which drugs are in the example",
}


def slide(prs, title, dark=False):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = NAVY if dark else CREAM
    if title:
        text(s, title, 0.6, 0.35, 12.1, 0.9, 30, bold=True, color=CREAM if dark else NAVY)
    return s


def text(s, body, x, y, w, h, size=18, bold=False, color=None, lines=None):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines or [body]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.space_after = Pt(8)
        for r in p.runs:
            r.font.size, r.font.bold, r.font.name = Pt(size), bold, FONT
            r.font.color.rgb = color or GREY
    return box


def notes(s, words):
    s.notes_slide.notes_text_frame.text = words


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    s = slide(prs, None, dark=True)
    text(s, "ALTERRA LABS · APPLIED RESEARCH TAKE-HOME", 0.8, 1.4, 11, 0.5, 14, True, RGBColor(0xE8, 0xA2, 0x7C))
    text(s, "Two ways a small LLM gets a patient’s medication list wrong", 0.8, 2.0, 11.5, 2.0, 44, True, CREAM)
    text(s, "Medication reconciliation · qwen2.5:3b (local), checked on gpt-5.4-mini",
         0.8, 4.3, 11.5, 0.8, 20, color=RGBColor(0xC9, 0xD3, 0xE0))
    text(s, "Controlled tests: real notes + one synthetic edit each. Shows cause, not hospital frequency.",
         0.8, 4.9, 11.5, 0.5, 16, color=RGBColor(0xE8, 0xA2, 0x7C))
    text(s, "Himani Shah · October 2026", 0.8, 5.7, 8, 0.5, 18, color=RGBColor(0xC9, 0xD3, 0xE0))
    notes(s, "I tested one clinical task, medication reconciliation: read a note and write the patient's current "
             "medication list. I used a small open model that runs on a laptop, and found two different, reproducible "
             "ways it gets the list wrong. I checked both on gpt-5.4-mini. To be clear on scope: these are controlled tests on "
             "transcribed MTSamples notes, each with one edit I made. They show what causes each error, not how often it "
             "happens in a hospital.")

    s = slide(prs, "Task, model, data: change one thing, compare on the same notes")
    s.shapes.add_picture(str(FIGURES_DIR / "workflow.png"), Inches(0.6), Inches(1.4), width=Inches(12.1))
    text(s, "", 0.6, 4.9, 12.1, 2.2, 17, lines=[
        "Model: qwen2.5:3b, 3.1B parameters, runs on a laptop (realistic for privacy-limited clinics). Comparison: gpt-5.4-mini.",
        "Data: 148 real MTSamples notes with a medication list. Every test = the real note + ONE controlled edit.",
        "Stats: per-note error rates, 95% Wilson intervals, paired McNemar tests. 48 unit tests on the scorer.",
    ])
    notes(s, "Every experiment takes a real note and changes exactly one thing, like adding 'Continue X' versus "
             "'Discontinue X'. Because both versions use the same notes, any difference comes from that one change.")

    s = slide(prs, "Failure 1: the model understands “discontinue” but doesn’t apply it")
    text(s, f"When the note says “Discontinue X”, qwen 3b still lists X as active in {N['f1_main']} of notes. "
            f"With “Continue X” instead: {N['f1_ctrl']} errors. Same notes, one word changed.", 0.6, 1.2, 12.1, 1.1, 21, True, NAVY)
    s.shapes.add_picture(str(FIGURES_DIR / "failure1_story.png"), Inches(0.6), Inches(2.35), width=Inches(12.1))
    text(s, f"Also on gpt-5.4-mini ({N['f1_gpt']}).", 0.6, 6.7, 12.1, 0.5, 15)
    notes(s, "Same notes, one word changed. With 'continue' the model never drops the drug. With 'discontinue' it "
             "keeps the stopped drug in 42% of notes. It holds with a different prompt and on gpt-5.4-mini at a lower "
             "rate. The right panel is the mechanism: it only works when the stop comes before the list or sits on "
             "the drug's line.")

    s = slide(prs, "Why: instructions that come after the list aren’t carried back")
    text(s, "", 0.6, 1.3, 12.1, 5.6, 22, lines=[
        "Hypothesis: the model copies the medication section top to bottom. A stop it meets later has to “reach back”, and often doesn’t.",
        f"Move the same sentence: before the list {N['f1_before']}, on the drug’s line {N['f1_inline']}, after the list {N['f1_after']}.",
        f"It knows: asked directly, it says “stop it” in {N['f1_knew']} failures.",
        "Two-step prompt: it writes “Discontinue X”, then lists X anyway (11 of 18 failures).",
    ])
    notes(s, "The medication list sits about a third of the way into a note. If the stop sentence comes before the "
             "list, or is attached to the drug's own line, errors halve. Anywhere after the list, they stay high.")

    s = slide(prs, "Failure 2: a format example in the prompt pushes the first drug off the list")
    text(s, f"With a one-line example in the prompt, the patient’s FIRST drug goes missing in {N['f2_top']} of notes, "
            f"against {N['f2_bottom']} when the same drug is last ({N['f2_p']}). Remove the example: {N['f2_noex']}.",
         0.6, 1.2, 12.1, 1.2, 20, True, NAVY)
    s.shapes.add_picture(str(FIGURES_DIR / "failure2_story.png"), Inches(0.6), Inches(2.45), height=Inches(4.6))
    text(s, "", 10.6, 2.6, 2.4, 4.4, 15, lines=[
        "Example (mts_3291): note starts “Glipizide 10 mg…”; model writes “Lopressor 50 mg” first, and Glipizide is gone.",
        "gpt-5.4-mini: 0/58 dropped.",
        "Harm: an active drug stops; an invented one starts.",
    ])
    notes(s, "Same notes, same drug, only its position changes. With the example in the prompt, the first drug is lost "
             "twice as often. Take the example out and the position effect disappears. In 9 cases the example's drug "
             "literally replaced the patient's first drug. My first guess was the bottom of the list; the data said "
             "otherwise.")

    s = slide(prs, "Why: the example competes for the answer’s first slot")
    text(s, "", 0.6, 1.3, 12.1, 5.6, 22, lines=[
        "My first guess was wrong: I expected the bottom of long lists. The data said the top (31% vs 16%).",
        "Clue: in 9 of 42 top drops, the answer starts with “Lopressor”, the example’s drug, which isn’t in the note.",
        "Test: remove only the example. Lost only with example 27 vs only without 6 (p = 0.0003). Position effect gone.",
        "Fix: no in-prompt example, or check every output drug appears in the note.",
    ])
    notes(s, "Removing the example is a direct causal test. Swapping its drugs shows the invented drugs follow the example.")

    s = slide(prs, "Two different failures, not one")
    text(s, "", 0.6, 1.3, 12.1, 5.6, 22, lines=[
        "Failure 1 comes from the NOTE: an instruction is read but not applied → a stopped drug stays.",
        "Failure 2 comes from the PROMPT: no instruction involved; the example pushes out a real drug → an active drug vanishes.",
        "Different fixes: removing the example erases Failure 2, but Failure 1 stays at 47% with a reworded, example-free prompt.",
        "Different models: Failure 1 also in gpt-5.4-mini (6%); Failure 2 only in the small model (gpt 0/58).",
    ])
    notes(s, "A reviewer may ask if these are the same thing, since both change the list. They aren't: different cause, "
             "different direction of error, different fix, and they split across models.")

    s = slide(prs, "What I tried that did not fail, and bugs I fixed")
    text(s, "", 0.6, 1.3, 12.1, 5.6, 19, lines=[
        "Allergy leak: drug named only under ALLERGIES → never put on the list (gpt-5.4-mini 0/20; real notes 0/51).",
        "“Check for stops” reminder: 42% → 32%, p = 0.13, not a reliable fix.",
        "Failure 2 on gpt-5.4-mini: 0/58, so it’s a small-model failure.",
        "Bugs found and fixed before final runs: Ollama silently cut prompts at 4,096 tokens; allergy picker could "
        "choose a drug already in the note under a brand name. Pilot outputs archived, not used.",
        "Checks: every Failure 1 error read by hand; 0/577 “removed” outputs hid a misspelled drug; results hold "
        "without example-drug targets and without notes that list a drug twice.",
    ])
    notes(s, "Negative results and bugs are part of the evidence that the positive results are real.")

    s = slide(prs, "Limits and what I’d do next")
    text(s, "", 0.6, 1.3, 12.1, 5.6, 19, lines=[
        "Limits: synthetic edits show cause, not frequency. MTSamples is not a discharge cohort. "
        "50–60 notes per test (CI about ±13 points). One small open model plus one API model.",
        "Next 1: MIMIC-IV discharge summaries to size how often stop instructions and long lists occur.",
        "Next 2: turn both failures into eval rubric items (every stop applied, every active drug kept, "
        "nothing invented) with clinician references.",
        "Next 3: mechanism depth, with attention/attribution during list writing and a size ladder (3B, 7B, 14B).",
        "Reproduce: bash run_all.sh rebuilds every number from cached outputs. AI use: Claude helped with code and "
        "drafting; all scoring is rule-based.",
    ])
    notes(s, "I'm careful not to claim prevalence. These are controlled tests that show cause.")

    out = ROOT / "slides.pptx"
    prs.save(out)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
