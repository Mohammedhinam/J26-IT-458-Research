# Next tabular development experiment — 2026-10-12

Status: **Planned / Not started**. This is a proposed experiment specification for owner review, not a results report. Today's work is documentation only.

## Why this step

The first fixed logistic baseline (commit [5dccc4b](https://github.com/Mohammedhinam/J26-IT-458-Research/commit/5dccc4b222e455eb834a1ff46c371215c27a48d1)) achieved development OOF AUROC 0.736721 and Brier 0.157823. At the predefined 0.50 threshold, sensitivity was 29.30% and specificity 93.61%. These are measured internal results from October 10, not new measurements today. Further development comparisons should explore regularisation and class weighting without choosing settings from the final test set.

## Proposed bounded comparison

Reuse the existing selective development loader, original frozen membership/order and all 12 conceptual inputs. Keep the 1,563 held-out participants reserved. Do not decode their predictors or labels. Preserve the existing audit, preprocessing and first-baseline reports.

| Setting | Proposed values | Reason |
|---|---|---|
| L2 regularisation C | 0.1, 1.0, 10.0 | Compare stronger, existing and weaker regularisation |
| class_weight | None, balanced | Compare ordinary fitting with weights computed from each training fold |
| Solver / iteration limit | lbfgs / 1000 | Reuse the first baseline's settings; stop on convergence failure |
| Validation | StratifiedKFold, 5 folds, shuffle=True, seed 42 | Reuse identical folds for all six candidates |
| Threshold | 0.50 for this comparison | Keep the existing demonstration operating point fixed |

Build a new preprocessing + classifier Pipeline inside every training fold for every candidate. Fit medians, scaling and encoding only on that fold's training participants. Do not use the already-fitted development matrix. Keep SEQN and OHQ850 out of predictors. Keep the training-fold prior DummyClassifier as a reference on the same folds.

For a provisional development candidate, rank by pooled OOF average precision. If tied, prefer lower Brier score, then smaller C, then no class weights. Record all candidate results rather than only the winner. These settings are proposed before the next run; any revision must be dated before execution.

## Outputs and interpretation

Report actual AUROC, trapezoidal PR-AUC, average precision, Brier, sensitivity/specificity at 0.50 and confusion counts for every candidate. Record development class balance, fold supports, settings, runtime versions and frozen-manifest hash. Store participant-level OOF predictions only in ignored data/ if needed later; commit aggregate reports and code/tests only.

The best candidate's score is a **development selection score**, not an unbiased final performance estimate: choosing among candidates on the same OOF results introduces selection optimism. A higher sensitivity with balanced weights can come with lower specificity or less reliable probabilities. Do not describe a weighted model's output as calibrated without calibration checks.

## Verification checklist for the later implementation

- [ ] Load exactly the saved development IDs and verify the manifest remains unchanged.
- [ ] Use fresh fold Pipelines and identical fold membership for every candidate; each participant gets one OOF prediction per candidate.
- [ ] Test training-fold-only imputation and class weighting, probability validity, identifier/outcome exclusion and convergence failure handling.
- [ ] Run focused tests and save measured comparison results; preserve original reports and untracked files.
- [ ] Record any changed cohort, settings or blockers plainly; stop rather than silently change the frozen experiment.

## Separate later stages — also not started

1. Awareness-feature ablation: the proposal requires comparison without OHQ835/OHQ860. Specify and test that separately before implementing it; today's plan leaves the current predictor list intact.
2. Calibration: compare uncalibrated and sigmoid-calibrated candidates within development validation. A calibrator must be fitted without the labels of the participants on which its probabilities are scored, using an inner training-only split/CV. Fitting and evaluating a calibrator on the same OOF labels would give an optimistic result.
3. Threshold selection: choose and document a development-only operating objective before tuning thresholds. Current 0.50 remains a demonstration threshold, not a selected clinical threshold.
4. Final configuration: freeze features, regularisation, weighting, calibration and threshold before any final held-out evaluation. Survey-weighted sensitivity and uncertainty intervals remain pending analyses.

No experiment in this document has run. There are no new metrics, model artifacts, SHAP results or final-test results to report.

## Copy-paste for Planner

Title: Plan development-only logistic comparison

Bucket: Tabular. Documentation status: Completed (Oct 12). Experiment status: Not started.

Notes: Documented a proposed six-configuration L2/class-weight comparison using the existing frozen development membership and fresh preprocessing within identical five-fold validation. Defined outputs, provisional selection rule and leakage checks. Calibration, threshold selection and awareness-feature ablation are separate later stages. No training or new evaluation ran today.

Checklist: document candidate settings; define verification and outputs; distinguish planned experiments from measured results.

Evidence: docs/tabular_development_plan.md and the commit containing this file.

Source: supplied proposal pages 20–22, attached AGENTS.md sections 6.2–7, docs/tabular_preprocessing_rules.md and docs/tabular_baseline.md. Parameter meanings: [sklearn LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).
