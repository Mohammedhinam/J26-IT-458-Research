# NHANES cleaning and preprocessing rules — 2026-10-10

Sources: attached AGENTS.md sections 5, 6.2 and 12; supplied proposal `RP-IT23311022 (2).pdf`, pages 19–20 and 22; verified `docs/nhanes_audit.md`. The proposal's NHANES rules agree with the requested cleaning stage. The audit report remains unchanged: 7,817 valid source labels is historical audit evidence, not the post-exclusion sample size.

## Cohort and exclusions

- Reuse the audited XPT loader, including its source-byte-verified zero decoding fix, and its one-to-one left joins. Do not rerun the audit report generator.
- Require valid OHQ850 labels (1=Yes, 2=No), unique non-missing SEQN and adult eligibility (age >=30). Log any age exclusions separately. The audited cohort contains no missing age or age below 30.
- Exclude non-special OHQ870 values outside integer 0–7 from the main analysis. The audit found three OHQ870=9 records. CDC's released range is 0–9, but the project explicitly requires 0–7 for the main analysis. Retain excluded rows separately for sensitivity review; do not clamp 9 to 7 or automatically re-include it.
- Keep missing predictors and refused/don't-know responses in the cohort. Apply the field-specific rules below rather than dropping rows for missing inputs.

## Field-specific special codes

| Fields | Codes mapped to missing | Valid values retained |
|---|---|---|
| DMDEDUC2, OHQ845 | 7, 9 | 1–5 |
| DMDMARTZ | 77, 99 | 1–3 |
| OHQ030 | 77, 99 | 1–7; 7 means never visited |
| OHQ860, OHQ835, SMQ020 | 7, 9 | 1, 2 |
| SMQ040 | 7, 9 | 1, 2, 3 |
| DIQ010 | 7, 9 | 1, 2, 3; 3 is borderline |
| OHQ870 | 77, 99 | Integer 0–7; other non-special answers tracked as exclusions |
| RIAGENDR | None | 1, 2 |
| RIDAGEYR, INDFMPIR | None | Age remains top-coded at 80; income ratio 0–5 including zero |

Unexpected non-missing codes in other fields cause a clear error instead of silent recoding. Outcomes are never imputed. Numeric missing values remain missing until development-only fitting.

## Smoking skip logic

| SMQ020 | SMQ040 | Derived SMOKING_STATUS |
|---|---|---|
| 2 (fewer than 100 lifetime cigarettes) | Skipped/missing | `fewer_than_100_lifetime` |
| 1 | 1 or 2 | `current` |
| 1 | 3 | `former` |
| 1 | Missing/special | Missing → `unknown` during categorical preprocessing |
| Missing/special | Missing/special | Missing → `unknown`; lifetime response is unknown |
| 2 or missing | An answered valid follow-up | Inconsistent → `unknown`, flagged for review |

Keep raw SMQ020/SMQ040 and separate skip/review-reason metadata. A skipped SMQ040 is not imputed or described as an unanswered current-smoking question. The raw two smoking fields are replaced by the one derived field in predictors; unknown is a missing-data category, not a fourth known smoking state.

## Split, fit and predictor boundary

Sort participants by SEQN, then use stratified `train_test_split(test_size=0.2, random_state=42)` on OHQ850 mapped to 1/0. Freeze participant membership in ignored `data/preprocessing/split_manifest.json`; later runs reuse it and reject incompatible cohorts/settings. Development and held-out IDs must be disjoint and cover the cleaned cohort.

The 12 conceptual inputs are RIDAGEYR, INDFMPIR, OHQ870, RIAGENDR, DMDEDUC2, DMDMARTZ, OHQ030, OHQ845, OHQ860, OHQ835, DIQ010 and SMOKING_STATUS. SEQN, OHQ850, OHQ555Q, survey fields, skip/review metadata and raw smoking fields are excluded by an explicit allowlist. WTINTPRP/SDMVSTRA/SDMVPSU stay in the cohort for later survey sensitivity analysis.

Use a sklearn ColumnTransformer with small numeric/categorical Pipelines:

- Numeric age, income ratio and cleaning days: median imputation, then StandardScaler. Add a fixed missing indicator for each numeric field so newly missing inputs can be represented. If a development numeric column is entirely missing, sklearn's documented zero fallback retains it; this is recorded rather than estimated from held-out data.
- Categorical fields: explicit constant `unknown` followed by one-hot encoding. Legal categories plus `unknown` are fixed from the codebooks, not discovered from held-out values. This keeps an explicit unknown column even if a category was absent in development data.
- Fit imputer/scaler/encoder on development rows only. Tonight transform development data only; held-out rows remain reserved. Synthetic tests exercise transform behaviour without final test evaluation.

For later cross-validation, create a fresh preprocessing transformer inside each model Pipeline so every fold fits only its training rows. Do not cross-validate on today's already-transformed development matrix. Calibration, thresholds and class weights will also be chosen within development data.

## Local artifacts and reproduction

Run `.venv/bin/python -m src.tabular.preprocess_nhanes`. Save only aggregate results to `docs/tabular_preprocessing.md`. Store the split manifest and participant-level sensitivity-review CSV under ignored `data/preprocessing/`; never commit them. No classifier, predictions, held-out metrics or model file is produced at this stage.

Sources: [CDC oral health](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm), [demographics](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm), [smoking skip logic](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm), [diabetes](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm), [sklearn SimpleImputer](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html), [OneHotEncoder](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html).
