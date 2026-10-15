# Exploratory development-only ResNet-50 pilot — proposed v1

2026-10-14. **PLAN, not training authorisation or the final scientific protocol.**

Purpose: the fastest honest PP1 prototype demonstrating authorised RGB → image-maximum MGI 0–4 → Grad-CAM, using the current code. Start ResNet-50, the signed proposal's baseline; retain EfficientNet-B0 comparison/fine-tuning as later stages. Do not fuse NHANES outputs.

## Prerequisites

The [strict-clean draft](vision_development_strict_clean_draft_v1.md) currently contains 680 Training / 53 Validation technical candidates and **zero approved records**. It is not accepted by the trainer. Obtain authentic retained-label reviewer/date/provenance, participant independence, exclusion/group/split approval, externally authenticated manifest freeze and separate exact-protocol approval. Re-count grades after approval if eligibility changes. Test remains sealed; no Test grades/statistics drive any decision.

Current retained candidates lack image-level MGI 0; MGI 1 has only 12 Training / 1 Validation. Preserve five definitions/logits; do not remap to four classes, create normal examples, mask unsupported predictions as validated, or claim validated five-class performance. Signed approval must explicitly acknowledge these limitations and the exploratory purpose.

## One bounded proposed profile — freeze before execution

Reuses the existing scaffold's illustrative settings; no new search, augmentation or training implementation.

| Setting | Proposed value | Basis / approval |
|---|---|---|
| Architecture | ResNet-50, five MGI 0–4 logits | Signed proposal baseline/schema |
| Weight source | `ResNet50_Weights.IMAGENET1K_V2`, already cached and documented | Current factory; availability not checked today; downloads remain disabled |
| Initial optimisation | Classification head only; pretrained backbone/BatchNorm frozen | Signed initial stage; existing code |
| Learning rate | `0.001` | One of proposal's explicit values; selected pilot setting requires approval |
| Batch / epoch cap / patience | `16 / 30 / 5` | Existing proposed resource cap, not activated |
| Seed / min_delta | `42 / 0.0` | Existing scaffold; no repeated seed search in pilot |
| Optimiser / weight decay | Adam / `0.0` | Existing code; implementation choices to approve |
| Class weighting | `none` for this first reference run | No weighting search; later Training-only balanced comparison separate |
| Preprocessing | Existing RGB 224×224 aspect-preserving letterbox, ImageNet normalisation | Reuse model pipeline; no grayscale, clinical crop or TXT predictor |
| Augmentation | None for initial exploratory reference | Current scaffold; explicit pilot choice to approve, not a silent replacement of later proposal augmentation |
| Device | Approved compatible Colab GPU for speed | Actual runtime/hardware recorded; CPU verification does not establish GPU reproducibility; any device change binds a new config hash |
| Early stopping / checkpoint | Validation `macro_f1_five_schema`; earliest best on ties | Unchanged trainer; no Test monitoring |

This is **one** ResNet-50 fit, at most 30 epochs with existing early stopping, plus a non-neural majority baseline derived from approved Training labels only. No learning-rate search, fine-tuning, calibration, architecture selection or final Test evaluation in this pilot. Later scientific comparison requires identical approved splits/conditions across both architectures and the proposal's full evaluation stages.

## Validation outputs and limitations

Reuse `validation_metrics`: fixed **5×5 confusion matrix**, actual class support, per-grade recall/F1, separately named five-schema and supported-grade macro-F1, ordinal MAE, quadratic weighted kappa, five-column multiclass Brier and per-grade AUROC. Grade-0 recall/AUROC remain undefined (`null`) without ground-truth support; five-schema macro-AUROC stays withheld if any grade is undefined. Do not replace missing support with a fabricated score. The code's five-schema macro-F1 assigns absent grades zero contribution; disclose this convention beside the supported-grade diagnostic.

Grade-1 Validation has one candidate, so recall can only be 0 or 1 if that record remains eligible; it is not a stable performance estimate. Small selected Validation, many caption-policy exclusions and repeated future tuning introduce uncertainty/selection optimism. Report the actual exploratory cohort and missing support, never a clinical acceptance claim. Majority predictions use only approved Training frequencies; proposed deterministic tie-break is the lowest integer grade among tied largest counts, subject to the same protocol approval.

## Real Grad-CAM after authorisation

Before fitting, fix a small deterministic list from **authorised development** records (for example, first three Validation source IDs lexicographically); never choose examples by attractive heatmaps or Test outcomes. After best-checkpoint restoration, use the existing ResNet `layer4[-1]` target and the predicted class; save original RGB, heatmap and aligned overlay. Record source ID, class, checkpoint/protocol hash and hook-cleanup/finite-output checks. An unsupported-grade prediction must be marked unvalidated. Grad-CAM shows model attribution, not clinical boundaries or independent explanation validity.

## Concrete sequence — not performed

1. Supply and authenticate the signed label/identity/split manifest and exact configuration; confirm documented cached pretrained weights and runtime without silent downloads/installations.
2. Reuse `fit_approved`; train Training only, monitor authorised Validation, save checkpoints/history under a new ignored `models/` run directory. Approval callbacks must authenticate evidence, never always return true.
3. Restore best checkpoint, report Validation and majority-baseline metrics with class support, then generate the preselected development Grad-CAM panels. Save actual results, failures and source/protocol hashes; no fabricated improvements.

The current production API has no real-dataset CLI yet. A minimal owner-approved integration caller is the next small code task **after the manifest/protocol conditions are met**; no trainer rewrite or gate bypass is required. This plan chooses no final model, final split activation, deployment threshold or final-Test evaluation.
