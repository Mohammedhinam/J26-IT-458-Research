# Vision training scaffold — synthetic CPU runtime verified

Date: 2026-10-14. Branch: `vinuthan`. No dental-image training, real-image inference, downloads, installs, commits or pushes.

Current verification: owner completed Colab v2, **7 backend + 44 approval/leakage/metric cases = 51 passed, 0 failed, 0 errors, 0 skipped**. Source hashes before/after are identical and match the current trainer/model/tests and v2 upload bundle. See [consolidated evidence record](vision_runtime_verification_results.md) and `vision_training_runtime_evidence_v2.zip`. This supersedes the historical missing-backend status below, not the scientific/approval blockers.

Authority: supplied AGENTS.md §§3, 6.1, 7, 8, 13; signed Component 2 proposal §§3.3–3.5, pp.20–22. RGB → image-level maximum visible MGI 0–4 → Grad-CAM remains independent of the questionnaire branch. Existing model/Grad-CAM code, source data, original splits, review statuses and historical evidence are unchanged.

## Verified prior runtime evidence

The original supplied v1 evidence is `/Users/vinuthanvinuthan/Downloads/vision_runtime_evidence.zip`. It was read in place; an unchanged byte-for-byte copy is now retained as `docs/vision_runtime_evidence.zip`. Its JSON, logs and XML record **8 passed, 0 failed, 0 errors, 0 skipped** (six original backend cases plus two architecture checks). Source hashes match the existing model pipeline and both source test files. The v2 evidence is separately retained in docs/; neither original was modified.

Recorded Colab runtime: Python 3.13.16, torch 2.11.0+cpu, torchvision 0.26.0+cpu, NumPy 2.1.3, Pillow 11.3.0, pytest 8.4.2. This verifies the previous model/Grad-CAM snapshot, **not the newly added trainer**.

## Interfaces and behaviour

`src/vision/train_pipeline.py` adds:

- `TrainingConfig`: explicit architecture, batch size, epochs, learning rate and patience; seed, improvement delta, backbone prefixes, BatchNorm policy, class weighting, decay and CPU/CUDA device. Unsupported choices fail rather than silently changing the protocol.
- `approved_partitions`: external approval-verification callback is mandatory. It checks qualified reviewer/date/evidence, label/split approval, completed duplicate review, participant independence, per-record caption/adjudication provenance, five-grade labels and source identifiers. Test entries need only sealed path/group/participant metadata; Test grades are not inspected or returned. Original Test images cannot move into development. Content or participant groups cannot cross splits. Repeated exact-content records require an externally selected single-record eligibility list; this code never chooses representatives or rewrites a manifest.
- `RGBDataset`: only Training/Validation records, reusing `preprocess_rgb` unchanged. Rejects Test records and path/symlink escapes; opens explicit RGB images without implicit grayscale conversion, cropping or EXIF rotation. No TXT input, augmentation, resplitting or label derivation is introduced.
- `configure_trainable_layers` and `training_mode`: initial head-only training keeps all backbone modules in eval mode, including their BatchNorm buffers and dropout. Only the head trains. Optional fine-tuning requires explicit existing backbone-module prefixes; frozen BatchNorm remains the default. `train_selected` updates only BatchNorm modules with trainable parameters. Untracked-statistics BatchNorm is rejected. No automatic stage transition occurs.
- `run_epoch`: fresh training gradients and optimiser steps only in Training; validation uses eval mode with gradients disabled. Five finite logits are required. Loss is sample-averaged cross-entropy; optional balanced weights are computed from Training labels only. Weighted training loss is the mean of weighted per-example terms, not PyTorch's weight-normalised mean; validation loss is unweighted. Missing training grades get zero weight, never fabricated support. No oversampling is implemented.
- `validation_metrics`: fixed 5×5 confusion matrix, support, accuracy, per-grade recall/F1, five-schema macro-F1, supported-grade macro-F1, ordinal MAE, quadratic weighted kappa, per-grade/macro AUROC and sum-over-classes multiclass Brier. Undefined recall/AUROC/kappa are `null`. Five-schema macro-F1 includes zero contribution for an absent grade; the supported-grade diagnostic is separately named. Macro AUROC is withheld if any class AUROC is undefined. These metrics do not establish five-class validity.
- `_fit`: Adam optimisation, validation five-schema macro-F1 monitoring, earliest best on ties, configurable patience/minimum improvement, atomic `best.pt` and `last.pt`, JSON history, and best-model restoration. Checkpoints contain model/optimiser, completed epoch, stopping state, history, loader/Python/NumPy/torch/CUDA RNG states, MGI schema, configuration and provenance identity.
- `fit_approved`: future integration API, requiring separate external authentication of the exact approved protocol. Protocol metadata must bind the configuration SHA-256 and acknowledge missing-grade support. Production models use the existing documented pretrained factory with downloads blocked; weights must already be cached. Production checkpoints are restricted to a new ignored repository `models/<run>/` location.
- `synthetic_smoke`: generated RGB images and a tiny five-output neural network only, one interrupted epoch followed by checkpoint resume. The CLI exposes this smoke mode only; it has no dataset-training command.

Approval callbacks are supplied by the future owner integration and must authenticate real evidence. A boolean field or a callback that always returns true is **not** authentication; the always-true callbacks in unit tests refer exclusively to fabricated synthetic metadata. This scaffold cannot grant reviewer, label, split or protocol approval.

### Determinism and practical resume scope

