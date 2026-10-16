# Focused v2 vs v3 Grade-2 prediction diagnostic

2026-10-15 · branch `vinuthan`. **Read-only saved predictions; no new training/inference or image decoding.**

> Provisional labels; non-clinical; non-final; participant independence unverified.

## Scope and provenance

Only `validation_predictions_best.json` and its existing payload-hash receipt were read from the two previously verified owner result ZIPs. Archive sizes agree with prior records; full archive hashes/CRC/source audits were reused, not repeated. No images, checkpoints, Training/held/Test data, captions or annotations were opened. Existing predictions/metrics/labels/splits remain unchanged.

| Run | Prediction payload SHA-256 | Previously verified result archive |
|---|---|---|
| v2 | `591eee408184fa96e20391d20113abf812b2c89a4dc0286bdbd2fb00489856a0` | `pp1_b1_balanced_v2_20261015T150352287886Z_results.zip` |
| v3 | `ad96de0c279092de2d0ff6206a93121d94023b4b4fa9148693a1769b77e29172` | `pp1_b1_lastblock_v3_20261015T155608744170Z_results.zip` |

**Alignment PASS:** 53 unique identical immutable `Validation/NNNNN` IDs; identical provisional labels and probability-column order `[1,2,3,4]`. Supports `[1,13,22,17]`. Stored argmax predictions agree with finite normalized probabilities. Rows were aligned by ID, not assumed file order. Raw logits are not saved; this analysis uses the available probabilities without reconstructing logits. A separate independent read-only arithmetic check agreed.

## Side-by-side confusion matrices

Rows=true provisional grades1–4; columns=predicted grades1–4. Counts, not percentages.

```text
       v2                   v3
     1  2  3  4           1  2  3  4
1 |  0  1  0  0      1 |  0  0  1  0
2 |  0 12  0  1      2 |  0  1 10  2
3 |  0 20  1  1      3 |  0  0 15  7
4 |  0 12  0  5      4 |  1  0  5 11
```

| True grade | Support | Correct v2→v3 | Recall v2→v3 | Predicted count v2→v3 |
|---|---:|---:|---:|---:|
| 1 | 1 | 0→0 | 0.0000→0.0000 | 0→1 |
| 2 | 13 | 12→1 | 0.9231→0.0769 | 45→1 |
| 3 | 22 | 1→15 | 0.0455→0.6818 | 1→31 |
| 4 | 17 | 5→11 | 0.2941→0.6471 | 7→20 |

Overall correct predictions18/53→27/53; macro-F1 0.229354→0.325872; macro-AUROC0.670016→0.627264; Brier0.700495→0.659312. Earlier verified metric records are reused unchanged. Grade3 gains14 correct and Grade4 gains6;Grade2 loses11. Better overall hard classification and Brier coexist with poorer Grade2 recall and lower macro-AUROC.

## Exact Grade-2 failure pattern

| Saved v2 prediction → saved v3 prediction | Number of true Grade-2 cases | IDs |
|---|---:|---|
| 2→2 | 1 | 00796 |
| 2→3 | 10 | 00778, 00784, 00794, 00798, 00805, 00808, 00809, 00816, 00823, 00824 |
| 2→4 | 1 | 00822 |
| 4→4 | 1 | 00807 |

**v2:**12/13correct;one Grade2→4 error. **v3:**1/13correct;10 Grade2→3 and2 Grade2→4 errors;none→1. Eleven formerly correct cases become wrong;none are recovered.00796remains correct;00807was already wrong and remains4.

Grade2 precision rises12/45=0.2667→1/1=1.0000 **because v3 predicts Grade2 only once**;recall collapses12/13=0.9231→1/13=0.0769. Grade2 false positives fall33→0 while false negatives rise1→12. Perfect-looking precision on one prediction is not a reliable success claim.

## Per-case probabilities and margins

