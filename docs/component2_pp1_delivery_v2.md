# Component 2 PP1 delivery checkpoint — 16 October 2026

**Working local software, incomplete scientific validation.** The owner's current instruction authorizes necessary installation and autonomous local engineering/tabular work. It does not authorize protected Test evaluation, clinical decisions, a new real Vision experiment or use of the 181 held records.

## Open the working React + FastAPI demonstration

```sh
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m src.tabular.api
```

Open **http://127.0.0.1:8766**. The currently running demo uses the existing hash-verified XGBoost A artifact. No retraining, Colab or new download is needed. Bind remains loopback only; no access logging, public deployment, browser analytics or external CDN. The previous standard-library demo remains available on its own entry point.

1. Explain the fictional default profile: **21.41% previous-treatment probability**, 12 grouped log-odds SHAP contributions, reconstruction checked.
2. Change cleaning days to 7: **24.41%** under the unchanged example smoking status. A higher result is shown honestly; this is model sensitivity, not a treatment recommendation.
3. Reset: **21.41%** exactly. Editing the original profile invalidates the prior explanation/scenario. Only smoking and cleaning days can be changed in the simulator; history and lifetime-smoking consistency are enforced.
4. Open Vision: three verified saved v3 examples, nine original/heatmap/overlay views. No branch fusion.
5. New-photo controls are intentionally inactive in the default real demo. The complete React/FastAPI/ResNet/Grad-CAM path was tested with generated inputs only. Read `vision_photo_adapter_verification_v1.md` before any future real input.

FastAPI endpoints: `GET /api/schema`, `POST /api/predict`, `POST /api/what-if`, `POST /api/reset`, `GET /api/vision`, `GET /api/vision/runtime`, opt-in `POST /api/vision/photo`. `/openapi.json` publishes request contracts. Reuses the existing scientific functions, model and shared colour processing; no parallel scientific implementation. Raw JPEG route requires explicit trusted runtime registration and fails closed. Invalid fields, non-finite/duplicate JSON, oversized bodies, stale model versions, cross-origin requests and arbitrary filesystem paths are rejected. This is a local development server, not production authentication or a public service.

## Existing development evidence: no new model fits

Outcome is **self-reported history of previous gum treatment (OHQ850)**. All rows use the original 6,251 development participants and five folds. Threshold 0.50 is a comparison reference only.

| Model | Accuracy | AUROC | PR-AUC | AP | Macro-F1 | Positive precision | Recall | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Training-prior | 0.751560 | 0.499486 | 0.398258 | 0.248216 | 0.429080 | 0.000000* | 0.000000 | 0.186718 |
| Logistic C=1 | 0.776356 | 0.736721 | 0.512827 | 0.513089 | 0.628571 | 0.602649 | 0.292981 | 0.157823 |
| XGBoost A reference | 0.775396 | 0.739398 | 0.515988 | 0.516263 | 0.616051 | 0.611028 | 0.264005 | 0.157268 |
| XGBoost A balanced | 0.727564 | 0.740041 | 0.515812 | 0.516088 | 0.660395 | 0.460897 | 0.569221 | 0.201243 |

*No positive predictions; precision shown as zero by reporting convention, not an estimable positive predictive value. Historical Logistic/Dummy area metrics are the previously reported six-decimal values; classification metrics were derived from their exact saved confusion counts. XGBoost values reuse the hash-verified saved OOF artifact. Exact numbers/provenance: `component2_pp1_delivery_metrics_v2.json`.

**Demonstration choice: retain raw XGBoost A**, which has slightly stronger ranking/lower Brier than the original Logistic reference and already verified TreeSHAP integration. This does not prove statistically superior/final performance; Logistic has slightly better fixed-threshold accuracy, recall and macro-F1. Balanced A trades more recall for more false positives and much worse Brier; its AUROC gain of 0.000643 has paired interval [-0.000525, 0.001875]. No reliable improvement or AUROC 0.80 achieved. Further blind searches are not justified by these results.

Existing matched calibration evidence remains authoritative: Full XGBoost sigmoid worsened Brier by 0.000708 (conditional interval [0.000296,0.001120]). Logistic sigmoid's small Brier change includes zero. Current A-reference diagnostic intercept **0.060288**, slope **1.061995**; diagnostics do not calibrate probabilities or establish personal clinical validity. Do not replace the raw model with a nominally calibrated model without evidence. Existing Youden thresholds are statistical demonstrations, not approved clinical operating points.

New descriptive age/recorded-sex evidence in `tabular_subgroup_evidence_v1.{md,json}` completes this part of proposal §3.5 using saved A-reference OOF predictions. Age-bin N: **1,699 / 1,828 / 2,724**; recorded sex N: **3,005 / 3,246**. AUROCs range 0.722221–0.758777 across age bins and 0.735388–0.743342 across recorded sex. 1,000 conditional participant-bootstrap intervals are included, not design-based national-population uncertainty or proof of fairness. No model fits, Test payloads or threshold changes.

## New Vision engineering, not new dental performance

