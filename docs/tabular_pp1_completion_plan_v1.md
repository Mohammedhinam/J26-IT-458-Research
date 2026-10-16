# Development-only PP1 completion recipe — 2026-10-15

Written before execution. Owner requested autonomous progress on both branches, a bounded attempt to improve questionnaire discrimination, and completion of SHAP/What-if. This is an engineering/development experiment, not selection of the final research model or permission to evaluate held-out participants. Original proposal §§3.3–3.5 and explanation/scenario validation p.23 apply. No predictors, outcome definitions or frozen memberships change.

## Bounded discrimination comparison

Keep the existing full 12 inputs, preprocessing, five StratifiedKFold folds/seed 42 and XGBoost A fixed settings. Retain CPU/single-worker operation. Six configurations, 30 fits maximum:

| ID | Depth | Learning rate | Trees | L2 lambda | Minimum child weight | Positive weight |
| --- | --- | --- | --- | --- | --- | --- |
| A_reference | 2 | 0.05 | 200 | 1 | 1 | 1 |
| A_short | 2 | 0.05 | 100 | 1 | 1 | 1 |
| A_long | 2 | 0.05 | 400 | 1 | 1 | 1 |
| A_long_regularized | 2 | 0.05 | 400 | 5 | 1 | 1 |
| A_long_child5 | 2 | 0.05 | 400 | 1 | 5 | 1 |
| A_balanced | 2 | 0.05 | 200 | 1 | 1 | Training-fold No / Yes |

Rationale: test under/over-fitting through tree count around the existing shallow reference, then two conservative regularization controls and proposal-supported class weighting. These are new prospectively recorded engineering choices under the owner's current request, not claimed to have appeared in the signed proposal. No search expansion, seed search, early stopping on scored folds, new features or oversampling. Earlier depth-3/Logistic/ablation/calibration comparisons are reused as history rather than rerun.

Run A first and require all ten historical full-A metrics to reproduce to six decimals/counts exactly. Each configuration fits a fresh preprocessing/model pipeline inside each training fold. Pooled metrics: AUROC, trapezoidal PR-AUC, AP, Brier, sensitivity/specificity and confusion counts at the unchanged reference 0.50. Any numerical AUROC-leading configuration is an exploratory candidate only. Report 1,000 fixed-seed paired, outcome-stratified prediction-only bootstrap intervals for AUROC/Brier differences against A. These condition on the saved OOF predictions and do not account for training, tuning, complex survey design or repeated model selection.

## Explanation and What-if engineering

Use the existing approved **Full XGBoost A** as an explicit development reference, regardless of this new comparison's results. This avoids silently promoting a development winner. Fit five fold models for the reference comparison and use their validation rows for cross-fitted aggregate TreeSHAP checks. Then fit one development-only reference on all 6,251 participants for predefined fictional profile demonstrations; its outputs are not validation metrics. Total recipe: 31 XGBoost fits, plus existing diagnostic computations. No calibrated individual-probability claim; raw SHAP explains raw log-odds, not a calibrated percentage.

Use `TreeExplainer(model_output='raw', feature_perturbation='tree_path_dependent')`; sum encoded contributions into the original 12 input groups, including numeric missingness. Check raw-margin reconstruction and sigmoid probability reconstruction (absolute tolerance 1e-5), and compare to XGBoost native exact contributions (1e-5). A failed explanation stops output; do not substitute an empty chart. Grouped sums are additive encoded-feature attributions, not a newly estimated conditional group-Shapley game or causal effects.

Accept exactly the 12 existing input fields using published NHANES codes and explicit unknowns. Age 30–80 (80=80+); poverty ratio 0–5 including zero; cleaning integer 0–7. Keep outcome, identifiers, raw smoking fields and survey fields out of prediction requests. For What-if only smoking status and cleaning days can change. The fewer-than-100 lifetime history cannot be rewritten into former/current smoking; unknown lifetime history cannot be invented. Former/current changes are illustrative re-inference only. Reset returns the untouched original profile. No monotonic-benefit assumption.

Support warnings use development-fitted marginal/category support and the exact smoking/cleaning pair count. Count <20 is a conservative **UI warning heuristic**, not statistical/clinical validation; disclose the count and threshold. This checks only these marginals/pair, not full-profile similarity, transportability or participant independence. Missing inputs are separately flagged. Prototype usability uses fictional predefined profiles because NHANES education/income definitions are US-specific.

## Evidence and completion boundary

Preserve historical reports/source files and all existing dirty work. Save OOF rows and the reference model only in fresh ignored local paths, with source/manifest/hash provenance; publish aggregate results and fictional examples only. Add focused synthetic tests and a local demonstration interface if existing dependencies permit. No held-out predictor/label access, final threshold/model freeze, clinical approvals, external messages, installs, commits or pushes.

Vision: preserve the three completed exploratory pilots and 181 holds. Reuse saved Validation evidence for a bounded uncertainty/readiness report and demonstration of existing outputs. Email is deferred at the owner's request. No automatic label recovery, Test access or new real-image experiment is implied. Qualified labels/participant independence and unsupported whole-image MGI 0 cannot be repaired by an internet search.

## Primary references checked

- [SHAP TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html): output units, training-path background and additivity.
- [XGBoost prediction API](https://xgboost.readthedocs.io/en/stable/python/python_api.html): native exact contribution/margin cross-check.
- [XGBoost parameters](https://xgboost.readthedocs.io/en/stable/parameter.html): tree count, regularization and positive weighting controls; numerical ranges above are project choices.
- [scikit-learn nested validation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html): selecting and scoring on the same development results is optimistic.
- [CDC oral health](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm) and [smoking](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm): endpoint, codes and skip logic.
