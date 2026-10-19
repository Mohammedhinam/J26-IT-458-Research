"""Run the isolated ROI experiment on one local photo after returning checkpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.vision.roi_inference_v1 import (
    load_roi_checkpoint_models,
    predict_tooth_rois,
    render_roi_overlay,
)


def run_demo(photo: Path, detector_checkpoint: Path, classifier_checkpoint: Path,
             output_dir: Path, device: str | None = None) -> dict:
    """Predict locally and save a JSON result plus a separate ROI overlay."""

    if not photo.is_file():
        raise FileNotFoundError(f"Photo does not exist: {photo}")
    if not detector_checkpoint.is_file() or not classifier_checkpoint.is_file():
        raise FileNotFoundError("Both returned experimental checkpoints are required.")
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing demo output: {output_dir}")

    detector, classifier, selected_device = load_roi_checkpoint_models(
        detector_checkpoint, classifier_checkpoint, device
    )
    prediction = predict_tooth_rois(
        detector, photo, crop_classifier=classifier, device=selected_device
    )
    prediction.update({
        "detector_checkpoint": str(detector_checkpoint.resolve()),
        "crop_classifier_checkpoint": str(classifier_checkpoint.resolve()),
        "device": selected_device,
        "input_photo": str(photo.resolve()),
    })
    output_dir.mkdir(parents=True)
    result_path = output_dir / "prediction.json"
    overlay_path = output_dir / "roi_overlay.png"
    result_path.write_text(json.dumps(prediction, indent=2) + "\n", encoding="utf-8")
    render_roi_overlay(photo, prediction, overlay_path)
    return prediction


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photo", type=Path, required=True)
    parser.add_argument("--detector", type=Path, required=True)
    parser.add_argument("--classifier", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default=None, help="Defaults to MPS on Apple Silicon, otherwise CUDA or CPU.")
    args = parser.parse_args()
    prediction = run_demo(args.photo, args.detector, args.classifier, args.output, args.device)
    print(json.dumps(prediction, indent=2))


if __name__ == "__main__":
    main()
