# Verified weighted exploratory pilot v2

2026-10-15 · branch `vinuthan`. Evidence checks passed. **Classification remains weak; no final model is selected.**

Original ZIP: `/Users/vinuthanvinuthan/Downloads/pp1_b1_balanced_v2_20261015T150352287886Z_results.zip`.
Size: 185,389,594 bytes. SHA-256: `ab9d61f3d59c807b9181e6937f1099364f3cc06dda6607745bdf5fc11cae8a82`.
[Detailed verification](vision_b1_balanced_results_verification_v2.json).

## Actual experiment

Same 680 Training / 53 Validation candidates, seed 42, batch 16, learning rate 0.001, frozen ResNet-50 backbone and BatchNorm. Only Training-derived balanced loss changed. Maximum 5 epochs, patience 2. The run stopped after 3 epochs; epoch 1 had the highest Validation macro-F1. Epochs 2 and 3 scored 0.144796 and 0.207165, below epoch 1's 0.229354.

## Best-checkpoint Validation comparison

| Metric | Training-majority | Unweighted v1 | Weighted v2 |
|---|---:|---:|---:|
| Accuracy | 0.320755 (17/53) | 0.320755 (17/53) | 0.339623 (18/53) |
| Four-grade macro-F1 | 0.121429 | 0.121429 | 0.229354 |
| Macro AUROC | 0.500000 | 0.659734 | 0.670016 |
| Brier, lower is better | 1.358491 | 0.688751 | 0.700495 |
| Ordinal MAE, lower is better | 0.962264 | 0.962264 | 0.905660 |
| Quadratic weighted kappa | 0.000000 | 0.000000 | 0.167304 |

The separate Training-proportion probability reference has Brier 0.730868 and AUROC 0.5. This differs from the historical one-hot majority baseline. Historical results were reused, not rerun. Weighted metrics were independently reconstructed from the saved 53 probabilities and provisional labels.

| Original grade | Provisional support | Predicted count | Recall | Precision |
|---|---:|---:|---:|---:|
| 1 | 1 | 0 | 0.000000 | Undefined: no predictions |
| 2 | 13 | 45 | 0.923077 | 0.266667 |
| 3 | 22 | 1 | 0.045455 | 1.000000: only one prediction |
| 4 | 17 | 7 | 0.294118 | 0.714286 |

Confusion rows are provisional grades 1–4; columns are predicted grades 1–4:

```
0   1   0   0
0  12   0   1
0  20   1   1
0  12   0   5
```

**Interpretation:** the previous grade-4-only predictions changed into strong grade-2 dominance: 45/53. Macro-F1 increased, but accuracy improved by only one case. Grade 1 was never predicted, and grade 3 recall remains poor. AUROC improved slightly; Brier worsened relative to unweighted v1. This is not a solved classifier, statistically established improvement or clinical success. One provisional grade-1 Validation case makes that grade's estimates particularly unstable. Repeated Validation-based checkpoint and experiment selection introduces optimism.

## Verification completed without another model run

- ZIP CRC, exact 26 files plus 5 directory entries, and all 25 listed payload hashes passed. Initial-head, best and last checkpoint bytes were verified; tensors were not loaded locally.
- All 19 source/test/owner/reference hashes match the frozen code bundle and before/after snapshots. Owner, code, protocol, weights, manifest, runtime-proof and fresh run-ID bindings agree. Embedded synthetic evidence matches the previously verified 27/27 run byte for byte; no tests were repeated.
- All 53 unique Validation IDs and labels match the hash-pinned development manifest. No JPEGs, NPY image arrays or Test labels were read. The unchanged bundle/runner preserves the 181 holds, NP015 and protected groups. The ZIP is not an independent process-access attestation.
- Independent confusion calculations and pairwise AUROC reproduce accuracy, F1, recall, AUC, Brier, MAE and kappa within 1e-12. Maximum probability-sum error is 6.7055e-8. Recomputed CE differs from the reported GPU loss by 4.26e-9; weighted CE agrees within 1e-6. This numerical reconciliation does not change any colour or clinical threshold.
- All three RGB Grad-CAM triplets decode with matching 1200×801 dimensions and no Pillow-visible metadata. Scores match the saved Validation probabilities. Predictions: 00733→4, 00734→3, 00766→2. All explanation statuses are `ok`. This proves artifact/math consistency, not clinical localization. Display previews remain disclosed as clipped; B1 model inputs remain unclipped.
- No training, inference, new pytest run, install, download, commit or push occurred during this review.

## Next single recommendation

The signed proposal §3.3, page 21, describes selected-layer fine-tuning after frozen-head training with smaller learning rates. Prepare one bounded last-bottleneck stage for owner approval, rather than blindly increasing epochs or repeatedly trying weights. [Prospective v3 plan](vision_b1_last_block_plan_v3.md). No v3 code or real run has started.

The original research remains MGI 0–4 with an independent NHANES branch. Whole-image MGI 0 support, qualified labels, participant independence, final research approval and final Test evaluation remain unresolved.

**Provisional labels; non-clinical; non-final; participant independence unverified.**

Viva: **Macro-F1 மேம்பட்டும் model ready இல்லை என்பது ஏன்?** முன்பு எல்லாவற்றுக்கும் grade 4 என்றது; இப்போது பெரும்பாலும் grade 2 என்கிறது. Grade 1/3-ஐ சரியாக வேறுபடுத்தவில்லை; accuracy ஒரு படத்தால் மட்டுமே உயர்ந்துள்ளது.
