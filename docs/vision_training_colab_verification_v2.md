# NEW Vision trainer CPU runtime verification — v2

Date: 2026-10-14. Branch: `vinuthan`. **Owner's Colab v2 completed: 51 passed, 0 failed, 0 errors, 0 skipped.**

Saved JSON/logs/JUnit XML and recorded source hashes have been verified against current code and the pinned v2 bundle. Seven backend cases and 44 other focused checks passed; before/after source hashes are unchanged. Evidence: `vision_training_runtime_evidence_v2.zip`; [consolidated verification record](vision_runtime_verification_results.md). Instructions and preparation-time observations below are retained as history/reproduction guidance, not a request for another run.

This version verifies the new training scaffold. The previous eight Colab passes verified model/Grad-CAM code only. Existing source, tests, earlier notebooks/bundles, dataset, MGI 0–4 definitions and pending reviewer decisions are unchanged. No new smoke tests are needed: the current focused suite already contains the required coverage.

## Files and simple Colab steps

Required files, both in this repository's `docs/` directory:

- `vision_training_colab_verification_v2.ipynb`
- `vision_training_colab_bundle_v2.zip`

1. Open Google Colab. **File → Upload notebook**: select the new `vision_training_colab_verification_v2.ipynb`.
2. Use a fresh CPU runtime: **Runtime → Change runtime type → Hardware accelerator: None**.
3. Run **Cell 1**. It detects installed packages, prints actual Python/torch/torchvision/NumPy/Pillow/pytest versions, checks imports/NumPy bridge/CPU torchvision op/RGB Pillow and records compatibility errors. It does not install anything. If it fails, skip to Cell 4 and retain evidence; do not guess a version pair or reinstall automatically.
4. Run **Cell 2**. Upload **only `vision_training_colab_bundle_v2.zip`** when prompted. The older v1 bundle is rejected. It verifies the ZIP and every source hash/size before writing the code to a new isolated `/content/rp_vision_trainer_v2_*/code/` directory. No checkout is overwritten.
5. Run **Cell 3**. It executes the seven backend cases first, then the remaining 44 approval/leakage/metric checks if the first job succeeds. Any failure, error, skip, timeout or unexpected count prevents verification and stops further jobs. Read the actual logs and counts; no automatic rerun or weakened assertion occurs.
6. Run **Cell 4**, including after any earlier failure. Download **`vision_training_runtime_evidence_v2.zip`**. Keep it before the Colab VM expires. It contains measured versions, source hashes, summary, logs/XML and any error tracebacks; no model checkpoints or dataset files.

Do not upload Dataset.rar, images, captions CSV, YOLO TXT, clinical manifests, .venv or weights. No Drive mount, Git clone, pip command or pretrained download is included. Namespace imports work from the isolated code root; no extra `__init__.py` files are required.

## Frozen code-only snapshot

Bundle: **17,098 bytes**. SHA-256:

`7b4d1c89e8f0465739b1ab4255465ccd6b8f644997f3c6a7f72a8a520b584cd0`

| Bundled source | Bytes | SHA-256 |
|---|---:|---|
| `src/vision/model_pipeline.py` | 12,298 | `c11ad18912575f3567d0baf0eefb1bfbb5eb00fbfa075880fe84aef1ccd34b3c` |
| `src/vision/train_pipeline.py` | 24,342 | `e7a979b0875af0e459496bca79ce3c80e594acf2639ea7dc9d8659ec75ffc695` |
| `tests/test_vision_training.py` | 15,303 | `797f70b29dd968a2b0e6d0b1528867bf115a68467f57b806cf779de024a3dedb` |

The fourth entry is `runtime_source_manifest.json`, protected by the pinned whole-ZIP checksum. It records version, source branch, HEAD, explicit uncommitted-file provenance, expected test counts and every source hash/size. HEAD is context, not evidence that these files were committed. Notebook pins the exact ZIP and source metadata independently, then checks source hashes before and after tests.

If source changes later, prepare a new versioned snapshot; do not disable or update checksum assertions to accept an unexplained mismatch. All source bytes here match the current working files. Remote cloning would omit the uncommitted trainer, so it is not used.

## Tests and acceptance

