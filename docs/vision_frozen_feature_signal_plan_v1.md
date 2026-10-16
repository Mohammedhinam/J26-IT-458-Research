# Vision frozen-feature signal check — prospective plan v1

2026-10-16 · branch `vinuthan` · **PLAN ONLY; no real feature extraction or model fit executed.**

Owner delegated assessment of external advice and routine engineering choices to Codex. This record selects the next small experiment design; it does not fabricate a new real-run/cloud permission, clinical label approval, final manifest or revised research objective. Existing one-run pilot permissions remain consumed.

## Decision and rationale

Use a fixed ImageNet ResNet-50 encoder and a regularised class-balanced linear classifier to ask whether the current B1 inputs contain transferable grade-discriminating signal. Prefer this limited diagnosis before another fine-tuning stage. The next comparison is not a claim that the method will improve accuracy. Keep the original MGI 0–4 research definitions and separate questionnaire branch; evaluate only exploratory supported grades 1–4 under a separately versioned model context.

Accepted from external advice: a frozen-feature probe, fold isolation, class-support reporting, primary-source checks and qualified review provenance. Rejected: deleting/rewriting original captions, inferring FDI identity from TXT order, automatically adding uncertain records, assuming approved 733-record CV folds exist, repeating completed Grade-2 analysis, declaring a causal imbalance/threshold explanation, and promising improvements from resolution or hardware changes. Ordinal objectives/region supervision remain future methodological choices, not activated additions.

## Exact candidate design

| Item | Prospective fixed recipe |
| --- | --- |
| Sources | Existing **680 Training candidates only**, sorted by immutable source ID; 53 Validation candidates are outside this experiment |
| Labels | Existing provisional MGI 1–4; no relabeling or missing MGI 0 invention |
| Input | Existing hash-verified 224×224 B1 float32 arrays; same single ImageNet normalization, no clipping or new colour processing |
| Feature encoder | Official `ResNet50_Weights.IMAGENET1K_V2`; fixed evaluation mode, all tensors/BatchNorm frozen; 2,048-dimensional average-pool features before the head |
| Forbidden encoders | Historical v2/v3 dental-fine-tuned checkpoints: they have seen these Training labels and cannot generate leakage-free CV evaluation features |
| CV | Proposed `StratifiedGroupKFold(5, shuffle=True, random_state=42)`, existing content-group IDs; freeze a NEW versioned fold recipe before extraction/fitting |
| Classifier | `StandardScaler` → `LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs", max_iter=2000)`; one fixed configuration, no C/seed search |
| Fold fitting | Fit scaler, balanced class weights and classifier on the 544 fitting records only; score the 136 excluded fold records once |
| Baselines | Training-fold most-frequent class and Training-fold class-prior probabilities; never choose a constant from scored-fold labels |
| Fit budget | Five classifier fits plus ten cheap baseline fits; one frozen feature pass across 680 records, no neural optimisation |
| Repeats/augmentation | None initially; deterministic extraction, no test-time augmentation or automatic retries |

For a truly fixed encoder with no data-fitted preprocessing, one feature cache can be reused across the five classifier folds. Hash the encoder weights, code, B1 contract, source manifest, arrays, IDs and feature cache. Scaler fitting across all 680 before CV is forbidden. Feature extraction must not update BatchNorm. Any convergence warning, non-finite feature, altered frozen tensor, missing/mixed ID, wrong mapping or hash mismatch stops that operation; no silent parameter changes.

The proposed linear classifier is a new, explicitly identified head on the ResNet representation. It is not identical to the historical Adam-trained neural head; historical 53-Validation results cannot be directly ranked against these new 680-Training OOF metrics as though the evaluation populations matched. No final model promotion.

## Metadata-only feasibility actually checked

Reused development DRAFT SHA-256 `b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1`; no image/NPY payload or Test record read. Training support **12 / 84 / 223 / 361**, 680 distinct known content groups. Proposed split seed42 yields:

| Fold | Fitting N | Scoring N | Scoring support MGI 1 / 2 / 3 / 4 |
| --- | --- | --- | --- |
| 1 | 544 | 136 | 3 / 17 / 44 / 72 |
| 2 | 544 | 136 | 2 / 16 / 45 / 73 |
| 3 | 544 | 136 | 2 / 17 / 45 / 72 |
| 4 | 544 | 136 | 2 / 17 / 45 / 72 |
| 5 | 544 | 136 | 3 / 17 / 44 / 72 |

All proposed fitting/scoring group intersections were empty. These are planning calculations, not trained results or an activated fold manifest. The 680 known groups are all singletons; grouping therefore adds no identified within-cohort linkage in this subset and **does not establish participant independence**. Unknown shared participants can still invalidate independence assumptions. The 181 holds, NP015, protected groups, 53 Validation and Test stay outside the probe loader.

## Outputs and interpretation

Save local ignored features and one OOF prediction per immutable Training ID. Publish aggregate support, predicted-class counts, confusion matrix, macro-F1, balanced accuracy, per-grade recall, ordinal MAE, QWK, one-vs-rest AUROC where defined and multiclass Brier. Within-one-grade accuracy is secondary because constant middle-grade predictions can look strong on that measure.

Use 1,000 fixed-seed paired content-group bootstrap draws for descriptive differences against the fold-derived baselines. Mark draws with undefined class metrics and report their count; do not silently invent metrics. Conditional intervals omit model-refitting uncertainty and unknown participant clustering. Grade-1 conclusions remain weak with only 12 total examples. The original 53 Validation cases have already informed prior work; not using them in this probe does not retroactively restore an unbiased evaluation history.

No automatic pass/fail scientific threshold or next training stage is set. A positive result would support only this fixed representation/probe on provisional within-source labels. A negative or imprecise result would not prove there is no visual signal or that all fine-tuning is futile. Do not select new thresholds, discard errors or change labels after seeing these OOF results.

## Next engineering step and execution requirements

Prepare a separate generated-data-tested extractor/probe runner and code-only Colab handoff. Preserve existing production trainer and final-research approval gate. Before any real run, require the current trusted 680-selection/fold/code/input/official-weight bindings, available compatible runtime and a fresh explicitly scoped execution record. No automatic weights download, new dental-data upload or reuse of consumed one-run permissions. The current task creates no execution record.

Focused checks needed: exclusion of 53/181/NP015/Test before payload access; genuine fixed encoder provenance; unchanged frozen weights/BatchNorm; four-grade ordering; fold-only scaler/class weights; exact OOF coverage; cache tampering rejection; deterministic synthetic execution; independent metric/baseline arithmetic. No completed dataset audit needs repeating.

Qualified label adjudication, participant evidence and any external MGI data remain separate scientific work. No method can learn or validate whole-image MGI 0 from its absence here.

Sources: [LP-FT primary study](https://arxiv.org/abs/2202.10054) motivates checking fixed representations, but does not establish efficacy on this dental task; [scikit-learn grouped CV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html) defines the grouping boundary. Project evidence: [strict candidate DRAFT](vision_development_strict_clean_draft_v1.md), [completed Grade-2 diagnosis](vision_grade2_v2_v3_diagnostic_v1.md), and [current working demo](component2_pp1_working_demo_v1.md).
