# Saved Training680 grade-1/2 learning diagnosis — v1

2026-10-16. **Descriptive analysis only; no new fits, inference, image decoding or label changes.**
Provisional labels; non-clinical; non-final; participant independence unverified.

Three hash-bound saved OOF files have identical 680 IDs, labels and five folds. Support is 12/84/223/361 for MGI1/2/3/4. Aggregate measurements: [JSON](vision_grade12_learning_diagnostic_v1.json). Record-level evidence (288 case-model rows covering 96 grade1/2 records) is local and ignored: `data/vision/grade12_saved_diagnostic_v1_20261016/grade12_cases.csv`.

| Frozen feature + C=1 head | Accuracy | Macro-F1 | Balanced accuracy | Grade1 correct | Grade2 correct | Grade2 → 1 / 3 / 4 errors |
|---|---:|---:|---:|---:|---:|---|
| ResNet, balanced | .475000 | .295114 | .293791 | 0/12 | 17/84 | 2 / 33 / 32 |
| EfficientNet, balanced | .526471 | .341037 | .340590 | 0/12 | 22/84 | 1 / 33 / 28 |
| EfficientNet, unweighted | .532353 | .337377 | .336938 | 0/12 | 19/84 | 0 / 35 / 30 |

These are Training-only OOF results. Historical fine-tuned v3 **53-Validation** accuracy .509434 is a different evaluation population and must not be ranked directly against them. Majority accuracy on these 680 records is .530882; high accuracy alone is uninformative about minority-grade recognition.

## Verified failure pattern

- Grade2 errors predominantly move upward to grades3/4: 65/84 ResNet, 61/84 balanced EfficientNet, 65/84 unweighted EfficientNet. Grade2 appears among the top two predictions in 46/84,49/84,47/84 respectively. This is not uniformly a narrow top-two decision problem.
- Grade1 is never correct. It is second-ranked in 4/12 ResNet cases, but never first or second in either EfficientNet head. Mean true-grade probability is .061920/.021122/.012656. A one-vs-rest AUROC does not establish usable four-way Grade1 classification. Only12 provisional examples are available.
- Mean maximum probability when wrong: .816927/.810040/.822155. Incorrect predictions with maximum probability ≥.8:215/185/192; ≥.9:167/137/147. Fixed bins are diagnostic, not selected operating cutoffs. All three Brier scores are worse than the training-prior baseline.
- Unweighted EfficientNet gains4 correct overall over balanced, while losing3 Grade2 correct. No justified balanced-performance winner was established by that change.

## Interpretation and next action

Observed high-confidence errors justify testing stronger regularisation as a **hypothesis**, not a diagnosis of their cause. Label uncertainty, inadequate class support, representation/scale limitations and selection noise remain plausible; none was causally established. Never relabel/exclude model errors or recover held records using predictions.

The next proposed bounded experiment is six fixed EfficientNet cached-head configurations selected **inside** each outer training fold. It requires new scoped authorization; no real fitting has occurred. Nested validation reduces optimism from this new search, but cannot remove prior backbone/analysis selection or unknown participant overlap. See [scikit-learn's nested-CV explanation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html) and [Cawley & Talbot, 2010](https://jmlr.org/papers/v11/cawley10a.html).

11 generated tests passed,0failed/errors/skipped. Source OOF hashes are recorded in the JSON. All181 holds, NP015,53Validation and Test payloads remain excluded. No clinical/final model claim.
