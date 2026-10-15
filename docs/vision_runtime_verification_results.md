# Vision synthetic Colab runtime verification — completed v1 and v2

Recorded: 2026-10-14. Branch: `vinuthan`. Both workflows were executed personally by the owner in Google Colab. This update verifies saved evidence only; it does not repeat execution, train on dental images, approve labels or activate a manifest.

## Actual selected test results

| Workflow / job | Passed | Failed | Errors | Skipped | Saved evidence |
|---|---:|---:|---:|---:|---|
| v1 model backend | 6 | 0 | 0 | 0 | `vision_runtime_evidence.zip`: `existing_backend.log/.xml` |
| v1 architecture Grad-CAM | 2 | 0 | 0 | 0 | Same ZIP: `architecture_gradcam.log/.xml` |
| **v1 total** | **8** | **0** | **0** | **0** | `vision_colab_runtime_verification.ipynb` source snapshot |
| v2 trainer backend | 7 | 0 | 0 | 0 | `vision_training_runtime_evidence_v2.zip`: `trainer_backend.log/.xml` |
| v2 approval/leakage/metrics | 44 | 0 | 0 | 0 | Same ZIP: `approval_and_metrics.log/.xml` |
| **v2 total** | **51** | **0** | **0** | **0** | `vision_training_colab_verification_v2.ipynb` source snapshot |

Across the two separate workflows, **59 selected test cases passed**. This is not a full repository test run, dental-model performance measurement or independent clinical validation. Local missing-torch skips remain historical facts; they no longer block synthetic CPU verification of these exact source snapshots. The v1 log's 32 deselected cases and v2 second job's seven deselected cases are not skips or additional passes. Subtotal rows must not be added to their component rows again.

JUnit suite start timestamps (UTC): v1 backend `2026-10-14T07:28:44.501110+00:00`, v1 Grad-CAM `2026-10-14T07:28:51.319942+00:00`, v2 backend `2026-10-14T08:24:55.463639+00:00`, v2 remaining checks `2026-10-14T08:25:07.610938+00:00`. These come from saved XML, not an invented execution date.

## Evidence integrity and current source matching

Both original ZIPs were found under `/Users/vinuthanvinuthan/Downloads/`, not the requested docs paths. They were read in place and copied byte-for-byte into docs/ without modifying originals. Both contain text JSON/log/XML evidence (and v2 checksum TXT), no datasets, clinical manifest or model weights.

| Retained evidence | Bytes | ZIP SHA-256 |
|---|---:|---|
| [vision_runtime_evidence.zip](vision_runtime_evidence.zip) | 2,438 | `95c7b8b0cf9aa6e2f93f554cef470ad7e5fd5cda63fe8916a9ebc6743afe15b7` |
| [vision_training_runtime_evidence_v2.zip](vision_training_runtime_evidence_v2.zip) | 4,082 | `7683dfa3f6782718aac3e67411b7cfd71a9abb17adc7a72a3b1426a9cf8660b5` |

ZIP CRC passes. Each saved JSON job count agrees with its pytest log and actual JUnit testcases/suite counters; return codes are zero and no failure/error/skip elements exist. Both runtime-source manifests identify `vinuthan` and explicitly include uncommitted code. Their manifest contents match the original code-only upload bundles, whose SHA-256 values are pinned in the corresponding notebooks. No notebook outputs were fabricated or overwritten with reconstructed executions.

| Current source | Verified in | SHA-256 |
|---|---|---|
| `src/vision/model_pipeline.py` | v1 and v2 | `c11ad18912575f3567d0baf0eefb1bfbb5eb00fbfa075880fe84aef1ccd34b3c` |
| `tests/test_vision_model_pipeline.py` | v1 | `027a707ad24d53e90d02e7c4bec818dce8063a73dc53ed35bd8420a56384c030` |
| `tests/test_vision_colab_runtime.py` | v1 | `28e6690de664307569e26908f2aa9d7db58212d00b030c3551f5c461f027a5a7` |
| `src/vision/train_pipeline.py` | v2 | `e7a979b0875af0e459496bca79ce3c80e594acf2639ea7dc9d8659ec75ffc695` |
| `tests/test_vision_training.py` | v2 | `797f70b29dd968a2b0e6d0b1528867bf115a68467f57b806cf779de024a3dedb` |

Every file's hash/size and bundled bytes match the current working source. v2 additionally records identical before/after source hashes, `source_hashes_unchanged=true`, overall `stage=verified` and `verified=true`; its saved bundle checksum matches `vision_training_colab_bundle_v2.zip`. v1 provides source snapshot hashes but no separate before/after field; that extra claim is made only for v2. No source/test/manifest was changed in this documentation task.

