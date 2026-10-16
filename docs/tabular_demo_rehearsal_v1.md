# Questionnaire PP1 rehearsal — verified 16 October 2026

Open **http://127.0.0.1:8768/**. This is the existing loopback-only React/FastAPI demo. If the server is stopped, use the existing command from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m src.tabular.api --port 8768
```

Use fictional profiles only. No participant dataset, final Test rerun, training, new calibration or cutoff adjustment is needed for this demonstration.

## Five practical steps and what to say

1. **Explain the target before clicking.** “இந்த questionnaire AI, முன்னாடி gum-disease treatment எடுத்ததாக ஒருவர் report செய்திருக்கிறாரா என்பதற்கான probability கொடுக்கிறது. இப்போது disease இருக்கிறதா அல்லது எதிர்காலத்தில் வருமா என்று சொல்லாது.” Outcome is OHQ850; it is never an input.
2. **Click Restore example profile, then Explain this profile.** The fictional example has 12 inputs and produces **21.41%** (actual raw probability 0.21408095955848694). “இது model estimate; எனக்கு 21.41% disease இருக்கிறது என்று அர்த்தம் இல்லை.” Smoking combines two source questions; unknown responses remain explicit.
3. **Show the 12 SHAP contribution rows.** “ஒவ்வொரு input-ம் இந்த prediction-ஐ base value-இலிருந்து எப்படித் தள்ளுகிறது என்பதை SHAP காட்டுகிறது. இது log-odds unit; probability percentage-point change அல்ல; காரணமும் அல்ல.” Actual base -1.1116950511932373 plus grouped contributions reconstructs raw margin -1.3004995584487915 within 2.2034510038793087e-7. Sigmoid reconstruction error is 4.253786931029957e-8; both pass the existing 1e-5 tolerance. Example smoking/cleaning pair has 84 development examples; this does not establish full-profile reliability.
4. **Set Scenario cleaning days to 7; leave smoking unchanged; click Compare scenario.** Actual output is **24.41%** (0.24407000839710236), a +2.9989 percentage-point model response. “Answer மாற்றியதும் model output மாறுகிறது. Cleaning அதிகமானதால் disease மோசமாகிறது என்று இதிலிருந்து சொல்ல முடியாது; கடந்த treatment history-யையும் இதனால் மாற்ற முடியாது.” The simulator permits only smoking and cleaning days, not age, sex or history. Never hide an inconvenient increase.
5. **Click Reset scenario.** Output returns exactly to **21.41%**. Editing the original profile clears the old explanation and disables the simulator until a new explanation is requested. “Original மற்றும் scenario தனித்தனியாக வைத்திருக்கிறோம்; பழைய answer-க்கு வந்த output-ஐ புதிய answer-க்கு காட்டுவதில்லை.”

## Explain measured performance separately

The fictional probability above is not an accuracy metric. Use [the completed frozen final report](tabular_final_test_results_v1.md) for performance:

| Frozen model | Held-out n | AUROC | Brier | Statistical cutoff | Sensitivity | Specificity |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost A raw | 1,563 | 0.760654 | 0.150858 | 0.26 | 0.559278 | 0.835745 |
| Logistic C1 raw | 1,563 | 0.756113 | 0.151364 | 0.28 | 0.541237 | 0.831489 |

“Development-ல் model/cutoff freeze செய்த பிறகு, தனி owner permission-உடன் ஒருமுறை final Test செய்தோம். XGBoost AUROC 0.7607; 95% conditional interval 0.7334–0.7889. Logistic-ஐவிட உறுதியாகச் சிறந்தது என்று நிரூபிக்கவில்லை. 0.80 இலக்கு அடையவில்லை.” AUROC is not percent accuracy. No further tuning on these Test results. At XGBoost cutoff 0.26, 171 reported Yes are missed and 193 reported No are flagged; the cutoff is not clinically approved. The live interface displays probabilities without implementing a clinical binary recommendation.

**Existing presentation limitation:** The unchanged generic footer says scientific evaluation/approvals are pending and the historical API role string says “not final model selection.” For this rehearsal explicitly explain that **questionnaire numerical freeze and one final evaluation are now complete**, while Vision label/group approvals, external/clinical validity and remaining research work are pending. The current final report/handoff are authoritative; the original model metadata were preserved. A future presentation-only wording update should use external provenance rather than rewrite historical artifacts.

## Actual rehearsal verification

Browser automation exercised Explain → change cleaning → Compare → Reset → edit original → Restore → Explain on the live local app. Observed 21.41% → 24.41% → 21.41%, 12 rows, visible additivity/unit/non-causal warnings, original-edit invalidation and zero uncaught page errors. Additional browser-origin API checks verified original/scenario/reset responses and five fail-closed requests: protected age, lifetime-smoking rewrite, cleaning=8, stale model version and outcome supplied as predictor all returned HTTP 422. Those expected rejections produce five browser network error entries; they are not unexpected JavaScript failures.

**17 explicit API/numerical assertions passed, zero failed**, plus the recorded UI observations above. These are rehearsal checks, not a new pytest/full-repository run or a repeated final evaluation. Exact fictional responses and provenance are in [verification JSON](tabular_demo_rehearsal_verification_v1.json). No scientific code, model, threshold, source data, split, historical result or frontend bundle changed. No install, upload, commit or push.

## Three important existing blocks

- `QuestionnairePrototype.predict`: அதே frozen model-ஐ வைத்து probability மற்றும் TreeSHAP எடுக்கிறது; UI-க்கு வேறு scientific model இல்லை.
- `simulate` checks `set(changes) <= EDITABLE`: smoking/cleaning தவிர வேறு field மாறுவதைத் தடுக்கிறது; immutable history மற்றும் model version சரிபார்க்கப்படுகின்றன.
- `reset` calls `simulate(original, {}, model_id)`: original profile-ஐ மீண்டும் பயன்படுத்துவதால் அதே prediction திரும்புகிறது.

Viva: **Why can cleaning=7 produce a higher probability?** “Model observational treatment-history associations கற்றிருக்கிறது. Answer மாற்றுவது hypothetical re-inference மட்டுமே; health benefit அல்லது causal effect நிரூபணம் இல்லை.”

## What still needs a human

Owner should perform this explanation aloud; this automation is not a usability study or evidence that the owner understands it. Obtain actual consented feedback separately without inventing users or responses. Vision qualified labels/content-group decisions, whole-image MGI0 evidence and participant independence remain unresolved; the 181 held images stay excluded.

What I understood (my own words):
