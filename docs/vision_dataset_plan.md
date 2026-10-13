# Vision dataset audit and extraction plan

Date: 2026-10-13. Branch: `vinuthan`. Status: **archive/caption precheck completed; extraction and training pending**.

## Authority and scope

The supplied signed Component 2 proposal, `RP-IT23311022 (2).pdf`, pages 17–18 (image labels), 20–21 (baseline/method), and 22 (validation), and supplied AGENTS.md sections 3–6.1 and 13 govern this plan. No separate vision implementation or architecture notes were found in the relevant docs; `src/vision/` previously contained only `.gitkeep`. Existing Planner notes identify the planned caption audit, ResNet-50 baseline and EfficientNet-B0 comparison.

Explicit requirements: 1,096 published images, split 732 training / 182 validation / 182 test; image-level maximum MGI 0–4 from captions; ambiguity review; duplicate and participant-overlap checks; caption/YOLO mapping verification before locking targets; identical labels and splits for ResNet-50, EfficientNet-B0 and majority baseline. RGB must be preserved. Training-only augmentation and documented pretrained sources apply to later training, not today's audit. MGI describes visible inflammation, not periodontitis diagnosis. Vision and NHANES remain independent.

Local choices proposed here: storage locations, manifest columns, conservative caption consistency checking and staged extraction procedure. They are audit implementation choices, not new training hyperparameters or an approved label repair policy.

## Archive sources and proposed location

Primary selected for read-only precheck:

`/Users/vinuthanvinuthan/Downloads/A DENTAL INTRAORAL IMAGE DATASET OF GINGIVITIS FOR IMAGE CAPTIONING 4/Dataset.rar`

Possible backup:

`/Users/vinuthanvinuthan/Downloads/A DENTAL INTRAORAL IMAGE DATASET OF GINGIVITIS FOR IMAGE CAPTIONING 2/Dataset.rar`

Both have 6,552,111,937 bytes. Equal size does **not** prove equal content; source SHA-256 comparison is pending. The unsuffixed download folder and folder `3` were empty when inspected. Neither source has been modified.

Proposed final raw directory:

`/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gingivitis/raw/`

Retain the archive's `Dataset/Training`, `Dataset/Validation`, `Dataset/Test` structure below that location. `git check-ignore` confirmed a proposed raw image path is ignored by the existing `/data/` rule. No data directory or extraction artifacts were created by this task.

## Actual archive/caption precheck

The installed `/usr/bin/bsdtar` listed the primary archive and streamed the three captions CSVs into memory. No image payload was read, decoded, resized or extracted.

| Split | Expected images | Archive image entries | Result | Caption rows | Needs review | Conflicting maxima |
|---|---:|---:|---|---:|---:|---:|
| Training | 732 | 732 | MATCH | 2196 | 0 | 0 |
| Validation | 182 | 182 | MATCH | 546 | 47 | 34 |
| Test | 182 | 182 | MATCH | 546 | 66 | 47 |
| Total | 1096 | 1096 | MATCH | 3288 | 113 | 81 |

There are no observed missing caption/image references, duplicate image filenames, duplicate archive member paths, case-insensitive path collisions, invalid numeric grades or missing caption variants in this precheck. These are checks of names and captions; unique names do not establish unique image content or distinct participants.

**113 images have inconsistent explicit grade sets across their three captions**, including 81 with inconsistent maxima. Example: validation `01105.jpg` variants 1/2 mention grades 1,2,3,4; variant 3 mentions 1,3,4 and omits the lower jaw. Its maximum stays 4, but inconsistent descriptions still require review. Test `01222.jpg` likewise has a shorter third caption. Do not silently use the first caption, majority vote, discard conflicting records or union conflicting captions to settle a target.

No provisional image-level MGI 0 labels were found. This is a five-class feasibility blocker, not permission to invent zero labels or change the proposal. An image may contain non-inflamed teeth while its maximum grade remains positive. Inspect conflict records and representative caption/image/YOLO examples before deciding whether image-level grade 0 genuinely exists. If it remains unsupported, report this to the owner/supervisor and approve any consequent scope/label change explicitly.

Full provisional distributions and all 113 anomaly filenames are in `docs/vision_dataset_audit.md`. Mixed explicit-grade image counts are 690 / 171 / 174; these count images with multiple numeric grades in at least one variant and include review records. Non-inflamed wording is not counted as a numeric zero in this statistic.

## Caption-derived labels

Caption members are `Dataset/Training/Train_captions.csv`, `Dataset/Validation/Validation_captions.csv`, and `Dataset/Test/Test_captions.csv`. Required fields: `FileName`, `#`, `BS1`; validation also contains `Vùng`. Match filenames within the published split. `#` is a caption-variant ID, not a class or participant ID.

1. Extract explicit numeric grades from phrases such as `gingivitis 2` or `Level 2 gingivitis`. Ignore tooth positions and tooth counts before `level of gingivitis`.
2. Validate every extracted numeric grade is an integer in 0–4. Require variant IDs 1,2,3 exactly once and matching explicit grade sets for a provisional label. Maximum grade is the image target only for consistent variants.
3. Preserve missing, invalid and conflicting records as `needs_review`; assign no default zero. Non-inflamed-only captions require reviewed examples and a documented approved wording rule. Positive numeric maxima remain positive even if other teeth are described as non-inflamed.
4. Verify published YOLO mapping with actual images and `.txt` annotations: 0/1 are ROI; 2–6 reportedly map to MGI 0–4. These are not locally verified classification labels. Record caption-versus-verified-YOLO disagreements before freezing labels.

