# 680 Training records frozen-feature signal check — actual results v1

2026-10-16 · branch vinuthan · **One owner-authorized local exploratory run completed.**

**Finding:** limited grade-discriminating signal under this fixed setup, with higher macro-F1, balanced accuracy and QWK than fold-derived baselines. This is a mixed result: accuracy is lower and probability error is substantially worse than the fold-prior baseline. No final-model selection, clinical validation or valid MGI 0 prediction is established.

Provisional labels; non-clinical; non-final; participant independence unverified.

## Frozen design and actual execution

- Original 680 Training records only, provisional grades 1–4 support **12 / 84 / 223 / 361**. Original 53 Validation records, 181 holds, NP015 and final Test payloads excluded. Cached 733-record manifest metadata was validated; only 680 Training model-array payloads opened.
- Existing 224×224 B1 extended-float arrays and one shared ImageNet normalization; no clipping, new export or source JPEG decoding.
- Official ImageNet ResNet-50 V2, frozen eval encoder and BatchNorm, 2,048 average-pool features; historical dental-tuned checkpoints forbidden.
- Exactly five seed 42 StratifiedGroupKFold folds, 544 fitting/136 scoring records each; IDs/folds frozen before extraction. Same predeclared fold support; no search or repeats.
- Fresh StandardScaler and LogisticRegression(C=1, balanced, lbfgs, max_iter=2000) inside each fitting fold. Exactly 5 classifier fits and 10 cheap majority/prior fits. **Zero neural optimizer steps.**
- Fit passed the existing convergence-warning stop. Extraction passed unchanged encoder/BatchNorm tensor checks.
- Local CPU, two torch threads. Actual probe runtime **98.69s**; process peak RSS **1125.09MiB**, measured by macOS resource.ru_maxrss. Weight download timing is separate.
- Owner separately authorized official weights download after missing-cache preflight. Download: 102,540,417 bytes, SHA **11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca**; no retry or alternate weights.
- Original MGI 0–4 definitions and final research-training gate unchanged; four supported grades here are exploratory.

## Pooled out-of-fold results

Each of 680 Training records has one score from a classifier that did not fit that record or its known content group.

| Metric | Frozen ResNet50 + balanced LR | Fold majority | Fold prior |
| --- | ---: | ---: | ---: |
| Accuracy ↑ | 0.475000 | 0.530882 | 0.530882 |
| Macro-F1 ↑ | 0.295114 | 0.173391 | 0.173391 |
| Balanced accuracy ↑ | 0.293791 | 0.250000 | 0.250000 |
| Quadratic weighted kappa ↑ | 0.214752 | 0.000000 | 0.000000 |
| Ordinal MAE ↓ | 0.620588 | 0.627941 | 0.627941 |
| Macro OVR AUROC ↑ | 0.633569 | 0.500000 | 0.484326 |
| Multiclass Brier ↓ | 0.831294 | 0.938235 | 0.595072 |
| Within-one-grade accuracy ↑ | 0.911765 | 0.858824 | 0.858824 |

Do not directly rank these against historical 53-record Validation v1/v2/v3 metrics: populations, heads and selection histories differ. The prior baseline's below 0.5 AUROC is the measured result of fold-varying training-prior probabilities, not an assumed 0.5 value.

Both baselines choose grade 4 for every record, hence identical hard-decision metrics. Their probabilities and Brier/AUROC values differ.

## Per-grade errors

| True MGI / predicted MGI | 1 | 2 | 3 | 4 | Support | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 3 | 4 | 5 | 12 | 0/12 = 0.000000 |
| 2 | 2 | 17 | 33 | 32 | 84 | 17/84 = 0.202381 |
| 3 | 1 | 22 | 73 | 127 | 223 | 73/223 = 0.327354 |
| 4 | 0 | 18 | 110 | 233 | 361 | 233/361 = 0.645429 |

Predicted counts 1/2/3/4: **3 / 60 / 220 / 397**.

Grade 2: **17 correct, 2→grade 1, 33→grade 3, 32→grade 4**. Grade 1: **0/12 correct**; support is insufficient for strong conclusions. Grade 2/3 performance remains weak. These observations do not establish label quality, preprocessing, weighting or fine-tuning as causal explanations.

## Uncertainty and trade-offs

