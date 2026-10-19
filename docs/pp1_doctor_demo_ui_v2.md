# PP1 Doctor Demo — reference-layout update

18 October 2026. Owner requested the supplied blue/teal doctor-dashboard reference be implemented using actual trained-model outputs.

## Implemented

- Teal PP1 header, dark sidebar, local SVG icons and visible Research Use Only label.
- Working Vision, Questionnaire, Results & Feedback, Model Comparison and About navigation. Vision opens by default. Selecting a Vision section preserves the current photo/results; leaving the Vision tab discards its session state as before.
- Compact drag-and-drop JPG/PNG input, full-field original preview, consent, shared Run All and explicit reset/remove controls.
- Doctor pre-reveal assessment remains above the run results. Developer mode remains explicitly not clinically reviewed.
- Three aligned, equal-height desktop result cards with genuine grades. ResNet class-score bars and compact original/heatmap/overlay; ROI counts, predicted boxes and scrollable per-ROI tables. CORAL shows all five actual crop probabilities.
- Feedback is placed below the results in model-specific cards, with Agree/Disagree/Uncertain buttons, optional grade, reason, notes and existing explicit JSON/CSV export.
- Research evidence, checkpoint information and technical details remain available without crowding the main comparison.
- Mobile navigation and stacked result cards; no horizontal page overflow in the verified 390-pixel viewport.

The screenshot's invented sample grades, clinical severity labels, confidence and gum-focused heatmaps were not copied. Model scores remain uncalibrated; image-level grade is distinct from detector confidence. Original heatmaps and ROI coordinates are unchanged. Whole-image MGI 0 and clinical-localisation limitations remain visible. Full photos are contained, not cropped to hide inconvenient attention.

## Changed files

- `src/tabular/ui/App.jsx`: dashboard shell, default Vision tab and functional sidebar section navigation.
- `src/tabular/ui/DoctorVision.jsx`: compact layout, score bars, table presentation, drop input and separate feedback panel. Existing inference queue, byte checks, stale-response protection and export allowlist retained.
- `src/tabular/ui/Icons.jsx`: local SVG icons; no icon CDN or remote requests.
- `src/tabular/ui/style.css`: reference-inspired blue/teal presentation, compact typography, responsive navigation/cards.
- `src/tabular/ui/app.js`: production bundle rebuilt with existing cached dependencies.
- `scripts/doctor_demo_browser_smoke.cjs`: updated selectors, selectable evidence folder, navigation/equal-height/drop checks.
- Documentation, project handoff and task logs.

## Verification

- Focused existing API suite: **21 passed, 0 failed**, 3 warnings.
- Final browser suite: **37 passed, 0 failed**. Includes actual Questionnaire/SHAP/what-if/reset, three real checkpoint photo responses, input hash identity, independent failure, stale-response reset, no-detection/flat-CAM presentation, doctor assessment gate, developer export labels, JSON/CSV downloads, formula-safe CSV, sidebar navigation, equal card heights, drag-and-drop, mobile overflow, loaded images, no browser persistence, no external browser transmissions and no page JavaScript errors.
- Fault cases use explicit synthetic fixtures only; screenshots and primary inference evidence use real returned model outputs.
- Protected hashes: **15/15 matched**, including model/checkpoint archives, dataset ZIP, prior research results, questionnaire scientific code, API and both ROI live adapters. No backend or trained-model changes in this UI task.
- Same permitted photo real outputs remain ResNet MGI 3, ROI v1 maximum 3 with 12 ROIs, CORAL maximum 2 with 12 ROIs. No new accuracy estimate or clinician judgement.
- React build and `git diff --check` passed. Existing dirty tree preserved; no commit, push, reset, retraining or Test access.

Earlier browser attempts exposed a numbered-heading selector assumption and asynchronous sidebar/scroll timing. The selector was corrected; sidebar navigation now opens existing sections immediately and uses nonanimated scrolling. Earlier reports are preserved alongside the final report; no failed attempt was relabelled as passed.

Evidence: `data/vision/doctor_demo_ui_v2_20261018/` contains final browser JSON, API JUnit XML, desktop/mobile screenshots, export software fixtures, dirty-tree snapshots and preservation receipts. Screenshots are bounded verification artifacts from the previously permitted non-study photo; normal uploads remain temporary. Free-text export notes must omit identifiers.

## Open the result

The existing server continues at **http://127.0.0.1:8771**. Refresh the page to load the rebuilt UI. Existing launch command and model limitations are documented in `docs/pp1_three_model_doctor_demo_v1.md`.

Viva: “This change improves the presentation. It does not alter model weights, training or predicted attention. The three outputs still come from the same photo and remain independent.”
