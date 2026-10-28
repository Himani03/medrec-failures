# list_position_noex: qwen2.5:3b (prompt: extract_noex)

Real MTSamples notes. In the edited arms, the target drug's own entry is moved to the top or the bottom of the same medication list; nothing else changes. Error = target drug missing from the list.

| Arm | Dropped / notes | Rate (95% CI) |
|---|---:|---:|
| Target moved to TOP of list [synthetic edit] | 21/134 | 16% (10%–23%) |
| Target where the note put it [real] | 17/134 | 13% (8%–19%) |
| Target moved to BOTTOM of list [synthetic edit] | 20/134 | 15% (10%–22%) |

Sensitivity, excluding targets named in the prompt example: bottom 16/112, top 17/112, only-bottom 13 vs only-top 14, p = 1.

| Paired comparison | Notes | Only A dropped | Only B dropped | p |
|---|---:|---:|---:|---:|
| Bottom vs top | 134 | 14 | 15 | 1 |
| Bottom vs original | 134 | 10 | 7 | 0.629 |
| Top vs original | 134 | 12 | 8 | 0.503 |

## [real] Every lexicon drug in the unedited notes: omitted by place in list

| Place in list | Omitted / drugs | Rate (95% CI) |
|---|---:|---:|
| first third | 0/0 | 0% (0%–0%) |
| middle third | 0/0 | 0% (0%–0%) |
| last third | 0/0 | 0% (0%–0%) |

| List length (entries) | Omitted / drugs | Rate (95% CI) |
|---|---:|---:|
| 3-5 | 0/0 | 0% (0%–0%) |
| 6-10 | 0/0 | 0% (0%–0%) |
| 11+ | 0/0 | 0% (0%–0%) |

## Same drug kept at the top but dropped at the bottom (14 notes)

- `mts_1774`: Seroquel
- `mts_1796`: Coreg
- `mts_2561`: K-Dur
- `mts_2971`: aspirin
- `mts_3049`: Ambien
- `mts_3054`: glyburide
- `mts_3290`: Klor-Con
- `mts_3335`: Prednisone
