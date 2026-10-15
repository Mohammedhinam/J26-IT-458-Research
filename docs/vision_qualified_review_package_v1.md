# Vision qualified-review and supervisor decision package v1

2026-10-14 — **PROPOSED / PENDING. No label, policy, grouping, split or training approval.**

Authority: AGENTS.md §§3, 6.1, 13 and supervisor-signed Component 2 proposal §§3.2–3.5 (PDF pp.17–22). Preserve RGB → maximum visible image MGI **0–4** → Grad-CAM; ResNet-50/EfficientNet-B0; separate NHANES branch. Conflicting labels require review and evaluation content must be independent. The partial-caption rule, representative/reservation rule and any change to evaluation units require recorded approval; they are not implicit proposal permissions.

## Open one package

Local entry: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/qualified_review_package_v1_20261014/index.html`.

The same directory contains:

- `review_checklist.csv`: filterable checklist with IDs, original splits, role, evidence, proposed action, blank reviewer/qualification/date/notes, **pending** decision and blank approved grade. Save human responses in a separate reviewed version; nothing automatically imports or activates them.
- `policy_evidence.html`: exact 274 candidate IDs and cached per-caption tooth-position evidence. Technical eligibility is not individual clinical validation.
- `missing_case_evidence.html` / `.json`: three original CSV captions, original TXT text and cached discrepancy evidence for the **17** referrals absent from the historical package.
- `missing_contact_sheets/cases_01.png` and `cases_02.png`: only those 17 additional RGB thumbnails, original colours and aspect ratios preserved; full-resolution originals linked.
- `group_annotation_evidence.html`: cached companion annotation evidence for all 16 multi-image groups; links to source captions/TXT, originals and existing review artifacts.
- `grouping_decisions.html`: separate supervisor grouping/identity decisions, without per-image grades, predictions or model outcomes; reuses NP015 contact sheet.
- `package_summary.json`: counts, overlapping flags, input hashes, original-image preservation metadata and pending approvals.

The existing 48 referral records and contact sheets are linked, not regenerated. Original review files remain unchanged. All record-level artifacts stay in ignored local storage; this aggregate document contains no approved labels or training manifest.

## Exact review accounting

| Record set | Training | Validation | Test | Total |
|---|---:|---:|---:|---:|
| Existing QA-review union | 47 | 128 | 164 | **339** |
| Upper-partial policy candidates, unapproved | 2 | 119 | 153 | **274** |
| Remaining qualified referrals | 45 | 9 | 11 | **65** |

The 274 and 65 are disjoint and cover all 339. The 65 comprise **48 historical referrals + 17 additional referrals**, not 65 new failures. Test `01247` remains in the 65 because of its independent tooth-box count anomaly. The old 113-case policy queue is historical; it must not be added to the current 274.

The 17 additional IDs are Training `00025, 00052, 00122, 00224, 00277, 00289, 00298, 00469, 00575, 00649, 00709`; Validation `00781, 00783, 00789`; Test `00940, 00941, 00942`. All exact 65 IDs and evidence are in the checklist/viewer.

Secondary flags overlap: 18 caption–TXT histogram disagreements, 16 tooth-count reviews, 9 declared-count mismatches, 9 unsupported-grade clauses, 3 incomplete-position flags and 1 pending omission-policy flag. These are **not** disjoint record totals or confirmed clinical errors.

Joint review covers **16 proposed multi-image groups / 36 sources**. Of these sources, 29 belong to the 65 referrals, 3 to the 274 policy candidates (Test `01308, 01310, 01311`) and 4 are supplemental companions (Training `00272, 00571, 00584, 00728`). The latter four plus NP015's two images are **6 context records outside the 339 QA set**. Thus the package references 345 unique source images; it does not create 345 QA failures.

The checklist has **376 decision rows**, comprising 274 policy records + 65 referrals + 6 context records + 16 joint annotation groups + 8 cross-split groups + 1 uncertain pair + 6 methodology decisions. Group/decision rows reuse source IDs and must not be counted as additional images.

## Decisions to obtain

| Checklist scope | Who signs | Evidence / required decision |
|---|---|---|
| `D-PARTIAL`, 274 `POLICY-*` IDs | Qualified annotation reviewer; supervisor for methodology | Accept/reject/revise the optional rule: complete matching C1/C2; every stated C3 shared position agrees; valid jaw-wise TXT grade histograms; no independent anomaly. TXT lacks explicit tooth IDs. Approval of the rule alone does not approve 274 clinical grades; preserve per-record eligibility/label provenance and escalate uncertainty. Strict default remains unchanged. |
| 65 `QA-*` IDs, `JG01–JG16` | Qualified dental/annotation reviewer | Review RGB + all captions + TXT and every content companion jointly. Resolve source meaning, tooth associations, coverage and target provenance; or retain unresolved/excluded status. Never vote across disputed grades or turn missing information into MGI 0. |
| 14 exact pairs, included in joint groups | Qualified dental/annotation reviewer | Cached evidence shows **11 pairs with differing complete tooth maps; 3 with ambiguous coverage/box maps**. Their 28 sources already occur in the 65. Tooth-map disagreement need not change image maximum; document that distinction. Human-expanded group companions require joint provenance review too. |
| `XS01–XS08`, `D-GROUPING` | Supervisor | Eight actual cross-split groups / 18 sources: seven Training–Test, one Training–Validation. Review PROPOSED whole-group Test > Validation > Training reservation and deterministic representative, or specify a proposal-aligned alternative. Do not use grades/outcomes. Original Test has 182 source images versus 180 proposed independent content units; explicitly decide this evaluation-unit change. |
| `NP015`, `D-IDENTITY` | Supervisor + source custodian / qualified reviewer | Training `00591` / Validation `00736`: owner **uncertain**, possible same participant, identity unverified. Obtain reliable provenance or approve a conservative whole-group hold. Neither merge automatically nor retain as proven independent. The 47 distinct-photo decisions also do not prove different participants. |
| `D-MGI0` | Supervisor, with qualified dental advice | Reliable image-maximum MGI 0 support absent; MGI 1 scarce. Keep five definitions unchanged. Document feasibility and unsupported-class limitations. Any amended scientific scope/protocol or new data needs explicit approval; no invented healthy examples. |
| `D-MANIFEST`, `D-TRAINING` | Qualified reviewer + supervisor | After decisions, create a new draft with signed final labels/provenance, authentic participant/group identity, approved analysis membership, all aliases/holds/exclusions, reviewer/date and final checksum freeze. Independently approve the training protocol and seal Test; this package activates nothing. |

Current reconciliation remains **1,076 proposed groups**, with all 54 human decisions retained (47 distinct / 6 visually same / 1 uncertain). The six same-content edges form five joined components; there is no ninth confirmed cross-split group from NP015. No count here is a cleaned, training-eligible cohort.

## What can unblock a manifest, and what still cannot be claimed

Obtain the written partial-caption policy decision and qualified record/group adjudications first; obtain supervisor grouping/NP015/identity and MGI-0 feasibility decisions in parallel. Approved exclusions/holds are permissible only through explicit, source-accounted decisions. All retained records, including those outside the flagged set, still require authenticated final label and eligibility provenance. Then a separately authorised draft manifest can be checked and frozen.

**Participant identity is still a hard integration blocker:** content-group IDs are not participant IDs. The current trainer requires genuine verified participant IDs and authenticated approval evidence. Supervisor acknowledgement that identities are unknown does not satisfy that code guard. Resolve the evidence or obtain a separately approved, proposal-aligned interface/protocol decision; never use placeholder IDs or bypass callbacks.

Missing MGI 0, scarce MGI 1, small selected dataset, uncertain participant independence and annotation reliability remain scientific limitations even after content-review decisions. Synthetic Colab verification (8 + 51 selected tests) establishes runtime behaviour, not dental-image performance or clinical validation. No training or Test inference occurred.

## Package verification

Cached-set partition and per-split counts checked exactly; reviewed-input hashes/provenance matched reconciliation v2. Checklist CSV round-trips to all 376 prepared records; every new decision remains pending and every approved grade is blank. Existing links/contact sheets are reused; only the 17 missing case evidence records and two RGB contact sheets were created. Source/code/report preservation and link checks are recorded in the factual logs. No full audit, relabeling, resplit, installation, model run, commit or push.
