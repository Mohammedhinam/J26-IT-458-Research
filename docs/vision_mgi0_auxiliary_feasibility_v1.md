# MGI 0 auxiliary-learning feasibility — v1

2026-10-14; branch `vinuthan`. **PROPOSED feasibility only. No training, clinical approval or manifest activation.**

Real source MGI-0 tooth-region annotations exist. They could supply supplementary representation-learning supervision, but do not supply whole-image maximum-MGI-0 examples. Fastest conditional PP1 route: approved development-only image pilot, retaining five definitions/logits and explicit unsupported-class reporting. This does not complete five-class validation.

## Authority and focused method

Signed Component 2 proposal §§3.2–3.5 (PDF pp.17–22) specifies RGB → maximum visible image MGI 0–4 → Grad-CAM; captions primary; conflicts reviewed; content/participant independence. AGENTS.md §§3, 6.1, 7, 13 and existing integrity, caption QA, label-verification, reconciliation v2 and trainer reports were reused. **Auxiliary tooth learning is not explicitly specified** and needs a documented supplementary-method approval; it would not replace the primary task.

Counts come from cached integrity/QA evidence. Detailed geometry covers only **116 Training/Validation zero-containing files: 7 cached box records + 109 selected TXT reads**. No full audit/hash/decode repeat. Test figures below are cached integrity inventory, never evidence for choosing a method; no fresh Test TXT/RGB/crop/prediction access.

