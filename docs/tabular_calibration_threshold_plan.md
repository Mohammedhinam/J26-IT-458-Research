# Proposed development-only calibration and threshold validation — 2026-10-13

Status: **PLAN ONLY — awaiting explicit owner approval. No implementation, data loading, model fits or experiments performed.**

## Meaning and proposal authority

Calibration asks whether predicted probabilities agree with observed Yes frequencies. Threshold selection converts a probability into a Yes/No decision and controls the sensitivity/specificity trade-off. A well-calibrated probability does not itself specify a useful operating threshold. The endpoint remains self-reported previous gum treatment, not current disease risk or diagnosis.

The supplied signed proposal sections 3.3–3.5 require development-only five-fold validation, model/baseline comparisons, both predefined feature sets, discrimination/probability/operating metrics and final choices fixed before untouched test evaluation. It proposes considering sigmoid calibration, using development out-of-fold predictions for calibration/threshold decisions, reporting calibration slope/intercept and reliability plots, and uncertainty/survey sensitivity. It does **not** prescribe the candidate shortlist, inner split proportions/fold count, threshold objective/grid, diagnostic details or candidate tie-breaks below. These are implementation/research choices for owner approval.

## Candidate shortlist — proposed, not final models

| Candidate | Existing setting | Historical AUROC / AP / Brier | Justification |
|---|---|---|---|
| Logistic Full | C=1, class_weight=None | 0.736721 / 0.513089 / 0.157823 | Preserve the original fixed, reproduced statistical baseline; C=0.1/no weights has only a small numerical Brier difference (0.157787) |
| Logistic Awareness-ablated | C=1, class_weight=None | 0.662407 / 0.377588 / 0.175290 | Same fixed setting; retain proposal-required feature sensitivity comparison |
| XGBoost Full | Approved profile A | 0.739398 / 0.516263 / 0.157268 | Highest observed AUROC/AP and lowest Brier among the four full XGBoost profiles; improvement is numerical, not demonstrated superiority |
| XGBoost Awareness-ablated | Approved profile A | 0.670896 / 0.386262 / 0.174243 | Same profile; strongest measured ablated XGBoost ranking/Brier |

Keep all existing preprocessing, Logistic settings and approved XGBoost A settings unchanged. A has depth=2, learning_rate=0.05, estimators=200, reg_lambda=1, with the approved fixed binary:logistic/CPU settings. Do not rerun the twelve Logistic/eight XGBoost configuration searches. Compare each of these four candidates with and without sigmoid calibration: **eight probability workflows**.

Balanced Logistic is not included in this bounded stage: the historical AP-leading full C=0.1/balanced model has Brier 0.202614 versus 0.186718 for the prior Dummy, and more false positives at 0.50. This does not prove it cannot benefit from calibration; excluding it is a scope choice requiring approval, not a final rejection. Changing thresholds on unweighted models is investigated separately from class weighting.

## Proposed leakage-safe evaluation recipe

Reuse the frozen 6,251 development participants in their saved order and exactly the existing five outer stratified folds (seed 42). The 1,563 final-test participants remain reserved. Verify manifest and outer-fold fingerprints against historical reports before any future fit.

For each outer fold, all four candidates share the following partitions and process:

1. Keep the outer validation rows sealed for scoring only. Stratify the remaining outer-training rows into **80% model/calibration pool and 20% threshold-tuning pool**, using seed 42. Freeze these inner memberships for all candidates; do not change the original development/test manifest.
2. Inside the model/calibration pool, use **3-fold StratifiedKFold(shuffle=True, random_state=42)**. Fit a fresh preprocessing + base classifier Pipeline on each inner training fold and produce inner OOF scores on its inner validation fold. This prevents imputation, scaling, encoding and XGBoost's base score from learning the scored inner rows.
3. Fit one sigmoid calibrator on those inner OOF scores/labels, then refit one fresh base Pipeline on the entire model/calibration pool. Proposed implementation: sklearn `CalibratedClassifierCV(estimator=Pipeline(...), method='sigmoid', cv=inner_three_folds, ensemble=False, n_jobs=1)`. This documented mode uses inner OOF scores for calibration and one final base-estimator refit. Use the resulting same base estimator as the uncalibrated reference; do not fit another base model just for that reference.
4. Predict the independent threshold-tuning pool with both raw and sigmoid workflows. Choose separate thresholds using only this pool and the predefined rule below. Its labels were used by neither the base models nor the calibrator.
5. Only now predict the outer validation rows. Record raw/calibrated probabilities and classifications at fixed 0.50 and at the thresholds learned for this fold. Outer labels must never affect preprocessing, base fits, calibration, early stopping, thresholds or fallback settings.

