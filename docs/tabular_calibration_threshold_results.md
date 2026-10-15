# Development-only calibration and demonstration-threshold validation — 2026-10-13

Owner approved docs/tabular_calibration_threshold_plan.md before implementation. Its historical pending status is preserved. No final model or deployment threshold selected.
Command: `.venv/bin/python -B -m src.tabular.calibration_threshold_nhanes`.
Development N=6251; Yes=1553 (24.844025%); No=4698. Outcome: self-reported previous gum treatment, not current disease risk/diagnosis.

## Approved recipe and preservation

Logistic C=1/no weights and approved XGBoost A, each Full/Awareness-ablated. Four candidates × Raw/Sigmoid = eight workflows. Existing preprocessing/feature selectors/model parameters reused without historical edits.
Five original outer folds; each outer-training fold split 80/20 (stratified, seed 42) into model/calibration and tuning pools. Three inner stratified folds (seed 42), sigmoid ensemble=False; 3 inner base fits + 1 pool refit per candidate/outer fold. Raw uses the exact same refitted estimator object as sigmoid. No separate raw fit, eval_set or early stopping.
Recipe budget executed: 80 base-estimator fits (40 Logistic/40 XGBoost), 20 binary sigmoid fits, eight joint diagnostic attempts. Inner OOF scores/labels train calibration; independent tuning labels select thresholds; outer labels used only for validation metrics/diagnostics.
Frozen manifest hash: `4d0f82149cb20485186ad929fca0a070a72fe4e4a3032b1cf8da37954c131551`. Outer-fold hash: `0822ca63d5ffa57375141ae15d97ca08333a207463eae909237892dbe9e3adb0` — MATCH to historical evidence before any fit. Final held-out payloads never loaded/decoded/transformed/evaluated; selective development loading/zero repair reused. Historical code/reports/plans/manifest and existing tracked/untracked work preserved.
New raw controls use smaller pool training sizes than historical experiments; no exact historical-metric reproduction is expected or claimed. Reduced inner-fit sizes also affect calibration score distributions; validate, do not assume calibration success.

## All eight workflows — fixed threshold 0.50

| Workflow | AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity | Specificity | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic / Full / Raw | 0.736631 | 0.512988 | 0.513245 | 0.158030 | 0.289762 | 0.937633 | 4405 | 293 | 1103 | 450 |
| Logistic / Full / Sigmoid | 0.736676 | 0.512206 | 0.512478 | 0.157956 | 0.269800 | 0.943806 | 4434 | 264 | 1134 | 419 |
| Logistic / Awareness-ablated / Raw | 0.662327 | 0.380100 | 0.380566 | 0.175221 | 0.047006 | 0.987229 | 4638 | 60 | 1480 | 73 |
| Logistic / Awareness-ablated / Sigmoid | 0.662399 | 0.380249 | 0.380744 | 0.175082 | 0.025113 | 0.993614 | 4668 | 30 | 1514 | 39 |
| XGBoost / Full / Raw | 0.738936 | 0.515313 | 0.515542 | 0.157477 | 0.264649 | 0.945934 | 4444 | 254 | 1142 | 411 |
| XGBoost / Full / Sigmoid | 0.738792 | 0.514229 | 0.514479 | 0.158184 | 0.275596 | 0.941039 | 4421 | 277 | 1125 | 428 |
| XGBoost / Awareness-ablated / Raw | 0.668366 | 0.383317 | 0.383851 | 0.174524 | 0.027688 | 0.992976 | 4665 | 33 | 1510 | 43 |
| XGBoost / Awareness-ablated / Sigmoid | 0.667924 | 0.382579 | 0.383112 | 0.174741 | 0.049581 | 0.984887 | 4627 | 71 | 1476 | 77 |

PR-AUC is trapezoidal; AP is separately defined. Threshold 0.50 is a reference only.

## Fold-learned Youden demonstration thresholds

