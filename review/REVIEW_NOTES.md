# Manual review log

What was checked by hand, and what changed because of it. Sheets of randomly sampled cases for further review come from `python src/review_sample.py`.

## Failure 1 (stop_instruction)

**Every main-case error was read** (qwen2.5:3b: 21 eligible plus 1 invalid; gpt-5.4-mini: 3). In each case the returned list contains the target drug by name or generic, with no "discontinued", "held" or "stop" annotation. The automatic label "still listed" was correct in all of them.

- `mts_1801` (Norvasc): the note has a second medication list later in the text that names **amlodipine** (the same drug, generic name) with a dose. "Discontinue Norvasc" is therefore arguably ambiguous. Both models kept amlodipine. Kept in the main numbers, and reported a sensitivity analysis that drops notes listing the target with a dose twice (2 of 50 eligible). Conclusions are unchanged.
- `mts_3403` (Coumadin, i.e. warfarin): a clear failure on an anticoagulant. Used as the example in the write-up.
- `mts_2971`: the model got stuck repeating "Lisinopril 20 mg" until the output limit, which is invalid JSON. It is scored as invalid, and since it also fails the control, it is outside the eligible set.

**False "removed" check.** A drug misspelled in the output would be scored as removed when it was really kept. I fuzzy-matched (similarity above 0.8) every word in every "removed" response against the target's names. Among the 577 non-two-step "removed" responses on both models, 0 contained a near-match. The only hits were two-step responses, where the drug is correctly quoted in the separate `stop_instructions` field and not in the medication list.

## Harness bugs found by review and tests

1. Ollama's default 4,096-token context silently truncated long prompts. All runs use 8,192. Pilot outputs are archived and unused.
2. The allergy-leak picker could choose a drug already in the note under a brand name (naproxen vs Aleve in `mts_1430`), which made one note "leak" in every arm. Fixed (brand names are now checked), guarded by a unit test, and those cases re-run.

## Who reviewed

The first-pass review above was done with an AI assistant (Claude) reading the raw outputs and notes. Human spot-check of the named cases (Himani): [x] mts_1801  [x] mts_3403  [x] mts_2971
