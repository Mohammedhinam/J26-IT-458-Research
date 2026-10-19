"""Synthetic checks for the isolated rank-consistent ordinal crop head."""

import pytest
import torch
import json
import zipfile
from PIL import Image
from types import SimpleNamespace

from src.vision.roi_ordinal_v2 import (
    CoralHead,
    _build_model,
    _predict_two_arms_with_detector,
    create_return_bundle,
    coral_class_probabilities,
    coral_grade_predictions,
    coral_loss,
    ordinal_targets,
)


def test_ordinal_target_encoding_preserves_grade_order():
    grades = torch.tensor([0, 1, 2, 3, 4])
    expected = torch.tensor([
        [0, 0, 0, 0],
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [1, 1, 1, 0],
        [1, 1, 1, 1],
    ], dtype=torch.float32)
    assert torch.equal(ordinal_targets(grades), expected)


def test_coral_head_emits_four_ordered_threshold_logits():
    torch.manual_seed(7)
    head = CoralHead(input_features=8, num_classes=5)
    logits = head(torch.randn(16, 8))
    assert logits.shape == (16, 4)
    assert torch.all(logits[:, :-1] > logits[:, 1:])


def test_coral_probabilities_are_valid_and_sum_to_one():
    logits = torch.tensor([[2.0, 1.0, -1.0, -2.0], [0.4, -0.2, -0.8, -1.3]])
    probabilities = coral_class_probabilities(logits)
    assert probabilities.shape == (2, 5)
    assert torch.all(probabilities >= 0)
    assert torch.allclose(probabilities.sum(dim=1), torch.ones(2), atol=1e-6)


def test_coral_median_prediction_counts_positive_thresholds():
    logits = torch.tensor([[2.0, 1.0, -1.0, -2.0], [-2.0, -3.0, -4.0, -5.0]])
    assert coral_grade_predictions(logits).tolist() == [2, 0]


def test_coral_rejects_rank_inconsistent_logits():
    logits = torch.tensor([[1.0, -1.0, 0.5, -2.0]])
    with pytest.raises(ValueError, match="rank-consistent"):
        coral_class_probabilities(logits)
    with pytest.raises(ValueError, match="rank-consistent"):
        coral_grade_predictions(logits)


def test_coral_loss_is_finite_and_differentiable():
    torch.manual_seed(11)
    head = CoralHead(input_features=4, num_classes=5)
    features = torch.randn(10, 4, requires_grad=True)
    grades = torch.tensor([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    loss = coral_loss(head(features), grades)
    loss.backward()
    assert torch.isfinite(loss)
    assert features.grad is not None
    assert head.shared_score.weight.grad is not None
    assert head.raw_threshold_gaps.grad is not None


def test_coral_loss_rejects_labels_outside_zero_to_four():
    logits = torch.zeros(2, 4)
    grades = torch.tensor([1, 5])
    with pytest.raises(ValueError, match="0 to 4"):
        coral_loss(logits, grades)


def test_both_classifier_heads_accept_a_resnet_image_batch():
    batch = torch.randn(2, 3, 224, 224)
    ce_model = _build_model("weighted_ce", pretrained=False)
    coral_model = _build_model("coral", pretrained=False)
    assert ce_model(batch).shape == (2, 5)
    assert coral_model(batch).shape == (2, 4)


class FakeDetector:
    def predict(self, *, source, **kwargs):
        box = SimpleNamespace(
            cls=torch.tensor([0.0]),
            xyxy=torch.tensor([[15.0, 15.0, 55.0, 55.0]]),
        )
        return [SimpleNamespace(path=source[0], boxes=box)]


class FixedCeClassifier(torch.nn.Module):
    def forward(self, batch):
        logits = torch.zeros(len(batch), 5)
        logits[:, 3] = 5.0
        return logits


class FixedCoralClassifier(torch.nn.Module):
    def forward(self, batch):
        return torch.tensor([2.0, 1.0, -1.0, -2.0], device=batch.device).repeat(len(batch), 1)


def test_same_detected_roi_is_scored_by_both_arms(tmp_path):
    image_path = tmp_path / "00042.jpg"
    Image.new("RGB", (80, 80), (120, 80, 100)).save(image_path)
    predictions = _predict_two_arms_with_detector(
        FakeDetector(), FixedCeClassifier(), FixedCoralClassifier(), [image_path],
        device="cpu", detector_batch=1, crop_batch=8,
    )
    assert predictions["weighted_ce"][0]["source_record_id"] == "Training/00042"
    assert predictions["weighted_ce"][0]["predicted_image_grade"] == 3
    assert predictions["coral"][0]["predicted_image_grade"] == 2
    assert predictions["weighted_ce"][0]["predicted_tooth_roi_count"] == 1
    assert predictions["coral"][0]["predicted_tooth_roi_count"] == 1


def test_new_return_bundle_is_integrity_checked_and_existing_bundle_preserved(tmp_path):
    output_root = tmp_path / "v2_run"
    detector_root = tmp_path / "v1_return"
    return_zip = tmp_path / "v2_return.zip"
    output_root.mkdir()
    detector_root.mkdir()
    config = {"experiment": "synthetic-only", "seed": 7}
    (output_root / "run_configuration.json").write_text(json.dumps(config))
    (output_root / "oof_metrics.json").write_text("{}")
    (output_root / "weighted_ce_oof_predictions.csv").write_text("id\n")
    (output_root / "coral_oof_predictions.csv").write_text("id\n")
    (output_root / "experiment_complete.json").write_text(json.dumps({"status": "all_requested_folds_completed"}))
    (output_root / "completed_folds.json").write_text("{}")
    for fold in range(5):
        fold_name = f"fold_{fold:02d}"
        coral_dir = output_root / fold_name / "coral"
        coral_dir.mkdir(parents=True)
        (coral_dir / "checkpoint_last.pt").write_bytes(f"coral-{fold}".encode())
        (output_root / fold_name / "fold_metrics.json").write_text("{}")
        detector_dir = detector_root / fold_name
        detector_dir.mkdir()
        (detector_dir / "detector_last.pt").write_bytes(f"detector-{fold}".encode())

    first = create_return_bundle(output_root, detector_root, return_zip)
    assert first["status"] == "created"
    original_hash = first["sha256"]
    with zipfile.ZipFile(return_zip) as archive:
        assert archive.testzip() is None
        assert "fold_00/coral_classifier_last.pt" in archive.namelist()
        assert "fold_00/detector_last.pt" in archive.namelist()

    second = create_return_bundle(output_root, detector_root, return_zip)
    assert second["status"] == "existing_return_preserved"
    assert second["sha256"] == original_hash

    (output_root / "run_configuration.json").write_text(json.dumps({"experiment": "different"}))
    with pytest.raises(ValueError, match="another run"):
        create_return_bundle(output_root, detector_root, return_zip)