| Linear minus either hard-decision baseline | Difference | Conditional 95% interval |
| --- | ---: | --- |
| Macro-F1 ↑ | +0.121724 | [+0.090782, +0.152331] |
| Balanced accuracy ↑ | +0.043791 | [+0.016199, +0.072388] |
| Quadratic weighted kappa ↑ | +0.214752 | [+0.139935, +0.291322] |

1,000 fixed-seed paired content-group bootstrap draws; 0 undefined. These are **baseline-difference intervals conditional on saved OOF predictions**, not absolute per-model or model-refit intervals. The 680 known groups are singletons; distinct participants are not established. Unknown participant overlap, provisional labels and prior repeated development selection are not corrected.

- Accuracy vs majority/prior: **-0.055882** (-5.59 percentage points).
- Brier vs prior: **+0.236222**, worse. Outputs are not calibrated/validated confidence estimates.
- MAE improves only **0.007353** grades.
- Within-one accuracy is secondary: a constant high/middle grade can score well.
- No whole-image MGI 0 examples exist here. This probe does not resolve the missing class.

## Verification and provenance

- **65 saved-result assertions passed, 0 failed** after correcting an initial ad-hoc row-sum assertion. Independently calculated sklearn metrics/confusion/recalls, exact IDs/labels/folds, fold-only Dummy probabilities and SHA bindings agree. Separate read-only reviewer metrics agree within 2e-15.
- Numerical note: initial audit used 1e-12 row-sum tolerance; measured maximum deviation **1.7637648852542043e-07** passes the established 1e-6 absolute metric tolerance. No saved probabilities were renormalized; production code, tests and colour policies unchanged.
- **16 prior focused generated tests** reused with unchanged source hashes; suite not rerun unnecessarily. The 65 assertions are not 65 pytest cases or a full repository test run.
- File-open tracing observed exactly 680 allowed Training model arrays; 0 Validation arrays, 0 held/Test payloads, 0 CAM arrays. Input writes blocked. Manifest and bound source-code hashes unchanged after execution.
- Manifest SHA: 8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f
- Fold SHA: e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4
- Feature-cache SHA: 5eba4578f72c3ad911b7ea69d61ed23aa9cd1d620362712b0dd244a6c8d75eb5
- OOF SHA: 18318980b1cfa216d535633ff57067d4456b39b150335a8abfdf2dc16c8174ea
- Raw results SHA: 7c3f788ecb629d34da2f31b1e8fd29091745fa10c33cff4d9f59ef227fd9edf4

Ignored local outputs: data/vision/training680_frozen_probe_v1_20261016T143627954173/.
Execution, owner decision, download, preflight and verification records: data/vision/training680_probe_execution_record_v1_20261016T143627954173/.
Numeric features, image IDs/probabilities and weights remain outside Git.

Aggregate evidence: [results JSON](vision_frozen_feature_signal_results_v1.json). Original [plan](vision_frozen_feature_signal_plan_v1.md) and [implementation evidence](vision_frozen_feature_probe_implementation_v1.md) preserved as historical records.

## One next recommendation

Prepare a bounded **EfficientNet-B0 frozen-feature comparison using these exact 680 records/folds and the same fold-local linear head**. This tests the proposal's alternate encoder before further blind ResNet fine-tuning. It needs prospective configuration/official-weight bindings and its own execution scope; it has **not** run or been authorized by this completed one-run record. No resolution/C sweep or held-label recovery based on errors.

Qualified label/group approval and participant evidence remain separate. All 181 holds remain held. No final model or MGI 0 support approved.

## Three important blocks — Tamil

1. **Freeze:** model.requires_grad_(False); model.eval() — ResNet/BatchNorm weights மாறாது; படத்திலிருந்து features மட்டும் கிடைக்கும்.
2. **Fold-local fitting:** StandardScaler + LogisticRegression; model.fit(x[fit],y[fit]) — fitting fold மட்டும் scaler/classifier-க்கு தெரியும்; score fold தகவல் training-க்குள் செல்லாது.
3. **OOF scoring:** predictions['linear'][score] = model.predict_proba(x[score]) — ஒவ்வொரு image-க்கும் அதை fit செய்யாத classifier-லிருந்து probability கிடைக்கும்; 680 scores முழுமையாக உள்ளன.

Viva: **Why not use the dental fine-tuned v3 encoder for this CV?** அது ஏற்கனவே இந்த Training labels பார்த்துள்ளது; score fold label தகவல் representation-க்குள் முன்பே கசிந்திருக்கும்.

No new neural training, original source/label/split changes, cloud upload, final Test use, commit or push.
