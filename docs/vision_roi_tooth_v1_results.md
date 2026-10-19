# Tooth ROI detector and crop-classifier experiment v1

Date: 17 October 2026  
Status: **Five-fold Colab training and Mac return verification complete. Overall accuracy rose, but Macro-F1 and Grades 1–2 did not improve. This remains a provisional research experiment, not an approved clinical model.**

## What was built

This is a separate exploratory Vision experiment. It does not replace the live PP1 model, its checkpoints, Grad-CAM path, labels, splits, or prior results.

The experiment uses a two-stage workflow:

1. A one-class YOLO26n detector finds tooth/perigingival regions. Its derived class 0 means only “tooth_roi”; it does not mean MGI grade 0.
2. A separate ResNet-18 classifies each detected crop into provisional tooth-level MGI 0–4. Its training crops retain the audited source TXT mapping: original class IDs 2–6 map to grades 0–4. It uses inverse-frequency class weights calculated from the current fold’s fit crops only.
3. The image-level output is the maximum grade among the crop classifier’s detected ROIs. If the detector finds no ROI, the image prediction is an explicit abstention and counts as incorrect in image-level scoring.

Broad source classes 0 and 1 (maxilla and mandible) are preserved separately and excluded from detector training and detector mAP. Detection mAP is a localization result; it is not image-level MGI accuracy.

## Dataset and annotation checks

The final package uses the existing frozen safe development manifest and fold protocol. It includes 680 Training images and 53 Validation images. The 53 Validation images are not used for model selection or the primary five-fold evaluation. The 181 held records, NP015 aliases, and all protected Test payloads are absent.

The source annotation audit for these 733 allowlisted records found:

- 2,199 caption variants, three per image.
- 10,262 source TXT rows, 14 boxes per image: one maxilla box, one mandible box, and 12 tooth boxes.
- 8,796 tooth boxes and derived crops.
- Zero selected-record disagreement between the three caption-derived maximum grades and the frozen manifest label.
- Zero disagreement between the maximum MGI grade mapped from source tooth TXT classes 2–6 and that caption-derived image maximum.
- Every selected source TXT parsed as five numeric YOLO fields with class IDs 0–6 and normalized coordinates in range.
- One source box extended 0.0024 pixels beyond the bottom image edge because of coordinate rounding. The derived view clips it to the image boundary; the original TXT is unchanged.
- All 733 inputs are RGB JPEGs with the same embedded opRGB ICC profile. New model views are color-managed to sRGB and resized to maximum side 1,600 pixels. Original source JPEG bytes are unchanged.

The raw source class mapping in the audited package is:

| Source TXT class | Meaning used here | Training tooth boxes | Validation tooth boxes |
| --- | --- | ---: | ---: |
| 0 | Maxilla ROI; not trained | — | — |
| 1 | Mandible ROI; not trained | — | — |
| 2 | Provisional tooth MGI 0 | 228 | 25 |
| 3 | Provisional tooth MGI 1 | 1,180 | 214 |
| 4 | Provisional tooth MGI 2 | 2,066 | 217 |
| 5 | Provisional tooth MGI 3 | 3,117 | 144 |
| 6 | Provisional tooth MGI 4 | 1,569 | 36 |

Training image-level maximum-label support is MGI 0–4 = 0 / 12 / 84 / 223 / 361. Validation image-level support is 0 / 1 / 13 / 22 / 17. The detector and crop classifier can see tooth-level MGI 0 boxes, but there are no whole-image MGI 0 examples in this selected bundle. MGI 1 image-level support remains only 12 Training and one Validation image. No grade was clinically verified for this experiment, and participant independence is not established by content-group separation.

The archive uses the existing five fixed Training folds, with content groups checked not to cross fit/score boundaries. It does not use random crop-level splitting: crops inherit their parent image’s fold. The full Colab run evaluates one out-of-fold image prediction per each of the 680 Training records.

Each saved fold has 6,528 fit crops and 1,632 score crops; all five fit sets contain all five crop grades. This makes the class-weight calculation valid without inventing support. The score-fold crop counts are diagnostic only; the primary label remains one image-level maximum per photo.

