# Development-only age/recorded-sex evidence — 2026-10-16

Signed proposal §3.5. Fixed age bins 30–44, 45–59 and 60–80 (80 means 80+); released sex codes 1/2. No data-driven subgroup selection, model refit or threshold tuning. Reused hash-bound A-reference OOF probabilities and selective development-only demographics.

| Group | N | Yes | AUROC | Brier | Sensitivity @0.50 | Specificity @0.50 |
| --- | --- | --- | --- | --- | --- | --- |
| age_30_44 | 1699 | 379 | 0.722739 | 0.150819 | 0.174142 | 0.971970 |
| age_45_59 | 1828 | 479 | 0.722221 | 0.165733 | 0.281837 | 0.934025 |
| age_60_80 | 2724 | 695 | 0.758777 | 0.155611 | 0.300719 | 0.933465 |
| recorded_sex_1 | 3005 | 730 | 0.743342 | 0.154379 | 0.253425 | 0.944615 |
| recorded_sex_2 | 3246 | 823 | 0.735388 | 0.159943 | 0.273390 | 0.944284 |

JSON includes TN/FP/FN/TP and 1,000 seed-42 respondent bootstrap AUROC/Brier intervals, conditional on saved predictions. These omit model-selection/refitting and complex-survey uncertainty. Group differences do not establish discrimination, fairness or transportability. No final clinical cutoff, protected Test evaluation or causal claim.
