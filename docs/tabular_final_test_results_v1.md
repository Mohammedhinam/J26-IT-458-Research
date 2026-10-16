# Frozen questionnaire final held-out evaluation — v1

Completed 2026-10-16 after two separate explicit owner approvals: numerical freeze first, then one final Test evaluation. The authorization is consumed. No rerun, Test-driven model selection, recalibration or threshold tuning is authorized.

**Outcome: self-reported previous gum-disease treatment (OHQ850), not current disease, future progression or a clinical screening diagnosis.**

## Fixed design

6,251 development / 1,563 held-out participants; held-out Yes 388, No 1,175. Existing frozen membership, 12 inputs / 47 encoded features. Full XGBoost A raw primary, full Logistic C1 raw comparator; no additional calibration. Frozen statistical cutoffs 0.26 and 0.28 were selected using development OOF Youden J; baseline constant 1,553/6,251 = 0.24844024956007038 uses cutoff 0.50. Cutoffs are demonstrations, not clinically approved operating points.

## Actual probability metrics

| Model | AUROC (conditional 95% CI) | Trapezoidal PR-AUC | Average precision | Brier |
|---|---|---|---|---|
| XGBoost_A_raw | 0.760654 [0.733363, 0.788940] | 0.552356 | 0.555094 | 0.150858 |
| Logistic_C1_raw | 0.756113 [0.727886, 0.783610] | 0.553807 | 0.554765 | 0.151364 |
| Training_rate | 0.500000 [0.500000, 0.500000] | 0.624120 | 0.248241 | 0.186617 |

The constant-score baseline trapezoidal PR-AUC (0.624120) is an endpoint-interpolation artefact of the tied-score PR curve; it does not demonstrate ranking skill. Its AUROC is 0.5 and AP equals held-out prevalence (0.248241). Report both PR measures; do not rank a constant predictor as superior using this trapezoidal number.

## Operating trade-offs

| Model | Fixed cutoff | Sensitivity | Specificity | TN | FP | FN | TP |
|---|---|---|---|---|---|---|---|
| XGBoost_A_raw | 0.50 | 0.268041 | 0.954894 | 1122 | 53 | 284 | 104 |
| XGBoost_A_raw | 0.26 | 0.559278 | 0.835745 | 982 | 193 | 171 | 217 |
| Logistic_C1_raw | 0.50 | 0.296392 | 0.948936 | 1115 | 60 | 273 | 115 |
| Logistic_C1_raw | 0.28 | 0.541237 | 0.831489 | 977 | 198 | 178 | 210 |
| Training_rate | 0.50 | 0.000000 | 1.000000 | 1175 | 0 | 388 | 0 |

At XGBoost 0.26, 217/388 reported Yes responses are detected and 171 are missed; 193/1,175 reported No responses are flagged. Compared with 0.50, this detects 113 additional Yes responses and adds 140 false positives. These labels concern reported treatment history, not a clinical examination.

## Conditional uncertainty and paired comparisons

1,000 fixed-seed paired participant bootstrap draws; zero undefined draws and zero predictive refits. Intervals condition on already-fitted models and do not incorporate development selection/refitting uncertainty, complex NHANES survey design or external transportability. All absolute and paired intervals are in the accompanying aggregate JSON.

| Metric | XGBoost minus Logistic point difference | Paired 95% CI |
|---|---|---|
| AUROC | 0.004540 | [-0.005623, 0.013846] |
| Average precision | 0.000330 | [-0.011968, 0.015204] |
| Brier | -0.000505 | [-0.002098, 0.001298] |
| Sensitivity frozen | 0.018041 | [-0.008003, 0.044671] |
| Specificity frozen | 0.004255 | [-0.008369, 0.016416] |

These intervals include zero; the evidence does not establish a clear overall XGBoost advantage over Logistic. At reference 0.50, XGBoost sensitivity is lower; its paired difference interval excludes zero. The original primary/comparator choices remain unchanged. Overall AUROC 0.80 feasibility target was not achieved; an age subgroup above 0.80 must not be substituted for the overall result.

## Calibration diagnostics — not recalibration

| Model | Joint intercept | Joint slope | Status |
|---|---|---|---|
| XGBoost_A_raw | 0.247322 | 1.244086 | OK |
| Logistic_C1_raw | 0.121330 | 1.118797 | OK |
| Training_rate | undefined | undefined | undefined: one class or constant scores |

Intercept/slope are descriptive joint regressions on the fixed Test predictions; they did not change any prediction. Ideal joint intercept/slope are 0/1; point estimates alone do not prove calibration. Coefficient intervals were not estimated. Constant-score baseline coefficients are undefined and recorded as JSON null. Reliability groups (counts, positive counts, mean probability, observed fraction) are retained in the JSON; no bin-based recalibration.

