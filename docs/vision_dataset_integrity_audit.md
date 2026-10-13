# Vision extraction and dataset-integrity audit

Date: 2026-10-13. Branch: `vinuthan`. **Audit complete; training BLOCKED.**

## Extraction safety and actual execution

- Primary: `/Users/vinuthanvinuthan/Downloads/A DENTAL INTRAORAL IMAGE DATASET OF GINGIVITIS FOR IMAGE CAPTIONING 4/Dataset.rar`
- Backup: `/Users/vinuthanvinuthan/Downloads/A DENTAL INTRAORAL IMAGE DATASET OF GINGIVITIS FOR IMAGE CAPTIONING 2/Dataset.rar`
- Both SHA-256: `16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b` — MATCH. Equal hashes establish identical local copies, not independent publisher authentication.
- Metadata: 2,205 entries; 2,195 regular files; no links, special entries, unsafe paths, duplicate member names or case collisions found.
- Declared and fully read file payload: 6,556,351,198 bytes. Largest file: 6,747,577 bytes.
- Available space before successful run: 179,934,396,416 bytes. Limits: 10 GiB total, 100 MiB/member, 3,000 entries, 2 GiB free reserve and 80 million pixels/image.
- First all-entry stdout integrity read FAILED: bsdtar attempted to decompress ten directory entries. No extraction took place during that failure. All regular-file bytes had been read, but the nonzero exit was not accepted.
- Fixed the command to select every validated regular file explicitly. Full integrity read then PASSED: declared byte total matched, exit 0, empty stderr. Extraction selected the same regular members with keep-existing and no owner/permission/ACL/xattr/flag restoration.
- New staging only: `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b`. No overwrite, raw promotion, deletion or source-archive modification. Extracted regular-file paths/sizes exactly matched the 2,195-member inventory.
- Original archive sizes/mtime remained unchanged. Raw images and annotation originals were never rewritten.

## Image verification

| Split | Proposal | Extracted images | Decode successes | Count check | Needs review |
|---|---:|---:|---:|---|---:|
| Training | 732 | 732 | 732 | MATCH | 34 |
| Validation | 182 | 182 | 182 | MATCH | 53 |
| Test | 182 | 182 | 182 | MATCH | 74 |
| Total | 1096 | 1096 | 1096 | MATCH | 161 |

All decoded files are RGB JPEG. No missing images/captions/annotations or decode failures were found.

| Dimensions (width × height) | Images |
|---|---:|
| 6969 × 4641 | 2 |
| 7286 × 4863 | 1094 |

## Confirmed duplicates and split-overlap blocker

SHA-256 found **14 exact duplicate pairs / 28 image entries**. Thus 1,096 file entries contain **1082 distinct byte contents**; do not describe them as 1,096 verified independent photographs/participants.

| Location | Exact duplicate pairs |
|---|---:|
| Test / Training | 7 |
| Training | 6 |
| Training / Validation | 1 |

**8 pairs cross published splits**. Preserve membership now; before training, an approved duplicate/group handling decision and proposal-aligned split review are required. No resplit or drop occurred.
Pixel SHA-256 and exact 64-bit dHash equality recovered the same 14 groups; these are three checks of the same duplicates, not 42 independent groups. No additional equal-pixel/equal-dHash groups were found. Exact dHash equality is a bounded candidate screen, not proof that all cropped, rotated or re-encoded near duplicates are absent.
Three exact duplicate pairs have different caption-derived maximum labels (3 versus 4). Six involved entries are additionally flagged for target disagreement; no label was repaired. Pair-level hashes/paths remain in ignored local JSON/manifests.

## Caption labels: provisional, not an approved final mapping

Filenames/variant IDs match the published splits: three variants per image, 3,288 caption rows. Explicit grade phrases were re-evaluated on extracted CSVs. Tooth positions/counts are not treated as grades. Missing/invalid/conflicting labels are never assigned zero. No invalid numeric grade or missing variant was found.

| Split | Caption max 0 | Max 1 | Max 2 | Max 3 | Max 4 | Caption conflict | Conflicting maxima |
|---|---:|---:|---:|---:|---:|---:|---:|
| Training | 0 | 12 | 87 | 229 | 404 | 0 | 0 |
| Validation | 0 | 2 | 17 | 60 | 56 | 47 | 34 |
| Test | 0 | 3 | 17 | 56 | 40 | 66 | 47 |

These counts describe consistent numeric captions only, including records with other audit issues. They are not training eligibility or final labels. There are 113 caption-grade-set conflicts, including 81 maximum disagreements. All remain needs_review.

## Raw annotation checks and MGI 0 investigation

Blank lines are formatting, not malformed labels. One initial invalid-row flag was a parser false positive; the parser was minimally fixed and regression-tested. Annotation-only checks were refreshed using cached image evidence, without repeating decoding/hashing. No malformed numeric/coordinate row remains; originals were unchanged.
All images have one code-0 ROI and one code-1 ROI. Sixteen annotation files differ from the described twelve tooth boxes: training nine with 13 and three with 11; validation one with 13; test one with 5 and two with 11. These are review flags, not automatic deletions.
Under the published Table 2 mapping HYPOTHESIS only, seven caption-consistent records disagree with annotation maxima. No annotation-derived final target is assigned.

