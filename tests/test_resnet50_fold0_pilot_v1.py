"""Generated-only qualification. No dental pixels/checkpoints or CUDA training."""
import copy
import json

import numpy as np
import pytest
import torch

from src.vision import resnet50_fold0_pilot_v1 as pilot


class TinyResNet(torch.nn.Module):
    """Small module boundaries for checking the optimizer/BN contract on CPU."""
    def __init__(self):
        super().__init__()
        self.stem = torch.nn.Conv2d(3, 4, 1)
        self.layer4 = torch.nn.Sequential(*[
            torch.nn.Sequential(torch.nn.Conv2d(4, 4, 1, bias=False),
                                torch.nn.BatchNorm2d(4), torch.nn.ReLU()) for _ in range(3)])
        self.fc = torch.nn.Linear(4, 4)

    def forward(self, values):
        return self.fc(self.layer4(self.stem(values)).mean((2, 3)))


@pytest.fixture(autouse=True)
def cpu_threads():
    before = torch.get_num_threads()
    torch.set_num_threads(2)
    yield
    torch.set_num_threads(before)


@pytest.mark.parametrize("stage,convolutions", [("warmup", 0), ("A", 1), ("B", 3)])
def test_stage_allowlist_and_frozen_batchnorm(stage, convolutions):
    model = TinyResNet()
    groups, names = pilot.configure(model, stage)
    assert len(names) == 2 + convolutions
    assert {n for n in names if n.startswith("fc.")} == {"fc.weight", "fc.bias"}
    assert groups[0]["lr"] == .001
    if stage != "warmup":
        assert groups[1]["lr"] == .00001
    assert len({id(p) for group in groups for p in group["params"]}) == len(names)
    assert all(not m.training for m in model.modules())
    for m in model.modules():
        if isinstance(m, torch.nn.BatchNorm2d):
            assert not any(p.requires_grad for p in m.parameters())


def test_actual_resnet50_layer_names_and_four_grade_head():
    from torchvision.models import resnet50
    model = resnet50(weights=None)
    model.fc = torch.nn.Linear(2048, 4)
    _, a = pilot.configure(model, "A")
    assert set(a) == {"fc.weight", "fc.bias", "layer4.2.conv1.weight",
                      "layer4.2.conv2.weight", "layer4.2.conv3.weight"}
    _, b = pilot.configure(model, "B")
    assert set(a) < set(b)
    assert len(b) == 12
    assert not any("bn" in name or "downsample.1" in name for name in b)


def test_unknown_stage_rejected():
    with pytest.raises(ValueError):
        pilot.configure(TinyResNet(), "all_backbone")


def test_class_weights_use_fit_counts_only():
    labels = np.repeat([1, 2, 3, 4], [9, 67, 179, 289])
    np.testing.assert_allclose(pilot.class_weights(labels), 544 / (4 * np.array([9, 67, 179, 289])), rtol=1e-7)


@pytest.mark.parametrize("labels", [[1, 2, 3], [0, 1, 2, 3], [1., 2., 3., 4.], [[1, 2, 3, 4]]])
def test_bad_class_mapping_rejected(labels):
    with pytest.raises(ValueError):
        pilot.class_weights(labels)


def test_hand_computed_metrics():
    probabilities = np.eye(4)[[0, 1, 3, 3]]
    result = pilot.measure(np.array([1, 2, 3, 4]), probabilities)
    assert result["accuracy"] == .75
    assert result["balanced_accuracy"] == .75
    assert result["macro_f1"] == pytest.approx(2/3)
    assert result["per_grade_recall"] == {"1": 1., "2": 1., "3": 0., "4": 1.}
    assert result["ordinal_mae"] == .25
    # Observed squared disagreement=.25; independent-marginal expectation=3.
    assert result["quadratic_weighted_kappa"] == pytest.approx(1 - .25/3)
    assert result["confusion_matrix"] == [[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,0,1]]


@pytest.mark.parametrize("scores", [np.zeros((4,4)), np.full((4,4), np.nan), np.ones((4,5)),
                                    np.tile([-.1,.4,.4,.3], (4,1))])
