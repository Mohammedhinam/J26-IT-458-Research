# EfficientNet cached-head class-weight comparison — actual results v1

2026-10-16 · vinuthan · One owner-authorized five-fit cached-feature experiment completed.

**Conclusion:** removing class weights is not a clear improvement. Four additional correct OOF predictions accompany slightly lower macro-F1, balanced accuracy and QWK and poorer Grade2 recall. All five prespecified balanced-versus-unweighted paired intervals include zero. No final model or deployment change.

Provisional labels; non-clinical; non-final; participant independence unverified.

## Prospective design and access

Followed [frozen plan](vision_efficientnet_head_plan_v1.md). Same 680 original Training IDs, labels MGI1–4 support12/84/223/361, 1,280 fixed EfficientNet features and exact five folds,544 fitting/136 scoring. Changed only class_weight=balanced→None; C=1, lbfgs, max_iter2000, seed42 and fold-local StandardScaler unchanged.

Exactly five new classifier fits. Reused balanced, majority and prior OOF probabilities unchanged. No encoder, image array, original JPEG, 53 Validation,181held,NP015, CAM or Test payload access; no weights download, installation, threshold tuning or calibration. Only three old cache files were read. New authorization/config/code/input/output bindings recorded before feature-value loading. No automatic retries.

## Pooled OOF results

| Metric | Unweighted C=1 | Balanced C=1 | Majority | Fold prior |
| --- | ---: | ---: | ---: | ---: |
| Accuracy ↑ | 0.532353 | 0.526471 | 0.530882 | 0.530882 |
| Macro-F1 ↑ | 0.337377 | 0.341037 | 0.173391 | 0.173391 |
| Balanced accuracy ↑ | 0.336938 | 0.340590 | 0.250000 | 0.250000 |
| QWK ↑ | 0.256634 | 0.267839 | 0.000000 | 0.000000 |
| Ordinal MAE ↓ | 0.570588 | 0.588235 | 0.627941 | 0.627941 |
| Macro OVR AUROC ↑ | 0.715040 | 0.711806 | 0.500000 | 0.484326 |
| Brier ↓ | 0.750812 | 0.753383 | 0.938235 | 0.595072 |
| Within-one accuracy ↑ | 0.902941 | 0.894118 | 0.858824 | 0.858824 |

Unweighted: **362/680 correct**, balanced358/680. Difference **4 records / +0.588235 percentage points**. Majority361/680: only **one additional correct record** (+0.147059 percentage points), not a reliable superiority claim; paired accuracy interval versus majority [-0.042647, +0.050037] includes zero.

27 predictions change:11 become correct,7 become incorrect,9 change while remaining wrong. Brier improves by only 0.002571 versus balanced and remains worse than fold prior by +0.155740; outputs are not calibrated clinical confidence.

## Grade errors

| True MGI | Pred1 | Pred2 | Pred3 | Pred4 | Recall balanced → unweighted |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 0 | 3 | 6 | 3 | 0/12 → 0/12 |
| 2 | 0 | 19 | 35 | 30 | 22/84 → 19/84 |
| 3 | 2 | 20 | 100 | 101 | 99/223 → 100/223 |
| 4 | 1 | 24 | 93 | 243 | 237/361 → 243/361 |

Grade2 errors:0→grade1,35→grade3,30→grade4;22→19 correct. Grade1 remains0/12. Predicted counts1/2/3/4:3/66/234/377. No labels corrected/excluded based on these outcomes.

## Paired uncertainty

| Unweighted minus balanced | Point difference | Conditional 95% interval |
| --- | ---: | --- |
| Accuracy ↑ | +0.005882 | [-0.005882, +0.017647] |
| Macro-F1 ↑ | -0.003661 | [-0.016796, +0.007747] |
| Balanced accuracy ↑ | -0.003652 | [-0.016934, +0.007585] |
| QWK ↑ | -0.011205 | [-0.042814, +0.019033] |
| Brier ↓ | -0.002571 | [-0.011346, +0.004933] |

1,000 fixed-seed paired content-group bootstrap draws;0undefined. Conditional on saved OOF predictions; no refitting, participant-independence, multiplicity or selection correction. All680known groups are singletons, unknown participant overlap remains. Three fixed feature/head configurations have now been evaluated on this680Training benchmark; repeated development exploration limits confirmation. Do not rank directly against historical53Validation scores.

