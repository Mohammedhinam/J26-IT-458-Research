# EfficientNet-B0 versus ResNet-50 — Training-only fixed-feature comparison v1

2026-10-16 · branch vinuthan · One bounded owner-authorized local comparison completed.

**Result:** EfficientNet-B0 features improve several point estimates over the existing ResNet-50 fixed-feature probe on the same 680 records/folds. This does not establish a learning-code bug, causal explanation, final winning model or clinical validity. Accuracy remains below the majority baseline, Brier remains worse than fold prior, and Grade 1 recall remains zero.

Provisional labels; non-clinical; non-final; participant independence unverified.

## Frozen recipe and scope

Followed [prospective plan](vision_efficientnet_probe_plan_v1.md), frozen before real feature extraction. Exactly 680 original Training candidates, labels MGI 1–4 support 12/84/223/361, identical content groups and five seed-42 folds. Each fold fits 544 and scores 136. Cached 733-record manifest metadata checked; 53 Validation, 181 holds, NP015, CAM arrays and Test payloads excluded.

Official EfficientNet_B0_Weights.IMAGENET1K_V1, fixed eval encoder/BatchNorm, removed classifier, 1,280 average-pool features. Previous ResNet uses 2,048 dimensions; this is part of the encoder comparison. Same existing 224×224 B1 extended-float inputs and ImageNet normalization, no clipping/augmentation/new resize. This matches the prior probe, not the canonical torchvision JPEG resize/crop recipe.

Reused existing fold/scaler/classifier/metric functions: fresh StandardScaler → LogisticRegression(C=1, balanced, lbfgs, max_iter=2000, seed42) per fold. Five classifier and ten Dummy fits. Zero neural optimizer steps or historical ResNet reruns. Convergence warnings/non-finite values/hash failures stop, no search/automatic retry.

Owner separately approved only official EfficientNet weights download. TLS official URL and filename SHA prefix verified; full measured SHA bound before execution: **7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934**, 21,444,401 bytes. The full SHA is computed locally, not claimed independently published. Runner performs no download.

## Actual pooled OOF results

| Metric | EfficientNet-B0 | ResNet-50 | Majority | Fold prior |
| --- | ---: | ---: | ---: | ---: |
| Accuracy ↑ | 0.526471 | 0.475000 | 0.530882 | 0.530882 |
| Macro-F1 ↑ | 0.341037 | 0.295114 | 0.173391 | 0.173391 |
| Balanced accuracy ↑ | 0.340590 | 0.293791 | 0.250000 | 0.250000 |
| QWK ↑ | 0.267839 | 0.214752 | 0.000000 | 0.000000 |
| Ordinal MAE ↓ | 0.588235 | 0.620588 | 0.627941 | 0.627941 |
| Macro OVR AUROC ↑ | 0.711806 | 0.633569 | 0.500000 | 0.484326 |
| Multiclass Brier ↓ | 0.753383 | 0.831294 | 0.938235 | 0.595072 |
| Within-one accuracy ↑ | 0.894118 | 0.911765 | 0.858824 | 0.858824 |

Both hard-decision baselines predict Grade 4 everywhere; their probability metrics differ. Same source IDs, labels/folds and baseline predictions were verified exactly; historical 53-record dental-pilot scores are not directly comparable to this table.

EfficientNet versus ResNet: accuracy **+5.15 percentage points**, macro-F1 **+0.045923**, macro-AUROC **+0.078237** and Brier **-0.077911**. Within-one accuracy worsened. Versus fold prior, accuracy is **-0.44 percentage points** and Brier **+0.158311**, worse.

## Grade-level evidence

| True / predicted MGI | 1 | 2 | 3 | 4 | Recall |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 0 | 3 | 6 | 3 | 0/12 = 0.000000 |
| 2 | 1 | 22 | 33 | 28 | 22/84 = 0.261905 |
| 3 | 6 | 27 | 99 | 91 | 99/223 = 0.443946 |
| 4 | 3 | 26 | 95 | 237 | 237/361 = 0.656510 |

Predicted counts MGI 1/2/3/4: **10 / 78 / 233 / 359**.

Grade 2 correct changes 17/84 → 22/84; errors are 1→Grade 1, 33→Grade 3, 28→Grade 4. Grade 3 changes 73/223 → 99/223; Grade 4 changes 233/361 → 237/361. Grade 1 remains 0/12. This does not resolve scarce MGI 1 or absent whole-image MGI 0.

## Paired uncertainty

| Difference | Reference | Point | Conditional 95% interval |
| --- | --- | ---: | --- |
| Macro-F1 ↑ | resnet | +0.045923 | [+0.000363, +0.092263] |
| Balanced accuracy ↑ | resnet | +0.046799 | [+0.003308, +0.091316] |
| QWK ↑ | resnet | +0.053087 | [-0.047026, +0.161460] |
| Macro-F1 ↑ | majority | +0.167646 | [+0.136334, +0.203878] |
| Balanced accuracy ↑ | majority | +0.090590 | [+0.062128, +0.125833] |
| QWK ↑ | majority | +0.267839 | [+0.196172, +0.345527] |
| Macro-F1 ↑ | prior | +0.167646 | [+0.136334, +0.203878] |
| Balanced accuracy ↑ | prior | +0.090590 | [+0.062128, +0.125833] |
| QWK ↑ | prior | +0.267839 | [+0.196172, +0.345527] |