Tuning grid 0.00–1.00 in 0.01 steps; maximise J, ties higher sensitivity then larger threshold. Exact integer confusion-count comparison avoids floating-point tie ambiguity. These are statistical demonstration thresholds, NOT clinically approved cutoffs. Each validation row uses its own fold's learned threshold, never a global average.
| Workflow | Sensitivity | Specificity | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic / Full / Raw | 0.554411 | 0.793316 | 3727 | 971 | 692 | 861 |
| Logistic / Full / Sigmoid | 0.555055 | 0.789911 | 3711 | 987 | 691 | 862 |
| Logistic / Awareness-ablated / Raw | 0.708950 | 0.521711 | 2451 | 2247 | 452 | 1101 |
| Logistic / Awareness-ablated / Sigmoid | 0.721829 | 0.512346 | 2407 | 2291 | 432 | 1121 |
| XGBoost / Full / Raw | 0.589182 | 0.751171 | 3529 | 1169 | 638 | 915 |
| XGBoost / Full / Sigmoid | 0.594334 | 0.735419 | 3455 | 1243 | 630 | 923 |
| XGBoost / Awareness-ablated / Raw | 0.716033 | 0.507237 | 2383 | 2315 | 441 | 1112 |
| XGBoost / Awareness-ablated / Sigmoid | 0.707663 | 0.516816 | 2428 | 2270 | 454 | 1099 |

| Workflow | Thresholds folds 1–5 | Min | Median | Max | Nonpositive tuning-J folds |
| --- | --- | --- | --- | --- | --- |
| Logistic / Full / Raw | 0.22, 0.31, 0.28, 0.28, 0.28 | 0.22 | 0.28 | 0.31 | 0 |
| Logistic / Full / Sigmoid | 0.22, 0.31, 0.28, 0.28, 0.28 | 0.22 | 0.28 | 0.31 | 0 |
| Logistic / Awareness-ablated / Raw | 0.25, 0.22, 0.24, 0.22, 0.24 | 0.22 | 0.24 | 0.25 | 0 |
| Logistic / Awareness-ablated / Sigmoid | 0.25, 0.23, 0.24, 0.22, 0.24 | 0.22 | 0.24 | 0.25 | 0 |
| XGBoost / Full / Raw | 0.24, 0.33, 0.25, 0.21, 0.25 | 0.21 | 0.25 | 0.33 | 0 |
| XGBoost / Full / Sigmoid | 0.21, 0.30, 0.22, 0.19, 0.23 | 0.19 | 0.22 | 0.30 | 0 |
| XGBoost / Awareness-ablated / Raw | 0.29, 0.20, 0.24, 0.25, 0.20 | 0.20 | 0.24 | 0.29 | 0 |
| XGBoost / Awareness-ablated / Sigmoid | 0.22, 0.20, 0.22, 0.24, 0.24 | 0.20 | 0.22 | 0.24 | 0 |

Any nonpositive-J fold is flagged as no useful tuning improvement; fixed 0.50 remains a reference, not a hidden successful fallback.

## Calibration diagnostics

Joint unpenalised regression y ~ intercept + slope × logit(p) on outer-OOF predictions, clipping only diagnostic logits at 1e-6. Ideal intercept=0/slope=1; these descriptive coefficients do not recalibrate scored probabilities. Joint intercept is not intercept-only calibration-in-the-large. Separation/nonconvergence is flagged, not silently penalised. Slope/intercept CIs remain pending.
| Workflow | Joint intercept | Slope | Clipped | Status |
| --- | --- | --- | --- | --- |
| Logistic / Full / Raw | -0.057952 | 0.937395 | 0 | OK |
| Logistic / Full / Sigmoid | 0.008003 | 1.005948 | 0 | OK |
| Logistic / Awareness-ablated / Raw | -0.102966 | 0.896493 | 0 | OK |
| Logistic / Awareness-ablated / Sigmoid | 0.010005 | 1.011005 | 0 | OK |
| XGBoost / Full / Raw | 0.048135 | 1.046072 | 0 | OK |
| XGBoost / Full / Sigmoid | 0.028747 | 1.023902 | 0 | OK |
| XGBoost / Awareness-ablated / Raw | 0.038691 | 1.040288 | 0 | OK |
| XGBoost / Awareness-ablated / Sigmoid | 0.056251 | 1.052809 | 0 | OK |

## Paired bootstrap 95% intervals

