# Development-only logistic comparison — 2026-10-13

Command: `.venv/bin/python -B -m src.tabular.logistic_comparison_nhanes`.
Outcome: self-reported previous gum treatment (OHQ850 Yes=1 / No=0). Internal development comparison only.

## Configuration and preservation

Development participants: 6251; Yes: 1553 (24.844025%); No: 4698.
Twelve L2 settings: C=0.1/1/10 × class_weight=None/balanced × full/awareness-ablated inputs. Ablation excludes only OHQ835 and OHQ860; cohort and outcome are identical.
Fresh baseline preprocessing + LogisticRegression inside each fold; lbfgs, max_iter=1000, random_state=42. Balanced weights are calculated by sklearn from training-fold labels only. No pre-fitted matrix, oversampling or calibration.
The existing five stratified folds are regenerated once using the same saved participant order, shuffle=True and seed=42, then reused for every configuration. Every participant has one OOF probability per configuration. Metrics pool OOF predictions using the unchanged baseline scoring function; threshold=0.50, positive if probability >= threshold.
Frozen split SHA-256: `4d0f82149cb20485186ad929fca0a070a72fe4e4a3032b1cf8da37954c131551`. Ordered validation-fold SEQN membership SHA-256: `0822ca63d5ffa57375141ae15d97ca08333a207463eae909237892dbe9e3adb0`.
Reused selective XPT loading and source-byte-verified zero repair. No held-out predictor/label payload is loaded or evaluated; only linkage SEQN bytes are scanned to select development records. No manifest, historical code/report, dataset or model is written. Participant predictions remain in memory only.

## Actual pooled OOF results

| Features | C | Class weight | Inputs | Encoded | AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity @0.50 | Specificity @0.50 | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full | 0.1 | None | 12 | 47 | 0.736270 | 0.513226 | 0.513490 | 0.157787 | 0.280103 | 0.941464 | 4423 | 275 | 1118 | 435 |
| Full | 0.1 | balanced | 12 | 47 | 0.736599 | 0.513405 | 0.513672 | 0.202614 | 0.592402 | 0.756918 | 3556 | 1142 | 633 | 920 |
| Full | 1.0 | None | 12 | 47 | 0.736721 | 0.512827 | 0.513089 | 0.157823 | 0.292981 | 0.936143 | 4398 | 300 | 1098 | 455 |
| Full | 1.0 | balanced | 12 | 47 | 0.736674 | 0.513142 | 0.513404 | 0.202745 | 0.594977 | 0.754789 | 3546 | 1152 | 629 | 924 |
| Full | 10.0 | None | 12 | 47 | 0.735910 | 0.512391 | 0.512650 | 0.157967 | 0.294913 | 0.935504 | 4395 | 303 | 1095 | 458 |
| Full | 10.0 | balanced | 12 | 47 | 0.735871 | 0.513123 | 0.513378 | 0.203029 | 0.593690 | 0.753938 | 3542 | 1156 | 631 | 922 |
| Awareness-ablated | 0.1 | None | 10 | 41 | 0.662062 | 0.377032 | 0.377751 | 0.175282 | 0.025757 | 0.992976 | 4665 | 33 | 1513 | 40 |
| Awareness-ablated | 0.1 | balanced | 10 | 41 | 0.662265 | 0.375951 | 0.376680 | 0.229724 | 0.665808 | 0.573436 | 2694 | 2004 | 519 | 1034 |
| Awareness-ablated | 1.0 | None | 10 | 41 | 0.662407 | 0.376866 | 0.377588 | 0.175290 | 0.044430 | 0.987229 | 4638 | 60 | 1484 | 69 |
| Awareness-ablated | 1.0 | balanced | 10 | 41 | 0.662200 | 0.375736 | 0.376466 | 0.229990 | 0.671603 | 0.568540 | 2671 | 2027 | 510 | 1043 |
| Awareness-ablated | 10.0 | None | 10 | 41 | 0.661804 | 0.376903 | 0.377616 | 0.175398 | 0.047006 | 0.986803 | 4636 | 62 | 1480 | 73 |
| Awareness-ablated | 10.0 | balanced | 10 | 41 | 0.661434 | 0.375951 | 0.376677 | 0.230380 | 0.672247 | 0.568114 | 2669 | 2029 | 509 | 1044 |