This deliberately conservative precheck does not exclude any image from the source or silently repair captions. Review must be independent of model performance. Auditing published image-test metadata/labels does not authorize using test predictions for selection; the NHANES final held-out payload is never accessed.

## Safe extraction and full content audit — proposed, not executed

1. Before extraction, confirm source archive identity, complete integrity/readability, advertised unpacked byte total and available disk space. Compressed size is not the unpacked requirement. Inspect verbose member metadata for symbolic/hard links, non-regular entries, unsafe paths, duplicate paths and case-only collisions. Stop if safety or capacity cannot be established.
2. Create a new ignored staging directory `data/vision/gingivitis/staging-<archive-sha256>/` only if absent. Extract verified regular dataset members with the installed tool into staging; never overwrite/merge an existing raw directory. Keep both original archives untouched. No install is authorized; if tooling cannot safely handle the archive, report a blocker.
3. Cross-check every extracted image/caption/annotation name. Stream SHA-256 per image once; record exact content duplicates within and across splits. With an available image decoder, verify decode success, dimensions and colour mode. No image decoder dependency has been verified for this task; report missing capability rather than installing it.
4. Inspect perceptual/near-duplicate or augmented-image risks separately: byte hashes cannot detect re-encoding/crops. Propose a bounded candidate-screen/manual-review method once installed decoder capabilities are known; do not invent a similarity cutoff now. Seek author metadata or documented group identifiers for repeated participants; filename numbering is not proof of participant independence.
5. Review ambiguous labels and representative caption/YOLO/image mappings. Record every decision, evidence and reviewer; never silently change the primary source. If cross-split duplicates/participants are confirmed, stop and propose a frozen grouped split for owner approval. If participant IDs are unavailable, retain the explicit unresolved independence limitation and obtain a decision before training.
6. Produce the outputs below; freeze accepted labels/splits only after review. Promote staging to `raw/` only when raw destination is absent and extraction verified. Do not delete an existing staging directory on failure; report its state for review.

No resizing, augmentation, upload, torch installation or training is part of this task. Later 224×224 RGB model views must preserve raw originals and use one accepted manifest. Validation/test processing will be fixed; test evaluation waits until model configuration is locked.

## Exact outputs

| Output | Location | Status / contents |
|---|---|---|
| Extraction/audit plan | `docs/vision_dataset_plan.md` | Created now; requirements, findings, safety gates and unresolved decisions |
| Dataset summary report | `docs/vision_dataset_audit.md` | Created now; measured archive/caption counts, provisional distributions and anomaly table; content checks explicitly pending |
| Audit implementation | `src/vision/audit_gingivitis.py` | Created now; read-only archive/CSV precheck; exclusive report creation prevents overwrite |
| Focused synthetic tests | `tests/test_audit_gingivitis.py` | Created now; grades, conflicts, missing references, duplicate/unsafe names and repeatability |
| Split/label manifest | `data/vision/gingivitis/audit/split_manifest.csv` | Proposed after extraction/review; one row per image: original split/path, source archive hash, image hash, dimensions, decode status, variant grade sets, provisional/reviewed maximum, label status/reason, verified participant/group ID if available; unknown IDs stay unknown |
| Label distribution table | `data/vision/gingivitis/audit/label_distribution.csv` | Proposed; per-split grades 0–4 and needs_review, with a separate reviewed/frozen status |
| Duplicate/anomaly records | `data/vision/gingivitis/audit/duplicates_anomalies.csv` | Proposed; missing/orphan references, caption conflicts, corrupt files, exact/near duplicates, within/across-split groups, identity gaps, severity and review decision |
| Label review provenance | `data/vision/gingivitis/audit/label_review.csv` | Proposed; image, variant disagreement, caption/YOLO/image evidence, reviewer, decision and date |

Datasets, per-image manifests and raw captions remain in ignored `data/`. Aggregate public-dataset audit evidence belongs in docs. No existing historical experiment or split manifest is modified.

## Blockers and approval gates

- Resolve the 113 caption inconsistencies, including 81 maximum-grade disagreements.
- Resolve missing provisional image-level MGI 0 support; do not start a purported five-class experiment without an agreed interpretation.
- Complete exact/near-duplicate, decode and participant-overlap checks; published split cleanliness is not yet established.
- Verify YOLO/caption/image mapping, safe extraction metadata, archive identity and unpacked capacity.
- Owner approval needed for extraction/full content audit next, any label repair/grouped split or scope change, and separately for training. No final labels/splits are frozen today.

## Important blocks to understand

- `caption_grades`: reads grade phrases rather than tooth numbers; returns explicit grade sets or a review reason.
- `audit_inventory`: joins filename references inside each published split and checks all three variants; creates provisional maxima without dropping unresolved images.
- `read_archive`: streams only the directory listing and captions into memory; leaves archive/image originals untouched.

Viva: Why not take the highest number in the caption? Tooth positions and tooth counts are numbers too. We extract only explicit MGI phrases, validate 0–4, and review conflicting variants before fixing the image label.
