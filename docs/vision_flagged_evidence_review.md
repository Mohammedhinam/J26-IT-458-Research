# Focused evidence review of the 161 flagged Vision records

Date: 2026-10-13. Branch: `vinuthan`. **161 reviewed, 0 adjudicated/resolved, 161 remain needs_review.**

Read the signed proposal pages 17–18/22, supplied AGENTS.md, and existing Vision audit/verification reports. Reused the extracted data and cached duplicate hashes. No extraction, download, full-dataset re-audit, relabel, new clinical grade, split change, training, installation, commit or push.

## What was examined and what was not adjudicated

For each of the 161 original flagged records (34 training, 53 validation, 74 test), read and compared all three CSV captions, the corresponding original TXT and the original RGB file: **483 captions, 161 TXT files and 161 photos**. Filename/variant matching passed. The 27 original-colour contact sheets were visually screened, displaying source thumbnails and separate raw-TXT overlays. Full-resolution RGB originals remain linked in the reviewer report. No clinical appearance/severity rating was assigned; a thumbnail screen is not a qualified dental examination.

Caption evidence separates explicit numeric phrases from those attached to actual FDI tooth positions. Empty tooth lists remain unsupported, not grade 0. Non-inflamed text is recorded as source wording with positions, not a newly approved target. TXT interpretation uses the proposal's documented 0/1 jaw ROI and 2–6 MGI 0–4 correspondence, previously corroborated by examples. ROI order was consistent in this cohort. Site-level comparison sorts six boxes per jaw left-to-right only when that configuration exists; this is a **positional hypothesis**, not verified clinical tooth identity. Sixteen records have ambiguous box count/rank; none receives a forced positional map. No invalid TXT numeric line or filename mismatch was found.

All original source labels, provisional maxima, duplicate groups and split memberships are preserved. Final-test annotations/photos were used exclusively for this approved evidence review, never model fitting or selection. The other 935 records were not re-audited; the previously sampled concern outside this cohort remains outside this task.

## Referral categories — mutually exclusive, not corrected labels

| Final evidence category | Training | Validation | Test | Total | Required next action |
|---|---:|---:|---:|---:|---|
| Consistent evidence including duplicate companions, with no open annotation dispute | 0 | 0 | 0 | 0 | No record is cleared in this flagged cohort |
| Conflicting/incomplete caption evidence: lower-jaw description omitted | 0 | 47 | 66 | 113 | Qualified annotation-policy approval; escalate clinical/site doubt |
| Requires qualified dental/tooth-annotation adjudication | 34 | 6 | 8 | 48 | Review original photo, all source descriptions/boxes and companions |
| Still unresolved | 34 | 53 | 74 | 161 | Preserve needs_review until approved decisions |

Within an individual file's evidence, 17 records have consistent captions/site associations/TXT, 117 have incomplete evidence and 27 have direct source/box/duplicate-target concerns. The 17 individually consistent records are **not group-wide clear**: their identical-photo companions have different tooth annotations or incomplete/ambiguous coverage. The final table incorporates those companion discrepancies and escalates four unsupported maximum-grade placeholder cases. This is referral triage, not proof that all 48 clinical labels are wrong.

## Main findings

1. **All 113 historical caption-conflict records share the same structural pattern:** captions 1/2 have supported positions for all twelve teeth; caption 3 describes only the six upper-jaw sites and omits all six lower-jaw sites. Parsed positions that are present agree with the positional TXT evidence. Historical 81 maximum disagreements and 32 same-maximum grade-set disagreements remain evidence, not automatically corrected outcomes. Missing lower-jaw grades must not become zero. Approval is required before relying on complete variants or repairing a template.
2. **Four of the seven prior CSV–TXT maximum discrepancies** contain numeric maximum-grade phrases with empty tooth lists. The other three contain substantive supported tooth-grade source disagreement. No new target is chosen in either subgroup.
3. **All fourteen exact-duplicate groups need joint source review:** eleven pairs have different complete positional TXT grade maps; three have an incomplete/extra-box companion, preventing a reliable pairwise map. Eight pairs cross published splits. Same maximum grade does not imply the same per-tooth evidence. These findings extend the earlier three maximum-label-disagreement pairs, rather than replacing them.
4. **48 records require grade/site/box adjudication** under the stated triage criteria: 28 duplicate entries + 13 nonduplicate tooth-count records + 3 substantive caption–TXT disputes + 4 unsupported maximum-grade clause cases. These categories are disjoint here. The 48 entries represent **34 distinct cached photo contents**, not 34 verified people.
5. **113 additional records require incomplete-caption policy adjudication**, with dental escalation if reviewer doubts remain. Independent clinical regrading is not asserted necessary from source consistency alone. All 161 still need an approved disposition; none is cleared or silently excluded.