The model/calibration pool is approximately 4,000 rows in each outer fold, with about 1,000 rows reserved for threshold tuning. These are arithmetic planning sizes, not new observed dataset counts. Final refits for this comparison use fewer rows than the historical 5,000/5,001-row outer training folds; therefore the new raw reference is the fair paired control, and exact reproduction of historical metrics is **not** expected. Historical results remain context/evidence, not a matched control for the new protocol.

Calibration scores come from smaller inner training sets before application to the refitted pool model, as in sklearn's documented ensemble=False recipe; check outer validation reliability rather than assuming successful calibration. No XGBoost eval_set, early stopping or retuning. Sigmoid uses decision_function when available (Logistic) or probability outputs otherwise (XGBoost), following the installed library. A fold-specific monotone mapping need not preserve the ranking of pooled predictions across different folds; report AUROC/AP again.

## Proposed operating-threshold rule

- Keep **0.50** as a fixed reference, not a selected final threshold.
- Search only **0.00, 0.01, ..., 1.00** (101 thresholds), separately for raw/sigmoid workflows on each fold's threshold-tuning pool. Positive means probability >= threshold.
- Primary criterion: maximise **Youden J = sensitivity + specificity - 1**. If tied, prefer higher sensitivity, then the larger threshold. This weights the two class-specific error rates equally; it does not establish clinical false-positive/false-negative costs and does not directly minimise overall errors in this imbalanced cohort.
- Report the achieved sensitivity/specificity and confusion counts rather than promising a required sensitivity. If maximum J is nonpositive, flag that no useful operating improvement was found; retain fixed 0.50 results as a reference rather than inventing a successful threshold.
- Store all five learned thresholds per workflow and their range/median as descriptive stability information. Evaluate each validation participant using the threshold learned without their fold. **Do not** average the five thresholds and evaluate that average on the same pooled OOF labels.

This stage validates a threshold-selection **procedure**, not one final deployment cutoff. No threshold is chosen during planning. Different cost-based/sensitivity-constrained objectives would require a separately approved, predeclared change before the future run; do not select an objective after looking at outcomes.

## Metrics and diagnostics after approval

For all eight raw/sigmoid workflows, pool one outer-OOF probability per development participant and report AUROC, trapezoidal PR-AUC, AP and Brier. Report sensitivity, specificity and TN/FP/FN/TP both at fixed 0.50 and using fold-learned thresholds. Include class/fold/inner-pool supports and exclusion-free coverage checks.

Report a reliability table/plot with **10 quantile bins**, including bin sizes, mean predicted probability and observed Yes fraction; show fewer bins explicitly if tied scores prevent ten distinct bins. Lower Brier alone does not prove better calibration because it also depends on discrimination.

Estimate diagnostic calibration slope/intercept by fitting an unpenalised logistic regression of the true outer-OOF label on logit(predicted probability), including an intercept. Proposed clipping for this diagnostic only: epsilon=1e-6; record the clipped count. Ideal joint intercept=0 and slope=1. This is a descriptive diagnostic fit, **not** a second calibrator and not a transformation of the predictions being scored. Its jointly estimated intercept differs from an intercept-only calibration-in-the-large estimate; do not confuse the terms or the sigmoid calibrator's parameters. Flag separation/nonconvergence/undefined estimates instead of silently adding a penalty.

Propose **1,000 paired participant bootstrap resamples, seed 42**, of the already-computed outer-OOF arrays for 95% intervals of AUROC/AP/PR-AUC/Brier and both sets of sensitivity/specificity, including paired calibrated-minus-raw differences. Use identical resampled participants for all workflows; do not refit models, recalibrators or thresholds in these resamples. Flag any one-class resamples as undefined. These conditional intervals omit training/selection variability, dependence from overlapping CV training sets and survey design; they are not nationally representative uncertainty. Slope/intercept are point diagnostics in this bounded stage; intervals for those diagnostics and survey-weighted analysis remain explicitly pending proposal work.

