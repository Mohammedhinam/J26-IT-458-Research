# Vision caption-label verification QA

Date: 2026-10-14. Branch: vinuthan.
Read-only annotation QA across all 1,096 cached records. No labels/splits approved or changed; no training.

## Fixed QA rules and limits

Explicit grades 0–4 and source non-inflamed wording must be grounded to explicit supported tooth positions. Empty clauses, invalid grades, conflicting positions and declared-count errors require review. Three complete agreeing variants are required for a candidate; the 113-pattern omission never automatically clears a record. Historical needs_review always stays pending.
TXT 0/1 are ROI; 2–6 correspond to MGI 0–4. Only grade-count histograms are compared, never asserted tooth identity. Histogram agreement is necessary evidence here, not clinical validation; equal histograms can conceal per-tooth permutations.
Rules are annotation QA only, uniformly applied to original splits. Test annotations/statistics are not used for model design, selection or final-test inference. RGB originals are not decoded, resized or modified in this task.

## Actual record counts

| Split | Source records | Original needs_review | New QA flags outside historical queue | QA-consistent and historically provisional | Pending union |
|---|---:|---:|---:|---:|---:|
| Training | 732 | 34 | 13 | 685 | 47 |
| Validation | 182 | 53 | 75 | 54 | 128 |
| Test | 182 | 74 | 90 | 18 | 164 |
| Total | 1096 | 161 | 178 | 757 | 339 |

These are source-evidence categories, not cleared training eligibility or approved clinical grades.

## QA issue flags (overlap; do not sum)

| Flag | Training | Validation | Test | Total |
|---|---:|---:|---:|---:|
| annotation_tooth_count_review | 12 | 1 | 3 | 16 |
| caption_txt_grade_histogram_disagreement | 14 | 2 | 2 | 18 |
| declared_tooth_count_mismatch | 1 | 5 | 3 | 9 |
| incomplete_caption_positions | 2 | 119 | 156 | 277 |
| lower_jaw_omission_policy_pending | 2 | 119 | 154 | 275 |
| unsupported_grade_clause | 1 | 5 | 3 | 9 |

## Candidate source maxima, not assigned labels

| Split | MGI 0 | MGI 1 | MGI 2 | MGI 3 | MGI 4 | Candidate withheld |
|---|---:|---:|---:|---:|---:|---:|
| Training | 0 | 12 | 84 | 223 | 366 | 47 |
| Validation | 0 | 1 | 13 | 23 | 17 | 128 |
| Test | 0 | 3 | 2 | 10 | 3 | 164 |
| Total | 0 | 16 | 99 | 256 | 386 | 339 |

## Regression evidence and new examples

- Training 00025: original status provisional; QA flags caption_txt_grade_histogram_disagreement; candidate None; approved grade remains unset.
- Training 00029: original status provisional; QA flags none; candidate 4; approved grade remains unset.
- Validation 01106: original status needs_review; QA flags incomplete_caption_positions, lower_jaw_omission_policy_pending; candidate None; approved grade remains unset.
- Test 01223: original status needs_review; QA flags incomplete_caption_positions, lower_jaw_omission_policy_pending; candidate None; approved grade remains unset.
- Lower-jaw-omission pattern found: 275 records; all remain policy-pending.
- Omission overlap: 114 already in the historical review queue; 161 outside it. The previously documented 113-case subset is included, not replaced or newly resolved.
- Newly flagged means outside the cached 161-record queue, not necessarily first discovery: 00025 was already documented as a sampled concern. The former 934-record hypothetical screen is not a verified clean cohort after this broader QA.
- First newly flagged examples: Training 00025; Training 00052; Training 00122; Training 00224; Training 00277; Training 00289; Training 00298; Training 00469; Training 00575; Training 00649.

## Remaining blockers

Qualified annotation/clinical review, incomplete-caption policy approval, unresolved duplicate groups and participant independence, absent image-level MGI 0 support, and final reviewed target/split manifest. Five-class MGI definitions and RGB → maximum MGI → Grad-CAM architecture remain unchanged. No four-class mapping, model choice, relabel or split policy is implemented.

Historical manifests/reports are preserved. New QA flags supplement, never overwrite, the 161-case history. Detailed QA output is a separate ignored local artifact, not a final label manifest.

## Verification performed

Final synthetic/regression suite: **73 passed, 0 failed** (38 new parser/QA checks + 35 existing Vision checks). All 113 prior omission cases were regression-checked against the new QA output; original statuses/targets/splits matched the cache for all 1,096 rows. The final parser output exactly matched the first recorded QA result. No package installation.

Parser verification initially exposed a false declared-count flag on a tooth-ID list; the count guard was corrected. An initial CSV example read used plain UTF-8 and exposed the BOM header; the production reader and synthetic BOM test use UTF-8-SIG. Neither check failure changed source annotations.
