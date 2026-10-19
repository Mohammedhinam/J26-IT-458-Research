# Controlled ResNet50 fold-0 pilot: prepared, not executed

Date: 2026-10-18. Owner authorized local preparation and validation only.
**Use preparation revision r2 below. No cloud upload or real dental/GPU training has occurred.**

## Deliverables

- Notebook: `notebooks/resnet50_fold0_controlled_pilot_v1_r2.ipynb`.
- ZIP: `data/vision/resnet50_fold0_pilot_v1_20261018_r2/resnet50_fold0_pilot_v1.zip`.
- ZIP size: **355,328,546 bytes** (355.33 MB decimal).
- ZIP SHA-256: `60f70f2703a95c870586190705e991ca72dfa6a2e999096a554585b2433665fa`.
- Manifest SHA-256: `1d2a49284a885621aa3b89d059f2be6283f381aa9449db0c4ead8eca206ebec4`.
- Prepared directory: `data/vision/resnet50_fold0_pilot_v1_20261018_r2/package/`.
- Portable runner: `src/vision/resnet50_fold0_pilot_v1.py`.
- Local builder: `scripts/prepare_resnet50_fold0_pilot_v1.py` (refuses existing versioned outputs).
- Independent local checker: `scripts/verify_resnet50_fold0_package_v1.py` (refuses an existing extraction).
- Qualification tests: `tests/test_resnet50_fold0_pilot_v1.py`.

The first preparation directory and notebook without `r2` are preserved historical failed
preparations. **Do not use them:** a preflight local variable caused the receipt to identify
the last array hash instead of the manifest hash. ZIP contents were not corrupt, but the
notebook correctly rejected the wrong binding. The runner was fixed, a generated regression
test added, and r2 built separately. No existing artifacts were replaced to repair this.

## Fixed data membership

| Original split / role | N | MGI 1 | MGI 2 | MGI 3 | MGI 4 |
|---|---:|---:|---:|---:|---:|
| Training / fit | 544 | 9 | 67 | 179 | 289 |
| Training / score | 136 | 3 | 17 | 44 | 72 |
| Total original Training | 680 | 12 | 84 | 223 | 361 |

No Validation image payload, Test payload, unrelated held record, NP015 alias or personal
photo was included. The existing five-fold assignment is reused, not regenerated; its digest
is `e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4`.
Source B1 manifest SHA is `8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f`.

Preparation checks existing protected/uncertain group exclusions. Runtime preflight checks
unique Training IDs, exact fold membership, fit/score group isolation, source-byte hash
overlap, B1 array-hash overlap, four-class support, geometry and every file hash/size.
Content-group isolation is not proof of participant independence; participant IDs remain
unverified. Labels remain provisional caption-derived image maxima, not newly approved labels.
Output index 0 maps to MGI 1, then indices 1/2/3 to MGI 2/3/4. Whole-image MGI 0 is unsupported.

## Matched experiment, awaiting separate execution permission

1. Load only the cached official `ResNet50_Weights.IMAGENET1K_V2` file, SHA
   `11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca`.
   Replace its ImageNet head with four fresh outputs using seed 42.
2. Train that head for exactly one shared warm-up epoch on the 544 fitting images only.
3. Copy the resulting complete state into both arms; use a fresh Adam optimizer per arm.
4. A trains head plus final bottleneck: five tensors, matching the v3 unfreeze boundary.
5. B trains head plus non-BatchNorm full layer4: twelve tensors on actual ResNet50.
6. Each arm trains exactly five epochs. Head LR .001, block LR .00001, batch16, no weight
   decay, augmentation, AMP, early stopping, scoring-based selection or extra fits.
7. Both arms receive identical cached B1 inputs, fitting-only class weights and deterministic
   per-epoch batch orders. All BatchNorm affine parameters and running state remain frozen.
8. Score both final epoch-5 states on the same136 images, only after both fits finish.

Budget: one warm-up plus two five-epoch adaptations = **11 epochs / 374 fitting updates**.
The historical dental v3 checkpoint is never loaded, accepted as initialization, or included
in the ZIP. This is a new fold-local comparison, not a replication of v3's selected run.
Starting cross-validation from v3 would contaminate this fold because v3 saw all680.

## B1 preservation and Grad-CAM

