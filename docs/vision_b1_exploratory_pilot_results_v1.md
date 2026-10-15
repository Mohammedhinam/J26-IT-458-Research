# B1 MGI1–4 exploratory pilot v1 — actual owner-run Colab results

2026-10-15, branch `vinuthan`. **Execution/evidence integrity PASS; classification feasibility not established.** This was the first authorized real development-image pilot, not final scientific evaluation or clinical validation.

## Actual evidence

Original archive preserved at `/Users/vinuthanvinuthan/Downloads/pp1_b1_mgi1to4_20261015T135216375748Z_results.zip`.
Size185285944bytes; SHA256 `4aa51bc52b3f313363dd88c3e56a299fb8c48a9c27f53bb1ae5114cf7f3181c4`.
[Verification record](vision_b1_exploratory_pilot_results_verification_v1.json).

- ZIP CRC and exact membership:19files,including18hash-listed payloads plus their hash index;4directory entries. All18hashes pass, including best.pt and last.pt. Checkpoint tensor contents were NOT loaded locally; no inference/training rerun.
-20source hashes before/after match the verified code ZIP and current repository. Owner record matches actual recorded YES. Protocol/code/manifest/measured official weights hashes and fresh run ID agree.
- Runtime evidence:TeslaT4,Python3.13.15,torch2.11.0+cu130,torchvision0.26.0+cu130,NumPy2.1.3,Pillow11.3.0. GPU preflight's dental_training_performed=False describes its earlier synthetic check, not the subsequently completed dental pilot.
- Recorded weights:official ResNet50 ImageNet1K_V2,full SHA `11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca`. Cached-status helper's download_attempted=False means that helper only inspected cache; it does not mean the authorized preceding download never occurred.
-680Training/53Validation; no Test in the versioned runner, test_used=False in result.181holds/NP015/protected-group exclusions remain bound by the pinned package and unchanged verified code; result ZIP alone is not an independent execution/access attestation.
-3epochs completed under max5/patience2,all Validation Macro-F1 ties; best epoch1 retained. Training loss1.069945→0.984904→0.940768; Validation loss1.173950→1.204403→1.226434. No automatic retry or protocol change.

## Selected best-checkpoint Validation result

| Metric | ResNet50 best epoch1 | Training-derived majority baseline |
|---|---:|---:|
|Accuracy|0.320755|0.320755|
|Four-grade macro-F1|0.121429|0.121429|
|Macro AUROC|0.659734|0.500000|
|Multiclass Brier (lower better)|0.688751|1.358491|
|Ordinal MAE|0.962264|0.962264|
|Quadratic weighted kappa|0.000000|0.000000|

Validation support grades1/2/3/4:1/13/22/17. Each of the53Validation argmax predictions is grade4 in all3epochs. Per-grade recall0/0/0/1. Classification does not beat majority, despite softer probabilities providing improved reported AUROC/Brier over the hard one-hot baseline. This does not identify the causal mechanism or establish robust discrimination: tiny/provisional Validation,one grade1case and early-stopping selection limit interpretation.

All6Training/Validation confusion tables were checked independently for row supports,accuracy,macro-F1,per-grade recall,ordinal MAE and weighted kappa. Per-image probabilities/labels are not included in this archive, so AUROC/Brier are recorded actual runner results, not independently recomputed here. No new pytest or GPU tests were run during this evidence review.

## Grad-CAM evidence

Exactly9RGBPNG files:original/heatmap/overlay for Validation/00733,00734,00766. All decode,have matching1200×801dimensions per triplet,no Pillow-visible metadata,and match recorded hashes. All3recorded explanation_status=ok,predicted grade4. File integrity/geometry success does not establish meaningful dental localization. These are disclosed clipped display previews of B1 inputs,not clinically validated boundaries or source-colour-identical images. No clinical interpretation performed.

## Interpretation and next step

Engineering flow now works end to end on authorized real development data. The current head-only classifier is not useful for distinguishing all four grades at argmax. Imbalance (Training12/84/223/361) may contribute, but no cause is proven and more epochs alone are not justified by this evidence.

**Next single recommended task:** a focused read-only diagnosis of the collapsed predictions using the saved result and existing input/label/head-training code; then predefine one Training-derived class-weighted head-only comparison if checks pass. Do not automatically rerun,unfreeze,change epochs,labels,split or select a final model. A further real experiment needs its own bounded owner authorization. Preserve this run as the unweighted reference. Validation used repeatedly is development evidence,not unbiased final evaluation.

**Provisional labels; non-clinical; non-final; participant independence unverified.** No whole-image MGI0 support or healthy-detection claim; original five-grade research objective and independent questionnaire branch unchanged.

Viva: **Why can AUROC improve while every predicted grade is4?** AUROC probability ranking-ஐ அளக்கும்; final grade அதிக probability உள்ள class-ஐ எடுக்கும். Other grades-க்கு probabilities வேறுபட்டாலும்,grade4 எப்போதும் அதிகமாக இருந்தால் எல்லாப் படங்களுக்கும் grade4தான் வரும்.
