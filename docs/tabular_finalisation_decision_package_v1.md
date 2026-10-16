# Questionnaire finalisation decision package — v1

2026-10-16 · branch `vinuthan` · **PROPOSED / PENDING OWNER APPROVAL**

This package reviews existing evidence. It does not select a new numerical threshold, activate a final model, refit models or authorize Test access. Outcome: **self-reported previous gum-disease treatment (OHQ850)**, not current disease, progression or treatment benefit. Use fictional profiles with NHANES US definitions.

## Recommended decision

| Decision | Proposed choice | Evidence and qualification |
|---|---|---|
| Primary candidate | Full-input, unweighted XGBoost profile A | Competitive discrimination/probability error; existing verified TreeSHAP/What-if implementation. Small advantage over Logistic is not established superiority. |
| Required comparator | Full-input Logistic, C=1, class_weight=None | Preserved regularised benchmark; avoid discarding a simpler, closely performing model. |
| Minimum baseline | Training-rate predictor | Training/development labels only; freeze the prevalence before Test access. |
| Additional probability mapping | None for primary or comparator | Sigmoid did not improve XGBoost Brier; Logistic sigmoid's small Brier improvement has an interval spanning zero. Raw outputs remain model estimates, not validated individual probabilities. |
| Feature set | Existing full12 inputs /47 encoded features | Keep awareness ablation as sensitivity evidence. Do not silently drop OHQ835/OHQ860 or hide dependence on them. |
| Threshold procedure | Existing Youden J rule on each model's development OOF predictions | Grid0.00–1.00 step0.01; exact ties higher sensitivity, then larger threshold. Positive if p≥t. Statistical treatment-history demonstration only, not a clinical cutoff. |
| Numerical threshold now | **Not selected** | Fold median0.25 is not a validated single threshold. No new tuning in this task. |
| Fixed0.50 | Retain as a reference operating point | Low sensitivity must be reported; do not call it the final screening cutoff. |

XGBoost A: depth2, learning_rate.05,200trees,reg_lambda1; `binary:logistic`, unweighted, seed42, CPU hist; all other approved settings unchanged in `xgboost_comparison_nhanes.py`. Logistic uses the existing fold-local preprocessing and L2/lbfgs C=1 configuration. No new features, search, oversampling or scope change.

## Existing matched development evidence

6,251 participants:1,553 Yes /4,698 No. Original five folds, one prediction per participant. These **full outer-training** comparisons differ from the smaller-pool calibration study below.

| Setting | AUROC | Trapezoidal PR-AUC | AP | Brier | Sensitivity @.50 | Specificity @.50 |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Full C1 raw | .736721 | .512827 | .513089 | .157823 | .292981 | .936143 |
| XGBoost Full A raw | .739398 | .515988 | .516263 | .157268 | .264005 | .944444 |
| XGBoost A balanced | .740041 | .515812 | .516088 | .201243 | .569221 | .779906 |

Balanced A increases recall but worsens Brier by about.044; its AUROC change versus A has conditional95% interval[-.000525,.001875]. Do not choose it merely for the highest AUROC. No measured AUROC.80. Logistic C.1 raw has Brier.157787, close to C1; the existing C1 calibration shortlist/reference is retained rather than reopening an unbounded search.

Sources: [12 Logistic settings](tabular_logistic_comparison.md), [8 XGBoost settings](tabular_xgboost_comparison.md), [6 later bounded XGBoost settings](tabular_pp1_completion_results_v1.md). All historical results preserved.

## Calibration evidence — all eight workflows

The calibration study used a separate matched recipe: each outer-training fold's80% model/calibration pool and20% tuning pool; three inner folds for sigmoid. Raw and sigmoid shared the same fitted base model. Hence these estimates must not be substituted for the full-training numbers above.