1,000 participant resamples, seed 42; same indices across workflows. Undefined one-class resamples: 0. Prediction-only: no model/calibrator/threshold refits. Conditional intervals omit training/selection variability, overlapping CV training dependence and survey design; not nationally representative uncertainty.

| Workflow | AUROC | PR-AUC (trapezoidal) | Average precision | Brier |
| --- | --- | --- | --- | --- |
| Logistic / Full / Raw | [0.721725, 0.750407] | [0.486406, 0.538303] | [0.486947, 0.538802] | [0.152647, 0.163919] |
| Logistic / Full / Sigmoid | [0.721728, 0.750444] | [0.485372, 0.537563] | [0.485983, 0.538089] | [0.152717, 0.163744] |
| Logistic / Awareness-ablated / Raw | [0.646957, 0.676846] | [0.359460, 0.403659] | [0.360402, 0.404485] | [0.170013, 0.180540] |
| Logistic / Awareness-ablated / Sigmoid | [0.647161, 0.676981] | [0.358839, 0.403560] | [0.359762, 0.404420] | [0.170011, 0.180347] |
| XGBoost / Full / Raw | [0.724198, 0.752044] | [0.487760, 0.540932] | [0.488298, 0.541421] | [0.152240, 0.163080] |
| XGBoost / Full / Sigmoid | [0.724130, 0.752055] | [0.486272, 0.540026] | [0.486960, 0.540533] | [0.152824, 0.163897] |
| XGBoost / Awareness-ablated / Raw | [0.653677, 0.682773] | [0.361439, 0.406623] | [0.362513, 0.407473] | [0.169453, 0.179718] |
| XGBoost / Awareness-ablated / Sigmoid | [0.653404, 0.682439] | [0.360812, 0.406020] | [0.361760, 0.407165] | [0.169667, 0.180146] |

| Workflow | Sensitivity @0.50 | Specificity @0.50 | Sensitivity learned | Specificity learned |
| --- | --- | --- | --- | --- |
| Logistic / Full / Raw | [0.268842, 0.311446] | [0.930835, 0.944355] | [0.529001, 0.578174] | [0.782004, 0.804315] |
| Logistic / Full / Sigmoid | [0.249054, 0.290850] | [0.937224, 0.950647] | [0.528853, 0.578507] | [0.778410, 0.801078] |
| Logistic / Awareness-ablated / Raw | [0.036822, 0.058414] | [0.983679, 0.990240] | [0.686721, 0.731377] | [0.508560, 0.536430] |
| Logistic / Awareness-ablated / Sigmoid | [0.017321, 0.033115] | [0.991239, 0.995761] | [0.699064, 0.743642] | [0.498725, 0.526880] |
| XGBoost / Full / Raw | [0.243328, 0.286665] | [0.939271, 0.952290] | [0.565619, 0.614090] | [0.739239, 0.763639] |
| XGBoost / Full / Sigmoid | [0.253319, 0.297298] | [0.934321, 0.947753] | [0.570259, 0.617657] | [0.723128, 0.747694] |
| XGBoost / Awareness-ablated / Raw | [0.020364, 0.036166] | [0.990578, 0.995331] | [0.695179, 0.737663] | [0.494061, 0.521510] |
| XGBoost / Awareness-ablated / Sigmoid | [0.039161, 0.060281] | [0.981046, 0.988273] | [0.686591, 0.729304] | [0.503170, 0.531171] |

Paired changes are Sigmoid minus Raw; negative Brier change indicates lower probability error. No causal/clinical superiority claim.

Paired changes are calculated from unrounded estimates; subtracting displayed six-decimal point estimates can differ by one in the last decimal.