## Fair comparison with the existing model

The historical EfficientNet reference is 52.21% accuracy and macro-F1 0.3464 on 680-image OOF evaluation; its Grade 1 recall was 0/12 and Grade 2 recall 27/84. That experiment used frozen EfficientNet features with a Logistic Regression head. The existing majority baseline was 53.09% accuracy and macro-F1 0.1734. See the existing [nested feature probe report](vision_nested_feature_probe_results_v1.md).

The completed ROI run scores one out-of-fold image prediction for each of the same 680 Training IDs, with the exact saved five-fold assignment (fold-assignment SHA-256 `e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4`). See the [returned Colab results](vision_roi_tooth_v1_colab_results.md) for metrics and conditional paired intervals. Image-level accuracy rose to 60.74%, but Macro-F1 fell to 0.3384, balanced accuracy to 0.3437, Grade 1 stayed 0/12, and Grade 2 fell to 8/84 from 27/84. Detector mAP is separate from MGI classification.

## Final data package

Use only this final package archive:

- Archive: data/vision/roi_tooth_v1_20261017/roi_tooth_dataset_v1_oneclass_v4.zip
- Size: 476,604,177 bytes
- SHA-256: 9b1e797f7f593438a5318410ed2aa1cfdd7a66b8db0aac865b3229b63d3a20c8
- Image manifest SHA-256: 975f4cde460b69c074b2655910f597623454b774dc27768d75f8002ce2ff1619
- Fold file SHA-256: ea850f313ec15db91fdb2cf8ab30c88f87bd63285d48758b6d4662ea7341857c
- Dataset build report: data/vision/roi_tooth_v1_20261017/dataset_build_report_oneclass.json

The ZIP passed its CRC check and file-count audit: 680 Training images/labels/raw annotations, 53 Validation images/labels/raw annotations, 8,796 crops, 2,199 selected captions, and zero held/Test/alias files. Derived detector labels contain only class 0 (tooth_roi). The package contains the latest training, inference and Mac demo scripts, plus the pinned dependency file. Earlier partial and five-grade detector package attempts remain in separate paths as preserved engineering history; they are not the upload package.

## Mac MPS pilot — actual result

A bounded one-epoch systems pilot ran on the MacBook Air M4 (16 GB RAM), using Ultralytics 8.4.178, PyTorch 2.11.0 and MPS:

- Fit subset: 48 images and 576 crops from fold 0’s fit IDs, selected to include all five crop grades.
- Score subset: 12 images and 144 ground-truth crops from fold 0’s score IDs.
- YOLO26n: one class, 640-pixel input, batch 4, one epoch.
- ResNet-18 crop classifier: batch 32, one epoch, class weights fit on the 576 training crops.
- MPS training completed; detector training printed about 2.39 GB peak MPS memory. Checkpoint loading, detector validation, crop classification, prediction, and output writing completed after correcting the output path.
- Local pretrained weights are isolated: YOLO26n at data/vision/roi_tooth_v1_20261017/baseline/pretrained_yolo26n.pt (5,544,453 bytes; SHA-256 f28150ee9e94164f9e5bf6bd9318236fc039b000239be5bebe30a74acd802c99) and torchvision ResNet-18 IMAGENET1K_V1 (SHA-256 f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec in the local Torch cache). The Colab runtime downloads its own initial weights; neither file is included in the data ZIP.

Observed smoke outputs, **not model-quality claims**:

| Measurement | Pilot output | Correct interpretation |
| --- | ---: | --- |
| One-class detector mAP50 | 0.0320 on 12 images | One epoch and 12 images; not a detector result suitable for comparison |
| Oracle ground-truth-crop classifier accuracy | 20.14% on 144 crops | The crop classifier works on real crops; it is not the photo-to-grade pipeline metric |
| Oracle crop macro-F1 / balanced accuracy | 0.2065 / 0.2579 | Same small, single-epoch crop smoke |
| Oracle crop recall, MGI 1 / MGI 2 | 18.18% / 4.44% | Small crop support; no improvement claim |
| Full photo pipeline at confidence 0.25 | 0/12 correct; 0% detection coverage | The one-epoch detector produced no boxes above the intended threshold |
| Low-confidence box-to-classifier path at 0.001 | 300 candidate boxes passed through the classifier | Deliberate plumbing stress test on Training/00002; boxes were dense and unusable |

