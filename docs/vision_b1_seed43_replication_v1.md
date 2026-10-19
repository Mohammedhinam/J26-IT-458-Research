# Local B1 last-block seed-43 replication — exploratory result

Date: 2026-10-16 (Asia/Kolkata) · Branch: `vinuthan` · No commit or push.

**Status:** One owner-authorized, local MPS development run completed. It does not improve on the immediately preceding seed-42 last-block result. It reproduces the poor Grade 1/2 recall and shows material run-to-run variation on the same small Validation set. This is not a final model, a five-grade result, or clinical evidence.

> Provisional labels; non-clinical; non-final; participant independence unverified.

> **Interpretation correction,17October2026:** The comparison did not isolate seed alone. The seed42v3reference ran on TeslaT4/CUDA (Python3.13.15,NumPy2.1.3); this run used AppleMPS (Python3.13.5,NumPy2.5.3) as recorded below. Interpret50.94%→43.40%as variation across **seed plus backend/runtime**, not proof of a causal seed/loader-RNG effect. This correction supersedes the seed-only wording in the historical interpretation/teaching notes and runner protocol shorthand; numeric results, saved receipts and hash-bound source remain unchanged. See [investigation](vision_accuracy_reverse_engineering_v1.md).

## What was run

The separate runner `src/vision/exploratory_pilot_b1_seed43_v1.py` reused the hash-verified weighted-v2 best checkpoint and the exact last-block v3 recipe. It changed the seed from 42 to 43, with no seed search. The four-output MGI 1–4 model trained on the same 680 provisional Training records and used the same 53 provisional Validation records for early stopping. It unfroze only the head and `layer4.2` convolution weights; all BatchNorm and other backbone tensors stayed frozen. Batch size 16, head LR .001, final-block LR .00001, balanced Training loss, maximum five epochs, patience two.

The local runtime used Apple MPS: Python 3.13.5, PyTorch 2.11.0, Torchvision 0.26.0, NumPy 2.5.3. No pretrained-weight download occurred; the starting tensors came from the verified v2 checkpoint. Best epoch was **2**. Early stopping ended after epoch 4. Training plus validation took **32.68 seconds**; measured whole-process peak RSS was **607.19 MiB**. The 315 frozen tensors were unchanged; only the two head tensors and three approved final-block convolution tensors changed.

Before fitting, the wrapper reverified the B1 package, exact 680/53 membership and class support, unique content groups, NP015 exclusion, fixed CAM-record presence, held count 181, the v2 archive/checkpoint hashes, and fresh output binding. It loaded only the development bundle. No source JPEG, held record, Test record/label, or CAM array was loaded by the training loop. No new Grad-CAM was run; existing seed-42 explanation artifacts remain historical.

## Results on the same 53 Validation IDs

All three saved prediction files were aligned by immutable ID. The 53 IDs and labels matched exactly across v2, v3 and seed 43; independent scikit-learn calculations reproduced each metric below. Confusion matrices use rows=true and columns=predicted, grades 1–4.

| Run | Accuracy | Macro-F1 | Recall MGI 1 / 2 / 3 / 4 | Macro AUROC | Brier | QWK | Ordinal MAE |
|---|---:|---:|---|---:|---:|---:|---:|
| Weighted head-only v2, seed 42 | 0.3396 | 0.2294 | 0.000 / 0.923 / 0.045 / 0.294 | 0.6700 | 0.7005 | 0.1673 | 0.9057 |
| Last-block v3, seed 42 | **0.5094** | **0.3259** | 0.000 / 0.077 / **0.682** / 0.647 | 0.6273 | 0.6593 | 0.2550 | **0.5849** |
| Last-block replication, seed 43 | 0.4340 | 0.2697 | 0.000 / 0.077 / 0.318 / **0.882** | 0.6565 | **0.6485** | 0.2556 | 0.6981 |
| Grade-4 majority, same Validation records | 0.3208 | 0.1214 | 0.000 / 0.000 / 0.000 / 1.000 | 0.5000 | — | 0.0000 | — |

Seed-43 confusion matrix:

