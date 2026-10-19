# EfficientNet proposal candidate: live photo and Grad-CAM integration

18 October 2026. Owner requested adding the trained EfficientNet-B0 candidate.
Integration is complete and locally verified. No training or accuracy improvement
is claimed by this UI/API change.

## Open the current proposal demo

**http://127.0.0.1:8773/**

```sh
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
zsh scripts/run_pp1_proposal_demo.sh
```

The earlier port-8771 process remains running and was not stopped or restarted.
Use **8773** for the new four-model demo. Its opt-in EfficientNet runtime uses an
additional CLI argument; the older running server cannot load that new endpoint
without a restart. Shared frontend files update on reload, so on the earlier
server the new candidate card will be unavailable while the three old runtimes
remain usable. The new version is independently available on 8773.

Upload one permitted intraoral JPG/PNG, select consent and use Run All Four Models.
Doctor Review Mode still requires an independent assessment before AI reveal.
Developer Mode stays explicitly not clinically reviewed. The same input SHA
binds all four genuine model responses. Two columns keep the whole-photo models
above the additional ROI comparisons, with individual feedback and errors.

| Card | Proposal/demo role | Actual output |
|---|---|---|
| A, EfficientNet-B0 | Main Vision candidate | MGI 1–4, class scores, predicted-class Grad-CAM original/heatmap/overlay |
| B, ResNet50 v3 | Vision baseline comparison | Existing grade/scores and Grad-CAM |
| C, YOLO ROI v1 + ResNet18 | Additional experimental comparison | Existing predicted boxes, crop grades, maximum crop grade |
| D, ROI v2 CORAL | Additional experimental comparison | Existing boxes, ordinal crop grades/probabilities, maximum crop grade |

Questionnaire still uses the existing XGBoost model, SHAP in log-odds and the
restricted what-if/reset workflow. Its target remains self-reported previous gum
treatment, independent of Vision. No fusion or diagnosis was introduced.

## Which EfficientNet model actually runs

Pinned existing checkpoint:
`data/efficientnet_adaptation_v1_20261017_1792202682936988000/fold0_last_block/final.pt`.
SHA-256: `b557f52e358ca88329391e01e3f2c6f77123d14bbbe1027dd38391a27ea96353`.

- Architecture: torchvision EfficientNet-B0, four-output head for MGI 1–4.
- Existing final-block + head adaptation arm, fold 0, fixed final epoch.
- Fold chosen prospectively for illustration, consistent with the existing ROI
  demo fold; not selected for the best score or best-looking heatmap.
- The checkpoint fitted 544 original Training images. It is **not** an
  all-development refit or final clinically validated model.
- Original checkpoint bytes, grades/arm/fold and training provenance bindings
  are checked before/after strict state loading. All **360/360 model state
  tensor hashes** match the original final training receipt.
- No model download, dataset scanner, retraining or checkpoint replacement.

**Metrics must remain distinct.** This neural arm's existing pooled 680-image
five-fold OOF accuracy is **46.76%**, Macro-F1 **0.3416**, Grade 1 **1/12**,
Grade 2 **33/84**. These are pooled experiment metrics, not an accuracy estimate
for an individual upload or this single fold alone. The **52.21%** experiment
used frozen EfficientNet features plus Logistic Regression and is a different
workflow. It is not the live neural model. ResNet v3's 50.94% on 53 reused
Validation images also cannot be ranked directly against these 680 OOF values.

“Main candidate” describes the signed proposal role. It does not establish that
EfficientNet is the best model, solves minority grades, or meets clinical targets.

## Preprocessing and Grad-CAM

The adapter reuses `prepare_local_upload()` and `LocalUploadPhotoRuntime`.
JPEG/PNG decoding, EXIF orientation, embedded ICC handling, explicit missing-ICC
sRGB assumption, B1 sampling, valid-box geometry and ImageNet normalization stay
the same as the existing local whole-photo pipeline. No antialiasing experiment
or silent preprocessing change was introduced.

Grad-CAM targets **`features.8`**, the last convolution/BatchNorm/activation block
before pooling. It explains the same predicted class used for the displayed MGI.
The existing alignment function removes model padding and maps attention to the
original display geometry. The original preview is unchanged. Eval mode freezes
dropout and BatchNorm. Input gradients allow CAM while model weights remain fixed.
Hooks are removed after requests. CPU is used for this bounded candidate runtime.

The heatmap is genuine model attention. The example still highlights peripheral
regions as well as intraoral regions. No mask, crop or colour manipulation forces
the explanation toward gums. Whole-image MGI 0 remains unsupported. Scores are
uncalibrated and not clinical confidence. Clinical localization remains unverified.

## Actual outputs and verification

On the owner's previously permitted non-study JPG:

| Model | Actual predicted image grade | Additional details |
|---|---:|---|
| EfficientNet-B0 | 3 | Scores for MGI 1–4: .0523625 / .1043020 / .4970290 / .3463065 |
| ResNet50 v3 | 3 | Existing actual Grad-CAM and four class scores |
| ROI v1 | 3 | 12 predicted tooth ROIs |
| CORAL v2 | 2 | 12 predicted tooth ROIs |

