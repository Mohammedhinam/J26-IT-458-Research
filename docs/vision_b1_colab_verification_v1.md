# B1 code-only Colab CPU verification handoff v1

2026-10-15 · vinuthan · PREPARED, **Colab not executed**. Original B1 code/tests, Option A limits/exporters and research-training gates preserved. No dental/Test payload, datasets/weights, model training, upload/download, install, commit or push during preparation.

## Files and exact manual steps

1. Open `docs/vision_b1_colab_verification_v1.ipynb` in Google Colab (Upload notebook).
2. Select Runtime → Change runtime type → **CPU**, then Run all.
3. When prompted upload **only** `docs/vision_b1_runtime_code_v1.zip`. No Drive mount, images, labels or data ZIP.
4. Existing Python/NumPy/Pillow-CMS/pytest/torch/torchvision must be available. Real CPU NMS probes the compiled torch/torchvision pairing. Missing/incompatible dependencies cause a clear STOP; no installer or automatic fallback. Use a compatible runtime separately rather than editing tests or enabling diagnostic mode.
5. Download `vision_b1_runtime_evidence_v1.zip` and return it for factual verification. Evidence downloads on test/dependency failure too, then the notebook raises an explicit error. A dependency STOP has no JUnit file because tests never began; no results are invented.

Acceptance requires **77 passed, 0 failed, 0 errors, 0 skipped**, both named backend tests passed, all source hashes unchanged and project/test imports confined to the extracted tree. A 75-pass/2-skip run is **INCOMPLETE**, never accepted. Even a one-test skip fails the strict notebook. The optional runner flag `--local-diagnostic` is for Mac evidence only, never used by the notebook and never permitted to return PASS.

## Archive integrity and dependency completeness

- ZIP: `docs/vision_b1_runtime_code_v1.zip`, **60,800 bytes**.
- Whole ZIP SHA256: `d848e87d49c32f259c20ec1127bc6aab0e22e4a825df34dc4bf86522109324ba`.
- Manifest SHA256: `5eea8d5689bfd705689f99fbc41cb64a80074f4b52c26b475ff0a485f8af9c19`.
- **11 hashed Python files + manifest = 12 entries**. Notebook pins ZIP SHA, manifest SHA and every Python payload SHA. Dependency closure follows actual local imports and both source_code_hashes declarations; missing required files fail before ZIP creation. Removing `exploratory_pilot.py` in a temporary fixture produced the expected missing-dependency error and no archive.
- Legacy/pilot/trainer files are included for imports/source-integrity checks, not execution of packaging/training. Only `tests/test_colour_b1_prototype.py` is selected. No conftest, requirements/install script, dataset, permission record, clinical labels or weights included.
- Builder: `src/vision/build_b1_verification_bundle.py`; runner: `src/vision/verify_b1_runtime.py`. Versioned output overwrite is rejected. Notebook archive validation rejects extra/duplicate entries, path escapes, non-regular entries, bad CRC/hashes or excessive size. Extraction creates a new local folder; no existing output overwritten.

| Included file | SHA256 |
|---|---|
| `src/vision/colour_b1_prototype.py` | `d3108ea3bf7f310f1b46960174d4936299ece19d762f4ca1ee9d900572b90856` |
| `src/vision/colour_policy.py` | `2bba567545143687f49b6e3ae63fdd72d1eacc10977d5ec373f00a4b5451a97b` |
| `src/vision/colour_qa.py` | `4ad2b81c715b01e624b527d1971cc303740ddf559461f2d953c831956c1e82e3` |
| `src/vision/exploratory_bundle.py` | `dda776ca1558ed4da795df7cee47c0fe19d382cf32c37ca89d22f4141974b615` |
| `src/vision/exploratory_bundle_v4.py` | `c914cc05ad2be4ff08873a5d2270b5836e0f84219a539435beeca09b57ad76cd` |
| `src/vision/exploratory_pilot.py` | `c5bf6cba173390f914a44c4537b91d4f2a8e150aa0f5e4842c2ca94bb1a4d535` |
| `src/vision/gamut_mapping_feasibility.py` | `41cd1d49fcebbb08d45fa1951755d4141a4611630ed9b081f26e5a9b273f368a` |
| `src/vision/model_pipeline.py` | `c11ad18912575f3567d0baf0eefb1bfbb5eb00fbfa075880fe84aef1ccd34b3c` |
| `src/vision/train_pipeline.py` | `e7a979b0875af0e459496bca79ce3c80e594acf2639ea7dc9d8659ec75ffc695` |
| `src/vision/verify_b1_runtime.py` | `bc5f2a2fe17f4e4321d80680b821d93c1b576c607440e29c6331bfe6de3e52f5` |
| `tests/test_colour_b1_prototype.py` | `db9fb9307b6453f0252ff9d1aef6c2541ca1ec829930e8f803818af122f63e85` |

