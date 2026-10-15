# Actual last-bottleneck exploratory pilot v3 — verified results

2026-10-15 · branch `vinuthan`. **The owner-authorized ONE stage completed. Its permission is consumed; no further training/retry is implied.** Engineering execution/integrity checks pass. Scientific quality remains limited; no final-model or clinical approval.

> Provisional labels; non-clinical; non-final; participant independence unverified.

## Actual execution and provenance

- Run: `pp1_b1_lastblock_v3_20261015T155608744170Z` on Tesla T4; Python3.13.15,torch2.11.0+cu130,NumPy2.1.3.
- Original results ZIP remains in `/Users/vinuthanvinuthan/Downloads/pp1_b1_lastblock_v3_20261015T155608744170Z_results.zip`;252199944bytes,SHA256 `c79f16cf59b268f86a5a4c4b6a3482636e374cb67629895f38e55dbb1eaf0d70`. No weights/results ZIP copied into tracked documentation.
- ZIP CRC,27unique files/5directory placeholders,all26payload hashes and22source hashes before/after/archive/current agree. Owner/code/protocol/initial-checkpoint/official-weight/manifest/runtime-proof/fresh-output bindings verified. Embedded synthetic evidence is byte-identical to prior actual **33passed/0failed/errors/skipped** qualification;tests were not rerun.
- Same680Training/53Validation provisional records and B1 preprocessing. All53saved Validation IDs/labels match the hash-pinned existing development manifest;no Test labels accessed. Source datasets,181holds,NP015/protected groups,splits/labels and final-research gates unchanged.
- Started from verified weighted-v2 **best epoch1**,SHA `c84936ad7af7366e44e4ae2456c00ba748bae47b983ef9e0df204ce80c386dbf`. Fresh Adam;8196head parameters at0.001 and4456448last-bottleneck convolution parameters at0.00001. Total trainable4464644;no new weight download or old-run replay.
- Completed the maximum **5additional stage epochs**;bestmacro-F1 at **epoch5**. This run reached its epoch cap;it did not terminate early. Patience2was preserved.
- Measured fit+threeCAM execution41.7868479seconds;peak allocated GPU395552768bytes=377.228515625MiB. This is PyTorch allocated tensor memory,not total/reserved GPU or complete notebook/upload time.

## Same-development comparison

| Actual experiment | Correct /53 | Accuracy | Macro-F1 | Macro-AUROC | Multiclass Brier↓ | Ordinal MAE↓ | Quadratic kappa |
|---|---:|---:|---:|---:|---:|---:|---:|
| Training-majority baseline |17|0.320755|0.121429|0.500000|1.358491|0.962264|0.000000|
| v1 unweighted head-only |17|0.320755|0.121429|0.659734|0.688751|0.962264|0.000000|
| v2 weighted head-only |18|0.339623|0.229354|0.670016|0.700495|0.905660|0.167304|
| v3 weighted final-bottleneck+head |27|0.509434|0.325872|0.627264|0.659312|0.584906|0.254985|

Independent NumPy/pairwise-AUROC calculations reproduce v3 six summary metrics within1e-12. Confusion matrix,F1,recall and per-grade AUROCs also agree. Probability-derived unweightedCE differs by1.08074e-8,consistent with float32logit/probability rounding. WeightedCE1.6807531also agrees within1e-6;class weights come only from Training counts12/84/223/361. This weighted diagnostic worsened versusv2 despite lower unweighted loss/Brier;do not report a universal improvement.

## Grade-specific behaviour and epoch history

| Provisional grade | Validation support | Correct v2→v3 | v3recall | v3F1 | v3AUROC | v3predicted count |
|---|---:|---:|---:|---:|---:|---:|
|1|1|0→0|0.000000|0.000000|0.653846|1|
|2|13|12→1|0.076923|0.142857|0.671154|1|
|3|22|1→15|0.681818|0.566038|0.476540|31|
|4|17|5→11|0.647059|0.594595|0.707516|20|

Rows=true grades1–4;columns=predicted grades1–4:

```text
 0  0  1  0
 0  1 10  2
 0  0 15  7
 1  0  5 11
```

v3predicts grade3/4 for51/53cases. It improves grades3/4argmax recognition but largely loses grade2recognition. Grade3one-vs-rest AUROC remains below0.5;better hard classification does not establish better probability ranking. Paired comparison:7cases correct in both,20newly correct,11previously correct now wrong,15wrong in both. Net gain9correct;this is not an independent significance claim.