All680 model NPY files are copied byte-for-byte from the frozen B1 bundle and hashed. They
remain extended-sRGB float32, 224-square, aspect-preserving letterboxes; values are not clipped
or re-resized. Existing `colour_b1_prototype.normalize` and `model_pipeline` are copied unchanged
into the portable package. Antialiasing is not changed or evaluated by this comparison.

Before any model inference, eight review cases were selected as the first two score IDs per
provisional grade: Training/00002,00007,00014,00016,00023,00030,00032,00062. For these eight
allowed Training sources, exact source-to-cached B1 array parity passed using the existing
converter. Source bytes were hash-checked before decoding and not modified.

Their full-frame, aspect-preserving display PNGs use the same B1 colour conversion, nearest
sampled preview geometry, max-side1200 and disclosed display-only clipping to RGB8. They have
no PNG metadata. They are never model inputs. This does not establish anonymity.

Future CAM output retains original / heatmap / overlay and `layer4[-1]` geometry. Each case
has both models' predicted-class CAMs plus CAMs for the common A-predicted target. This makes
different explained grades explicit instead of comparing unlabeled different-class maps.
The final native feature map remains7x7; broader training does not increase its resolution.
No gingival masks, attention losses, masked overlays or cosmetic filtering were added.
Heatmaps are model attention, not verified disease localization or gum boundaries.

Clinician review should record an independent assessment before seeing predictions, then
review the predeclared matched views with model identity blinded: relevant / irrelevant /
uncertain, reason and notes. No numerical clinical localization metric is justified without
qualified anatomical ground truth. Tooth/arch boxes are not gingival segmentation labels.

## Evaluation outputs and interpretation

`metrics.json` reports A/B accuracy, Macro-F1 over grades1–4, balanced accuracy, per-grade
recall, confusion matrix with explicit order, ordinal MAE and quadratic weighted kappa.
`predictions.json` contains the same136 IDs, provisional labels, grades and uncalibrated
four-class probabilities for both arms. No results for this experiment exist yet.

Only within-pilot matched comparisons are valid. A136-image fold result must not be ranked
directly against historical680-image OOF52.21%/60.74% results or selected53-image v3 metrics.
The scoring fold has only three Grade1 images. Attractive heatmaps cannot establish improvement;
interpret Macro-F1 and minority recall alongside accuracy and blinded visual findings. No
automatic winner selection, demo replacement, hyperparameter search or full five-fold run follows.

## Actual local validation

- Final generated qualification: **34 passed, 0 failed/errors/skipped**, 2.20s. Tiny synthetic
  CPU optimizer fixtures validate the training machinery; no real dental model was fitted.
- Hand-computed metrics checked, including QWK=11/12 for the generated confusion fixture.
  The first test run had an incorrect expected QWK (.9); the expected value was corrected
  from the independent marginals, not by altering the metric implementation.
- Actual ResNet50 architecture: exact A/B trainable allowlists and frozen BN verified.
- Package: **698 hash/size-verified members + manifest =699 ZIP entries**; CRC passed.
- Exact B1 source/cache parity: **8/8**, source and derivatives kept separate.
- Isolated extraction outside checkout imports with Python `-I -B`, unrelated cwd: passed.
- Official ImageNet loading, one generated224x224 forward producing1x4 finite logits,
  generated real-architecture CAM geometry/target, no changed model tensors: passed.
- Missing-approval run blocked before training/output creation; no CPU fallback: passed.
- Notebook: all **6 code cells parse**; actual preflight cell exercised locally with an
  explicitly simulated permission flag, without upload/install/training. Default flags in
  the saved notebook remain false. Notebook v4.5 schema validated using nbformat5.10.4.
- **29/29 protected existing artifact hashes unchanged**, including all existing model files,
  ROI archives, current UI, API and protected research records.
- Clean Colab installation and CUDA training are **not yet executed or verified**.

Receipts: `preparation.json`, `preflight.json`, `portable_verification.json`,
`notebook_schema_verification.json`, `notebook_cell_local_verification.json`, preserved JUnit
receipts and final preservation receipt under the r2 directory. The portability receipt's
schema field is false because nbformat is absent in the model venv; the separate schema
receipt records the successful validation with the existing base Python installation.

