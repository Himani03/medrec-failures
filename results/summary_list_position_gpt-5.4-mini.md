# list_position: gpt-5.4-mini (prompt: extract)

Real MTSamples notes. In the edited arms, the target drug's own entry is moved to the top or the bottom of the same medication list; nothing else changes. Error = target drug missing from the list.

| Arm | Dropped / notes | Rate (95% CI) |
|---|---:|---:|
| Target moved to TOP of list [synthetic edit] | 0/58 | 0% (0%–6%) |
| Target where the note put it [real] | 0/58 | 0% (0%–6%) |
| Target moved to BOTTOM of list [synthetic edit] | 0/58 | 0% (0%–6%) |

Sensitivity, excluding targets named in the prompt example: bottom 0/46, top 0/46, only-bottom 0 vs only-top 0, p = 1.

| Paired comparison | Notes | Only A dropped | Only B dropped | p |
|---|---:|---:|---:|---:|
| Bottom vs top | 58 | 0 | 0 | 1 |
| Bottom vs original | 58 | 0 | 0 | 1 |
| Top vs original | 58 | 0 | 0 | 1 |

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

## Same drug kept at the top but dropped at the bottom (0 notes)

