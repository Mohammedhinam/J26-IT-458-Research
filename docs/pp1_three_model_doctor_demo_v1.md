# PP1 Three-Model Doctor Demo — implementation and verification

18 October 2026 (Asia/Kolkata). Owner approved implementation in this chat. Existing dirty changes were preserved; no training, Test-label access, external image upload, commit, push or reset.

## Run locally

A verified server was left running at **http://127.0.0.1:8771**. Open that URL and choose **Vision · exploratory evidence**. To start it again when that port is free:

```bash
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
.venv/bin/python -B -m src.tabular.api \
  --port 8771 \
  --local-photo-uploads \
  --vision-checkpoint models/vision_live_demo_v1/v3_best.pt \
  --roi-v1-return-zip data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return.zip \
  --roi-v1-device mps \
  --roi-v2-return-zip data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip \
  --roi-v2-device mps
```

1. Select one permitted non-study JPG/PNG, up to 8 MiB; confirm permission.
2. **Doctor Review Mode:** record an independent MGI 0–4 assessment, Uncertain or Cannot assess before running AI. This is a presenter-declared review workflow; reviewer credentials are not authenticated.
3. **Developer Demo Mode:** no doctor assessment is required; the UI and export explicitly mark it not clinically reviewed.
4. Choose **Run All Three Models**. Runs are sequential to bound resources; each model has its own queued/running/success/failure/unavailable status. The same original file bytes reach each endpoint and SHA-256 values are checked against the browser's source digest.
5. Review three separate result cards, then optionally record Agree/Disagree/Uncertain, reviewer-proposed grade, reason and notes for each model. Do not enter names, IDs or other patient identifiers in free text.
6. Explicitly download **Export Feedback** as JSON or CSV. It includes only the assessment, model/prediction provenance and feedback allowlist. It excludes image bytes, filename, source-photo hash and patient-ID fields. CSV cells are quoted and formula-like text is neutralised. Free text is not automatically de-identified: the reviewer must omit identifiers.
7. Reset, replace the file, change modes, leave the Vision tab or reload to discard case state. No automatic retraining or persistent feedback store exists.

## What changed

- Added `src/tabular/ui/DoctorVision.jsx`: dedicated Vision comparison workspace, two modes, shared upload, consent, independent per-model status/results, source identity verification, stale-response invalidation, clinician/developer feedback and explicit local export.
- `src/tabular/ui/App.jsx`: mounts this workspace; existing questionnaire functions remain intact. Saved examples and aggregate metrics remain under a clearly separate expandable research section.
- `src/tabular/ui/style.css` and rebuilt `app.js`: desktop three-column cards, mobile stacking, readable tables and statuses. Existing cached esbuild/React dependencies were reused, without installs/downloads.
- `src/tabular/api.py`: additive input SHA field, local blob-preview CSP permission, independent optional model loading. A missing/bad checkpoint remains unavailable; no cached or different model substitutes for it. Questionnaire and other successfully loaded models remain available.
- `src/vision/roi_ordinal_v2_live.py`: local uploads now use shared validated sRGB pixels, including EXIF/ICC/alpha handling, saved losslessly in a temporary PNG just like v1. Registered-photo mode, trained detector settings, 15% crop padding, resize/normalisation, weights, targets and aggregation are unchanged.
- v1/v2 preview renderers: numbered detected ROI labels match per-crop rows; coordinates, confidence and grades are unchanged. These are predictions, not source TXT annotations, tooth identities or clinical boundaries.
- Tests: updated focused API tests; added generated decoding/cleanup/CAM geometry checks and reproducible browser/CAM verification scripts.

The initial dirty-tree snapshots and hashes are retained in `data/vision/doctor_demo_20261018_v1/before/` and adjacent preservation records. Files already modified before this task were edited in place without Git reset or replacement from HEAD.

## Genuine outputs and limitations

| Card | Actual available information |
| --- | --- |
| ResNet50 B1 v3 | Four-output MGI 1–4 grade and uncalibrated scores; class-specific original/heatmap/overlay; explanation status; pinned checkpoint SHA |
| YOLO ROI v1, fold 00 | Tooth/perigingival detections; detector confidence; per-crop grade; maximum crop image grade; checkpoint hashes. Crop probabilities are not supplied. |
| YOLO ROI v2 CORAL, fold 00 | Same box information; CORAL per-crop grade/probabilities; maximum crop image grade; checkpoint hashes. No image-level probability distribution. |

ROI folds are not all-development refits. Image-level MGI 0 evaluation support is absent. Grades 1/2 remain weak. No inference-time integration change improves the reported OOF accuracy or establishes clinical validity. The three grades are independent and never fused with each other or with the questionnaire.

The questionnaire remains a separate live XGBoost development reference predicting **self-reported previous gum treatment**, with exact TreeSHAP in log-odds and restricted smoking/interdental-cleaning sensitivity analysis.

## Grad-CAM investigation

The code targets ResNet `layer4[-1]` and the predicted class logit. It spatially averages the class gradients, weights channels, retains positive evidence and normalises per photo. Alignment upsamples to the 224-square input, removes letterbox padding and maps to the original display geometry. The original is preserved. No heatmap manipulation, anatomical masking or selective cropping was added.

