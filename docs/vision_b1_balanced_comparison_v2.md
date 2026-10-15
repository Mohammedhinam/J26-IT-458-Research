# Owner-authorized B1 Training-balanced comparison v2

2026-10-15 · branch `vinuthan`. **Implemented and prepared; real weighted results pending.** Owner answered YES to this one-variable comparison after reviewing the actual checkpoint diagnosis. No further routine permission is needed for this exact bounded run once the new synthetic checks pass.

## Actual owner-run Colab qualification — verified

2026-10-15: **27passed,0failed/errors/skipped in8.89s**,TeslaT4/CUDA. All4new backend checks executed and passed. Original4375-byte evidence ZIP preserved in Downloads;byte-identical copy `docs/vision_b1_balanced_runtime_evidence_v2.zip`,SHA256 `c0f249b67b58f0c408579d02162f0c963dfba12cdad64ee2c83c433527180cda`. ZIP CRC,5evidence hashes,exact27unique JUnit IDs/log/summary,and19before/after/code-archive/current hashes agree. Python3.13.15,torch2.11.0+cu130,torchvision0.26.0+cu130,NumPy2.1.3,Pillow11.3.0,pytest8.4.2. No rerun during verification.

This supersedes the local4backend skips as a separate actual run,without rewriting historical preparation results. **Real weighted dental training has NOT run yet.** Next:the already authorized second run cell in the same runtime;no new approval,data upload or weights download. [Verification record](vision_b1_balanced_runtime_verification_v2.json).

## What changes and why

The unweighted reference predicted grade4 for all53Validation images. Actual saved checkpoints show318backbone tensors unchanged and head Adam43/129steps. No run-explaining implementation defect was established. Imbalance is a hypothesis: this experiment tests Training-derived class weights without changing other modeling choices.

|Setting|Approved value|
|---|---|
|Inputs and membership|Same pinned680Training/53Validation; B1float arrays/letterbox unchanged|
|Excluded|All181holds,NP015/protected content groups andTest unchanged|
|Model|Fresh ResNet50 ImageNet1K_V2,head-only,frozen backbone/BatchNorm|
|Original grades|1,2,3,4→four logits; five-grade research schema0–4 unchanged|
|Seed/batch/lr|42/16/0.001,Adam,no weight decay|
|Bound|Maximum5epochs,patience2,same Validation macroF1 tie-breaking|
|Only numerical intervention|Training-only balanced cross-entropy; no augmentation,resampling,unfreezing or preprocessing change|
|Baseline|Preserve/reuse actual unweighted v1 plus Training-majority reference; no baseline retraining|