## Recorded shared runtime

| Component | Actual value in both ZIPs |
|---|---|
| Python | 3.13.16 |
| PyTorch | 2.11.0+cpu |
| Torchvision | 0.26.0+cpu |
| NumPy | 2.1.3 |
| Pillow | 11.3.0 |
| pytest | 8.4.2 |
| Execution device | CPU |

v2 records Linux x86_64 and two requested/actual CPU threads. Both record successful import, NumPy bridge, CPU torchvision operator and RGB Pillow compatibility probes. These are measured runtime records, not assumptions about future Colab images or GPU reproducibility.

## What is now verified, and what is not

v1 verifies both five-logit architecture forwards, Grad-CAM target layers/class gradients/alignment, frozen-backbone behaviour and hook/state cleanup on generated RGB. v2 verifies generated-image training/validation for both architectures, freezing/BatchNorm controls, reproducible uninterrupted-versus-resumed synthetic histories/weights, early stopping/best checkpoint selection, save/load/resume and synthetic approval/content/participant leakage guards plus metric checks.

Actual architecture instances use `weights=None`; v1's two negative cache guards request pretrained metadata only and reject before construction/download. Tiny synthetic optimisation is runtime plumbing, not dental-image learning. No pretrained download, dental-image training/inference or final-Test model inference occurred in the documented workflows. Passing fabricated approval fixtures demonstrates rejection/acceptance logic, not authenticity of a real human approval.

Scientific evaluation remains pending: approved data, learned dental checkpoint, comparable ResNet/EfficientNet/majority experiments, class support, discrimination/calibration/uncertainty and real explanation validation. RGB → maximum visible MGI (0–4) → Grad-CAM is unchanged; NHANES remains independent. No clinical diagnosis, fusion, forecasting or validated five-class performance is claimed.

## Dataset approval status — reused reports, no new audit

Sources: [near-review artifacts](vision_near_duplicate_review_v1.md), [grouping proposal](vision_content_grouping_v1.md), [optional caption-policy check](vision_incomplete_policy_check.md), [caption QA](vision_caption_label_qa.md) and [label/duplicate approval plan](vision_label_verification_duplicate_plan.md).

| Existing evidence | Status after runtime verification |
|---|---|
| 1,096 original images | Source files/splits unchanged |
| 274 incomplete-caption policy candidates | Still unapproved; check eligibility is not clinical approval |
| 339 historical/new QA review records | None cleared; overlapping categories must not be added as separate exclusions |
| 14 confirmed exact duplicate pairs, eight cross-split | Content equality known; label conflicts and approved placement/representatives still unresolved |
| 54 near-duplicate candidate pairs, 11 cross-split | All human decisions pending; 40 components are review graphs, not automatic confirmed groups |
| Image-level MGI 0 | Supported examples absent; no missing label becomes zero |
| Participant identity / final grouping | Unknown identity is not proof of independence |
| Frozen verified eligibility/split manifest | Not approved or activated |

These quantities have different units and overlap: images, candidate pairs and review components are not additive. Runtime passes do not reduce the review queue or change original memberships.

## Next SINGLE practical step

**Complete human, label-blind visual review of the existing 54 near-duplicate pairs**, prioritising the 11 cross-split pairs. Reuse the prepared viewer/contact sheets and `review_pairs.csv`; no hashing, extraction or model inference is needed. A reviewer records `visually_same_content`, `distinct` or `uncertain`, plus identity/date/notes, retaining `pending` if no decision is possible. `distinct` does not prove different participants. Do not expose grades or model outcomes to these duplicate decisions or automatically merge a transitive component.

Existing entry page and decision CSV:

`data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/near_duplicate_review_v1/index.html`

`data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/near_duplicate_review_v1/review_pairs.csv`

This recommendation schedules no review and records no decision. It resolves the next concrete content-group blocker; it does not itself authorise a training manifest.

### Approvals still necessary after that step

- Qualified dental/annotation reviewer approves the optional incomplete-caption policy and supported individual/group labels; adjudicates unresolved QA, including the historical 48 clinical/annotation referrals and exact-group annotation conflicts. Those referrals are part of prior review evidence, not 48 additional exclusions.
- Supervisor approves label-blind representative/placement rules, participant identity evidence or an explicit proposal-aligned resolution of its absence, final grouping basis and protection of original Test groups. Content groups alone cannot satisfy the current trainer's verified participant-independence gate.
- Supervisor resolves absent image-level MGI 0 feasibility while preserving all five definitions and avoiding fabricated examples or an undocumented objective change.
- Qualified reviewer/supervisor approves final label provenance and a versioned frozen eligibility/group/split manifest; separately freezes the exact training protocol and authorises actual training. No original file or historical manifest should be overwritten.

