# example_leak: qwen2.5:3b

[real] 148 unedited MTSamples notes. Only the format example in the prompt changes. 'Invented' = a lexicon drug in the output that appears nowhere in the note.

| Prompt | Notes with an invented drug | Rate (95% CI) | Invented drugs (count) | Target drug missing |
|---|---:|---:|---|---:|
| Example: Lopressor 50 mg, aspirin 81 mg | 15/148 | 10% (6%–16%) | metoprolol (15), aspirin (7), enalapril (1), hydrochlorothiazide (1), lisinopril (1) | 34/148 |
| Example: Lasix 40 mg, Zocor 20 mg | 2/148 | 1% (0%–5%) | diltiazem (1), lisinopril (1), omeprazole (1), quetiapine (1), carbamazepine (1) | 21/148 |
| No example | 0/148 | 0% (0%–3%) | none | 22/148 |

Paired, default example vs no example: invented only with example 15, only without 0, exact McNemar p = 6.1e-05.