| Workflow | AUROC | Brier | Joint intercept | Slope | Sensitivity @.50 | Specificity @.50 |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Full Raw | .736631 | .158030 | -.057952 | .937395 | .289762 | .937633 |
| Logistic Full Sigmoid | .736676 | .157956 | .008003 | 1.005948 | .269800 | .943806 |
| Logistic Ablated Raw | .662327 | .175221 | -.102966 | .896493 | .047006 | .987229 |
| Logistic Ablated Sigmoid | .662399 | .175082 | .010005 | 1.011005 | .025113 | .993614 |
| XGBoost Full Raw | .738936 | .157477 | .048135 | 1.046072 | .264649 | .945934 |
| XGBoost Full Sigmoid | .738792 | .158184 | .028747 | 1.023902 | .275596 | .941039 |
| XGBoost Ablated Raw | .668366 | .174524 | .038691 | 1.040288 | .027688 | .992976 |
| XGBoost Ablated Sigmoid | .667924 | .174741 | .056251 | 1.052809 | .049581 | .984887 |

XGBoost Full sigmoid-minus-raw Brier=.000708, conditional95% interval[.000296,.001120]: worse probability error in this matched study. Logistic Full change=-.000074, interval[-.000303,.000140]: no clear benefit. Lowest Brier is one criterion, not automatic final-model selection. Joint intercept/slope point estimates do not prove clinical calibration; coefficient intervals remain pending. They are diagnostics, not an applied correction.

Ablation lowers discrimination to around.66–.67, indicating awareness-feature dependence, not causality. SHAP also gives the awareness fields large contributions. The intended proxy endpoint and limitations must remain prominent.

## Operating-point trade-off already measured

These are **fold-specific demonstration thresholds**, each selected using its independent tuning pool. They are not one final cutoff.

| Full workflow | Sensitivity learned | Specificity learned | TN | FP | FN | TP | Fold thresholds |
|---|---:|---:|---:|---:|---:|---:|---|
| Logistic Raw | .554411 | .793316 |3727|971|692|861|.22/.31/.28/.28/.28|
| Logistic Sigmoid | .555055 | .789911 |3711|987|691|862|.22/.31/.28/.28/.28|
| XGBoost Raw | .589182 | .751171 |3529|1169|638|915|.24/.33/.25/.21/.25|
| XGBoost Sigmoid | .594334 | .735419 |3455|1243|630|923|.21/.30/.22/.19/.23|

For XGBoost Raw, lowering to fold-learned cutoffs changes TP411→915 and FP254→1169 relative to.50 in the same calibration study. It trades missed treatment-history reports for many more false positives. No clinical false-negative/false-positive cost has been established. Source and all ablated outcomes: [original calibration report](tabular_calibration_threshold_results.md).

## Exact next preparation, only after approval

1. Pin current code, manifest, model, OOF, feature schema and runtime hashes in a new versioned local receipt. Keep6,251/1,563 split and original five folds. Do not deserialize or transform held-out payloads.
2. Reuse the already saved full-development XGBoost A model and6,251OOF predictions after verifying provenance/hash/membership. **Zero new XGBoost fits.** Do not replace it with one of the smaller calibration-pool estimators.
3. Historical Logistic code/reports explicitly retained predictions in memory only; there is no saved Logistic model in the current `models/` inventory. Prepare only its missing artifacts: **five fixed-fold C1 raw Logistic fits plus one full-development fit = six fits**. First reproduce all ten historical reference metrics to six decimals/counts exactly; stop on mismatch, leakage or convergence failure. No12-setting rerun. Persist OOF/model only in ignored local storage.
4. Compute one proposed cutoff per model from its own development OOF scores using the frozen J/grid/tie rule. Report no-useful-J cases rather than silently falling back. This cutoff selection is development tuning: apparent OOF performance after selection is optimistic and must be labelled descriptive. Do not borrow the median fold cutoff. Threshold transport from CV-trained to full-development models remains uncertain until protected evaluation.
5. Save immutable candidate/comparator/baseline hashes, numerical cutoffs, class mapping, preprocessing, estimator settings, calibration choice, protocol/metric/bootstrap definitions and limitations. No source-manifest mutation or automatic UI/model substitution. Keep the current demo working.
6. Present the freeze receipt for explicit owner review. **No final Test evaluation in this preparation scope.** Approval of this document is not Test permission.