| Additional epoch | Training CE | Validation CE | Validation macro-F1 | New best? |
|---|---:|---:|---:|---|
|1|1.165477|1.231766|0.261016|Yes|
|2|1.080095|1.290994|0.144444|No|
|3|1.015960|1.214091|0.273269|Yes|
|4|0.983261|1.257767|0.158333|No|
|5|0.901012|1.149886|0.325872|Yes|

Validation behaviour oscillates markedly. Training metrics are online across updates,not a separate fixed-final-checkpoint Training evaluation. Do not infer a proved failure mechanism or prescribe extra epochs from these aggregates alone.

## Frozen-state and Grad-CAM evidence

Compared saved initial/selected320tensor SHA entries: **315unchanged**;only `fc.weight`,`fc.bias`,`layer4.2.conv1.weight`,`layer4.2.conv2.weight`,`layer4.2.conv3.weight` changed. This agrees with the verified runner's per-epoch/final checks and reported proof. ALL BatchNorm affine/statistics are in the frozen set. This review did **not** independently deserialize checkpoint tensors locally;no Torch installation or model execution occurred. Checkpoint payload hashes and internal ZIP CRC verified:

- Best:`36dd33662e277d3770995bf406f714b71231e77846a4a6a01ef418864259b2ee`.
- Last:`019c1de23d6ce72e98de16135dbb2064f72711de64642d7cd85f9f6e6bfe47e9`.

Three fixed Validation examples produced original/heatmap/overlay PNGs,each1200×801RGB,empty image metadata and explanation status`ok`:00733→grade4,00734→grade3,00766→grade4. Saved probabilities align with the53best-checkpoint predictions;the three original display previews remain byte-identical to v2. Heatmaps indicate model attention,not clinical boundaries. Display previews are disclosed clipped sRGB views;model input remains B1 extended float.

## Interpretation, limits and next step

v3shows a measured exploratory classification improvement,**not a successful validated disease model**. Macro-F1 0.325872 remains below the provisional0.70feasibility target. Macro-AUROC fell fromv2 0.670016to0.627264. Grade1is unsupported by reliable evaluation(only1Validationcase)and grade2recall is poor. No whole-imageMGI0training evidence exists. Qualified labels/participant independence/final manifest remain unapproved. Repeated use of the same53Validationcases and a development-selected initial checkpoint causes selection optimism;no Test or clinical generalization claim is justified. This four-output exploratory configuration does not replace the original five-grade research objective or independent questionnaire branch.

**ONE recommended next action:** freeze these three run records and perform a focused development-only error analysis of grade2↔3/4 confusions using existing53saved probability records and cached annotation evidence,then predefine any further experiment. No immediate extra epochs,hyperparameter search,relabeling,final model declaration or automatic retraining. Any future real run requires a fresh explicit bounded owner decision;clinical labels remain a qualified-review decision.

## Three important blocks / viva

1. `requires_grad_(name in allowed)`: அனுமதித்த head மற்றும் கடைசி மூன்று convolution weights மட்டும் கற்கும்;315மற்ற tensorsமாறவில்லை என்பதை saved hashes காட்டுகின்றன.
2. `sum(w_target*CE)/sum(w_target)`: Training-ல் குறைவான grades-க்கும் கற்றலில் எடை கொடுக்கிறது;எல்லா grade-களும் சரியாக வரும் என்ற உறுதி அல்ல.
3. `Validation macro-F1` selection: epoch5-ஐத் தேர்ந்தெடுத்தது நான்கு grades-ன்F1சராசரி. Accuracy மட்டும் பார்த்தால் grade2தவறுகளை மறந்துவிடலாம்;AUROCவேறு probability-rankingதிறனை அளக்கிறது.

Viva: Accuracyமேம்பட்டாலும் ஏன் final modelஎன்று சொல்லவில்லை? பதில்: அதே சிறிய Validationsetமீண்டும் பயன்படுத்தியுள்ளோம்;grade1/2பலவீனம்,AUROCகுறைவு,provisionallabelsமற்றும்participantindependenceசிக்கல்கள் தீரவில்லை.

[Factual machine-readable verification](vision_b1_lastblock_results_verification_v3.json). No new tests,training,inference,installs/downloads,commits or pushes during evidence review.
