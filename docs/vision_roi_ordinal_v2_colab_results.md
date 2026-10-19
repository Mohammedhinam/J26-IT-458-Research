# Ordinal tooth-crop experiment v2 — returned Colab results

Date: 17 October 2026  
Status: **Five-fold Colab run and local checkpoint smoke test complete. The CORAL arm modestly improves Grade 2 recall versus the matched weighted-CE arm, but does not improve overall accuracy, does not identify Grade 1, and does not outperform the earlier ROI model overall. Keep it as a separate research result; do not replace the PP1 demo.**

## What ran

The owner returned `roi_tooth_v2_coral_return.zip` from a Tesla T4 Colab run. It completed 12 epochs for each arm across five fixed folds. The experiment used the same 680 provisional Training images, 544 fit / 136 score images per fold, 8,160 tooth crops, and the saved v1 tooth detector for both arms. Validation pixels, held images, and Test data were not used; validation did not select models or settings. The labels are not clinically approved, and participant independence is not verified.

The matched comparison is between fit-fold weighted cross-entropy (CE) and a CORAL-style ordinal head. Both use the same ResNet-18 ImageNet V1 initialization, crop protocol, five folds, and 12-epoch budget. This is a comparison of two complete classifier methods; it is not a loss-only ablation because the CE arm is class-weighted and the ordinal arm uses uniform threshold BCE.

The 641,395,780-byte ZIP passed CRC validation and its 21 return-manifest entries matched byte counts and SHA-256 values. The run configuration, completion record, fold assignments, dataset/protocol/code input hashes, and 680-row OOF files were checked. Each arm has one OOF prediction for all 680 Training IDs; the IDs, targets, groups, and folds match the frozen manifest. Every OOF metric and the paired bootstrap were independently recomputed from the returned predictions. `test_split_used=false`, `validation_used_for_model_selection=false`, and `labels_approved=false` are recorded in the receipt.

## Image-level results

Only provisional image grades 1–4 are represented. There are no whole-image grade-0 examples, so grade-0 recall is unsupported. Rows in the confusion matrices are true grades and columns are predicted grades, in order 1, 2, 3, 4.

| Same-run arm | Accuracy | Macro-F1 | Balanced accuracy | Grade 1 recall | Grade 2 recall | Grade 3 recall | Grade 4 recall | QWK | Ordinal MAE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Weighted CE | 59.85% (407/680) | 0.3241 | 0.3348 | 0/12 (0%) | 5/84 (5.95%) | 97/223 (43.50%) | 305/361 (84.49%) | 0.3645 | 0.4647 |
| CORAL ordinal | 59.71% (406/680) | 0.3279 | 0.3351 | 0/12 (0%) | 15/84 (17.86%) | 46/223 (20.63%) | 345/361 (95.57%) | 0.3751 | 0.4750 |

Confusion matrices:

- Weighted CE: `[[0,2,8,2],[0,5,48,31],[0,10,97,116],[0,0,56,305]]`
- CORAL: `[[0,3,7,2],[0,15,31,38],[0,8,46,169],[0,0,16,345]]`

CORAL correctly classified 10 more Grade 2 images than the matched CE arm, but it correctly classified 51 fewer Grade 3 images and 40 more Grade 4 images. Overall it got one fewer image correct. Macro-F1 increased by 0.0038; balanced accuracy increased by 0.0003; neither result establishes a reliable overall improvement. Grade 1 stayed at zero. Grade 2 remains weak at 15/84 and below the historical EfficientNet result of 27/84.

Against the earlier v1 ROI run (60.74% accuracy, 0.3384 Macro-F1, Grade 2 8/84), this CORAL run has lower accuracy and Macro-F1, while Grade 2 recall is descriptively higher at 15/84. Because the classifier training run differs, this cross-version difference cannot be attributed to CORAL alone. The earlier EfficientNet nested-feature reference remains 52.21% accuracy, 0.3464 Macro-F1, Grade 1 0/12 and Grade 2 27/84. These comparisons use the same 680 provisional Training IDs and saved folds; they do not make the labels clinically verified or resolve unknown participant overlap.

The paired 1,000-draw, seed-42 bootstrap is conditional on these fixed predictions. CORAL-minus-CE intervals were accuracy −3.68 to +3.24 percentage points, Macro-F1 −3.31 to +4.11 pp, balanced accuracy −2.78 to +2.81 pp, Grade 1 recall 0 pp, and Grade 2 recall +4.61 to +20.25 pp. It does not include refitting uncertainty, and it cannot establish participant-level independence.

## Detector and tooth-level interpretation

The v2 archive includes the same frozen fold-specific detector checkpoints as the verified v1 return bundle; their SHA-256 hashes match. Detector mAP was not newly estimated in v2. The v1 mAP50 / mAP50–95 values (0.9598 / 0.4967 mean across its five folds) are localization results only and must not be described as image-level MGI accuracy. The returned CORAL classifier's image grade is the maximum predicted grade over detected tooth ROIs. The returned probabilities are per-tooth probabilities; this method does not define a calibrated image-level probability distribution.

