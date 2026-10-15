# Proposed development-only XGBoost comparison — 2026-10-13

Status: **Awaiting owner approval. No implementation or experiment run.**

## Authority and approval boundary

The supplied Component 2 proposal, pages 21–22, supports a controlled comparison of tree depth, learning rate, number of estimators and regularisation, using five-fold stratified development validation. It does not specify exact numeric search ranges. The relevant AGENTS.md rules, existing development plan and comparison report also contain no approved XGBoost ranges. Therefore every numeric choice below is a proposal for approval, not a previously authorised research setting. The owner's current instruction requires stopping here before training code or experiments.

## Proposed four profiles

| Profile | max_depth | learning_rate | n_estimators | reg_lambda (L2) | Purpose |
|---|---|---|---|---|---|
| A | 2 | 0.05 | 200 | 1.0 | Shallow reference with conservative updates |
| B | 3 | 0.05 | 200 | 1.0 | Compare modestly deeper interactions with A |
| C | 3 | 0.10 | 100 | 1.0 | Compare faster updates/fewer trees with B |
| D | 3 | 0.05 | 200 | 5.0 | Compare stronger L2 regularisation with B |

These are four specified profiles, not a Cartesian grid. Profile C changes learning rate and tree count together; it cannot isolate either parameter's individual effect. The two schedules have the same learning_rate × n_estimators product, which does not imply equivalent models or performance. Values are chosen to keep this first comparison small, with shallow trees and at most 200 estimators; they are not claimed to be optimal.

Run each profile with full 12-input and awareness-ablated 10-input feature sets, excluding only OHQ835/OHQ860 for ablation. Proposed workload: **8 configurations × 5 folds = 40 XGBoost fits**. No additional grid expansion, early-stopping search, class-weight search or repeat seeds in this experiment.

## Fixed settings included in the approval request

Use installed XGBoost 3.4.1, CPU, with explicit settings:

| Parameter | Proposed fixed value |
|---|---|
| booster / objective | gbtree / binary:logistic |
| tree_method / device | hist / cpu |
| random_state / n_jobs | 42 / 1 |
| eval_metric | logloss |
| reg_alpha / gamma | 0.0 / 0.0 |
| min_child_weight / max_delta_step | 1.0 / 0.0 |
| subsample | 1.0 |
| colsample_bytree / colsample_bylevel / colsample_bynode | 1.0 / 1.0 / 1.0 |
| scale_pos_weight | 1.0 (unweighted first comparison) |
| grow_policy / max_bin | depthwise / 256 |
| base_score | None; installed-version automatic estimation from training-fold labels only |
| early_stopping_rounds | None; fixed tree counts, no validation eval_set |
| validate_parameters / verbosity | True / 1 |

Other parameters retain the installed version's defaults, which must be recorded in the eventual report. Fixed CPU/single-worker settings and full row/column sampling reduce sources of variation. No runtime duration is promised; only the fit/tree-count budget is bounded. Package metadata confirms installation; runtime/import/training readiness has not been tested in this planning stage.

## Reuse, leakage boundaries and verification after approval

1. Reuse the existing selective development loader, zero-decoding repair and saved development order. Require the frozen manifest hash to match existing evidence. Do not overwrite the manifest or read held-out record payloads.
2. Regenerate exactly the existing five folds once with StratifiedKFold(shuffle=True, random_state=42). Verify the ordered validation-ID membership hash against the Logistic report: `0822ca63d5ffa57375141ae15d97ca08333a207463eae909237892dbe9e3adb0`.
3. Reuse the fresh preprocessing factory and established ablation adapter. Replace only the classifier with a fresh XGBClassifier in each fold. Fit preprocessing and classifier on training rows only; use validation rows only to obtain OOF probabilities. No early stopping on scored validation folds.
4. Add focused synthetic tests for feature exclusion, identical folds, train-only preprocessing, one OOF prediction per participant, deterministic predictions and reuse of the existing metric function. Test that runtime failures stop reporting rather than silently changing settings.
5. Preserve original baseline/comparison code, reports and all existing tracked/untracked changes. Save a separate aggregate XGBoost comparison report; no participant predictions or model artifacts need to be written.

## Expected outputs — not available yet

For every configuration, report pooled OOF AUROC, trapezoidal PR-AUC, Average Precision, Brier, sensitivity/specificity at the existing 0.50 comparison threshold, and TN/FP/FN/TP. Keep outcome definitions, participants, folds and metric implementation identical to the Logistic experiment. No final threshold optimisation or calibration is part of this comparison.

Use the existing full and ablated C=1.0/no-weight Logistic rows as fixed primary references and the historical training-fold-prior Dummy row as the feature-independent reference. Preserve all twelve Logistic rows; show their existing development-selected highest-AP configuration only as clearly labelled secondary context, not a final winner. Reference results are reused, not regenerated or edited to improve a comparison.

Existing measured full-feature references: Logistic AUROC 0.736721 / Brier 0.157823; Dummy AUROC 0.499486 / Brier 0.186718. These are historical measurements, not XGBoost results. No expected XGBoost metric or guaranteed AUROC 0.80 is stated.

Report all eight XGBoost settings and their trade-offs. Choosing settings from the same OOF results introduces selection optimism; these are internal development results, not unbiased final-test estimates, calibrated personal probabilities or clinical validation. Do not automatically declare a final winning model.

## Pending proposal work

Owner approval of these exact profiles and fixed settings is the current blocker. After implementation/comparison, development-only calibration and threshold decisions, uncertainty and survey-weighted sensitivity analysis, SHAP/what-if and the independent vision branch remain pending. Final held-out evaluation must wait until all relevant choices are frozen.

Sources: supplied proposal pages 21–22; attached AGENTS.md sections 6.2, 7 and 13; docs/tabular_development_plan.md and docs/tabular_logistic_comparison.md. Parameter meanings: [official XGBoost parameters](https://xgboost.readthedocs.io/en/stable/parameter.html). Documentation explains parameter behaviour; it does not approve or prescribe this project's proposed numeric profiles.
