# Broad probe on real notes: qwen2.5:3b

Notes: 148, valid JSON: 147.

- Target drug (picked from the medication section) missing: 33/147 = 22% (95% CI 16%–30%)
- Notes with at least one lexicon drug omitted: 66/147 = 45% (95% CI 37%–53%)
- Notes with at least one extra drug (not from the medication section): 38/147 = 26% (95% CI 19%–33%)

## Where extra drugs came from

| Source of extra drug | Entries | Notes affected | Examples |
|---|---:|---:|---|
| not_in_note | 46 | 28 | Multivitamin (mts_2547); multivitamin daily (mts_1396); multivitamin daily (mts_3183); Lopressor 25 mg (mts_3105) |
| other:HISTORY OF PRESENT ILLNESS | 9 | 5 | Lovenox 2.5 mg subcutaneous q24h (mts_2561); Zosyn 225 mg q8h (mts_2561); vancomycin 1g q8h (mts_2561); Darvocet 100 mg q.6h. (mts_1804) |
| other:AXIS V | 4 | 1 | Lorazepam 0.5 mg p.o. q.12h. (mts_1801); Fexofenadine 180 mg p.o. q.d. (mts_1801); Flonase 50 mcg b.i.d. (mts_1801); Lorazepam 0.5 mg p.o. p.r.n. anxiety and agitation (mts_1801) |
| other:ASSESSMENT AND PLAN | 3 | 2 | pregabalin 50 mg three times a day (mts_3108); Oxycodone 5 mg q2h as needed (mts_3109); Lorazepam 0.25-0.5 mg qhs as needed (mts_3109) |
| other:RECOMMENDATIONS | 3 | 2 | Campral 666 mg q.d. (mts_1790); Trazodone 50 mg q.h.s. (mts_1790); PhosLo 800 mg t.i.d. (mts_3049) |
| other:PLAN AND SUGGESTION | 3 | 1 | Percocet 0.25/325 mg q6h (mts_2769); Morphine sulfate 10 mg q4-6h as needed (mts_2769); Calcium with vitamin D (mts_2769) |
| other:MEDICATIONS | 2 | 1 | Avelox 400 mg p.o. daily (mts_3416); guaifenesin 10 cc p.o. q.6h. p.r.n for cough (mts_3416) |
| other:NEW MEDICATIONS | 2 | 1 | Prednisone 20 mg p.o. daily for seven days (mts_3971); Flonase nasal spray daily for 30 days (mts_3971) |
| other:HOSPITAL COURSE PER PROBLEM LIST | 1 | 1 | Labetalol p.r.n. for systolic blood pressure greater than 200 (mts_3413) |
| other:PHYSICAL EXAMINATION | 1 | 1 | Physical therapy (mts_2769) |
| other:PLANS | 1 | 1 | K-Tab 10 mEq (mts_1350) |
| other:LABS | 1 | 1 | Sodium Bicarbonate 650 mg three tablets t.i.d. (mts_3049) |

## Real allergies: does an allergen appear on the active list? (real notes, no edits)

Notes with a drug-like word in ALLERGIES: 51. Allergen on active list: 2/51 = 4% (95% CI 1%–13%).

- `mts_3154`: Lorazepam 0.5 mg every 8 hours as needed for anxiety
- `mts_3003`: baby aspirin 81 mg daily, Pravachol 10 mg daily