## Actual preparation verification

Fresh extraction outside the repository ran with Python `-I -B`, explicit extracted root/config boundaries, plugin autoload and cache disabled. Actual result: **75 passed, 0 failed, 0 errors, 2 skipped**, 77 unique collected node IDs, 0.24s. All **11/11 hashes MATCH before/after**, and all project/test module origins stayed under extraction. This verifies portability of the available path, **not the two missing PyTorch backends**. Runner correctly returned process exit3 / INCOMPLETE / acceptance_passed=false despite pytest itself returning0 for skips.

Local versions: Python3.12.14, NumPy2.3.5, Pillow12.3.0, LCMS2.19, pytest9.1.1; torch/torchvision absent. Only the existing pure pytest package directory was appended after the bundled runtime site-packages for Mac diagnostic execution. No repository source directory was appended; current extracted source hashes match the ZIP. This dependency-only accommodation is absent from the Colab notebook.

Additional **12/12 acceptance-logic assertions passed**, separately from the77 suite: exact full-pass fixture, any skips/failures/errors, missing/duplicate/skipped backend, wrong total, nonzero exit, changed source, import escape and bad dependencies. These are generated decision-logic fixtures, not claimed architecture passes. Notebook cells parsed; actual upload/extract/run/failure-download cell flow was exercised with a fake local Colab UI: missing pytest/torch caused strict FAIL, safe failure evidence ZIP produced, final cell raised NOT PASSED. No cloud upload/download occurred. This mock result is not Colab verification.

Durable preparation evidence: `docs/vision_b1_handoff_verification_v1.json` includes source hashes before/after, isolated import origins, environment, counts and guard checks. Transient full pytest log/JUnit and collected IDs are under the fresh extraction's `synthetic_evidence/`; location is recorded in the preparation JSON module-origin paths. `/tmp/rp_b1_handoff_isolation_v1.json` and `/tmp/rp_b1_handoff_guards_v1.json` are transient auxiliary records, not cloud evidence.

## Two required Colab backend cases

- `tests/test_colour_b1_prototype.py::test_resnet50_unclipped_forward_weights_none` — generated extended-float input, real ResNet-50 five-logit finite CPU forward; weights=None and unchanged input.
- `tests/test_colour_b1_prototype.py::test_resnet50_gradcam_frozen_backbone_hooks_and_alignment_weights_none` — real frozen-backbone ResNet-50 class-specific autograd, hooks cleaned, aligned overlay/attention, preview disclosure, weights/gradients unchanged; no optimizer/training.

The downloaded Colab evidence contains pytest.log, JUnit XML (if tests started), environment versions/CPU compatibility probe, collected test IDs, isolated module origins, source-before/source-after hashes, verification verdict, code manifest, original ZIP/manifest binding and an evidence-file hash map. Hashes establish integrity, not human/clinical approval. A timeout/interrupted runner is FAIL and cannot be printed as PASS.

## Teaching and boundaries

`dependency_files()` follows actual code dependencies before creating the ZIP, avoiding the previous missing-file failure. `acceptance()` requires every condition together; skips cannot become passes. `source_hashes()` before/after checks the notebook tested unchanged pinned source. Viva: **Does 77 passed mean the dental model is accurate?** இல்லை; generated software compatibility மட்டுமே. Real labels/class support/participant independence and scientific evaluation remain unresolved.

Current B1 generated prototype is not production-integrated, rejects full-resolution dental inputs, and grants no real packaging permission. Option A remains failed/unchanged. Missing MGI0, provisional labels, unknown participant independence and all cohort/NP015/duplicate/Test protections persist.

**ONE next manual action:** open the new notebook in Colab, choose CPU and Run all; upload the matching code-only ZIP when prompted. Return the downloaded evidence without claiming success in advance.
