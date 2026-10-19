"""Inference helpers for the isolated v2 ordinal tooth-ROI model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.vision.roi_inference_v1 import GRADE_COLORS, _load_srgb_photo
from src.vision.roi_workflow_v1 import YoloBox, box_to_xyxy, maximum_image_grade


def choose_device(device: str | None = None) -> str:
    """Prefer Apple MPS on the Mac, then CUDA, and use CPU as a fallback."""

    import torch

    if device:
        return device
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def load_coral_roi_models(
    detector_checkpoint: str | Path,
    classifier_checkpoint: str | Path,
    *,
    fold: int,
    device: str | None = None,
) -> tuple[Any, Any, str]:
    """Load one returned fold's detector and CORAL classifier safely."""

    import torch
    from ultralytics import YOLO

    from src.vision.roi_ordinal_v2 import _build_model

    detector_path = Path(detector_checkpoint)
    classifier_path = Path(classifier_checkpoint)
    if not detector_path.is_file() or not classifier_path.is_file():
        raise FileNotFoundError("Both fold-specific v2 checkpoints are required.")

    # The returned state uses tensors and plain metadata, so weights_only avoids arbitrary pickle loading.
    state = torch.load(classifier_path, map_location="cpu", weights_only=True)
    if state.get("arm") != "coral" or int(state.get("fold", -1)) != int(fold):
        raise ValueError("The CORAL checkpoint arm or fold does not match the requested fold.")
    if int(state.get("epoch", 0)) != 12:
        raise ValueError("The expected completed v2 checkpoint has exactly 12 epochs.")

    # Build the exact four-threshold CORAL head and load the verified fold state.
    classifier = _build_model("coral", pretrained=False)
    classifier.load_state_dict(state["model_state"])
    selected_device = choose_device(device)
    classifier = classifier.to(selected_device).eval()
    detector = YOLO(str(detector_path))
    return detector, classifier, selected_device


def _crop_transform(photo, box_xyxy: list[float]):
    """Crop with the same 15% padding, size, and normalization used in training."""

    from torchvision import transforms

    x1, y1, x2, y2 = box_xyxy
    box = YoloBox(
        class_id=0,
        center_x=((x1 + x2) / 2.0) / photo.width,
        center_y=((y1 + y2) / 2.0) / photo.height,
        width=(x2 - x1) / photo.width,
        height=(y2 - y1) / photo.height,
    )
    left, top, right, bottom = box_to_xyxy(box, photo.width, photo.height, padding_fraction=0.15)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])
    return transform(photo.crop((left, top, right, bottom)))


def predict_coral_tooth_rois(
    detector: Any,
    classifier: Any,
    image_path: str | Path,
    *,
    device: str,
    confidence: float = 0.25,
    iou: float = 0.70,
    image_size: int = 640,
) -> dict:
    """Detect tooth ROIs, classify each crop, and return the photo's maximum grade."""

    import numpy as np
    import torch

    from src.vision.roi_ordinal_v2 import coral_class_probabilities, coral_grade_predictions

    if not 0.0 < confidence < 1.0:
        raise ValueError("Confidence must be between 0 and 1.")
    if not 0.0 < iou <= 1.0 or image_size < 1:
        raise ValueError("IoU and image size must match valid YOLO inference settings.")

    # Use the same orientation-aware sRGB photo as the existing isolated ROI viewer.
    photo = _load_srgb_photo(image_path)
    bgr_photo = np.asarray(photo)[:, :, ::-1].copy()
    results = detector.predict(
        source=bgr_photo, imgsz=image_size, conf=confidence, iou=iou,
        device=device, save=False, verbose=False,
    )
    if not results:
        raise RuntimeError("The YOLO detector returned no result object.")

    result = results[0]
    boxes = getattr(result, "boxes", None)
    xyxy_rows: list[list[float]] = []
    confidence_rows: list[float] = []
    crop_tensors = []
    if boxes is not None:
        for box in boxes:
            detector_class = int(box.cls[0].item())
            if detector_class != 0:
                raise ValueError("The v2 detector must return only the tooth_roi class 0.")
            xyxy = [float(value) for value in box.xyxy[0].detach().cpu().tolist()]
            xyxy_rows.append(xyxy)
            confidence_rows.append(float(box.conf[0].item()))
            crop_tensors.append(_crop_transform(photo, xyxy))

    detections = []
    if crop_tensors:
        classifier.eval()
        with torch.no_grad():
            for start in range(0, len(crop_tensors), 64):
                crop_batch = torch.stack(crop_tensors[start:start + 64]).to(device)
                logits = classifier(crop_batch)
                grades = coral_grade_predictions(logits).cpu().tolist()
                probabilities = coral_class_probabilities(logits).cpu().tolist()
                for local_index, grade in enumerate(grades):
                    index = start + local_index
                    probability = probabilities[local_index]
                    detections.append({
                        "grade": int(grade),
                        "detector_confidence": confidence_rows[index],
                        "xyxy": xyxy_rows[index],
                        "grade_probabilities": {str(g): float(value) for g, value in enumerate(probability)},
                    })

    grades = [row["grade"] for row in detections]
    return {
        "model_family": "roi_tooth_v2_coral",
        "image_mgi_grade": maximum_image_grade(grades),
        "detections": detections,
        "explanation_type": "predicted tooth-ROI boxes with ordinal per-crop MGI probabilities",
        "label_status": "provisional; not clinically verified",
        "notice": "Research output only. Boxes are not clinical gum boundaries or a diagnosis.",
        "no_detection": not bool(detections),
        "used_crop_classifier": True,
    }
