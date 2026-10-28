# Medication reconciliation: exploratory failure analysis

**Status: preliminary draft; not a completed evaluation.** This draft reports one manually checked pilot example. It does not establish a reproducible model failure or failure rate. Replace this status and update all results only after the planned experiments finish and cases are reviewed.

## Task and system

We tested whether a language model can reconcile a medication list with a later plan instruction. The prototype selects one medication from a source note, inserts a synthetic `Continue` or `Discontinue` instruction, and asks the model to return the medication list. We ran the local open model `qwen2.5:3b` through Ollama at temperature 0. The currently reviewed example comes from MTSamples, a collection of transcribed medical cases, not hospital discharge summaries. This is therefore a controlled medication-list/plan-conflict probe, not a direct evaluation of discharge medication reconciliation.

The scorer currently checks only the selected target medication. It does not measure whole-list accuracy, frequency accuracy, or clinical appropriateness of other medications.

## Candidate finding: a stop instruction was not applied during list extraction

**Candidate failure statement:** In one MTSamples note, Qwen2.5:3b included hydralazine in its extracted medication list after the prompt added a synthetic instruction to discontinue it.

The source note's medication section lists hydralazine 100 mg three times daily. Manual inspection found no existing instruction to hold or discontinue hydralazine in the source text. The experiment added `PLAN: Discontinue hydralazine.` at the end of the note. In the continue-control response, the model listed hydralazine with 100 mg. In the discontinue extraction response, it still listed hydralazine, without a dose. The scorer therefore marked the discontinue case as an error. An explicit checklist prompt also left hydralazine in the output. When asked directly whether hydralazine should still be taken, the model answered `no` and cited the inserted plan sentence.

This single paired example is consistent with a gap between identifying a stop instruction and applying it while constructing a medication list. It does not establish that mechanism: one example cannot rule out prompt, parsing, or model variability. The explicit checklist not fixing this example is a negative pilot observation, not evidence that checklists generally fail.

**Counts:** continue control 0/1 target errors; standard discontinue extraction 1/1; checklist extraction 1/1; direct stop question 0/1. These are counts for one note and must not be presented as population rates or accompanied by inferential claims.

**Clinical relevance:** If a real medication stop instruction were omitted from a reconciled list, a clinician or downstream system could act on stale medication information. The specific risk depends on the medication and care context. This synthetic case does not demonstrate patient harm, and this corpus cannot estimate how often the trigger occurs in actual discharge summaries.

## Second candidate: position sensitivity

No position-sensitivity result is available in this draft. The planned experiment compares the same instruction placed early, in the middle, and late in matched notes, with early-versus-late as the primary contrast. Until those matched results are run and reviewed, position sensitivity is an untested hypothesis and must not be presented as a second failure.

## Approaches that have not established a failure

- The checklist prompt did not remove hydralazine in the one reviewed pilot case. This is insufficient to assess the intervention across notes.
- The direct question was answered correctly in that same case while extraction retained the target. This motivates a mechanism test but does not reveal the model's internal process.
- Position sensitivity, long-note attention effects, and real-world prevalence have not been measured.
- No frontier-model comparison or independent stability rerun is available.

## Limitations and next work

The evidence is one note from MTSamples with a synthetic plan instruction, one local model, and a target-only scorer. MTSamples transcriptions are not a representative cohort of discharge summaries. No clinician adjudication has been performed. The sample is too small for confidence intervals, model comparisons, prevalence estimates, or claims of reproducibility. Complete the planned matched experiments, manually review errors and non-errors, report denominators and paired confidence intervals, and include a second failure only if a distinct condition is supported. If time prevents that work, submit this as a pilot with one candidate finding and explicitly state that a second failure was not established.

## Data source

The transcription samples were distributed through the [MTSamples Kaggle dataset](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions/metadata). Follow the source's attribution request and link to [MTSamples](https://www.mtsamples.com/).

## Reproducibility and AI-tool disclosure

The code and experiment protocol are in this repository. The reviewed pilot used `qwen2.5:3b` through Ollama at temperature 0; four prompts were run on one source note. OpenAI Codex assisted with code, study design, and this draft. A Gemini smoke attempt did not yield usable evaluation results. No frontier-model result is reported. Update this section with final commands, exact model identifiers, dates, settings, and any additional AI tools used.
