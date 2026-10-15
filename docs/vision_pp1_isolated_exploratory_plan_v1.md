# Isolated PP1 exploratory Vision pilot — PLAN v1

2026-10-14, branch `vinuthan`. **Design only: no pilot code, image package, training or inference executed.**

Purpose: an explicitly authorised engineering demonstration using provisional development labels, separate from qualified-approved research training. Preserve RGB → image-maximum MGI 0–4 → Grad-CAM and the independent NHANES branch. This is not clinical validation, a final model or participant-independent performance evidence.

Authority: AGENTS.md §§3/6.1/7/13; signed Component 2 proposal §§3.2–3.5 (PDF pp.17/21–22); strict-clean development DRAFT v1; current model/Grad-CAM/trainer. The proposal's frozen-head stage supports the architecture, but unapproved labels/unknown participant identity **do not satisfy its final scientific validation requirements**. This separate provisional pathway requires explicit owner opt-in; supervisor endorsement is needed before presenting it as proposal-aligned research evidence. Owner opt-in never substitutes for qualified approval.

## 1. Separate pathway; production gate unchanged

Proposed new, small `src/vision/exploratory_pilot.py` entry point; no changes to `fit_approved`, `approved_partitions`, model factory, Grad-CAM or historical records.

- Require explicit `--exploratory-provisional`, a recorded owner-authorisation artifact and exact cohort/config/bundle hashes before real images open. Missing/mismatched acknowledgement fails closed.
- Use a clearly named provisional dataset adapter, reusing `preprocess_rgb`, model factory, `TrainingConfig`, seed/freezing functions, metrics and the existing internal `_fit` loop. Do not call `fit_approved` with dummy callbacks, fabricate reviewer/participant metadata or set a manifest to approved.
- `candidate_mgi_grade` becomes a numerical tensor target **only in the exploratory runtime adapter**; preserve its provisional provenance. The original DRAFT's approved `mgi_grade`, participant IDs, analysis splits and approval flags remain unchanged/null/false.
- All notebook output, result JSON, checkpoint context and CAM captions carry `EXPLORATORY / PROVISIONAL LABELS / NON-CLINICAL / NON-FINAL / PARTICIPANT INDEPENDENCE UNVERIFIED`. Checkpoints live only in a new ignored `models/exploratory_pp1/<run-id>/`, with a distinct experiment identity. No automatic promotion/resume into approved research runs.
- Keep negative tests proving the existing production API still rejects this DRAFT and pilot artifacts; the exploratory wrapper must also refuse absent opt-in, Test/noncandidate records and wrong hashes.

The internal loop is already shared by approved integration and synthetic tests; this wrapper adds an explicitly different authorisation/context boundary instead of rewriting optimisation. The new wrapper itself will need focused verification; the historical 59 Colab synthetic passes do not verify it.

## 2. Physical data isolation