Tamil handoff: code-ன் synthetic runtime verification முடிந்தது; dental model இன்னும் train செய்யப்படவில்லை. அடுத்தது 54 near-pairs-ஐ மனிதர் பார்த்து evidence decisions பதிவு செய்வது. Clinical labels, MGI 0 support மற்றும் participant-safe manifest approval தனியாகத் தேவை.

Viva: 59 passes என்றால் dental model accuracy உறுதியா? இல்லை; இரண்டு குறிப்பிட்ட synthetic workflows-ன் code/runtime checks மட்டுமே. Approved dental data-ல் training மற்றும் scientific evaluation இன்னும் நடைபெறவில்லை.


## 2026-10-14 — PP1 exploratory scaffold Colab evidence and packaging preflight

Owner executed the separate new scaffold workflow; recorded evidence is now verified, without rerunning tests. This update supersedes the historical local 58-pass/2-skip blocker for this exact unchanged source snapshot. It does not replace earlier v1 model/Grad-CAM (8) or v2 trainer (51) evidence, and does not represent a full repository run or dental-model performance.

| Evidence | Actual result |
|---|---|
| `pilot_runtime_verification.json` | Synthetic only; 60 tests, 60 passed, 0 failures/errors/skips; dental_training_run=false; test_data_used=false |
| `pilot_synthetic_pytest.log` | 60 passed in 4.65 seconds |
| `pilot_synthetic_checks.xml` | 60 actual testcase elements, suite counters agree; no failure/error/skip elements |
| JUnit suite timestamp | 2026-10-14T17:56:12.082618+00:00; suite time 4.655 seconds |
| `code_manifest.json` | Six SHA-256 records; scope code_only_synthetic_verification; dental_data_included=false |
| Runtime | Python 3.13.15; torch 2.11.0+cu130; torchvision 0.26.0+cu130; NumPy 2.1.3; Pillow 11.3.0; pytest 8.4.2; CUDA available; Tesla T4 |

T4 identifies the available Colab runtime GPU; it is not proof that all selected synthetic checks used GPU optimisation or that dental training occurred. The new tests include generated-image/synthetic adapter and checkpoint provenance cases. No architecture performance claim follows.

Original Downloads evidence was read in place and retained byte-for-byte as [vision_pp1_scaffold_runtime_evidence_v1.zip](vision_pp1_scaffold_runtime_evidence_v1.zip): **3,194 bytes**, SHA-256 `d1c59f3795d2c99db9b67120fa06690bc770f0c0b079b4937cb28840d862d687`. Both ZIP CRC and code-bundle CRC pass. Saved code-archive SHA `bdbd49b0f71e297d87ca17ff7f262964ed5996cf836821cf5f37737d290ce418` matches the current seven-entry code-only bundle. Every saved source hash equals both the current uncommitted file and its bundled bytes:

| Current source/test | SHA-256 |
|---|---|
| `src/vision/model_pipeline.py` | `c11ad18912575f3567d0baf0eefb1bfbb5eb00fbfa075880fe84aef1ccd34b3c` |
| `src/vision/train_pipeline.py` | `e7a979b0875af0e459496bca79ce3c80e594acf2639ea7dc9d8659ec75ffc695` |
| `src/vision/exploratory_bundle.py` | `b694a058f493193a0b4a6d222e765f93a188e0eb633fdb36369b04ac953aca2b` |
| `src/vision/exploratory_pilot.py` | `e5ffc0564a6ec68404e568be73b92674554554a952637212113a8b668a975ccc` |
| `tests/test_exploratory_bundle.py` | `287e72d7ea9477f01df9f9efd09f6f6a3da4ef4ca8ea2466ec880712e7d7d9b6` |
| `tests/test_exploratory_pilot.py` | `1293d8ed44855c9bf3aa397bbd3fa78b213da70dd1bb529188078e81d801cf33` |

The evidence supplies one source-hash map, not separately retained before/after maps; no additional before/after record is invented. The current saved notebook defaults `RUN_PILOT=False`. The owner confirms it remained false and no real dental images were uploaded; the ZIP records synthetic_only/no_dental_training/no_Test_use and contains only text evidence. It does not contain the executed notebook or a separate saved RUN_PILOT variable. Source matching verifies provenance, not an independent audit of all cloud uploads.

