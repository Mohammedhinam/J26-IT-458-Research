"""Synthetic geometry and mapping checks for the isolated ROI experiment."""

import pytest
import torch
from PIL import Image
from pathlib import Path
from types import SimpleNamespace

from src.vision.roi_workflow_v1 import (
    YoloBox,
    box_to_xyxy,
    detector_label_for_tooth_box,
    image_grade_metrics,
    maximum_image_grade,
    parse_yolo_label_lines,
)
from src.vision.roi_inference_v1 import predict_tooth_rois


@pytest.mark.parametrize("source_class,grade", [(2, 0), (3, 1), (4, 2), (5, 3), (6, 4)])
def test_source_tooth_classes_map_to_provisional_mgi(source_class, grade):
    box = parse_yolo_label_lines([f"{source_class} 0.5 0.5 0.2 0.3"])[0]
    assert box.mgi_grade == grade


@pytest.mark.parametrize("source_class", [0, 1])
def test_arch_boxes_do_not_receive_a_tooth_grade(source_class):
    box = parse_yolo_label_lines([f"{source_class} 0.5 0.5 0.9 0.4"])[0]
    assert box.mgi_grade is None
    assert detector_label_for_tooth_box(box, 1600, 1068) is None


def test_label_parser_rejects_malformed_or_out_of_range_rows():
    with pytest.raises(ValueError, match="five YOLO fields"):
        parse_yolo_label_lines(["2 0.5 0.5 0.2"])
    with pytest.raises(ValueError, match="outside 0..6"):
        parse_yolo_label_lines(["7 0.5 0.5 0.2 0.2"])
    with pytest.raises(ValueError, match="positive"):
        parse_yolo_label_lines(["2 0.5 0.5 0 0.2"])


def test_crop_box_is_padded_then_clipped_to_image():
    box = YoloBox(class_id=4, center_x=0.02, center_y=0.5, width=0.2, height=0.3)
    assert box_to_xyxy(box, 100, 80, padding_fraction=0.15) == (0, 24, 15, 56)


def test_derived_detector_label_uses_one_tooth_roi_class_and_normalized_coordinates():
    box = YoloBox(class_id=6, center_x=0.5, center_y=0.5, width=0.25, height=0.5)
    label = detector_label_for_tooth_box(box, 1600, 1068)
    values = label.split()
    assert values[0] == "0"
    assert len(values) == 5
    assert all(0 <= float(value) <= 1 for value in values[1:])


def test_image_label_is_maximum_detected_tooth_grade():
    assert maximum_image_grade([1, 2, 0, 3]) == 3
    assert maximum_image_grade([]) is None
    with pytest.raises(ValueError, match="integer from 0 to 4"):
        maximum_image_grade([5])


def test_image_metrics_count_no_detection_as_wrong_and_report_coverage():
    metrics = image_grade_metrics([
        {"true_image_grade": 1, "predicted_image_grade": 1},
        {"true_image_grade": 2, "predicted_image_grade": None},
        {"true_image_grade": 3, "predicted_image_grade": 4},
    ])
    assert metrics["n_images"] == 3
    assert metrics["n_with_detection"] == 2
    assert metrics["n_no_detection"] == 1
    assert metrics["detection_coverage"] == pytest.approx(2 / 3)
    assert metrics["per_grade_recall"]["1"] == 1.0
    assert metrics["per_grade_recall"]["2"] == 0.0
    assert len(metrics["confusion_matrix"]) == 6


class FakeDetector:
    def __init__(self, with_box=True):
        self.with_box = with_box

    def predict(self, **kwargs):
        if not self.with_box:
            boxes = None
        else:
            item = SimpleNamespace(
                cls=torch.tensor([0.0]),
                conf=torch.tensor([0.91]),
                xyxy=torch.tensor([[10.0, 10.0, 50.0, 50.0]]),
            )
            boxes = [item]
        return [SimpleNamespace(boxes=boxes)]


class FakeCropClassifier(torch.nn.Module):
    def forward(self, batch):
        logits = torch.zeros(len(batch), 5)
        logits[:, 2] = 5.0
        return logits


def test_demo_adapter_uses_crop_classifier_and_reports_roi_explanation(tmp_path):
    image_path = tmp_path / "photo.jpg"
    Image.new("RGB", (80, 80), (120, 80, 100)).save(image_path)
    prediction = predict_tooth_rois(
        FakeDetector(), image_path, crop_classifier=FakeCropClassifier(), device="cpu"
    )
    assert prediction["image_mgi_grade"] == 2
    assert prediction["detections"][0]["detector_grade"] == 0
    assert prediction["used_crop_classifier"] is True
    assert "ROI boxes" in prediction["explanation_type"]


def test_demo_adapter_returns_abstention_when_no_roi_is_detected(tmp_path):
    image_path = tmp_path / "photo.jpg"
    Image.new("RGB", (80, 80), (120, 80, 100)).save(image_path)
    prediction = predict_tooth_rois(
        FakeDetector(with_box=False), image_path,
        crop_classifier=FakeCropClassifier(), device="cpu",
    )
    assert prediction["image_mgi_grade"] is None
    assert prediction["no_detection"] is True
