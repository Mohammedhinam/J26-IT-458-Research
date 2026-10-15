"""Focused synthetic checks for nested calibration and threshold boundaries."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

from test_baseline_nhanes import synthetic_inputs
from src.tabular import calibration_threshold_nhanes as experiment
from src.tabular.preprocess_nhanes import NUMERIC


def fingerprint(x, y):
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    return experiment.fold_fingerprint(x, folds)


def test_threshold_grid_exact_ties_and_nonpositive_j_flag():
    decision = experiment.select_threshold([0, 0, 1, 1], [0.1, 0.6, 0.4, 0.9])
    assert decision == {"threshold": 0.4, "J": 0.5, "useful": True}
    perfect = experiment.select_threshold([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert perfect["threshold"] == 0.8 and perfect["J"] == 1
    constant = experiment.select_threshold([0, 0, 1, 1], [0.3]*4)
    assert constant == {"threshold": 0.3, "J": 0.0, "useful": False}


@pytest.mark.parametrize("family", ["Logistic", "XGBoost"])
def test_raw_uses_same_fitted_base_and_tuning_labels_cannot_change_calibration(family):
    x, y = synthetic_inputs(100)
    pool, tuning, validation = x.iloc[:60], x.iloc[60:80], x.iloc[80:]
    inner = tuple(StratifiedKFold(3, shuffle=True, random_state=42).split(pool, y.iloc[:60]))
    output, fitted = experiment.fit_fold((family, "Full"), pool, y.iloc[:60], tuning, y.iloc[60:80], validation, inner)
    raw = fitted.calibrated_classifiers_[0].estimator
    assert fitted.ensemble is False and fitted.method == "sigmoid"
    np.testing.assert_array_equal(output["Raw"][0], raw.predict_proba(validation)[:, 1])
    np.testing.assert_array_equal(output["Sigmoid"][0], fitted.predict_proba(validation)[:, 1])
    changed, again = experiment.fit_fold((family, "Full"), pool, y.iloc[:60], tuning, 1-y.iloc[60:80], validation, inner)
    for version in experiment.VERSIONS:
        np.testing.assert_array_equal(output[version][0], changed[version][0])
    first = fitted.calibrated_classifiers_[0].calibrators[0]
    second = again.calibrated_classifiers_[0].calibrators[0]
    assert (first.a_, first.b_) == (second.a_, second.b_)


def test_nested_fits_are_isolated_and_cover_every_participant_once(monkeypatch):
    x, y = synthetic_inputs(100)
    original_fit = Pipeline.fit
    records = []
    tuning_calls = []
    selector = experiment.select_threshold

    def track_fit(self, fit_x, fit_y=None, **kwargs):
        if "classifier" not in self.named_steps:
            return original_fit(self, fit_x, fit_y, **kwargs)
        assert kwargs == {}  # No eval_set or outer/tuning payload passed to fit.
        record = {"model": self, "ids": fit_x.index.tolist(), "columns": fit_x.columns.tolist()}
        records.append(record)
        np.testing.assert_array_equal(fit_y, y.loc[fit_x.index].to_numpy())
        result = original_fit(self, fit_x, fit_y, **kwargs)
        numeric = self.named_steps["preprocess"].named_transformers_["numeric"]
        values = fit_x[list(NUMERIC)]
        medians = values.median()
        np.testing.assert_allclose(numeric.named_steps["impute"].statistics_, medians)
        np.testing.assert_allclose(numeric.named_steps["scale"].mean_, values.fillna(medians).mean())
        return result

    def track_threshold(labels, probability):
        tuning_calls.append(labels.index.tolist())
        return selector(labels, probability)

    monkeypatch.setattr(Pipeline, "fit", track_fit)
    monkeypatch.setattr(experiment, "select_threshold", track_threshold)
    probabilities, learned, thresholds, partitions, dummy = experiment.run_validation(x, y, fingerprint(x, y))
    assert len(records) == 80 and len({id(record["model"]) for record in records}) == 80
    assert len(tuning_calls) == 40 and len(partitions) == 5
    outer = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    for fold, (training, validation) in enumerate(outer):
        pool, tuning = train_test_split(training, test_size=0.2, random_state=42, stratify=y.iloc[training])
        inner = tuple(StratifiedKFold(3, shuffle=True, random_state=42).split(x.iloc[pool], y.iloc[pool]))
        for candidate_number, candidate in enumerate(experiment.CANDIDATES):
            fits = records[fold*16+candidate_number*4:fold*16+candidate_number*4+4]
            expected_ids = [x.index[pool[train]].tolist() for train, _ in inner] + [x.index[pool].tolist()]
            for record, ids in zip(fits, expected_ids):
                assert record["ids"] == ids
                assert set(ids).isdisjoint(x.index[tuning])
                assert set(ids).isdisjoint(x.index[validation])
                assert record["columns"] == experiment.input_columns(candidate[1])
            calls = tuning_calls[fold*8+candidate_number*2:fold*8+candidate_number*2+2]
            assert calls == [x.index[tuning].tolist()]*2
        np.testing.assert_allclose(dummy[validation], y.iloc[pool].mean())
    for key in experiment.WORKFLOWS:
        assert len(thresholds[key]) == 5
        assert np.isfinite(probabilities[key]).all()
        assert learned[key].shape == (100,)


def test_all_workflows_reproduce_predictions_and_thresholds():
    x, y = synthetic_inputs(100)
    first = experiment.run_validation(x, y, fingerprint(x, y))
    second = experiment.run_validation(x, y, fingerprint(x, y))
    assert first[2] == second[2] and first[3] == second[3]
    for key in experiment.WORKFLOWS:
        np.testing.assert_array_equal(first[0][key], second[0][key])
        np.testing.assert_array_equal(first[1][key], second[1][key])


def test_bootstrap_is_paired_prediction_only_reproducible_and_flags_one_class(monkeypatch):
    y = np.array([0, 0, 1, 1])
    raw, sigmoid = ("Logistic", "Full", "Raw"), ("Logistic", "Full", "Sigmoid")
    probability = np.array([0.1, 0.4, 0.6, 0.9])
    probabilities = {raw: probability, sigmoid: probability.copy()}
    learned = {key: value >= 0.5 for key, value in probabilities.items()}

    def forbidden(*_):
        pytest.fail("Bootstrap must not fit models or select thresholds")

    monkeypatch.setattr(experiment, "make_candidate", forbidden)
    monkeypatch.setattr(experiment, "select_threshold", forbidden)
    first = experiment.bootstrap_intervals(y, probabilities, learned, repetitions=40)
    second = experiment.bootstrap_intervals(y, probabilities, learned, repetitions=40)
    assert first[2] > 0 and first[2] == second[2]
    for key in probabilities:
        np.testing.assert_array_equal(first[0][key], second[0][key])
    np.testing.assert_array_equal(first[1][("Logistic", "Full")], np.zeros((8, 2)))


def test_calibration_diagnostics_known_calibration_clipping_and_undefined_cases():
    p = np.repeat([0.2, 0.5, 0.8], 50)
    y = np.concatenate([np.r_[np.ones(yes), np.zeros(50-yes)] for yes in (10, 25, 40)])
    result = experiment.calibration_diagnostic(y, p)
    assert result["status"] == "OK"
    assert result["intercept"] == pytest.approx(0, abs=0.005)
    assert result["slope"] == pytest.approx(1, abs=0.005)
    assert result["clipped"] == 0
    assert "separation" in experiment.calibration_diagnostic([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])["status"]
    assert "constant" in experiment.calibration_diagnostic([0, 0, 1, 1], [0.5]*4)["status"]
    extremes = np.array([0, 0.1, 0.5, 0.9, 1.0])
    original = extremes.copy()
    assert experiment.calibration_diagnostic([0, 1, 0, 1, 0], extremes)["clipped"] == 2
    np.testing.assert_array_equal(extremes, original)


def test_reliability_bins_cover_rows_and_handle_ties():
    rows = experiment.reliability_rows([0, 1]*10, np.linspace(0.1, 0.9, 20))
    assert len(rows) == 10 and sum(row[1] for row in rows) == 20 and sum(row[2] for row in rows) == 10
    tied = experiment.reliability_rows([0, 1]*10, np.full(20, 0.3))
    assert len(tied) == 1 and tied[0][:3] == (1, 20, 10)


def test_probability_and_operating_metrics_are_correct_and_separate():
    scores = experiment.workflow_metrics([0, 0, 1, 1], [0.1, 0.1, 0.9, 0.9], [0, 1, 0, 1])
    assert scores["AUROC"] == scores["Average precision"] == 1
    assert scores["Brier"] == pytest.approx(0.01)
    assert scores["Sensitivity @0.50"] == scores["Specificity @0.50"] == 1
    assert scores["Sensitivity learned"] == scores["Specificity learned"] == 0.5
    assert [scores[name + " learned"] for name in ("TN", "FP", "FN", "TP")] == [1, 1, 1, 1]


def test_overlapping_participants_are_rejected_before_fit():
    x, y = synthetic_inputs(100)
    inner = tuple(StratifiedKFold(3, shuffle=True, random_state=42).split(x.iloc[:60], y.iloc[:60]))
    with pytest.raises(ValueError, match="disjoint"):
        experiment.fit_fold(("Logistic", "Full"), x.iloc[:60], y.iloc[:60], x.iloc[50:70], y.iloc[50:70], x.iloc[80:], inner)


def test_wrong_outer_fingerprint_stops_before_model_fits(monkeypatch):
    x, y = synthetic_inputs(100)

    def forbidden(*_):
        pytest.fail("Wrong frozen folds must stop before any fit")

    monkeypatch.setattr(experiment, "fit_fold", forbidden)
    with pytest.raises(ValueError, match="Outer folds differ"):
        experiment.run_validation(x, y, "wrong")