1,000 seed-42 content-group bootstrap draws; zero undefined draws. Intervals condition on saved OOF predictions, omit model-refitting uncertainty, unknown participant clustering and development-selection history. All 680 known groups are singletons; participant independence remains unverified. Two encoders are now compared, each with one fixed head configuration; no multiplicity/selection correction or independent confirmation.

The macro-F1 difference lower limit against ResNet is only +0.000363 and sensitive to Monte Carlo/tail precision; do not call it decisive. QWK difference includes zero. Conditional positive intervals do not justify a final model declaration or clinically reliable probabilities.

## Verification and runtime

- **46 focused generated/regression tests passed, 0 failed/errors/skipped:** 30 new EfficientNet tests plus 16 directly affected existing probe tests. No dental data/weights download in tests.
- **79 saved-result assertions passed, 0 failed:** independent sklearn metrics, confusion/recalls, training-fold priors/majority, exact IDs/labels/folds, current hashes and runtime access. Probability maximum row-sum deviation 1.4500983525067568e-07, within existing 1e-6 contract. Probabilities not renormalized.
- Actual local CPU/two-thread run **48.26s**, macOS process peak RSS **1130.66 MiB**. Not a controlled hardware speed benchmark versus the previous run.
- Exactly 680 model-array hashes verified/read. Runtime trace: zero Validation/held/Test/CAM payloads; source writes blocked. Frozen encoder/BatchNorm state unchanged.
- Original B1 manifest, prior ResNet results/OOF and all old implementation hashes preserved. New explicit scope and output directory; one-run permission consumed.
- Fold SHA: e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4
- New feature SHA: d8cda6807e7954e2dd8d7cf20be77b46e5063f89910436df294381901231d838
- New OOF SHA: c78fd5be1507c0e4b18b9cafff2a8f63ef12fac2d584c1fea52d1ae1b863d8cb
- Raw results SHA: d450ea6a9e21d560a3e21b51df707a538b676783575e9ebe25b4d3ca84bf0eb8
- JUnit SHA: bb7281cd7e45761c1c16149e5c0e720ffd45f35f84828775295f99d636e35535

Local ignored output: data/vision/training680_efficientnet_probe_v1_20261016T151400472912/.
Owner decision/preflight/download/access/result-verification evidence: data/vision/training680_efficientnet_execution_v1_20261016T151400472912/.
Aggregate evidence: [JSON](vision_efficientnet_probe_results_v1.json).
Original research model/Grad-CAM/trainer and final-approved manifest gates were not modified.

## What was and was not fixed

Generated checks verify grade mapping, frozen BatchNorm/weights, consistent unclipped normalization, fold-local scaling/class weighting, exact cache/fold membership and tamper rejection. No confirmed learning implementation bug was found in these checks. The controlled encoder replacement improved several measured OOF metrics; it does not show whether remaining errors are caused by resolution, labels, limited samples, imbalance or optimization. Do not relabel/exclude model errors or manufacture MGI 0.

## One next recommendation

Prepare one prospectively bounded **head-only learning comparison using the cached EfficientNet features**: existing balanced C=1 versus fixed unweighted C=1 on the same folds, to measure probability/discrimination/recall trade-offs without new image inference. This is advice, not an automatic additional run. No C/seed/resolution sweep, final threshold/model or recovery of held images. Qualified label/group review remains independent and necessary.

## Three blocks to understand — Tamil

1. **model.classifier = Identity; model.eval; requires_grad(False):** EfficientNet-ல் image features மட்டும் எடுக்கிறோம்; weights/BatchNorm மாறாது.
2. **base.probe(features, ids, labels, groups):** பழைய அதே folds, fitting-only scaler மற்றும் balanced Logistic classifier மீண்டும் பயன்படுத்தப்படுகின்றன; encoder தவிர classifier recipe மாறாது.
3. **Reference OOF SHA + exact IDs/folds + paired comparison:** ஒரே images-ன் இரண்டு encoder predictions-ஐ ஒப்பிடுகிறோம்; easy/hard images மாறியதால் வந்த போலி முன்னேற்றம் அல்ல. Unknown participant overlap இன்னும் தீரவில்லை.

Viva: **Does AUROC 0.712 mean 71.2% correct diagnosis?** இல்லை. இங்கு 4 provisional grades-க்கான macro ranking metric; accuracy 52.65%. இது clinical diagnosis validation அல்ல.

No original image/CSV/TXT/label/split modifications, held/Test inference, cloud upload, final-model activation, commit or push.