def test_invalid_probabilities_fail(scores):
    with pytest.raises(ValueError):
        pilot.measure(np.array([1, 2, 3, 4]), scores)


def test_generated_stages_match_and_resume_without_extra_steps(tmp_path, monkeypatch):
    torch.manual_seed(42)
    model = TinyResNet()
    arrays = np.random.default_rng(2).normal(0, .25, (8,3,8,8)).astype(np.float32)
    labels = np.array([1,2,3,4]*2)
    binding = {"generated_only": True}
    initial = pilot.state_hashes(model)
    pilot.train_stage(model, "warmup", arrays, labels, tmp_path / "warmup", binding, "cpu")
    shared = copy.deepcopy(model.state_dict())
    for arm in ("A", "B"):
        model.load_state_dict(shared)
        pilot.train_stage(model, arm, arrays, labels, tmp_path / arm, binding, "cpu")
        saved = torch.load(tmp_path / arm / "epoch_05.pt", weights_only=True)
        for name, value in initial.items():
            if "1.running_" in name or "1.num_batches_tracked" in name or name.startswith("stem."):
                assert saved["tensor_hashes"][name] == value
    a = torch.load(tmp_path / "A/epoch_05.pt", weights_only=True)
    b = torch.load(tmp_path / "B/epoch_05.pt", weights_only=True)
    assert a["initial_tensor_hashes"] == b["initial_tensor_hashes"]
    assert a["order_sha256"] == b["order_sha256"]
    before = pilot.sha256_file(tmp_path / "A/epoch_05.pt")
    def forbidden(*args, **kwargs):
        raise AssertionError("Resume must not execute an extra optimization step")
    monkeypatch.setattr(pilot, "train_epoch", forbidden)
    model.load_state_dict(shared)
    pilot.train_stage(model, "A", arrays, labels, tmp_path / "A", binding, "cpu")
    assert pilot.sha256_file(tmp_path / "A/epoch_05.pt") == before
    model.load_state_dict(shared)
    with pytest.raises(ValueError, match="provenance"):
        pilot.train_stage(model, "A", arrays, labels, tmp_path / "A", {"changed": True}, "cpu")


def test_future_training_gate_fails_before_access(tmp_path):
    with pytest.raises(PermissionError):
        pilot.run(tmp_path / "absent_data", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_cuda_required_without_cpu_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="CUDA"):
        pilot.run(tmp_path / "absent_data", tmp_path / "out", execute=True,
                  approval=pilot.APPROVAL_TEXT, manifest_sha="a"*64)


def test_non_imagenet_initial_checkpoint_rejected(tmp_path, monkeypatch):
    path = tmp_path / "untrusted.pt"
    path.write_bytes(b"not official imagenet weights")
    def forbidden(*args, **kwargs):
        raise AssertionError("Untrusted bytes must not be deserialized")
    monkeypatch.setattr(torch, "load", forbidden)
    with pytest.raises(ValueError, match="Non-ImageNet"):
        pilot.model_factory(path)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "missing"])
def test_package_path_failures(tmp_path, name):
    with pytest.raises(ValueError):
        pilot.safe_path(tmp_path, name)


def test_symlink_and_overwrite_rejected(tmp_path):
    (tmp_path / "original").write_text("preserve")
    (tmp_path / "link").symlink_to(tmp_path / "original")
    with pytest.raises(ValueError):
        pilot.safe_path(tmp_path, "link")
    with pytest.raises(FileExistsError):
        pilot.write_json(tmp_path / "original", {})
    assert (tmp_path / "original").read_text() == "preserve"


@pytest.fixture
def generated_manifest(monkeypatch):
    score_grades = np.repeat([1,2,3,4], [3,17,44,72]).tolist()
    fit_grades = np.repeat([1,2,3,4], [9,67,179,289]).tolist()
    rows = [{"id": f"Training/{i:05}", "role": "score" if i < 136 else "fit", "grade": grade,
             "group": f"group-{i}", "source_sha256": f"source-{i}", "array": f"arrays/{i:05}.npy"}
            for i, grade in enumerate(score_grades + fit_grades)]
    folds = [0]*136 + [1]*544
    monkeypatch.setattr(pilot, "FOLDS_SHA", pilot.digest(folds))
    membership = {"ids": [r["id"] for r in rows], "roles": [r["role"] for r in rows],
                  "grades": [r["grade"] for r in rows], "groups": [r["group"] for r in rows]}
    return {"version": pilot.VERSION, "config": pilot.CONFIG, "source_manifest_sha256": pilot.SOURCE_MANIFEST_SHA,
            "fold_assignment_sha256": pilot.FOLDS_SHA, "qualified_labels_approved": False,
            "participant_independence_verified": False, "records": rows,
            "membership_sha256": pilot.digest(membership), "cam_ids": [r["id"] for r in rows[:8]],
            "fold_snapshot": {"ids": membership["ids"], "folds": folds}}


