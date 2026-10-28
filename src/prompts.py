"""All prompts in one place, so the exact wording is easy to review."""

# Main task: medication reconciliation.
EXTRACT = """You are assisting with medication reconciliation.

Read the clinical note below and list every medication the patient should be
taking AFTER this encounter (their active medication list going forward).

Return only compact JSON in this format:
{{"medications": ["<drug name as written in the note> <dose and unit>", ...]}}
Example: {{"medications": ["Lopressor 50 mg", "aspirin 81 mg"]}}

CLINICAL NOTE:
<<<
{note}
>>>"""

# Intervention: same task plus one explicit instruction.
# If errors drop a lot, the model CAN do the task but does not by default.
EXTRACT_CAREFUL = """You are assisting with medication reconciliation.

Read the clinical note below and list every medication the patient should be
taking AFTER this encounter (their active medication list going forward).

Important: before answering, check the WHOLE note, including the plan, for
instructions that stop, hold, or discontinue a medication, and apply them to the list.

Return only compact JSON in this format:
{{"medications": ["<drug name as written in the note> <dose and unit>", ...]}}
Example: {{"medications": ["Lopressor 50 mg", "aspirin 81 mg"]}}

CLINICAL NOTE:
<<<
{note}
>>>"""

# Mechanism test for example leakage: identical to EXTRACT except the format
# example. If the invented drugs follow the example, the example is the source.
EXTRACT_SWAP = EXTRACT.replace('["Lopressor 50 mg", "aspirin 81 mg"]', '["Lasix 40 mg", "Zocor 20 mg"]')
EXTRACT_NOEX = EXTRACT.replace('Example: {{"medications": ["Lopressor 50 mg", "aspirin 81 mg"]}}\n', '')

# Robustness: same task, different wording, to check the failure is not one phrasing.
EXTRACT_ALT = """Below is a patient's clinical note. Write the patient's current medication
list as it stands at the end of this visit: include medications that should
continue and leave out any that were stopped.

Return only compact JSON in this format:
{{"medications": ["<drug name as written in the note> <dose and unit>", ...]}}

NOTE:
<<<
{note}
>>>"""

# Mechanism test: make the model write the stop instructions down FIRST, then
# build the list. If this fixes errors, the model can find and apply the
# instruction when the steps are separated, so the failure is in combining them.
EXTRACT_TWOSTEP = """You are assisting with medication reconciliation.

Read the clinical note below.
Step 1: copy every sentence that stops, holds, or discontinues a medication.
Step 2: list every medication the patient should be taking AFTER this encounter,
leaving out anything stopped in step 1.

Return only compact JSON in this format:
{{"stop_instructions": ["..."], "medications": ["<drug name as written in the note> <dose and unit>", ...]}}

CLINICAL NOTE:
<<<
{note}
>>>"""

# Knowledge probe: ask about the target directly. If the model answers
# correctly but still lists the drug, it may know the instruction but fail
# to apply it while building the list.
PROBE_STOPPED = """Read the clinical note below.

Question: After this encounter, should the patient still be taking {drug}?

Return only JSON: {{"answer": "yes" | "no" | "unclear", "evidence": "<short quote from the note>"}}

CLINICAL NOTE:
<<<
{note}
>>>"""

PROMPTS = {
    "extract": EXTRACT,
    "extract_careful": EXTRACT_CAREFUL,
    "extract_twostep": EXTRACT_TWOSTEP,
    "extract_alt": EXTRACT_ALT,
    "extract_swap": EXTRACT_SWAP,
    "extract_noex": EXTRACT_NOEX,
    "probe_stopped": PROBE_STOPPED,
}


def render(prompt_name: str, case: dict) -> str:
    return PROMPTS[prompt_name].format(note=case["text"], drug=case["target"]["surface"])
