# NHANES input and outcome audit

This report is generated from the four local XPT files. It describes data only; it does not train a model, split data, impute values, or remove rows from the joined cohort.
OHQ850 means self-reported previous gum treatment; it is the outcome only, never a predictor. These are unweighted sample counts, not population estimates or disease diagnoses.

## Reproduction and input identity

Command: `.venv/bin/python src/tabular/audit_nhanes.py`
Python: 3.13.5; pandas: 3.0.6.

| Input file in data/ | SHA-256 |
| --- | --- |
| P_DEMO.xpt | 2e46c6c26bf77cd8989f64011ace12cbf42c0f3e03414eb59acc5328c8f87913 |
| P_OHQ.xpt | 1a800f4c796879a1e15bc1fb8ebdccf0f5eec000baf0398a458c78a7da7d40c5 |
| P_SMQ.xpt | 29b7f6c59ab570c042c866312f0eb4329009e85fadbda6f9427a8bf31ecb3a3f |
| P_DIQ.xpt | 79153f799fc2171792771c4aa250029c62807f14915f1f81405b03233b1e5ae3 |

## Confirmed XPORT zero decoding correction

The installed pandas XPORT reader decodes all-zero IBM float bytes as 5.397605346934028e-79. For INDFMPIR and OHQ870 only, each exact artifact is checked against the source bytes before restoring 0.0 in memory. Source files, missing values, and other numbers are unchanged; this is decoding correction, not imputation. Counts below cover full source files, before the valid-label view.

| File | Field | Verified zero cells restored |
| --- | --- | --- |
| P_DEMO | INDFMPIR | 142 |
| P_OHQ | OHQ870 | 2620 |

## Input file dimensions and SEQN checks

| File | Rows | Columns | Rows with duplicate SEQN | Unique non-missing SEQN | Missing SEQN |
| --- | --- | --- | --- | --- | --- |
| P_DEMO | 15560 | 29 | 0 | 15560 | 0 |
| P_OHQ | 14986 | 39 | 0 | 14986 | 0 |
| P_SMQ | 11137 | 16 | 0 | 11137 | 0 |
| P_DIQ | 14986 | 28 | 0 | 14986 | 0 |

Duplicate count means the number of rows whose SEQN occurs more than once. Missing SEQN values are counted separately.

## OHQ850 outcome values

- All value counts, including NaN: NaN: 7133, 2.0: 5876, 1.0: 1941, 9.0: 36
- Valid labels (1 = Yes, 2 = No): 7817
- Missing OHQ850: 7133; other non-missing invalid labels: 36; code 7: 0; code 9: 36.
- Yes (1): 1941 (24.83% of valid labels)
- No (2): 5876 (75.17% of valid labels)
- Codes other than 1 and 2, including blanks, are not valid labels.

## Valid-outcome cohort and left joins

| Stage | Rows | Unique non-missing SEQN |
| --- | --- | --- |
| P_OHQ valid OHQ850 | 7817 | 7817 |
| After left join P_DEMO | 7817 | 7817 |
| After left join P_SMQ | 7817 | 7817 |
| After left join P_DIQ | 7817 | 7817 |

Starting valid P_OHQ rows: 7817. Rows after all three left joins: 7817. No rows lost: **YES**. No row expansion: **YES**.
Age >= 30 diagnostic count in the joined valid-label view: 7817. This is reported only; no age filter was applied.
Age below 30: 0; missing age: 0. Age eligibility agrees with section 6.2: **YES**.

## Predictor checks in the joined valid-outcome cohort

