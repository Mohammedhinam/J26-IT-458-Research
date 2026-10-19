# Local Vision photo upload demo v1

Date: 2026-10-18  
Purpose: allow the PP1 presenter to run the saved Vision models on a newly selected photo from the local React demo.

## Current model-comparison update (2026-10-18)

The owner wants to compare what the saved Vision models return for the same uploaded photo. The page now keeps three runnable outputs visible together: the existing ResNet50 + Grad-CAM checkpoint, ROI v1 weighted-CE fold 00, and ROI v2 CORAL fold 00. These are independent model runs; their grades are not averaged or combined.

For the supplied 540×360 photo, the ResNet50 output is MGI 3; ROI v1 returns 12 boxes (11 crop grades 1 and one crop grade 3, maximum 3); ROI v2 returns 12 boxes (9 crop grades 1 and 3 crop grades 2, maximum 2). These different single-photo results do not establish which model is more accurate. The UI also shows the saved 680-image OOF comparison: ResNet + Logistic 47.50%, EfficientNet + Logistic 52.21%, ROI v1 60.74%, and ROI v2 59.71%. The 52.21% EfficientNet + Logistic arm has no packaged fitted classifier, so it cannot currently run on an uploaded photo. ROI v1 and v2 use fold 00 for illustration, not a final all-development refit.

## Start the demo

From the project root, run:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
.venv/bin/python -B -m src.tabular.api --port 8770 \
  --local-photo-uploads \
  --vision-checkpoint models/vision_live_demo_v1/v3_best.pt \
  --roi-v1-return-zip data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return.zip \
  --roi-v1-device mps \
  --roi-v2-return-zip data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip \
  --roi-v2-device mps
```

The optional user-photo runtime is enabled explicitly by `--local-photo-uploads`. It loads the existing pinned ResNet50 checkpoint and the checksum-verified fold-00 pairs from both ROI return archives. No model is trained or downloaded. Open `http://127.0.0.1:8770`, select **Vision · exploratory evidence**, choose a photo, check the local-processing/research-limits box, then run each of the three model actions. Their outputs remain visible together until the photo is reset or replaced. Stop the server with Ctrl+C in the terminal.

## What the presenter sees

**Run ResNet50 + Grad-CAM** returns the selected image, one predicted whole-image MGI grade, four model output scores for MGI 1–4, and the heatmap and overlay for that prediction. The heatmap represents model attention; it is not a tooth boundary or clinical explanation. The current checkpoint has no whole-image MGI 0 output.

**Run YOLO v1 · 60.74% OOF** loads the saved v1 detector and weighted-CE crop classifier. **Run YOLO v2 CORAL · 59.71% OOF** loads the saved v2 CORAL pair. Each model proposes tooth-region boxes, predicts a grade per crop, and shows the maximum crop grade as a provisional image-level summary. Detector confidence describes box detection, not MGI grade confidence. Both use fold 00 for this illustration; neither is a final all-development refit or a clinically validated image-level MGI result.

These three Vision outputs do not merge with the questionnaire branch. Questionnaire inputs separately estimate previous self-reported gum treatment (OHQ850); they do not predict current disease, and their outputs are not combined with photo grades.

## Photo handling and colour

Accepted files are JPEG, PNG, or WebP, up to 8 MiB and within the image dimension limit. The API checks the payload format against its content type, applies EXIF orientation, converts an embedded ICC profile to sRGB, and assumes sRGB for RGB photos with no embedded profile. CMYK needs an embedded profile. This input policy lets ordinary phone photos run through the demo; it is not clinical colour calibration. MGI and tooth/gum appearance can vary with lighting, camera settings and colour processing.

The app is loopback-only at `127.0.0.1`. It requires the consent checkbox. Images are processed in memory; the ROI adapter uses a temporary file for the existing detector helper and removes it after inference. Neither route adds uploaded photos to the dataset or saves them. The output includes `photo_saved: false`.

## Sample result and limits

The owner-provided RGB JPEG (540×360, no embedded ICC) was accepted under the explicit sRGB assumption. ResNet50 predicted MGI 3 with these model outputs:

| Grade | Model output |
|---|---:|
| MGI 1 | 0.1293 |
| MGI 2 | 0.2825 |
| MGI 3 | 0.3508 |
| MGI 4 | 0.2374 |

The Grad-CAM hotspot fell mainly on the upper lip, not the teeth. This shows why an attention overlay must not be described as a clinical boundary. ROI v1 returned 12 boxes (11 crop grades of 1, one crop grade of 3), hence provisional maximum crop grade 3. ROI v2 returned 12 boxes (9 crop grades of 1, 3 crop grades of 2), hence provisional maximum crop grade 2. Both detector confidence ranges were 0.5322–0.7285. These are outputs for one photo, not an accuracy result. They do not establish clinical performance.

The saved same-680-image OOF comparison is ResNet + balanced Logistic head 47.50% accuracy / 0.2951 Macro-F1; EfficientNet + Logistic head 52.21% / 0.3464; ROI v1 60.74% / 0.3384; and ROI v2 CORAL 59.71% / 0.3279. ROI v1 has the highest accuracy in this table but lower Macro-F1 than EfficientNet and Grade 2 recall of 8/84 versus 27/84; all four have Grade 1 recall 0/12. Therefore these results do not identify a universally best model or show the weak-grade problem is fixed. The ResNet50 + Grad-CAM live checkpoint is a separate saved model and is not the ResNet + Logistic row. Labels remain provisional, participant independence is unverified, and neither branch is clinically validated.

## Verification performed

- Focused tests: 57 passed for local upload normalization, both ROI runtimes, evidence data, existing photo explanation and API integration.
- Local server: all three photo runtimes reported ready on MPS; the aggregate evidence route returned the verified four-row 680-image comparison.
- API: an upload without consent returned HTTP 403; consented requests for the same sample photo returned HTTP 200 through ResNet, ROI v1 and ROI v2, each with `photo_saved: false`.
- Browser UI: a generated-only PNG completed file selection and consent; all three model outputs remained visible together after running each button. The ResNet panel labels its scores as uncalibrated. The two ROI models correctly returned no grade for this non-dental synthetic image.
- Actual sample response: ResNet predicted MGI 3; ROI v1 predicted maximum grade 3 across 12 boxes; ROI v2 predicted maximum grade 2 across 12 boxes. These are side-by-side examples only.
- Preservation: sample photo SHA-256 `195e3cd12410f75117b95893349edaaaddb9a15a3ca4405d68ac61a4f3a5fef1`, ResNet checkpoint SHA-256 `36dd33662e277d3770995bf406f714b71231e77846a4a6a01ef418864259b2ee`, ROI v1 ZIP SHA-256 `ebb41badf4bd2154019dad55ba2f459ad1807c7f42b0722c13d849be2460f9bb`, and ROI v2 ZIP SHA-256 `e78240b01a1b039e091be0d2e31881ce96c1b1e47388e99f8f49b2541094771b` were checked. No training, labels, splits, protected Test data or existing PP1 result files were modified.
- Browser file chooser test was blocked because the available Playwright browser restricts file selection to a different project directory. The local HTTP upload routes were tested directly with the real sample file.
