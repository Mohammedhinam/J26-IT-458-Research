"""Generated-only checks for the prospective paired adaptation experiment."""

import copy
from pathlib import Path

import numpy as np
import pytest
import torch

from src.vision import efficientnet_adaptation_v1 as adaptation


class TinyEfficientNet(torch.nn.Module):
    """Match the relevant B0 module boundaries without dental data or weights."""

    def __init__(self):
        super().__init__()
        self.features = torch.nn.Sequential(
            torch.nn.Sequential(
                torch.nn.Conv2d(3, 4, 1, bias=False),
                torch.nn.BatchNorm2d(4),
                torch.nn.SiLU(),
            ),
            *[torch.nn.Identity() for _ in range(7)],
            torch.nn.Sequential(
                torch.nn.Conv2d(4, 4, 1, bias=False),
                torch.nn.BatchNorm2d(4),
                torch.nn.SiLU(),
            ),
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Dropout(0.2), torch.nn.Linear(4, 4)
        )

    def forward(self, values):
        features = self.features(values).mean(dim=(2, 3))
        return self.classifier(features)


@pytest.fixture(autouse=True)
def bounded_cpu_threads():
    old_threads = torch.get_num_threads()
    torch.set_num_threads(2)
    yield
    torch.set_num_threads(old_threads)


@pytest.fixture
def generated_cohort():
    random = np.random.default_rng(123)
    arrays = random.normal(0, 0.25, (40, 3, 8, 8)).astype(np.float32)
    labels = np.tile(np.arange(1, 5), 10)
    ids = [f"generated/{number:03}" for number in range(40)]
    groups = [f"group{number:03}" for number in range(40)]
    folds = np.repeat(np.arange(5), 8)
    return arrays, labels, ids, groups, folds


@pytest.mark.parametrize("arm", ["head_only", "last_block"])
def test_only_prespecified_parameters_train_and_batchnorm_stays_frozen(arm):
    model = TinyEfficientNet()
    adaptation.configure_model(model, arm)
    adaptation.training_mode(model)
    names = {name for name, value in model.named_parameters() if value.requires_grad}
    expected = {"classifier.1.weight", "classifier.1.bias"}
    if arm == "last_block":
        expected.add("features.8.0.weight")
    assert names == expected
    assert model.classifier.training
    assert model.classifier[0].training
    assert not model.features.training
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            assert not module.training
            assert all(not parameter.requires_grad for parameter in module.parameters())


def test_unknown_arm_is_rejected_before_optimization():
    with pytest.raises(ValueError):
        adaptation.configure_model(TinyEfficientNet(), "full_backbone")


def test_actual_b0_architecture_has_only_final_pointwise_convolution_and_head_trainable():
    from torchvision.models import efficientnet_b0

    model = efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, 4)
    configuration = adaptation.configure_model(model, "last_block")
    assert set(configuration["trainable_names"]) == {
        "features.8.0.weight", "classifier.1.weight", "classifier.1.bias"
    }
    assert configuration["trainable_parameters"] == 414724
    adaptation.training_mode(model)
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            assert not module.training
            assert all(not parameter.requires_grad for parameter in module.parameters())


@pytest.mark.parametrize("arm", ["head_only", "last_block"])
def test_optimizer_groups_use_prespecified_learning_rates_without_duplicates(arm):
    model = TinyEfficientNet()
    configuration = adaptation.configure_model(model, arm)
    groups = configuration["parameter_groups"]
    parameters = []
    for group in groups:
        assert len(group["params"]) == len(group["names"])
        for parameter, name in zip(group["params"], group["names"]):
            assert parameter is dict(model.named_parameters())[name]
            assert parameter.requires_grad
            assert group["lr"] == (0.001 if name.startswith("classifier.") else 0.00001)
        parameters.extend(group["params"])
    assert len({id(parameter) for parameter in parameters}) == len(parameters)
    assert {id(parameter) for parameter in parameters} == {
        id(parameter) for parameter in model.parameters() if parameter.requires_grad
    }


def test_class_weights_are_computed_from_fitting_targets_only():
    targets = np.array([0, 1, 1, 2, 2, 2, 3, 3, 3, 3])
    np.testing.assert_allclose(adaptation.class_weights(targets), [2.5, 1.25, 10 / 12, 0.625])


@pytest.mark.parametrize("targets", [[], [0, 1, 2], [0, 1, 2, 4], [0, 1, 2, -1]])
def test_invalid_or_missing_class_cannot_silently_produce_weights(targets):
    with pytest.raises(ValueError):
        adaptation.class_weights(np.array(targets, dtype=int))


def test_five_folds_are_complete_group_isolated_and_preserve_all_classes(generated_cohort):
    _, labels, ids, groups, folds = generated_cohort
    adaptation.validate_folds(ids, labels, groups, folds)


@pytest.mark.parametrize("fault", ["duplicate_id", "unsorted", "group_leak", "missing_fold", "invalid_label", "missing_class", "length"])
def test_invalid_folds_fail_before_model_factory(generated_cohort, fault):
    _, labels, ids, groups, folds = generated_cohort
    labels, ids, groups, folds = labels.copy(), list(ids), list(groups), folds.copy()
    if fault == "duplicate_id":
        ids[1] = ids[0]
    elif fault == "unsorted":
        ids[0], ids[1] = ids[1], ids[0]
    elif fault == "group_leak":
        groups[8] = groups[0]
    elif fault == "missing_fold":
        folds[folds == 4] = 3
    elif fault == "invalid_label":
        labels[0] = 0
    elif fault == "missing_class":
        labels[labels == 1] = 2
    elif fault == "length":
        labels = labels[:-1]
    with pytest.raises(ValueError):
        adaptation.validate_folds(ids, labels, groups, folds)