All13 rows below have provisional true grade2;IDs have the `Validation/` prefix. `Top1/Top2` lists `grade:probability`;Top1 is the stored prediction. `Δtop`=Top1−Top2;`m2`=p2−max(other grades),positive when grade2 strictly wins. These are score gaps,not calibrated confidence or clinical severity. Four decimal places are displayed;calculations and the companion JSON use saved precision.

| ID | v2 p2 | v2 Top1 / Top2 | v2 Δtop | v2 m2 | v3 p2 | v3 Top1 / Top2 | v3 Δtop | v3 m2 |
|---|---:|---|---:|---:|---:|---|---:|---:|
| 00778 | 0.4453 | 2:0.4453 / 3:0.2400 | 0.2052 | +0.2052 | 0.4096 | 3:0.4356 / 2:0.4096 | 0.0259 | -0.0259 |
| 00784 | 0.3551 | 2:0.3551 / 3:0.2643 | 0.0908 | +0.0908 | 0.2256 | 3:0.4732 / 4:0.2604 | 0.2128 | -0.2475 |
| 00794 | 0.3700 | 2:0.3700 / 3:0.2562 | 0.1138 | +0.1138 | 0.1294 | 3:0.5454 / 4:0.2884 | 0.2570 | -0.4160 |
| 00796 | 0.3830 | 2:0.3830 / 4:0.2684 | 0.1146 | +0.1146 | 0.4734 | 2:0.4734 / 4:0.2916 | 0.1818 | +0.1818 |
| 00798 | 0.3904 | 2:0.3904 / 3:0.2583 | 0.1321 | +0.1321 | 0.1683 | 3:0.6059 / 4:0.1734 | 0.4325 | -0.4376 |
| 00805 | 0.3733 | 2:0.3733 / 4:0.2761 | 0.0973 | +0.0973 | 0.1438 | 3:0.4478 / 4:0.4034 | 0.0444 | -0.3040 |
| 00807 | 0.2834 | 4:0.3059 / 2:0.2834 | 0.0225 | -0.0225 | 0.0859 | 4:0.5071 / 3:0.2866 | 0.2205 | -0.4212 |
| 00808 | 0.3889 | 2:0.3889 / 3:0.2597 | 0.1292 | +0.1292 | 0.0928 | 3:0.5451 / 4:0.2498 | 0.2953 | -0.4523 |
| 00809 | 0.3911 | 2:0.3911 / 3:0.2416 | 0.1495 | +0.1495 | 0.1485 | 3:0.5376 / 4:0.2585 | 0.2791 | -0.3891 |
| 00816 | 0.3432 | 2:0.3432 / 3:0.2623 | 0.0809 | +0.0809 | 0.0784 | 3:0.4663 / 4:0.3563 | 0.1100 | -0.3879 |
| 00822 | 0.3029 | 2:0.3029 / 4:0.2675 | 0.0354 | +0.0354 | 0.1833 | 4:0.4041 / 3:0.3225 | 0.0816 | -0.2208 |
| 00823 | 0.3614 | 2:0.3614 / 4:0.2515 | 0.1100 | +0.1100 | 0.2126 | 3:0.4311 / 4:0.3435 | 0.0877 | -0.2185 |
| 00824 | 0.3981 | 2:0.3981 / 3:0.2638 | 0.1343 | +0.1343 | 0.1774 | 3:0.6172 / 4:0.1877 | 0.4294 | -0.4397 |

| Grade-2 subset summary | v2 | v3 |
|---|---:|---:|
| Mean p2 | 0.368161 | 0.194547 |
| Median p2 | 0.373322 | 0.168258 |
| Mean signed m2 | 0.105425 | -0.290675 |
| Median signed m2 | 0.113791 | -0.387942 |
| Mean Top1−Top2 gap | 0.108888 | 0.204462 |
| Grade2 in top2 |13/13|2/13|
| Grade2 rank1/2/3/4 counts |12/1/0/0|1/1/8/3|

p2decreases12/13times;only00796increases. Mean change−0.173614(−17.3614probability percentage points);median change−0.220685. Mean signed m2changes+0.105425→−0.290675. Average class-probability vectors shift `[0.135072,0.368161,0.248943,0.247823]`→`[0.054815,0.194547,0.455633,0.295005]`:the largest mean increase is Grade3.

