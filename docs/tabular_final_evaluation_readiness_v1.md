# Frozen Tabular evaluator — readiness only

2026-10-16 · `vinuthan` · **READY FOR APPROVAL; REAL TEST NOT RUN**

Owner instructed continuing after development preparation. This step implements and qualifies the evaluator, without interpreting “continue” as final held-out permission. No new numerical freeze approval or Test authorization was recorded.

Prepared receipt remains unchanged, SHA-256:
`e08073b43e89ba99982483344e2612f577f46ae8ee0988b2458e5cfc2b8c6e0c`.
See [actual development preparation](tabular_freeze_preparation_results_v1.md).

## Two explicit decisions still needed

1. **Numerical freeze:** approve Full XGBoost A raw primary/cutoff.26, Full Logistic C1 raw comparator/cutoff.28, constant development-rate baseline.24844024956007038, no added calibration, exact prepared artifacts/protocol. Scope `approve_tabular_numerical_freeze_v1` bound to the receipt above.
2. **Final evaluation:** separately authorize one evaluation of those fixed choices on the1,563 held-out participants. Scope `evaluate_frozen_tabular_1563_once_v1`, binding the actual numerical approval record, receipt, evaluator/subgroup source hashes and fresh ignored output path. No predictive fitting, cutoff tuning, Test-driven model/calibration changes or feedback retries.

The two approvals may be supplied as two explicit decisions; preparation approval alone does not satisfy either Test gate. Provenance documents real human authorization, not cryptographic identity or clinical approval. No permission record is fabricated by this readiness task.

## Implemented safeguards

`src/tabular/evaluate_frozen_tabular.py` has no automatic execution on import and no self-starting CLI. The guarded `run` requires both scopes and explicit opt-in before model/data access. The held-out loader rejects direct calls without its internal capability; normal execution grants it only after authorization and an exclusive claim.

Before Test decoding it verifies receipt/model/OOF/protocol/source hashes, class mapping0/1, exact12feature order/47encoded features, model parameters bound by the preparation receipt and unchanged runtime versions. Only locally generated hash-verified joblib artifacts may be loaded.

A fixed claim at `data/tabular_final_test_once_v1/evaluation_claim.json` is created exclusively **before** Test loading. A fresh output path cannot evade that claim. Any failure retains it; no automatic retry, deletion or overwrite. It is currently absent. A failure would require diagnosis and a new explicitly scoped decision rather than pretending evaluation succeeded.

The existing audited XPT selector is reused with the held-out allowlist only after those gates. Expected1563unique records must survive the existing fixed cleaning rules unchanged. No silent exclusions, imputation of labels, resplit, preprocessing fit or changed predictor list. Original source files/manifest stay read-only.

## Registered evaluation outputs

- Frozen XGBoost/Logistic probabilities plus the fixed development-rate baseline on the same records; positive ifp≥.26/.28 respectively. Baseline uses.50 only as a reference, without a tuned cutoff.
- AUROC, trapezoidal PR-AUC, AP, Brier, sensitivity/specificity and confusion at.50 and the frozen operating cutoffs. Thresholds are statistical treatment-history demonstration cutoffs, not clinical cutoffs. Constant-predictor trapezoidal PR-AUC needs AP alongside it, as documented in the original baseline.
- Joint calibration intercept/slope and reliability tables. Diagnostic regressions describe fixed predictions; they do not modify probabilities, train a predictive model or authorize recalibration on Test. Constant/separated/nonconvergent coefficients remain explicit JSONnull with a reason. Coefficient intervals are not implemented, and that limitation is reported.
- 1,000seed42 paired participant bootstrap draws shared across models for eight discrimination/probability/operating metrics and XGBoost-minus-comparator differences; undefined one-class draws counted. No resample refits or retuning. These are conditional sample intervals, not complex-survey uncertainty.
- Existing predefined age30–44/45–59/60–80 and released-sex1/2 subgroup functions, with supports, AUROC/Brier intervals and small-group flags. Empty/undefined outcomes retain explicit status rather than being hidden.
- Private predictions/SEQN/labels stored only in ignored local output. Public reporting is aggregate. No UI/model substitution or cloud deployment.

Complex-survey variance/appropriate domain inference and clinical/Sri Lankan transportability remain unresolved; the existing development-weighted point sensitivity is preserved. This evaluator does not claim national estimates or complete scientific validation. Optional later survey analysis must not select or tune models using Test results.

## Actual qualification in this task

**16 generated tests passed,0failed/errors/skipped**. They cover both authorization scopes, stale code/output/receipt/freeze bindings, direct-loader rejection, exclusive once-only claims, generated end-to-end scoring without predictive fitting, fixed cutoff/confusion/Brier correctness, paired bootstrap determinism/zero identical-model differences, undefined diagnostic JSON and no second decode on a second output path.

An initial end-to-end fixture reused the numeric fixture's age0–99; it correctly failed the existing age30–80 subgroup guard. The generated fixture was corrected to eligible ages and valid sex codes. Production bounds/assertions were not relaxed. Another generated check exposed that the existing diagnostic helper represents undefined coefficients asNaN; the evaluator converts those to JSONnull while preserving the explicit reason, leaving historical helper behavior unchanged.

Actual frozen-artifact compatibility was additionally checked using **one existing fictional profile**, not a participant: XGBoost.21408095955848694, Logistic.19675996209720317, baseline.24844024956007038. Both artifact hashes remained unchanged; zero predictive fits, no held-out loader, no real claim or authorization record. These values are software checks, not model performance or personal clinical estimates.

[Source/test/hash verification](tabular_final_evaluation_verification_v1.json). No Test payload/header access, real Test inference, install/download, training, commit or push in this readiness task. No full repository suite or new clinical result claimed.

## Viva explanation

- Authorization precedes data: knowing a file path is not permission to use final evaluation answers.
- `predict_proba` reuses frozen preprocessing/model state. No `fit` or threshold selection occurs in predictive evaluation.
- The once-only claim prevents repeated scoring after seeing an unfavorable result. Final outcomes must be reported honestly, even ifAUROC.80 is not reached.

Next action: owner reviews the exact numerical freeze and separately decides whether to authorize the one final evaluation. No real evaluation starts from this report alone.
