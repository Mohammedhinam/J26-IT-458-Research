# First development-only NHANES baseline — 2026-10-10

Command: `.venv/bin/python -m src.tabular.baseline_nhanes`.
Outcome: self-reported previous gum treatment, OHQ850 Yes=1 / No=0. These are internal validation results, not diagnosis or current disease risk.

## Fixed experiment design

Frozen development membership reused in its saved order. Only SEQN bytes are scanned across source files; only development record payloads are decoded. No held-out labels/predictors are loaded, transformed or evaluated. Original audit/preprocessing reports and split manifest are unchanged.
Development N=6251; Yes=1553 (24.844025%); No=4698 (75.155975%). Inputs=12; encoded column counts across fitted folds=[47].
Frozen split manifest SHA-256: `4d0f82149cb20485186ad929fca0a070a72fe4e4a3032b1cf8da37954c131551`.
5-fold StratifiedKFold(shuffle=True, random_state=42); identical folds for both models. Each participant has one out-of-fold probability; metrics pool those probabilities rather than averaging fold metrics.
Every model/fold has a fresh Pipeline: existing numeric median/scaling/missing flags and categorical unknown/one-hot preprocessing, then classifier. No pre-fitted matrix is used.
DummyClassifier(strategy='prior') uses its training-fold positive proportion. LogisticRegression uses fixed L2, C=1.0, lbfgs, max_iter=1000, class_weight=None, random_state=42. No tuning, oversampling or post-hoc calibration; class weighting and regularisation search remain future development experiments.
Threshold fixed before execution at 0.50; positive if probability >= threshold. It is a demonstration operating point, not a clinical or selected final threshold.
PR-AUC below is trapezoidal area under the precision-recall curve. Average precision is also reported because its step-weighted definition differs from trapezoidal area. Brier is mean squared probability error; lower is better.

## Actual pooled out-of-fold results

| Model | AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity @0.50 | Specificity @0.50 | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Training-rate dummy | 0.499486 | 0.398258 | 0.248216 | 0.186718 | 0.000000 | 1.000000 | 4698 | 0 | 1553 | 0 |
| L2 logistic regression | 0.736721 | 0.512827 | 0.513089 | 0.157823 | 0.292981 | 0.936143 | 4398 | 300 | 1098 | 455 |

## Fold class balance

| Fold | Training N | Training Yes | Validation N | Validation Yes | Encoded columns |
| --- | --- | --- | --- | --- | --- |
| 1 | 5000 | 1242 | 1251 | 311 | 47 |
| 2 | 5001 | 1243 | 1250 | 310 | 47 |
| 3 | 5001 | 1243 | 1250 | 310 | 47 |
| 4 | 5001 | 1242 | 1250 | 311 | 47 |
| 5 | 5001 | 1242 | 1250 | 311 | 47 |

## Limits and next step

Fold prior probabilities differ slightly, so pooled dummy ranking metrics need not equal exactly 0.5/prevalence; PR trapezoidal interpolation can also exaggerate a constant predictor's area. Compare average precision alongside PR-AUC. No uncertainty intervals, calibration slope/intercept, survey weighting or awareness-feature ablation are claimed in this first experiment.
Next: review these development results, then predefine further development-only regularisation/class-weight/calibration and awareness-feature ablation comparisons. Keep final held-out evaluation deferred until all choices are fixed.
Runtime: Python 3.13.5; pandas 3.0.6; numpy 2.5.3; scikit-learn 1.9.1.
XPT selection uses pandas XPORT header metadata/private IBM decoder; unsupported layouts fail explicitly. Synthetic tests guard participant selection and the audited zero repair.
Metric definitions: [sklearn PR curve](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html), [average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).
