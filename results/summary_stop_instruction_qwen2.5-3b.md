# stop_instruction: qwen2.5:3b

Real MTSamples notes with ONE synthetic plan sentence inserted. A controlled stress test, not a real-world prevalence estimate.

Notes run: 60. The control listed the target correctly on **50**; rates below use those eligible notes (the model could find and list the drug).

| Arm | Errors / eligible | Rate (95% CI) | Outcomes | Errors / all notes |
|---|---:|---:|---|---:|
| Control: 'Continue X' near end | 0/50 | 0% (0%–7%) | listed: 50 | 10/60 |
| 'Discontinue X' near end (main case) | 21/50 | 42% (29%–56%) | removed: 28, still_listed: 21, marked_stopped: 1 | 22/60 |
| Same + 'check for stops' reminder | 16/50 | 32% (21%–46%) | removed: 32, still_listed: 15, marked_stopped: 2, invalid_output: 1 | 18/60 |
| Same, 2 steps: copy stop sentences, then list | 18/50 | 36% (24%–50%) | removed: 32, still_listed: 18 | 19/60 |
| Reworded prompt: control | 1/50 | 2% (0%–10%) | listed: 49, dropped: 1 | 3/60 |
| Reworded prompt: 'Discontinue X' near end | 22/50 | 44% (31%–58%) | removed: 24, still_listed: 22, marked_stopped: 4 | 27/60 |
| 'Discontinue X' near start | 11/50 | 22% (13%–35%) | removed: 39, still_listed: 11 | 12/60 |
| 'Discontinue X' in middle | 22/50 | 44% (31%–58%) | removed: 27, still_listed: 22, marked_stopped: 1 | 24/60 |
| 'Discontinue X' right after med list | 18/50 | 36% (24%–50%) | removed: 31, still_listed: 18, marked_stopped: 1 | 20/60 |
| 'Discontinue X' inside the med entry | 10/50 | 20% (11%–33%) | removed: 38, still_listed: 10, marked_stopped: 2 | 11/60 |
| Direct question: 'still taking X?' | 7/50 | 14% (7%–26%) | no: 43, yes: 7 | 8/60 |

Robustness, reworded prompt (own control as eligibility): control correct on 57/60; stopped drug still listed 27/57 = 47% (35%–60%).

Sensitivity: excluding targets named in the prompt example (metoprolol, aspirin): control 0/40, main case 15/40 = 38% (24%–53%).

Sensitivity: excluding 2 notes where the drug is listed with a dose twice (e.g. admission and discharge lists), main-case rate = 19/48 = 40% (27%–54%).

## Paired comparisons on the same notes (exact McNemar test)

| Comparison | Notes | Only A wrong | Only B wrong | p |
|---|---:|---:|---:|---:|
| Inside med entry vs near end | 50 | 1 | 12 | 0.00342 |
| Right after med list vs near end | 50 | 3 | 6 | 0.508 |
| Near start vs near end | 50 | 2 | 12 | 0.0129 |
| Middle vs near end | 50 | 6 | 5 | 1 |
| Reminder prompt vs default | 50 | 1 | 6 | 0.125 |
| Two-step prompt vs default | 50 | 7 | 10 | 0.629 |

**Knows but does not apply:** of 21 notes where the stopped drug stayed on the list, the model answered the direct question correctly ('no') on 16.

**Contradicts itself in one answer (two-step prompt, drug never named in the prompt):** of 18 two-step failures, the model copied the 'Discontinue X' sentence in step 1 and still listed X in step 2 on 11.

## Main-case errors (first 8)

- `mts_1335`: 'Discontinue Crestor.' -> still listed; direct question answer: no
- `mts_1357`: 'Discontinue aspirin.' -> still listed; direct question answer: no
- `mts_1431`: 'Discontinue Zocor.' -> still listed; direct question answer: no
- `mts_1432`: 'Discontinue Amlodipine.' -> still listed; direct question answer: no
- `mts_172`: 'Discontinue Toprol.' -> still listed; direct question answer: no
- `mts_175`: 'Discontinue Metoprolol.' -> still listed; direct question answer: no
- `mts_1783`: 'Discontinue Aspirin.' -> still listed; direct question answer: no
- `mts_1785`: 'Discontinue Norvasc.' -> still listed; direct question answer: no
