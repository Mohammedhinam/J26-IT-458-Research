# Vision safe-progress checkpoint — 2026-10-16

**Authorized safe work completed; one new real experiment awaits specific owner scope.** No new real-image inference/training, clinical approvals, installations, cloud activity, commit or push in this mission.

## Completed

1. Reused signed proposal §§3.1–3.5/explanation validation, verified experiments and cached data evidence. No repeat dataset/colour audits, feature extraction or prior experiments.
2. Prepared [181-development reviewer workflow](vision_held_development_review_v2.md):52Training+129Validation. Every decision pending; zero approved/recovered records. Disjoint queues121partial-policy,54otherannotationreferrals,4groupcompanions,2NP015. These are not54near-pair decisions, which were already reviewed. Existing52Training package preserved. Only2partial-policy records are Training;119areValidation.
3. Completed [saved680OOF Grade1/2 diagnosis](vision_grade12_learning_diagnostic_v1.md). Exactly680aligned IDs/labels/folds and288private case-model rows; no new fits. Grade2 balancedEfficientNet22/84 vsunweighted19/84;allGrade1correct0/12. High-confidence errors observed; no causal learning-code bug established.
4. Prepared [one bounded nested-head plan](vision_nested_feature_probe_plan_v1.md) and separate runner. Six fixed configurations,95fits, cache-only, fresh explicit scope. **Generated-only verification; no real results or permission record.**
5. Updated local React/FastAPI demo with separate historical53Validation and680TrainingOOF evidence. Hash-checked aggregate inputs, no per-image IDs/paths exposed. New-photo runtime remains inactive; nine existing savedGradCAM views remain available. Questionnaire prediction/SHAP/reset preserved.

## Reused actual results, not rerun

| Training680 fivefoldOOF | Accuracy | Macro-F1 | Balanced accuracy | Recall MGI1/2/3/4 |
|---|---:|---:|---:|---|
| ResNet balanced | .475000 | .295114 | .293791 | 0/12;17/84;73/223;233/361 |
| EfficientNet balanced | .526471 | .341037 | .340590 | 0/12;22/84;99/223;237/361 |
| EfficientNet unweighted | .532353 | .337377 | .336938 | 0/12;19/84;100/223;243/361 |
| Majority | .530882 | .173391 | .250000 | 0/12;0/84;0/223;361/361 |

Historical53Validation v3:accuracy.509434,macro-F1.325872,recalls0/1,1/13,15/22,11/17. **Different population; do not compare its accuracy directly to680OOF.** EfficientNet shows a representation improvement over ResNet in the controlled probe, but no reliable four-grade classifier or calibrated probabilities has been demonstrated. Unweighted accuracy barely exceeds majority while minority-grade recall remains poor.

## Actual new verification

| Focused suite | Passed | Failed/errors/skipped |
|---|---:|---:|
| Held-development review workflow |17|0/0/0|
| Saved-prediction diagnostic |11|0/0/0|
| Nested cached-feature runner, generated inputs only |10|0/0/0|
| Aggregate evidence + directly affected API regressions |20|0/0/0|

58selected tests passed across these four suites; **not a repository-wide run or clinical test**. Nine held-review artifact assertions passed. Twelve core browser checks passed, then3post-hint/accessibility checks passed. Desktop/mobile aggregate screenshots inspected; mobile table scrolls within the page with an explicit hint and keyboard-focusable region. Browser automation initially used an invalid relative request URL; changed test URL to absolute, no application defect inferred. Screenshot tool initially rejected the project path due its own root configuration; used the tool's permitted output location and copied the generated aggregate screenshots into ignored local storage. No unrelated existing file changed.

[Verification and current hashes](vision_evidence_demo_verification_v1.json). Updated demo: `http://127.0.0.1:8768`; restart with `.venv/bin/python -B -m src.tabular.api --port 8768`. The earlier8766server was left alone. No external deployment.

## Important code the owner should understand

- `saved_grade_diagnostic.analyze`: compares immutable ID/label/fold arrays before probabilities. A fair comparison needs the same records and evaluation procedure; analysis returns counts/ranks, not revised labels.
- `nested_feature_probe.select`: receives only outer-fitting rows. Each inner fit includes its own scaler/classifier; outer scoring labels cannot choose settings. The proposed maximum is95fits, not an unrestricted search.
- `vision_evidence.card/load_evidence`: verifies fixed aggregate report hashes and whitelists display fields; separates53historicalValidation from680OOF. No private case IDs, dataset images, final-model promotion or new-photo activation.

Viva: Why not select settings using the outer-fold score? Because that would use the evaluation answers to choose the model and make the reported performance optimistic. Inner folds choose, outer folds evaluate the selection procedure; earlier development decisions still limit independence.

## Remaining blockers and one next action

All181holds, NP015, original labels/splits/proposed groups and research-training gates remain. Qualified annotation/group decisions and participant evidence are absent. Whole-imageMGI0 is absent; Grade1 has only12Training/1Validation examples. Existing synthetic/runtime correctness does not establish clinical label validity or performance.

**Next single engineering action:** obtain explicit authorization for exactly the95-fit Training680cachedEfficientNet nested-head experiment in the frozen proposal. It requires no Colab, photos, weights,53Validation,held/Test data or installations. No real run until authorized. Qualified human review can proceed independently using the existing review package, without automatic promotion.

Resume: read `AGENTS.md`, the handoff and `vision_autonomous_checkpoint_v1.json`. This is a resumable local record; no background scheduler or automatic cross-session continuation is asserted.
