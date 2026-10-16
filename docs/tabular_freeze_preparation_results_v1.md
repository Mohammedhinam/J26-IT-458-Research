# Tabular development freeze preparation — actual results

2026-10-16 · branch `vinuthan` · **PREPARED — PENDING OWNER NUMERICAL FREEZE REVIEW**

Owner approved the concrete six-Logistic-fit preparation in [decision package v1](tabular_finalisation_decision_package_v1.md). It completed once. This is not final Test authorization, clinical approval or a deployed-model change. The original proposal, labels, splits, historical reports and working demo remain unchanged.

## Candidate set prepared

- Primary: Full-input, unweighted **XGBoost A raw**, existing saved development model and OOF reused. No additional sigmoid mapping; **zero new XGBoost fits**.
- Comparator: Full-input **Logistic C=1 raw**, same preprocessing, seed42 and five original folds. Exactly five OOF fits and one full-development fit. All ten historical metrics/counts reproduced to six decimals/counts exactly before the sixth fit.
- Baseline: constant development treatment-history rate **1553/6251 = .24844024956007038**; no estimator fit needed. OOF reference priors use fitting-fold labels only.
- Identical 6,251 development participants,1,553 Yes/4,698 No,12 conceptual inputs/47 encoded features. OHQ850 and SEQN are not predictors. The final 1,563 participants were not decoded/transformed/evaluated.

## Actual proposed numerical cutoffs

The existing Youden J rule was applied to each model's own development OOF scores: grid0.00–1.00 in.01 steps, ties higher sensitivity then larger threshold, positive if probability≥threshold. These are **statistical treatment-history demonstration cutoffs, not clinical cutoffs**.

| Model | Proposed cutoff | AUROC | Trapezoidal PR-AUC | AP | Brier | Sensitivity at proposed cutoff | Specificity at proposed cutoff |
|---|---:|---:|---:|---:|---:|---:|---:|
| XGBoost A raw | **.26** | .739398 | .515988 | .516263 | .157268 | **.545396** | **.806301** |
| Logistic C1 raw | **.28** | .736721 | .512827 | .513089 | .157823 | **.535093** | **.822052** |

**The same OOF labels selected these cutoffs.** The operating metrics below are apparent development results, not independent cutoff validation. Earlier configuration/feature/model selection adds optimism. No performance claim about the sealed Test set or a Sri Lankan/clinical population is made. Choosing a threshold does not improve AUROC or change the model's probabilities.

| Model / operating point | TN | FP | FN | TP | Sensitivity | Specificity |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost @.50 reference |4437|261|1143|410|.264005|.944444|
| XGBoost @.26 selected |3788|910|706|847|.545396|.806301|
| Logistic @.50 reference |4398|300|1098|455|.292981|.936143|
| Logistic @.28 selected |3862|836|722|831|.535093|.822052|

XGBoost gains437 true positives but adds649 false positives compared with.50 in this same saved OOF comparison. Logistic gains376 true positives and adds536 false positives. No clinical error-cost preference has been established. We did not use the old median fold threshold.25 or recalibrate/retrain XGBoost.

## Frozen artifacts and integrity

Prepared local directory:
`data/tabular_final_freeze_v1_20261016T143007292661Z/`

- `freeze_receipt.json`: candidate/comparator settings, exact feature order and outcome mapping, preprocessing/code/manifest/fold bindings, runtime, cutoffs, baseline, artifact hashes and final-evaluation protocol.
- `logistic_model.joblib`: new full-development comparator; saved/reloaded probabilities matched exactly on three development rows. This is an integrity check, not a training-performance estimate.
- `development_oof.npz`: aligned SEQN/labels/folds and XGBoost/Logistic/prior probabilities; ignored and local only.
- `training_rate.json` and `protocol.json`: fixed baseline and truthful owner preparation authorization/bindings. No Test authorization record.

