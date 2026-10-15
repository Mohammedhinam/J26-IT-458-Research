# Vision model/Grad-CAM implementation — synthetic runtime verified

Date: 2026-10-14. Branch: `vinuthan`. **Code only; no dataset training or real-image inference.**

Current verification: owner completed Colab v1, **8 passed, 0 failed, 0 errors, 0 skipped**. Saved JSON/logs/JUnit XML and all source hashes were checked against the current code and upload bundle. See [consolidated evidence record](vision_runtime_verification_results.md) and `vision_runtime_evidence.zip`. Historical local skips below are retained; the synthetic backend-verification blocker is resolved, while dental training/evaluation and human approvals remain pending.

Authority: supplied AGENTS.md §§3/6.1/8/13 and signed Component 2 proposal §§3.2–3.5 and explanation validation, pp.18/20–23. RGB → image-level maximum MGI → Grad-CAM remains independent of NHANES. No proposal, grade definitions, source labels, memberships, review statuses or manifest was changed.

## Implemented interfaces

| Function | Purpose / boundary |
|---|---|
| `preprocess_rgb(image, size=224)` | Explicit RGB PIL input; aspect-preserving letterbox; ImageNet normalisation; retains unchanged source RGB and inverse geometry |
| `model_spec(architecture)` | Explicit pretrained source identifiers, last-convolution-block target and five MGI output order |
| `make_model(...)` | ResNet-50 or EfficientNet-B0, five fresh output units; optional initial backbone freezing; defaults to cached pretrained weights with implicit downloads blocked |
| `map_model_output(logits)` | Five finite logits → schema grade 0–4 and uncalibrated softmax scores; no calibrated-confidence or clinical-validity claim |
| `aggregate_gradcam(activations, gradients)` | Class-gradient channel weights, positive weighted activations and normalised spatial map |
| `align_cam(...)`, `render_gradcam(...)`, `gradcam_views(...)` | Remove input padding, restore original H×W, and produce separate original/heatmap/overlay RGB arrays without changing source colours |
| `class_gradcam(model, target_layer, prepared, class_index=None)` | One class logit, autograd gradient to selected feature block; defaults to the same forward pass's argmax class; no optimiser or parameter update |
| `approved_training_records(manifest)` | Proposed integration contract: reject unapproved/unverified or cross-split-content records; return only approved Training metadata; does not open images or grant approval |

Weights interfaces follow official [ResNet-50](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet50.html) and [EfficientNet-B0](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html) documentation. Named choices are `ResNet50_Weights.IMAGENET1K_V2` and `EfficientNet_B0_Weights.IMAGENET1K_V1`. No weights were loaded or downloaded. The five-unit MGI classifier head is freshly initialised and **untrained**; pretrained ImageNet features do not establish dental validity.