This is a necessary artifact-completion step, not repeat hyperparameter research. If an already verified Logistic artifact is later located through relevant provenance, reuse it instead of refitting; stop if its provenance conflicts. No such artifact was found in the current narrow model inventory.

## Final evaluation protocol to approve separately

After the final freeze and separate Test authorization: evaluate the frozen XGBoost, Logistic and training-rate baseline on exactly the same1,563held-out participants once. No refitting/recalibration/threshold changes from Test outcomes. Report AUROC, trapezoidal PR-AUC, AP, Brier, calibration slope/intercept and reliability tables; sensitivity/specificity/confusion at each frozen statistical cutoff and at.50. Use paired seed42participant bootstrap intervals (1,000draws) with undefined-case accounting; clearly conditional sample uncertainty, not national-population uncertainty. No Test-feedback loop to improve the reported final result.

Record survey-weight sensitivity usingWTINTPRP and appropriate domain/design analysis withSDMVSTRA/SDMVPSU if population inference is intended. Existing point sensitivity and respondent bootstrap do not establish national estimates. Existing age/recorded-sex summaries are exploratory; final subgroup supports/intervals remain necessary, with small-group warnings. Verify the software handles undefined/constant/separation cases honestly. No claim that medical or Sri Lankan transportability is established.

## Proposal alignment and approval checklist

Signed proposal §§3.3–3.5(pp.20–23) explicitly require the matched model/baseline comparison, development-only preprocessing/calibration/threshold decisions, final method freeze before Test, uncertainty/survey sensitivity, correct SHAP units and constrained What-if. It considers sigmoid; it does not require activating sigmoid when evidence is worse. It does **not** specify Youden J, this final C1/raw recipe, six-artifact-recovery fits or a numerical clinical cutoff: those are owner-reviewed implementation choices.

- [ ] Approve Full XGBoost A raw as primary candidate, Full Logistic C1 raw as comparator, training-rate baseline; not a clinical winner.
- [ ] Approve no additional sigmoid mapping, retaining all calibration/ablation evidence and caveats.
- [ ] Approve the exact **six-Logistic-fit /zero-XGBoost-fit** development preparation and reproducibility stops.
- [ ] Approve OOF Youden J/grid/tie procedure for **statistical treatment-history demonstration**, with later numerical freeze review.
- [ ] Keep1,563Test payloads closed until a separate final-evaluation authorization.

All decisions remain **PROPOSED/PENDING**. No owner approval signature or permission record has been fabricated.

## What is already working; what remains

TreeSHAP log-odds additivity passed on all6,251OOF rows,47encoded features grouped to12inputs. What-if changes only smoking/cleaning, validates support and resets exactly. API/UI and fictional examples already work; no need to rewrite them. Historical tests/browser results are reused, not rerun or counted as new. New work in this task is documentation plus **51 report consistency assertions,3/3 artifact hashes and8/8 core source hashes matched**; no pytest run because no functional code changed.

Remaining after preparation: owner numerical freeze, separately authorized protected evaluation, coefficient/uncertainty and survey-design limitations, and ethical/consented usability work before participant involvement. The feasibilityAUROC.80 target remains unmet; no model/threshold choice can be claimed to fix it without measurement.

Viva: **Why not automatically calibrate?** Calibration is another learned mapping. In our matched development study it worsened XGBoost Brier, so we retain raw estimates with diagnostics rather than assuming an extra step helps. **Why not use cutoff.25?** It is only the median of fold-specific demonstration cutoffs; final cutoff must follow the approved development rule and be frozen before Test.

Evidence/hashes: [machine-readable review receipt](tabular_finalisation_decision_evidence_v1.json). No new fit, threshold selection, dataset/manifest/history change, Test payload access, install, commit or push.
