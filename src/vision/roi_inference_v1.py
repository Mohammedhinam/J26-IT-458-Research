"""Inference adapter for the isolated YOLO tooth-ROI model family.

This module is separate from the current PP1 photo endpoint. It can be used
only after the new Colab checkpoint has been returned and verified.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.vision.roi_workflow_v1 import maximum_image_grade


GRADE_COLORS = {
    0: (0, 160, 80),
    1: (40, 120, 240),
    2: (255, 190, 0),
    3: (255, 120, 0),
    4: (180, 60, 220),
}


def _choose_torch_device(device: str | None = None) -> str:
    import torch

    if device:
        return device
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def load_roi_checkpoint_models(
    detector_checkpoint: str | Path,
    classifier_checkpoint: str | Path,
    device: str | None = None,
) -> tuple[Any, Any, str]:
    """Load the new detector and crop classifier without touching the live demo."""

    import torch
    from torch import nn
    from torchvision import models
    from ultralytics import YOLO

    selected_device = _choose_torch_device(device)
    detector = YOLO(str(detector_checkpoint))
    state = torch.load(classifier_checkpoint, map_location="cpu", weights_only=False)
    classifier = models.resnet18(weights=None)
    classifier.fc = nn.Linear(classifier.fc.in_features, 5)
    classifier.load_state_dict(state["model_state"])
    classifier = classifier.to(selected_device).eval()
    return detector, classifier, selected_device


def _load_srgb_photo(image_path: str | Path):
    """Apply EXIF orientation and honor an embedded color profile for demo input."""

    from io import BytesIO

    from PIL import Image, ImageCms, ImageOps

    with Image.open(image_path) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        profile_bytes = source.info.get("icc_profile")
        if profile_bytes:
            input_profile = ImageCms.ImageCmsProfile(BytesIO(profile_bytes))
            srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
            source = ImageCms.profileToProfile(
                source, input_profile, srgb_profile,
                renderingIntent=0, outputMode="RGB",
            )
        return source.copy()


def predict_tooth_rois(
    model: Any,
    image_path: str | Path,
    confidence: float = 0.25,
    crop_classifier: Any | None = None,
    device: str | None = None,
) -> dict:
    """Detect tooth ROIs, classify their crops, and return the maximum grade."""

    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence threshold must be between 0 and 1")
    if crop_classifier is None:
        raise ValueError("The one-class detector locates ROIs; a trained crop classifier is required for MGI grades.")
    selected_device = _choose_torch_device(device)
    import numpy as np

    srgb_photo = _load_srgb_photo(image_path)
    bgr_photo = np.asarray(srgb_photo)[:, :, ::-1].copy()
    results = model.predict(
        source=bgr_photo, conf=confidence, verbose=False,
        **({"device": selected_device} if selected_device else {}),
    )
    if not results:
        raise RuntimeError("the detector returned no result object")
    result = results[0]
    boxes = getattr(result, "boxes", None)
    detections = []
    if boxes is not None:
        detector_rows = []
        crops = []
        transform = None
        if crop_classifier is not None:
            from torchvision import transforms

            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=(0.485, 0.456, 0.406),
                    std=(0.229, 0.224, 0.225),
                ),
            ])
        source = srgb_photo
        for box in boxes:
            detector_grade = int(box.cls[0].item())
            if detector_grade != 0:
                raise ValueError("The ROI detector must return its single tooth_roi class (0).")
            coordinates = [float(value) for value in box.xyxy[0].tolist()]
            detector_rows.append((box, detector_grade, coordinates))
            if crop_classifier is not None:
                x1, y1, x2, y2 = coordinates
                padding_x = max(1.0, (x2 - x1) * 0.15)
                padding_y = max(1.0, (y2 - y1) * 0.15)
                left = max(0, round(x1 - padding_x))
                top = max(0, round(y1 - padding_y))
                right = min(source.width, round(x2 + padding_x))
                bottom = min(source.height, round(y2 + padding_y))
                if right <= left or bottom <= top:
                    raise ValueError("detected ROI is empty after clipping to the photo")
                crops.append(transform(source.crop((left, top, right, bottom))))

        classifier_grades = []
        if crop_classifier is not None and crops:
            import torch

            crop_classifier.eval()
            with torch.no_grad():
                for start in range(0, len(crops), 64):
                    logits = crop_classifier(torch.stack(crops[start:start + 64]).to(selected_device))
                    classifier_grades.extend(logits.argmax(dim=1).cpu().tolist())

        for index, (box, detector_grade, coordinates) in enumerate(detector_rows):
            grade = classifier_grades[index]
            if grade not in range(5):
                raise ValueError("ROI checkpoint returned an unknown MGI class")
            detections.append({
                "grade": grade,
                "detector_grade": detector_grade,
                "confidence": float(box.conf[0].item()),
                "xyxy": coordinates,
            })
    grades = [row["grade"] for row in detections]
    return {
        "model_family": "roi_tooth_v1",
        "image_mgi_grade": maximum_image_grade(grades),
        "detections": detections,
        "explanation_type": "predicted tooth/perigingival ROI boxes with provisional per-tooth grades",
        "notice": "Research output only. Boxes are not clinical gum boundaries or a diagnosis.",
        "no_detection": not bool(detections),
        "used_crop_classifier": crop_classifier is not None,
    }


def render_roi_overlay(image_path: str | Path, prediction: dict, output_path: str | Path) -> Path:
    """Draw predicted ROI boxes and grades on a separate display image."""

    from PIL import ImageDraw, ImageFont

    source_path = Path(image_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image = _load_srgb_photo(source_path)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for row in prediction.get("detections", []):
        grade = int(row["grade"])
        x1, y1, x2, y2 = [round(value) for value in row["xyxy"]]
        color = GRADE_COLORS[grade]
        draw.rectangle((x1, y1, x2, y2), outline=color, width=max(2, image.width // 700))
        label = f"MGI {grade}  {float(row['confidence']):.2f}"
        draw.text((x1, max(0, y1 - 14)), label, fill=color, font=font)
    image.save(output, format="PNG", icc_profile=None)
    return output
