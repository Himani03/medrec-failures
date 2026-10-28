# Pre-run research protocol

This protocol keeps the experiments tied to the Alterra take-home: identify two distinct, reproducible clinical-task failures; measure them against controls; test a mechanism; and state clinical relevance and limitations honestly.

## Task and scope

**Task:** From a clinical note that includes a medication section and a plan, produce the active medication list after the encounter.

**Current dataset:** MTSamples transcription examples from the supplied project archive. They are not hospital discharge summaries. Each test adds a synthetic `PLAN` sentence. The study therefore measures controlled medication-list/plan conflict resolution on this corpus. It does not estimate prevalence in actual discharge summaries.

**Model comparison:** Use an open model locally during development to reduce cost. For final results, run the selected frontier model and the open model with the same prompts, cases, scoring, and temperature where supported. Record exact model IDs, dates, settings, and provider routes. Do not send restricted clinical notes to a service until its data route is approved.

## Candidate failure 1: plan application

**Hypothesis statement:** When a note's medication section contains a target drug and a later plan says to discontinue it, the model may still include that drug in the active medication list.

**Matched cases:** For each source note, compare the same target under a synthetic `Continue <drug>` control and a `Discontinue <drug>` case. Also run a checklist prompt and a direct yes/no question about whether the target remains active.

**Mechanism hypothesis:** The model can locate and understand the stop instruction when asked directly, but fails to apply it while composing the medication list.

**Mechanism test:** Compare direct-question accuracy with extraction on the same note. Compare default extraction with the explicit checklist prompt. Correct direct answers plus failed extraction are consistent with an application problem, but do not establish an internal reasoning mechanism.

## Candidate failure 2: position sensitivity

**Hypothesis statement:** For the same note, target drug, and discontinuation instruction, the model may be more likely to keep the drug when the instruction appears later in the note.

**Matched cases:** Put the identical sentence at early, middle, and late locations in the same source note. Keep all other text unchanged. Use early versus late as the primary paired contrast and middle as secondary. Test the longest available source notes and record character/token lengths.

**Mechanism hypothesis:** The model is less likely to use an instruction when it appears in a less attended position in a long input.

**Mechanism test:** Move only the instruction position, then repeat with controlled padding while preserving the medication and plan content. A position effect supports the hypothesis; absence of an effect is a negative result to report. This is not, by itself, proof of an attention mechanism or a general context-length limit.

## Distinctness rule

Both candidates concern medication instructions, so do not assume they are distinct just because the prompts differ. Report them as two failures only if the evidence supports different conditions and mechanisms: plan-application failure across positions, and an additional reproducible position effect under matched content. If position does not change behavior, report that negative result and choose another independently supported failure category if time allows. Do not manufacture a second failure to satisfy the rubric.

## Sample, scoring, and analysis

- Use up to 100 distinct source notes per experiment, with one target per note. The same note's arms form a matched set; model calls within that set are not independent observations.
- Before any main run, manually inspect selected targets and synthetic placements. Check the original medication section, drug alias, dose, existing stop language, prompt, and scorer output.
- Score only the selected target medication in the current harness. For a discontinue case, retaining the target is an error; for the continue control, omitting it is an error. In the continue control, also score the target's numeric dose and unit against the source medication section. Invalid JSON is an error and must be reported separately. Frequency and other medications are not scored.
- Report both unconditional counts and the plan-application rate among notes where the continue control correctly lists the target. State each denominator.
- Report Wilson 95% confidence intervals for rates and exact McNemar tests for paired comparisons. Specify early versus late as the position primary contrast before examining outputs.
- Inspect a blinded sample of errors and non-errors. Record adjudication decisions and any corrected parser/scorer labels.
- A cached rerun is not an independent stability check. For a stability check, use a fresh run or cache namespace, keep the model version and prompts fixed, and disclose any serving changes.

## Clinical relevance and prevalence

For each reproduced failure, give a conditional harm pathway. For example, a discontinued anticoagulant remaining on an active list could lead to unintended restarting and bleeding risk. This is a plausible risk pathway, not an observed outcome in this dataset. Estimate trigger prevalence only from a suitable real-note cohort with documented inclusion criteria. MTSamples plus synthetic instructions cannot support a real-world prevalence estimate. If no suitable cohort is available, say that prevalence is unknown.

## Reporting decisions

The write-up should include:

1. One page per supported failure: one-sentence statement, manually reviewed example, rate and interval, mechanism test, and conditional harm.
2. A section for tests that did not surface failures, including tested hypotheses, sample counts, model, and results.
3. A limitations section distinguishing source notes from synthetic edits and stating dataset, model, and scoring limits.
4. A reproducible command, README, exact model disclosure, and code that can recreate the scored tables and figures.

## Current pilot status

The current local run used `qwen2.5:3b` through Ollama on one source note and four prompt arms. It showed 0/1 target errors for the continue control, 1/1 for default discontinue extraction, 1/1 for checklist extraction, and 0/1 for the direct stop question. Treat this only as a harness check and an example to review. The sample is too small for a rate, the candidate failures have not been established, and no frontier-model comparison or clinical-prevalence estimate is complete.
