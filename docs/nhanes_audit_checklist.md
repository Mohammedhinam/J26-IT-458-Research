# NHANES audit checklist — 2026-10-08

Status: Checklist prepared. Audit script not written or run; no local dataset counts obtained. The owner deferred execution to the next session.

## Planned checks

- Load P_DEMO.xpt, P_OHQ.xpt, P_SMQ.xpt and P_DIQ.xpt from ignored data/ with pandas.read_sas(format="xport").
- Report each file's rows, columns, missing SEQN and duplicate SEQN counts. Reject ambiguous joins; never silently deduplicate.
- Count every OHQ850 value, including NaN and special codes. Identify the valid 1/2 audit view without altering source files or recoding the outcome.
- Left-join valid OHQ850 rows to DEMO, SMQ and DIQ on SEQN. Check row count and unique IDs before and after each join.
- Report NaNs, field-specific special codes and distributions/ranges for the 13 predictors from attached AGENTS.md section 6.2.
- Report RIDAGEYR range and any values below 30 or missing; do not exclude them in this audit. The released value 80 means 80 or older.
- Compare observed counts with AGENTS.md references: OHQ rows 14,986; Yes 1,941; No 5,876; valid 7,817. Mark MATCH/MISMATCH only after execution. These are reference values, not local results.
- Print and save the report; test valid labels and row-preserving joins. No modelling, split, imputation or further row exclusions.

## Codebook notes verified during preparation

Special codes are field-specific: OHQ030 uses 77/99 for refusal/unknown, while 7 means never visited. OHQ870 also uses 77/99; seven days is valid. Values above seven days must be reported for review and retained in this audit. RIDAGEYR's 80 is top-coding, not missingness.

Sources checked on 2026-10-08:

- [CDC oral health codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm)
- [CDC demographics codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm)
- [CDC smoking codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm)
- [CDC diabetes codebook](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm)

## Planner task

Title: Component 2 — Prepare NHANES audit checklist
Due: 2026-10-08
Status: Completed (documentation only)
Notes: Prepared the audit checks and checked field-specific CDC coding. No audit execution, local counts, model or data cleaning completed.
Checklist: Review source files; review join/count checks; review special-code rules.
Evidence: Git commit that adds this checklist; use its actual hash from git log.
