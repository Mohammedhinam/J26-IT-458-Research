# Focused Vision label verification and duplicate-handling decision plan

Date: 2026-10-13. Branch: `vinuthan`. **PLAN ONLY — implementation and training await approval.**

## Sources and scope

Read the supplied AGENTS.md, signed `RP-IT23311022 (2).pdf` pages 17–18/22, existing Vision reports/options, cached `audit_verified/integrity_results.json`, selected extracted CSV/TXT records, and three original training photos. Reused extracted data; no extraction, image-wide decode/hash audit, label edit, resplit or training was performed. Existing code, reports, manifest and dirty work remain unchanged; this plan and appended factual logs are the only changes.

Local source root: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/`. Verified inventory JSON SHA-256: `0c420ca47fe63f6eeb0a9b613286c6329490eb0a9fecd163671a49760cd0f969`.

The proposal explicitly specifies maximum visible MGI per image, captions as primary label evidence, mapping review, and a new participant-grouped split if published groups overlap. [Original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11462013/) describes tooth annotations/captions. A live paper refresh was blocked by CAPTCHA/403; its previously read content and historical report were reused, alongside the available signed proposal Table 4. No new source confirmation or clinical validation is claimed.

## What actual examples verify

| TXT code | Documented meaning | Local example evidence | Verification limit |
|---:|---|---|---|
| 0 | Maxillary ROI | `00029` box centre y=0.472109 covers upper jaw in inspected photo | Structural correspondence; not severity |
| 1 | Mandibular ROI | `00029` box centre y=0.657675 covers lower jaw | Structural correspondence; not severity |
| 2 | MGI 0 | `00029` upper-left tooth code 2 corresponds to caption's non-inflamed tooth 13 | Source annotation correspondence, not independent clinical grading |
| 3 | MGI 1 | `00029` upper teeth 22/23 have code 3 and captions grade 1 | Same limit |
| 4 | MGI 2 | `00029` upper teeth 12/11/21 and lower tooth 41 have code 4 and captions grade 2 | Same limit |
| 5 | MGI 3 | `00029` lower teeth 43/42/31 have code 5 and captions grade 3 | Same limit |
| 6 | MGI 4 | `00029` lower teeth 32/33 have code 6 and captions grade 4 | Same limit |

Tooth ordering was checked by sorting small boxes left-to-right within the observed upper/lower rows, against the captions and original photo. `00029` upper codes are `[2,4,4,4,3,3]`; lower codes `[5,5,4,5,6,6]`. `00001` gives a second correspondence for grades 1–3: upper `[3,4,3,3,3,4]`, lower `[5,5,5,4,5,4]`. The ROI boxes cover jaws; codes 2–6 describe tooth-region annotations. The signed proposal's mapping is technically corroborated in these examples, rather than inferred merely from numeric range. Qualified annotator approval remains necessary before freezing labels/mapping; appearance was not assigned new clinical grades here.

`00025` was also visually inspected. Its caption maximum and TXT maximum both equal 4 under the documented mapping, but a code-2 tooth box has no corresponding non-inflamed description, and some tooth-level assignments differ. Thus agreement on maximum does not prove complete annotation agreement. This is an additional sampled review concern outside the historical 161 flags; that inventory was not changed. Do not interpret the other 935 provisionally unflagged records as adjudicated labels.

CSV/TXT are annotation evidence only. Future classifier input is RGB image data; TXT coordinates/codes and captions will not be training predictors.

## Tooth-level and image-level frequencies — keep the units separate

Raw annotation-box frequencies under the corroborated documented interpretation (ROI codes excluded):

| Split | MGI 0 / code 2 | MGI 1 / code 3 | MGI 2 / code 4 | MGI 3 / code 5 | MGI 4 / code 6 |
|---|---:|---:|---:|---:|---:|
| Training | 244 | 1218 | 2178 | 3399 | 1751 |
| Validation | 30 | 306 | 774 | 755 | 320 |
| Test | 35 | 307 | 899 | 713 | 221 |
| Total | 309 | 1831 | 3851 | 4867 | 2292 |

These are 13,150 raw tooth-box annotations, not independent people or fully adjudicated teeth. Duplicate photos and the 16 non-12 tooth-box files remain included. All five tooth-code rows have at least one mismatch against the paper's published counts; not every individual cell mismatches (e.g. test code 5 is 713 in both). No source count is repaired.

Image maxima from raw TXT codes, excluding ROI, are diagnostic quantities only:

| Split | Max 0 | Max 1 | Max 2 | Max 3 | Max 4 |
|---|---:|---:|---:|---:|---:|
| Training | 0 | 12 | 88 | 230 | 402 |
| Validation | 0 | 2 | 18 | 83 | 79 |
| Test | 0 | 3 | 25 | 87 | 67 |
| Total | 0 | 17 | 131 | 400 | 548 |

Existing caption-derived provisional maxima, requiring consistent numeric grade sets across three variants:

| Split | Max 0 | Max 1 | Max 2 | Max 3 | Max 4 | Unresolved caption variants |
|---|---:|---:|---:|---:|---:|---:|
| Training | 0 | 12 | 87 | 229 | 404 | 0 |
| Validation | 0 | 2 | 17 | 60 | 56 | 47 |
| Test | 0 | 3 | 17 | 56 | 40 | 66 |
| Total | 0 | 17 | 121 | 345 | 500 | 113 |

Neither table supplies approved training labels. Raw maxima retain disputed annotations; caption maxima may include empty tooth-list placeholders. Counts retain original memberships and duplicate entries. No eligibility adjustment or model choice uses test labels.

## Reconcile the 161 historical review records without double-counting

| Mutually exclusive review bucket | Training | Validation | Test | Total |
|---|---:|---:|---:|---:|
| Caption grade-set conflicts | 0 | 47 | 66 | 113 |
| Caption–TXT maximum discrepancies | 3 | 4 | 0 | 7 |
| Exact duplicate entries, including their secondary issues | 20 | 1 | 7 | 28 |
| Tooth-count issues outside duplicate groups | 11 | 1 | 1 | 13 |
| Union | 34 | 53 | 74 | 161 |

The 113 caption conflicts comprise 81 different maxima and 32 matching maxima with different grade sets. Matching maxima still need review, particularly when a caption omits a jaw or has placeholder tooth lists.

Across all issue flags: 16 tooth-count records include 3 duplicate entries; 6 duplicate-target-disagreement records are entirely inside the 28 duplicate entries; one record has both secondary issues. Near-duplicate fingerprint flags refer to those same 28 exact-duplicate entries, not another 28 images. Category overlaps are reconciled by file identity; they are not independent exclusions. The new sampled `00025` concern should be added to the reviewer backlog after approval without silently rewriting the historical 161.

### Focused examination of all seven caption–TXT discrepancies

| Sample | Numeric caption maximum | TXT diagnostic maximum | Actual annotation issue | Proposed disposition |
|---|---:|---:|---|---|
| Training `00097` | 3 | 2 | All three captions explicitly attach grade 3 to tooth positions; TXT has no code 5 | Qualified reviewer compares both sources/photo; no preferred source assumed |
| Training `00162` | 4 | 3 | Grade-4 phrases have empty tooth lists; grade 3 has the actual positions | Review placeholder grammar and image; no automatic 4→3 change |
| Training `00358` | 4 | 3 | Captions attach grade 4 to lower teeth; TXT contains grades 2/3 under mapping | Qualified reviewer; substantive disagreement |
| Validation `00782` | 4 | 3 | Grade-4 phrases have empty tooth lists | Same placeholder review, no automatic relabel |
| Validation `00786` | 4 | 3 | Grade-4 phrases have empty tooth lists | Same |
| Validation `00818` | 4 | 1 | Grades 2–4 have empty tooth lists; normal/grade-1 phrases specify teeth | Same; empty phrases do not constitute grounded tooth labels |
| Validation `00821` | 1 | 2 | Captions specify normal/grade-1 teeth; TXT assigns all twelve code 4 | Qualified reviewer; substantive disagreement |

All three variants were directly read for these seven records. Four discrepancies have unsupported maximum-grade phrases with empty tooth lists; three have substantive source disagreements. These are explanatory triage findings, not adjudication. The existing regex detects numeric phrases without proving associated tooth positions. After approval, a parser revision should flag unsupported clauses and retain uncertain records for review, with targeted synthetic tests; it must not silently settle labels by selecting TXT, first caption, majority or union. A complete placeholder census was not run, so the sample concern is not an exhaustive new anomaly count.

## Maximum grade and five-class feasibility

The maximum is defensible as a prespecified summary of the highest reliably annotated visible tooth-region grade: it follows proposal page 17, is reproducible after adjudication and respects ordinal severity. It is not full-mouth disease severity, a patient diagnosis or the dataset's original captioning task. It is sensitive to one erroneous high-grade clause and cannot be defended when captions lack actual tooth grounding or visible coverage. Qualified annotation review, provenance and explicit rules for mixed grades/ungradable regions are required.

MGI 0 exists at tooth level (309 boxes in 133 images), but normal teeth coexist with higher-grade teeth. `00029` includes a normal upper tooth and grade-4 lower teeth, so its maximum is positive. No raw TXT has only code-2 tooth boxes; no reliable caption maximum-0 image was found. Placeholder-positive captions are an additional parsing concern, but they do not establish missing all-normal photographs.

An evidence-backed image-level five-class comparison is **not presently feasible**: there is zero supported class-0 image data. A five-output network is technically possible but would neither learn nor validate grade 0; unsupported-class recall/AUROC cannot be presented as measured performance. Four observed positive maximum grades may support a narrower task after review, but that needs supervisor approval/proposal amendment. Alternatively an approved independent all-normal image source/protocol could address support, with licence/domain/group/split checks. Switching to tooth-level five-class classification would change the target unit and scope and requires separate approval. None is selected here. Never use ROI code 0, missing captions, healthy individual teeth or fabricated examples to fill image class 0.

## Non-destructive duplicate/group policy — recommended for approval

1. Preserve every source image, caption/TXT and published membership as provenance. Build a **new versioned analysis manifest**, not physical file moves/deletions. Group exact byte/pixel-identical aliases together; add verified participant identifiers and confirmed near-duplicate relations where available. Hash groups are a minimum content grouping, not proof of different patients outside those groups.
2. Adjudicate labels jointly for duplicate groups, especially the three pairs with conflicting maxima. Select one representative per identical photo using a predetermined label-blind ordering; retain all aliases as provenance. Do not choose a copy because its label or later model result is convenient. A reviewer-approved group label and representative choice are separate decisions.
3. Recommended test-protection policy: reserve all groups containing an original test member wholly for final testing; reserve validation-linked groups from training too. Prevent every alias entering development. Within-training aliases count once. This creates a proposed group-resolved split/eligibility manifest with original membership retained alongside it. Do not tune on original test labels or predictions; adjudication is dataset quality work only.
4. For **known duplicates only**, this reserved-destination scenario gives 718 training / 182 validation / 182 test distinct contents, total 1,082: seven train–test aliases and one train–validation alias leave development, six within-training aliases count once. This is an illustrative policy calculation, NOT a created split or a final eligible cohort. Unresolved labels, additional identity/near-duplicate evidence or a scope change may alter counts.
5. Proposal page 22 explicitly requires a new participant-grouped split if overlap is detected. Supervisor must approve whether the reserved-test group-resolved manifest satisfies that protocol or requires a full new grouped partition. Without documented participant IDs, call any hash-only partition **content-grouped**, not verified participant-grouped. Approve grouping basis, unknown-identity limitation, eligibility, final counts and deterministic split/representative rules before implementation. If full repartition is required, approve seed/proportions before building it; no result-driven choice among splits.
6. Freeze reviewed labels, group IDs and the new manifest before any ResNet-50/EfficientNet-B0/majority comparison. Final test groups stay outside fitting, augmentation, hyperparameter selection, calibration and model selection. Future inputs remain RGB photos only. No manifest, label or file changed in this task.

## Concise decision table

| Topic | Verified finding | Unresolved blocker | Recommended action / approval |
|---|---|---|---|
| ROI/MGI code mapping | Proposal Table 4 is corroborated by spatial/caption examples: 0/1 ROI, 2–6 MGI 0–4 | Numeric prose inconsistency and actual annotation errors; not clinical validation | Qualified annotator signs off mapping and example provenance before freezing targets |
| 161 review records | 113 + 7 + 28 + 13 exclusive buckets; secondary overlaps accounted for | No labels adjudicated; maximum agreement can hide tooth disagreements | Reviewer works by record/group with all variants, TXT and image; add sampled concern; retain unresolved status |
| Parser grounding | Four of seven discrepancies contain empty maximum-grade tooth lists | Current numeric regex lacks clause grounding; wider extent unknown | Approve conservative unsupported-clause flagging and focused tests before code changes |
| Image MGI 0 | Tooth-level zero annotations coexist with positive grades; image-level zero support absent | Current dataset cannot substantiate all five image classes | Supervisor chooses maintain/revise target or approve additional all-normal data; no automatic zero assignment |
| Duplicates | 14 pairs, 8 across splits; 3 pairs have different caption maxima | Published split not independent; broader participant linkage unknown | Approve new content/participant-group manifest and reserved-test policy or full grouped partition; no current resplit |
| Maximum target | Explicit proposal target; useful ordinal summary after reliable labels | Sensitive to placeholder phrases/annotation error; not a validated diagnosis | Keep prespecified maximum provisionally; qualified adjudication and scope approval required |

## Approval checklist — stop here

- [ ] Qualified reviewer approves the technical class mapping and distinguishes it from clinical grade validation.
- [ ] Approve written adjudication rules for conflicting/missing/empty-position captions and inconsistent tooth boxes; all changes require reviewer/evidence/date provenance.
- [ ] Approve review of historical 161 records, duplicate groups and the additional sampled tooth-level concern; decide how unresolved labels remain excluded from any future eligibility manifest without deleting originals.
- [ ] Supervisor decides how to handle absent image-level MGI 0 support and any proposal/scope amendment.
- [ ] Approve duplicate representative rules and the reserved-test group-resolved policy, or specify a new participant-grouped partition; accept/report limitations if patient identifiers remain unavailable.
- [ ] Approve final eligibility/group/split definitions and any seed/proportions before implementation; preserve all original membership/source labels separately.
- [ ] After adjudication, grouping and manifest verification, give **separate training approval**. No test-driven model choices permitted.

Teaching check: a code-2 normal tooth is not an image-level zero label; 161 means the union of affected image records, not the sum of overlapping flags; identical photos must belong to one analysis group even when filenames differ.

Viva: Why not keep one duplicate in training and its other filename in testing? The model sees identical pixels during fitting, so that test observation is not independent. Group aliases together, preserve originals and approve the new analysis manifest before training.