| Existing backend test function | Cases | What it checks |
|---|---:|---|
| `test_frozen_backbone_bn_and_validation_no_grad` | 1 | Frozen parameters and BN buffers unchanged; head trains; validation changes neither parameters nor gradients |
| `test_selected_batchnorm_updates_only_approved_module` | 1 | Explicit fine-tuning parameter/mode flags and BN behaviour; invalid prefixes rejected |
| `test_checkpoint_resume_matches_uninterrupted_and_reproducible` | 1 | Identical uninterrupted/resumed histories and last weights; changed config/context rejected |
| `test_early_stopping_and_best_checkpoint_reload` | 1 | Patience stops the synthetic run and reloads best validation weights |
| `test_actual_architecture_generated_train_validation_step` | 2 | ResNet-50 and EfficientNet-B0 generated-image optimisation/validation; frozen backbone unchanged |
| `test_generated_smoke_supports_checkpoint_reload_and_resume` | 1 | Tiny generated-RGB smoke with save/load/resume; no final Test use |
| **Backend job total** | **7** | **Previously skipped cases, no new cases invented** |
| Remaining focused checks | **44** | Unapproved manifests/protocols, original-Test exclusion, participant/content leakage, duplicate records, caption provenance, safe paths/RGB, Training-only weights, MGI mapping/support, metrics and stopping logic |

**Acceptance criterion met in saved Colab evidence:** 7 backend + 44 focused = **51 passed, 0 failed, 0 errors, 0 skipped**, successful process return codes and unchanged verified source hashes. Exact pytest collection was checked during preparation: these selections cover all 51 cases without overlap. The seven backend checks and 44 other cases ran in separate CPU subprocesses, each with a 600-second timeout.

CPU thread limits, hidden CUDA devices, disabled pytest plugin autoload, isolated PYTHONPATH and no bytecode/cache writes keep execution scoped. Existing tests call `pretrained=False`, `allow_download=False` for actual architectures (`weights=None`); tiny models are generated locally. The only production-entry test blocks model construction through a synthetic rejection fixture. No production manifest is activated.

Synthetic optimisation changes temporary random model parameters to test the loop. It is not dental-image training, clinical ground truth, a five-class validity result or a model comparison. Checkpoint tests use pytest temporary directories; weights are deliberately excluded from the evidence export.

## Evidence and failure interpretation

`verification_summary.json` begins with `verified=false`. Per job it records exact pass/fail/error/skip counts from pytest XML, expected counts, commands and return codes. On timeout/missing or unreadable XML, unavailable counts remain `null`, not invented zeroes; captured output and tracebacks are retained. A failed first job leaves the second unexecuted, not implicitly passed. Summary also records source hashes before/after and the final verification state. Dependency/upload failures can still be exported through Cell 4.

The evidence ZIP uses a new export location each time. Older v1 evidence and source artifacts are preserved. Missing/incompatible libraries are real runtime blockers; no installation is attempted. Keep the exact error evidence for a scoped diagnosis rather than silently editing the verified source or tests.

## What was verified locally for this preparation task

- Four code cells parse successfully; all execution counts are null and outputs empty.
- ZIP CRC, exact four-entry whitelist, source byte equality, SHA-256 values and pinned notebook metadata pass.
- Collection only confirms seven backend and 44 other focused cases; no trainer test was executed again here.
- Synthetic XML/subprocess fixtures verify notebook status handling for successful counts, failure, skip, count mismatch, changed source and timeout. These test the workflow's reporting logic only; they are **not Colab or trainer test results**.
- Existing 44 local passes / seven missing-torch skips remain historical scaffold evidence. No new Colab execution, dependency installation, training run or pretrained download occurred.

Zero-skip trainer verification in compatible Colab is complete. Remaining blockers: qualified label/duplicate/participant eligibility approval, missing-MGI-0 feasibility and a separately frozen experiment protocol. Runtime success cannot resolve those research approvals.

Tamil teaching: SHA-256 என்பது upload செய்த code சரியான version தானா என்று பார்க்கும் fingerprint. `weights=None` architecture plumbing-ஐ pretrained download இல்லாமல் சோதிக்கிறது. `verified=true` என்பது actual tests அனைத்தும் pass ஆன பிறகு மட்டும்; அது dental accuracy அல்லது reviewer approval இல்லை.

Viva: பழைய எட்டு passes ஏன் trainer-க்கு போதாது? அவை model forward/Grad-CAM checks; புதிய optimiser, BatchNorm, checkpoint மற்றும் resume paths தனியாக ஓடி pass ஆக வேண்டும்.
