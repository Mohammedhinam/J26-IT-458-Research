"""Synthetic-only checks for endpoint semantics, explanations and safe scenarios."""

import copy
import json

import joblib
import numpy as np
import pandas as pd
import pytest

from src.tabular import questionnaire_explain as explain
from src.tabular.xgboost_comparison_nhanes import make_xgboost_pipeline
from src.tabular.preprocess_nhanes import CAT_CODES, FEATURES


def generated_inputs(n=80):
    rows = []
    for i in range(n):
        row = dict(explain.EXAMPLE_PROFILE)
        row.update(RIDAGEYR=30 + i % 51, INDFMPIR=(i % 50) / 10, OHQ870=i % 8)
        for field, codes in CAT_CODES.items():
            row[field] = str(codes[i % len(codes)])
        if i % 7 == 0:
            row["INDFMPIR"] = np.nan
        rows.append(row)
    frame = pd.DataFrame(rows, columns=FEATURES, index=pd.Index(range(100, 100 + n), name="SEQN"))
    labels = pd.Series([int(i % 4 == 0) for i in range(n)], index=frame.index)
    return frame, labels


@pytest.fixture(scope="module")
def prototype():
    x, y = generated_inputs()
    model = make_xgboost_pipeline(("Full", "A"))
    model.fit(x, y)
    return explain.QuestionnairePrototype(model, explain.fit_support(x), {"scope": "synthetic test"})


def test_exact_additivity_native_crosscheck_and_12_group_coverage(prototype):
    result = prototype.predict(explain.EXAMPLE_PROFILE)
    assert len(result["contributions"]) == 12
    total = result["base_log_odds"] + sum(row["contribution_log_odds"] for row in result["contributions"])
    assert total == pytest.approx(result["raw_log_odds"], abs=1e-5)
    assert 1 / (1 + np.exp(-total)) == pytest.approx(result["probability"], abs=1e-5)
    assert all(error <= 1e-5 for error in result["checks"].values())
    assert result["outcome"] == "self_reported_previous_gum_treatment"
    assert "log-odds" in result["shap_method"] or "raw_log_odds" in result
    assert "not separately calibrated" in result["calibration"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("field,value", [
    ("RIDAGEYR", 29), ("RIDAGEYR", 81), ("RIDAGEYR", None), ("RIDAGEYR", 40.5),
    ("OHQ870", 9), ("OHQ870", 1.5), ("OHQ870", True), ("INDFMPIR", -0.1),
    ("INDFMPIR", float("inf")), ("INDFMPIR", float("nan")),
    ("RIAGENDR", "7"), ("DIQ010", 3), ("SMOKING_STATUS", "never"),
])
def test_invalid_profiles_fail_closed(field, value):
    with pytest.raises(ValueError):
        explain.validate_profile({**explain.EXAMPLE_PROFILE, field: value})


@pytest.mark.parametrize("extra", ["OHQ850", "SEQN", "SMQ020", "WTINTPRP"])
def test_non_predictors_rejected(extra):
    with pytest.raises(ValueError, match="12 input"):
        explain.validate_profile({**explain.EXAMPLE_PROFILE, extra: 1})


def test_valid_zero_seven_borderline_unknown_and_age80_preserved(prototype):
    profile = {**explain.EXAMPLE_PROFILE, "RIDAGEYR": 80, "INDFMPIR": 0, "OHQ030": "7",
               "OHQ870": 7, "DIQ010": "3", "OHQ835": None}
    result = prototype.predict(profile)
    assert result["profile"] == profile
    assert any("OHQ835: unknown" in warning for warning in result["support"]["warnings"])
    assert any(row["field"] == "OHQ835" and row["value"] is None for row in result["contributions"])


def test_deterministic_reset_and_source_profile_immutable(prototype):
    profile = copy.deepcopy(explain.EXAMPLE_PROFILE)
    before = copy.deepcopy(profile)
    baseline = prototype.predict(profile)
    first = prototype.simulate(profile, {"SMOKING_STATUS": "former", "OHQ870": 7}, prototype.model_id)
    second = prototype.simulate(profile, {"SMOKING_STATUS": "former", "OHQ870": 7}, prototype.model_id)
    assert first == second and profile == before
    assert set(first["changed_fields"]) == {"SMOKING_STATUS", "OHQ870"}
    for field in set(FEATURES) - explain.EDITABLE:
        assert first["original"]["profile"][field] == first["scenario"]["profile"][field]
    reset = prototype.reset(profile, prototype.model_id)
    assert reset["scenario"] == baseline and reset["probability_difference"] == 0
    assert reset["is_reset"]


@pytest.mark.parametrize("changes", [{"RIDAGEYR": 50}, {"OHQ850": 1}, {"OHQ835": "1"},
                                     {"OHQ870": None}, {"SMOKING_STATUS": "fewer_than_100_lifetime"}])
def test_invalid_or_protected_scenario_changes_rejected(prototype, changes):
    with pytest.raises(ValueError):
        prototype.simulate(explain.EXAMPLE_PROFILE, changes, prototype.model_id)


@pytest.mark.parametrize("original", ["fewer_than_100_lifetime", None])
def test_scenario_cannot_invent_lifetime_smoking_history(prototype, original):
    with pytest.raises(ValueError, match="lifetime"):
        prototype.simulate({**explain.EXAMPLE_PROFILE, "SMOKING_STATUS": original},
                           {"SMOKING_STATUS": "current"}, prototype.model_id)


def test_wrong_model_version_and_malformed_schema_fail(prototype):
    with pytest.raises(ValueError, match="version"):
        prototype.reset(explain.EXAMPLE_PROFILE, "stale")
    with pytest.raises(ValueError, match="12 input"):
        explain.validate_profile({})
    with pytest.raises(ValueError, match="Unrecognized"):
        explain.encoded_groups(["categorical__OHQ850_1"])


def test_support_uses_training_only_and_warns_on_unseen_pair():
    x, _ = generated_inputs()
    x["SMOKING_STATUS"], x["OHQ870"] = "former", 0
    support = explain.fit_support(x)
    warning = explain.support_warnings(explain.EXAMPLE_PROFILE, support)
    assert warning["smoking_cleaning_pair_count"] == 0
    assert warning["warnings"] and support["n"] == 80
    assert "full-profile" in warning["scope"]
    assert "SEQN" not in json.dumps(support)


def test_explanation_corruption_stops_instead_of_hiding_failure(prototype, monkeypatch):
    real = explain.shap.TreeExplainer

    class Corrupt:
        def __init__(self, *args, **kwargs):
            self.real = real(*args, **kwargs)

        def __call__(self, *args, **kwargs):
            result = self.real(*args, **kwargs)
            result.values[:, 0] += 1
            return result

    monkeypatch.setattr(explain.shap, "TreeExplainer", Corrupt)
    with pytest.raises(ValueError, match="verification"):
        prototype.predict(explain.EXAMPLE_PROFILE)


def test_own_saved_model_roundtrip_preserves_prediction(tmp_path, prototype):
    target = tmp_path / "generated.joblib"
    joblib.dump(prototype, target)
    restored = joblib.load(target)
    assert restored.model_id == prototype.model_id
    assert restored.predict(explain.EXAMPLE_PROFILE) == prototype.predict(explain.EXAMPLE_PROFILE)
