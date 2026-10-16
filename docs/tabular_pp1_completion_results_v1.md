# Questionnaire PP1 development completion — 2026-10-15

Development-only prototype: probability of self-reported previous gum treatment. Not current disease, diagnosis, future risk or a treatment-effect estimate. NHANES US definitions; use fictional profiles for demonstrations.

Prospective recipe: `tabular_pp1_completion_plan_v1.md`. Historical files and frozen manifest unchanged.
6,251 development participants (1,553 Yes); original five folds; 30 CV fits plus one reference demonstration fit. No held-out payloads decoded/evaluated. All ten XGBoost A reference metrics reproduced to six decimals/counts exactly.

| Configuration | AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity @0.50 | Specificity @0.50 | TN | FP | FN | TP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_reference | 0.739398 | 0.515988 | 0.516263 | 0.157268 | 0.264005 | 0.944444 | 4437 | 261 | 1143 | 410 |
| A_short | 0.735895 | 0.510715 | 0.510707 | 0.158318 | 0.236317 | 0.954662 | 4485 | 213 | 1186 | 367 |
| A_long | 0.738298 | 0.514803 | 0.515074 | 0.157502 | 0.283967 | 0.938272 | 4408 | 290 | 1112 | 441 |
| A_long_regularized | 0.739455 | 0.513796 | 0.514072 | 0.157464 | 0.282035 | 0.939336 | 4413 | 285 | 1115 | 438 |
| A_long_child5 | 0.737902 | 0.513260 | 0.513527 | 0.157733 | 0.289762 | 0.938910 | 4411 | 287 | 1103 | 450 |
| A_balanced | 0.740041 | 0.515812 | 0.516088 | 0.201243 | 0.569221 | 0.779906 | 3664 | 1034 | 669 | 884 |

Numerical AUROC leader: A_balanced; difference versus A = 0.000643. This is development selection, not a final winner or independent superiority finding.
No final threshold selected; 0.50 is the existing comparison only. AUROC 0.80 is not achieved.

## Paired prediction-only 95% intervals

| Configuration | AUROC delta interval | Brier delta interval |
| --- | --- | --- |
| A_short | [-0.005947176286055181, -0.0010646116211171428] | [0.0005570423738788209, 0.001554452708578024] |
| A_long | [-0.0033947276409493606, 0.0012725647800697361] | [-0.00024560261600268044, 0.000679527696157639] |
| A_long_regularized | [-0.002070338188326387, 0.0020747824079898275] | [-0.0002461042462232256, 0.0006234988160631878] |
| A_long_child5 | [-0.004416750822437626, 0.0016186502483418344] | [-8.878828138906072e-05, 0.0010213887738596125] |
| A_balanced | [-0.0005246406452635771, 0.0018747428383303177] | [0.04165582196372215, 0.04593875978662971] |
1,000 fixed-seed outcome-stratified draws. Positive AUROC / negative Brier differences favour a candidate. Conditional intervals omit model refitting, search selection, multiplicity and complex survey uncertainty; no national-population or clinical claims.

## Working explanation and What-if

TreeSHAP computed on all 6,251 unseen-fold rows for reference A, 47 encoded columns grouped to 12 inputs. All raw-margin, probability and native-contribution checks pass 1e-5; raw log-odds units are explicit. No calibrated-percentage or causal attribution claim.
| Input | Mean absolute grouped log-odds contribution |
| --- | --- |
| OHQ860 | 0.42408555392906 |
| OHQ835 | 0.2661752917816041 |
| OHQ030 | 0.2286986208402822 |
| OHQ870 | 0.17240319516181216 |
| OHQ845 | 0.142674183056207 |
| RIDAGEYR | 0.06924253953142448 |
| DMDEDUC2 | 0.06830766460674621 |
| DIQ010 | 0.04477793081881667 |
| INDFMPIR | 0.040009608860501776 |
| DMDMARTZ | 0.03718801469726756 |
| SMOKING_STATUS | 0.027050681708780167 |
| RIAGENDR | 0.0024710452544994647 |

Fictional example probability: 0.21408096; hypothetical former smoking/7 cleaning days: 0.25849256. This is model response, not an expected health improvement or evidence that past treatment can change.
Reset and saved-model reload reproduce the original exactly. Only the existing reference A powers the demo. Age/history/outcome remain protected; unsupported lifetime-smoking changes are rejected; development category/pair support warnings are disclosed.
The reference is raw, not separately calibrated; the existing calibration study showed no automatic XGBoost Brier improvement. Calibration diagnostics/reliability bins are in the aggregate JSON, not applied as a new probability mapping.

Local model: `models/questionnaire_pp1_v1/model.joblib`, SHA256 `c3f7458d1f6681fb4db18aa9d064a9d69baa75b16e634daa262210cbd91a9213`. Local OOF rows: `data/tabular_pp1_v1/development_oof.npz`. Both ignored; no data/model commit.
## Remaining scientific completion

Final model/calibration/threshold freeze, untouched held-out evaluation, complex-survey variance/domain analysis, subgroup checks and user comprehension/usability measurement remain pending. A subsequent saved-OOF survey-weight point sensitivity analysis is recorded in `tabular_survey_sensitivity_v1.md`; it does not supply design-based uncertainty. Working functions do not establish validated personal probability or Sri Lankan transportability. Original research proposal remains unchanged.

Final software verification (2026-10-16): 76 focused/directly affected regression tests passed, zero failures/skips; 15 browser checks passed. The local demonstration and exact launch command are documented in `component2_pp1_working_demo_v1.md`. This is not a full repository test run.

Runtime: {"python": "3.13.5", "numpy": "2.5.3", "pandas": "3.0.6", "sklearn": "1.9.1", "xgboost": "3.4.1", "shap": "0.52.0"}