For a matched training-rate reference, compute each outer fold's positive proportion from its model/calibration pool and assign it to that outer validation fold. This is equivalent to a prior Dummy, needs no additional model fit and uses no validation labels. Preserve the historical Dummy report; do not present its old aggregate score as a paired prediction array.

## Selection optimism and final-test protection

Proposed provisional ranking: lowest pooled outer-OOF Brier; exact ties prefer uncalibrated, then Logistic, then fewer-input ablation. Report all eight workflows and every operating trade-off; do not hide worse calibration or discrimination. This rule and shortlist need owner approval before implementation.

Even with independent tuning/scoring inside each outer fold, selecting among eight workflows on the pooled results remains optimistic. XGBoost A was also shortlisted using earlier results from these same development participants; nesting cannot undo that prior selection. These are exploratory development comparisons, not unbiased validation of the entire search history. Bootstrap intervals do not fix selection optimism. Do not automatically declare a final model or clinically suitable cutoff.

After reviewing this stage, obtain separate approval to freeze the candidate, preprocessing, calibration method, threshold-selection rule and numerical final threshold. A later final development-only preparation would use the **same 80/20 pool/tuning recipe**, with inner three-fold OOF calibration inside the pool, then choose the threshold on the independent tuning pool. Freeze the resulting base estimator/calibrator/threshold before accessing final-test payloads. Do not refit on the tuning rows or all development rows afterward without redesigning/revalidating the calibration recipe.

Only a separately authorised final evaluation may score the untouched 1,563 participants. Do not recalibrate, retune or replace the model based on those final-test results; report failures truthfully. The frozen hold-out remains independent of selection, but survey/population and external clinical validity limitations still apply.

## Proposed computational budget

| Planned operation | Count |
|---|---|
| Base-estimator fits: 4 candidates × 5 outer folds × (3 inner fits + 1 pool refit) | 80 (40 Logistic, 40 XGBoost) |
| Binary sigmoid calibrator fits: 4 candidates × 5 outer folds | 20 |
| Joint diagnostic slope/intercept fits: 4 candidates × 2 probability versions | 8 |
| Total estimator/calibrator/diagnostic fits for this stage | 108 |
| Threshold checks: 8 workflows × 5 folds × 101 grid points | 4,040 scoring checks, no model fits |
| Paired bootstrap | 1,000 prediction-only resamples, no refits |

Raw-reference predictions reuse each fitted base estimator; Dummy uses five prior calculations. Final development preparation, final-test evaluation and diagnostic-interval estimation are **not** included or authorised by this plan. No elapsed runtime is promised. Synthetic test fits, if later implemented, are separate from this experiment budget.

## Reuse and future verification requirements

Reuse the selective development loader, zero-decoding fix, input/ablation selectors, fresh Pipeline factories, model parameters and threshold-independent probability metrics. The existing scorer hardcodes threshold 0.50, so a later separate operating-metric helper must accept a threshold without changing historical baseline scoring. Preserve all existing code/reports and manifest; store only aggregate evidence under docs/. No source code is changed in this task.

Future focused tests must verify disjoint outer-validation/pool/tuning memberships, inner fold fit boundaries, unchanged outer fingerprints, exact candidate settings, no threshold-label influence on calibration, matched raw/calibrated base models, deterministic threshold ties, complete OOF coverage, diagnostic clipping/failure handling and preservation of historical work. Save future participant-level memberships/predictions only in ignored storage if needed; never in docs/.

## Approval checklist and current status

Owner approval is required for: the four-candidate shortlist and exclusion of balanced Logistic; outer-train 80/20 pool/tuning split; inner three-fold ensemble=False calibration; threshold grid/Youden objective/tie-breaks; diagnostic clipping/bins and point-only slope/intercept scope; bootstrap method/count; provisional Brier ranking/ties; and the fit budget. Approval of implementation would not itself authorise final held-out evaluation.

Written today: this plan and factual diary/AI-log entries only. No data payloads loaded, tests/model experiments run, package changes, commits or pushes. Stop here until explicitly approved.

Sources: supplied proposal sections 3.3–3.5, pages 20–23; relevant AGENTS.md rules; historical baseline/Logistic/XGBoost reports and approved plans. API behaviour: [sklearn CalibratedClassifierCV](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html) and [calibration guide](https://scikit-learn.org/stable/modules/calibration.html). These sources explain methodology; numeric choices above remain proposals for owner approval.
