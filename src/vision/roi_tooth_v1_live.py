"""Temporary local-upload adapter for the verified YOLO ROI v1 checkpoints."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from .roi_inference_v1 import _load_srgb_photo, load_roi_checkpoint_models, predict_tooth_rois


MAX_OVERLAY_SIDE = 1200
NOTICE = (
    "Experimental v1 output. Boxes are model detections, not clinical gum boundaries. "
    "The image grade is the maximum predicted crop grade; this fold is not a final refit."
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified_checkpoint_pair(return_zip: Path, temporary_root: Path):
    """Verify the saved Colab receipt and selected fold hashes before loading weights."""
    receipt_path = return_zip.parent / "colab_verification_summary_v1.json"
    if return_zip.is_symlink() or not return_zip.is_file() or not receipt_path.is_file():
        raise FileNotFoundError("Keep the v1 return ZIP beside its verification summary.")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    archive_record = receipt.get("return_zip", {})
    if (receipt.get("status") != "verified_complete"
            or archive_record.get("sha256") != _sha256_file(return_zip)):
        raise ValueError("The v1 return ZIP does not match its verification summary.")

    expected = {
        "fold_00/detector_last.pt",
        "fold_00/crop_classifier_last.pt",
    }
    temporary_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(return_zip) as archive:
        manifest_members = [
            name for name in archive.namelist()
            if name.endswith("return_integrity_manifest.csv")
        ]
        if len(manifest_members) != 1:
            raise ValueError("The v1 ZIP must contain one return integrity manifest.")
        prefix = manifest_members[0][:-len("return_integrity_manifest.csv")]
        completion = json.loads(archive.read(prefix + "experiment_complete.json"))
        if (completion.get("status") != "all_requested_folds_completed"
                or completion.get("test_split_used") is not False):
            raise ValueError("The v1 archive is incomplete or records unexpected Test use.")
        lines = archive.read(manifest_members[0]).decode("utf-8").splitlines()
        manifest = {row["path"]: row for row in csv.DictReader(lines)}
        if not expected.issubset(manifest):
            raise ValueError("The v1 return manifest is missing fold 00 checkpoints.")

        extracted = {}
        for name in sorted(expected):
            payload = archive.read(prefix + name)
            record = manifest[name]
            digest = hashlib.sha256(payload).hexdigest()
            if len(payload) != int(record["bytes"]) or digest != record["sha256"]:
                raise ValueError(f"The v1 checkpoint failed its manifest check: {name}")
            path = temporary_root / Path(name).name
            path.write_bytes(payload)
            extracted[name] = path
    return (
        extracted["fold_00/detector_last.pt"],
        extracted["fold_00/crop_classifier_last.pt"],
        receipt,
        manifest["fold_00/detector_last.pt"]["sha256"],
        manifest["fold_00/crop_classifier_last.pt"]["sha256"],
    )


def _render_overlay(photo_path: Path, prediction: dict) -> str:
    """Render predicted boxes and crop grades as a bounded research-only preview."""
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont

    from .roi_inference_v1 import GRADE_COLORS

    image = _load_srgb_photo(photo_path)
    scale = min(1.0, MAX_OVERLAY_SIDE / max(image.size))
    if scale < 1.0:
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            resample=Image.Resampling.LANCZOS,
        )
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=12)
    for index, row in enumerate(prediction.get("detections", []), start=1):
        x1, y1, x2, y2 = row["xyxy"]
        bounds = tuple(round(value * scale) for value in (x1, y1, x2, y2))
        color = GRADE_COLORS[int(row["grade"])]
        draw.rectangle(bounds, outline=color, width=2)
        # Short indices match the UI table; scores stay separate from box labels.
        label=f"{index:02d}"
        draw.rectangle((bounds[0],bounds[1],bounds[0]+18,bounds[1]+16),fill=color)
        draw.text((bounds[0]+2,bounds[1]),label,fill=(0,0,0),font=font)
    footer_height = 30
    draw.rectangle((0, image.height - footer_height, image.width, image.height), fill=(32, 32, 32))
    draw.text((8, image.height - 22), "RESEARCH ONLY | predicted ROI; not a clinical boundary",
              fill=(255, 255, 255), font=ImageFont.load_default())
    output = BytesIO()
    image.save(output, format="PNG", icc_profile=None)
    return base64.b64encode(output.getvalue()).decode("ascii")


class ROIV1PhotoRuntime:
    """Use one fold of the saved 60.74%-OOF workflow for a temporary photo demo."""

    upload_mode = "local_user_upload_demo"
    synthetic_only = False

    def __init__(self, detector, classifier, device, receipt, detector_sha, classifier_sha, temp):
        self.detector = detector
        self.classifier = classifier
        self.device = device
        self.receipt = receipt
        self.detector_sha = detector_sha
        self.classifier_sha = classifier_sha
        self._checkpoint_temp = temp

    def status(self):
        return {
            "ready": True,
            "upload_mode": self.upload_mode,
            "model_family": "roi_tooth_v1",
            "model_label": "YOLO26n tooth ROI + ResNet18 weighted-CE crop classifier",
            "image_level_oof_accuracy": 0.6073529411764705,
            "image_level_oof_macro_f1": 0.3384393403845929,
            "fold": 0,
            "device": self.device,
            "message": "Ready for local user-photo inference; uploads are temporary and not saved.",
            "photo_saved": False,
            "final_model": False,
        }

    def predict_upload(self, payload: bytes, content_type: str):
        """Validate colour/file handling, infer from a temporary file, then remove it."""
        from .local_photo_upload_demo import prepare_local_upload

        prepared = prepare_local_upload(payload, content_type)
        try:
            with tempfile.TemporaryDirectory(prefix="component2_roi_v1_photo_") as temporary:
                # Save the already-normalized sRGB pixels so model preprocessing receives
                # the same orientation and colour space that the upload check established.
                photo_path = Path(temporary) / "photo.png"
                prepared.srgb_image.save(photo_path, format="PNG", icc_profile=None)
                result = predict_tooth_rois(
                    self.detector, photo_path, crop_classifier=self.classifier, device=self.device,
                )
                overlay = _render_overlay(photo_path, result)
            detections = [
                {**row, "detector_confidence": row["confidence"]}
                for row in result["detections"]
            ]
            return {
                **result,
                "model_label": "YOLO26n tooth ROI + ResNet18 weighted-CE crop classifier",
                "fold": 0,
                "device": self.device,
                "detections": detections,
                "overlay_png_base64": overlay,
                "notice": NOTICE,
                "final_model": False,
                "all_development_refit": False,
                "return_zip_sha256": self.receipt["return_zip"]["sha256"],
                "detector_checkpoint_sha256": self.detector_sha,
                "classifier_checkpoint_sha256": self.classifier_sha,
                "input_format": prepared.input_format,
                "input_colour_policy": prepared.input_colour_policy,
                "photo_saved": False,
            }
        finally:
            prepared.close()


def build_runtime(return_zip: str | Path, *, device: str | None = None):
    """Load fold 00 only after receipt, completion and checkpoint hashes pass."""
    checkpoint_temp = tempfile.TemporaryDirectory(prefix="component2_roi_v1_checkpoints_")
    try:
        detector_path, classifier_path, receipt, detector_sha, classifier_sha = _verified_checkpoint_pair(
            Path(return_zip), Path(checkpoint_temp.name)
        )
        detector, classifier, selected_device = load_roi_checkpoint_models(
            detector_path, classifier_path, device=device,
        )
        return ROIV1PhotoRuntime(
            detector, classifier, selected_device, receipt,
            detector_sha, classifier_sha, checkpoint_temp,
        )
    except Exception:
        checkpoint_temp.cleanup()
        raise
