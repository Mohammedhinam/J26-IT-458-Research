"""Synthetic checks for cleaning, structural skips and development-only fitting."""

import numpy as np
import pandas as pd
import pytest

from src.tabular.audit_nhanes import PREDICTORS
from src.tabular.preprocess_nhanes import (
    FEATURES, NUMERIC, clean_cohort, derive_smoking_status,
    make_preprocessor, model_inputs, split_participants,
)


def sample_frame(n=20):
    frame = pd.DataFrame({name: np.ones(n) for name in PREDICTORS})
    frame["SEQN"] = np.arange(1, n + 1)
    frame["OHQ850"] = [1, 2] * (n // 2)
    frame["RIDAGEYR"] = 40.0
    frame["SMQ020"] = 2.0
    frame["SMQ040"] = np.nan
    frame["WTINTPRP"] = 1000.0
    frame["OHQ555Q"] = 999.0
    return frame


def test_special_codes_preserve_valid_seven_borderline_and_zero_without_mutating_input():
    raw = sample_frame()
    raw.loc[0, ["OHQ030", "DIQ010", "INDFMPIR", "OHQ870"]] = [7, 3, 0, 7]
    specials = {"DMDEDUC2": 7, "DMDMARTZ": 77, "OHQ030": 99, "OHQ845": 9,
                "OHQ860": 7, "OHQ870": 99, "OHQ835": 9, "SMQ020": 9, "DIQ010": 9}
    for name, value in specials.items():
        raw.loc[1, name] = value
    original = raw.copy(deep=True)
    main, review, log = clean_cohort(raw)
    assert main.loc[0, ["OHQ030", "DIQ010", "INDFMPIR", "OHQ870"]].tolist() == [7, 3, 0, 7]
    assert all(pd.isna(main.loc[1, name]) for name in specials)
    assert len(main) == 20 and review.empty
    assert log["special_codes_to_missing"]["OHQ870"] == 1
    assert "WTINTPRP" in main
    pd.testing.assert_frame_equal(raw, original)


def test_smoking_skip_current_former_unknown_and_inconsistent_followup():
    raw = pd.DataFrame({"SMQ020": [2, 1, 1, 1, 1, 9, 2, 7],
                        "SMQ040": [np.nan, 1, 2, 3, np.nan, np.nan, 1, 9]})
    original = raw.copy(deep=True)
    status, reason, skipped = derive_smoking_status(raw)
    assert status.iloc[:4].tolist() == ["fewer_than_100_lifetime", "current", "current", "former"]
    assert status.iloc[4:].isna().all()
    assert reason.iloc[4:].tolist() == ["missing_followup", "unknown_lifetime_response", "inconsistent_answers", "unknown_lifetime_response"]
    assert skipped.tolist() == [True, False, False, False, False, False, False, False]
    pd.testing.assert_frame_equal(raw, original)


def test_age_and_cleaning_day_exclusions_are_separate_and_review_keeps_original_values():
    raw = sample_frame()
    raw.loc[0, "RIDAGEYR"] = 29
    raw.loc[1:3, "OHQ870"] = 9
    raw.loc[4, "OHQ870"] = 99
    main, review, log = clean_cohort(raw)
    assert log["audit_valid_labels"] == 20
    assert log["age_exclusions"] == 1
    assert log["cleaning_day_exclusions"] == 3
    assert len(main) == 16 and len(review) == 3
    assert review["OHQ870"].eq(9).all()
    assert review["exclusion_reason"].eq("OHQ870_outside_integer_0_to_7").all()
    assert pd.isna(main.loc[4, "OHQ870"])
    assert set(main["SEQN"]).isdisjoint(review["SEQN"])


@pytest.mark.parametrize("field,value", [("RIAGENDR", 7), ("OHQ030", 8), ("OHQ850", 9)])
def test_unexpected_codes_or_outcomes_are_rejected(field, value):
    raw = sample_frame()
    raw.loc[0, field] = value
    with pytest.raises(ValueError):
        clean_cohort(raw)


def test_split_is_frozen_disjoint_and_rejects_changed_cohort(tmp_path):
    main, _, _ = clean_cohort(sample_frame(50))
    path = tmp_path / "split_manifest.json"
    dev, held, manifest = split_participants(main, path)
    saved = path.read_bytes()
    assert len(dev) == 40 and len(held) == 10
    assert set(dev["SEQN"]).isdisjoint(held["SEQN"])
    assert set(dev["SEQN"]) | set(held["SEQN"]) == set(main["SEQN"])
    assert dev["OHQ850"].value_counts().to_dict() == {1: 20, 2: 20}
    _, _, reused = split_participants(main.sample(frac=1, random_state=99), path)
    assert reused == manifest
    with pytest.raises(ValueError, match="refusing to overwrite"):
        split_participants(main.iloc[:-1], path)
    assert path.read_bytes() == saved
    duplicate = pd.concat([main, main.iloc[[0]]])
    with pytest.raises(ValueError, match="unique"):
        split_participants(duplicate)


def test_development_only_fit_explicit_unknowns_missing_flags_and_no_label_leakage():
    raw = sample_frame(4)
    raw.loc[0:1, "RIDAGEYR"] = [30, 40]
    raw.loc[0:1, "INDFMPIR"] = [0, 2]
    raw.loc[0:1, "OHQ870"] = [0, 4]
    main, _, _ = clean_cohort(raw)
    x_dev, y = model_inputs(main.iloc[:2])
    assert len(FEATURES) == 12
    assert y.tolist() == [1, 0]
    assert set(x_dev) == set(FEATURES)
    assert not {"SEQN", "OHQ850", "WTINTPRP", "OHQ555Q", "SMQ020", "SMQ040", "smoking_status_reason"} & set(x_dev)
    processor = make_preprocessor()
    transformed_dev = processor.fit_transform(x_dev)
    imputer = processor.named_transformers_["numeric"].named_steps["impute"]
    np.testing.assert_array_equal(imputer.statistics_, [35, 1, 2])
    scaler = processor.named_transformers_["numeric"].named_steps["scale"]
    original_mean = scaler.mean_.copy()
    held = main.iloc[[2]].copy()
    held.loc[:, "RIDAGEYR"] = np.nan
    held.loc[:, "INDFMPIR"] = 5
    held.loc[:, "OHQ870"] = np.nan
    held.loc[:, "OHQ030"] = np.nan
    x_held, _ = model_inputs(held)
    transformed_held = processor.transform(x_held)
    names = list(processor.get_feature_names_out())
    assert transformed_dev.shape == (2, 47)
    assert transformed_held.shape == (1, 47) and np.isfinite(transformed_held).all()
    assert transformed_held[0, names.index("categorical__OHQ030_unknown")] == 1
    assert transformed_held[0, names.index("missing__missingindicator_RIDAGEYR")] == 1
    np.testing.assert_array_equal(imputer.statistics_, [35, 1, 2])
    np.testing.assert_array_equal(scaler.mean_, original_mean)


def test_entirely_missing_numeric_column_has_explicit_fallback_and_flag():
    main, _, _ = clean_cohort(sample_frame())
    main["INDFMPIR"] = np.nan
    x, _ = model_inputs(main)
    processor = make_preprocessor()
    matrix = processor.fit_transform(x)
    assert np.isfinite(matrix).all()
    index = NUMERIC.index("INDFMPIR")
    assert processor.named_transformers_["numeric"].named_steps["impute"].statistics_[index] == 0
    names = list(processor.get_feature_names_out())
    assert (matrix[:, names.index("missing__missingindicator_INDFMPIR")] == 1).all()
