# ResNet50 fold-0 controlled adaptation: actual Colab results

Verified locally on 2026-10-18 after the owner explicitly approved and executed the single
bounded Colab pilot. **Full-layer4 adaptation B improves on matched A, but the experiment
does not establish a fix for Grade1, overall accuracy or gingival attention.** Existing PP1
models and demo remain unchanged. No further training, promotion or new data collection ran.

## Preserved return and scope

- Owner return: `/Users/vinuthanvinuthan/Downloads/resnet50_fold0_return_v1.zip`.
- ZIP:1,800,930,004bytes, SHA-256
  `e169edc135e5f6786bf510bd81d5cb3b77125d08edfa944ac5f121f4f694de8c`.
- Independent preservation copy and extracted artifacts:
  `data/vision/resnet50_fold0_pilot_v1_20261018_r2/colab_return_v1_20261018/`.
- Archive contains155files including its integrity JSON and60directory entries. All154
  listed file hashes and streamed ZIP CRCs passed. The supplied archive remains unchanged.
- Original input manifest SHA:
  `1d2a49284a885621aa3b89d059f2be6283f381aa9449db0c4ead8eca206ebec4`.
- Original Training fold0:544fit/136score; fit grades1–4=9/67/179/289;
  score grades1–4=3/17/44/72. All labels provisional. No Validation or Test payloads used.
- Run:TeslaT4, CUDA13.0, Python3.13.15, Torch2.11.0+cu130,
  torchvision0.26.0+cu130, NumPy2.5.3, sklearn1.9.1, Pillow11.3.0.

## Matched experiment actually completed

Official ImageNetV2 initialization was used, not the v3 dental checkpoint. One shared head
warm-up epoch was followed by5epochs of A (head plus final bottleneck) and5epochs of B
(head plus full non-BN layer4). Seed42, batch16, Adam, headLR.001/blockLR.00001,
fitting-only inverse-frequency weights, no augmentation/AMP/early stopping, unchanged cached
B1float32 inputs and all BatchNorm affine parameters/statistics frozen. Score predictions
come from the fixed final epochs. No scoring-based epoch/hyperparameter selection was added.

Epoch checkpoints confirm34optimizer steps per epoch:34warm-up+170A+170B=374total updates.
A has5trainable tensors; B12. Both arms' initial320tensor hashes equal the shared warm-up's
final hashes exactly. Fresh local ImageNet+seeded-head initialization reproduces all320
logged initial tensor hashes, including the fresh four-output head.

Online fitting weightedCE fell from1.4697to.8132 in A and1.4662to.4972 in B. These are
across-update fitting summaries, not fixed-final-state fitting evaluation or proof of a
specific overfitting mechanism. Decreased fitting loss alone does not establish improved localization.

## Independently reproduced 136-image results

| Metric | A: final bottleneck | B: full layer4 | Fitting-majority Grade4 |
|---|---:|---:|---:|
| Correct images |55/136|62/136|72/136|
| Accuracy |40.4412%|45.5882%|52.9412%|
| Macro-F1, grades1–4 |.234132|.317485|.173077|
| Balanced accuracy |.286171|.337734|.250000|
| Grade1 recall |0/3|0/3|0/3|
| Grade2 recall |1/17|5/17|0/17|
| Grade3 recall |38/44|30/44|0/44|
| Grade4 recall |16/72|27/72|72/72|
| Ordinal MAE |.632353|.580882|.639706|
| Quadratic weighted kappa |.170626|.361873|.000000|

B−A:accuracy+5.1471percentage points, Macro-F1+.083353, balanced accuracy+.051563,
MAE−.051471, QWK+.191246. Paired correctness:47both correct,8A-only,15B-only,66both wrong.
The net gain is7images, not15. Grade2 gains are accompanied by a Grade3recall decrease.

A predicts grades1–4 in1/2/112/21images; B in0/17/86/33. Grade3 remains dominant. B improves
balanced recognition relative to A and the majority baseline, while its accuracy remains
below that baseline. This is neither a general overall-performance win nor a Grade1 fix.

Rows=true grades1–4, columns=predicted grades1–4:

```text
A                       B
 0  0  3  0              0  1  2  0
 0  1 16  0              0  5 12  0
 1  0 38  5              0  8 30  6
 0  1 55 16              0  3 42 27
```

Metrics were reconstructed directly from saved probabilities using independent NumPy
confusion/precision/recall/distance calculations, not the runner's sklearn metric function.
Largest summary difference is1.1102230246251565e-16. All136IDs, labels and predicted argmax
grades per arm match the original frozen scoring records; probability shape/order/sums checked.

## Conditional uncertainty diagnostic

Paired fixed-prediction known-content-group bootstrap:1000draws,seed42; groups in this
scoring subset are single-record groups.53draws omitted a supported grade and were skipped;
947valid draws remained. Percentile95%intervals for B−A:

- Accuracy:−1.47to+12.50percentage points.
- Macro-F1:+.0186to+.1536.
- Balanced accuracy:−.0080to+.1190.
- Grade2recall:+5.88to+46.15percentage points.
- Ordinal MAE:−.1324to+.0221.
- QWK:+.0892to+.2985.

These describe the fixed saved predictions and the stated resampling/grade-support condition.
They do not include refitting/seed variation, label uncertainty, unknown participant correlation
or deployment shift. The diagnostic does not establish a clinical or population-level significance claim.