Weights N/(4*n),in original grade1–4order:14.1666667,2.0238095,0.7623318,0.4709141. Formula reuses `train_pipeline.class_weights`; no Validation-derived weights/caps or fabricated missing MGI0 support. Use sum(w_target*CE)/sum(w_target) per batch. Epoch `loss` remains unweighted CE for comparison; weighted CE is a separate diagnostic. [PyTorch2.11 definition](https://docs.pytorch.org/docs/2.11/generated/torch.nn.CrossEntropyLoss.html).

## Implementation and verification actually performed

- New isolated `src/vision/exploratory_pilot_b1_balanced_v2.py`:reuse v1 Dataset/model/metrics/Grad-CAM and existing checkpoint writer. A separate short fit loop is necessary because historical v1 hardcodes unweighted CE. No historical source is edited or monkey-patched.
- New `verify_b1_balanced_runtime_v2.py`:runs only the27new focused tests;requires exact case IDs,all4backend passes,no skips/failures/errors,actual JUnit XML/logs,source hashes before/after and evidence payload hashes. A PASS boolean alone cannot satisfy the gate.
- Source/code/protocol/official weights/manifest/runtime-verification/output bindings are required. Official cached weights full SHA11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca;no new downloads. One exclusive experiment marker prevents retries under a different run ID. Previous owner scope/hash records cannot authorize this version.
- Save initial head,atomic best/last checkpoints,per-epoch metrics,best-checkpoint53Validation probabilities with original IDs,majority baseline and three original/CAM/overlay triplets. Probabilities are captured during the selected epoch,so no extra Validation inference is needed to save them. Record runtime/protocol/weights/owner/source provenance and result-file hashes.
- Actual local focused result:**23passed,0failed/errors,4skipped**. Missing local torch/torchvision caused the four backend skips;no install performed. Final code ZIP freshly extracted:the same23/4outcome,exact27case IDs,isolated source imports and all19payload hashes unchanged. Original20-file snapshot preserved. This is **NOT Colab27/27or real training PASS**.
- Two Colab cells compile. No dental arrays/JPEGs/Test data opened,model execution performed,real weighted training,inference,upload,download,install,commit or push during local preparation. Cached original result JSON supplies the historical aggregate reference.

Four new backend checks must actually pass in Colab:
1. Weighted loss matches independent scalar/nativeTorch references;all-one weights reproduce unweighted gradients.
2. Generated ResNet50 weighted step,fresh-seed head identity,frozen backbone/BN;uses CUDA when available,weights=None.
3. Generated tiny-model weighted fit,best checkpoint reload,prediction coverage,metric reconciliation and reproducibility.
4. Correct batch-weight denominator,unweighted loss reporting,and no Validation updates.

## Exact next manual Colab steps

Use the **existing completed GPU notebook/runtime**. Do not open a new runtime or rerun its previous training cells.

1. Add ONE new code cell at the bottom;copy the entire [verification cell](vision_b1_balanced_verify_colab_cell_v2.txt). When prompted,upload ONLY [vision_b1_balanced_code_v2.zip](vision_b1_balanced_code_v2.zip),89337bytes,SHA256 `698782ceaf3f387e22a9803036c02cd9188f5184680f16c439684e8b738f0221`.19source/test/aggregate-JSON files plus manifest;no dental images,weights,annotations or per-image labels.
2. It verifies/extracts to a fresh code directory,runs exactly27generated cases,and downloads `vision_b1_balanced_runtime_evidence_v2.zip`. **Any failure/error/skip/dependency STOP means no real run.** Return exact error/evidence;do not retry or auto-install.
3. Only after27passed/0failed/errors/skipped,add ONE further cell with the [authorized run cell](vision_b1_balanced_run_colab_cell_v2.txt). It binds the actual synthetic proof and current cached hashes to the truthful owner record,then runs the already approved ONE comparison. No extra YES required for this scope. Existing data/weights cache is reused;no733-image reupload or weight download.
4. It prints each epoch,creates the three CAMtriplets and actual comparison,and downloads a new resultsZIP with hashes. Return that ZIP;do not repeat the run or tune further if performance is poor. Incomplete output is not a successful result archive.

If the original runtime,data directory or official cache has disappeared,STOP and report that fact. The supplied [reference notebook](vision_b1_balanced_existing_runtime_v2.ipynb) is a copy of the two cells for reading;its first cell intentionally stops in a blank runtime. Do not reset the working runtime to open it.

## Limits and interpretation

Class weighting is not guaranteed to solve collapse;grade1weight14.17 may overfit its12Training examples. Validation has only one grade1 and MGI0 has no whole-image support. Weighted softmax scores are uncalibrated. Report all metrics/prediction distributions even if worse;do not select a final model/cutoff or claim clinical fidelity. Repeated Validation selection carries optimism;finalTest remains sealed,participant independence unknown,andqualified labels/final research approvals pending.

**Provisional labels; non-clinical; non-final; participant independence unverified.**

Three important lines:
- `trainer.class_weights(training_labels,"balanced")[1:]`:Training-only weights,drop the unused0slot without inventing a grade.
- `(losses*weights[targets]).sum()/weights[targets].sum()`:correct weighted batch objective,not division by batch size.
- `base.Dataset` and the pinned manifest keep the same eligible provisional records;loss weighting does not change their labels or splits.

Viva:**Why class weights?** Grade4படங்கள் அதிகமாக இருப்பதால்,குறைவான grades-ன் errors-க்கும் loss-ல் அதிக முக்கியத்துவம் கொடுத்து ஒரே மாற்றத்தைச் சோதிக்கிறோம். அது accuracyமேம்படும் என்ற உத்தரவாதம் அல்ல.
