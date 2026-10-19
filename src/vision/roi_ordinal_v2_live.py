"""Registered-photo runtime for the isolated v2 tooth-ROI experiment."""

from __future__ import annotations

import base64
from hashlib import sha256
from pathlib import Path
import tempfile

from . import photo_explanation
from .roi_inference_v1 import GRADE_COLORS, _load_srgb_photo
from .roi_ordinal_v2_demo import _verified_checkpoint_pair
from .roi_ordinal_v2_inference import load_coral_roi_models, predict_coral_tooth_rois


MAX_OVERLAY_SIDE = 1200
NOTICE = (
    "Experimental research output. ROI boxes are model detections, not clinical gum "
    "boundaries or a diagnosis. Grade 1/2 performance is not validated."
)


def _render_preview(photo_path: Path, prediction: dict) -> str:
    """Draw detected boxes on a bounded preview and return PNG data for React."""

    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont

    image = _load_srgb_photo(photo_path)
    original_width, original_height = image.size
    scale = min(1.0, MAX_OVERLAY_SIDE / max(original_width, original_height))
    if scale < 1.0:
        image = image.resize(
            (max(1, round(original_width * scale)), max(1, round(original_height * scale))),
            Image.Resampling.LANCZOS,
        )

    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=12)
    for index, row in enumerate(prediction.get("detections", []), start=1):
        grade = int(row["grade"])
        x1, y1, x2, y2 = row["xyxy"]
        bounds = (
            round(x1 * scale), round(y1 * scale),
            round(x2 * scale), round(y2 * scale),
        )
        color = GRADE_COLORS[grade]
        draw.rectangle(bounds, outline=color, width=2)
        # Indices match the per-crop table without overlapping long score strings.
        draw.rectangle((bounds[0],bounds[1],bounds[0]+18,bounds[1]+16),fill=color)
        draw.text((bounds[0]+2,bounds[1]),f"{index:02d}",fill=(0,0,0),font=font)

    footer = "RESEARCH ONLY | provisional ROI boxes; not a clinical boundary"
    draw.rectangle((0, image.height - 30, image.width, image.height), fill=(32, 32, 32))
    draw.text((8, image.height - 23), footer, fill=(255, 255, 255), font=ImageFont.load_default())

    output = BytesIO()
    image.save(output, format="PNG", icc_profile=None)
    return base64.b64encode(output.getvalue()).decode("ascii")


