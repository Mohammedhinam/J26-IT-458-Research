"""Small, shared helpers for the isolated tooth-ROI research experiment.

Source TXT labels remain unchanged. This module only interprets their boxes,
clips derived coordinates at image edges, and combines predicted tooth grades.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


RAW_CLASS_TO_MGI = {raw_class: raw_class - 2 for raw_class in range(2, 7)}
MGI_GRADES = (0, 1, 2, 3, 4)
BOX_CLIP_TOLERANCE = 1e-6


@dataclass(frozen=True)
class YoloBox:
    """One normalized YOLO box, retaining the source class ID."""

    class_id: int
    center_x: float
    center_y: float
    width: float
    height: float

    @property
    def mgi_grade(self) -> int | None:
        """Return a provisional tooth grade; arch boxes have no grade."""

        return RAW_CLASS_TO_MGI.get(self.class_id)


def parse_yolo_label_lines(lines: Iterable[str]) -> list[YoloBox]:
    """Read five-field YOLO rows and reject unsafe or unknown annotations."""

    boxes: list[YoloBox] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        values = line.split()
        if len(values) != 5:
            raise ValueError(f"line {line_number}: expected five YOLO fields")
        try:
            class_value = float(values[0])
            numbers = [float(value) for value in values[1:]]
        except ValueError as exc:
            raise ValueError(f"line {line_number}: label contains non-numeric data") from exc
        if not class_value.is_integer():
            raise ValueError(f"line {line_number}: class ID must be an integer")
        class_id = int(class_value)
        if class_id not in range(7):
            raise ValueError(f"line {line_number}: source class ID is outside 0..6")
        if not all(0.0 <= number <= 1.0 for number in numbers):
            raise ValueError(f"line {line_number}: normalized values must be in 0..1")
        center_x, center_y, width, height = numbers
        if width <= 0.0 or height <= 0.0:
            raise ValueError(f"line {line_number}: box width and height must be positive")
        boxes.append(YoloBox(class_id, center_x, center_y, width, height))
    return boxes


def box_to_xyxy(
    box: YoloBox,
    image_width: int,
    image_height: int,
    padding_fraction: float = 0.0,
) -> tuple[int, int, int, int]:
    """Convert a normalized box to clipped pixel coordinates.

    The optional padding expands a tooth box so its crop can include nearby
    gingiva. A tiny source rounding overshoot is clipped to the image edge.
    """

    if image_width <= 0 or image_height <= 0:
        raise ValueError("image dimensions must be positive")
    if padding_fraction < 0:
        raise ValueError("padding_fraction cannot be negative")
    center_x = box.center_x * image_width
    center_y = box.center_y * image_height
    half_width = box.width * image_width * (0.5 + padding_fraction)
    half_height = box.height * image_height * (0.5 + padding_fraction)
    x1 = max(0, min(image_width, round(center_x - half_width)))
    y1 = max(0, min(image_height, round(center_y - half_height)))
    x2 = max(0, min(image_width, round(center_x + half_width)))
    y2 = max(0, min(image_height, round(center_y + half_height)))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("box becomes empty after clipping to the image")
    return x1, y1, x2, y2


def detector_label_for_tooth_box(
    box: YoloBox,
    image_width: int,
    image_height: int,
) -> str | None:
    """Make a one-class tooth-ROI detector row; ignore broad arch boxes.

    The source class-to-MGI mapping is retained separately for crop-classifier
    targets. Detector class 0 means only "tooth ROI" in the derived dataset.
    """

    grade = box.mgi_grade
    if grade is None:
        return None
    x1, y1, x2, y2 = box_to_xyxy(box, image_width, image_height)
    center_x = ((x1 + x2) / 2.0) / image_width
    center_y = ((y1 + y2) / 2.0) / image_height
    width = (x2 - x1) / image_width
    height = (y2 - y1) / image_height
    return f"0 {center_x:.8f} {center_y:.8f} {width:.8f} {height:.8f}"


def maximum_image_grade(grades: Sequence[int]) -> int | None:
    """Aggregate detected tooth grades using the project's image-maximum rule."""

    if not grades:
        return None
    if any(grade not in MGI_GRADES for grade in grades):
        raise ValueError("predicted tooth grade must be an integer from 0 to 4")
    return max(grades)


def image_grade_metrics(records: Sequence[dict]) -> dict:
    """Score image maxima while counting no-detection cases as failures."""

    # Import sklearn only when evaluation is requested so geometry checks stay light.
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

    supported_grades = [1, 2, 3, 4]
    y_true: list[int] = []
    y_pred: list[int] = []
    no_detection = 0
    for row in records:
        true_grade = int(row["true_image_grade"])
        predicted = row.get("predicted_image_grade")
        if true_grade not in supported_grades:
            raise ValueError("image target must be one of the supported grades 1..4")
        if predicted is None:
            no_detection += 1
            predicted = -1
        predicted = int(predicted)
        if predicted not in (-1, 0, 1, 2, 3, 4):
            raise ValueError("image prediction must be None or an MGI grade 0..4")
        y_true.append(true_grade)
        y_pred.append(predicted)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3, 4, -1])
    per_grade_recall: dict[str, float | None] = {}
    for grade in range(5):
        support = sum(value == grade for value in y_true)
        if support == 0:
            per_grade_recall[str(grade)] = None
        else:
            correct = sum(t == grade and p == grade for t, p in zip(y_true, y_pred))
            per_grade_recall[str(grade)] = correct / support

    detected = len(records) - no_detection
    supported_true_grades = sorted(set(y_true))
    recall_by_supported_grade = [
        sum(true == grade and pred == grade for true, pred in zip(y_true, y_pred))
        / sum(true == grade for true in y_true)
        for grade in supported_true_grades
    ]
    return {
        "n_images": len(records),
        "n_with_detection": detected,
        "detection_coverage": detected / len(records) if records else None,
        "n_no_detection": no_detection,
        "accuracy_all_images": accuracy_score(y_true, y_pred) if records else None,
        "macro_f1_supported_grades_1_to_4": f1_score(
            y_true, y_pred, labels=supported_grades, average="macro", zero_division=0
        ) if records else None,
        "balanced_accuracy_supported_grades_1_to_4": (
            sum(recall_by_supported_grade) / len(recall_by_supported_grade)
            if recall_by_supported_grade else None
        ),
        "per_grade_recall": per_grade_recall,
        "confusion_matrix_labels": [0, 1, 2, 3, 4, "no_detection"],
        "confusion_matrix": cm.tolist(),
        "unsupported_image_grade_0": True,
    }