Class-gradient weighting follows the [Grad-CAM paper](https://arxiv.org/abs/1610.02391). Targets are ResNet `layer4[-1]` and EfficientNet `features[-1]`. Hooks are removed and every module's original train/eval flag restored even on error. `autograd.grad` obtains feature gradients without accumulating parameter gradients; a gradient-enabled input supports frozen feature extractors. These synthetic backend paths passed in the owner's Colab v1 run; local torch remains absent.

## Preprocessing and display choices

Both architectures use the same RGB 224×224 letterbox with ImageNet mean/std. This is an implementation choice for preserving the complete image and inverse alignment, **not** Torchvision's stock ImageNet resize/centre-crop transform. Review and freeze it in the future approved experiment protocol before training. It changes no clinical target or dataset membership. No augmentation or training hyperparameter selection is implemented.

Padding is normalised mean colour, not new gingival content. Source pixel orientation is kept as provided; caller-side image loading/EXIF orientation handling must be specified consistently at integration. The CAM is resized to input coordinates, padding is cropped out, then the map is resized to original dimensions. Original RGB is returned unchanged; only the separate heatmap/overlay uses pseudocolour. Overlay alpha defaults to 0.45 as a display parameter, not a decision threshold. Zero attention leaves source pixels untinted.

Zero-positive, spatially constant and padding-only signals are reported explicitly as `no_positive_signal`, `no_spatial_contrast` and `padding_only_signal`. A heatmap is model attention, never a clinically validated inflammation boundary. Grad-CAM needs autograd and is deliberately rejected inside `torch.inference_mode`; a surrounding `torch.no_grad` is overridden locally. Current implementation expects floating-point32 model/input operation.

## Approval gate, not a training-ready manifest

This model module adds no training loop or dataset loader; the separate scaffold is documented in [vision_training_scaffold.md](vision_training_scaffold.md). A future manifest adapter must provide externally qualified-approved label/split provenance (`status=approved`, reviewer/date and explicit label/split approval), verified MGI labels, original image identifiers and approved analysis content-group IDs/splits. The helper rejects cross-split groups and unresolved labels and never returns evaluation rows as training metadata. The field contract is an integration proposal, not a created/frozen research manifest or reviewer authentication mechanism; approval authenticity must be verified externally.

Existing PROPOSED grouping artifacts, 54 pending near-pair decisions, 274 unapproved caption-policy candidates and unresolved annotation records cannot supply approved training eligibility. Participant independence, exact-group annotation conflicts and absent image-level MGI 0 support remain unresolved. All five definitions stay intact; there are no fabricated grade-0 examples or claims that five-class learning/evaluation is presently valid.

## Historical local focused verification

**32 passed, 0 failed, 6 skipped.** Only synthetic images/arrays and synthetic metadata were used.

- Passed: RGB shapes/channel order/normalisation/source preservation; landscape/portrait/square geometry; complete five-index mapping and finite-score checks; class-specific CAM algebra; padding removal/spatial alignment; original/heatmap/overlay shape and colour preservation; explicit degenerate-explanation statuses; approval/leakage metadata guards.
- Skipped: two actual architecture forward/target checks, two uncached-weight download guards, frozen-backbone class-autograd consistency/state/hook check, and zero-signal/inference-mode backend check. All six require unavailable torch; torchvision is also unavailable. These are **not passed backend tests**.
- Runtime used: bundled Python 3.12.14, NumPy 2.3.5, Pillow 12.3.0, installed pytest 9.1.1 from the project environment via a pure-Python path append. No package installation or prior audit/test rerun.
- `.venv` Python 3.13.5 has NumPy/pytest but lacks torch, torchvision and Pillow. Bundled and system Python also lack torch/torchvision. No alternative backend or mock neural-network performance is substituted.

## Remaining integration requirements

1. Synthetic backend verification is complete: six prior backend plus two architecture Grad-CAM cases passed in Colab v1. No repeat run is needed for this unchanged snapshot. Obtain documented pretrained weights through an explicitly approved/cached route before future authorized dental training; keep model artifacts ignored.
2. Complete qualified visual/annotation adjudication and approve duplicate/participant grouping, final labels and a frozen split/eligibility manifest. Resolve missing-MGI-0 feasibility without silently changing definitions.
3. Approve/freeze preprocessing, source orientation handling, documented pretrained source, initial head-only stage and later training protocol. The separate trainer's synthetic BatchNorm/checkpoint/resume paths passed in Colab v2; this does not approve a dental experiment protocol.
4. After a trained dental checkpoint exists and evaluation authorization is given, verify real explanations, parameter-randomisation sensitivity, calibration/confidence and eventual qualified spatial review. No held-out image is used now.

Teaching: preprocessing stores the inverse image geometry; the classifier output order is exactly MGI 0–4; Grad-CAM differentiates the selected class logit rather than a different class or a clinical label.

Viva: Why does a five-output head not prove five-class validity? The outputs encode the intended definitions, but reliable examples, approvals and measured learning/evaluation support are separate requirements.

No installs, original image/CSV/TXT payloads accessed for model development, actual dataset training, model/test-image inference, commits or pushes. Existing tracked/untracked work and historical evidence are preserved.