| Predictor | NaN count | Special-code counts | Categorical value counts or numeric min/max |
| --- | --- | --- | --- |
| RIDAGEYR | 0 | None specified | min=30.0; max=80.0 |
| RIAGENDR | 0 | None specified | 1.0: 3795, 2.0: 4022 |
| DMDEDUC2 | 0 | 7: 2, 9: 12 | 2.0: 904, 4.0: 2414, 5.0: 1978, 3.0: 1822, 1.0: 685, 9.0: 12, 7.0: 2 |
| DMDMARTZ | 0 | 77: 8, 99: 2 | 3.0: 1010, 1.0: 4701, 2.0: 2096, 77.0: 8, 99.0: 2 |
| INDFMPIR | 1186 | None specified | min=0.0; max=5.0 |
| OHQ030 | 0 | 77: 1, 99: 25 | 3.0: 1031, 1.0: 2973, 6.0: 1264, 2.0: 1163, 5.0: 621, 7.0: 130, 4.0: 609, 99.0: 25, 77.0: 1 |
| OHQ845 | 0 | 7: 0, 9: 8 | 4.0: 1847, 5.0: 894, 1.0: 853, 2.0: 1687, 3.0: 2528, 9.0: 8 |
| OHQ860 | 0 | 7: 1, 9: 60 | 2.0: 6470, 1.0: 1286, 9.0: 60, 7.0: 1 |
| OHQ870 | 0 | 77: 0, 99: 2 | 7.0: 2692, 0.0: 2602, 4.0: 389, 3.0: 612, 5.0: 292, 1.0: 466, 2.0: 666, 6.0: 93, 99.0: 2, 9.0: 3 |
| OHQ835 | 0 | 7: 0, 9: 91 | 1.0: 1512, 2.0: 6214, 9.0: 91 |
| SMQ020 | 0 | 7: 2, 9: 2 | 1.0: 3444, 2.0: 4369, 7.0: 2, 9.0: 2 |
| SMQ040 | 4373 | 7: 0, 9: 0 | 1.0: 1106, NaN: 4373, 3.0: 2040, 2.0: 298 |
| DIQ010 | 0 | 7: 0, 9: 3 | 2.0: 6159, 1.0: 1405, 3.0: 250, 9.0: 3 |

RIDAGEYR min/max: 30.0 / 80.0. NHANES top-codes age 80 as 80 or older, so a displayed maximum of 80 means 80+.

## Anomalies and skip-pattern checks

OHQ870 non-special responses outside the project's integer 0–7 rule: 3; values/counts: 9.0: 3. Refusal 77 and don't-know 99 are counted separately above. These rows are flagged and retained; no cleaning-day exclusions were applied.
The CDC OHQ870 frequency table lists a released range of 0–9, while the question asks about the last seven days and AGENTS.md requires 0–7. This is a documented range discrepancy requiring review before preprocessing; 8 and 9 are not CDC refusal/don't-know codes.
SMQ040 missing total: 4373. Of these, SMQ020=No: 4369; SMQ020=7/9: 4; SMQ020=Yes: 0. CDC skips SMQ040 after No/refused/don't-know answers to SMQ020. Missing smoking responses are not imputed here.
The valid-label audit view is not a finalized cleaned modelling sample; handling special codes, missing predictors and flagged cleaning-day values remains future work.

## Reference-count comparison

| Measure | AGENTS.md reference | Found | Result |
| --- | --- | --- | --- |
| P_OHQ rows | 14986 | 14986 | MATCH |
| OHQ850 Yes (1) | 1941 | 1941 | MATCH |
| OHQ850 No (2) | 5876 | 5876 | MATCH |
| OHQ850 valid (1 or 2) | 7817 | 7817 | MATCH |

Any MISMATCH above is a direct difference between the documented reference and the observed file count; no discrepancy is explained away here.

## Codebook sources reviewed

- [CDC oral health: OHQ030, OHQ835, OHQ845, OHQ850, OHQ860, OHQ870](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm)
- [CDC demographics: RIDAGEYR, RIAGENDR, DMDEDUC2, DMDMARTZ, INDFMPIR](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm)
- [CDC smoking: SMQ020, SMQ040](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm)
- [CDC diabetes: DIQ010 (3 = borderline is a valid category)](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm)
- [SAS XPORT format: IBM numeric representation](https://support.sas.com/content/dam/SAS/support/en/technical-papers/record-layout-of-a-sas-version-5-or-6-data-set-in-sas-transport-xport-format.pdf)