The next task has now completed its **cohort dry-run**: 680 Training / 53 Validation, 733 selected hashes MATCH, all 181 holds and NP015 excluded, zero known selected group overlap, no Test label/image access and no real image packaging. **Overall packaging safety is BLOCKED**: three eligible full-resolution Validation CAM originals retain GPSInfo/opaque metadata, and the current builder copies them verbatim. Published dataset CC BY 4.0 reuse needs attribution; privacy rights are separate. See [development packaging preflight](vision_development_packaging_preflight_v1.md) for evidence, mapping, sizes, safe next revision and conditional authorisation commands.

Final research labels/manifest and participant independence remain unapproved. Existing historical records are preserved; no installs, weight downloads, dataset modification, dental training/inference, commit or push. Next single step is a scoped metadata-safe export/attribution/hash revision with synthetic regression checks, then separate real packaging approval. Existing 60-pass evidence remains valid for the unchanged v1 snapshot.

Targeted GPS clarification: all three selected CAM originals contain only GPSVersionID, no latitude/longitude or GPS time/date fields. No location leak or patient identity is asserted. The packaging review blocker concerns nonempty DateTime/opaque MakerNote metadata copied verbatim, with no export sanitisation policy or verification.


## 2026-10-15 — Metadata-safe exploratory export revision v2

This is **local metadata-export regression evidence**, not a new Colab verification. The affected source revision passed **73 selected generated-data cases, 0 failures/errors/skips**, Python 3.12.14, NumPy 2.3.5, Pillow 12.3.0, existing pytest 9.1.1. Initial verification-order bug was caught and fixed; initial/repaired/final XML retained in the ignored v2 evidence directory. No model training/inference was executed. No completed architecture/trainer Colab tests were repeated.

The original 8/51/60 Colab workflows and ZIPs remain preserved as historical snapshot evidence. Four scaffold source/test files now differ; do not apply the old six-file/60-pass certification to new code. Unchanged `model_pipeline.py` and `train_pipeline.py` retain their previously verified hashes. New code-only ZIP SHA: `52ab60b1a0c7dc87da4fd2804f97d4ce709ca411b9928306986df9149c47f98b`; current four-module digest `3c3f79231082282acdcbb6a6c0cd3a45701e7c1e179bec164c425caafaef9719`. Six current file hashes/ZIP contents/CRC and new notebook syntax/off state were checked. New metadata-only notebook has **not** run in Colab.

See [v2 report and exact approval requirements](vision_metadata_safe_export_v2.md). Real data remains unexported/unpackaged, with unsupported source ICC/non-sRGB handling intentionally blocked; no confirmed GPS location leak, private-value logging, label/split change, final approval activation, download, install, commit or push.


## 2026-10-15 — ICC-to-sRGB metadata-safe export v3

Authorised ICC fix verified locally using generated profiles/images: **95 selected cases passed in 0.59 seconds, 0 failures/errors/skips**, Python 3.12.14 / NumPy 2.3.5 / Pillow 12.3.0 / LittleCMS 2.19 / existing pytest 9.1.1. Includes 21 new ICC cases and affected export/CAM/guard regressions; no architecture optimisation, model training/inference or completed Colab workflow repeated. Synthetic nonidentity conversion matches independent LCMS reference and the fixture's Lab consistency assertion; it is not measured clinical colour validity.

New code-only ZIP `vision_pp1_icc_safe_code_v3.zip` SHA `324f9fe84a4783b71ccc1371a1764ffb3665f8670cc6cc97377d005990acf7d6`; seven current source/test hashes, eight entries and CRC checked. Current four-module digest `44455f3e80ad0629f509427e2f5e37af93a6cb7f5cab42b27d3fdc85f2d7b639`. New `vision_pp1_icc_safe_verification_v3.ipynb` code parses and RUN_PILOT remains false; **not executed in Colab**. Historical 8/51/60 Colab results and 73-case local v2 evidence retain their original snapshots and must not be presented as v3 execution. Model/trainer files retain their original hashes.

The three allowed real CAM headers pass the new supported-ICC/orientation validator; no real pixels were decoded/converted/exported and no all-cohort transform guarantee is claimed. See [v3 solution and packaging-only approval](vision_icc_colour_export_v3.md). Source bytes/clinical labels/splits, final approval gates and old evidence remain unchanged; all actual data packaging/upload/training permissions pending. No Test, weights download, install, commit or push.