00778is one narrow Grade2/3 reversal:p2=0.409648,p3=0.435576,m2=−0.025928. The other11misclassified Grade2cases have m2between−0.218538and−0.452288;Grade2 is ranked3rd/4th in11/13cases. Therefore most errors are not tiny top-two boundary flips. This is a descriptive pattern,not a statistically established population-wide tendency.

## Observations versus possible causes

| Status | What the evidence supports |
|---|---|
| Verified | Same53records/labels/mapping;Grade2 scores and ranks shift downward in12/13cases,mainly in favour of Grade3. |
| Verified | v2over-predicts Grade2(45/53);v3under-predicts Grade2(1/53)and assigns51/53toGrades3/4. |
| Not established | Class imbalance caused this shift;imbalance exists historically,but these files cannot isolate its effect. |
| Not established | Unfreezing,head learning rate,fresh optimizer,preprocessing or label errors caused it;there is no causal ablation or new visual/annotation evidence here. |
| Unavailable | Raw logits,gradients and per-image intermediate-epoch trajectories;only selected-checkpoint probabilities are saved. |
| Limit | No supported whole-imageMGI0;single Grade1 Validation sample;alllabels provisional;participant independence unverified. Repeated checkpoint/model choices on the same53cases create selection optimism. |

## One proposed next action — stability experiment plan, not an automatic fix

These predictions do **not** justify choosing a corrective learning rate,loss weight,threshold,relabeling or extra epochs. The defensible next question is whether the observed class trade-off is sensitive to the run random seed.

**Recommend owner review of ONE predeclared seed-replication experiment only:**reuse the pinned v2best initialization and exact v3recipe,but change run seed42→43. Keep the same680/53/B1/Training-only weights/five trainable tensors/frozenBatchNorm/two learning rates/batch16/max5epochs/patience2/Validationmacro-F1 selection. Reuse the existingseed42reference;do not rerun baselines or search seeds. Seed43is a prospective arbitrary replication choice,not selected for good Validation outcomes. Report every grade and all saved53probabilities,including worse results.

Rationale:the broad rank redistribution on this small development Validation sample warrants a stability check before further tuning. This tests run-seed sensitivity,not the root cause or a guaranteed repair. A global seed changes all RNG streams used by the runner;it must not be presented as an isolated sampler-order effect. One additional seed cannot establish general reproducibility,clinical performance or unbiased final model selection. **Fresh explicit owner approval is required before implementing/running another real experiment.** Any such replication needs a separately versioned run scope/configuration,new hash-bound authorization and fresh one-attempt guard;never rerun the consumed v3cell or bypass its marker. Nothing is implemented or run here;all previous one-run permissions are consumed.

## Simple Tamil / viva

- ID மூலம் alignசெய்வது:இரண்டு models-லும் ஒரே படத்தைத்தான் ஒப்பிடுகிறோம்;row orderதவறால் முடிவு மாறாது.
- `m2=p2−max(other)`எதிர்மறையானால் Grade2-ஐவிட வேறொரு grade scoreஅதிகம்.12படங்களில் இப்படித்தான் உள்ளது.
- Grade2recallகுறைந்தாலும் overallaccuracyஉயரலாம்:Grade3/4-ல்20correctஅதிகரித்தது;Grade2-ல்11correctகுறைந்தது;net+9.

Viva:இந்தanalysisகாரணத்தைக் கண்டுபிடித்துவிட்டதா? பதில்:இல்லை;probabilities/ranksஎப்படி மாறின என்பதைத்தான் உறுதிப்படுத்துகிறது. காரணத்தைச் சோதிக்க prospective controlled experimentதேவை.

[Exact numeric diagnostic](vision_grade2_v2_v3_diagnostic_v1.json). Source files/ZIPs unchanged;no training,inference,image decoding,Test/held access,installs,downloads,uploads,commit or push.