| Candidate | AUROC | PR-AUC (trapezoidal) | Average precision | Brier |
| --- | --- | --- | --- | --- |
| Logistic / Full | 0.000046 [-0.000071, 0.000163] | -0.000782 [-0.001854, 0.000121] | -0.000767 [-0.001717, 0.000123] | -0.000074 [-0.000303, 0.000140] |
| Logistic / Awareness-ablated | 0.000073 [-0.000135, 0.000263] | 0.000149 [-0.000861, 0.001080] | 0.000178 [-0.000687, 0.001103] | -0.000139 [-0.000381, 0.000118] |
| XGBoost / Full | -0.000144 [-0.000427, 0.000130] | -0.001085 [-0.002514, 0.000312] | -0.001063 [-0.002387, 0.000329] | 0.000708 [0.000296, 0.001120] |
| XGBoost / Awareness-ablated | -0.000442 [-0.000804, -0.000073] | -0.000738 [-0.001887, 0.000313] | -0.000738 [-0.001837, 0.000296] | 0.000217 [-0.000115, 0.000598] |

| Candidate | Sensitivity @0.50 | Specificity @0.50 | Sensitivity learned | Specificity learned |
| --- | --- | --- | --- | --- |
| Logistic / Full | -0.019961 [-0.027745, -0.013358] | 0.006173 [0.004030, 0.008612] | 0.000644 [-0.002643, 0.004510] | -0.003406 [-0.005758, -0.001273] |
| Logistic / Awareness-ablated | -0.021893 [-0.029793, -0.014997] | 0.006386 [0.004244, 0.008883] | 0.012878 [0.006978, 0.019351] | -0.009366 [-0.012980, -0.006057] |
| XGBoost / Full | 0.010947 [0.006361, 0.015905] | -0.004896 [-0.007003, -0.003006] | 0.005151 [0.000000, 0.010891] | -0.015751 [-0.020004, -0.011881] |
| XGBoost / Awareness-ablated | 0.021893 [0.014705, 0.029929] | -0.008089 [-0.010944, -0.005741] | -0.008371 [-0.022079, 0.005088] | 0.009579 [0.000838, 0.018183] |

## Matched training-rate reference

Prior probabilities computed from each model/calibration pool, assigned to its outer validation rows; five prior calculations, no extra model fits. Historical Dummy results remain untouched.
| AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity @0.50 | Specificity @0.50 | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.499615 | 0.473595 | 0.248297 | 0.186718 | 0.000000 | 1.000000 | 4698 | 0 | 1553 | 0 |

## Reliability tables — ten quantile bins requested

### Logistic / Full / Raw — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 37 | 0.050969 | 0.059105 |
| 2 | 625 | 66 | 0.093260 | 0.105600 |
| 3 | 625 | 80 | 0.127820 | 0.128000 |
| 4 | 625 | 102 | 0.156755 | 0.163200 |
| 5 | 625 | 129 | 0.183903 | 0.206400 |
| 6 | 625 | 128 | 0.211428 | 0.204800 |
| 7 | 625 | 133 | 0.242575 | 0.212800 |
| 8 | 625 | 197 | 0.300719 | 0.315200 |
| 9 | 625 | 295 | 0.451492 | 0.472000 |
| 10 | 625 | 386 | 0.660689 | 0.617600 |

### Logistic / Full / Sigmoid — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 38 | 0.057543 | 0.060703 |
| 2 | 625 | 65 | 0.101059 | 0.104000 |
| 3 | 625 | 80 | 0.135234 | 0.128000 |
| 4 | 625 | 103 | 0.163283 | 0.164800 |
| 5 | 625 | 129 | 0.189367 | 0.206400 |
| 6 | 625 | 120 | 0.215535 | 0.192000 |
| 7 | 625 | 140 | 0.244791 | 0.224000 |
| 8 | 625 | 198 | 0.298851 | 0.316800 |
| 9 | 625 | 295 | 0.438729 | 0.472000 |
| 10 | 625 | 385 | 0.636950 | 0.616000 |

### Logistic / Awareness-ablated / Raw — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 48 | 0.065022 | 0.076677 |
| 2 | 625 | 76 | 0.115374 | 0.121600 |
| 3 | 625 | 103 | 0.155217 | 0.164800 |
| 4 | 625 | 134 | 0.193830 | 0.214400 |
| 5 | 625 | 145 | 0.229124 | 0.232000 |
| 6 | 625 | 176 | 0.261584 | 0.281600 |
| 7 | 626 | 179 | 0.293625 | 0.285942 |
| 8 | 624 | 187 | 0.328810 | 0.299679 |
| 9 | 625 | 226 | 0.374888 | 0.361600 |
| 10 | 625 | 279 | 0.466199 | 0.446400 |

