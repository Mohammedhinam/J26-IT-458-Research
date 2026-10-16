# Component 2 working PP1 demo — 2026-10-16

The questionnaire now runs locally from inputs to a previous-gum-treatment probability, checked TreeSHAP contributions and constrained What-if/reset. The separate Vision tab displays the three verified, previously saved v3 Grad-CAM examples. It does not accept new images or perform new Vision inference. This is a working research demonstration, not completed scientific validation.

## Open the demo

Open http://127.0.0.1:8765 while the local server is running. If it is stopped, run:

```sh
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m src.tabular.local_demo
```

Use the fictional example, click **Explain this profile**, inspect the contributions, compare an allowed smoking/cleaning scenario, then reset. The Vision tab shows saved originals, heatmaps and overlays for 00733, 00734 and 00766. No Colab, installation, upload or additional training is needed to demonstrate these existing functions. The server binds to localhost only; it is not a public deployment. Existing installed Python libraries are reused; FastAPI deployment remains separate work.

## Measured results

| Evidence | Actual result | Meaning / limitation |
| --- | --- | --- |
| New focused and directly affected regression suite | **76 passed, 0 failed, 0 skipped**, 5.93 seconds | 50 new tests and 26 existing regression tests; not a full repository run |
| Browser functional checks | **15 passed, 0 failed** | Inputs, SHAP, scenario/reset, guards, saved Vision views and mobile layout |
| Valid browser flow | 0 page errors, 0 console errors | Deliberately invalid scenario separately rejected |
| Local prediction + SHAP HTTP timing | Median **11.14 ms**, p95 **12.22 ms** | 30 requests after one warmup; fictional profile, arm64 Mac; not load/usability testing |
| Original XGBoost A reference | AUROC **0.739398**, Brier **0.157268** | All ten historical reference metrics reproduced to six decimals/counts |
| Numerically highest new AUROC | **0.740041**, balanced A | Difference 0.000643; paired conditional 95% interval **[-0.000525, 0.001875]** includes zero |
| Balanced A probability error | Brier **0.201243** | Worse than reference; not promoted into the demo |
| Development SHAP verification | **6,251 / 6,251** OOF rows passed | Maximum raw-margin error 0.000002629, probability error 0.000000253; tolerance 0.00001 |
| Saved Vision v3 | Accuracy **27/53 = 50.94%**, macro-F1 **0.325872** | Previously measured exploratory result; Grade-2 recall only 1/13; no new training |

Six predeclared XGBoost settings used the same frozen development membership and five folds: 30 fold fits plus one reference demonstration fit. Fresh preprocessing stayed inside every training fold. [Full comparison](tabular_pp1_completion_results_v1.md) contains all configurations and trade-offs. No held-out participant payload was loaded or evaluated. AUROC 0.80 was not achieved, and the small numerical gain is not established superiority.

The demo retains the existing raw XGBoost A reference, not an automatically selected final winner. Its fictional profile gives **21.408096%**; changing current to former smoking and cleaning days from 2 to 7 gives **25.849256%**. That increase is honestly displayed: this is model sensitivity for reported past treatment, not evidence that healthier behaviour causes harm or changes someone's treatment history. Reset reproduces the original exactly.

Survey-weight sensitivity reused saved OOF predictions without additional model fits: reference weighted AUROC **0.734877**, balanced **0.735493**. These are descriptive weighted point estimates, not population inference; complex-design variance remains pending. [Survey report](tabular_survey_sensitivity_v1.md).

Saved Vision uncertainty also reused predictions only. The v3-v2 macro-F1 interval crosses zero, and Grade 1 has only one Validation example. Neither repeated Validation selection nor unverified participant independence is resolved by bootstrapping. [Vision uncertainty](vision_saved_prediction_uncertainty_v1.md).

## Three code blocks to understand

1. `src/tabular/pp1_questionnaire_workflow.py:run_bounded`: ஒவ்வொரு fold-க்கும் புதிய preprocessing + model உருவாக்குகிறோம். அந்த fold-ன் training answers மட்டுமே அதைப் fit செய்கின்றன. வெளியே வைத்த development-validation rows-க்கு probability கிடைக்கும்; இதனால் preprocessing leakage தவிர்க்கப்படுகிறது.
2. `src/tabular/questionnaire_explain.py:explain_frame`: 47 encoded columns-ன் SHAP contributions-ஐ 12 கேள்விகளாகச் சேர்க்கிறோம். Base value + contributions model log-odds-க்கு சமமா என்று சோதிக்கிறோம். இவை probability percentage-point changes அல்ல; காரணம் நிரூபிக்கும் விளக்கமும் அல்ல.
3. `src/tabular/questionnaire_explain.py:simulate`: smoking status, cleaning days மட்டும் மாற்றலாம். History/age மாறாது; lifetime-smoking history-க்கு முரணான மாற்றம் நிராகரிக்கப்படும். அதே model மீண்டும் கணக்கிடும்; reset பழைய profile-ஐ மீட்டுத் தரும்.