def test_metadata_partition_passes(generated_manifest):
    assert len(pilot.validate_records(generated_manifest)) == 680


@pytest.mark.parametrize("kind", ["validation", "grade0", "duplicate", "group_leak", "source_alias",
                                  "role_swap", "clinical_claim", "fold_binding"])
def test_corrupt_partition_metadata_fails(generated_manifest, kind):
    manifest = copy.deepcopy(generated_manifest)
    rows = manifest["records"]
    if kind == "validation": rows[0]["id"] = "Validation/00000"
    if kind == "grade0": rows[0]["grade"] = 0
    if kind == "duplicate": rows[1]["id"] = rows[0]["id"]
    if kind == "group_leak": rows[136]["group"] = rows[0]["group"]
    if kind == "source_alias": rows[136]["source_sha256"] = rows[0]["source_sha256"]
    if kind == "role_swap": rows[0]["role"], rows[136]["role"] = "fit", "score"
    if kind == "clinical_claim": manifest["qualified_labels_approved"] = True
    if kind == "fold_binding": manifest["fold_snapshot"]["folds"][0] = 1
    with pytest.raises(ValueError):
        pilot.validate_records(manifest)


def test_generated_gradcam_preserves_original_geometry_and_weights():
    torch.manual_seed(1)
    model = TinyResNet()
    original = np.full((12,18,3), 180, np.uint8)
    prepared = pilot.cam.RGBInput(original, np.ones((3,8,8), np.float32), (0,1,8,6))
    before = pilot.state_hashes(model)
    views, detail = pilot.gradcam(model, prepared, target_index=1)
    assert detail["explained_grade"] == 2
    assert views["overlay"].shape == original.shape
    np.testing.assert_array_equal(views["original"], original)
    assert pilot.state_hashes(model) == before
    assert not model.layer4[-1]._forward_hooks
    assert all(p.grad is None for p in model.parameters())


def test_preflight_receipt_binds_manifest_not_last_array(tmp_path, monkeypatch):
    # Two generated arrays exercise the complete file loop without study data.
    rows = []
    for number, role in enumerate(("fit", "score")):
        path = tmp_path / (role + ".npy")
        np.save(path, np.full((224,224,3), number / 2, np.float32), allow_pickle=False)
        rows.append({"role": role, "array": path.name, "array_sha256": pilot.sha256_file(path),
                     "valid_box": [0,0,224,224], "source_dimensions": [224,224]})
    (tmp_path / "weights").mkdir()
    weights = tmp_path / "weights/resnet50-11ad3fa6.pth"
    weights.write_bytes(b"generated-weight-integrity-fixture-only")
    monkeypatch.setattr(pilot, "WEIGHTS_SHA", pilot.sha256_file(weights))
    manifest = {"cam_ids": [], "files": {
        p.relative_to(tmp_path).as_posix(): {"bytes": p.stat().st_size, "sha256": pilot.sha256_file(p)}
        for p in tmp_path.rglob("*") if p.is_file()}}
    pilot.write_json(tmp_path / "manifest.json", manifest)
    monkeypatch.setattr(pilot, "validate_records", lambda value: rows)
    expected = pilot.sha256_file(tmp_path / "manifest.json")
    result = pilot.preflight(tmp_path, expected)
    assert result["manifest_sha256"] == expected
    assert result["manifest_sha256"] != rows[-1]["array_sha256"]
    with pytest.raises(ValueError, match="Manifest SHA"):
        pilot.preflight(tmp_path, rows[-1]["array_sha256"])
