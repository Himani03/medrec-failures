# Applied Research take-home: medication reconciliation

This repository is a prototype evaluation for the Alterra Applied Research take-home. It tests whether a model can produce an active medication list after reading a note that contains medication information and a plan instruction.

## Current status

An honest, preliminary write-up based on the manually reviewed pilot is in [`SUBMISSION_DRAFT.md`](SUBMISSION_DRAFT.md). It is explicitly not a completed evaluation.

The pipeline has completed a **one-note local smoke run** with `qwen2.5:3b` through Ollama. The target was hydralazine 100 mg. The model included it in the continue control, still returned it after the synthetic plan said to discontinue it, and correctly answered a direct question that it should not be taken. An added checklist prompt did not fix the extraction result. This example has not had independent clinical adjudication, and the saved output predates the dose/unit scoring update below.

This is one exploratory example, not evidence of a reproducible failure or a failure rate. The standard plan-application and position experiments are configured for 100 notes each, but those runs have not been completed. The frontier-model comparison, manual adjudication, final mechanism tests, and clinical-impact analysis also remain to be done.

## Candidate failure hypotheses

These are questions to test, not findings already established.

1. **Plan application (reasoning):** When the medication list contains a drug and the plan says to discontinue it, does the model nevertheless retain that drug in the active list?
2. **Position sensitivity (attention):** With the note and instruction held fixed, does moving the same discontinuation instruction early, into the middle, or late in the note change whether the model removes the drug?

The second experiment uses the longest source notes available. It tests sensitivity to instruction position within this corpus; it does not test the model's maximum context length. Before claiming two distinct failures, check that the position effect is reproducible and meaningfully different from general plan-application errors.

## Data and what the task represents

The current source is the Kaggle **Medical Transcriptions** dataset, scraped from [MTSamples](https://www.mtsamples.com/). The Kaggle listing marks it CC0. MTSamples asks users to credit its site, so cite and link MTSamples in any write-up or redistribution. See the [Kaggle dataset listing](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions/metadata) and [MTSamples attribution notice](https://github.com/microsoft/clinical_visit_note_summarization_corpus/blob/main/NOTICE).

These are transcription samples from varied specialties, not a cohort of hospital discharge summaries. The model receives the original medication section, and the experiment adds a synthetic `PLAN` sentence. So this prototype tests **resolving a medication-list/plan conflict**. It does not yet reproduce the exact workflow of removing the discharge-medications answer section and reconstructing that list from the rest of a MIMIC discharge summary. State this scope clearly in the write-up. Do not use this dataset to estimate real-world prevalence or patient harm.

`src/prepare_data.py` selects notes with a medication section and at least two lexicon-matched drugs with doses, then chooses one target per note with a fixed seed. The small lexicon and section parser can select a false match, so audit the selected cases before a larger run.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/prepare_data.py
```

## Run the experiments

Use a local Ollama model for pipeline development:

```bash
python src/run.py --experiment plan_application --provider ollama --model qwen2.5:3b --n 5 --workers 1
```

Run the two candidate-failure experiments at their configured sample size (100 notes each):

```bash
python src/run.py --experiment plan_application --provider ollama --model qwen2.5:3b --workers 1
python src/run.py --experiment position_sensitivity --provider ollama --model qwen2.5:3b --workers 1
python src/analyze.py --model qwen2.5:3b
```

For the final model run, choose a provider/model only after checking its data-handling terms and the dataset terms. Store credentials in a local `.env` file based on `.env.example`; never include `.env` in a ZIP or repository. Run the same experiments on the frontier model and report the exact model identifier and settings.

The runner uses temperature 0, a fixed seed for note selection, and caches exact prompts and responses under `results/cache/`. Caching avoids repeating completed calls; it does not make serving behavior deterministic across model versions. Use a small `--n` only for debugging. Do not use that output as a rate estimate.

## Experimental design and scoring

Each source note gets one target drug. The plan-application experiment runs four arms on each note: a continue control, standard extraction after a discontinue instruction, extraction after the same instruction plus a checklist reminder, and a direct question about whether the drug should still be taken. The primary extraction analysis includes notes where the model correctly lists the target in the continue control. Report those eligible counts and the unconditional results too.

The position experiment puts the same `PLAN: Discontinue <drug>.` sentence at early, middle, and late positions in the same note, plus a continue control. Specify early-versus-late as the primary paired comparison before looking at results; treat middle as secondary. Use the note as the paired unit, not each model call as an independent sample.

The current scorer evaluates whether the **one target drug** is present or absent as expected. In the continue control, it also compares that target's dose and unit with the source medication section. It does not grade frequency or the rest of the medication list. Do not describe these scores as whole-list medication-reconciliation accuracy. The direct-question probe can suggest whether the model can identify the instruction, but it cannot prove an internal mechanism.

## Manual case review before reporting

Review a blinded sample of errors and non-errors from each model. For each reviewed case, check:

- the target drug and its dose really appear in the parsed medication section;
- the selected target is not already held or discontinued elsewhere in the source note;
- the synthetic instruction names the intended drug and appears at the intended position;
- the raw model response is valid JSON and the scorer parsed the target correctly;
- the scored outcome matches the note and the expected active/inactive status;
- the dose and unit comparison is correct when the target is expected to remain active.

Record adjudication decisions and correct parser or alias errors before calculating final results. Preserve original model responses and document any corrected labels.

## Reporting against the take-home rubric

- **What fails:** one testable, one-sentence statement per candidate failure.
- **Evidence:** manually reviewed examples, paired controls, denominators, confidence intervals, and a rerun for stability.
- **Why:** one mechanism hypothesis per failure plus a test, including the checklist and direct-question probes for plan application and position/padding probes for position sensitivity.
- **Clinical relevance:** describe a conditional potential harm, such as a discontinued anticoagulant remaining active. Do not claim observed harm. Estimate trigger prevalence only from an appropriate real-note cohort; MTSamples cannot supply a hospital discharge prevalence estimate.
- **What did not fail:** list each tested hypothesis, its test set and model, and the observed result, including null or inconclusive results. Do not omit failed hypotheses.
- **Limitations:** clearly separate real source notes from synthetic edits; state that one transcription corpus, one hospital system (if using MIMIC), and one model do not establish general performance.

See [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) for the pre-run protocol and decision rules.

## Repository map

```text
src/prepare_data.py   select base transcriptions and target drugs
src/perturb.py        insert controlled synthetic instructions
src/prompts.py        extraction, mechanism, and intervention prompts
src/llm.py            provider calls and cached outputs
src/experiments.py    experimental arms and sample sizes
src/score.py          target-drug scoring
src/stats.py          Wilson confidence interval and exact McNemar test
src/analyze.py        summary tables and figures
data/                 source CSV and prepared note records
```

## AI-tool disclosure

OpenAI Codex assisted with code, experiment framing, and documentation. A local `qwen2.5:3b` smoke run was completed through Ollama (temperature 0; one source note; four prompts). A Gemini smoke attempt returned service errors and produced no usable evaluation output. No frontier-model evaluation result is reported yet. Update this disclosure with every model and tool used for final evaluation and analysis.
