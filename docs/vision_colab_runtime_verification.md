# Minimal Colab Vision runtime verification — v1

Date: 2026-10-14. Source branch: `vinuthan`. **Owner's Colab v1 completed: 8 passed, 0 failed, 0 errors, 0 skipped.**

Saved evidence has been checked: `vision_runtime_evidence.zip`, JSON/logs/JUnit XML, runtime versions and source hashes match the uploaded bundle/current source. See [consolidated verification record](vision_runtime_verification_results.md). The preparation-time/local results below are historical, not the current cloud status. Retain these instructions for reproduction; do not repeat verification for the unchanged snapshot.

Use the unchanged `src/vision/model_pipeline.py` and existing focused tests. The files are currently uncommitted, so cloning the remote branch would omit them. This workflow uploads a frozen code-only snapshot, with SHA-256 verification, without datasets, weights, labels, manifests or credentials.

## Exact steps

1. Save `docs/vision_colab_runtime_verification.ipynb` and `docs/vision_colab_runtime_bundle_v1.zip` from this workspace to your Mac.
2. Open [Google Colab](https://colab.research.google.com/). Choose **File → Upload notebook**, select the `.ipynb`. Choose **Runtime → Change runtime type → Hardware accelerator: None**. Use a fresh standard CPU runtime; do not mount Drive or upload datasets. These menu steps follow the [official Colab FAQ](https://research.google.com/colaboratory/faq.html).
3. Run **Cell 1**. It prints actual Python/torch/torchvision/NumPy/Pillow/pytest versions and checks imports, NumPy↔torch round trip, CPU torchvision compiled-op compatibility and RGB Pillow. It installs nothing. If missing/incompatible, stop; the exact traceback is saved as `/content/vision_compatibility_failure.txt`. Do not guess a torch/torchvision version pair or reinstall automatically.
4. Run **Cell 2**, selecting only `vision_colab_runtime_bundle_v1.zip` when prompted. It checks the bundle and all three file hashes, validates source branch metadata, and writes to a new isolated `/content/rp_component2_runtime_*` directory. It does not overwrite an existing checkout.
5. Run **Cell 3**. It runs the six formerly skipped cases first, then two actual-architecture Grad-CAM synthetic checks in separate CPU subprocesses. Read the exact printed counts and tracebacks. Any skip/failure/error stops further tests and prevents a VERIFIED claim. No optimiser, training loop, dental image, final-test inference or pretrained-weight loading/download is involved.
6. Run **Cell 4** to download `vision_runtime_evidence.zip`, containing actual runtime versions, source hashes, JSON summary, pytest logs and XML. If Cell 1 failed before upload, Cell 4 downloads its compatibility traceback instead. Retain the results before the Colab VM expires. On failure, report this evidence; only a confirmed scoped implementation bug should lead to a source fix/regression test.

The notebook has four code cells. No pip command, Git command, Drive mount or dataset access is included.

## Source snapshot and reproduction

Bundle SHA-256:

`f590ff163ed2e8e20b3f07dc372052f7fad2b22ba2c5812f4fdd38cf94d78e9e`

Exact bundle contents:

- `src/vision/model_pipeline.py` — unchanged implementation.
- `tests/test_vision_model_pipeline.py` — unchanged original focused tests.
- `tests/test_vision_colab_runtime.py` — two narrowly scoped actual-architecture synthetic smoke tests.
- `runtime_source_manifest.json` — every file's hash/size, source `vinuthan`, current source HEAD and explicit uncommitted-code provenance. HEAD is context, not a claim that the uploaded files were committed.

If any source file changes later, prepare a new versioned bundle/notebook with updated hashes; do not disable checksum verification. Record actual runtime versions instead of assuming a fixed Colab image or installing a different stack unnecessarily.

## Exact tests and expected scope

| Existing backend cases | Number | Verifies |
|---|---:|---|
| `test_actual_backend_model_shapes_and_targets_no_download` | 2 architecture parameters | ResNet-50 / EfficientNet-B0 five-logit forward, CAM target registration, untrained-head flags |
| `test_uncached_pretrained_weights_never_download_implicitly` | 2 architecture parameters | Empty cached-weight path fails before construction/download |
| `test_actual_autograd_class_consistency_frozen_backbone_and_hook_cleanup` | 1 | Toy-model class-specific gradients, frozen backbone, spatial peaks, hook/state cleanup, unchanged parameters |
| `test_actual_autograd_no_positive_signal_and_inference_guard` | 1 | Explicit zero signal and inference-mode guard |
| **Previously skipped total** | **6** | **Must pass with zero skips/errors** |
| Additional `test_each_architecture_gradcam_alignment_and_frozen_state` | 2 architecture parameters | Actual target identity, head-only requires_grad flags, synthetic RGB forward, nonzero finite feature gradients, hook cleanup, unchanged weights/BN buffers, original-coordinate RGB output alignment |

The executable selections used by Cell 3, from its isolated code root, are:

```bash
python -B -m pytest -q -rs --color=no -p no:cacheprovider \
  tests/test_vision_model_pipeline.py \
  -k 'actual_backend or uncached_pretrained or actual_autograd' \
  --junitxml existing_backend.xml

python -B -m pytest -q -rs --color=no -p no:cacheprovider \
  tests/test_vision_colab_runtime.py \
  --junitxml architecture_gradcam.xml
```

The notebook also sets isolated PYTHONPATH, disables plugin autoload, fixes CPU thread limits and hides GPU devices for reproducible CPU checks. The additional smoke tests set seed 42. Runtime versions/hashes and exact output logs are captured; no learned performance or clinical metrics are generated.

All constructed models use `pretrained=False`, i.e. Torchvision `weights=None`; the two negative cache-guard tests request pretrained metadata only, then deliberately verify rejection before any model or pretrained weights are created/loaded. No source pipeline rewrite is needed for this distinction.

Acceptance criterion **6 existing backend cases + 2 architecture checks passed, 0 failed/errors/skipped** has been met in the owner's saved Colab v1 evidence. Synthetic model outputs/heatmaps do not establish clinical relevance, missing-grade-0 support or five-class dataset validity.

## Historical results obtained during preparation

- Prior unchanged implementation evidence: 32 local tests passed, 6 skipped (torch unavailable). Those 32 numerical tests were not rerun for this task.
- This task's targeted local dry-run: **0 passed, 0 failed, 8 skipped, 32 deselected**. All eight selected cases require unavailable torch/torchvision; none is claimed verified.
- New smoke-test source and notebook code-cell syntax validated; code-only ZIP membership and file checksums verified. Notebook has no execution outputs. No Colab session was accessed or run.
- No implementation failures were observed; no source pipeline or existing test assertions were modified. Missing runtime dependencies are a blocker, not a reason to fake backend success.

## Remaining blockers and boundaries

Compatible Colab execution and evidence retention are complete for this source snapshot. Qualified label/duplicate/participant grouping approval, final frozen eligibility/split manifest, MGI-0 feasibility and future experiment-protocol approval remain separate requirements. This notebook does not approve any label, clear review statuses, activate a manifest or train a dental model.

Teaching: checksums ensure the exact uncommitted code is tested; `weights=None` tests the architecture without downloading/training; a zero-skip test result verifies plumbing only, not dental accuracy.

Viva: Does a successful synthetic Colab test mean our MGI model is trained? No. It verifies runtime, shapes, gradients and alignment; approved data and actual learning/evaluation are separate future work.