The return also records a separate classifier-only diagnostic on the annotated tooth crops in each score fold. Summing the five fold confusion matrices gives 8,160 crop predictions per arm:

| Crop classifier on annotated tooth crops | Accuracy | Macro-F1 | Balanced accuracy | Recall for MGI 0, 1, 2, 3, 4 |
| --- | ---: | ---: | ---: | --- |
| Weighted CE | 46.59% | 0.4031 | 0.3923 | 14.91%, 39.15%, 31.41%, 59.48%, 51.18% |
| CORAL ordinal | 40.78% | 0.3738 | 0.4192 | 35.53%, 28.73%, 33.20%, 29.87%, 82.28% |

These are tooth-crop classification metrics using annotated crop locations; they bypass predicted localization and cannot be substituted for photo-level MGI metrics or detector mAP. CORAL has higher balanced accuracy on crops but lower crop accuracy and Macro-F1. It also has lower Grade 1 crop recall than weighted CE, while whole-image Grade 1 recall is zero in both arms. Crop-level predictions do not validate the image-level maximum-grade rule.

## Mac smoke test and isolated preview

The CORAL fold-00 model and matching detector loaded on Apple MPS. On `Training/00002` from the frozen Training package, it detected 12 ROIs and predicted image grade 4, exactly matching the saved CORAL OOF row (12 ROIs, grade 4); the provisional caption-derived target is grade 3. Each tooth's five CORAL class probabilities sums to 1. The result is a checkpoint/inference parity smoke test on one image, not a new accuracy estimate.

The separate research-only adapter is [roi_ordinal_v2_demo.py](../src/vision/roi_ordinal_v2_demo.py), with model loading and preprocessing in [roi_ordinal_v2_inference.py](../src/vision/roi_ordinal_v2_inference.py). It saves JSON with the per-tooth probabilities and a separate ROI overlay to a new output directory. The overlay explicitly calls the displayed score a YOLO **box score**; it is not the MGI classifier probability. It also carries a visible research-only disclaimer. The JSON preserves the per-grade probabilities separately. The generated smoke preview is [roi_overlay.png](../data/vision/roi_tooth_v1_20261017/ordinal_v2/demo_outputs_v2/Training_00002_fold00_mps_research_only_final/roi_overlay.png), with its [prediction record](../data/vision/roi_tooth_v1_20261017/ordinal_v2/demo_outputs_v2/Training_00002_fold00_mps_research_only_final/prediction.json).

Example local command for another permitted image, using the already verified return ZIP and its adjacent `verification.json`:

```bash
PYTHONPATH=. .venv/bin/python -m src.vision.roi_ordinal_v2_demo \
  --photo /path/to/permitted_photo.jpg \
  --return-zip data/vision/roi_tooth_v1_20261017/ordinal_v2/colab_return_v1_20261017/roi_tooth_v2_coral_return.zip \
  --fold 0 \
  --output data/vision/roi_tooth_v1_20261017/ordinal_v2/demo_outputs_v2/my_photo_fold00 \
  --device mps
```

Each fold checkpoint was trained on only four of the five folds. There is no final model refit on all development images, so a chosen-fold preview is not the final PP1 model or a validated new-photo product. The v2 adapter remains separate; the working PP1 Grad-CAM route, model, and UI were not modified by this experiment.

## Interpretation and limits

The run suggests that this CORAL setup trades Grade 3 performance for more Grade 2 and Grade 4 predictions. It does **not** fix the classification problem: Grade 1 is still never identified, Grade 2 recall is only 17.86%, overall accuracy is slightly lower than matched weighted CE, and both Macro-F1 values are below 0.35. The paired fixed-prediction interval for Grade 2 is positive, but that conditional interval is not a substitute for refitting, qualified annotations, participant grouping, or a truly independent evaluation.

All image and tooth labels remain provisional. Boxes are model-localized tooth/perigingival regions, not clinically verified gum boundaries. This output is not a diagnosis or a periodontitis stage. No protected Test score was produced. Do not promote these checkpoints into the working PP1 demo on the strength of this experiment.

## How to explain it in a viva

1. The detector locates tooth regions; the crop classifier predicts an ordered MGI grade for each region; the photo grade is the maximum predicted tooth grade.
2. CORAL predicts four ordered threshold probabilities (`grade > 0` through `grade > 3`). The final image result is still checked with separate image-level metrics; detector mAP is not classification accuracy.
3. In the matched run, CORAL found 10 more Grade 2 images than weighted CE but lost 51 correct Grade 3 images and one correct image overall. Therefore it is a measured trade-off, not a proven general improvement.

Likely question: **Did the ordinal method solve the low-accuracy problem?**  
Answer: “No. It raised Grade 2 recall compared with the matched weighted-CE arm, but Grade 1 recall stayed zero, overall accuracy was one image lower, and Grade 3 recall dropped. The result is an exploratory trade-off on provisional labels, not a validated fix.”

Assumptions and unresolved points: MGI grade order is meaningful for this exploratory model; image labels and tooth labels still need qualified verification; participant independence is not established; grade 0 is absent at image level; and a final all-development refit has not been made.