class ROIV2PhotoRuntime:
    """Run one verified fold only for inputs in the PP1 source registry."""

    def __init__(
        self,
        *,
        detector,
        classifier,
        device: str,
        fold: int,
        receipt: dict,
        detector_sha256: str,
        classifier_sha256: str,
        photo_runtime,
        checkpoint_temp,
    ):
        self.detector = detector
        self.classifier = classifier
        self.device = device
        self.fold = fold
        self.receipt = receipt
        self.detector_sha256 = detector_sha256
        self.classifier_sha256 = classifier_sha256
        self.allowed_inputs = dict(getattr(photo_runtime, "allowed_inputs", {}))
        runtime_status = photo_runtime.status() if callable(getattr(photo_runtime, "status", None)) else {}
        self.local_upload_demo = runtime_status.get("upload_mode") == "local_user_upload_demo"
        self.profile_sha256 = getattr(photo_runtime, "profile_sha256", None)
        self.synthetic_only = photo_runtime.synthetic_only
        self._checkpoint_temp = checkpoint_temp

    def status(self) -> dict:
        """Report whether both the model and its registered input scope are ready."""

        return {
            "ready": self.local_upload_demo or bool(self.allowed_inputs),
            "upload_mode": "local_user_upload_demo" if self.local_upload_demo else "registered",
            "model_family": "roi_tooth_v2_coral",
            "model_label": "YOLO tooth ROI + ResNet18 CORAL crop classifier",
            "fold": self.fold,
            "device": self.device,
            "synthetic_only": self.synthetic_only,
            "registered_count": len(self.allowed_inputs),
            "message": (
                "Ready for local user-photo inference; uploads are temporary and not saved."
                if self.local_upload_demo else
                "Ready for registered generated-image checks only."
                if self.synthetic_only else
                "Ready for source-registered non-study photos only."
            ) if self.local_upload_demo or self.allowed_inputs else "A registered photo runtime is required.",
            "notice": NOTICE,
        }

    def predict(self, payload: bytes) -> dict:
        """Check the source registry before using the research-photo route."""

        if not isinstance(payload, bytes) or not 0 < len(payload) <= photo_explanation.MAX_BYTES:
            raise ValueError("JPEG must be nonempty and at most 8 MiB")

        # The known byte hash must be registered before any photo decoder runs.
        origin = self.allowed_inputs.get(sha256(payload).hexdigest())
        expected_origin = "generated" if self.synthetic_only else "owner_supplied_nonstudy"
        if origin != expected_origin:
            raise ValueError("Photo is not in the source-confirmed local demo registration")

        # Reuse the PP1 colour, format, orientation and geometry checks for this model too.
        prepared = photo_explanation.prepare_jpeg(payload, self.profile_sha256)

        evidence = getattr(prepared, "display_evidence", {})
        colour_policy = evidence.get(
            "colour_policy", "Registered JPEG passed the existing qualified colour checks."
        )
        return self._predict_temporary(payload, ".jpg", colour_policy)

    def predict_upload(self, payload: bytes, content_type: str) -> dict:
        """Process one local UI upload after explicit format and colour checks."""
        if not self.local_upload_demo:
            raise ValueError("This runtime does not accept unregistered user uploads")
        from .local_photo_upload_demo import prepare_local_upload

        prepared = prepare_local_upload(payload, content_type)
        try:
            # Match v1: reuse validated pixels, including ICC, EXIF and alpha handling.
            # PNG is lossless; the trained detector/crop transforms below stay unchanged.
            return self._predict_temporary(
                None, ".png", prepared.input_colour_policy,
                input_format=prepared.input_format, normalized_image=prepared.srgb_image,
            )
        finally:
            prepared.close()

    def _predict_temporary(self, payload, suffix, colour_policy, *, input_format="JPEG", normalized_image=None):
        """Use a bounded temporary path required by the existing YOLO helper."""
        with tempfile.TemporaryDirectory(prefix="component2_roi_photo_") as temporary:
            photo_path = Path(temporary) / ("photo" + suffix)
            if normalized_image is None:
                photo_path.write_bytes(payload)  # Preserve the separate registered-photo mode.
            else:
                normalized_image.save(photo_path, format="PNG", icc_profile=None)
            result = predict_coral_tooth_rois(
                self.detector,
                self.classifier,
                photo_path,
                device=self.device,
            )
            overlay = _render_preview(photo_path, result)

        result.update({
            "model_label": "YOLO tooth ROI + ResNet18 CORAL crop classifier",
            "fold": self.fold,
            "device": self.device,
            "synthetic_only": self.synthetic_only,
            "overlay_png_base64": overlay,
            "notice": NOTICE,
            "final_model": False,
            "all_development_refit": False,
            "return_zip_sha256": self.receipt["zip_sha256"],
            "detector_checkpoint_sha256": self.detector_sha256,
            "classifier_checkpoint_sha256": self.classifier_sha256,
            "input_format": input_format,
            "input_colour_policy": colour_policy,
            "photo_saved": False,
        })
        return result


def build_runtime(return_zip: str | Path, photo_runtime, *, device: str | None = None):
    """Verify the returned fold weights and bind them to the existing photo registry."""

    if photo_runtime is None or not photo_runtime.status().get("ready"):
        raise ValueError("The source-registered local photo runtime must be enabled first")

    archive_path = Path(return_zip)
    if archive_path.is_symlink() or not archive_path.is_file():
        raise ValueError("A regular local v2 return ZIP is required")

    # Keep the extracted, hash-verified fold files alive for the model runtime lifetime.
    checkpoint_temp = tempfile.TemporaryDirectory(prefix="component2_roi_v2_checkpoints_")
    try:
        detector_path, classifier_path, receipt, detector_sha, classifier_sha = (
            _verified_checkpoint_pair(archive_path, 0, Path(checkpoint_temp.name))
        )
        detector, classifier, selected_device = load_coral_roi_models(
            detector_path,
            classifier_path,
            fold=0,
            device=device,
        )
        return ROIV2PhotoRuntime(
            detector=detector,
            classifier=classifier,
            device=selected_device,
            fold=0,
            receipt=receipt,
            detector_sha256=detector_sha,
            classifier_sha256=classifier_sha,
            photo_runtime=photo_runtime,
            checkpoint_temp=checkpoint_temp,
        )
    except Exception:
        checkpoint_temp.cleanup()
        raise