These are model predictions, not clinical labels or single-photo accuracy.
All four request responses had the same source-byte hash and `photo_saved:false`.
The unchanged fictional Questionnaire example returned 21.41% previous-treatment
probability. SHAP, what-if and reset were verified in the browser.

- **40 focused pytest cases passed, 0 failed**, with 3 existing SHAP deprecation
  warnings. Includes 8 EfficientNet-specific cases, existing decoding/CAM checks
  and consent/inactive/malformed/new endpoint/old endpoint/questionnaire checks.
- **40 browser assertions passed, 0 failed**. Includes four actual checkpoint
  responses, same-photo identity, eight explanation images, candidate/baseline
  order, two-column layout, individual failures, candidate failure preserving
  other results, stale reset, feedback exports, mobile, no storage or external
  browser requests, and no page JavaScript errors.
- Error/flat-CAM/no-detection browser fixtures are synthetic and are not clinical
  results. Export fixtures remain clearly software tests, not doctor feedback.
- Direct inference versus CAM probability difference on the permitted photo:
  **2.0862e-7**, within the existing 1e-6 probability precision bound.
- Generated JPEG without ICC, oriented JPEG with ICC and RGBA PNG with ICC all
  pass real-checkpoint probability/grade/CAM-size/original-preview, state and
  BatchNorm/eval/hook-cleanup checks. No study/Test image is used by these tests.
- **39/39 protected artifact hashes unchanged**, including all 10 EfficientNet
  checkpoints, older model archives, dataset ZIP, questionnaire model/scientific
  source and previous research. Four intended API/UI files changed with exact
  before snapshots. Existing dirty edits were preserved.

An initial three-case numerical check used an overly strict 1e-7 tolerance for
ordinary inference versus gradient-enabled float32 execution. Measured differences
were about 1.5–2.1e-7. The final tests independently compare CAM with a separate
gradient-enabled forward at 1e-7, and ordinary inference at the shared 1e-6 bound.
No predictions, weights, input processing or heatmaps were changed to pass tests.
The initial failing XML is preserved separately from the final passing XML.

## Changed and added files

- `src/vision/efficientnet_live.py`: pinned provenance-checked loader and small
  adapter sharing existing preprocessing/CAM validation.
- `src/tabular/api.py`: optional runtime, two local endpoints and CLI opt-in.
- `src/tabular/ui/DoctorVision.jsx`: candidate first, baseline next, four cards,
  available whole-photo outputs and four independent feedback records.
- `src/tabular/ui/style.css`, `app.js`: readable two-column comparison and cached
  dependency build. No install, remote icon or frontend service.
- `tests/test_efficientnet_live.py`, `tests/test_component2_api.py`: meaningful
  provenance/CAM/state/HTTP tests and updated four-model UI contract.
- `scripts/run_pp1_proposal_demo.sh`, `scripts/doctor_demo_four_model_smoke.cjs`:
  versioned launch and browser verification. Older launcher/script preserved.
- New report, evidence, handoff/log entries and a separate updated PPT.

Endpoints: `GET /api/vision/efficientnet-runtime` and
`POST /api/vision/efficientnet-photo`. The photo route uses the same loopback,
same-origin, consent, bounded-body, serialization lock, no-store and error handling
boundaries as the existing photo workflow. Response identity adds model name,
proposal role, fold, training arm, CAM target layer and correctly scoped aggregate
evaluation. Unsupported/missing runtimes fail independently, with no cached-example
fallback or invented score. No auto-persistence or auto-retraining is added.

Private evidence: `data/vision/efficientnet_live_integration_20261018_v1/`.
Final test XML: `focused_tests_final.xml`. Browser: `browser_verification.json`.
Actual screenshot: `efficientnet_card.png` or `four_models_clean.png`.
Checkpoints: `checkpoint_and_inference_verification.json`. Preservation:
`preservation_before.json`, `preservation_after.json` and `source_before/`.

Updated deck: `docs/pp1_final_20261018/PP1_Proposal_Doctor_Demo_v3.pptx`.
All ten slides were rendered and inspected, including native editable metrics
tables and actual candidate screenshot. Package/layout/font/import checks passed.
Native PowerPoint execution remains untested; rehearse before PP1. Earlier PPTs
and the original three-model report are preserved as historical versions.

## Viva explanation

“EfficientNet-B0 is our proposal candidate. We integrated an existing fold-0 neural
checkpoint without retraining. The same photo also goes through ResNet baseline
and two ROI experiments. Grad-CAM explains predicted-class attention, not clinical
gum boundaries. The 46.76% neural OOF result and 52.21% frozen-feature Logistic
result are different workflows.”

Three important code blocks: SHA/schema checks prevent loading the wrong model;
`weights=None` prevents an unintended download; the shared local runtime preserves
the trained B1 input and honest image geometry. Likely viva question: **Why not
display 52.21% for this card?** It belongs to a different classifier workflow.

No new training, external upload, label/split change, Test access, commit/push/reset
or old-process shutdown occurred. Grade 1/2 performance, participant independence,
clinical grading and disease localization remain unresolved research limitations.
