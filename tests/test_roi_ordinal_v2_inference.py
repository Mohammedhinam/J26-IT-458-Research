from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from PIL import Image

from src.vision.roi_ordinal_v2_demo import _render_coral_overlay, _verified_checkpoint_pair
from src.vision.roi_ordinal_v2_inference import load_coral_roi_models, predict_coral_tooth_rois


class FakeDetector:
    def __init__(self, classes=(0, 0)):
        self.boxes = []
        for index, class_id in enumerate(classes):
            left = 8 + index * 24
            self.boxes.append(SimpleNamespace(
                cls=torch.tensor([class_id]),
                xyxy=torch.tensor([[left, 10, left + 18, 36]], dtype=torch.float32),
                conf=torch.tensor([0.9 - index * 0.1]),
            ))

    def predict(self, **kwargs):
        return [SimpleNamespace(boxes=self.boxes)]


class FakeCoralClassifier(torch.nn.Module):
    def forward(self, crops):
        logits = torch.tensor([2.0, 1.0, -1.0, -2.0], device=crops.device)
        return logits.unsqueeze(0).repeat(crops.shape[0], 1)


def test_coral_roi_inference_returns_per_crop_probabilities_and_max_grade(tmp_path: Path) -> None:
    photo_path = tmp_path / "photo.jpg"
    Image.new("RGB", (96, 64), (120, 80, 60)).save(photo_path)

    result = predict_coral_tooth_rois(
        FakeDetector(), FakeCoralClassifier(), photo_path, device="cpu",
    )

    assert result["model_family"] == "roi_tooth_v2_coral"
    assert result["image_mgi_grade"] == 2
    assert len(result["detections"]) == 2
    assert all(row["grade"] == 2 for row in result["detections"])
    assert all(abs(sum(row["grade_probabilities"].values()) - 1.0) < 1e-5 for row in result["detections"])
    assert result["detections"][0]["detector_confidence"] == pytest.approx(0.9)
    assert "confidence" not in result["detections"][0]
    assert result["label_status"] == "provisional; not clinically verified"
    assert "not clinical gum boundaries" in result["notice"]


def test_no_detected_rois_is_an_abstention_not_grade_zero(tmp_path: Path) -> None:
    photo_path = tmp_path / "photo.jpg"
    Image.new("RGB", (96, 64), (120, 80, 60)).save(photo_path)

    result = predict_coral_tooth_rois(
        FakeDetector(classes=()), FakeCoralClassifier(), photo_path, device="cpu",
    )

    assert result["image_mgi_grade"] is None
    assert result["no_detection"] is True
    assert result["detections"] == []


def test_inference_rejects_non_tooth_detector_class(tmp_path: Path) -> None:
    photo_path = tmp_path / "photo.jpg"
    Image.new("RGB", (96, 64), (120, 80, 60)).save(photo_path)

    with pytest.raises(ValueError, match="only the tooth_roi class"):
        predict_coral_tooth_rois(
            FakeDetector(classes=(2,)), FakeCoralClassifier(), photo_path, device="cpu",
        )


def test_coral_overlay_is_separate_and_marks_research_only(tmp_path: Path) -> None:
    photo_path = tmp_path / "photo.jpg"
    overlay_path = tmp_path / "overlay.png"
    original = Image.new("RGB", (96, 64), (120, 80, 60))
    original.save(photo_path)

    result = _render_coral_overlay(photo_path, {
        "detections": [{"grade": 2, "detector_confidence": 0.9, "xyxy": [10, 10, 50, 50]}],
    }, overlay_path)

    assert result == overlay_path
    assert photo_path.read_bytes() != overlay_path.read_bytes()
    with Image.open(overlay_path) as image:
        assert image.size == (96, 64)
        assert image.getpixel((0, 63)) == (32, 32, 32)


def test_coral_loader_rejects_wrong_arm_or_fold_before_model_loading(tmp_path: Path) -> None:
    detector_path = tmp_path / "detector.pt"
    classifier_path = tmp_path / "classifier.pt"
    detector_path.write_bytes(b"not loaded before the guard")
    torch.save({"arm": "weighted_ce", "fold": 0, "epoch": 12}, classifier_path)

    with pytest.raises(ValueError, match="arm or fold"):
        load_coral_roi_models(detector_path, classifier_path, fold=0, device="cpu")


def test_verified_pair_checks_zip_and_selected_member_hashes(tmp_path: Path) -> None:
    return_zip = tmp_path / "result.zip"
    members = {
        "experiment_complete.json": json.dumps({
            "status": "all_requested_folds_completed", "test_split_used": False,
        }).encode(),
        "fold_00/detector_last.pt": b"fake detector checkpoint",
        "fold_00/coral_classifier_last.pt": b"fake coral checkpoint",
    }
    manifest = [
        {"path": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        for name, payload in members.items() if name.startswith("fold_")
    ]
    members["return_integrity_manifest.csv"] = (
        "path,bytes,sha256\n" + "".join(f"{row['path']},{row['bytes']},{row['sha256']}\n" for row in manifest)
    ).encode()
    with zipfile.ZipFile(return_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    zip_hash = hashlib.sha256(return_zip.read_bytes()).hexdigest()
    (tmp_path / "verification.json").write_text(json.dumps({"status": "verified", "zip_sha256": zip_hash}))

    detector, classifier, receipt, detector_hash, classifier_hash = _verified_checkpoint_pair(
        return_zip, 0, tmp_path / "temporary",
    )

    assert detector.read_bytes() == members["fold_00/detector_last.pt"]
    assert classifier.read_bytes() == members["fold_00/coral_classifier_last.pt"]
    assert receipt["zip_sha256"] == zip_hash
    assert detector_hash == manifest[0]["sha256"]
    assert classifier_hash == manifest[1]["sha256"]