```text
             Predicted MGI
True MGI       1   2   3   4
     1         0   0   1   0
     2         0   1   6   6
     3         0   1   7  14
     4         0   0   2  15
```

Compared with v3 seed 42, seed 43 reduced accuracy by **7.55 percentage points** and macro-F1 by **0.0562**. Grade 2 recall stayed at **1/13 (7.69%)**; Grade 1 stayed **0/1**. Grade 4 recall rose, while Grade 3 recall fell. Compared with v2, the new run has higher accuracy but far lower Grade 2 recall. These are descriptive comparisons on the repeatedly reused 53-record development Validation set; selection optimism and the single Grade-1 case make them unstable. Do not choose a winner from them.

## Interpretation and limits

- The seed replication does **not** fix MGI 1 or 2. It confirms that results move materially with the seed/loader RNG while the training recipe stays fixed.
- No cause is established for the poor Grade 1/2 results. This run cannot separate provisional-label noise, sparse support, image signal, patient overlap, or optimization effects.
- The 680-image EfficientNet nested-CV result (accuracy 0.5221, macro-F1 0.3464) is a different Training-only cross-validation workflow. It must not be ranked directly against this 53-image Validation score.
- The original five-grade MGI 0–4 research target remains unchanged, but this exploratory model has four outputs because no supported whole-image MGI 0 examples were available. Tooth-level MGI 0 boxes do not validate whole-image MGI 0 classification.
- The existing 172-record visual screen remains a review aid: 43 Training +129 Validation, all decisions pending, no AI grades assigned. It does not constitute an individual visual audit of all 733 model candidates. Captions/TXT and all review statuses remain unchanged.
- The best seed-43 checkpoint is an **experimental artifact only**, not a replacement for seed-42 v3 or an approved deployment/final-research model.

## Verification and locations

- Focused tests: **9 passed, 0 failed, 0 skipped**. A generated MPS ResNet forward/backward smoke step also passed before the real run. The first focused test run caught a wrong expected-grade source reference; it was corrected before the training run.
- Exact validation ID/label coverage: 53/53 aligned across the saved v2, v3 and seed-43 predictions; zero Test IDs.
- Local output (ignored): `data/vision/pp1_b1_lastblock_seed43_v1_20261016T234343+0530/`.
- Best checkpoint SHA-256: `2a6381c1f920e1aada04774bab814600764eae6f4b7a281e1a3f4e3cc677516f`.
- Validation-prediction SHA-256: `87c2398e7efe65229cae17aca644b92028fdf1b054c1297185be17ef8db6aa17`.
- Results JSON SHA-256: `8d47e92673d57630bfbd9c534452ce9a9d46c87688db177e7f3bbf3c4a21bfd7`.
- Independent saved-prediction metric cross-check: `data/vision/pp1_b1_lastblock_seed43_v1_20261016T234343+0530/independent_validation_metrics.json`, SHA-256 `008f2ae016af1db0109191b3da6ba96bc12c2966589138cf7ae3ad0502a0a078`.
- Starting v2 best checkpoint SHA-256: `c84936ad7af7366e44e4ae2456c00ba748bae47b983ef9e0df204ce80c386dbf`.
- Frozen B1 development manifest SHA-256: `8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f`.

No original images, annotations, labels, splits, 181 holds, NP015 state, Test boundary, historical results, or research-training approval gate changed. No upload, install, commit, or push.

## Teaching notes

1. `LocalTrainingConfig.validate()` lets this isolated wrapper use MPS while still running the shared CPU-validated training rules. The shared approved-training code was not changed.
2. `validate_records()` rejects Test split names before reading any grade, then checks exact counts, grades, IDs, NP015, and unique content groups.
3. The call to `stage.fit(...)` reuses the tested v3 fitting loop; only the run configuration’s seed differs. The output is a new local checkpoint and 53 saved predictions.

Viva: **Did seed 43 improve the model?** No. Against seed-42 v3, accuracy fell from 50.94% to 43.40%, macro-F1 fell from 0.3259 to 0.2697, and Grade-2 recall remained 1/13. It is a stability finding, not a new winner.