## Predefined age / recorded-sex diagnostics

Subgroup operating metrics below use reference 0.50, not the frozen model-specific cutoffs. Age 80 represents 80+. These are descriptive conditional comparisons, not fairness certification or model-selection criteria. Full three-model subgroup results and conditional intervals are in JSON.

| Subgroup | n | Yes | XGBoost AUROC | Logistic AUROC | XGBoost Brier | Logistic Brier |
|---|---|---|---|---|---|---|
| age_30_44 | 446 | 80 | 0.723600 | 0.711612 | 0.132749 | 0.135059 |
| age_45_59 | 441 | 127 | 0.714279 | 0.717940 | 0.175044 | 0.173120 |
| age_60_80 | 676 | 181 | 0.801691 | 0.801138 | 0.147028 | 0.147928 |
| recorded_sex_1 | 789 | 193 | 0.763310 | 0.758163 | 0.150620 | 0.150894 |
| recorded_sex_2 | 774 | 195 | 0.757531 | 0.753483 | 0.151102 | 0.151843 |

## Execution and independent saved-evidence checks

- 109 independent saved-evidence assertions passed; zero failures. Exact membership/confusions and independently recomputed sklearn probability metrics agree within 1e-7 (maximum difference 1.13518471567e-08; float32/float64 arithmetic). No new inference, model fits or bootstrap reruns during verification.
- Previously qualified 16 focused synthetic tests passed, zero failed/errors/skipped; unchanged tests/code were reused, not rerun or counted as new tests.
- One actual evaluation: 12.556 seconds; peak RSS 228.70 MiB, two-thread cap. Not a performance benchmark.
- Runtime instrumentation observed zero predictive/preprocessing fits, two descriptive calibration regressions, four selective XPT returns of exactly 1,563 authorized held-out IDs each. Source hashes, frozen models, thresholds, manifest and historical evidence unchanged.
- Private per-participant predictions and approvals: `data/tabular_final_test_results_v1_20261016T153805043162Z/` and `data/tabular_final_test_execution_v1_20261016T153805043162Z/`. They remain ignored and are not copied into docs.
- Frozen receipt SHA-256: `e08073b43e89ba99982483344e2612f577f46ae8ee0988b2458e5cfc2b8c6e0c`.
- Actual results SHA-256: `abcc52076b7073767f4f13907e9682f5da683bc9fc31fef5000351c4e13b391c`.
- Private predictions SHA-256: `bea8b43941366012e5886e314b075dd643376353089a08751b72d700530e3f8a`.
- Persistent canonical claim retained unchanged; never remove it to rerun. See verification JSON for code/execution/hash bindings. No clinical/institutional approval invented.

## Limits and next step

Final held-out evaluation for this frozen workflow is complete, not the entire research project. Full inputs include treatment-awareness-associated fields; cross-sectional self-reports, US-specific socioeconomic context, survey design and external-population applicability remain limitations. Descriptive uncertainty does not establish clinical reliability or causality. Do not use these Test results to choose new hyperparameters, thresholds, feature sets or calibration.

Next: rehearse the existing questionnaire prediction → SHAP → constrained What-if demonstration using these frozen results and limitations. Historical UI/model metadata remain untouched; any later presentation update must preserve provenance and avoid treating statistical cutoffs as clinical guidance. Vision qualified-label/group approvals and missing whole-image MGI 0 remain separate blockers. No new training, Test rerun, deployment, commit or push.

## Three lines to understand (Tamil)

1. `authorize(...)` + `claim_once(...)`: இரண்டு owner approvals மற்றும் ஒருமுறை மட்டுமே run ஆகும் பாதுகாப்பு; Test-ஐப் பார்த்துப் பின்னால் model மாற்றுவதைத் தடுக்கிறது.
2. `predict_frozen(...)`: ஏற்கனவே development-ல் fit செய்த model-ஐ மட்டுமே பயன்படுத்துகிறது; Test-ல் புதிய training இல்லை.
3. `p >= frozen_cutoff`: probability-ஐ முன்பே முடிவு செய்த statistical cutoff-உடன் ஒப்பிடுகிறது; cutoff குறைந்தால் அதிக Yes கிடைக்கலாம், false positives-மும் அதிகரிக்கலாம்.

Viva: Why freeze before Test? Answer: Test முடிவைப் பார்த்து settings மாற்றினால் அது சுதந்திரமான மதிப்பீடாக இருக்காது. அதனால்தான் model/cutoff-ஐ முன்பே freeze செய்தோம்.