The historical 161-record union remains exactly 113 caption conflicts + 7 caption–TXT discrepancies + 28 duplicate entries + 13 other tooth-count records. Secondary tooth-count and duplicate-label flags overlap; they are not additional images. Broader participant identity remains unknown. The absence of reliable image-level maximum-MGI-0 examples and five-class feasibility remain unresolved from prior evidence; this review does not manufacture zero labels or change the target.

## Reviewer-friendly artifacts — ignored local storage only

Artifact root:

`/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/review_evidence_2026-10-13/`

| File | Contents |
|---|---|
| `index.html` | Search/filter by image ID, split and referral; all three verbatim captions, original TXT, site-comparison table, RGB original links, duplicate companion links and recommended action |
| `reviewer_cases.csv` | All 161 record IDs, original splits, source evidence, discrepancies, referral category and pending reviewer fields |
| `clinical_adjudication_required.csv` | Exact 48-record clinical/tooth-annotation referral list, with all source evidence and reasons |
| `annotation_policy_review.csv` | Exact 113-record omitted-lower-jaw policy review list |
| `case_evidence.json` | Structured case evidence; original provisional targets retained, approved grade fields blank |
| `duplicate_group_review.json` | All 14 groups, original member paths/splits and pairwise evidence differences |
| `review_summary.json` | Counts and explicit scope limitations |
| `review_contact_01.png` … `review_contact_27.png` | Final referral captions; source-colour thumbnail beside raw-box overlay, never a generated clinical judgment |
| `contact_01.png` … `contact_27.png` | Initial intrarecord-screen sheets retained as provenance; use final sheets for group-aware referral captions |
| `build_review.py`, `finalize_review.py` | Artifact-generation/triage recipe only; does not update training data, source labels or source manifests |

Full per-image evidence, photos, captions and reviewer lists remain ignored in data/. The original CSV/TXT/images are unchanged. Contact sheets are RGB, aspect-preserving previews with no grayscale, enhancement or colour grading. Source and overlay are separate; box colours identify raw codes only. Full-resolution originals should be opened for qualified review. Reviewer/date/decision/approved-grade fields remain pending/blank; there is no ground-truth declaration or software-suggested replacement target.

## Verification and limitations

- Exact case coverage: 161 distinct flagged paths; three variants each; no new/dropped records. Original split counts and provisional maxima matched cached evidence.
- Viewer: 161 original-photo elements; all 515 local image/artifact/companion links resolved. CSV referral lists partition the cohort as 48 + 113 with no overlaps.
- Every exported review status is needs_review, every approved-grade field blank; source records/manifests remain unchanged.
- Twenty-seven contact pages were viewed for visual screening; representative final pages were checked after referral captions changed. Photo/overlay pixel regions were compared with initial sheets and remained identical. A footer-layout clipping issue was fixed in these newly created artifacts only.
- Small mechanical assertions checked supported positions, empty-list handling and report coverage. This task introduced no model code or new training tests; prior 35-test audit evidence remains historical, not a new test run.
- An initial preservation assertion falsely failed because five cached-manifest nanosecond timestamps were rounded by JSON/JavaScript numeric serialization. Corrected comparison precision; all five prior manifest byte hashes matched, source metadata was unchanged, and all 483 exported caption records/161 TXT texts matched their originals. Existing dirty-file byte hashes and original log prefixes also matched.
- Positional parsing/box ordering may miss unusual wording, orientation or tooth identity. Findings are source-evidence flags for a reviewer, not automated clinical adjudication. Reviewers may escalate further cases; unresolved uncertainty stays explicit.

## Approval required — stop

Approve a qualified reviewer for the 48 listed records and the 113 incomplete-caption policy cases. The reviewer must use full RGB images and source provenance, record decisions/date, and resolve duplicate groups jointly. No reviewer has supplied an approved grade in this task. Any later label change, source-priority rule, eligibility/group/split manifest or training requires separate explicit approval. Preserve originals and final-test independence throughout.

Teaching check: matching two captions is evidence, not automatic adjudication; a duplicate photo can have different source annotations; needs_review is a pending decision, not a fifth or healthy class.

Viva: Why are all 161 still unresolved after this review? Because the review documents source agreements/discrepancies and prepares a qualified decision, while no authorized reviewer has approved labels or group handling.
