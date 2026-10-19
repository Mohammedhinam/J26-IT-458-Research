# Ordinal tooth-crop comparison — v2 Colab handoff

Date: 17 October 2026  
Status: **Colab T4 run, return verification, and isolated Mac MPS smoke test complete.** Actual results and limitations are in [the returned-results report](vision_roi_ordinal_v2_colab_results.md). This is an isolated follow-up to the completed v1 ROI experiment. It does not change labels, folds, existing checkpoints, or the working PP1 demo.

## Research question

Does a rank-consistent ordinal crop-classifier head improve image-level MGI recognition over the current weighted cross-entropy crop-classifier recipe when both are evaluated on the same 680 Training images and five saved folds?

MGI crop labels have an order from 0 to 4. The CORAL-style arm predicts four threshold answers: whether a crop's grade is above 0, above 1, above 2, and above 3. For example, crop grade 2 becomes `[1, 1, 0, 0]`. The source paper uses a shared score across thresholds to maintain rank consistency; this implementation parameterizes decreasing threshold biases directly so the threshold probabilities stay ordered during training. See the [CORAL paper](https://arxiv.org/abs/1901.07884) and the authors' [PyTorch implementation](https://github.com/Raschka-research-group/coral_pytorch).

This is a comparison of two complete classifier methods, not a loss-only ablation. The weighted-CE arm uses fit-fold inverse-frequency class weights, as in v1. The CORAL arm uses an unweighted mean binary cross-entropy across its four thresholds. No validation score chooses an arm or changes a setting.

## Fixed data and evaluation protocol

- Reuse the exact v1 dataset ZIP: 680 Training images, 53 Validation records present in the package, and no held or Test records. Only the 680 Training IDs enter fitting and scoring; Validation is counted from metadata and not opened by the experiment.
- Reuse five saved folds with 544 fit images and 136 score images per fold. The fold assignment SHA-256 is `e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4`; the source protocol SHA-256 is `2253db0e89aad06a2fe49a90d313b7ae0e08a806b87845d49753b3d9e48dbc4b`.
- Each fold has 6,528 fit crops and 1,632 score crops. A crop stays with its parent image's fold. Existing source class IDs 2–6 map to provisional tooth grades 0–4; the image-level target remains the maximum caption-derived grade 1–4. There are no whole-image grade-0 examples.
- Freeze and reuse the matching v1 fold's YOLO tooth detector for both classifier arms. No detector training is repeated; its earlier localization mAP is carried as context and is not re-estimated.
- Use the same ResNet-18 ImageNet V1 backbone weights, crop generation and normalization, seeds, optimizer, 12-epoch budget, batch size 64, and fold records. The crop-classifier output head and objective differ by arm. No early stopping, augmentation, threshold tuning, or model selection on score folds.
- Score each out-of-fold photo by taking the maximum predicted grade over the same detected tooth ROIs. A photo with no detected ROI remains an incorrect abstention. If any abstentions occur, QWK and ordinal MAE are withheld rather than assigning an unsupported whole-image grade 0.

## What is measured

Image-level results are reported separately for each arm: accuracy, Macro-F1, balanced accuracy, confusion matrix, recall for each supported image grade, quadratic weighted kappa, and ordinal mean absolute error. Tooth-crop results report crop accuracy, Macro-F1, balanced accuracy, confusion matrix, and per-grade recall. The paired 1,000-draw content-group bootstrap is conditional on the saved predictions; it does not include refitting uncertainty or unknown participant overlap.

Image-level AUROC and Brier score are omitted: the photo output is the maximum among tooth grades, and this pipeline does not define a validated photo-level probability distribution. Detector mAP remains a separate localization result and is unchanged because YOLO is frozen.

## Files and Colab inputs

- Notebook: [notebooks/roi_tooth_v2_ordinal_colab.ipynb](../notebooks/roi_tooth_v2_ordinal_colab.ipynb)
- Small source bundle to upload beside the existing files in Drive: [roi_tooth_v2_coral_code_v1.zip](../data/vision/roi_tooth_v1_20261017/ordinal_v2/roi_tooth_v2_coral_code_v1.zip) — 24,857 bytes, SHA-256 `8af0d3596d3afe4586d5407ecedb27754315f606b7c0e8e55c8a39e08abfffdf`.
- Existing data input: `roi_tooth_dataset_v1_oneclass_v4.zip` — SHA-256 `9b1e797f7f593438a5318410ed2aa1cfdd7a66b8db0aac865b3229b63d3a20c8`.
- Existing frozen detector input: `roi_tooth_v1_colab_return.zip` — SHA-256 `ebb41badf4bd2154019dad55ba2f459ad1807c7f42b0722c13d849be2460f9bb`.
- Expected Drive folder: `My Drive/RP-J26-IT-458/roi_tooth_v1/`. It must contain all three exact-name inputs: the v4 dataset ZIP, the existing `roi_tooth_v1_colab_return.zip`, and the new code ZIP. If the v1 return ZIP is absent, upload the verified local copy before running the notebook.
- New resumable output folder: `roi_tooth_v2_coral_colab_run_v1/`.
- New result archive: `roi_tooth_v2_coral_return.zip`. It contains the five CORAL classifier checkpoints, matching frozen detector copies, OOF predictions, metrics, run configuration, and a SHA-256 manifest. Weighted-CE checkpoints stay in the new run folder for comparison. Existing v1 files are never replaced.
- Notebook SHA-256: `418f6ba927252ed3c11ada47caf9655e8409cf5d0d7fbf9044de68938a8f20ba`.

Use a Colab CUDA runtime, with T4 as the intended choice. The notebook validates all three input ZIPs, checks every file in the v1 return manifest, checks the frozen protocol and fold assignment, installs the existing pinned Vision requirements, verifies the official ResNet-18 ImageNet V1 weights, and stops if CUDA is unavailable. It locates `experiment_complete.json` inside the v1 archive after extraction because that ZIP stores files under its `roi_tooth_v1_colab_return/` folder. Drive discovery accepts either the original nested project path or the owner’s root-level `My Drive/roi_tooth_v1` shortcut. Classifier checkpoints are saved to Drive after each epoch and resume only with the same configuration. No files have been uploaded to Drive by Codex.

## Colab return and Mac verification completed

- Colab ran on Tesla T4 for 12 epochs across five fixed folds, with no Test data or validation model selection. The ZIP and all 21 manifest entries passed integrity verification. All 680 OOF IDs, labels, groups and folds matched the frozen manifest; image-level metrics and the paired bootstrap were recomputed independently. See [the actual results](vision_roi_ordinal_v2_colab_results.md).
- CORAL scored 59.71% accuracy / 0.3279 Macro-F1 and recall 0/12, 15/84, 46/223, 345/361 for grades 1–4. Same-run weighted CE scored 59.85% / 0.3241 and recall 0/12, 5/84, 97/223, 305/361. CORAL improved Grade 2 versus matched CE but not overall accuracy; Grade 1 remains unsolved.
- On annotated tooth crops (8,160 held-out fold crops), weighted CE reached 46.59% accuracy / 0.4031 Macro-F1 / 0.3923 balanced accuracy; CORAL reached 40.78% / 0.3738 / 0.4192. These are crop-classifier diagnostics, not detector mAP or full-image accuracy.
- The CORAL fold-00 checkpoint and matching detector loaded on Mac MPS. `Training/00002` returned 12 ROIs and image grade 4, matching its saved OOF prediction; its provisional target is grade 3. The separate overlay calls the displayed detector score a box score, not class confidence.
- Synthetic inference, checkpoint-guard and ordinal regression suite plus existing v1 ROI tests passed: **30 passed** after the inference adapter and research-only overlay were added.
- Seven synthetic ordinal-head tests and the existing v1 ROI tests had earlier passed together: **24 passed** before the real return and adapter work.
- A generated-only CPU pilot trained each arm for one epoch on five synthetic crops, scored five synthetic crops, then resumed from the saved checkpoint successfully. This is software plumbing evidence, not dental-image performance.
- The real package metadata guard passed: 733 allowlisted records, 680 Training, 53 Validation metadata records, five 544/136 folds, 8,160 Training crop rows, and the expected source/fold hashes. No Validation pixels, held data, or Test payload were opened for this check.
- The extracted v1 return bundle passed its embedded file-size and SHA-256 checks for all 19 entries; all five detector checkpoints were present.
- The official cached ImageNet V1 ResNet-18 weight SHA-256 matched `f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec`.
- The ten protected legacy artifacts still match their recorded before-experiment hashes. The v2 adapter is separate from the working PP1 UI/model; no source labels, folds, protected Test, or old results changed. No new upload, commit, or push was performed.

## Student explanation

1. `ordinal_targets` converts one MGI crop grade into four ordered yes/no threshold answers. Grade 2 produces `[1, 1, 0, 0]`.
2. `CoralHead` shares one score between thresholds and keeps threshold biases ordered. That prevents a prediction from claiming “above 2” while denying “above 1.”
3. `_run_fold` fits on the saved `fit_ids`, then scores the matching `score_ids`. Every crop uses its parent photo's fold, which prevents crops from one photo crossing between fit and score.

Likely viva question: **Why use an ordinal head for MGI?**  
Answer: “MGI grades have an order. The ordinal head learns whether each crop is above a sequence of grade thresholds, so a grade-4 prediction has to cross more thresholds than a grade-2 prediction. In this matched run it increased Grade 2 recall, but Grade 3 recall fell and overall accuracy did not improve, so the result is a trade-off rather than a fix.”

Assumption and limits: MGI's grade order is useful for this experiment, but labels remain provisional and are not clinically verified. Grade 1 has only 12 image-level examples; participant independence is unverified; whole-image MGI 0 is absent. Each returned checkpoint was trained on four folds only; no final all-development refit exists. Keep the adapter isolated and do not describe this as a clinical tool or a validated accuracy improvement.
