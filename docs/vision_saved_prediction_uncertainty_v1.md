# Saved Vision v2/v3 uncertainty — 2026-10-15

Added conditional uncertainty to the completed Grade-2 diagnosis; no new experiment, image decoding, model inference or label adjudication.

| Metric | v3 minus v2 conditional 95% interval |
| --- | --- |
| accuracy | 0.037736 to 0.301887 |
| macro_f1 | -0.006352 to 0.210820 |
| ordinal_mae | -0.490566 to -0.132075 |
| macro_auroc | -0.119841 to 0.031671 |

1,000 paired outcome-stratified resamples of the same 53 saved predictions, seed42. Image sampling assumes independence that remains unverified; fixed-label support and repeated checkpoint/model selection are not accounted for. These are descriptive sensitivity intervals, not final research or clinical confidence bounds.

| Grade | Correct / support | Conditional exact-binomial recall interval |
| --- | --- | --- |
| 1 | 0 / 1 | 0.000000 to 0.975000 |
| 2 | 1 / 13 | 0.001946 to 0.360297 |
| 3 | 15 / 22 | 0.451276 to 0.861353 |
| 4 | 11 / 17 | 0.383284 to 0.857903 |

Grade1 has only one Validation example. Its stratified bootstrap cannot measure class variation; report the broad conditional binomial interval instead, still subject to unverified independence/provisional labels. MGI0 has no supported full-image sample; no MGI0 performance can be estimated.
Keep v1/v2/v3 as exploratory evidence. No email is required to continue the working PP1 software demo, but internet research cannot adjudicate uncertain clinical labels or establish participant identity. The 181 holds remain excluded. Next new real Vision experiment needs an explicit bounded protocol/authorization and Colab; this analysis does not activate one.