| Raw code | Published Training | Found | Published Validation | Found | Published Test | Found | Check |
|---|---:|---:|---:|---:|---:|---:|---|
| 0 | 732 | 732 | 182 | 182 | 182 | 182 | MATCH |
| 1 | 732 | 732 | 182 | 182 | 182 | 182 | MATCH |
| 2 | 247 | 244 | 53 | 30 | 53 | 35 | MISMATCH |
| 3 | 1209 | 1218 | 328 | 306 | 325 | 307 | MISMATCH |
| 4 | 2190 | 2178 | 765 | 774 | 908 | 899 | MISMATCH |
| 5 | 3392 | 3399 | 751 | 755 | 713 | 713 | MISMATCH |
| 6 | 1764 | 1751 | 337 | 320 | 231 | 221 | MISMATCH |

All published tooth-code count comparisons (codes 2–6) are MISMATCH; report them plainly. The numeric source prose also conflicts with its Table 2. These facts do not authorize repairing annotations or treating a mapping hypothesis as verified.

| Split | Images containing raw code 2 | Images with only code 2 tooth boxes |
|---|---:|---:|
| Training | 101 | 0 |
| Validation | 15 | 0 |
| Test | 17 | 0 |

There are 309 raw code-2 tooth boxes across 133 images, and 140 images contain recognised non-inflamed wording. Every image has a positive explicit caption grade; no reliable image-level maximum-0 example was found. Under the mapping hypothesis, no annotation has exclusively grade-0 tooth boxes either.
The signed proposal page 17 explicitly supports image-level maximum MGI. The dataset supports tooth-level grades/captions; it does not supply a prevalidated maximum-grade classifier. Normal teeth coexist with inflamed teeth, so normal-tooth counts cannot fill an absent whole-image maximum-0 class. Five-class feasibility remains unresolved; no new labeling rule is applied.
Published counts/mapping and per-tooth context: [original dataset paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11462013/), sections 3.3/4.3–4.4. Dataset identity/licence: [Mendeley version 1](https://data.mendeley.com/datasets/3253gj88rr/1).

## Participant independence and final-test boundary

The paper claims one individual per image. Local captions, filenames and annotations supply no documented participant identifier. Metadata header review of 1,096 images found no nonempty ImageDescription, UserComment, ImageUniqueID, CameraOwnerName or BodySerialNumber in the checked fields. Opaque camera MakerNote metadata was not interpreted as participant identity. GPSInfo metadata tags exist; coordinate or identity values are not disclosed in this report.
No participant ID was invented from numbering, camera metadata, timestamps or caption IDs. Participant-level independence remains NOT LOCALLY VERIFIABLE. Exact image overlap is confirmed regardless of that identity limitation.
Published train/validation/test membership is unchanged in all local manifests. Final-test payloads were accessed solely for this approved integrity/label audit; no fitting, hyperparameter selection, calibration, threshold selection or model-choice decision occurred. NHANES held-out payloads were not accessed.

## Unresolved issue summary

| Issue | Distinct affected images |
|---|---:|
| conflicting_caption_grades | 113 |
| duplicate_content | 28 |
| caption_yolo_hypothesis_disagreement | 7 |
| annotation_tooth_count_review | 16 |
| duplicate_caption_target_disagreement | 6 |
| Union needs_review | 161 |

Issue categories overlap; do not sum them as independent exclusions. No image was excluded, relabelled or moved.

## Local outputs and verification

Verified audit directory: `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/audit_verified`

- `integrity_results.json`: source hashes, safety limits, extraction inventory, cached decode/hash evidence and final annotation review.
- `split_manifest.csv`: one row per 1,096 entries; original membership, hashes/dimensions, provisional captions, review reasons, raw annotation codes and unknown participant IDs.
- `label_distribution.csv`: caption-only counts plus counts with no currently detected issue; neither constitutes approved training labels.
- `duplicates_anomalies.csv` and `label_review.csv`: unresolved records and pending reviewer decisions.
- `/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/metadata_identity_review.csv`: local metadata review; values not exposed, candidate text only hashed.
- Original intermediate `audit/` snapshot remains preserved, including the blank-line false-positive flag; `audit_verified/` supersedes it for findings.
- Final focused tests: **35 passed, 0 failed**. Tests cover archive safety/limits, existing-file protection, real synthetic extraction, byte-stream coverage/overflow, decoding, byte-versus-pixel fingerprints, raw-code validation, blank-line handling, metadata identity boundaries and duplicate-label preservation.
- Tests used installed pytest with bundled Python 3.12.14/Pillow 12.3.0; no package installation. An initial Pillow deprecation warning was fixed before final verification.

## Required next decisions — STOP

Owner/supervisor approval is required for label adjudication, verification of the class mapping, missing-grade-0 feasibility, and duplicate/group handling. See `docs/vision_label_review_options.md`. An approved leakage-safe split/eligibility plan must precede training; no final mapping/model choice is made here. Training needs separate approval after those blockers are resolved.

No installation, commit, push, destructive Git operation, source-data change or unrelated refactoring performed. Historical reports/plans and existing tracked/untracked work preserved.