- Optional photo adapter reuses B1 extended float input and four-output v3 interpretation. Generated CPU **and MPS** forward/Grad-CAM tests pass. Unsupported ICC/orientation/format fails rather than guessing colours. Original source bytes/metadata are not written back.
- 680-Training-only frozen-feature probe runner implemented and synthetic tested. Fixed ImageNet ResNet50 → fold-local StandardScaler/balanced LogisticRegression, five grouped folds, majority/prior baselines, exact OOF coverage and conditional paired content bootstrap. No dental feature extraction or classifier fitting yet. Fresh explicitly scoped real-run authorization required; old pilot permissions are consumed. [Runner handoff](vision_frozen_feature_probe_implementation_v1.md).
- Existing v3 performance remains accuracy **0.509434**, macro-F1 **0.325872**, Grade2 recall **1/13**, macro-AUROC **0.627264** on 53 repeatedly used Validation cases. New software tests do not improve those numbers. No supported whole-image MGI0, only 12 Training/1 Validation MGI1, provisional labels, unverified participant independence, 181 holds unchanged.

## Actual verification and reproducibility

**98 passed, 0 failed, 0 errors, 0 skipped**, 6.39 seconds, focused integration/regression suite. Breakdown: 16 photo tests (CPU+MPS), 16 probe tests, 11 FastAPI tests, 5 subgroup tests, 50 directly affected existing questionnaire/demo tests. This is not the full repository suite. JUnit: `component2_integration_tests_v2.xml`; source hashes/environment/browser evidence: `component2_integration_verification_v2.json`.

Browser verified prediction, 12 SHAP rows, scenario/reset, nine saved views, disabled default photo route, mobile/desktop no horizontal overflow and generated-photo end-to-end output with three aligned 40×24 views. Screenshots visually inspected. No dental image was newly decoded or inferred.

Owner-approved packages installed only inside `.venv`: PyTorch2.11.0, Torchvision0.26.0, Pillow11.3.0, FastAPI0.143.2, Uvicorn0.54.0. `pip check` passed. Mac MPS built/available; generated tensor and full generated Grad-CAM passed. No pretrained weights downloaded. Optional exact requirements: `component2_runtime_requirements_v2.txt`.

React19.2.0/ReactDOM19.2.0/esbuild0.25.10 are installed in ignored `data/component2_ui_dependencies_v2/`. Source/lock and bundled browser assets are under `src/tabular/ui/`; rebuilding with `sh src/tabular/ui/build.sh` installs the pinned frontend dependencies, so do not rerun needlessly. Browser runtime needs no npm process or internet connection. Licence notice retained.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider \
 tests/test_frozen_feature_probe.py tests/test_photo_explanation.py \
 tests/test_component2_api.py tests/test_subgroup_evidence.py tests/test_local_demo.py \
 tests/test_questionnaire_explain.py tests/test_pp1_questionnaire_workflow.py \
 tests/test_saved_pilot_demo.py tests/test_saved_sensitivity.py
```

## Remaining decisions and limits

| Item | Concrete next step | Boundary |
| --- | --- | --- |
| PP1 rehearsal | Owner opens local demo and explains output/SHAP/What-if | No new data/Colab required |
| Vision signal experiment | Authorize one documented 680-only local probe with fresh bindings | 53 Validation/181 holds/NP015/Test excluded; no neural fine-tuning |
| New real-photo demo | Register an explicitly authorized non-study compatible photo and pinned v3 checkpoint | Current adapter does not support arbitrary phone ICC/EXIF; no clinical inference approval |
| Final questionnaire evaluation | Review/freeze model, calibration choice and threshold protocol, then separately authorize held-out evaluation | 1,563-person final Test stays sealed |
| Vision scientific eligibility | Qualified label/group/participant review; establish absent/scarce-class evidence | No automatic held-image recovery or MGI0 fabrication |
| Remaining research validation | Survey-design/domain uncertainty, explanation expert review, consented usability feedback | Conditional bootstrap/software tests do not replace these |

Do not describe the full project as scientifically complete. Neither more GPU speed nor a UI can repair missing labels or approve clinical claims. No human-participant study, deployment, email, upload, commit or push occurred.

## Tamil understanding / viva

1. **FastAPI adapter**: ஏற்கனவே tested model function-ஐ HTTP request வழியாக அழைக்கிறது. Input தவறாக இருந்தால் result கொடுக்காது. இதனால் UI/API/model இடையே வேறு preprocessing வராது.
2. **React state**: original profile, scenario, explanation தனித்தனியாக வைத்திருக்கிறது. கேள்விகளை மாற்றினால் பழைய prediction நீக்கப்படும்; reset original-ஐ மீண்டும் கணக்கிடும்.
3. **Fold-local scaler + classifier**: score செய்யும் image fitting-க்குள் போகாது. இதுதான் probe result நியாயமானதா என்பதற்கான முக்கிய பாதுகாப்பு.

Viva: Why is 77.54% accuracy not enough to call the questionnaire model excellent? **75.16% respondents report No already; always-No achieves that accuracy. AUROC, positive recall, Brier, baselines and uncertainty must be assessed together.**

Technical sources: [FastAPI request bodies](https://fastapi.tiangolo.com/tutorial/body/), [middleware](https://fastapi.tiangolo.com/tutorial/middleware/), [React createRoot](https://react.dev/reference/react-dom/client/createRoot). Research authority: signed proposal §§3.1–3.5 and explanation/scenario validation p.23. Existing results and original research safeguards are preserved.