Existing Validation examples 00733/00734/00766 and the owner's previously permitted photo show broad attention including gum/mucosa and peripheral lip/retractor regions. This supports an honest attention warning, not a claim of validated gingival localisation. Shortcut learning, coarse features, lack of gingival supervision and photo-domain/colour differences remain hypotheses; no one cause was established.

A bounded real-checkpoint check used only that permitted non-study photo. Native feature shape was 1×2048×7×7. An independent PyTorch CAM-algebra reference differed by at most **1.7881393432617188e-7** after the same alignment. Predicted/explained grade matched (3), probabilities matched, weights were unchanged, parameter gradients were unset and hooks removed. This validates calculation/parity checks on one photo, not clinical localisation.

The UI explicitly warns that red heatmap intensity is relative within one photo, may highlight lips/teeth, cannot be compared across photos as severity/confidence, and does not prove clinical correctness. Flat/no-positive/padding-only statuses are surfaced.

## Verification results

| Verification | Result |
| --- | --- |
| Focused Python/API/generated checks | **102 passed, 0 failed**, 3 dependency deprecation warnings |
| Browser acceptance checks, final run | **32 passed, 0 failed** |
| Bounded pinned ResNet CAM parity/integrity checks | **6 passed** |
| Missing-ResNet startup with real ROI ZIPs | **4 passed**: ResNet unavailable; v1/v2 ready; 12-input questionnaire schema available |
| Preservation | **12/12** protected artifact hashes matched |
| React production bundle | Built successfully using cached dependencies |
| Diff whitespace check | Passed |

The final browser run covers doctor pre-reveal gating, developer warnings, three real responses, source-byte identity, no-save flags, loaded original/Grad-CAM/ROI previews, desktop/mobile layout, JSON/CSV privacy and formula escaping, independent failure, no-detection/flat-CAM states, mismatched input identity, late-response reset, file-change invalidation, no browser storage, no external browser requests and no JavaScript page errors. It also exercises actual questionnaire prediction, SHAP rendering, what-if and exact reset. Fault/no-detection/stale-response cases use explicitly synthetic intercepted responses; they are not model-performance evidence.

On the permitted photo, real responses were ResNet MGI **3**, ROI v1 maximum **3** with **12** ROIs, and CORAL maximum **2** with **12** ROIs. All source hashes matched; all reported `photo_saved=false`. These are repeatable one-photo outputs, not a new accuracy estimate or a doctor's judgement. ResNet hotspot still lies near the upper lip and was preserved honestly.

The first browser attempt had a test-script JSON/CSV-format selection mistake; the second reselected the identical file and therefore did not trigger a browser change event. Both attempts are preserved. The final script explicitly selects JSON and selects a different case file; all 32 checks pass. An earlier screenshot exposed a CSP-blocked local blob preview; the restricted `img-src blob:` fix is covered by actual image-loaded verification.

## Evidence and rerunning checks

All local evidence is under `data/vision/doctor_demo_20261018_v1/`:

- `verification_summary.json`, `focused_tests.xml`, `browser_verification.json`
- `cam_real_verification.json`, `missing_checkpoint_verification.json`
- `preservation_before.json`, `preservation_after.json`
- `desktop_real_outputs.png`, `mobile_real_outputs.png`
- `feedback_smoke.json/.csv` (developer software checks only)
- `doctor_mode_synthetic_feedback.json` (synthetic UI fixture, not actual clinician feedback)

Focused tests:

```bash
.venv/bin/python -B -m pytest -q \
  tests/test_component2_api.py tests/test_doctor_demo_inference.py \
  tests/test_roi_ordinal_v2_live.py tests/test_roi_tooth_v1_live.py \
  tests/test_photo_explanation.py tests/test_local_photo_upload_demo.py \
  tests/test_vision_model_pipeline.py
```

Browser script: `scripts/doctor_demo_browser_smoke.cjs`. Set `PP1_DEMO_URL`, `PP1_PERMITTED_PHOTO` and `NODE_PATH` to the existing local Playwright package directory; it opens its own headless Chrome and closes it after verification. No installation is necessary on this Mac. It performs three bounded real inferences and explicitly synthetic fault tests. Existing evidence paths should be copied/versioned before an intentional rerun.

CAM script: `scripts/verify_doctor_demo_cam.py`; run with `python -B -m scripts.verify_doctor_demo_cam --photo <permitted-photo> --report <new-report.json>`. It refuses to replace an existing report.

## Remaining work

A qualified clinician has not yet performed the proposed independent 10–15-photo review. No new classification accuracy, healthy-grade support, disease segmentation or clinical correctness is claimed. Whole-image unsupported-class limitations, weak Grade 1/2 performance and unknown participant independence persist. Review mode is not a credential/authentication system. Feedback has no server persistence and unsaved feedback is lost on navigation/reset. Cancelling the browser request invalidates its result but cannot stop an already executing server tensor operation; execution remains bounded by the selected image/model rather than a training job.

Viva explanation: “We send the same image bytes to three existing trained workflows, verify input identity, show only their available outputs, and collect the clinician's independent assessment before revealing them. Grad-CAM explains the selected model class; YOLO boxes locate learned tooth ROIs. Neither proves a clinical diagnosis.”
