"""Synthetic checks for approved settings, folds, leakage and OOF scoring."""

import json

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold
from xgboost.core import XGBoostError

from test_baseline_nhanes import synthetic_inputs
from src.tabular import baseline_nhanes as baseline
from src.tabular import xgboost_comparison_nhanes as comparison
from src.tabular.preprocess_nhanes import NUMERIC


def expected_folds(x, y):
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    return folds, comparison.fold_fingerprint(x, folds)


@pytest.mark.parametrize("old,new", [
    ("| D | 3 | 0.05 | 200 | 5.0 |", "| D | 3 | 0.05 | 200 | 9.0 |"),
    ("gbtree / binary:logistic", "gbtree / reg:squarederror"),
])
def test_plan_verification_accepts_approved_settings_and_rejects_conflicts(old, new):
    plan = comparison.PLAN.read_text()
    comparison.verify_plan(plan)
    assert old in plan
    with pytest.raises(ValueError):
        comparison.verify_plan(plan.replace(old, new))


def test_factory_uses_exact_profiles_binary_objective_and_existing_feature_schemas():
    x, y = synthetic_inputs()
    original = x.copy(deep=True)
    for configuration in comparison.CONFIGURATIONS:
        model = comparison.make_xgboost_pipeline(configuration)
        actual = model.named_steps["classifier"].get_params()
        for name, expected in {**comparison.FIXED_SETTINGS, **comparison.PROFILES[configuration[1]]}.items():
            assert actual[name] == expected
        assert actual["objective"] == "binary:logistic"
    for feature_set, width in [("Full", 47), ("Awareness-ablated", 41)]:
        model = comparison.make_xgboost_pipeline((feature_set, "A"))
        columns = comparison.input_columns(feature_set)
        model.fit(x[columns], y)
        names = model.named_steps["preprocess"].get_feature_names_out()
        assert len(names) == width
        if feature_set == "Awareness-ablated":
            assert len(columns) == 10
            assert not any("OHQ835" in name or "OHQ860" in name for name in names)
    pd.testing.assert_frame_equal(x, original)


def test_all_eight_use_same_folds_and_train_only_preprocessing_and_base_score(monkeypatch):
    x, y = synthetic_inputs()
    y[:] = 0
    y.iloc[:13] = 1  # Different fold priors expose a global base-score estimate.
    folds, fingerprint = expected_folds(x, y)
    records = []
    factory = comparison.make_xgboost_pipeline

    def capture(configuration):
        model = factory(configuration)
        original_fit, original_predict = model.fit, model.predict_proba
        record = {"configuration": configuration, "model": model}
        records.append(record)

        def fit(train_x, train_y, **kwargs):
            assert kwargs == {}  # No scored validation eval_set or early stopping.
            record["train"] = train_x.index.tolist()
            pd.testing.assert_series_equal(train_y, y.loc[train_x.index])
            return original_fit(train_x, train_y)

        def predict(validation_x):
            record["validation"] = validation_x.index.tolist()
            return original_predict(validation_x)

        model.fit, model.predict_proba = fit, predict
        return model

    monkeypatch.setattr(comparison, "make_xgboost_pipeline", capture)
    scores, probabilities, widths, actual_folds = comparison.run_comparison(x, y, fingerprint)
    assert len(scores) == len(probabilities) == len(widths) == 8
    assert len(records) == 40 and len({id(record["model"]) for record in records}) == 40
    for actual, expected in zip(actual_folds, folds):
        np.testing.assert_array_equal(actual[0], expected[0])
        np.testing.assert_array_equal(actual[1], expected[1])
    differs_from_global = False
    for configuration in comparison.CONFIGURATIONS:
        selected = [record for record in records if record["configuration"] == configuration]
        assert len(selected) == 5
        seen = []
        for record, (train, validation) in zip(selected, folds):
            assert record["train"] == x.index[train].tolist()
            assert record["validation"] == x.index[validation].tolist()
            assert set(record["train"]).isdisjoint(record["validation"])
            seen.extend(record["validation"])
            numeric = record["model"].named_steps["preprocess"].named_transformers_["numeric"]
            values = x.iloc[train][list(NUMERIC)]
            medians = values.median()
            np.testing.assert_allclose(numeric.named_steps["impute"].statistics_, medians)
            np.testing.assert_allclose(numeric.named_steps["scale"].mean_, values.fillna(medians).mean())
            differs_from_global |= not np.allclose(medians, x[list(NUMERIC)].median())
            classifier = record["model"].named_steps["classifier"]
            native = json.loads(classifier.get_booster().save_config())
            base_score = json.loads(native["learner"]["learner_model_param"]["base_score"])[0]
            assert base_score == pytest.approx(y.iloc[train].mean(), abs=1e-6)
        assert sorted(seen) == sorted(x.index)
        assert np.isfinite(probabilities[configuration]).all()
        assert scores[configuration] == baseline.score_predictions(y, probabilities[configuration])
        assert widths[configuration] == (47 if configuration[0] == "Full" else 41)
    assert differs_from_global


