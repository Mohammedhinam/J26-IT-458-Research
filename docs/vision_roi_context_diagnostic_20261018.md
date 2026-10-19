# ROI coverage and fixed-context inference diagnostic

18 October 2026. Local exploratory engineering only. No training or demo change.

## Finding

The existing crops already include visible gum margins in multiple examples.
The four-photo review does **not** demonstrate that missing gum context is the
main cause of weak Grade 1/2 performance. It does not establish clinically
sufficient coverage either. Existing annotations describe tooth/perigingival
regions, not verified gingival segmentation masks.

One prospectively fixed expansion from 15% to 30% context on each side increased
single-fold accuracy by one image but reduced Macro-F1, balanced accuracy and
Grade 2 recall. **Keep the existing demo preprocessing. No model promotion.**

## Coverage inspection

Four deterministic fit-only cases: Training/00055 and 00075 (provisional image
Grade 1), Training/00009 and 00015 (Grade 2). They belong to the 544-image fit
partition, not the 136 scoring partition. Selection took the first two sorted
fit IDs in each grade. No held, Validation or Test photo payload was opened.

For each case, the contact sheet shows the existing sRGB model-image derivative,
source tooth annotations in blue, the 15% padded training crop windows in orange,
and all 12 actual saved training crops. Source annotation classes 2–6 map to
provisional tooth MGI 0–4. Classes 0/1 are arch regions and are excluded here.
The original full-resolution source photograph is not the displayed derivative.

All **48/48 crop JPEGs reproduced byte for byte**, using the original crop
geometry, Lanczos resize, JPEG quality 95, subsampling 0 and optimize settings.
The 56 accessed model-photo/annotation/crop hashes remained unchanged.

AI visual observations: baseline crops contain visible marginal gum tissue,
including upper and lower examples. The amount varies between teeth and photos.
The crops contain tooth surfaces too. These observations are not clinical review
and do not assign new grades or masks. A qualified reviewer must judge tissue
coverage against the intended MGI assessment. Blank review fields remain blank.

## Fixed comparison

`scripts/pp1_roi_context_diagnostic_v1.py` runs two distinct stages. `prepare`
creates only the fit review. After viewing those sheets, `fixed_protocol.json`
was written before `score` accessed scoring pixels.

- Same original fold 0: 544 fit / 136 score, scoring grades 1/2/3/4 = 3/17/44/72.
- Original content groups remain disjoint. Membership hashes match the actual
  frozen fold-00 checkpoint evidence and the independent ResNet pilot manifest.
- Same v1 fold-00 YOLO detector and ResNet18 crop-classifier checkpoints.
- Detector inference once per image: size 640, confidence .25, NMS IoU .70.
  Both arms consume the **same predicted boxes**. Detector mAP is unchanged.
- Baseline 15% versus candidate 30% symmetric padding, clipped to the same image.
  The historical v1 scoring resize/normalization and max-crop-grade rule remain.
- Frozen weights, eval mode, no optimizer, no training and no parameter search.
- All 136 score photos had detections. Local MPS execution took 14.42 seconds
  for the paired inference loop, excluding model setup and verification.

| Metric | Baseline 15% | Expanded 30% |
|---|---:|---:|
| Accuracy | 84/136 = 61.76% | 85/136 = 62.50% |
| Macro-F1, supported image grades 1–4 | 0.334708 | 0.297981 |
| Balanced accuracy | 0.347092 | 0.328283 |
| Grade 1 recall | 0/3 | 0/3 |
| Grade 2 recall | 1/17 | 0/17 |
| Grade 3 recall | 20/44 | 15/44 |
| Grade 4 recall | 63/72 | 70/72 |
| Ordinal MAE | 0.441176 | 0.448529 |
| QWK | 0.429895 | 0.379869 |

Confusion matrices, rows true / columns predicted grades 1,2,3,4:

```text
Baseline                  Expanded
0  1   2   0              0  0   3   0
0  1  11   5              0  0  10   7
0  1  20  23              0  0  15  29
0  1   8  63              0  0   2  70
```

23 image predictions changed. Both correct 76, baseline alone correct 8,
expanded alone correct 9, both wrong 43. Extra context moved predictions toward
Grade 4 in this experiment. This is evidence against adopting this inference
change as a Grade 1/2 fix. It does not prove that every context-aware training
method would fail.

## Interpretation limits

This is a **frozen-weight inference ablation**, not a retrained ROI model or a
new 680-image OOF experiment. The classifier trained on 15% crops; 30% context
changes its input distribution. A future matched training study would answer a
different question. One small fold, three Grade 1 cases, provisional labels and
unverified participant independence limit conclusions. Existing development
selection history also means this is exploratory, not a fresh confirmatory test.

The local 15% baseline reproduced **128/136** historical Colab hard predictions,
not all 136. Historical CUDA versus current MPS/runtime execution differ. The
cause of those eight disagreements has not been isolated. Both new arms share
the current detector outputs, which makes their within-run comparison matched.
Do not claim exact historical replication, a new 680-image accuracy, or a
statistically/clinically established gain from the 1-image accuracy difference.

No Grad-CAM was fabricated for this ROI pipeline. Earlier controlled ResNet
matched CAM evidence remains in `docs/vision_resnet50_fold0_colab_results_v1.md`.
Clinician review of both that evidence and these crop sheets is **pending**.

## Grade 1/2 data preparation

The safe Training cohort still contains only **12 Grade 1 and 84 Grade 2 images**.
Within fold-0 fit data, the review queue contains **9 Grade 1 + 67 Grade 2 = 76**
cases. It is a metadata-only queue with empty qualified-grade/reviewer fields.
It introduces no additional examples, corrected labels, clinical approval or
release of any held case. No reviewer was contacted.

The next evidence step is qualified review and genuinely additional permitted
Grade 1/2 photos with participant/source tracking. Use the accompanying data
intake checklist. Model outputs and doctor-demo observations must never silently
become training labels. Keep all 181 holds and protected Test aliases excluded.

## Reproducibility and evidence

Private local root: `data/vision/pp1_final_local_20261018_v1/roi_context/`.

- `index.html`: local four-case coverage gallery.
- `preparation.json`: counts, selection and exact crop-export checks.
- `fixed_protocol.json`: pre-scoring settings and fit-only observations.
- `results.json`, `per_image_predictions.jsonl`: actual matched predictions.
- `independent_verification.json`: **76 assertions passed, 0 failed**. These
  independently recompute metrics, aggregation, membership and source preservation.
- `coverage_review_pending.json`, `grade12_fit_review_queue.json`: blank reviews.

Twelve generated geometry checks also passed: parity with the historical crop
formula, in-image bounds and containment of the baseline by the expanded crop.
They are assertions, not additional pytest test cases. The runner refuses to
overwrite outputs. For an intentional new run, choose a new versioned OUT path
and freeze a new protocol rather than deleting or replacing this evidence.

Important code blocks to defend: `inputs()` enforces split/group membership;
`crop_bounds()` changes only the declared context; `score_fixed()` reuses one
box list and the same frozen classifier for both arms. Saving uses exclusive
creation so existing evidence cannot be overwritten accidentally.

Viva: **Why reject the higher accuracy?** The extra correct image came with worse
Macro-F1 and Grade 2 recall. Our research goal includes minority grades, so
accuracy alone does not justify changing the demo.
