# Frozen-feature probe implementation — 2026-10-16

Implemented the prospective `vision_frozen_feature_signal_plan_v1.md` recipe in `src/vision/frozen_feature_probe.py`. **Synthetic software checks only; no real 680-image extraction or probe fit has occurred.**

## Implemented scope

- `training_rows`: reuse pinned B1 manifest verification before payload access; select exactly 680 Training IDs, support 12/84/223/361. All 53 Validation candidates, 181 holds, NP015/protected groups and Test remain outside the extractor.
- `make_folds`: sorted immutable IDs, five seed-42 StratifiedGroupKFold partitions; complete once-only OOF coverage, no content-group overlap and all four grades required on both sides. Known content grouping does not establish participant independence.
- `extract_features`: fixed eval ResNet-50 average-pool features, 2,048 dimensions, no gradients/optimisation, unchanged tensors/BatchNorm; shared B1 float normalization without clipping. No dental-fine-tuned encoder permitted in the real entry point.
- `probe`: a fresh StandardScaler + balanced LogisticRegression(C=1, lbfgs, max_iter=2000) within each fold; fold-derived majority/prior baselines. Convergence warnings stop execution; no silent retries or tuning.
- `load_feature_cache`: numeric-only NPZ, 64 MiB bound, SHA, dimensions, finite values and exact IDs/labels/groups/folds checked. No pickle loading. Cache hashes accompany results.
- `paired_intervals`: 1,000 deterministic content-group resamples of saved OOF predictions; paired macro-F1, balanced-accuracy and QWK differences. Missing-grade resamples counted. No refitting/participant-independence/selection correction claim.
- `run_authorized`: separate scope `run_training680_frozen_probe_v1`; binds manifest, current code, fixed config, selection, folds, official ImageNet V2 weights and fresh ignored output path. Writes protocol before extraction. Old pilot authorization fails. Never downloads, scans the source dataset, accesses Validation arrays or changes training gates.

## Actual generated verification

16 focused tests passed, zero failed/skipped. Includes actual CPU ResNet-50 weights=None feature execution, frozen BatchNorm/tensors, deterministic results, grouped folds, independently checked scaler means/prior probabilities/confusion counts, rejection of invalid inputs, missing owner opt-in, stale scope, wrong manifest and cache corruption. This is not evidence of dental predictive signal.

The generated feature fixture deliberately contains separable class signal; its perfect synthetic classification tests mechanics, not clinical performance. No real result is fabricated.

## Before a real probe run

The user has authorized runner development and synthetic checks. No fresh real-probe execution record was created. Previous v1/v2/v3 real pilot permissions were consumed.

Required next explicit scope: **one local, 680-Training-only fixed ImageNet ResNet-50 feature pass and five-fold linear probe**, with the documented recipe and current hashes. Exclude the 53 Validation/181 holds/NP015/Test; no neural training, additional searches, cloud upload or final-model promotion. The existing official checkpoint must be available and hash-match; a new weights download is not automatic. Generate the truthful owner record only after this decision, not from an example permission template.

Mac PyTorch now works, including MPS. The reproducible probe path currently uses CPU, seed42 and two torch threads; a GPU protocol change is unnecessary for readiness. No Colab action is needed for completed synthetic tests.

## Three lines to explain

1. `model.eval(); model.requires_grad_(False)`: படத்திலிருந்து features மட்டும் எடுக்கிறது; backbone/BatchNorm கற்றதை மாற்றாது.
2. `model.fit(x[fit], y[fit])`: அந்த fold-ல் score செய்யப்படும் images scaler/classifier fitting-க்கு போகாது.
3. `predictions['linear'][score] = model.predict_proba(x[score])`: ஒவ்வொரு Training image-க்கும் அது fitting-ல் இல்லாத fold-இலிருந்து ஒரு probability கிடைக்கும்.

Viva: Why not reuse the v3 dental checkpoint as the CV feature encoder? It already learned these Training labels; that would leak label information into every fold's representation.
