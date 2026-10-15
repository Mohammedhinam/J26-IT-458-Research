# Approved development-only XGBoost comparison — 2026-10-13

Command: `.venv/bin/python -B -m src.tabular.xgboost_comparison_nhanes`.
Owner approved profiles A–D, both feature sets and the plan's fixed settings before implementation. The original proposal-plan file is preserved; its pending status describes the pre-approval stage.
Outcome: self-reported previous gum treatment, OHQ850 Yes=1 / No=0; binary:logistic produces probabilities. No diagnosis or current-disease-risk claim.

## Approved settings and validation

| Profile | max_depth | learning_rate | n_estimators | reg_lambda |
| --- | --- | --- | --- | --- |
| A | 2 | 0.05 | 200 | 1.0 |
| B | 3 | 0.05 | 200 | 1.0 |
| C | 3 | 0.1 | 100 | 1.0 |
| D | 3 | 0.05 | 200 | 5.0 |

Participants: 6251 development; Yes=1553 (24.844025%); No=4698. Full/ablated inputs exclude only OHQ835/OHQ860 for ablation. Five-fold StratifiedKFold(shuffle=True, random_state=42), original saved order; 8 configurations × 5 folds = 40 XGBoost fits.
Frozen manifest SHA-256: `4d0f82149cb20485186ad929fca0a070a72fe4e4a3032b1cf8da37954c131551`. Ordered validation-fold membership SHA-256: `0822ca63d5ffa57375141ae15d97ca08333a207463eae909237892dbe9e3adb0` — MATCH to Logistic evidence before training.
Every fit reused fresh existing preprocessing/ablation steps with a fresh XGBClassifier. Medians/scaling/encoding and automatic base score learned from training rows only. No validation eval_set, early stopping, class-weight search, resplitting or pre-fitted development matrix. Errors/warnings stop reporting instead of silently changing approved settings.
Reused selective XPT loading/zero repair; no held-out predictor/label payload loaded, decoded, transformed or evaluated. Historical reports and manifest remain unchanged. OOF predictions/models stay in memory; no datasets or model artifacts are written.
All metrics use the existing scorer and pooled OOF predictions, one per participant/configuration. Threshold=0.50 for comparison only; PR-AUC is trapezoidal, Average Precision is separately defined. No final threshold selection or calibration.

Shared explicit settings:

```json
{
  "base_score": null,
  "booster": "gbtree",
  "colsample_bylevel": 1.0,
  "colsample_bynode": 1.0,
  "colsample_bytree": 1.0,
  "device": "cpu",
  "early_stopping_rounds": null,
  "eval_metric": "logloss",
  "gamma": 0.0,
  "grow_policy": "depthwise",
  "max_bin": 256,
  "max_delta_step": 0.0,
  "min_child_weight": 1.0,
  "n_jobs": 1,
  "objective": "binary:logistic",
  "random_state": 42,
  "reg_alpha": 0.0,
  "scale_pos_weight": 1.0,
  "subsample": 1.0,
  "tree_method": "hist",
  "validate_parameters": true,
  "verbosity": 1
}
```

Other installed classifier defaults (null delegates to XGBoost defaults; NaN denotes the missing-value marker):

```text
{
  "callbacks": null,
  "enable_categorical": true,
  "feature_types": null,
  "feature_weights": null,
  "importance_type": null,
  "interaction_constraints": null,
  "max_cat_threshold": null,
  "max_cat_to_onehot": null,
  "max_leaves": null,
  "missing": NaN,
  "monotone_constraints": null,
  "multi_strategy": null,
  "num_parallel_tree": null,
  "sampling_method": null
}
```

## Actual XGBoost OOF results — all eight configurations

| Features | Profile | Inputs | Encoded | AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity @0.50 | Specificity @0.50 | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full | A | 12 | 47 | 0.739398 | 0.515988 | 0.516263 | 0.157268 | 0.264005 | 0.944444 | 4437 | 261 | 1143 | 410 |
| Full | B | 12 | 47 | 0.736583 | 0.513028 | 0.513351 | 0.157976 | 0.292337 | 0.938910 | 4411 | 287 | 1099 | 454 |
| Full | C | 12 | 47 | 0.735676 | 0.512463 | 0.512789 | 0.158075 | 0.294269 | 0.940613 | 4419 | 279 | 1096 | 457 |
| Full | D | 12 | 47 | 0.737189 | 0.512184 | 0.512610 | 0.157760 | 0.287830 | 0.939549 | 4414 | 284 | 1106 | 447 |
| Awareness-ablated | A | 10 | 41 | 0.670896 | 0.385532 | 0.386262 | 0.174243 | 0.016742 | 0.995104 | 4675 | 23 | 1527 | 26 |
| Awareness-ablated | B | 10 | 41 | 0.667360 | 0.379967 | 0.380457 | 0.174764 | 0.049581 | 0.983184 | 4619 | 79 | 1476 | 77 |
| Awareness-ablated | C | 10 | 41 | 0.668049 | 0.379396 | 0.379959 | 0.174699 | 0.056021 | 0.982759 | 4617 | 81 | 1466 | 87 |
| Awareness-ablated | D | 10 | 41 | 0.668929 | 0.382963 | 0.383521 | 0.174432 | 0.048938 | 0.985100 | 4628 | 70 | 1477 | 76 |