### Logistic / Awareness-ablated / Sigmoid — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 47 | 0.076853 | 0.075080 |
| 2 | 625 | 76 | 0.127889 | 0.121600 |
| 3 | 625 | 105 | 0.165824 | 0.168000 |
| 4 | 625 | 134 | 0.201513 | 0.214400 |
| 5 | 625 | 145 | 0.233513 | 0.232000 |
| 6 | 625 | 174 | 0.262627 | 0.278400 |
| 7 | 625 | 179 | 0.290987 | 0.286400 |
| 8 | 625 | 187 | 0.322010 | 0.299200 |
| 9 | 625 | 228 | 0.362506 | 0.364800 |
| 10 | 625 | 278 | 0.442904 | 0.444800 |

### XGBoost / Full / Raw — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 33 | 0.062388 | 0.052716 |
| 2 | 625 | 61 | 0.106607 | 0.097600 |
| 3 | 625 | 86 | 0.139412 | 0.137600 |
| 4 | 625 | 94 | 0.167242 | 0.150400 |
| 5 | 625 | 134 | 0.192382 | 0.214400 |
| 6 | 625 | 135 | 0.214995 | 0.216000 |
| 7 | 625 | 133 | 0.237068 | 0.212800 |
| 8 | 625 | 191 | 0.289001 | 0.305600 |
| 9 | 625 | 298 | 0.441099 | 0.476800 |
| 10 | 625 | 388 | 0.630540 | 0.620800 |

### XGBoost / Full / Sigmoid — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 33 | 0.100601 | 0.052716 |
| 2 | 625 | 62 | 0.122874 | 0.099200 |
| 3 | 625 | 85 | 0.142474 | 0.136000 |
| 4 | 625 | 91 | 0.160721 | 0.145600 |
| 5 | 625 | 135 | 0.178652 | 0.216000 |
| 6 | 625 | 136 | 0.196141 | 0.217600 |
| 7 | 625 | 134 | 0.214464 | 0.214400 |
| 8 | 625 | 191 | 0.263680 | 0.305600 |
| 9 | 625 | 295 | 0.436812 | 0.472000 |
| 10 | 625 | 391 | 0.662140 | 0.625600 |

### XGBoost / Awareness-ablated / Raw — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 49 | 0.078493 | 0.078275 |
| 2 | 625 | 77 | 0.127274 | 0.123200 |
| 3 | 625 | 111 | 0.165823 | 0.177600 |
| 4 | 625 | 109 | 0.200693 | 0.174400 |
| 5 | 625 | 144 | 0.234331 | 0.230400 |
| 6 | 625 | 169 | 0.264567 | 0.270400 |
| 7 | 625 | 176 | 0.292933 | 0.281600 |
| 8 | 625 | 200 | 0.323775 | 0.320000 |
| 9 | 625 | 241 | 0.361913 | 0.385600 |
| 10 | 625 | 277 | 0.438251 | 0.443200 |

### XGBoost / Awareness-ablated / Sigmoid — 10 actual bins

| Bin | N | Yes | Mean probability | Observed Yes fraction |
| --- | --- | --- | --- | --- |
| 1 | 626 | 44 | 0.106900 | 0.070288 |
| 2 | 625 | 83 | 0.135158 | 0.132800 |
| 3 | 625 | 114 | 0.162144 | 0.182400 |
| 4 | 625 | 105 | 0.189703 | 0.168000 |
| 5 | 625 | 141 | 0.219768 | 0.225600 |
| 6 | 625 | 173 | 0.249322 | 0.276800 |
| 7 | 625 | 178 | 0.279449 | 0.284800 |
| 8 | 626 | 198 | 0.314821 | 0.316294 |
| 9 | 624 | 239 | 0.361667 | 0.383013 |
| 10 | 625 | 278 | 0.462673 | 0.444800 |

## Fold/inner-pool supports

