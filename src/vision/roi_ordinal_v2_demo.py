"""Run the isolated v2 CORAL detector demo on one photo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

from src.vision.roi_inference_v1 import GRADE_COLORS, _load_srgb_photo
from src.vision.roi_ordinal_v2_inference import load_coral_roi_models, predict_coral_tooth_rois


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified_checkpoint_pair(
    return_zip: Path, fold: int, temporary_root: Path,
) -> tuple[Path, Path, dict, str, str]:
    """Check the local receipt and ZIP manifest before extracting one fold pair."""

    temporary_root.mkdir(parents=True, exist_ok=True)
    receipt_path = return_zip.parent / "verification.json"
    if not receipt_path.is_file():
        raise FileNotFoundError("The verified return ZIP and its verification.json must stay together.")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "verified" or receipt.get("zip_sha256") != _sha256_file(return_zip):
        raise ValueError("The return ZIP does not match its local verification receipt.")

    detector_name = f"fold_{fold:02d}/detector_last.pt"
    classifier_name = f"fold_{fold:02d}/coral_classifier_last.pt"
    expected_paths = {detector_name, classifier_name}
    with zipfile.ZipFile(return_zip) as archive:
        completion = json.loads(archive.read("experiment_complete.json"))
        if completion.get("status") != "all_requested_folds_completed" or completion.get("test_split_used") is not False:
            raise ValueError("The return ZIP does not record a complete, Test-free run.")
        manifest = {
            row["path"]: row
            for row in csv.DictReader(archive.read("return_integrity_manifest.csv").decode("utf-8").splitlines())
        }
        if not expected_paths.issubset(manifest):
            raise ValueError(f"The return manifest is missing the fold {fold} checkpoint pair.")

        extracted = []
        for name in (detector_name, classifier_name):
            payload = archive.read(name)
            expected = manifest[name]
            actual_hash = hashlib.sha256(payload).hexdigest()
            if len(payload) != int(expected["bytes"]) or actual_hash != expected["sha256"]:
                raise ValueError(f"The selected checkpoint failed its manifest check: {name}")
            path = temporary_root / Path(name).name
            path.write_bytes(payload)
            extracted.append(path)
    return (
        extracted[0], extracted[1], receipt,
        manifest[detector_name]["sha256"], manifest[classifier_name]["sha256"],
    )


def _render_coral_overlay(photo: Path, prediction: dict, output: Path) -> Path:
    """Draw ROI grade labels while naming YOLO confidence as a box score."""

    from PIL import ImageDraw, ImageFont

    image = _load_srgb_photo(photo)
    draw = ImageDraw.Draw(image)
    label_font = ImageFont.load_default(size=16)
    for row in prediction.get("detections", []):
        grade = int(row["grade"])
        x1, y1, x2, y2 = [round(value) for value in row["xyxy"]]
        color = GRADE_COLORS[grade]
        draw.rectangle((x1, y1, x2, y2), outline=color, width=max(2, image.width // 700))
        label = f"MGI {grade} | box {float(row['detector_confidence']):.2f}"
        draw.text((x1, max(0, y1 - 18)), label, fill=color, font=label_font)
    footer_height = 40
    draw.rectangle((0, image.height - footer_height, image.width, image.height), fill=(32, 32, 32))
    draw.text(
        (8, image.height - footer_height + 10),
        "RESEARCH ONLY | Provisional ROI boxes; not a diagnosis or clinical gum boundary",
        fill=(255, 255, 255), font=ImageFont.load_default(size=18),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", icc_profile=None)
    return output


def run_demo(photo: Path, return_zip: Path, fold: int, output_dir: Path,
             device: str | None = None) -> dict:
    """Predict one photo and save research-only JSON and a separate ROI overlay."""

    if not photo.is_file():
        raise FileNotFoundError(f"Photo does not exist: {photo}")
    if not return_zip.is_file():
        raise FileNotFoundError(f"Verified v2 return ZIP does not exist: {return_zip}")
    if fold not in range(5):
        raise ValueError("Choose one returned fold from 0 to 4.")
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing demo output: {output_dir}")

    # Load only the selected fold after checking its integrity against the saved receipt.
    with tempfile.TemporaryDirectory(prefix="roi_v2_fold_") as temporary:
        detector_path, classifier_path, receipt, detector_sha, classifier_sha = _verified_checkpoint_pair(
            return_zip, fold, Path(temporary)
        )
        detector, classifier, selected_device = load_coral_roi_models(
            detector_path, classifier_path, fold=fold, device=device
        )
        prediction = predict_coral_tooth_rois(
            detector, classifier, photo, device=selected_device,
        )

    # Save outputs to a new path so the original photo, v1 model, and PP1 demo stay unchanged.
    output_dir.mkdir(parents=True)
    prediction.update({
        "fold": fold,
        "device": selected_device,
        "input_photo": str(photo.resolve()),
        "input_photo_sha256": _sha256_file(photo),
        "return_zip_sha256": receipt["zip_sha256"],
        "detector_checkpoint_sha256": detector_sha,
        "coral_checkpoint_sha256": classifier_sha,
    })
    prediction["notice"] = (
        "Research-only provisional output. Do not present it as a clinical diagnosis, "
        "a verified gum boundary, or a validated Grade 1/2 classifier."
    )
    result_path = output_dir / "prediction.json"
    overlay_path = output_dir / "roi_overlay.png"
    result_path.write_text(json.dumps(prediction, indent=2) + "\n", encoding="utf-8")
    _render_coral_overlay(photo, prediction, overlay_path)
    return prediction


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photo", type=Path, required=True)
    parser.add_argument("--return-zip", type=Path, required=True)
    parser.add_argument("--fold", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default=None, help="Defaults to MPS on Apple Silicon, then CUDA or CPU.")
    args = parser.parse_args()
    prediction = run_demo(args.photo, args.return_zip, args.fold, args.output, args.device)
    print(json.dumps(prediction, indent=2))


if __name__ == "__main__":
    main()
