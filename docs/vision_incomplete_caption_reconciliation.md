# Focused reconciliation of 113 incomplete-caption records

Date: 2026-10-13. Branch: `vinuthan`. Evidence analysis only; **all 113 remain needs_review**. No approved grades, policy implementation, split change or training.

Reused `vision_flagged_evidence_review.md` and the existing ignored `annotation_policy_review.csv` / `case_evidence.json` reviewer artifacts. Selected exactly their 113-record list; did not repeat the 161-image audit, extraction or image-content checks. Original train/validation/test membership is retained.

## Checks and actual results

Compared source wording at every explicit tooth position. Checked single, complete position coverage in captions 1/2, six upper positions in caption 3, declared tooth counts and unparsed clauses. Literal non-inflamed wording was compared as source wording, not converted into an approved clinical grade. Independent raw-clause parsing reproduced the cached site evidence, including normal wording. No labels or files in the reviewer artifacts were changed.

| Finding | Training | Validation | Test | Total |
|---|---:|---:|---:|---:|
| Records examined | 0 | 47 | 66 | 113 |
| Caption 1 vs 2 position disagreements | 0 | 0 | 0 | 0 |
| Caption 3 upper-jaw position disagreements | 0 | 0 | 0 | 0 |
| Ambiguous/unparseable position evidence under these checks | 0 | 0 | 0 | 0 |
| Agreement with lower-jaw omission only | 0 | 47 | 66 | 113 |

All 113 Caption 1/2 pairs are identical source text, each describing 12 sites: **1,356 paired site comparisons**. Caption 3 is the exact upper-jaw prefix of those captions, each describing six sites: **678 shared upper-site comparisons**. All six lower sites are omitted in Caption 3. Existing TXT positional hypotheses agree at the described sites for all 113 cases; TXT remains supporting annotation evidence, not model input or independent clinical ground truth. Agreement between identical caption variants does not establish independent annotation reliability.

Examples: Validation `01105`, `01106`; Test `01222`, `01223`. For `01223`, captions 1/2 describe upper grade-2 sites and lower grade-2/3 sites; Caption 3 retains only the upper description. This illustrates source omission, not a proposed replacement target.

## Historical flags and overlap

| Historical flag | Validation | Test | Total |
|---|---:|---:|---:|
| Different numeric maxima across caption variants | 34 | 47 | 81 |
| Same numeric maximum, different grade sets | 13 | 19 | 32 |

These are disjoint subgroups of the same 113 omission cases, not 113 additional disagreements. Double-comma formatting occurs in 16 validation and 19 test records (35 total), overlaps the above groups and did not prevent position/count parsing. Eight test records contain explicit non-inflamed wording; no new clinical grade was assigned. Missing descriptions never imply grade 0.

## Eligibility for approval, not adjudication

All 113 are candidates for a supervisor-approved incomplete-caption policy. No new disagreement-based dental referral was identified within this subset, but clinical correctness and tooth identity remain unverified. Any qualified reviewer doubt requires escalation; no case is cleared here. The separate 48-record adjudication list is outside this reconciliation and unchanged.

Proposed approval criteria must be fixed before implementation: complete and unambiguous Caption 1/2 site coverage/agreement; Caption 3 agreement at every shared site with lower omissions explicitly recorded; provenance and reviewer sign-off; escalation for any source or clinical uncertainty. TXT may corroborate evidence, never automatically choose the grade. Do not tune these criteria against final-test performance or model outcomes. Test annotations were examined only for the authorized dataset-evidence reconciliation, never model development or selection.

All 113 review statuses stayed needs_review and approved-grade fields stayed blank. Read artifact hashes were unchanged. No installations, commits or pushes occurred during the reconciliation itself. Later publication of this report is documentation only; label adjudication, duplicate handling and training require separate approval.