Receipt SHA-256:
`e08073b43e89ba99982483344e2612f577f46ae8ee0988b2458e5cfc2b8c6e0c`

Primary artifact stays at `models/questionnaire_pp1_v1/model.joblib`, SHA-256 `c3f7458d1f6681fb4db18aa9d064a9d69baa75b16e634daa262210cbd91a9213`. It remains the existing `QuestionnairePrototype`; the predictor is its `.model` attribute. Its old `final_model=False` provenance and current UI were preserved. The external receipt records the proposed freeze without rewriting historical model metadata.

Original split SHA-256 `4d0f82149cb20485186ad929fca0a070a72fe4e4a3032b1cf8da37954c131551`; five-fold membership SHA-256 `0822ca63d5ffa57375141ae15d97ca08333a207463eae909237892dbe9e3adb0`.

## Actual verification

**13 focused tests passed,0failed/errors/skipped**, including the existing selective-XPT/zero-decoding regression. Generated tests cover six-fit isolation, mismatch stopping before the sixth fit, saved reload, exact threshold tie rules, no-useful-J rejection, reference tampering/membership errors, fresh scope/hash rejection and inability to grant Test access. These are selected software tests, not a repository-wide run.

**63 independent saved-artifact assertions passed**, with zero verification refits. Independent metric calculations, all101 cutoff candidates, chosen confusion matrices, exact OOF membership, fitting-only medians/scaler means, reference preservation, six observed fits/convergence, baseline construction and file/code hashes agreed.

Selective development loading returned6,251 development rows from each of P_DEMO/P_OHQ/P_SMQ/P_DIQ, and every returned SEQN was in the frozen development membership. As in the verified existing loader, shared XPT headers/linkage bytes are scanned, but held-out predictor/outcome records are not decoded. Runtime file guards allowed only the four XPT sources, manifest, saved development OOF and existing primary model; all other dataset/model paths were rejected. Source writes were forbidden.

Local execution0.273s,peakRSS210.03MiB,two CPU threads; this is an execution record, not a controlled speed/latency benchmark. Private authorization/access/fit/verification records:
`data/tabular_final_preparation_execution_v1_20261016T143007292661Z/`.

[Aggregate receipt and results](tabular_freeze_preparation_results_v1.json), [current source/test verification](tabular_freeze_verification_v1.json). No new datasets, installs, cloud activity, commits or pushes. No Test evaluation, demo substitution or final clinical-model claim.

## Owner review and next step

Review the exact raw-model choices, proposed cutoffs .26/.28, probability-error evidence and false-positive/false-negative trade-offs. If accepted, record numerical freeze approval against the exact receipt hash. **The next Test operation still requires separate explicit authorization after that freeze.** This preparation scope is consumed; do not rerun or tune further automatically.

After separate final-evaluation authorization, compare the frozen XGBoost, Logistic and baseline on the same protected1,563 participants once, with fixed0.50 and frozen statistical cutoffs, the registered metrics and paired uncertainty. Do not choose models, calibrators or cutoffs using those results. Calibration diagnostic intervals, complex-survey inference, transportability and consented usability limitations remain; .80 AUROC has not been demonstrated.

## Three lines to understand for viva

1. `fit_configuration(... BASELINE_CONFIGURATION)` fits preprocessing/classifier inside each original training fold. OOF participants do not fit their own transformer or model; the reproduction gate precedes the full-development comparator fit.
2. `checked_reference(...)` verifies SHA-256 and exact SEQN/label order before reusing XGBoost probabilities. This makes the comparison paired without another XGBoost experiment.
3. `select_threshold(y, probability)` applies the already approved J/grid/tie rule to development OOF only. It is tuning, so its same-data operating performance is explicitly labelled apparent; Test remains reserved.

Viva: **Why is the .26 sensitivity not final validated sensitivity?** Those same development answers helped choose.26. Only a later untouched evaluation with the cutoff already frozen can assess its held-out performance; it still would not establish clinical validity or transfer to another population.