The low-confidence output is not a threshold search or a demo-quality overlay. The completed Colab run and its actual image-level limitations are reported below; this small Mac pilot remains only an engineering smoke. It confirmed that image loading, one-class detection, crop extraction, ResNet loading, grade inference and overlay writing connect end to end.

Pilot files and exact counts are in data/vision/roi_tooth_v1_20261017/pilot/engineering_pilot_report.json. The pilot’s metrics are separate from the 52.21% EfficientNet reference and must not be compared as an improvement.

## Colab run and actual outputs

The completed notebook used the final ZIP at this Drive path:

    My Drive/RP-J26-IT-458/roi_tooth_v1/roi_tooth_dataset_v1_oneclass_v4.zip

The notebook checks the ZIP SHA-256, ZIP paths/CRC, all image and raw-label hashes, the source-tooth mapping, one-class detector labels, crop files, frozen fold coverage, and group separation. It installs requirements-vision-roi-v1.txt while using Colab’s existing GPU PyTorch/Torchvision environment. It stops if CUDA is not available.

The five-fold experiment completed on a Tesla T4: YOLO26n detector 30 epochs and ResNet-18 crop classifier 12 epochs, detector batch 16, crop batch 64, seed 42. The fold metrics confirm that the scoring fold did not drive model selection. The returned archive contains five detector/classifier checkpoint pairs.

Actual results were saved under the Drive folder:

- run_configuration.json — package, software, GPU, model-weight hashes and fixed configuration.
- fold_00 through fold_04 — detector and crop-classifier checkpoints and per-fold metrics.
- oof_predictions.csv and oof_metrics.json — one image-level prediction for each of the 680 Training records, Accuracy, Macro-F1, balanced accuracy, confusion matrix, per-grade recall and detection coverage.
- Detector mAP values, reported separately from image-level MGI.
- return_bundle and roi_tooth_v1_colab_return.zip — five model pairs, fold metrics, OOF evidence and a SHA-256 manifest.

The 53 Validation records were not used for model selection or the primary score. The returned OOF predictions contain only the 680 Training IDs; the completion record confirms the Test split was not used. Qualified label approval remains false, participant independence is unknown, and whole-image MGI 0 has no support.

## Returned checkpoints and isolated Mac smoke

The returned archive is saved at `data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return.zip` and extracted beside it. ZIP CRC passed and all 19 files matched the embedded SHA-256 manifest. The isolated Mac CLI loaded Fold 00 on MPS and produced the saved overlay for `Training/00002`; the result matched its OOF grade 4 and 12 detected ROIs. These experimental files are ignored by Git. The existing live-demo checkpoint and Grad-CAM path remain separate and unchanged.

The new local CLI runs one returned fold pair (fold 00 is suitable for a development smoke demo; it is not a model refit on all 680 images):

    .venv/bin/python -m src.vision.roi_demo_v1 \
      --photo /absolute/path/to/a/permitted/photo.jpg \
      --detector data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return/fold_00/detector_last.pt \
      --classifier data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return/fold_00/crop_classifier_last.pt \
      --output data/vision/roi_tooth_v1_20261017/demo_outputs/photo_001

It saves prediction.json and roi_overlay.png, predicts locally, honors EXIF orientation and embedded ICC profiles, and refuses to overwrite an existing output folder. The box overlay is a model explanation, not a gum boundary or clinical diagnosis. This CLI is isolated and is not wired into the currently working PP1 API/UI. The existing Grad-CAM demo remains unchanged. The returned model is still provisional and Grade 1/2 performance is weak; do not present it as a validated clinical model or replace the PP1 demo.

## Preservation, issues, and limits

