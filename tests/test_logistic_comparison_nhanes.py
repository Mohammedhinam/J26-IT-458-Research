"""Focused synthetic tests for fixed folds, ablation and reproduction gates."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold

from test_baseline_nhanes import synthetic_inputs
from src.tabular import baseline_nhanes as baseline
from src.tabular import logistic_comparison_nhanes as comparison
from src.tabular.preprocess_nhanes import FEATURES, NUMERIC


def baseline_reference(x, y):
    scores = baseline.run_oof(x, y)[0][baseline.MODELS[1]]
    return {name: comparison.metric_text(value) for name, value in scores.items()}


def test_ablation_excludes_only_authorised_inputs_and_encoded_columns():
    x, y = synthetic_inputs()
    original = x.copy(deep=True)
    full = comparison.make_comparison_pipeline(("Full", 1.0, None))
    old = baseline.make_baseline(baseline.MODELS[1])
    assert full.named_steps["classifier"].get_params() == old.named_steps["classifier"].get_params()
    ablated = comparison.make_comparison_pipeline(("Awareness-ablated", 1.0, None))
    columns = comparison.input_columns("Awareness-ablated")
    assert columns == [name for name in FEATURES if name not in ("OHQ835", "OHQ860")]
    ablated.fit(x[columns], y)
    full.fit(x, y)
    names = ablated.named_steps["preprocess"].get_feature_names_out()
    assert len(names) == 41
    assert not any("OHQ835" in name or "OHQ860" in name for name in names)
    assert len(full.named_steps["preprocess"].get_feature_names_out()) == 47
    assert ablated.named_steps["preprocess"].n_features_in_ == 10
    pd.testing.assert_frame_equal(x, original)


def test_all_twelve_use_identical_folds_and_training_only_preprocessing(monkeypatch):
    x, y = synthetic_inputs()
    reference = baseline_reference(x, y)
    fitted = []
    factory = comparison.make_comparison_pipeline

    def capture(configuration):
        model = factory(configuration)
        original_fit = model.fit
        original_predict = model.predict_proba
        record = {"configuration": configuration, "model": model}
        fitted.append(record)

        def fit(train_x, train_y):
            record["train"] = train_x.index.tolist()
            pd.testing.assert_series_equal(train_y, y.loc[train_x.index])
            return original_fit(train_x, train_y)

        def predict(validation_x):
            record["validation"] = validation_x.index.tolist()
            return original_predict(validation_x)

        model.fit = fit
        model.predict_proba = predict
        return model

    monkeypatch.setattr(comparison, "make_comparison_pipeline", capture)
    results, predictions, widths, folds, reproduced = comparison.run_comparison(x, y, reference)
    original_folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    assert len(results) == len(predictions) == len(widths) == 12
    assert len(fitted) == 60 and len({id(record["model"]) for record in fitted}) == 60
    assert all(row[-1] == "MATCH" for row in reproduced)
    for actual, expected in zip(folds, original_folds):
        np.testing.assert_array_equal(actual[0], expected[0])
        np.testing.assert_array_equal(actual[1], expected[1])

    differs_from_global = False
    for configuration in comparison.CONFIGURATIONS:
        records = [record for record in fitted if record["configuration"] == configuration]
        assert len(records) == 5
        seen = []
        for record, (train, validation) in zip(records, original_folds):
            assert record["train"] == x.index[train].tolist()
            assert record["validation"] == x.index[validation].tolist()
            assert set(record["train"]).isdisjoint(record["validation"])
            seen.extend(record["validation"])
            processor = record["model"].named_steps["preprocess"]
            numeric = processor.named_transformers_["numeric"]
            values = x.iloc[train][list(NUMERIC)]
            medians = values.median()
            np.testing.assert_allclose(numeric.named_steps["impute"].statistics_, medians)
            np.testing.assert_allclose(numeric.named_steps["scale"].mean_, values.fillna(medians).mean())
            differs_from_global |= not np.allclose(medians, x[list(NUMERIC)].median())
            assert record["model"].named_steps["classifier"].class_weight == configuration[2]
        assert sorted(seen) == sorted(x.index)  # Exactly one validation slot each.
        assert np.isfinite(predictions[configuration]).all()
        assert widths[configuration] == (47 if configuration[0] == "Full" else 41)
    assert differs_from_global  # Test data would expose a global-fit implementation.


def test_ablated_predictions_ignore_changed_awareness_answers():
    x, y = synthetic_inputs()
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    configuration = ("Awareness-ablated", 1.0, "balanced")
    original = comparison.fit_configuration(x, y, folds, configuration)[1]
    changed = x.copy(deep=True)
    changed["OHQ835"] = "2"
    changed["OHQ860"] = "unknown"
    modified = comparison.fit_configuration(changed, y, folds, configuration)[1]
    np.testing.assert_array_equal(original, modified)


def test_reproduction_matches_original_baseline_probabilities_and_all_metrics():
    x, y = synthetic_inputs()
    old_metrics, _, old_probabilities = baseline.run_oof(x, y)
    reference = {name: comparison.metric_text(value) for name, value in old_metrics[baseline.MODELS[1]].items()}
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    actual, probability, _ = comparison.fit_configuration(x, y, folds, comparison.BASELINE_CONFIGURATION)
    np.testing.assert_array_equal(probability, old_probabilities[baseline.MODELS[1]])
    assert all(row[-1] == "MATCH" for row in comparison.verify_reproduction(actual, reference))


def test_reproducibility_of_all_twelve_configurations():
    x, y = synthetic_inputs()
    reference = baseline_reference(x, y)
    first = comparison.run_comparison(x, y, reference)
    second = comparison.run_comparison(x, y, reference)
    assert first[0] == second[0]
    for configuration in comparison.CONFIGURATIONS:
        np.testing.assert_array_equal(first[1][configuration], second[1][configuration])


def test_failed_reproduction_stops_before_other_configurations(monkeypatch):
    x, y = synthetic_inputs()
    reference = baseline_reference(x, y)
    reference["Brier"] = "0.900000"
    calls = []
    original = comparison.fit_configuration

    def capture(*args):
        calls.append(args[-1])
        return original(*args)

    monkeypatch.setattr(comparison, "fit_configuration", capture)
    with pytest.raises(ValueError, match="expected 0.900000, found"):
        comparison.run_comparison(x, y, reference)
    assert calls == [comparison.BASELINE_CONFIGURATION]


def test_historical_parser_retains_all_ten_recorded_metrics():
    reference = comparison.historical_metrics(comparison.HISTORICAL_REPORT.read_text())
    assert len(reference) == 10
    assert reference["AUROC"] == "0.736721" and reference["Brier"] == "0.157823"
    assert [reference[name] for name in ("TN", "FP", "FN", "TP")] == ["4398", "300", "1098", "455"]


def test_identifier_or_outcome_inputs_are_rejected():
    x, y = synthetic_inputs()
    reference = baseline_reference(x, y)
    with pytest.raises(ValueError, match="allowlist"):
        comparison.run_comparison(x.assign(OHQ850=y), y, reference)