## Verification and execution

- **22 focused generated tests passed,0failed/errors/skipped.** Includes independent unweighted sklearn pipeline/scaler arithmetic, deterministic folds/intervals, cache corruption and membership rejection, stale scope/bindings and an end-to-end generated run proving no image/encoder loader is used. Not a full repository test.
- **81 saved-result checks passed,0failed:** independently computed sklearn metrics for all four references, exact metadata/OOF membership, immutable balanced/baseline probabilities, actual fold-local scaler means and five unweighted/converged fitting records.
- Actual solver iterations per fold:117,130,121,116,123; none hit2000/convergence warning.
- Actual runtime **5.21s**, peak macOS RSS **191.97MiB**. No controlled hardware benchmark claim.
- File-open tracing allowed only old features.npz/results.json/oof.npz and new output/evidence paths; all other Vision data reads and input writes blocked. Original cache/source code hashes preserved.
- Probability row-sum error max1.2503005564212799e-07, within established1e-6; saved probabilities unchanged.
- Feature SHA:d8cda6807e7954e2dd8d7cf20be77b46e5063f89910436df294381901231d838
- Fold SHA:e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4
- New OOF SHA:466ed5d278d687c0b90f50bd215629e1828c0122ffd532a3f49d81ef0754a502
- Raw results SHA:fb3816417c43bd77d1aef1ea86cfe238ee656417193dc184f6b4ef8d4415b029

Local ignored outputs:data/vision/training680_efficientnet_unweighted_v1_20261016T152930927867/.
Truthful owner/preflight/execution/verification records:data/vision/training680_efficientnet_head_execution_v1_20261016T152930927867/.
Aggregate [JSON](vision_efficientnet_head_results_v1.json), [runner](../src/vision/efficientnet_head_comparison.py), [generated tests](../tests/test_efficientnet_head_comparison.py). Existing reports, labels, splits, clinical/final-training gates and models preserved. No commit/push.

## Practical interpretation and remaining Vision work

No learning-code bug was demonstrated. Weighting changes the learned decision trade-off on these fixed folds but disabling it does not clearly fix the weak performance/probability quality. Keep both as exploratory evidence; do not promote a winner from a four-record accuracy difference or start another blind sweep.

Remaining:
1. Qualified caption/grade decisions and final content/split approval. All181holds stay excluded:52Training,129Validation. The54near-pair human decisions are already recorded; NP015 and final grouping approvals remain unresolved.
2. Genuine supported whole-image MGI0 evidence and better MGI1 support. No synthetic/fabricated healthy labels or automatic external-dataset mapping.
3. Freeze a scientifically defensible cohort and model/evaluation protocol, obtain required approvals, then perform approved final training/evaluation with protected Test independence. This cached-head CV is not the final five-grade research comparison.
4. Complete approved new-photo runtime activation/compatibility and end-to-end prediction+Grad-CAM integration. Existing factories/trainer/Grad-CAM, actual pilot checkpoints and saved examples are implemented; new cached CV heads are not deployed models. Default arbitrary-photo inference remains inactive.
5. PP1 usability feedback, evidence, demo rehearsal and owner explanations. No clinical/participant-independence claim.

Next practical priority: qualified review/group decisions plus the explicitly provisional PP1 demo integration, rather than more unplanned optimizer changes. Further real runs require separately bounded scope; no approval is fabricated.

## Three blocks — Tamil

1. **class_weight=None:** ஒவ்வொரு sample-க்கும் சம loss weight; அரிய grade-க்கு கூடுதல் weight இல்லை. இதனால் அனைத்து grades-க்கும் சம முக்கியத்துவம் கிடைத்தது என்று பொருள் இல்லை.
2. **fresh scaler+classifier inside each fitting fold:** score செய்யும் image தகவல் scaler/model fitting-க்கு போகாது.
3. **cached balanced predictions + paired OOF:** ஒரே680images-ல் weight மாற்றத்தின் trade-off மட்டும் ஒப்பிடப்படுகிறது; புதிய image features எடுக்கவில்லை.

Viva: **Does slightly higher accuracy mean this is the better model?** இல்லை. இங்கே4கூடுதல் correct இருந்தாலும் Grade2 recall மற்றும் macro-F1 குறைந்தன; interval-லும் தெளிவான winner இல்லை.
