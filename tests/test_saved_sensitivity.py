"""Independent arithmetic checks for saved-prediction sensitivity helpers."""

import numpy as np
import pytest

from src.tabular.baseline_nhanes import score_predictions
from src.tabular.survey_sensitivity import weighted_metrics
from src.vision.saved_prediction_uncertainty import exact_recall_interval, measurements, paired_bootstrap


def test_uniform_weights_reproduce_original_scorer_and_scale_invariance():
    y, p = np.array([0, 1, 0, 1]), np.array([.2, .7, .6, .3])
    ordinary = score_predictions(y, p)
    weighted = weighted_metrics(y, p, np.ones(4))
    for name in list(ordinary)[:6]:
        assert weighted[name] == pytest.approx(ordinary[name])
    assert weighted_metrics(y, p, np.array([1, 2, 3, 4])) == weighted_metrics(y, p, np.array([10, 20, 30, 40]))


def test_weighted_brier_matches_manual_sum_and_invalid_weights_rejected():
    actual = weighted_metrics([0, 1], [.2, .6], [1, 3])
    assert actual["Brier"] == pytest.approx((.04 + 3*.16)/4)
    for weights in ([0, 1], [-1, 2], [np.nan, 1]):
        with pytest.raises(ValueError):
            weighted_metrics([0, 1], [.2, .6], weights)


def test_single_failed_case_recall_interval_is_wide_not_zero():
    assert exact_recall_interval(0, 1) == pytest.approx([0, .975])
    assert exact_recall_interval(1, 1) == pytest.approx([.025, 1])
    with pytest.raises(ValueError):
        exact_recall_interval(0, 0)


def test_vision_perfect_mapping_and_paired_determinism():
    labels = np.array([1, 2, 3, 4] * 3)
    perfect = np.eye(4)[labels-1] * .8 + .05
    metric = measurements(labels, perfect)
    assert metric == {"accuracy": 1, "macro_f1": 1, "ordinal_mae": 0, "macro_auroc": 1}
    intervals = paired_bootstrap(labels, perfect, perfect, repetitions=10)
    assert all(value == [0, 0] for value in intervals.values())
    assert intervals == paired_bootstrap(labels, perfect, perfect, repetitions=10)
    with pytest.raises(ValueError):
        measurements(labels, perfect * 2)
