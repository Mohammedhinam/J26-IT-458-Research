# Tabular cleaning and preprocessing verification — 2026-10-10

Command: `.venv/bin/python -m src.tabular.preprocess_nhanes`. Rules: `docs/tabular_preprocessing_rules.md`.
The existing audit report is preserved. No classifier was trained, no held-out predictions/metrics were generated, and held-out predictors were not transformed.

| Stage | Rows |
| --- | --- |
| Audited valid OHQ850 view | 7817 |
| Age exclusions | 0 |
| Non-special OHQ870 outside integer 0–7 excluded | 3 |
| Main cleaned cohort | 7814 |
| Development | 6251 |
| Reserved held-out | 1563 |

Excluded OHQ870 values/counts: {9.0: 3}. Participant details are stored only in ignored `data/preprocessing/ohq870_sensitivity_review.csv`.
Main cohort Yes: 1941; No: 5873. Development positive labels: 1553.
Seed: 42; held-out fraction: 0.2; split overlap: 0 participants.
Membership is frozen locally in ignored `data/preprocessing/split_manifest.json`. No split IDs are committed.

## Special-code replacements (before age/cleaning-day exclusions)

| Field | Special codes mapped to missing |
| --- | --- |
| DMDEDUC2 | 14 |
| DMDMARTZ | 10 |
| OHQ030 | 26 |
| OHQ845 | 8 |
| OHQ860 | 61 |
| OHQ870 | 2 |
| OHQ835 | 91 |
| SMQ020 | 4 |
| SMQ040 | 0 |
| DIQ010 | 3 |

## Smoking derivation

| Derived status | Rows |
| --- | --- |
| fewer_than_100_lifetime | 4366 |
| former | 2040 |
| current | 1404 |
| unknown | 4 |

| Derivation/review reason | Rows |
| --- | --- |
| fewer_than_100_lifetime | 4366 |
| answered_followup | 3444 |
| unknown_lifetime_response | 4 |

SMQ040 skipped by design: 4366. These rows have a known fewer-than-100 lifetime category, not imputed current-smoking responses.

## Missing inputs after cleaning, before imputation

| Conceptual input | Missing |
| --- | --- |
| RIDAGEYR | 0 |
| INDFMPIR | 1185 |
| OHQ870 | 2 |
| RIAGENDR | 0 |
| DMDEDUC2 | 14 |
| DMDMARTZ | 10 |
| OHQ030 | 26 |
| OHQ845 | 8 |
| OHQ860 | 61 |
| OHQ835 | 91 |
| DIQ010 | 3 |
| SMOKING_STATUS | 4 |

Conceptual inputs: 12; encoded columns: 47; development matrix: 6251 × 47; all finite: True.
Three numeric inputs plus three missing indicators and codebook-defined categorical/unknown one-hot columns are used. SEQN, OHQ850, survey fields, raw smoking fields and review metadata are absent from the feature matrix.

## Development-fitted numeric medians

| Field | Imputer median/fallback | Entire development column missing |
| --- | --- | --- |
| RIDAGEYR | 56.0 | False |
| INDFMPIR | 2.2649999999999997 | False |
| OHQ870 | 3.0 | False |

Encoded feature names: numeric__RIDAGEYR, numeric__INDFMPIR, numeric__OHQ870, missing__missingindicator_RIDAGEYR, missing__missingindicator_INDFMPIR, missing__missingindicator_OHQ870, categorical__RIAGENDR_1, categorical__RIAGENDR_2, categorical__RIAGENDR_unknown, categorical__DMDEDUC2_1, categorical__DMDEDUC2_2, categorical__DMDEDUC2_3, categorical__DMDEDUC2_4, categorical__DMDEDUC2_5, categorical__DMDEDUC2_unknown, categorical__DMDMARTZ_1, categorical__DMDMARTZ_2, categorical__DMDMARTZ_3, categorical__DMDMARTZ_unknown, categorical__OHQ030_1, categorical__OHQ030_2, categorical__OHQ030_3, categorical__OHQ030_4, categorical__OHQ030_5, categorical__OHQ030_6, categorical__OHQ030_7, categorical__OHQ030_unknown, categorical__OHQ845_1, categorical__OHQ845_2, categorical__OHQ845_3, categorical__OHQ845_4, categorical__OHQ845_5, categorical__OHQ845_unknown, categorical__OHQ860_1, categorical__OHQ860_2, categorical__OHQ860_unknown, categorical__OHQ835_1, categorical__OHQ835_2, categorical__OHQ835_unknown, categorical__DIQ010_1, categorical__DIQ010_2, categorical__DIQ010_3, categorical__DIQ010_unknown, categorical__SMOKING_STATUS_fewer_than_100_lifetime, categorical__SMOKING_STATUS_former, categorical__SMOKING_STATUS_current, categorical__SMOKING_STATUS_unknown

Next: a fresh preprocessing + regularised logistic regression Pipeline fitted within development folds; compare a training-rate baseline using development-only validation. Keep final held-out evaluation deferred.
