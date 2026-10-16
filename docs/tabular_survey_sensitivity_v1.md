# Development OOF survey-weight sensitivity — 2026-10-15

Reused six saved predictions; zero model fits. Selective development-only P_DEMO linkage reused. Frozen manifest/predictions unchanged; no held-out payloads read.

| Setting | AUROC | PR-AUC (trapezoidal) | Average precision | Brier | Sensitivity @0.50 | Specificity @0.50 |
| --- | --- | --- | --- | --- | --- | --- |
| A_reference | 0.734877 | 0.500016 | 0.500790 | 0.152844 | 0.298740 | 0.940795 |
| A_short | 0.732641 | 0.495459 | 0.495696 | 0.153422 | 0.265246 | 0.950116 |
| A_long | 0.733682 | 0.501043 | 0.501805 | 0.153075 | 0.322625 | 0.933954 |
| A_long_regularized | 0.735181 | 0.498748 | 0.499510 | 0.153120 | 0.315386 | 0.933105 |
| A_long_child5 | 0.733447 | 0.500684 | 0.501387 | 0.153291 | 0.326348 | 0.931363 |
| A_balanced | 0.735493 | 0.497455 | 0.498336 | 0.208698 | 0.588973 | 0.768728 |

N=6251; WTINTPRP positive/finite for all rows. Weighted positive share=0.236969. Design coverage: 24 strata / 49 stratum-PSU pairs.
Weights normalized to mean one; normalized weighted confusion counts in JSON are not integer participant counts or population totals. Point sensitivity analysis only: not survey-weighted training, new tuning, final evaluation or nationally representative inference. Complex-design variance and appropriate domain analysis remain pending; respondent bootstrap intervals cannot replace them.
Source: [CDC pre-pandemic demographics and interview weights](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm); signed proposal §3.5.
