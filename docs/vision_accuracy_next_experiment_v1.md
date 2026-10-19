# Proposed matched EfficientNet adaptation experiment

17 October 2026 · Preview for owner review · **Not implemented or run.**

## Question and reason

Does adapting the final EfficientNet block improve image-level grade recognition compared with fitting only its neural classifier head? The existing 52.21% workflow froze the ImageNet encoder and fitted Logistic Regression heads; it did not fine-tune EfficientNet's neural layers. This proposal tests adaptation without simultaneously changing images, labels, resolution or architecture.

This is an exploratory engineering comparison, not final research-model approval. Original MGI0–4 scope remains; four supported pilot grades do not become a replacement research target. No clinically qualified labels or participant independence are assumed.

## Exact proposed comparison

| Item | Proposed fixed choice |
|---|---|
| Records | Same original680Training records in the hash-pinned B1 bundle; no additional records |
| Labels | Existing provisional image-maximum MGI1–4 labels, unchanged |
| Folds | Same saved five outer known-content-group folds;544fitting/136scoring per fold |
| Inputs | Existing224×224 B1 extended-float arrays, same ImageNet normalization and padding |
| Weights | Existing official EfficientNet-B0 ImageNetV1 cache; verify exact SHA before loading; no download |
| Backend | Mac MPS for **both** arms and all folds, if a generated compatibility check passes; stop otherwise |
| Arm A | Frozen EfficientNet encoder and BatchNorm; train only the four-output neural head |
| Arm B | Same initial encoder/head; train head and the final EfficientNet feature block (`features.8`); freeze all BatchNorm statistics and affine parameters |
| Optimizer | Fresh AdamW per arm/fold; head learning rate0.001, ArmB block rate0.00001; weight decay0.0001 |
| Loss | Cross-entropy with weights derived only from that fold's fitting labels |
| Schedule | Exactly5epochs per fit; batch16; no early stopping, scheduler, augmentation or checkpoint selection |
| Randomness | Seed42; seed again before each arm/fold; matching initialization and fitting-record shuffle order between arms |
| Work limit | Exactly10real neural fits:2arms×5folds;50epochs total; no search or automatic repeat |
| Scoring | Final epoch only; exactly one outer-held score per record per arm |
| Primary outcome | Paired ArmB minus ArmA pooled OOF macro-F1 across the same four supported grades |
| Other outcomes | Per-grade recall/support, accuracy, balanced accuracy, QWK, ordinal MAE, macro AUROC, Brier and both confusion matrices |
| Historical context | Show saved52.21% nested-LR and53.09% majority results separately; they do not isolate the neural unfreezing effect |
| Result rule | Report both arms and every class even if worse. No final-model selection, deployment replacement or accuracy guarantee |

`features.8` is the final EfficientNet feature block, not the whole backbone. The future runner must check the installed architecture and list/hash every trainable tensor before fitting. ArmA and ArmB need independent fresh model instances. The identical small head must be initialized from the same seed before optimizer creation. If these conditions cannot be met, stop rather than silently changing the experiment.

There is no early-stopping choice here: five epochs are a prospectively fixed budget, not an assertion that convergence is reached. Record fitting losses so under-training remains visible; do not use outer scores to extend training. An arm producing non-finite loss/probabilities, changed frozen tensors, convergence/runtime errors, or incomplete OOF coverage fails; preserve the failure and do not retry automatically.

## Execution boundaries

- No53Validation arrays,181held records,NP015, protected Test aliases or final Test images/labels. Validate split metadata before decoding any payload. No source JPEG/CSV/TXT reads or regenerated derivatives.
- No label correction, group/split change, data source addition, tooth crops, object detector, synthetic clinical samples, resolution change, new colour interpretation or antialias activation.
- The real-run entry point must bind owner decision, exact configuration, current runner/dependency source hashes, official weights SHA, manifest SHA, frozen fold membership, both arms and fresh output ID. Require explicit opt-in and a persistent one-attempt marker before fitting.
- Save models/predictions only under ignored `data/`/`models/`. Report aggregate metrics and measured runtime/memory; do not invent elapsed time or use another run as a benchmark.
- First qualify the new runner on generated arrays for arm initialization, exact trainable/frozen tensors, BN, loss, fold isolation, one-score coverage, failure handling and fit budget. This software qualification is not dental performance evidence.
- No installation, weight download, upload, commit or push is included. If existing dependencies/weights cannot support the exact scope, report the missing item.
- This plan does not itself authorize execution or record an owner's acceptance. The owner has requested investigation; the new bounded training configuration is presented here for understanding and a concrete decision, as required by the current handoff and teaching rules.

## What this can and cannot tell us

A positive paired macro-F1 difference would support adapting this block under this exact setup. A negative result would reject that improvement in this run. Neither outcome establishes clinical generalization, participant independence or whole-imageMGI0 support. Unknown participants, provisional labels, scarceGrade1 and earlier development selection remain limitations. This experiment does not test the antialiasing hypothesis; changing both at once would obscure which change mattered.

## Three lines to understand before implementation

1. `model.requires_grad_(False)` freezes the common pretrained starting point; only the declared head/block parameters are re-enabled.
2. `loss = CrossEntropyLoss(weight=fit_fold_weights)(model(images), grades)` teaches image grades using fitting-fold information only.
3. `oof[score_indices] = final_epoch_predictions` records scores from a model that did not train on those records or their known content groups.

Viva: **Why compare two newly trained arms rather than only the old52.21% score?** The old score used a different head and selection procedure. Two matched neural arms help separate the effect of unfreezing the final block from changing the classifier/training workflow.

Owner decision / what I understood: pending.
