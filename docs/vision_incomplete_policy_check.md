# Optional incomplete-caption policy check

Date: 2026-10-14. Branch: vinuthan.
Check-only mode, not policy activation. Strict remains the default. No approved labels or review statuses changed.

Requirements: matching complete Caption 1/2; all six stated upper positions in Caption 3 match; no additional independent anomaly; valid upper/lower TXT grade histograms. Each tooth centre must belong to exactly one documented jaw ROI, with six tooth boxes per jaw. Ambiguous geometry is rejected, not assigned by left-to-right rank or nearest jaw. Jaw metadata does not prove FDI tooth identity.

| Original split | Omission records checked | Policy-eligible candidates | Blocked by independent evidence |
|---|---:|---:|---:|
| Training | 2 | 2 | 0 |
| Validation | 119 | 119 | 0 |
| Test | 154 | 153 | 1 |
| Total | 275 | 274 | 1 |

Every checked record still requires qualification/approval; eligible does not mean clinically validated or training-ready. Original candidate_image_maximum, qa_requires_review and historical fields are unchanged.

## Blocked records

- Test 01247: annotation_tooth_count_review

## Approval and boundaries

This optional configuration only tests an approval proposal. Activating an incomplete-caption label policy, accepting individual clinical labels and freezing final eligibility/splits require qualified reviewer/supervisor approval with provenance and date. MGI 0–4, RGB → maximum visible MGI → Grad-CAM and the independent questionnaire architecture are unchanged. Missing information is never zero.
No full dataset/image re-audit, model fitting, selection, inference or test evaluation. Final-test annotations are examined exclusively for this authorized QA check. Criteria and geometry rules are fixed independently of performance outcomes. Historical QA flags and original statuses are not cleared; evidence candidates never automatically reduce the unresolved queue.

## Configuration and actual verification

- `verify_record(..., policy="strict")` remains the default and has the same strict result fields/values as before.
- `policy="check_upper_partial"` adds only `incomplete_policy_check`. It never changes `candidate_image_maximum`, approved grade, source label, original status/split, or `qa_requires_review`.
- CLI opt-in: `--policy check_upper_partial --cached-qa <existing QA JSON>`, plus existing `--staging`, `--report` and `--details` arguments. The CLI selects only cached omission records; fresh selected CSV/TXT checks reject stale cached evidence. Source images are not opened. Existing outputs cannot be overwritten.
- Lower/upper ROI code mapping is 1/0; tooth codes 2–6 are MGI 0–4. Unique centre-in-ROI membership is a conservative jaw evidence rule, not clinical tooth identification. Both complete captions must match each jaw histogram; the six shared upper sites must agree in Caption 3. Additional duplicate/annotation/source flags block eligibility.
- Final tests: **90 passed, 0 failed, 0 skipped** (17 new policy checks + 73 earlier checks). Live local annotation regression confirms 274 expected candidates and Test 01247 exclusion, with unchanged cached fields. Synthetic tests cover unchanged strict default, jaw swaps hidden by whole-image histograms, ambiguous/outside/reversed ROIs, non-six jaw counts, caption conflicts, independent duplicates, unsupported clauses, deterministic copying and CLI avoidance of full dataset QA.
- Exact evidence candidates: Training 01100–01101; Validation 01102–01220; Test 01221–01246 and 01248–01374. Test 01247 remains blocked by eleven total tooth boxes, including only five lower boxes.
- All 275 checked records remain pending qualified approval. The broader historical QA union remains 339 flagged records; this task does not clear 274 of them or declare a final eligible cohort. All five MGI definitions and missing-class-0 blockers remain unchanged.

Approval checklist: qualified reviewer/supervisor accepts the written evidence policy and geometry limitations; reviewer records individual/group decisions and provenance; final labels/eligibility/split manifest receive separate approval; training requires separate authorization. Check-mode selection is not that authorization.
