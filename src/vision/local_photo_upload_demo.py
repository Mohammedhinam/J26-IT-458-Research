"""Opt-in, loopback-only inference for a presenter-selected photo.

Images are processed in memory and are never added to a dataset or saved. This
does not change the separate hash-registered research-photo adapter.
"""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageOps

from . import b1_jpeg_source_v1 as source
from . import colour_b1_prototype as b1
from . import exploratory_pilot_b1_v1 as pilot
from . import photo_explanation as photo


VERSION = "local-photo-upload-demo-v1"
SUPPORTED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
MAX_BYTES = photo.MAX_BYTES
MAX_PIXELS = photo.MAX_PIXELS


class _SrgbDemoConverter:
    """Represent sRGB-encoded samples in B1's sRGB-referenced float space."""

    def convert(self, pixels, *, precision=False):
        # B1's reference coordinate system is sRGB, so normalized sRGB codes
        # are the canonical values after any embedded profile is converted.
        values = np.ascontiguousarray(pixels.astype(np.float64) / 255, dtype="<f4")
        return values, None, {}


@dataclass
class PreparedLocalUpload:
    """One decoded upload plus its temporary normalized image and model view."""

    srgb_image: Image.Image
    model_input: b1.B1Input
    input_format: str
    input_colour_policy: str
    orientation_applied: bool

    def close(self):
        self.srgb_image.close()


def prepare_local_upload(payload, content_type):
    """Normalize JPEG/PNG/WebP to sRGB, then apply the trained B1 resize."""
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_BYTES:
        raise ValueError("Choose a nonempty image no larger than 8 MiB")
    if content_type not in set(SUPPORTED_FORMATS.values()):
        raise ValueError("Use a JPEG, PNG or WebP photo")

    try:
        opened = Image.open(BytesIO(payload))
    except (OSError, ValueError):
        raise ValueError("The selected file is not a readable photo") from None

    with opened:
        if SUPPORTED_FORMATS.get(opened.format) != content_type:
            raise ValueError("The image contents do not match the selected file type")
        width, height = opened.size
        if not (0 < width <= 16384 and 0 < height <= 16384 and width * height <= MAX_PIXELS):
            raise ValueError("Photo dimensions exceed the supported limit")

        orientation = opened.getexif().get(274, 1)
        profile_bytes = opened.info.get("icc_profile")
        opened.load()
        oriented = ImageOps.exif_transpose(opened)
        try:
            mode = oriented.mode
            alpha = oriented.getchannel("A") if mode == "RGBA" else None
            if mode == "CMYK":
                if not profile_bytes:
                    raise ValueError("CMYK photos need an embedded colour profile")
                color_source = oriented.copy()
            elif mode in ("RGB", "RGBA"):
                color_source = oriented.convert("RGB")
            else:
                raise ValueError("Use an RGB phone photo (JPEG, PNG or WebP)")

            if profile_bytes:
                try:
                    input_profile = ImageCms.ImageCmsProfile(BytesIO(profile_bytes))
                    output_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
                    srgb_image = ImageCms.profileToProfile(
                        color_source, input_profile, output_profile,
                        renderingIntent=0, outputMode="RGB",
                    )
                    color_policy = "Embedded ICC converted to sRGB before inference."
                except Exception:
                    raise ValueError("This photo's embedded colour profile cannot be converted to sRGB") from None
            else:
                if mode not in ("RGB", "RGBA"):
                    raise ValueError("A colour profile is required for this image mode")
                srgb_image = color_source.copy()
                color_policy = "No ICC profile was present; RGB values were assumed to be sRGB for this demo."

            if alpha is not None:
                background = Image.new("RGB", srgb_image.size, (255, 255, 255))
                background.paste(srgb_image, mask=alpha)
                srgb_image.close()
                srgb_image = background

            srgb_image.load()
            if srgb_image.width * srgb_image.height > MAX_PIXELS:
                srgb_image.close()
                raise ValueError("Oriented photo dimensions exceed the supported limit")

            # The network receives the same 224×224 B1 representation used by
            # training; the smaller preview is only for showing the upload.
            converter = _SrgbDemoConverter()
            model_view = source.model_view(srgb_image, converter)
            display = srgb_image.copy()
            display.thumbnail((photo.PREVIEW_SIDE, photo.PREVIEW_SIDE), Image.Resampling.LANCZOS)
            preview = np.asarray(display, dtype=np.uint8).copy()
            display.close()
            left, top, model_width, model_height = source.stream.full_geometry(
                srgb_image.width, srgb_image.height
            )
            evidence = {
                "display_only": True,
                "source_dimensions": [width, height],
                "oriented_dimensions": [srgb_image.width, srgb_image.height],
                "preview_dimensions": [preview.shape[1], preview.shape[0]],
                "input_format": opened.format,
                "icc_profile_present": bool(profile_bytes),
                "orientation_applied": orientation not in (None, 1),
                "colour_policy": color_policy,
                "clinical_colour_validated": False,
                "photo_saved": False,
            }
            model_input = b1.B1Input(
                preview, b1.normalize(model_view),
                (left, top, model_width, model_height), evidence,
            )
            return PreparedLocalUpload(
                srgb_image.copy(), model_input, opened.format, color_policy,
                orientation not in (None, 1),
            )
        finally:
            if oriented is not opened:
                oriented.close()


class LocalUploadPhotoRuntime:
    """Run one pinned model on a photo selected in the local PP1 UI."""

    upload_mode = "local_user_upload_demo"
    synthetic_only = False

    def __init__(self, model, cam_layer, checkpoint_sha256):
        self.model = model
        self.cam_layer = cam_layer
        self.checkpoint_sha256 = checkpoint_sha256

    def status(self):
        return {
            "ready": True,
            "version": VERSION,
            "upload_mode": self.upload_mode,
            "message": "Local user-photo demo is ready; uploaded photos are not saved.",
            "accepted_format": "JPEG, PNG or WebP up to 8 MiB; embedded ICC is converted to sRGB; missing ICC is explicitly assumed sRGB",
            "maximum_bytes": MAX_BYTES,
            "healthy_mgi0_supported": False,
            "local_only": True,
            "photo_saved": False,
        }

    def explain_upload(self, payload, content_type):
        prepared = prepare_local_upload(payload, content_type)
        try:
            result = pilot.gradcam(self.model, self.cam_layer, prepared.model_input)
            response = photo._checked_result(
                result, prepared.model_input, self.checkpoint_sha256, synthetic=False
            )
            response.update({
                "upload_mode": self.upload_mode,
                "input_colour_policy": prepared.input_colour_policy,
                "input_format": prepared.input_format,
                "orientation_applied": prepared.orientation_applied,
                "photo_saved": False,
            })
            return response
        finally:
            prepared.close()


def load_runtime(checkpoint):
    """Load only the already-pinned v3 checkpoint; no registration or download."""
    model, cam_layer = photo.load_v3_model(Path(checkpoint))
    return LocalUploadPhotoRuntime(model, cam_layer, photo.V3_CHECKPOINT_SHA)