## Future execution order, only after explicit approval

1. Obtain owner approval for this exact cloud upload and bounded CUDA pilot; do not infer
   this from local preparation authorization. Check applicable institutional/privacy clearance.
2. Open the **r2** notebook in a private Colab session and select a CUDA GPU, preferably T4.
3. Enable the cloud flag only after approval. Install the pinned dependencies and restart
   the session if required; re-run its configuration cell and restore approved settings.
4. Manually upload only the r2 ZIP to the runtime Files sidebar. No automatic uploader or
   Drive mount is supplied. Run ZIP SHA, safe extraction and full preflight cells.
5. Verify CUDA and pinned versions. Enable `RUN_TRAINING` and enter the exact approval text
   shown in the notebook only after training approval, then execute the gated run cell.
6. Review A/B metrics and matched CAM views. If completed, optionally create/download the
   return ZIP manually. It contains experimental CAM photos as well as weights/results;
   it does not install anything into the PP1 demo.
7. Keep returned results in a new local experiment directory and verify their return-integrity
   hashes. A later demo integration or full five-fold experiment requires its own decision.

Pinned tested local versions: Python3.13.5, torch2.11.0, torchvision0.26.0, numpy2.5.3,
Pillow11.3.0, scikit-learn1.9.1. GPU needs are unprofiled; T4-class16GB GPU / approximately
12GB host RAM is a reasonable intended environment for224px/batch16, not a measured guarantee.
Allow at least6GB free runtime disk for extraction, epoch checkpoints and return ZIP. No
runtime-duration or new-accuracy estimate is claimed. The notebook records GPU/CUDA/runtime,
seeds, batch-order hashes, initial/final tensor hashes and per-epoch fitting loss/checkpoints.

Every epoch is saved without overwriting prior files. Matching-runtime interrupted fitting
can resume; incompatible provenance, a partial checkpoint or completed run fails closed.
Interrupted scoring/CAM export currently requires inspection and is not automatically
overwritten. Colab VM files are ephemeral: manually download results/checkpoints before ending
the session. No automatic persistent Drive storage has been introduced.

## Licence, privacy and remaining decisions

The [official dataset record](https://data.mendeley.com/datasets/3253gj88rr/1) states CC BY4.0.
That licence permits sharing/adaptation with attribution, a licence link and an indication
of changes. The package includes creator/title/DOI/source/licence and derivative descriptions
in `ATTRIBUTION.json`. It does not imply licensor endorsement. See the
[CC BY4.0 terms](https://creativecommons.org/licenses/by/4.0/).

**Copyright permission and privacy/institutional permission are separate.** The licence does
not establish that all privacy/publicity rights or institutional requirements for processing
patient-derived images in Colab have been cleared. Removing metadata is not proof of anonymity.
This preparation does not declare legal/privacy clearance or clinical approval. Cloud upload
and GPU execution are explicitly still unauthorized; no data has been transmitted by this task.

[Colab's official FAQ](https://research.google.com/colaboratory/faq.html) explains hosted VM
execution, variable GPU availability, ephemeral runtimes and notebook sharing of code/output.
Keep notebook outputs private/omitted when sharing. No personal or newly collected patient
photos are included, and adding any requires separate permission.

**Preparation blockers: none remaining. Execution blockers: explicit cloud/GPU approval;
applicable privacy/institutional clearance not established; actual CUDA compatibility pending.**
Scientific limitations remain provisional labels, unknown participant independence, no
whole-imageMGI0, rareGrade1 and coarse unvalidated attention. These are not reasons to invent masks.

## Teaching notes

- `validate_records`: proves exactly which images fit and score; source-group boundaries stay intact.
- `configure` / `train_epoch`: changes only approved parameters; fitting-only weighted loss gives
  minority grades more weight without fabricating new examples.
- `model_factory` / `train_stage`: official initialization and shared warm-up prevent score-data
  exposure; hashes make changed/frozen tensors and resumable checkpoint identity inspectable.
- Viva: Why not start from v3? It has already seen all680, including the136 scoring images;
  starting from it would invalidate a clean held-fold learning comparison.

What I understood (owner): pending; owner should explain the partition, shared warm-up and
Grad-CAM limitations in their own words before presenting the experiment as their work.