The [original paper, Table 2/§3.3](https://doi.org/10.1016/j.dib.2024.110960) documents per-tooth annotations and code 2 = MGI 0. PMC HTML was CAPTCHA-blocked; the primary article PDF was accessible through its PMC storage mirror. [Mendeley v1](https://data.mendeley.com/datasets/3253gj88rr/1) is the original source. Published claims do not override local discrepancies.

## Actual counts — tooth regions, not whole-image targets

| Original split | Raw code-2/MGI-0 boxes | Distinct source files | Source files currently QA-flagged |
|---|---:|---:|---:|
| Training | **244** | **101** | 7 |
| Validation | **30** | **15** | 4 |
| Test: cached inventory | **35** | **17** | 13 |
| Total | **309** | **133** | 24 |

These are real annotations on real RGB files, **not 309 clinically approved independent samples or 133 verified participants**. The 133 filenames represent **131 cached byte/pixel contents and 131 proposed reconciled groups**. Training `00271`/Test `00943` and Training `00275`/Test `00947` are aliases with different zero-box counts (2 vs 1; 3 vs 1). No justified deduplicated tooth count exists without region correspondence/adjudication.

Published code-2 counts 247/53/53 versus local 244/30/35 are **MISMATCH** for all three splits. No source was repaired. Supported image-maximum-MGI-0 examples remain **0**. A healthy tooth beside a grade-3 tooth gives image maximum 3. Training `00029` has a source-supported zero region and a positive maximum; it is not a whole-image zero example. The clinically approved training-crop count is **not established**.

## Geometry and annotation reliability

Existing code convention: `(class, centre-x, centre-y, width, height)`. TXT has no explicit FDI IDs; none were inferred from line order/rank.

| Development zero-box check | Training | Validation |
|---|---:|---:|
| Finite normalised geometry, fully inside image | 244/244 | 30/30 |
| Centre inside exactly one jaw ROI | 244 | 30 |
| Entire box inside exactly one jaw ROI | 220 | 24 |
| Zero-containing files with any grade-histogram disagreement | 3 | 1 |
| Files with zero-count disagreement in a complete caption | 2 | 1 |

**30 boxes extend past a jaw ROI rectangle** despite valid image bounds. This is a context-review flag, not proven wrong grading; do not clip automatically. Native dimensions are approximately 297–1,012 × 388–979 px in Training and 435–997 × 442–754 px in Validation; size alone does not establish gingival coverage.

Training `00025` has one zero box versus zero supported zero positions in all captions; `00097` has two versus zero. Validation `00789` has one versus two. The distinct development zero-source review queue is **11 files**: Training `00025,00052,00060,00085,00097,00271,00275`; Validation `00789,00811,00818,01144`. Flags overlap; unflagged does not mean approved.

Two prespecified Training-only RGB previews (`00029`, `00025`) show local gingival/tooth regions, not whole photographs. No clinical appearance grade was assigned. Tight cropping can omit relevant marginal/papillary context or include adjacent differently graded tissue; qualified review must approve region validity/context margins. The paper's prose calls columns 4/5 height/width, whereas existing code uses YOLO width/height. Current/swapped illustrative previews expose that ambiguity without choosing a clinical interpretation. Confirm exporter/example provenance before a crop protocol is frozen.

## Can auxiliary learning help?

**Plausible, unmeasured.** A shared RGB encoder with a separate five-grade tooth-region head, or crop pretraining followed by the unchanged whole-image task, could learn useful regional features. Include approved examples from all grades: zero-only supervised training provides no graded contrast. Task mismatch can also cause negative transfer. [Ruder, auxiliary tasks/task relationships](https://arxiv.org/html/1706.05098v1) supports this general rationale, not a guaranteed improvement here.

TXT would supply crop coordinates/targets, not numerical inputs to deployed image inference. That exceeds its current verification-only use and requires explicit approval. The existing primary trainer requires caption-derived **image-maximum** provenance; tooth targets must never be passed through that contract as image labels.

The primary head still lacks genuine whole-image zero positives and independent zero evaluation cases. For cross-entropy on a positive-grade image, the class-0 logit gradient is `p0`; a separate auxiliary zero loss does not create a primary zero-labelled photograph. Auxiliary learning cannot establish whole-image zero sensitivity, discrimination or calibration. Do not replace maximum with minimum, treat crops as full images, or silently substitute a tooth-detector aggregation pipeline.

## Three practical options

| Option | Contribution | Limitation / approval | PP1 recommendation |
|---|---|---|---|
| **A: Existing tooth-region auxiliary learning** | Real regional MGI-0 signal; possible encoder transfer | Qualified region labels/context, parent grouping, auxiliary protocol and bounded development comparison required; no whole-image-zero validation | Optional later experiment; extra implementation/review work |
| **B: Genuine external whole-image MGI-0 evidence** | Direct primary zero positives and independent evaluation support | No suitable specific external source verified here. Requires access/licence, comparable qualified MGI labels, identity/group independence and approved data extension; normals only from another camera/site risk source/class confounding | Most direct route to missing primary support; investigate availability in parallel |
| **C: Exploratory development image pilot on supported grades** | Reuses existing model/trainer/Grad-CAM | Approved manifest and protocol still required; retain five logits/definitions, mark zero unsupported, report scarce grade 1. No validated five-class or clinical claim | **Fastest conditional prototype route**, ResNet-50 first |

Recommendation is based on task-unit validity and implementation effort, not Test grades/outcomes. Route C is a staged feasibility experiment, not a silent four-class remapping or changed research topic. Route B remains necessary to substantiate primary zero performance unless genuinely supported original whole-image zero cases are later independently established.

## Independence and next step

Freeze parent participant/content partitions **before** crops. All crops/augmentations/aliases inherit the complete parent's group/split; never randomly split crops. Under PROPOSED Test > Validation > Training reservation, Training `00271/00275` belong to Test content groups: **5 raw Training zero boxes** must not enter training under that rule. The remaining 239 are not an approved crop cohort. This uses grouping metadata, not Test grades to choose placement.

Optimiser updates, auxiliary pretraining and learned transforms use approved Training only. Validation may evaluate an approved protocol, never pretrain the shared encoder before its primary validation measurement. Test stays sealed for both tasks. Preserve all 54 human decisions/eight cross-split conflicts; NP015 remains unresolved even though absent from the zero development subset. Content IDs/filenames cannot substitute for authenticated participant IDs.

**Next implementation, not executed:** prepare a non-activating strict-clean image eligibility draft using current QA/group evidence and trainer contract, with pending reviewer/date/label/identity fields, holds/exclusions, sealed Test metadata and unsupported-zero acknowledgement. Obtain the required qualified and supervisor decisions; only then separately authorise a bounded development ResNet-50 pilot with existing Grad-CAM. Reuse existing guards; never fake authentication.

If A receives separate approval later, implement a parent-linked fail-closed crop-manifest adapter and synthetic geometry/group-isolation tests first. Crop margin, loss weight, head design and protocol remain unapproved; no training crop dataset created today.

## Saved evidence and verification

Ignored local directory: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/mgi0_auxiliary_feasibility_v1_20261014/`.

Contains `feasibility_evidence.json`, `verification.json`, two Training context previews and `context_preview_provenance.json`. Checks: 309/133 source totals; 131 contents; 274 development zero boxes; **114 unchanged source-input hashes**, **87 pre-existing Git files preserved**, original preview-image size/mtime and log prefixes intact. Clinical approval fields false; FDI identity absent. Diary/AI log appended only; no original data/code/reports modified, training, Test inference, install, download, commit or push.

Viva: **Can healthy tooth crops validate a healthy whole-image classifier?** No: they supervise a different unit and provide no independently labelled all-normal full-image evaluation cases.
