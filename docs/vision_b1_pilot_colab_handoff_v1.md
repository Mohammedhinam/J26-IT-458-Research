# Colab handoff — B1 MGI1–4 exploratory pilot v1

2026-10-15. **Prepare/run code-only synthetic verification first; no dental upload or training yet.**

## இப்போது நீங்கள் செய்ய வேண்டியது

1. [Notebook](vision_b1_pilot_colab_v1.ipynb)-ஐ Google Colab-ல் திறக்கவும்.
2. Upload cell-ல் **[vision_b1_pilot_code_v1.zip](vision_b1_pilot_code_v1.zip)** மட்டும் தேர்ந்தெடுக்கவும்.
3. Generated verification cell-ஐ இயக்கவும். Installed torch/torchvision compatibility முதலில் check ஆகும். Missing/incompatible என்றால் STOP; auto-install இல்லை.
4. PASS condition: **71 passed,0 failed,0 errors,0 skipped**, all3 new backend tests passed,20 source hashes before/after unchanged. **Skips = PASS அல்ல.**
5. Download ஆகும் `vision_b1_pilot_runtime_evidence_v1.zip`-ஐ திருப்பி வழங்கவும். `RUN_PILOT=False` அப்படியே இருக்கட்டும். Runtime evidence-ல் actual versions/counts/XML/logs/hashes இருக்கும்.

Code ZIP SHA256: `eba79c8f5539edf5014546986466157688f261397c05d9a63437ef768c40de30`.
Code ZIP:20 Python source/test files + verification_manifest.json. No dental image/annotation/weights/data archive included.

Local preparation evidence: **68 passed,0 failed/errors,3 skipped** from the actual isolated ZIP, source hashes unchanged. This is **not Colab PASS**. Notebook JSON/cells compiled; formal nbformat validator unavailable, no install performed.

## மூன்று pending backend tests

- `test_resnet50_four_output_optimization_and_frozen_batchnorm_weights_none`
- `test_four_class_gradcam_geometry_and_hook_cleanup_weights_none`
- `test_four_class_synthetic_checkpoint_loading_and_reproducibility`

All use generated inputs/`weights=None`; no pretrained download or real dental model training.

## Local package — verified, keep local for now

ZIP:
`/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/pp1_b1_dev_v1_20261015T085436527238Z.zip`

Size:732575501bytes; SHA256:
`a8a4f7f339c589f81335d7afb663f4cf62d30e217f65bc480683d0a770afed70`

Manifest SHA256:
`8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f`

680 Training +53 Validation,733 model arrays +3 full-resolution CAM arrays.181 holds/NP015/protected/Test material excluded. Originals unchanged. This package is not code ZIP and is **not required for the current synthetic verification**.

## Future separately authorised real pilot

After actual71/71 Colab evidence is verified, obtain separate explicit owner decisions for cloud upload, official weights access and exploratory training. Existing local permission grants none of these.

The notebook contains disabled later cells:
- `CLOUD_DATA_AUTHORIZATION=None`; future record must bind scope `upload_exploratory_b1_development_v1`, actual archive SHA, manifest SHA, owner/date.
- `TRAINING_AUTHORIZATION=None`; future scope `run_cloud_exploratory_b1_mgi1to4_v1` binds actual manifest/protocol/code/weights hashes and new run ID, plus all existing provisional acknowledgements and explicit cloud/training flags.
- `RUN_PILOT=False`; enable only in a new cell after separate permission and passed runtime checks. Default controls intentionally keep it off.
- `ALLOW_WEIGHT_DOWNLOAD=False`; no download implementation included. Cached authentic `ResNet50_Weights.IMAGENET1K_V2` required. Official provenance: https://download.pytorch.org/models/resnet50-11ad3fa6.pth ; record full SHA and verify the published filename hash prefix. Local cache status is missing; none downloaded.
- Fresh isolated Colab data directory, no Drive mount. Exact safe archive extraction, strict NPY integrity, four-output model and bounded5epoch training; no Test loader.
- Evidence/result download cells save actual runtime, training/Validation metrics, checkpoints and three disclosed Grad-CAM previews only after a future authorised run.

Projected resources from actual package:699MiB compressed upload, approximately1.7GB extracted payload plus synthetic test/checkpoint scratch; recommend≥8GB free Colab disk and ordinary≥12GB RAM. Actual local JPEG export peak206.171875MiB does **not** measure GPU training memory. Batch16 frozen ResNet50 is proposed for a T4-class GPU; actual device memory/runtime remains to be measured. CPU verification is supported; the real bounded pilot explicitly requires CUDA.

Original research still MGI0–4; this separate pilot predicts only1–4. MGI1 support12 Training/1 Validation; MGI0/healthy prediction unsupported. Labels provisional, participant independence unverified, no clinical/final claims. Display previews can clip colours; model inputs remain unclipped extended floats.

**Provisional labels; non-clinical; non-final; participant independence unverified.**