Before/after SHA-256 checks matched all 10 recorded existing artifacts, including the live ResNet checkpoint, questionnaire model, baseline manifest/folds, prior Vision reports/verification and protected source files. No original model, checkpoint, label, source image, split, demo/API/UI code or research result was overwritten. No commit, push or external upload was made.

Two initial exporter attempts stopped on a caption-parser mismatch and left partial directories; they were retained. The mismatch was caused by my first exporter pattern omitting the audited “Level 3 gingivitis” wording. I switched to the repository’s canonical caption parser and prechecked all 733 allowlisted records before the final build. The first complete five-grade detector export is also retained; the final design separates one-class localization from MGI crop classification.

A separate agent read-only audit accidentally exposed derived Test filenames and aggregate caption/conflict metadata from an existing audit document. No Test image or TXT payload was opened, copied or used, and no Test-derived value entered the dataset, training or metrics. This incident is recorded for transparency; the sealed Test payload remains out of scope.

Formal clinical/supervisor label verification, participant identity review, the missing image-level MGI 0 feasibility decision, and real-photo demo validation remain pending. Colab training and the development-only image-level comparison are complete; their mixed result is in the [returned results report](vision_roi_tooth_v1_colab_results.md). The one-class detector has AGPL-3.0 Ultralytics dependencies; review package licensing before any non-academic distribution.

## Files to understand and defend

- src/vision/roi_workflow_v1.py — validates five-field TXT rows, maps original classes, clips box geometry and computes maximum image grade/metrics.
- src/vision/roi_dataset_v1.py — checks the frozen manifest/folds, audits captions and boxes, color-manages images, exports derivative labels/crops, and creates a final ZIP without editing source files.
- src/vision/roi_colab_train_v1.py — builds fold lists, trains/resumes YOLO and ResNet-18, fits crop class weights only on fit crops, and reports detector mAP, crop-only metrics and image-level MGI separately.
- src/vision/roi_inference_v1.py and src/vision/roi_demo_v1.py — load returned model pairs and run a local photo to grade plus ROI overlay, without modifying the existing demo.
- tests/test_roi_workflow_v1.py — synthetic tests for mapping, malformed labels, clipped boxes, abstention and adapter output.
- notebooks/roi_tooth_v1_colab.ipynb — clean-runtime setup, integrity checks, full five-fold run/resume, result collection.

Key viva explanation: “TXT class 0 in the derived YOLO file means tooth_roi, while original TXT classes 2–6 provide provisional MGI crop targets. We first detect tooth/perigingival boxes, classify each crop, and take the maximum predicted grade for image MGI. Detector mAP and image-level MGI scores answer different questions.”

Likely viva question: “Why use class weights?”  
Answer: “The training crops are imbalanced across grades. I calculate weights from only the training side of each fold so rare grades contribute more to the crop-classifier loss, while the held-out fold remains untouched.”

Likely viva question: “Why is the Mac pilot not evidence that accuracy improved?”  
Answer: “It used one epoch and only 12 score images, and found no boxes at the planned threshold. That checked software paths only. The later five-fold T4 result is the actual development comparison: accuracy rose, but Macro-F1 and Grade 1/2 recall did not improve.”

## Verification evidence and references

- Synthetic ROI tests: 14 passed.
- Existing caption-label tests plus ROI tests: 52 passed.
- Notebook JSON and Python code cells were checked before execution; the clean T4 Colab run completed all five folds and returned a checksum-verified result bundle.
- Returned result ZIP CRC and all 19 SHA-256 manifest entries passed; exact 680-ID/five-fold membership was matched to the existing EfficientNet OOF evidence.
- Fold 00 detector/classifier loaded on Mac MPS; one held-out Training image produced an OOF-matching grade and overlay.
- Focused ROI tests after return: 14 passed, 0 failed.
- Package CRC and allowlist audit passed; model and research artifact SHA-256 preservation audit matched 10/10.
- Official Ultralytics training documentation: https://docs.ultralytics.com/modes/train
- Official Ultralytics detection-label format documentation: https://docs.ultralytics.com/datasets/detect
- Mendeley source dataset: https://data.mendeley.com/datasets/3253gj88rr/1
