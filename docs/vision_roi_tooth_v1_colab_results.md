# Tooth ROI Colab result — v1

Date: 17 October 2026  
Status: **All five planned folds completed and returned.** The result does not solve the Grade 1–2 recognition problem and does not replace the PP1 demo model.

## What ran

The Colab run used a Tesla T4 with CUDA, Ultralytics 8.4.178, PyTorch 2.11.0+cu130 and torchvision 0.26.0+cu130. It trained a one-class YOLO26n `tooth_roi` detector for 30 epochs and a ResNet-18 crop classifier for 12 epochs in each of five fixed folds. Each fold fit 544 images/6,528 crops and scored 136 images/1,632 crops. Fit and score crops stayed with their parent images. Fold metrics say `full_model_selection_on_score_fold: false` for all five folds.

The return package matches the prepared fold protocol SHA-256 `2253db0e89aad06a2fe49a90d313b7ae0e08a806b87845d49753b3d9e48dbc4b` and fold assignment SHA-256 `e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4`. We independently checked all 680 Training IDs, provisional labels, content-group IDs and fold assignments against the existing EfficientNet OOF evidence. Each image has one OOF prediction. No Validation image was used for model selection; the completion record says Test was not used.

## Image-level MGI results

All metrics use the 680 Training photos, with provisional caption-derived image grades 1–4. There are no whole-image grade 0 examples. The confusion matrices use row=true grade, column=predicted grade, in order 1, 2, 3, 4.

| Workflow | Accuracy | Macro-F1 | Balanced accuracy | Grade 1 recall | Grade 2 recall | Grade 3 recall | Grade 4 recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Historical nested EfficientNet features + Logistic Regression | 52.21% (355/680) | 0.3464 | 0.3486 | 0/12 (0%) | 27/84 (32.14%) | 96/223 (43.05%) | 232/361 (64.27%) |
| ROI detector + crop classifier | 60.74% (413/680) | 0.3384 | 0.3437 | 0/12 (0%) | 8/84 (9.52%) | 92/223 (41.26%) | 313/361 (86.70%) |
| Majority grade-4 baseline | 53.09% (361/680) | 0.1734 | 0.2500 | 0/12 (0%) | 0/84 (0%) | 0/223 (0%) | 361/361 (100%) |

The ROI pipeline got 58 more images correct than the historical nested EfficientNet result, mainly by getting more Grade 4 images correct. It also got 19 fewer Grade 2 images correct; Grade 1 stayed at zero correct. Its predicted-grade counts were 1 / 20 / 189 / 470 for grades 1–4, versus true support 12 / 84 / 223 / 361. This is an upward skew toward Grade 4, not a fix for Grades 1 and 2. The Grade 1/2 feasibility target remains unmet; the project’s provisional Macro-F1 target of 0.70 is also unmet.

Confusion matrices:

| Workflow | Matrix, rows/columns grades 1–4 |
| --- | --- |
| Historical EfficientNet | `[[0,5,5,2],[4,27,28,25],[8,33,96,86],[4,34,91,232]]` |
| ROI pipeline | `[[0,3,7,2],[1,8,43,32],[0,8,92,123],[0,1,47,313]]` |

A paired 1,000-draw bootstrap resampled the 680 saved content groups with replacement, using seed 42 and fixed OOF predictions. All 680 groups are single-image groups; no draws were undefined. ROI minus historical EfficientNet intervals were: accuracy **+8.53 percentage points** (95% conditional interval +3.82 to +12.94), Macro-F1 **−0.80 pp** (−5.03 to +3.35), balanced accuracy **−0.49 pp** (−4.35 to +3.30), and Grade 2 recall **−22.62 pp** (−33.33 to −12.64). These intervals describe fixed predictions on this provisional cohort; they do not account for refitting, model-selection uncertainty, or unknown participant identity.

## Tooth detector results

The one-class tooth-ROI detector averaged **mAP50 0.9598** (fold range 0.9446–0.9718) and **mAP50–95 0.4967** (range 0.4777–0.5134) over the five 136-image score folds. Detection coverage at confidence 0.25 was 680/680. These measure tooth-region localization only; they are not image-level MGI accuracy and do not prove clinical gum boundaries.

## Ground-truth-crop classifier diagnostic

Across the five held-out folds, the crop classifier was also scored on 8,160 source-annotated tooth crops, bypassing detector localization. It achieved 46.67% crop accuracy, Macro-F1 0.4054 and balanced accuracy 0.3950. Per-grade crop recall for MGI 0–4 was 15.35%, 37.20%, 34.12%, 57.49% and 53.35%. This is a tooth-crop diagnostic, not the image-level MGI result: the full photo pipeline must also detect ROIs and take the maximum predicted tooth grade. The grade-2-to-3/4 confusion and max aggregation are plausible contributors to the low image-level Grade 2 recall, but the saved outputs do not establish one cause.

## Returned files and local smoke

The original returned ZIP is retained in Downloads. A verified copy and its extracted contents are in the ignored local folder:

- ZIP: `data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return.zip`
- Checkpoints/results: `data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return/`
- ZIP size: 698,712,947 bytes; SHA-256: `ebb41badf4bd2154019dad55ba2f459ad1807c7f42b0722c13d849be2460f9bb`
- CRC check passed; all 19 manifested files match their byte counts and SHA-256 values.

Fold 00 detector and classifier loaded locally on Apple MPS. An isolated smoke inference on the fold’s own held-out development image `Training/00002` returned image grade 4 with 12 tooth ROIs, matching the saved OOF row. The expected grade from the provisional caption is 3, so this is also an example of a real image-level error. The overlay is at `data/vision/roi_tooth_v1_20261017/demo_outputs/colab_fold00_training_00002/roi_overlay.png`; it is an experimental visual, not a clinical boundary. The live PP1 model and UI were not changed.

The existing preservation record still reports **10/10** protected artifact hashes matched, including the live demo checkpoint, questionnaire model, manifests, prior model results and source files. No commit or push was made.

## Limits and viva explanation

These are research outputs from provisional image labels. Qualified clinical label approval is false, participant independence is unverified, and there are zero whole-image MGI 0 cases. There was no Test evaluation. The max-over-ROIs rule and the rare-grade support need further evaluation; the observed Grade 4 skew is descriptive and does not establish a single cause. Do not present this as a diagnosis, a periodontitis stage, a final Test score, or a ready-to-deploy model.

Viva explanation: “YOLO only finds tooth regions. ResNet-18 assigns each crop a provisional MGI grade, and the image score is the maximum crop grade. The detector mAP checks localization; the separate image-level metrics check grade prediction. Accuracy rose, but Grade 2 recall and Macro-F1 did not, so we cannot say the ROI method fixed classification.”
