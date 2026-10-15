# PROPOSED: one bounded last-bottleneck stage v3

2026-10-15 · branch `vinuthan`. **Plan only; pending owner decision.** No v3 implementation, qualification or training has started. The two previous one-run authorizations are consumed. Reuse [verified v2 results](vision_b1_balanced_results_v2.md); do not repeat audits or old experiments.

## Rationale and proposal authority

Weighted head-only v2 achieved macro-F1 0.229354 and 18/53 accuracy, but predicted grade 2 for 45/53 cases. Frozen ImageNet features may be insufficient for this task; this is a hypothesis, not a proved cause.

Signed proposal §3.3, page 21, explicitly describes frozen-head training followed by selected-layer fine-tuning, and considers learning rates 0.00001, 0.0001 and 0.001. It does not specify the exact block, simultaneous parameter-group rates, pilot duration or starting checkpoint. Those choices below require owner approval.

## Proposed fixed recipe: one experiment, no search

| Item | Exact proposed choice |
|---|---|
| Starting state | Verified weighted v2 best epoch 1; never the last checkpoint |
| Best.pt SHA-256 | `c84936ad7af7366e44e4ae2456c00ba748bae47b983ef9e0df204ce80c386dbf` |
| Source ZIP SHA-256 | `ab9d61f3d59c807b9181e6937f1099364f3cc06dda6607745bdf5fc11cae8a82` |
| Trainable convolutions | ResNet-50 `layer4.2` only: the final bottleneck; earlier convolutions frozen |
| Head | Existing four-output MGI 1–4 head remains trainable |
| BatchNorm | Freeze ALL running statistics AND affine parameters, including the selected block |
| Optimizer | Fresh Adam; do not reuse v2 optimizer state |
| Learning rates | Head 0.001 unchanged; selected convolution block 0.00001; no weight decay |
| Loss | Same Training-only balanced weights and correct target-weight denominator |
| Data | Same 680/53; all 181 holds, NP015, protected groups and Test remain excluded |
| Preprocessing | Same B1 normalization, letterbox, labels and original splits |
| Bounds | Seed 42, batch 16, maximum 5 ADDITIONAL stage epochs, patience 2 |
| Selection | Validation four-grade macro-F1; same tie-breaking |
| Augmentation/sampling | None |
| Reporting | Previous metrics, support/prediction counts, historical references, 53 saved probabilities and three fixed CAM triplets |

This is a new fine-tuning stage, not a pure one-factor causal experiment: a new trainable block, lower block learning rate and fresh optimizer form its prospective recipe. Starting from v2 best reuses a development-selected checkpoint. Further Validation selection is optimistic; this is not final model selection or independent evaluation. Original five-grade definitions and final Test boundary remain unchanged.

## Minimum implementation if approved

1. Add a separate versioned runner/config. Reuse Dataset, metrics, loss and Grad-CAM. Preserve v1/v2 code, evidence and research gates. Authenticate the starting checkpoint hash, version, schema and context before loading with `weights_only=True`.
2. Explicit trainable-name allowlist: `fc` plus the `layer4.2` convolutions. Freeze every BatchNorm affine parameter and statistic. Exactly two optimizer groups; each parameter belongs once. Measure trainable parameter count and GPU memory rather than inventing them.
3. Generated tests must prove exact initialization, selected-convolution/head updates, unchanged earlier layers and BatchNorm, both learning rates, checkpoint/prediction coverage, determinism, authorization bindings and the existing exclusion/Test boundaries. Require actual Colab PASS with no skips before a real run.
4. Record fresh truthful owner approval and source/protocol/checkpoint/manifest/runtime-proof/output bindings. One exclusive attempt marker; no automatic retry or adjustment. Reuse the existing verified development data and checkpoint; no new pretrained download. Return actual results even if worse, and stop on a safety failure.

## Remaining limitations

Fine-tuning may overfit 680 provisional Training cases. Grade 1 has 12 Training / 1 Validation examples and no correct Validation predictions so far. Clinical label and participant/group approvals remain pending. No whole-image MGI 0 support or clinical colour fidelity is established. This stage cannot resolve those gaps or establish five-class validity. Grad-CAM remains model attention, not a diagnosis or clinical boundary.

**Owner decision required:** approve or reject this exact generated qualification plus ONE bounded last-bottleneck exploratory stage. Nothing is activated by this plan.

## Owner decision update — 2026-10-15

The original PROPOSED/PENDING text above is preserved as the prospective snapshot. Owner subsequently answered **"yes processd ultra venuma?"**, approving this exact generated qualification and ONE bounded real fine-tuning stage. Implementation/handoff now prepared; local and fresh-extraction results28passed/5backend skips. Actual Colab33/33 is still required before training; no v3 real run yet. See [current handoff](vision_b1_lastblock_handoff_v3.md) and truthful [owner record](vision_b1_lastblock_owner_authorization_20261015.json). No clinical, qualified-label, participant-independence or final-research approval is implied.