def test_reproducibility_for_all_eight_and_ablation_ignores_awareness_answers():
    x, y = synthetic_inputs()
    _, fingerprint = expected_folds(x, y)
    first = comparison.run_comparison(x, y, fingerprint)
    second = comparison.run_comparison(x, y, fingerprint)
    assert first[0] == second[0]
    for configuration in comparison.CONFIGURATIONS:
        np.testing.assert_array_equal(first[1][configuration], second[1][configuration])
    changed = x.copy(deep=True)
    changed["OHQ835"], changed["OHQ860"] = "2", "unknown"
    modified = comparison.run_comparison(changed, y, fingerprint)
    for configuration in comparison.CONFIGURATIONS:
        if configuration[0] == "Awareness-ablated":
            np.testing.assert_array_equal(first[1][configuration], modified[1][configuration])


def test_wrong_fold_fingerprint_or_outcome_inputs_fail_before_training(monkeypatch):
    x, y = synthetic_inputs()

    def forbidden(*_):
        pytest.fail("Invalid membership/inputs must fail before training")

    monkeypatch.setattr(comparison, "make_xgboost_pipeline", forbidden)
    with pytest.raises(ValueError, match="Fold membership differs"):
        comparison.run_comparison(x, y, "invalid")
    _, fingerprint = expected_folds(x, y)
    with pytest.raises(ValueError, match="allowlist"):
        comparison.run_comparison(x.assign(OHQ850=y), y, fingerprint)


def test_existing_scorer_is_reused_and_known_probability_metrics_are_correct():
    assert comparison.score_predictions is baseline.score_predictions
    scores = comparison.score_predictions([0, 0, 1, 1], [0.1, 0.1, 0.9, 0.9])
    assert scores["AUROC"] == scores["PR-AUC (trapezoidal)"] == scores["Average precision"] == 1
    assert scores["Brier"] == pytest.approx(0.01)
    assert [scores[name] for name in ("TN", "FP", "FN", "TP")] == [2, 0, 0, 2]
    assert comparison.THRESHOLD == 0.50


def test_runtime_failure_stops_without_trying_other_settings(monkeypatch):
    x, y = synthetic_inputs()
    _, fingerprint = expected_folds(x, y)
    called = []

    class BrokenModel:
        def fit(self, *_):
            raise XGBoostError("synthetic runtime failure")

    def broken(configuration):
        called.append(configuration)
        return BrokenModel()

    monkeypatch.setattr(comparison, "make_xgboost_pipeline", broken)
    with pytest.raises(XGBoostError, match="synthetic runtime failure"):
        comparison.run_comparison(x, y, fingerprint)
    assert called == [comparison.CONFIGURATIONS[0]]


def test_historical_references_are_read_exactly_without_new_fits():
    text = comparison.BASELINE_REPORT.read_text()
    names = tuple(comparison.historical_metrics(text))
    row = comparison.reference_row(text, "| Model |", "| Training-rate dummy |", names)
    assert row == ["0.499486", "0.398258", "0.248216", "0.186718", "0.000000", "1.000000", "4698", "0", "1553", "0"]