Seeds cover Python, NumPy, torch CPU/CUDA; deterministic torch algorithms are required, cuDNN benchmarking is disabled, and training shuffle uses a saved generator. Loaders use zero workers, no random augmentation and no distributed/AMP/scheduler logic. Resume accepts only the same run's `last.pt`, alongside its `best.pt`, and validates configuration/manifest/source identity. Existing run directories are rejected without explicit resume. Checkpoints load with `weights_only=True` and never restore a pickled model object.

Resume is epoch-boundary only; interrupted partial epochs are not recoverable. Exact replay assumes the same software/hardware/thread environment. Production provenance includes torch/NumPy/device/thread settings and code hashes; arbitrary cross-platform reproducibility is not claimed. Changing epoch budget/configuration or approved membership requires a separate run, not a disguised continuation. Only scaffold-owned checkpoint/history files may be replaced during resume.

PyTorch references: [saving/restoring model and optimiser state](https://docs.pytorch.org/tutorials/beginner/saving_loading_models), [deterministic algorithm behaviour](https://docs.pytorch.org/docs/main/generated/torch.use_deterministic_algorithms.html), [BatchNorm running statistics](https://docs.pytorch.org/docs/stable/generated/torch.nn.BatchNorm2d.html).

## PROPOSED configuration — not an activated experiment protocol

| Setting | Proposal requirement / candidate implementation | Approval status |
|---|---|---|
| Models/outputs | ResNet-50 and EfficientNet-B0; five MGI 0–4 logits, unchanged definitions | Signed proposal; no dental validity established |
| Initial stage | Cached documented pretrained backbone, head-only optimisation, frozen BatchNorm | Proposal supports frozen feature extraction; exact BN treatment to freeze in protocol |
| Learning rates | 1e-5, 1e-4, 1e-3 | Explicit proposal values; no search run |
| Monitoring | Validation macro-F1, fixed five-schema convention; absent-class support disclosed | Proposal macro-F1 requirement; metric convention to approve |
| Illustrative resource cap | Batch 16, maximum 30 epochs, patience 5, min_delta 0 | PROPOSED only; memory/compute and owner approval required |
| Optimiser/regularisation | Adam; weighting none versus training-only balanced; decay 0 initially | Implementation choices requiring approval; no winner selected |
| Seeds | Start seed 42, up to three prespecified seeds for final configuration | Proposal supports up to three; exact seed list pending |
| Fine-tuning | Explicit selected module prefixes, learning rate and BN mode | Pending; no layers released on real images |
| Preprocessing | Existing RGB 224×224 letterbox/ImageNet normalisation; no augmentation yet | Existing implementation; orientation/augmentation protocol pending |

The illustrative settings above are not defaults for a dental run. Required config values and external protocol checks prevent silent protocol activation. Future comparison must use identical approved labels/splits, comparable tuning effort and augmentation across architectures, plus the proposal's majority-class baseline. Calibration, uncertainty intervals, paired comparisons, timing/memory, explanation checks and final Test evaluation remain separate future tasks.

Current missing image-level MGI 0 support makes validated five-class performance unavailable. Retaining five outputs does not solve this. Balanced weighting cannot create missing examples. The 274 caption-policy candidates and 54 near-duplicate human decisions remain unapproved/pending; unknown participant identity is a real independence blocker, not filled with fabricated IDs. Any departure from participant-level independence requires explicit supervisor resolution; this API currently fails closed.

## Historical local scaffold verification

Focused local suite: **44 passed, 0 failed, 0 errors, 7 skipped**. Syntax passes for both new Python files. Local runtime: bundled Python 3.12.14 / NumPy 2.3.5 / Pillow 12.3.0 with existing pytest 9.1.1. No dependency was installed.

Passed: config validation; externally authenticated approval requirements; missing/proposed evidence rejection; original-Test exclusion; content/participant split isolation; same-split duplicate rejection; caption provenance and TXT-only rejection; safe RGB loading/path guards; Training-only weights and missing-grade handling; known metric examples/ties/undefined support; early-stopping decisions; protocol rejection before model construction.

Skipped in the historical local run because torch was unavailable: frozen-backbone/validation-gradient check; selected BatchNorm behaviour; uninterrupted-versus-resumed reproducibility; best-checkpoint/early-stop reload; two actual architecture generated-image optimisation cases; generated smoke/checkpoint-resume case. All seven subsequently passed in the owner's Colab v2 run. The older eight v1 passes still do not count as trainer passes. No synthetic smoke optimisation was executed locally during implementation or this documentation update.

In a compatible approved Colab code root, upload the unchanged `model_pipeline.py`, new `train_pipeline.py` and `tests/test_vision_training.py` into their matching paths, then run (no datasets or package installation needed):

```bash
PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  python -B -m pytest -q -rs -p no:cacheprovider tests/test_vision_training.py
```

All 51 cases have now passed with zero failures/skips/errors in Colab v2; rerunning is unnecessary for this unchanged snapshot. The old v1 runtime bundle does not include the trainer. The command below is a retained optional generated-only CLI interface, not an instruction to repeat verification; outputs stay confined to ignored `models/synthetic-*`:

```bash
PYTHONPATH=. python -B -m src.vision.train_pipeline --smoke
```

No source datasets are needed for either command. Human approvals, model-weight provenance/cache and a frozen experiment protocol are still required before any actual dataset training.

Teaching: `approved_partitions` protects entry to training; `training_mode` freezes both parameters and BatchNorm behaviour; validation macro-F1 alone drives `_fit` early stopping and checkpoint choice, never Test evidence.

Viva: Why is `requires_grad=False` alone insufficient for freezing a backbone? BatchNorm running buffers can still change in train mode; keeping the frozen backbone in eval mode prevents this drift.