| Fold | Pool N | Pool Yes | Tuning N | Tuning Yes | Validation N | Validation Yes | Inner membership hash |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4000 | 994 | 1000 | 248 | 1251 | 311 | 9fd242aa300998cb7b41545ff4bcce18a8e48254006259c43699edac66c020a7 |
| 2 | 4000 | 994 | 1001 | 249 | 1250 | 310 | 192c358316d506b5ec96b701b187cd8b77fe15f0735d5c0ae1897397eacb3c19 |
| 3 | 4000 | 994 | 1001 | 249 | 1250 | 310 | 1d1b21e9c95aadb82c081ce664fcba5bc89ecd4e3d1793a217a62e4a1bf5fc68 |
| 4 | 4000 | 993 | 1001 | 249 | 1250 | 311 | 86e890aae1c33aadb12e88f886dd7e17e97a3797d019eb283cc9f128469f259b |
| 5 | 4000 | 993 | 1001 | 249 | 1250 | 311 | 73c9ea961e9717169b7c5ac6c194f11c61d5a0fe840be967f5c46c4fac8adbc6 |

## Provisional probability-error ordering and limitations

Logistic sigmoid joint intercept/slope are closer to 0/1, but its small Brier reductions have paired intervals spanning zero. Full XGBoost sigmoid has higher Brier (paired increase 0.000708, conditional 95% interval [0.000296, 0.001120]); calibration did not automatically improve probability error. All eight diagnostic fits are OK with zero clipped predictions, but diagnostic coefficient intervals remain pending.

Learned Youden demonstration thresholds increase recall at the cost of false positives. For Full XGBoost Raw, TP rises from 411 to 915 and FP from 254 to 1,169 compared with 0.50. Awareness-ablated demonstration operating points have sensitivity around 0.71 but specificity near 0.51–0.52. These are trade-offs, not clinical approvals.

Lowest pooled Brier is a provisional probability-calibration ranking ONLY, not automatic final-model selection. Lower Brier alone does not establish better calibration. Read discrimination, diagnostics, false positives/negatives and threshold trade-offs together.
1. XGBoost / Full / Raw (0.157477); 2. Logistic / Full / Sigmoid (0.157956); 3. Logistic / Full / Raw (0.158030); 4. XGBoost / Full / Sigmoid (0.158184); 5. XGBoost / Awareness-ablated / Raw (0.174524); 6. XGBoost / Awareness-ablated / Sigmoid (0.174741); 7. Logistic / Awareness-ablated / Sigmoid (0.175082); 8. Logistic / Awareness-ablated / Raw (0.175221)
All workflows are reported. Earlier candidate shortlisting and choosing among these development results introduce selection optimism; nested calibration/tuning boundaries do not erase earlier selection. Bootstrap intervals do not fix that optimism. No clinically approved cutoff, final model, calibrated personal-risk claim or deployment threshold.
Remaining work: owner review of all trade-offs; separately approved final development preparation/freeze; diagnostic intervals and survey sensitivity; SHAP/what-if and independent vision work. Final held-out evaluation remains reserved until all choices are frozen and separately authorised.
Runtime: Python 3.13.5; pandas 3.0.6; numpy 2.5.3; scikit-learn 1.9.1; XGBoost 3.4.1 verified before fitting. No installations, datasets/models written, commits or pushes.

## Verification record — 2026-10-13

- New focused tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_calibration_threshold_nhanes.py` — final run 11 passed, 0 failed. The first instrumentation run had one assertion expecting Series labels; sklearn supplies NumPy labels internally. Corrected the assertion to compare values against the recorded participant IDs, without changing the protocol.
- Existing regression tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_xgboost_comparison_nhanes.py tests/test_logistic_comparison_nhanes.py tests/test_baseline_nhanes.py tests/test_preprocess_nhanes.py` — 34 passed, 0 failed.
- Combined final verification: 45 passed, 0 failed. Tests record all 80 synthetic nested base fits, confirm train-only preprocessing, identical outer/pool/tuning/inner memberships, the same fitted raw/calibrated base object, calibration independence from tuning labels, deterministic cutoffs, coverage, reproducibility, metrics, diagnostic clipping/separation and prediction-only paired bootstrap.
- Historical/current source, tests, reports, plans, manifest and original untracked files preserved with before/after hashes. Previous diary/AI-log text retained; new entries appended only. No model or deployment threshold selected.
