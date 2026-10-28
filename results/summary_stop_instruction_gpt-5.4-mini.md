# stop_instruction: gpt-5.4-mini

Real MTSamples notes with ONE synthetic plan sentence inserted. A controlled stress test, not a real-world prevalence estimate.

Notes run: 50. The control listed the target correctly on **50**; rates below use those eligible notes (the model could find and list the drug).

| Arm | Errors / eligible | Rate (95% CI) | Outcomes | Errors / all notes |
|---|---:|---:|---|---:|
| Control: 'Continue X' near end | 0/50 | 0% (0%–7%) | listed: 50 | 0/50 |
| 'Discontinue X' near end (main case) | 3/50 | 6% (2%–16%) | removed: 47, still_listed: 3 | 3/50 |
| Same + 'check for stops' reminder | 1/50 | 2% (0%–10%) | removed: 49, still_listed: 1 | 1/50 |
| Same, 2 steps: copy stop sentences, then list | 1/50 | 2% (0%–10%) | removed: 49, still_listed: 1 | 1/50 |
| Reworded prompt: control | 0/50 | 0% (0%–7%) | listed: 50 | 0/50 |
| Reworded prompt: 'Discontinue X' near end | 1/50 | 2% (0%–10%) | removed: 49, still_listed: 1 | 1/50 |
| 'Discontinue X' near start | 6/50 | 12% (6%–24%) | removed: 44, still_listed: 6 | 6/50 |
| 'Discontinue X' in middle | 4/50 | 8% (3%–19%) | removed: 46, still_listed: 4 | 4/50 |
| 'Discontinue X' right after med list | 3/50 | 6% (2%–16%) | removed: 47, still_listed: 3 | 3/50 |
| 'Discontinue X' inside the med entry | 2/50 | 4% (1%–13%) | removed: 48, still_listed: 2 | 2/50 |
| Direct question: 'still taking X?' | 0/50 | 0% (0%–7%) | no: 50 | 0/50 |

Robustness, reworded prompt (own control as eligibility): control correct on 50/50; stopped drug still listed 1/50 = 2% (0%–10%).

Sensitivity: excluding targets named in the prompt example (metoprolol, aspirin): control 0/44, main case 3/44 = 7% (2%–18%).

Sensitivity: excluding 2 notes where the drug is listed with a dose twice (e.g. admission and discharge lists), main-case rate = 2/48 = 4% (1%–14%).

## Paired comparisons on the same notes (exact McNemar test)

| Comparison | Notes | Only A wrong | Only B wrong | p |
|---|---:|---:|---:|---:|
| Inside med entry vs near end | 50 | 1 | 2 | 1 |
| Right after med list vs near end | 50 | 2 | 2 | 1 |
| Near start vs near end | 50 | 5 | 2 | 0.453 |
| Middle vs near end | 50 | 2 | 1 | 1 |
| Reminder prompt vs default | 50 | 0 | 2 | 0.5 |
| Two-step prompt vs default | 50 | 0 | 2 | 0.5 |

**Knows but does not apply:** of 3 notes where the stopped drug stayed on the list, the model answered the direct question correctly ('no') on 3.

**Contradicts itself in one answer (two-step prompt, drug never named in the prompt):** of 1 two-step failures, the model copied the 'Discontinue X' sentence in step 1 and still listed X in step 2 on 1.

## Main-case errors (first 8)

- `mts_13`: 'Discontinue hydrochlorothiazide.' -> still listed; direct question answer: no
- `mts_1801`: 'Discontinue Norvasc.' -> still listed; direct question answer: no
- `mts_2547`: 'Discontinue amitriptyline.' -> still listed; direct question answer: no