def test_generated_cohort_cannot_pass_real_pinned_contract(generated_cohort):
    _, labels, ids, groups, folds = generated_cohort
    with pytest.raises(ValueError):
        adaptation.validate_folds(ids, labels, groups, folds, strict=True)


def test_paired_arms_start_identically_and_freeze_all_unselected_state(generated_cohort):
    arrays, labels, _, _, folds = generated_cohort
    torch.manual_seed(17)
    initial = TinyEfficientNet()
    before = {name: tensor.clone() for name, tensor in initial.state_dict().items()}
    results = []
    trained_models = []
    for arm in adaptation.ARMS:
        model = copy.deepcopy(initial)
        result = adaptation.fit_arm(
            model,
            torch.from_numpy(arrays[folds != 0]),
            torch.from_numpy(labels[folds != 0] - 1),
            torch.from_numpy(arrays[folds == 0]),
            arm,
            epochs=1,
            batch_size=8,
        )
        results.append(result)
        trained_models.append(model)
        assert result["frozen_check"]
        probabilities = result["probabilities"]
        assert probabilities.shape == (8, 4)
        assert np.isfinite(probabilities).all()
        np.testing.assert_allclose(probabilities.sum(axis=1), 1, atol=1e-6)
        assert not torch.equal(before["classifier.1.weight"], model.state_dict()["classifier.1.weight"])
        for name, value in model.state_dict().items():
            if name not in result["trainable_names"]:
                assert torch.equal(before[name], value), name
    assert results[0]["initial_sha"] == results[1]["initial_sha"]
    assert results[0]["order_sha"] == results[1]["order_sha"]
    assert torch.equal(before["features.8.0.weight"], trained_models[0].state_dict()["features.8.0.weight"])
    assert not torch.equal(before["features.8.0.weight"], trained_models[1].state_dict()["features.8.0.weight"])


def test_exact_ten_fits_cover_every_outer_record_once_per_arm(generated_cohort):
    arrays, labels, ids, groups, folds = generated_cohort
    finished = []
    result = adaptation.execute_comparison(
        arrays, labels, ids, groups, folds,
        model_factory=TinyEfficientNet,
        epochs=1,
        batch_size=8,
        on_fit_complete=lambda *args, **kwargs: finished.append((args, kwargs)),
    )
    assert result["fit_count"] == 10
    assert len(result["fit_records"]) == 10
    assert len(finished) == 10
    assert set(result["probabilities"]) == set(adaptation.ARMS)
    for probabilities in result["probabilities"].values():
        assert probabilities.shape == (40, 4)
        assert np.isfinite(probabilities).all()
        np.testing.assert_allclose(probabilities.sum(axis=1), 1, atol=1e-6)


def test_factory_failure_stops_comparison_without_automatic_retry(generated_cohort):
    arrays, labels, ids, groups, folds = generated_cohort
    attempts = []

    def failing_factory():
        attempts.append(True)
        if len(attempts) == 3:
            raise RuntimeError("generated intentional factory failure")
        return TinyEfficientNet()

    with pytest.raises(RuntimeError, match="generated intentional factory failure"):
        adaptation.execute_comparison(
            arrays, labels, ids, groups, folds,
            model_factory=failing_factory, epochs=1, batch_size=8,
        )
    assert len(attempts) == 3


def test_attempt_marker_cannot_be_reused_or_overwritten(tmp_path):
    marker = tmp_path / "attempt.json"
    adaptation.consume_attempt(marker, {"scope": "generated-test"})
    original = marker.read_bytes()
    with pytest.raises(FileExistsError):
        adaptation.consume_attempt(marker, {"scope": "second-attempt"})
    assert marker.read_bytes() == original


def test_no_opt_in_blocks_before_any_file_access(monkeypatch, tmp_path):
    def forbidden_access(*args, **kwargs):
        raise AssertionError("File access occurred before opt-in")

    monkeypatch.setattr(Path, "open", forbidden_access)
    with pytest.raises((ValueError, PermissionError), match="(?i)opt"):
        adaptation.run_authorized(
            tmp_path / "never-read-root",
            tmp_path / "never-read-weights",
            tmp_path / "never-create-output",
            tmp_path / "never-read-authorization",
            opt_in=False,
        )


def test_opt_in_alone_does_not_replace_generated_qualification(monkeypatch, tmp_path):
    def forbidden_access(*args, **kwargs):
        raise AssertionError("File access occurred before qualification")

    monkeypatch.setattr(Path, "open", forbidden_access)
    with pytest.raises((ValueError, PermissionError), match="(?i)qualif"):
        adaptation.run_authorized(
            tmp_path / "never-read-root",
            tmp_path / "never-read-weights",
            tmp_path / "never-create-output",
            tmp_path / "never-read-authorization",
            opt_in=True,
            qualification=None,
        )


def test_metric_report_uses_actual_multiclass_brier_field():
    labels = np.array([1, 2, 3, 4])
    probabilities = np.full((4, 4), 0.25)
    candidate = 0.8 * np.eye(4) + 0.2 * probabilities
    metrics = {
        "head_only": adaptation.base.measure(labels, probabilities),
        "last_block": adaptation.base.measure(labels, candidate),
    }
    differences = adaptation.metric_differences(metrics)
    assert differences["multiclass_brier"] == pytest.approx(-0.72)
    assert differences["accuracy"] == pytest.approx(0.75)
