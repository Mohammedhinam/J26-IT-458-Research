# Held-development review workflow v2

2026-10-16 · vinuthan · Cached evidence only. No new audit, images, labels, split or eligibility change.

One local review entry now covers all **181 development holds** while preserving the old Training52 package:

data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/development_held_review_v2_20261016/index.html

The same directory contains pending decision CSV, selected cached evidence JSON, role instructions, summary and verification. Search/filter by Training or Validation. No images preload; source RGB links open only on deliberate human action. No Test source links/records/grade objects are included. Existing 914-record development DRAFT and split-first cached QA reader are reused; skipped/Test bodies are discarded before JSON decoding. No original CSV/TXT/RGB read or new source hashing/extraction.

## Disjoint work queues

| Review route | Training | Validation | Total |
| --- | ---: | ---: | ---: |
| Partial-caption policy / qualified annotation review | 2 | 119 | 121 |
| Other annotation referrals | 45 | 9 | 54 |
| Additional group companions | 4 | 0 | 4 |
| NP015 identity uncertainty | 1 | 1 | 2 |
| Total held | 52 | 129 | 181 |

The 54 annotation-referral records are a different unit from the already reviewed 54 near-duplicate pairs. Do not repeat that completed pair review or add overlapping flag counts to181.

Separate overlapping boundaries: Training has9 protected-evaluation aliases,1 source proposed for Validation reservation and1 NP015 source. Validation has the other NP015 source. Multi-image-group flags cover25Training/1Validation and cross-split flags10Training/1Validation. These overlap the table; they are not additional exclusions.

The previous conditional Training recovery bound remains **41 sources /33 proposed content units**, only if proposed reservations are accepted and all label/group/identity requirements are resolved. These are not33 approved images or distinct people. Resolving121 partial flags mainly expands Validation evidence; only2 are Training. No supported whole-image MGI0 recovery is established.

## Required human decisions

- Qualified dental/annotation reviewer: verify source evidence and original RGB where needed; record actual identity/qualification/date/evidence and grade only when clinically supported. Keep uncertainty otherwise. TXT is annotation corroboration, not model input or tooth-ID ground truth.
- Supervisor/source custodian: decide partial-caption methodology, duplicate representatives/reservations, NP015 and participant-independence limitations. A grade decision cannot release protected evaluation content.
- Project owner: organize records and real reviewer responses in a new version; do not invent clinical qualifications or fill grades from model predictions.

All181 CSV decisions remain pending; reviewer/date/proposed-grade fields are blank and approval/eligibility false. This viewer has no automatic import/approval/activation. A future approved manifest requires verified human decisions plus all existing gates; this task creates none.

## Actual verification

**17 generated tests passed,0failed/errors/skipped.** Includes malformed Test and unselected-body non-deserialization, metadata-first rejection, coverage/duplicates, inactive human fields, forbidden Test/approved state and overlap accounting.

**9 artifact assertions passed:** exact181 unique IDs,52/129split,all pending/blank,no approval,old52IDs preserved,181cards/no preloads,181development-only source links,disjoint partitions and unchanged cached input hashes. Not a repeated dataset/model audit or full repository test.

Input DRAFT SHA b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1; QA SHA5e56facd669fee9492412bb9795c8a25cf520783148e0f651b73aa8a8e6e318f. Actual output hashes are in the ignored summary. Original sources, manifests, review decisions and all181holds unchanged; no training, installation, cloud action, commit/push.

Teaching: filter by technical_candidate=false, not training_eligible=false (all914 have the latter false). Split metadata must be read before label bodies; missing/uncertain evidence never becomes MGI0. Reviewer fields record human decisions; they do not authenticate them or grant training approval.

Viva: **Why not add all121 partial cases to Training?** Only2 are originally Training;119 are Validation, and none has received new qualified approval.
