# Actual nested EfficientNet cached-head experiment — v1

2026-10-16. One owner-authorized95-fit run completed. **Provisional labels; non-clinical; non-final; participant independence unverified.**

[Frozen prospective plan](vision_nested_feature_probe_plan_v1.md), [actual aggregate evidence/all inner settings](vision_nested_feature_probe_results_v1.json). Historical53Validationpilot50.94% is a different population and must not be ranked directly against these680TrainingOOF results.

## Actual same-cohort comparison

All rows use680Training records, provisional MGI1/2/3/4support12/84/223/361, exact same five outerfolds and fixed ImageNet features. The new row evaluates an **inner-selected workflow**, not one final chosen head. No full680deployment refit was made.

| Workflow | Accuracy | Macro-F1 | Balanced accuracy | Recall MGI1/2/3/4 (correct/support) | QWK | Macro AUROC | Brier | MAE |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| ResNet balancedC1, historical | .475000 | .295114 | .293791 | 0/12;17/84;73/223;233/361 | .214752 | .633569 | .831294 | See original report |
| EfficientNet balancedC1, historical | .526471 | .341037 | .340590 | 0/12;22/84;99/223;237/361 | .267839 | .711806 | .753383 | .588235 |
| EfficientNet unweightedC1, historical | .532353 | .337377 | .336938 | 0/12;19/84;100/223;243/361 | .256634 | .715040 | .750812 | .570588 |
| **New nestedEfficientNet head** | **.522059** | **.346429** | **.348645** | **0/12;27/84;96/223;232/361** | **.300275** | **.716342** | **.613977** | **.601471** |
| Majority | .530882 | .173391 | .250000 | 0/12;0/84;0/223;361/361 | .000000 | .500000 | .938235 | .627941 |
| Training-prior | .530882 | .173391 | .250000 | 0/12;0/84;0/223;361/361 | .000000 | .484326 | .595072 | .627941 |

New confusion matrix, rows=true provisional MGI1–4,columns=predictedMGI1–4:

```
 0   5   5   2
 4  27  28  25
 8  33  96  86
 4  34  91 232
```

Predicted counts16/99/220/345. Within-one accuracy.885294. Grade2recall32.14%, Grade3recall43.05%, Grade4recall64.27%; Grade1recall0%. Grade2errors4→MGI1,28→MGI3,25→MGI4. Its truegrade is among top2 in51/84.

## Settings actually selected

| Outer fold | C | Class weight | Fits |
|---|---:|---|---:|
|0|.01|balanced|19|
|1|.01|balanced|19|
|2|.01|balanced|19|
|3|.1|balanced|19|
|4|.01|balanced|19|

Each outer-fitting subset ran six fixed settings×three innerfolds, selected meaninner macro-F1 with the predefined tie order, then fitted one outer model. Fresh scaler/class weights for every fitting subset. Outer scoring labels did not choose settings. All30inner candidate summaries are retained in JSON; no settings omitted or extra search performed.

## What improved and what did not

Against savedbalancedC1: Grade2correct22→27, macro-F1.341037→.346429, balancedaccuracy.340590→.348645,QWK.267839→.300275 and Brier.753383→.613977. But accuracy358→355correct, Grade3correct99→96, Grade4correct237→232, ordinalMAE.588235→.601471. **Mixed trade-offs; no across-grade reliability or final winner.** Descriptive improvement over prior heads is not separately established as statistically significant.

Saved-probability diagnostics: mean maximum probability when wrong .618236, versus .810040 forbalancedC1. Incorrect predictions with maximum probability≥.8 fell185→48;≥.9 fell137→23. These are fixed descriptive bins, not selected clinical cutoffs. Lower Brier does not mean calibrated probabilities; the prior baseline still has better Brier. No calibration was fitted.

Prospectively specified1000-draw paired content-group bootstrap differences versusmajority/prior: macro-F1[.142076,.205798], balancedaccuracy[.067929,.132703],QWK[.228956,.367339];0undefined draws. These are conditional saved-OOF intervals, **not** refitting/participant/selection-corrected intervals. NestedCV handles this six-setting head search; earlier encoder/development selection and unknown participant identity remain limitations.

## Verification and boundaries

- 95real Logisticfits,0neuraloptimizersteps,0newencoderexecution. CPUtwo threads,8.422s including result generation/bootstrap;peakRSS212.47MiB, not a controlled speed benchmark.
- Onlythree existing cache input files opened:features.npz/results.json/oof.npz. Runtime audit blocked all other Vision data paths. No original images,53Validation,181held,NP015,CAM or Test payloads accessed.
- 57independent saved-result assertions passed: immutable680membership/support/folds, group isolation, actualouter scalermeans, allsixinner candidates/selection order, convergence, independent metrics/confusion/recalls, unchanged baseline predictions/cache/hash and1000bootstrap coverage.0verificationrefits.
- Existing10generated nested-runner tests reused, not rerun. Old results/code/labels/splits and research gates preserved; no installs/cloud/commit/push. One-run authorization consumed; no automatic retry/next experiment.

Exact local outputs: `data/vision/training680_nested_efficientnet_v1_20261016T123118054533Z`; authorization/access/runtime/verification: `data/vision/nested_efficientnet_execution_v1_20261016T123118054533Z`. PublicJSON contains hashes; per-record predictions remain ignored/local.

## Next action

Use the existing52Training held-review package to obtain genuine qualified annotation and grouping decisions. Do not add held images automatically or select them using model errors. Further model sweeps are not an established solution for12Grade1examples, absentwhole-imageMGI0, uncertain labels or participant identity. Keep the current model as an explicitly provisional demo; do not claim reliable four-grade or clinical performance.
