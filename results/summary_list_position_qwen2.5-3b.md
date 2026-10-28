# list_position: qwen2.5:3b (prompt: extract)

Real MTSamples notes. In the edited arms, the target drug's own entry is moved to the top or the bottom of the same medication list; nothing else changes. Error = target drug missing from the list.

| Arm | Dropped / notes | Rate (95% CI) |
|---|---:|---:|
| Target moved to TOP of list [synthetic edit] | 42/134 | 31% (24%–40%) |
| Target where the note put it [real] | 30/134 | 22% (16%–30%) |
| Target moved to BOTTOM of list [synthetic edit] | 22/134 | 16% (11%–24%) |

Sensitivity, excluding targets named in the prompt example: bottom 19/112, top 37/112, only-bottom 10 vs only-top 28, p = 0.0051.

| Paired comparison | Notes | Only A dropped | Only B dropped | p |
|---|---:|---:|---:|---:|
| Bottom vs top | 134 | 11 | 31 | 0.00289 |
| Bottom vs original | 134 | 10 | 18 | 0.185 |
| Top vs original | 134 | 18 | 6 | 0.0227 |

## [real] Every lexicon drug in the unedited notes: omitted by place in list

| Place in list | Omitted / drugs | Rate (95% CI) |
|---|---:|---:|
| first third | 75/284 | 26% (22%–32%) |
| middle third | 28/222 | 13% (9%–18%) |
| last third | 37/194 | 19% (14%–25%) |

| List length (entries) | Omitted / drugs | Rate (95% CI) |
|---|---:|---:|
| 3-5 | 16/93 | 17% (11%–26%) |
| 6-10 | 77/318 | 24% (20%–29%) |
| 11+ | 47/289 | 16% (12%–21%) |

## Same drug kept at the top but dropped at the bottom (11 notes)

- `mts_1364`: Atenolol
- `mts_1440`: metoprolol
- `mts_1774`: Seroquel
- `mts_1793`: Synthroid
- `mts_3049`: Ambien
- `mts_3054`: glyburide
- `mts_3335`: Prednisone
- `mts_3350`: Lasix
