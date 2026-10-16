"""Prospective settings, fold isolation, reference gate and paired uncertainty."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold

from test_questionnaire_explain import generated_inputs
from src.tabular import pp1_questionnaire_workflow as workflow
from src.tabular.preprocess_nhanes import NUMERIC


def test_bounded_settings_and_training_only_class_weight():
    assert len(workflow.SETTINGS) == 6
    model = workflow.make_model("A_balanced", pd.Series([0, 0, 0, 1]))
    assert model.named_steps["classifier"].get_params()["scale_pos_weight"] == 3
    for name in workflow.SETTINGS:
        classifier = workflow.make_model(name, [0, 1]).named_steps["classifier"]
        assert classifier.get_params()["max_depth"] == 2
        assert classifier.get_params()["n_estimators"] <= 400
        assert classifier.get_params()["early_stopping_rounds"] is None
    with pytest.raises(ValueError):
        workflow.make_model("unbounded", [0, 1])


def test_all_folds_are_identical_train_only_and_explanations_cover_each_row(monkeypatch):
    x, y = generated_inputs(40)
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    fingerprint = workflow.fold_fingerprint(x, folds)
    records = []
    original = workflow.make_model

    def factory(name, training_y):
        model = original(name, training_y)
        fit = model.fit

        def capture(train_x, train_y, **kwargs):
            assert not kwargs
            records.append((name, train_x.index.tolist()))
            fit(train_x, train_y)
            imputer = model.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"]
            np.testing.assert_allclose(imputer.statistics_, train_x[list(NUMERIC)].median())
            if name == "A_balanced":
                assert model.named_steps["classifier"].get_params()["scale_pos_weight"] == (train_y == 0).sum() / (train_y == 1).sum()
            return model

        model.fit = capture
        return model

    monkeypatch.setattr(workflow, "make_model", factory)
    scores, predictions, shap, checks, settings = workflow.run_bounded(x, y, fingerprint)
    assert len(records) == 30 and len(settings) == 30
    assert shap.shape == (40, 12) and np.isfinite(shap).all() and len(checks) == 5
    for name in workflow.SETTINGS:
        assert [ids for setting, ids in records if setting == name] == [x.index[t].tolist() for t, _ in folds]
        assert scores[name] == workflow.score_predictions(y, predictions[name])
    # Repeat only the small generated recipe to test deterministic OOF values.
    repeated = workflow.run_bounded(x, y, fingerprint)
    for name in predictions:
        np.testing.assert_array_equal(predictions[name], repeated[1][name])
    np.testing.assert_array_equal(shap, repeated[2])


def test_fold_mismatch_stops_before_fit(monkeypatch):
    x, y = generated_inputs(40)
    monkeypatch.setattr(workflow, "make_model", lambda *_: pytest.fail("Must fail before fitting"))
    with pytest.raises(ValueError, match="fold membership"):
        workflow.run_bounded(x, y, "wrong")


def test_reference_mismatch_stops_before_new_settings(monkeypatch):
    x, y = generated_inputs(40)
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    original, names = workflow.make_model, []

    def capture(name, labels):
        names.append(name)
        return original(name, labels)

    monkeypatch.setattr(workflow, "make_model", capture)
    with pytest.raises(ValueError, match="metric names"):
        workflow.run_bounded(x, y, workflow.fold_fingerprint(x, folds), {"AUROC": "-1"})
    assert names == ["A_reference"] * 5


def test_paired_intervals_identical_predictions_exact_zero_and_known_direction():
    labels = np.array([0, 0, 1, 1] * 5)
    reference = np.full(20, 0.5)
    better = np.where(labels == 1, 0.9, 0.1)
    probabilities = {"A_reference": reference, "same": reference.copy(), "better": better}
    actual = workflow.paired_intervals(labels, probabilities, repetitions=20)
    assert actual["same"] == {"delta_auroc_95": [0, 0], "delta_brier_95": [0, 0]}
    assert actual["better"]["delta_auroc_95"] == [0.5, 0.5]
    np.testing.assert_allclose(actual["better"]["delta_brier_95"], [-0.24, -0.24])
    assert actual == workflow.paired_intervals(labels, probabilities, repetitions=20)