PR-AUC is trapezoidal precision-recall area; Average precision uses its separate step-weighted definition. Sensitivity/specificity and confusion counts use the fixed comparison threshold 0.50.

## Baseline reproduction gate

Full inputs, C=1.0, class_weight=None ran first. All ten historical results MATCH at six decimals (counts exactly); only then were the other eleven configurations run.
| Metric | Historical | Reproduced | Result |
| --- | --- | --- | --- |
| AUROC | 0.736721 | 0.736721 | MATCH |
| PR-AUC (trapezoidal) | 0.512827 | 0.512827 | MATCH |
| Average precision | 0.513089 | 0.513089 | MATCH |
| Brier | 0.157823 | 0.157823 | MATCH |
| Sensitivity @0.50 | 0.292981 | 0.292981 | MATCH |
| Specificity @0.50 | 0.936143 | 0.936143 | MATCH |
| TN | 4398 | 4398 | MATCH |
| FP | 300 | 300 | MATCH |
| FN | 1098 | 1098 | MATCH |
| TP | 455 | 455 | MATCH |

## Identical fold class balance

| Fold | Training N | Training Yes | Validation N | Validation Yes |
| --- | --- | --- | --- | --- |
| 1 | 5000 | 1242 | 1251 | 311 |
| 2 | 5001 | 1243 | 1250 | 310 |
| 3 | 5001 | 1243 | 1250 | 310 |
| 4 | 5001 | 1242 | 1250 | 311 |
| 5 | 5001 | 1242 | 1250 | 311 |

## Interpretation and future work

Full-feature AUROC spans 0.735871–0.736721; awareness-ablated AUROC spans 0.661434–0.662407. This decrease shows dependence on the awareness inputs within this experiment, not a causal or diagnostic finding. Balanced weights increase sensitivity at 0.50 while reducing specificity and worsening Brier scores. For example, the highest-AP setting has Brier 0.202614 versus 0.157787 for full C=0.1 without weights; AP alone does not establish reliable probabilities.

Highest pooled OOF Average Precision candidate: Full, C=0.1, class_weight=balanced. This is a development candidate, not the final model. The documented selection rule uses AP, then Brier, smaller C and no weights; an exact remaining feature-set tie prefers Full for deterministic ordering.
Selecting among twelve configurations on the same development OOF results introduces selection optimism. These point estimates are not unbiased final-performance estimates or evidence of clinical validity. Awareness ablation is a model-dependence comparison, not a causal analysis. Balanced-weight outputs are not claimed to be calibrated.
Threshold 0.50 remains comparison-only; no final threshold was selected or optimised. Uncertainty intervals, calibration slope/intercept and survey-weighted sensitivity are not evaluated here.
Next according to the proposal: predefine and implement the controlled development-only XGBoost comparison against Logistic Regression and the training-rate baseline on the same folds and both feature sets. Calibration and threshold selection must remain development-only, with final held-out evaluation deferred until choices are frozen.
Runtime: Python 3.13.5; pandas 3.0.6; numpy 2.5.3; scikit-learn 1.9.1.
Sources: comparison plan 8aa77fd; explicit 12-configuration task; supplied Component 2 proposal pages 20–22. Historical report: docs/tabular_baseline.md. Test/owner-review records: docs/diary.md and docs/ai_log.md.

## Verification record — 2026-10-13

- New focused tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_logistic_comparison_nhanes.py` — 8 passed, 0 failed.
- Existing regression tests: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_baseline_nhanes.py tests/test_preprocess_nhanes.py` — 17 passed, 0 failed.
- Combined verification: 25 passed, 0 failed. Synthetic tests cover identical folds for all settings, actual ablation, training-only medians/scaling, reproducibility, exact baseline probabilities/metrics and stopping on reproduction failure. The actual-data runner independently verified all ten historical baseline results.
- Before/after SHA-256 checks matched for historical audit/preprocessing/baseline code and evidence, the original comparison plan, frozen split manifest and all three pre-existing untracked files. No commit or push was performed.