## Preserved Logistic and Dummy references

Historical rounded OOF measurements reused below, not retrained. Both primary Logistic rows are C=1/None; all twelve original Logistic results remain in docs/tabular_logistic_comparison.md. The secondary AP-leading row is development-selected, not a final model. Dummy uses training-fold priors and is feature-independent.
| Reference | AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity @0.50 | Specificity @0.50 | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic Full C=1/None (primary) | 0.736721 | 0.512827 | 0.513089 | 0.157823 | 0.292981 | 0.936143 | 4398 | 300 | 1098 | 455 |
| Logistic Ablated C=1/None (primary) | 0.662407 | 0.376866 | 0.377588 | 0.175290 | 0.044430 | 0.987229 | 4638 | 60 | 1484 | 69 |
| Prior Dummy (feature-independent) | 0.499486 | 0.398258 | 0.248216 | 0.186718 | 0.000000 | 1.000000 | 4698 | 0 | 1553 | 0 |
| Logistic Full C=0.1/balanced (secondary development-selected AP leader) | 0.736599 | 0.513405 | 0.513672 | 0.202614 | 0.592402 | 0.756918 | 3556 | 1142 | 633 | 920 |

## Identical fold class balance

| Fold | Training N | Training Yes | Validation N | Validation Yes |
| --- | --- | --- | --- | --- |
| 1 | 5000 | 1242 | 1251 | 311 |
| 2 | 5001 | 1243 | 1250 | 310 |
| 3 | 5001 | 1243 | 1250 | 310 |
| 4 | 5001 | 1242 | 1250 | 311 |
| 5 | 5001 | 1242 | 1250 | 311 |

## Limitations and remaining work

Full-feature A has numerically higher AUROC/AP and lower Brier than the fixed full-feature C=1/None Logistic reference (0.739398/0.516263/0.157268 versus 0.736721/0.513089/0.157823), but lower sensitivity at 0.50 (0.264005 versus 0.292981). No paired uncertainty/significance analysis was performed, so this small numerical difference is not evidence of a reliable superiority. Ablated A also ranks higher than its fixed Logistic reference, with much lower sensitivity at 0.50; all trade-offs are shown rather than choosing a final winner.

All eight settings are reported. Choosing between these settings or between XGBoost and the development-selected Logistic configurations using the same OOF results introduces selection optimism. These are internal point estimates, not unbiased final-test estimates or evidence of clinical validity. No final winning model is declared.
Probability calibration is unverified: Brier measures probability error, but calibration slope/intercept and reliability curves are not evaluated here. No calibrated personal-probability claim. Awareness ablation is a dependence comparison, not causal evidence; profile C jointly changes learning rate/tree count and cannot isolate either effect.
Measured development configurations with AUROC >=0.80: none. This is a provisional feasibility target, not clinical validation or a final-test result.
Remaining proposal work: development-only calibration/operating-point decisions, uncertainty and survey-weighted sensitivity analysis, SHAP/what-if and independent vision work. Keep final held-out evaluation reserved until configurations/calibration/threshold are frozen.
Runtime: Python 3.13.5; pandas 3.0.6; numpy 2.5.3; scikit-learn 1.9.1; XGBoost 3.4.1.
Sources: owner-approved docs/tabular_xgboost_plan.md; supplied Component 2 proposal pages 21–22; historical baseline/Logistic reports. No installation, commit or push.

## Verification record — 2026-10-13

- New focused tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_xgboost_comparison_nhanes.py` — 9 passed, 0 failed.
- Existing regression tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_logistic_comparison_nhanes.py tests/test_baseline_nhanes.py tests/test_preprocess_nhanes.py` — 25 passed, 0 failed.
- Total verification: 34 passed, 0 failed. Tests cover approved-plan conflicts, exact model settings, feature schemas, identical folds, training-only imputation/scaling/base score, deterministic predictions, awareness exclusion, metric correctness and stopping on runtime failure.
- Manifest and fold-membership hashes matched historical evidence before actual training. Historical code, tests, reports, the approved plan and pre-existing untracked work were preserved; existing diary/AI-log text retained with new records appended only.
