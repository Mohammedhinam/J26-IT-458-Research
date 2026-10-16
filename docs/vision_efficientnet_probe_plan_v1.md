# EfficientNet-B0 fixed-feature comparison — prospective v1

2026-10-16 · vinuthan · Owner accepted the proposed bounded comparison and separately approved downloading only official EfficientNet-B0 weights. This is not clinical/final-label approval or permission for additional searches.

Freeze before extraction: exactly the prior 680 Training IDs, provisional MGI 1–4 support 12/84/223/361, original content groups and five seed-42 folds (fold SHA e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4). Exclude 53 Validation, 181 held records, NP015, CAM arrays and Test payloads.

Change only the fixed encoder: official EfficientNet_B0_Weights.IMAGENET1K_V1, 1,280 average-pool features, classifier removed, all parameters and BatchNorm frozen in eval. ResNet50 V2 results remain unchanged. Different feature dimensionality is part of this encoder comparison; no causal claim about optimizer or label problems follows from the result.

Use the SAME existing 224×224 B1 extended-float arrays and normalization, without clipping or another resize/crop. This intentionally matches the earlier probe input contract; it is not the torchvision default JPEG resize/crop recipe. No source JPEG decoding, augmentation, higher-resolution export or original data modification.

Fresh StandardScaler → LogisticRegression(C=1, class_weight=balanced, solver=lbfgs, max_iter=2000, random_state=42) inside each training fold. Exactly five classifier fits plus ten fold-derived majority/prior fits. No neural optimization, tuning loop or automatic retry. Stop on convergence warning, non-finite values, changed frozen tensors or any binding mismatch.

Report all prior metrics, confusion/recalls/predicted counts and 1,000 fixed-seed paired content-group bootstrap differences in macro-F1, balanced accuracy and QWK against the saved ResNet probe and baselines. These conditional intervals omit refitting, unknown participant clustering and selection history. Compare using identical IDs/labels/folds, not historical 53-record Validation scores. Missing MGI 0 and scarce MGI 1 remain unresolved; probabilities are uncalibrated.

Official installed torchvision URL: https://download.pytorch.org/models/efficientnet_b0_rwightman-7f5810bc.pth. Validate TLS/source and published filename SHA prefix 7f5810bc; record the full downloaded SHA and bind it before the real run. Do not claim the full digest was independently published. No implicit weight downloads in the runner.

Bindings: current source hashes, config, original manifest, exact selection/folds, measured official weight hash, prior results SHA 7c3f788ecb629d34da2f31b1e8fd29091745fa10c33cff4d9f59ef227fd9edf4, prior OOF SHA 18318980b1cfa216d535633ff57067d4456b39b150335a8abfdf2dc16c8174ea and a new ignored local output directory. Record one actual owner decision, no forged scientific approval.

Focused generated tests precede execution. Current final research-training gates, original labels/splits, Option A failures and all existing work remain unchanged. No commit/push, Test access, cloud upload, final model selection or new real-image Grad-CAM.
