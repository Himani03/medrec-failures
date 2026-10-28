# Results: qwen2.5:3b

These are controlled stress tests on MTSamples transcriptions with synthetic PLAN instructions. They do not estimate error prevalence in real discharge workflows.

The model listed the target in the continue control on **1 / 1** notes. Error rates below use notes with a correct control response.

## Error rates

| Arm | Eligible n | Eligible errors | Eligible rate (95% CI) | All cases errors/n | Outcomes |
|---|---:|---:|---:|---:|---|
| Continue control | 1 | 0 | 0.0% (0.0%–79.3%) | 0/1 | listed: 1 |
| Discontinue, late | 1 | 1 | 100.0% (20.7%–100.0%) | 1/1 | still_listed: 1 |
| Explicit checklist prompt | 1 | 1 | 100.0% (20.7%–100.0%) | 1/1 | still_listed: 1 |
| Direct stop question | 1 | 0 | 0.0% (0.0%–79.3%) | 0/1 | no: 1 |

## Paired comparisons (exact McNemar test)

| Comparison | n | A only wrong | B only wrong | p |
|---|---:|---:|---:|---:|
| Checklist prompt vs default | 1 | 0 | 0 | 1 |

## Target dose and unit in the continue control

Among 1 controls where the target was listed and its dose could be scored, 0 had a dose or unit mismatch. A missing target is counted in the medication status analysis instead. Frequency and the rest of the medication list are not scored.


On 1 of 1 failed late-plan cases with a probe result, the model answered the direct stop question correctly.

## Example errors

- `mts_2993` at late: still_listed; inserted instruction: Discontinue hydralazine.
