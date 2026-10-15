"""Generated aggregate results only; no datasets, checkpoint tensors or torch."""
from copy import deepcopy
import json

import numpy as np
import pytest

from src.vision import diagnose_b1_pilot_v1 as diagnosis
from src.vision import exploratory_pilot_b1_v1 as pilot


def example():
    result = {"protocol": json.loads(json.dumps(pilot.protocol())), "test_used": False,
              "best_epoch": 1, "history": []}
    for number in range(1, 4):
        row = {"epoch": number}
        for split, support in (("training", [12, 84, 223, 361]), ("validation", [1, 13, 22, 17])):
            matrix = np.zeros((4, 4), dtype=int)
            matrix[:, 3] = support
            row[split] = {"support": support, "n": sum(support), "confusion_matrix": matrix.tolist(),
                          "loss": 1.0, "macro_f1_four_grades": .1}
        result["history"].append(row)
    return result


def test_frozen_protocol_json_tuple_serialization_is_not_a_conflict():
    report = diagnosis.analyse_results(example())
    assert report["validation_all_grade4_each_epoch"]
    assert report["training_metrics_are_online"]
    assert not report["root_cause_established"]


def test_training_prior_and_balancing_have_independent_scalar_reference():
    support = [12, 84, 223, 361]
    result = diagnosis.training_reference(support, [1, 13, 22, 17])
    np.testing.assert_allclose(result["training_priors"], [n / 680 for n in support])
    np.testing.assert_allclose(result["proposed_training_only_balanced_weights"], [680 / (4*n) for n in support], rtol=1e-7)
    assert result["proposal_activated"] is False


def test_validation_counts_never_change_training_weights_or_priors():
    first = diagnosis.training_reference([12, 84, 223, 361], [1, 13, 22, 17])
    changed = diagnosis.training_reference([12, 84, 223, 361], [40, 2, 3, 8])
    for key in ("training_priors", "proposed_training_only_balanced_weights"):
        assert first[key] == changed[key]


def test_prior_brier_independent_formula_and_no_fake_healthy_grade():
    result = diagnosis.training_reference([12, 84, 223, 361], [1, 13, 22, 17])
    p = result["training_priors"]
    expected = sum(n * sum((p[j] - (i == j))**2 for j in range(4)) for i,n in enumerate([1,13,22,17])) / 53
    assert result["training_prior_baseline"]["multiclass_brier"] == pytest.approx(expected)
    assert result["training_prior_baseline"]["macro_auroc"] == .5
    assert result["training_prior_baseline"]["healthy_mgi0_supported"] is False


@pytest.mark.parametrize("counts", [[0, 84, 223, 361], [-1, 1, 1, 1], [1.5, 2, 3, 4], [1, 2, 3], [0,0,0,0]])
def test_invalid_or_missing_training_class_fails_without_fabricating(counts):
    with pytest.raises(ValueError): diagnosis.training_reference(counts, [1, 13, 22, 17])


@pytest.mark.parametrize("change", ["test", "protocol", "epoch", "matrix", "nan", "support", "best"])
def test_malformed_or_changed_run_evidence_fails_closed(change):
    result = deepcopy(example())
    if change == "test": result["test_used"] = True
    if change == "protocol": result["protocol"]["training"]["class_weight"] = "balanced"
    if change == "epoch": result["history"][1]["epoch"] = 9
    if change == "matrix": result["history"][0]["validation"]["confusion_matrix"][0][3] = 2
    if change == "nan": result["history"][0]["training"]["loss"] = float("nan")
    if change == "support": result["history"][0]["training"]["support"] = [1, 2, 3, 4]
    if change == "best": result["best_epoch"] = 0
    with pytest.raises(ValueError): diagnosis.analyse_results(result)


def test_deterministic_diagnosis_without_image_or_model_io():
    assert diagnosis.analyse_results(example()) == diagnosis.analyse_results(example())


def test_checkpoint_reader_rejects_unknown_run_before_importing_torch(tmp_path):
    with pytest.raises(ValueError, match="verified completed run"):
        diagnosis.inspect_saved_checkpoints(tmp_path / "other", "missing", "missing")