**Viva question:** Why can the What-if output increase after a seemingly healthier scenario?

**Answer:** நம்ம target முந்தைய gum treatment பற்றிய self-report. Model கற்றது data associations; treatment effect அல்ல. அதனால் scenario change நல்ல உடல்நலப் பலனை நிரூபிக்காது; output அதிகரிப்பையும் மறைக்காமல் காட்டுகிறோம்.

## Files and verification

New code: `src/tabular/{questionnaire_explain,pp1_questionnaire_workflow,local_demo,survey_sensitivity}.py`, `src/vision/{saved_pilot_demo,saved_prediction_uncertainty}.py`.

New tests: `tests/test_questionnaire_explain.py`, `tests/test_pp1_questionnaire_workflow.py`, `tests/test_local_demo.py`, `tests/test_saved_pilot_demo.py`, `tests/test_saved_sensitivity.py`.

New aggregate evidence/UI: `docs/tabular_pp1_completion_plan_v1.md`, `docs/tabular_pp1_completion_results_v1.{md,json}`, `docs/tabular_survey_sensitivity_v1.{md,json}`, `docs/vision_saved_prediction_uncertainty_v1.{md,json}`, `docs/component2_local_demo_v1.html`, `docs/component2_demo_assets_receipt_v1.json`, `docs/component2_local_demo_verification_v1.json`, and this handoff. Existing diary, AI log and current-state handoff updated; older evidence retained.

The local model, participant OOF predictions and copied saved Vision images remain only in ignored `models/questionnaire_pp1_v1/`, `data/tabular_pp1_v1/` and `data/pp1_demo_saved_vision_v1/`. The server verifies pinned model/manifest/asset hashes. No checkpoint from an untrusted source is loaded. No original Vision image was decoded for this task; saved PNG previews were checked and copied byte-for-byte from the already verified results ZIP.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_questionnaire_explain.py tests/test_pp1_questionnaire_workflow.py \
  tests/test_local_demo.py tests/test_saved_pilot_demo.py tests/test_saved_sensitivity.py \
  tests/test_baseline_nhanes.py tests/test_preprocess_nhanes.py tests/test_xgboost_comparison_nhanes.py
```

Actual run: `76 passed in 5.93s`. Re-running training or the completed bounded experiment is unnecessary for opening the demo. Final browser screenshot was visually checked; aggregate browser/timing evidence is in `component2_local_demo_verification_v1.json`.

## Remaining completion requirements

- **Vision:** the 181 held records stay excluded; qualified labels, possible participant overlap, absent whole-image MGI 0 and scarce MGI 1 remain unresolved. Training and saved Grad-CAM worked, but performance is weak and final scientific eligibility is not approved. No external replacement dataset with verified equivalent MGI labels was qualified. Email is deferred at the owner's request.
- **Questionnaire:** freeze final model/calibration/operating-threshold protocol before untouched held-out evaluation; finish survey-design uncertainty, subgroup checks and external-applicability limitations. Existing calibration comparisons remain historical evidence, not automatic deployment approval.
- **Demo:** obtain owner understanding and short fictional-profile usability feedback. New-photo Vision inference/API deployment and any further real training require their explicit scope and appropriate runtime; they are not simulated as completed here.

**Next single action:** owner opens the local demo and rehearses one questionnaire explanation + What-if/reset and one saved Vision example. This checks the two independent user-facing explanations before deciding on further model work. No Colab help is needed for that step.

All work stayed on `vinuthan`. No source datasets, original labels/splits, historical implementations, research gates or teammate files were changed. No Test evaluation, new Vision training, installation, cloud upload, commit or push occurred.

## Sources used for implementation decisions

Raw-margin additivity and explanation units follow [SHAP TreeExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html) and [XGBoost prediction documentation](https://xgboost.readthedocs.io/en/stable/python/python_api.html). Search/selection optimism is consistent with [scikit-learn's nested-CV guidance](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html). Variable meanings and skip patterns were checked against the CDC [OHQ](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm), [SMQ](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm), [DEMO](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm) and [DIQ](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm) codebooks.