Source DRAFT: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/strict_clean_development_draft_v1_20261014/development_manifest_draft_v1.json`.

Frozen source SHA-256: `b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1`.

Use its exact **680 Training + 53 Validation = 733** technical candidates. Keep **181 held records**, all multi-image groups, protected-Test groups and both NP015 groups out. No new representative, partial-caption policy, resplit or label selection. Verify Training/Validation content-group disjointness and protected/uncertain group exclusion before packaging and again before running. Unknown participant identity remains explicitly unverified; do not invent IDs.

After separate packaging authorisation, create a new ignored local bundle containing:

- Only 733 development RGB derivatives, a candidate-only provisional manifest, opaque blocked-group metadata, per-file SHA-256 and a versioned bundle checksum.
- Aspect-preserving lossless RGB PNG derivatives with long side 224, using the existing preprocessing resize dimensions/LANCZOS convention. At runtime, reuse existing letterbox/normalisation. Verify tensor equivalence to original preprocessing; do not crop, grayscale, regrade or overwrite originals.
- Full-resolution originals for **three preselected eligible Validation IDs: `00733`, `00734`, `00766`**, for aligned Grad-CAM display only; never move them into Training. Selection is lexical and fixed before performance is known.
- Code-only files for the existing model/trainer plus the new wrapper, focused tests and notebook. No original dataset RAR, shared full QA/caption cache, CSV/TXT annotation tree, held images or Test files/labels.

Use a **fresh Colab runtime**, upload only this allowlisted bundle, and extract into a new `/content/pp1_exploratory_v1/`. **No Drive mount, local-Mac runtime or full repository/data mount.** Test data is physically absent from the supplied runtime inputs. If an original-data mount or unexpected bundle entry is present, stop; do not automatically delete user files.

Loader paths must stay inside the dedicated bundle root; reject absolute paths, traversal, symlinks, unexpected files, duplicates, noncandidate IDs and missing/altered bytes. The runner receives no original dataset root, Test path or general dataset-download capability. This isolation is for the sanctioned workflow, not a claim of security against arbitrary unrelated notebook code.

## 3. One small proposed experiment

| Setting | Proposed fixed value |
|---|---|
| Architecture / schema | ResNet-50, five logits in MGI 0–4 order |
| Pretrained source | `ResNet50_Weights.IMAGENET1K_V2`; documented cached checkpoint, `allow_download=False` |
| Trainable layers | Classification head only; backbone and BatchNorm frozen |
| Seed / batch size | `42 / 16` |
| Learning rate / optimiser | `0.001 / Adam` |
| Epoch cap / patience / min_delta | **`5 / 2 / 0.0`** |
| Class weighting / weight decay | `none / 0.0` |
| Augmentation / fine-tuning | None in this initial engineering pilot |
| Checkpoint monitor | Existing Validation five-schema macro-F1; earliest best on ties |
| Runs / tuning | **One fit**, no search, calibration, EfficientNet comparison or additional seeds |

This explicitly smaller profile replaces neither the earlier 30-epoch proposed approved-research profile nor the final proposal protocol. All values require owner authorisation before execution. Record actual runtime/device/thread and source hashes; deterministic execution can fail on unsupported kernels—stop rather than silently disable it. No automatic CPU fallback, batch reduction or hyperparameter change.

At 680/53 and batch 16: **43 Training + 4 Validation batches/epoch**, at most **215 optimisation batches + 20 Validation batches**. Early stopping can reduce this. Majority baseline uses provisional Training frequencies only, lowest-grade tie-break; currently its predicted grade is 4. Run the same Validation metrics for it. Never select a model/policy from Test data.

## 4. Honest outputs and explanations

Report actual class support, fixed 5×5 confusion matrix, per-grade recall/F1, separately named five-schema/supported-grade macro-F1, ordinal MAE, quadratic weighted kappa, per-grade AUROC and multiclass Brier. Retain the existing metric conventions; do not rewrite metrics to improve the presentation.

**MGI 0: 0 Training / 0 Validation.** No fabricated examples, oversampling, healthy substitution or four-class remapping. Grade-0 recall/AUROC remain undefined; five-schema macro-AUROC withheld where undefined. Five logits/softmax scores do not mean five classes were validated. Any grade-0 prediction must be tagged unsupported, never described as a confirmed healthy mouth.

**MGI 1: 12 Training / 1 Validation.** Report support; one-record recall is unstable. Results measure agreement with provisional labels on a small selected subset, not clinical accuracy or participant-independent generalisation. Reusing Validation for early stopping introduces selection optimism. Softmax remains uncalibrated; no disease-risk/confidence claim.

After restoring best checkpoint, reuse `class_gradcam` at `layer4[-1]` for the three fixed Validation originals. Explain the predicted class; preserve colours/alignment and hook cleanup; produce original/heatmap/overlay plus checkpoint/provenance IDs. No attractive-example selection or Test inference. CAM is model attribution, not clinical ground truth or inflammation boundaries.

## 5. Colab resources and access

Actual candidate file metadata totals **4,427,774,122 bytes (4.12 GiB)**; no RGB files were opened for this estimate. The three selected original JPEGs total **16,932,897 bytes (16.15 MiB)**. Resized 733 RGB images require at most **105.23 MiB of 224×224 RGB pixel payload**, before PNG/ZIP overhead/compression. A **250 MiB data-bundle planning allowance** is reasonable, not an observed archive size; measure the real package after creation.

Use one available Colab GPU session. **Planning budgets**, not measured consumption: approximately 8 GiB host RAM, 8 GiB GPU memory and 1 GiB free working disk for bundle, code, documented weights and a few checkpoints. Record actual peak usage; stop on resource failure. Do not promise a GPU type or wall-clock duration. [Colab FAQ](https://research.google.com/colaboratory/faq.html) confirms fluctuating hardware/limits; benchmark the first authorised epoch before quoting a completion time.

TorchVision lists the chosen weight file as about **97.8 MB** ([official ResNet-50 documentation](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet50.html)). Cache availability was **not checked** today. The previous Colab tests used `weights=None`, so they do not prove pretrained weights are available. If missing, stop and obtain explicit approval for the exact official source/version/checksum or a supplied approved checkpoint. No silent download or random-weight substitution. Detect installed dependencies; reuse compatible versions, no automatic reinstalls.

## 6. Required authorisation and next executable step

Owner must explicitly authorise **implementation/local packaging** first: new isolated provisional wrapper, allowlisted development image copies/derivatives and code notebook, preserving the current production gate. This is not label/manifest approval and does not authorise training automatically.

Before a pilot run, record a separate owner authorisation bound to candidate manifest + bundle + exact configuration + weight-source hashes, acknowledging:

1. All labels remain provisional/unqualified; participant independence unverified; known/possible content overlaps stay held.
2. This single bounded run is non-clinical/non-final, not approved scientific evaluation; MGI 0 unsupported and MGI 1 scarce.
3. Only packaged development data may be used; Test inaccessible; no policy activation, qualified-approval forgery, scope/five-grade change or promotion to a final model.
4. Documented cached weights, checked runtime and new ignored output location; no unexpected downloads/installations.

This task authorises **design only**. No authorisation artifact is signed or fabricated here. Retained final-research labels/participant/split approvals remain pending; owner pilot opt-in cannot fulfil those gates. Supervisor confirmation is required before describing this exploratory departure as accepted proposal research evidence or approved final training.

**Next executable step after implementation authorisation:** add only the thin exploratory wrapper, allowlist bundle builder and new opt-in Colab notebook; test on synthetic fixtures first (absent opt-in, path/Test rejection, group/NP015 holds, source hashes, original production-gate rejection and resize equivalence). Prepare—not run—the development bundle. Show preflight hashes/contents and resolve the weight-source requirement before separately authorising the one pilot.

Teaching: opt-in authorises an engineering experiment, not clinical labels; Test isolation means no Test files supplied, not merely ignoring a label column; missing-class metrics stay undefined. Viva: **Why keep the approved-training gate if this pilot has a separate path?** Its purpose is different and disclosed; exploratory permission must never be mistaken for qualified research approval.
