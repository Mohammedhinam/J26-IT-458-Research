# Optional live YOLO tooth-box demo (ROI v2)

17 October 2026 · Local integration only.

## What is connected

The Vision page now has two separate actions for the same registered photo:

- **Run ResNet50 + Grad-CAM** keeps the existing PP1 photo path unchanged.
- **Run YOLO tooth boxes + CORAL** calls a new optional FastAPI route. It uses the returned v2 fold-00 detector and crop classifier, then displays the predicted tooth boxes, each crop's MGI estimate, the detector's box confidence, and the maximum predicted grade across detected crops.

The React page does not run every trained model. The optional ROI result is explicitly labelled as one cross-validation fold, not a final all-development refit. Box confidence is not grade confidence. Boxes are predicted tooth ROIs, not clinical gum boundaries. No-detection returns no image grade rather than assuming grade 0.

The route reuses the existing source-registration rules: exact registered JPEG hash first, then the qualified RGB/ICC/orientation checks. It does not allow arbitrary uploads, held records, sealed Test files, or unknown-source photos. No photo is saved by the API route. The displayed overlay is reduced to a maximum 1,200-pixel side and strips source metadata.

## Mac setup and run

No Colab is needed for this integration or inference. The verified ZIP is `data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip` with SHA-256 `e78240b01a1b039e091be0d2e31881ce96c1b1e47388e99f8f49b2541094771b`. Its 21 checkpoint/result manifest entries were verified. The selected fold-00 detector/classifier pair is loaded on MPS when available and CPU otherwise. Use Colab only if another training run is required.

To test the complete page with the existing generated-only fixture, run this from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
.venv/bin/python -B -m src.tabular.api --port 8772 \
  --vision-checkpoint models/vision_live_demo_v1/v3_best.pt \
  --vision-registration data/pp1_live_photo_verification_v1_20261017T013402631604Z/generated_registration.json \
  --vision-registration-sha256 15d2e8584225660154dd5ce7291829b3993c33f7a7509dd411aea3482c7629e8 \
  --roi-v2-return-zip data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip
```

Open `http://127.0.0.1:8772/`, choose **Vision**, and upload only `data/pp1_live_photo_verification_v1_20261017T013402631604Z/generated_only.jpg`. The image is a generated colour fixture, not teeth. The ROI model correctly returned no detections on it; this validates request handling and abstention only, not dental inference.

For a real live box demonstration, the owner must first identify one permitted, source-confirmed **non-study** RGB JPEG and register its exact bytes under the already documented local-photo procedure in [the registered-photo guide](vision_registered_photo_live_demo_v1.md). The generated-only registration cannot accept a dental photo. Do not register Mendeley study, held, or Test images. Until a real eligible JPEG is registered, the UI integration is ready but there is no real dental photo available for a live upload demo.

## Verification

- `sh src/tabular/ui/build.sh` rebuilt the React bundle successfully.
- 76 focused tests passed across the new runtime, existing v2 inference, FastAPI demo, and registered-photo guard tests.
- The real fold-00 checkpoint pair loaded on Mac MPS. A generated-only image passed through the real API route and returned HTTP 200, zero ROIs, no grade, and a bounded preview. This was not scored as a model result.
- A Playwright page check confirmed the Vision tab shows the generated-only registration state, fold-00/MPS status, and the separate ROI action. The file upload could not be exercised through Playwright MCP because its allowed filesystem roots point at another project; the actual FastAPI route was exercised locally with TestClient and the generated fixture.
- No Colab training, labels, splits, original artifacts, PP1 checkpoint, or protected Test files were changed. No commit, push, or external upload was made.

## Three blocks to explain

1. `build_runtime` verifies the return ZIP receipt and selected checkpoint hashes before loading the fold. It loads fold 00 only and keeps its temporary checkpoint files for the server lifetime.
2. `ROIV2PhotoRuntime.predict` checks the registered byte hash before decoding. The same qualified image constraints are applied before the YOLO detector runs; the classifier only grades detected tooth crops.
3. `/api/vision/roi-photo` is separate from `/api/vision/photo`, so the original Grad-CAM route stays intact. React lets the presenter choose which one model path to run on the registered photo.

Likely viva question: **Why show an ROI box and a crop grade separately?** The YOLO score measures its confidence that a tooth ROI box is present. The crop classifier estimates the MGI grade inside that crop. They are different outputs and neither is a clinical diagnosis.
