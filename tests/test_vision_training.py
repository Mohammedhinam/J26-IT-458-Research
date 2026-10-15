"""Focused synthetic scaffold tests; no clinical images, source manifests or downloads."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json

import numpy as np
from PIL import Image
import pytest

from src.vision import train_pipeline as tp


def configuration(**changes):
    return replace(tp.TrainingConfig("resnet50", 5, 3, 0.001, 3), **changes)


def approved_fixture():
    # Fabricated metadata for gate tests only, never an approval for dental data.
    records = []
    for split in ["Training", "Validation", "Test"]:
        for index in range(2):
            row = {"image_path": f"{split}/{index}.png", "original_split": split,
                   "analysis_split": split, "content_group_id": f"content-{split}-{index}",
                   "participant_id": f"person-{split}-{index}"}
            if split != "Test":
                row.update(label_status="verified", mgi_grade=index + 1,
                           label_provenance={"source_reference": "synthetic caption",
                                             "qualified_reviewer": "synthetic fixture", "date": "test",
                                             "source_kind": "caption_csv",
                                             "target_definition": "maximum_visible_mgi"})
            records.append(row)
    return {"status": "approved", "approval": {
        "labels_approved": True, "split_approved": True, "duplicate_review_complete": True,
        "participant_independence_verified": True, "qualified_reviewer": "synthetic fixture",
        "date": "test", "evidence_reference": "synthetic only"}, "records": records}


@pytest.mark.parametrize("changes", [dict(batch_size=0), dict(epochs=True), dict(patience=-1),
    dict(learning_rate=0), dict(learning_rate=float("nan")), dict(min_delta=-1),
    dict(seed=-1), dict(batchnorm="train_selected"), dict(freeze_backbone=False),
    dict(class_weight="smote"), dict(device="test"), dict(unfreeze_prefixes=["layer4"])])
def test_invalid_configuration_is_rejected(changes):
    with pytest.raises(ValueError):
        configuration(**changes).validate()


def test_valid_head_and_selected_finetuning_configuration():
    configuration().validate()
    configuration(freeze_backbone=False, unfreeze_prefixes=("layer4",), batchnorm="train_selected").validate()


def test_manifest_gate_preserves_sources_and_never_returns_test():
    manifest = approved_fixture()
    before = deepcopy(manifest)
    partitions = tp.approved_partitions(manifest, lambda m: True)
    assert set(partitions) == {"Training", "Validation"}
    assert len(partitions["Training"]) == len(partitions["Validation"]) == 2
    assert manifest == before and all("Test" not in r["image_path"] for rows in partitions.values() for r in rows)
    # Test has no labels/provenance at all and is accepted as sealed metadata.
    assert all("mgi_grade" not in r for r in manifest["records"] if r["analysis_split"] == "Test")


@pytest.mark.parametrize("field", ["labels_approved", "split_approved", "duplicate_review_complete",
                                   "participant_independence_verified", "evidence_reference"])
def test_missing_approval_fails_closed(field):
    manifest = approved_fixture()
    del manifest["approval"][field]
    with pytest.raises(ValueError, match="approval evidence"):
        tp.approved_partitions(manifest, lambda m: True)


@pytest.mark.parametrize("verifier", [None, lambda m: False, lambda m: "approved"])
def test_external_authentication_is_required(verifier):
    with pytest.raises(ValueError, match="External"):
        tp.approved_partitions(approved_fixture(), verifier)


@pytest.mark.parametrize("field", ["content_group_id", "participant_id"])
def test_cross_split_group_overlap_fails_before_image_loading(field):
    manifest = approved_fixture()
    manifest["records"][4][field] = manifest["records"][0][field]
    with pytest.raises(ValueError, match="crosses splits"):
        tp.approved_partitions(manifest, lambda m: True)


@pytest.mark.parametrize("field", ["label_status", "mgi_grade", "label_provenance", "participant_id"])
def test_unverified_or_unknown_evidence_is_blocked(field):
    manifest = approved_fixture()
    del manifest["records"][0][field]
    with pytest.raises(ValueError):
        tp.approved_partitions(manifest, lambda m: True)


def test_original_test_cannot_be_moved_to_development():
    manifest = approved_fixture()
    manifest["records"][4]["analysis_split"] = "Training"
    with pytest.raises(ValueError, match="Original Test"):
        tp.approved_partitions(manifest, lambda m: True)


def test_same_split_duplicates_are_not_silently_sampled_twice():
    manifest = approved_fixture()
    manifest["records"][1]["content_group_id"] = manifest["records"][0]["content_group_id"]
    with pytest.raises(ValueError, match="Repeated content"):
        tp.approved_partitions(manifest, lambda m: True)


def test_txt_only_label_provenance_is_not_a_classification_label():
    manifest = approved_fixture()
    manifest["records"][0]["label_provenance"]["source_kind"] = "yolo_txt"
    with pytest.raises(ValueError, match="caption label provenance"):
        tp.approved_partitions(manifest, lambda m: True)


@pytest.mark.parametrize("path", ["../Test/secret.png", "/Test/secret.png", "Training/0.png"])
def test_unsafe_or_duplicate_manifest_paths(path):
    manifest = approved_fixture()
    manifest["records"][1]["image_path"] = path
    with pytest.raises(ValueError, match="path"):
        tp.approved_partitions(manifest, lambda m: True)


def test_loader_never_opens_test_and_reuses_rgb_preprocessing(tmp_path):
    partitions = tp.approved_partitions(approved_fixture(), lambda m: True)
    opened = []
    def reader(path):
        opened.append(path)
        return Image.new("RGB", (8, 4), (200, 30, 40))
    dataset = tp.RGBDataset(partitions["Training"], tmp_path, "Training", reader)
    image, label = dataset[0]
    assert image.shape == (3, 224, 224) and label == 1
    assert len(opened) == 1 and "Test" not in str(opened[0])
    with pytest.raises(ValueError):
        tp.RGBDataset(approved_fixture()["records"][4:], tmp_path, "Test", reader)
    with pytest.raises(ValueError):
        tp.RGBDataset(partitions["Validation"], tmp_path, "Training", reader)


def test_symlink_escape_is_rejected_before_read(tmp_path):
    (tmp_path / "Training").symlink_to(tmp_path.parent, target_is_directory=True)
    rows = approved_fixture()["records"][:2]
    dataset = tp.RGBDataset(rows, tmp_path, "Training", lambda p: pytest.fail("Must not read"))
    with pytest.raises(ValueError, match="escapes"):
        dataset[0]


def test_training_only_weighting_preserves_absent_zero_class():
    weights = tp.class_weights([1, 1, 1, 2], "balanced")
    np.testing.assert_allclose(weights, [0, 2/3, 2, 0, 0])
    assert tp.class_weights([1, 2], "none") is None
    with pytest.raises(ValueError):
        tp.class_weights([1, 7], "balanced")


def test_metric_correctness_known_perfect_and_uniform_examples():
    truth = np.arange(5)
    perfect = tp.validation_metrics(truth, np.eye(5))
    assert perfect["macro_f1_five_schema"] == perfect["quadratic_weighted_kappa"] == 1
    assert perfect["macro_auroc_five_schema"] == 1 and perfect["multiclass_brier"] == perfect["ordinal_mae"] == 0
    uniform = tp.validation_metrics(truth, np.full((5, 5), 0.2))
    assert uniform["macro_auroc_five_schema"] == 0.5
    assert uniform["multiclass_brier"] == pytest.approx(0.8)
    assert uniform["macro_f1_five_schema"] == pytest.approx(1/15)
    assert uniform["ordinal_mae"] == 2 and uniform["confusion_matrix"][4][0] == 1


def test_missing_class_metrics_are_explicit_and_json_safe():
    values = tp.validation_metrics([1, 2], np.eye(5)[[1, 2]])
    assert values["missing_grades"] == [0, 3, 4]
    assert values["per_grade_recall"][0] is None and values["per_grade_auroc"][0] is None
    assert values["macro_auroc_five_schema"] is None
    assert values["macro_f1_five_schema"] == 0.4 and values["macro_f1_supported_grades"] == 1
    json.dumps(values, allow_nan=False)


@pytest.mark.parametrize("probability", [np.ones((2, 5)), np.full((2, 5), np.nan), np.zeros((2, 4))])
def test_invalid_probability_metrics_fail(probability):
    with pytest.raises(ValueError):
        tp.validation_metrics([1, 2], probability)


def test_early_stopping_ties_do_not_replace_best():
    assert tp.stopping_update(0.3, 0.3, 1, 2, 0) == (0.3, 2, False)
    assert tp.stopping_update(0.4, 0.3, 1, 2, 0) == (0.4, 0, True)
    with pytest.raises(ValueError):
        tp.stopping_update(float("nan"), 0.3, 0, 2, 0)


def test_protocol_is_required_before_any_model_or_dataset_access(monkeypatch, tmp_path):
    monkeypatch.setattr(tp.vp, "make_model", lambda *a, **k: pytest.fail("Model construction must be blocked"))
    with pytest.raises(ValueError, match="configuration"):
        tp.fit_approved(approved_fixture(), tmp_path, configuration(), tmp_path / "run", lambda m: True, None)


def torch_backend():
    return pytest.importorskip("torch", reason="New trainer backend requires compatible Colab runtime")


def tiny_model(torch):
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.features = torch.nn.Sequential(torch.nn.Conv2d(3, 2, 1), torch.nn.BatchNorm2d(2),
                                                torch.nn.AdaptiveAvgPool2d(1), torch.nn.Flatten())
            self.fc = torch.nn.Sequential(torch.nn.Dropout(0.2), torch.nn.Linear(2, 5))
        def forward(self, image):
            return self.fc(self.features(image))
    return Tiny()


def test_frozen_backbone_bn_and_validation_no_grad():
    torch = torch_backend()
    model = tiny_model(torch)
    config = configuration()
    tp.configure_trainable_layers(model, config)
    before = {k: v.clone() for k, v in model.features.state_dict().items()}
    loader = torch.utils.data.DataLoader(tp.synthetic_data("Training", 5), batch_size=5)
    criterion = torch.nn.CrossEntropyLoss(reduction="sum")
    optimizer = torch.optim.Adam((p for p in model.parameters() if p.requires_grad), lr=0.01)
    tp.run_epoch(model, loader, criterion, config, optimizer)
    assert not model.features.training and model.fc.training
    assert all(torch.equal(value, model.features.state_dict()[name]) for name, value in before.items())
    assert all(p.grad is None for p in model.features.parameters())
    for p in model.parameters():
        p.grad = None
    snapshot = {k: v.clone() for k, v in model.state_dict().items()}
    measured = tp.run_epoch(model, loader, criterion, config)
    assert measured["n"] == 5 and all(p.grad is None for p in model.parameters())
    assert all(torch.equal(value, model.state_dict()[name]) for name, value in snapshot.items())


def test_selected_batchnorm_updates_only_approved_module():
    torch = torch_backend()
    model = tiny_model(torch)
    config = configuration(freeze_backbone=False, unfreeze_prefixes=("features.0",), batchnorm="train_selected")
    tp.configure_trainable_layers(model, config)
    tp.training_mode(model, config)
    assert model.features[0].weight.requires_grad and not model.features[1].training
    config = replace(config, unfreeze_prefixes=("features",))
    tp.configure_trainable_layers(model, config)
    tp.training_mode(model, config)
    assert model.features[1].training
    with pytest.raises(ValueError):
        tp.configure_trainable_layers(model, replace(config, unfreeze_prefixes=("missing",)))


def test_checkpoint_resume_matches_uninterrupted_and_reproducible(tmp_path):
    torch = torch_backend()
    config = configuration()
    train, val = tp.synthetic_data("Training"), tp.synthetic_data("Validation")
    context = {"synthetic": True}
    def fresh():
        tp.seed_everything(config.seed)
        return tiny_model(torch)
    full_model, interrupted_model = fresh(), fresh()
    full = tp._fit(full_model, train, val, config, tmp_path / "full", context)
    tp._fit(interrupted_model, train, val, config, tmp_path / "resume", context, stop_after=1)
    resumed = tp._fit(fresh(), train, val, config, tmp_path / "resume", context,
                      resume=tmp_path / "resume/last.pt")
    assert full["history"] == resumed["history"] and full["best_epoch"] == resumed["best_epoch"]
    full_last = torch.load(tmp_path / "full/last.pt", weights_only=True)
    resumed_last = torch.load(tmp_path / "resume/last.pt", weights_only=True)
    assert all(torch.equal(v, resumed_last["model"][k]) for k, v in full_last["model"].items())
    for changed in [replace(config, seed=9), config]:
        changed_context = context if changed.seed == 9 else {"synthetic": "different manifest"}
        with pytest.raises(ValueError, match="identity mismatch"):
            tp._fit(fresh(), train, val, changed, tmp_path / "resume", changed_context,
                    resume=tmp_path / "resume/last.pt")


def test_early_stopping_and_best_checkpoint_reload(tmp_path):
    torch = torch_backend()
    config = configuration(epochs=5, patience=1, min_delta=1.0)
    tp.seed_everything(config.seed)
    model = tiny_model(torch)
    result = tp._fit(model, tp.synthetic_data("Training"), tp.synthetic_data("Validation"),
                     config, tmp_path / "early", {"synthetic": True})
    assert result["early_stopped"] and result["best_epoch"] == 1 and len(result["history"]) == 2
    best = torch.load(tmp_path / "early/best.pt", weights_only=True)
    assert all(torch.equal(v, model.state_dict()[k]) for k, v in best["model"].items())


@pytest.mark.parametrize("architecture", ["resnet50", "efficientnet_b0"])
def test_actual_architecture_generated_train_validation_step(architecture):
    torch = torch_backend()
    pytest.importorskip("torchvision")
    config = configuration(architecture=architecture, epochs=1)
    tp.seed_everything(config.seed)
    model = tp.vp.make_model(architecture, pretrained=False, allow_download=False)["model"]
    tp.configure_trainable_layers(model, config)
    backbone = {k: v.clone() for k, v in model.state_dict().items()
                if not k.startswith("fc.") and not k.startswith("classifier.")}
    criterion = torch.nn.CrossEntropyLoss(reduction="sum")
    optimizer = torch.optim.Adam((p for p in model.parameters() if p.requires_grad), lr=config.learning_rate)
    loader = torch.utils.data.DataLoader(tp.synthetic_data("Training", 5), batch_size=5)
    measured = tp.run_epoch(model, loader, criterion, config, optimizer)
    assert measured["n"] == 5 and math_is_finite(measured["loss"])
    assert all(torch.equal(v, model.state_dict()[k]) for k, v in backbone.items())
    before = {k: v.clone() for k, v in model.state_dict().items()}
    validation = torch.utils.data.DataLoader(tp.synthetic_data("Validation", 5), batch_size=5)
    assert tp.run_epoch(model, validation, criterion, config)["n"] == 5
    assert all(torch.equal(v, model.state_dict()[k]) for k, v in before.items())


def math_is_finite(value):
    return np.isfinite(value)


def test_generated_smoke_supports_checkpoint_reload_and_resume(tmp_path):
    torch_backend()
    result = tp.synthetic_smoke(tmp_path / "smoke")
    assert result["checkpoint_reload_and_resume"] and not result["test_used"]
    assert len(result["history"]) == 2