## Actual matched Grad-CAM review

All8predeclared cases were retained; no review case was selected after seeing its attention.
There are32explanations:8images×2arms×predicted/common-A-target. Originals match their
prepared full-frame display previews exactly, metadata are empty, dimensions match, and
every explanation reports `ok`, `layer4[-1]`, and native1×2048×7×7features.

Saved comparison pages arrange existing panels only, preserving their heatmap content:

- [Matched cases page1](../data/vision/resnet50_fold0_pilot_v1_20261018_r2/colab_return_v1_20261018/review/matched_cam_page_1.png)
- [Matched cases page2](../data/vision/resnet50_fold0_pilot_v1_20261018_r2/colab_return_v1_20261018/review/matched_cam_page_2.png)

Columns:original, A predicted-class CAM, B explaining A's target grade, B predicted-class CAM.
Keeping the common target makes changed predictions an explicit part of the comparison.

**Qualitative AI visual observations, not clinician-verified anatomical labels:**

| Case | Provisional grade / A / B | Visible pattern |
|---|---|---|
|Training/00002|3/3/3|A concentrates above upper front teeth; B shifts strongly toward lower-left and opposite peripheral regions. A change does not establish better gingival focus.|
|Training/00007|2/3/3|Both retain upper-left tooth/gum-region attention and a lower-right image-border hotspot.|
|Training/00014|3/3/3|B retains strong left peripheral attention; A also highlights upper front teeth.|
|Training/00016|1/3/3|Both strongly highlight the left lateral/retractor vicinity; neither prediction matches the provisional grade.|
|Training/00023|2/3/2|Common-grade3maps stay similar at the lower-left periphery; B's own grade2map instead highlights the lower-right boundary.|
|Training/00030|4/3/3|Both retain a strong left lateral hotspot extending toward the retractor/mouth edge.|
|Training/00032|4/3/2|Common-grade3Battention remains lateral; its own grade2map moves toward the lower-left boundary.|
|Training/00062|1/3/2|Common-grade3maps highlight the upper-right margin; B's own grade2map highlights the lower-left margin.|

**Conclusion:** peripheral/lip/retractor/teeth-associated attention remains apparent in these
examples. Consistent clinically relevant gingival localization is not demonstrated. Correct
classification (e.g.00023B) does not establish clinically appropriate attention. There are
no verified gingival masks or clinician localization scores, so no gum-overlap percentage,
clinical-boundary accuracy or clinical explanation-quality score is claimed.

Independent CPU reproduction used only these8permitted scoring B1inputs with the returned
final checkpoints.16image predictions agree; max probability difference from CUDA is
1.9073486328125e-6. All32CAMs agree in target/status/geometry; saved-vs-CPU RGB differences
are at most1level out of255, largest panel mean difference.00028715. These are small
backend numerical/display rounding differences, not an attention correction. Checkpoint
tensors, parameter gradient slots and hooks remain unchanged after this inference check.

The calculation/alignment reproduction supports faithful rendering of these learned maps.
It does not prove that Grad-CAM is faithful causal localization or that preprocessing has
no effect on learning. Known B1sampling/antialias hypotheses were intentionally not changed.
Shortcut learning remains a hypothesis requiring a separate controlled study, not a diagnosis
made from the appearance of heatmaps alone.

## Verification and preservation

`scripts/verify_resnet50_fold0_return_v1.py` verifies extraction allowlists, every file hash,
all11checkpoint payloads with restricted `weights_only=True`/CPU loading,3520tensor-hash
entries, allowed trainable/frozen state, per-epoch optimizer steps/finite moments, batch-order
hashes, initial/final stage chain, class weights, metrics and matched inference/CAM results.
The verification script performs zero optimizer steps. Existing29protected artifacts match
their original hashes before/after, including the live ResNet, ROI archives, Questionnaire,
API/UI and previous research results. Dirty working-tree changes were retained.

Evidence directory contains `verification.json`, `paired_diagnostic.json`, before/after
preservation receipts, the original copied ZIP, extracted artifacts and review pages. The
archive's internal hashes are integrity evidence, not a remote machine/security attestation.

## Research decision and handoff

This completes the authorized single-fold experiment and return review. Preserve A/B as
experimental checkpoints; do not replace the PP1 models or label B a verified gum-focused
model. No further epochs, parameter search, new folds or deployment were authorized/run.

The comparison is136original Training score images, not680-image OOF or the53reused
Validation cases; historical52.21%/60.74%/59.71% figures cannot be ranked directly against it.
Labels remain provisional, participant independence unresolved, whole-imageMGI0unsupported
and Grade1support only3scoring images. No clinical validation or supervisor approval inferred.

A qualified reviewer can now assess the eight matched common-target/predicted-target views
without model identity, using relevant/irrelevant/uncertain plus notes. Further claims of
gingival focus need qualified anatomy evidence. Any next learning or preprocessing study
needs a new predefined protocol and explicit bounded approval.

Viva: Why is B not automatically the new demo model? It improved matched A's balanced
classification but missed every Grade1case, remained below majority accuracy and did not
demonstrate consistent gingival attention; the evaluation is one provisional development fold.
Owner understanding: pending; no AI interpretation is clinical ground truth.
