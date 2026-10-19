"""Opt-in photo explanation adapter; no training, dataset scanner or downloads.

The default demo does not activate this runtime. Only hash-registered inputs
are accepted. Original study/Test/held images are not registered by this code.
"""

from dataclasses import dataclass
from hashlib import sha256
import base64
import io
from pathlib import Path
from types import MappingProxyType

import numpy as np
from PIL import Image

from . import b1_jpeg_source_v1 as source
from . import colour_b1_prototype as b1
from . import exploratory_pilot_b1_v1 as pilot


VERSION = "pp1-photo-explanation-v1"
V3_CHECKPOINT_SHA = "36dd33662e277d3770995bf406f714b71231e77846a4a6a01ef418864259b2ee"
QUALIFIED_PROFILE_SHA = "2b8daf8cabe783b17f801e6687f57016b53c775a826269e21c51313083c9fefc"
MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 40_000_000
PREVIEW_SIDE = 1200
GRADES = (1, 2, 3, 4)
NOTICE = "Provisional labels; non-clinical; non-final; participant independence unverified."


def _digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _png(values):
    """Encode new display-only RGB pixels without copying source metadata."""
    pixels = np.asarray(values)
    if pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[-1] != 3:
        raise ValueError("Expected RGB8 explanation view")
    out = io.BytesIO()
    Image.fromarray(pixels).save(out, format="PNG")
    return base64.b64encode(out.getvalue()).decode("ascii")


def prepare_jpeg(payload, expected_profile_sha):
    """Reuse qualified B1 model sampling; previews are separate display data."""
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_BYTES:
        raise ValueError("JPEG must be nonempty and at most 8 MiB")
    if not _digest(expected_profile_sha):
        raise ValueError("A trusted qualified ICC profile binding is required")
    with Image.open(io.BytesIO(payload)) as image:
        if image.format != "JPEG" or image.mode != "RGB":
            raise ValueError("Only explicit RGB JPEG is supported by this adapter")
        width, height = image.size
        if not (0 < width <= 16384 and 0 < height <= 16384 and width * height <= MAX_PIXELS):
            raise ValueError("Image geometry exceeds the supported bound")
        if image.getexif().get(274, 1) != 1:
            raise ValueError("Non-identity EXIF orientation is not qualified; no silent rotation")
        profile = image.info.get("icc_profile")
        if not isinstance(profile, bytes) or sha256(profile).hexdigest() != expected_profile_sha:
            raise ValueError("Missing or unqualified ICC profile; no assumed sRGB fallback")
        converter = source.Converter(profile)
        if not np.all(converter.parsed.gammas == converter.parsed.gammas[0]):
            raise ValueError("This adapter requires the qualified equal-channel profile family")
        image.load()
        model_view = source.model_view(image, converter)

        # Match the existing CAM preview convention: sample canonical pixels,
        # then clip ONLY the display view. Never resize RGB8 before conversion.
        scale = min(1.0, PREVIEW_SIDE / max(width, height))
        w, h = max(1, round(width * scale)), max(1, round(height * scale))
        xs = np.minimum(((np.arange(w) + .5) * width / w).astype(int), width - 1)
        ys = np.minimum(((np.arange(h) + .5) * height / h).astype(int), height - 1)
        preview = np.empty((h, w, 3), dtype=np.uint8)
        for row, y in enumerate(ys):
            with image.crop((0, int(y), width, int(y) + 1)) as strip:
                values = converter.convert(np.asarray(strip)[:, xs, :], precision=True)[0]
            preview[row] = np.rint(np.clip(values[0], 0, 1) * 255).astype(np.uint8)
    left, top, w_model, h_model = source.stream.full_geometry(width, height)
    return b1.B1Input(preview, b1.normalize(model_view), (left, top, w_model, h_model), {
        "display_only": True, "source_dimensions": [width, height],
        "preview_dimensions": [w, h], "source_sha256": sha256(payload).hexdigest(),
        "colour_policy": "B1 extended float model input; clipped sRGB display preview only",
        "clinical_colour_validated": False,
    })


def _checked_result(result, prepared, checkpoint_sha, synthetic):
    """Four-output semantics stay explicit and every displayed view is aligned."""
    probabilities = np.asarray(result.get("probabilities"), dtype=float)
    if (probabilities.shape != (4,) or not np.isfinite(probabilities).all()
            or np.any(probabilities < 0) or np.any(probabilities > 1)
            or not np.isclose(probabilities.sum(), 1, atol=1e-6, rtol=0)):
        raise ValueError("Expected four finite normalized probabilities")
    grade = GRADES[int(probabilities.argmax())]
    if type(result.get("predicted_mgi_grade")) is not int or result["predicted_mgi_grade"] != grade:
        raise ValueError("Prediction/grade mapping mismatch")
    shape = prepared.original_rgb.shape
    views = {}
    for name in ("original", "heatmap", "overlay"):
        values = np.asarray(result.get(name))
        if values.shape != shape or values.dtype != np.uint8:
            raise ValueError("Explanation views must preserve preview geometry and RGB")
        views[name] = _png(values)
    if not np.array_equal(result["original"], prepared.original_rgb):
        raise ValueError("Explanation changed the original display view")
    if result.get("explanation_status") not in (
        "ok", "no_positive_signal", "no_spatial_contrast", "padding_only_signal"
    ):
        raise ValueError("Unknown explanation status")
    return {"version": VERSION, "notice": NOTICE, "mgi_grades": list(GRADES),
            "predicted_grade": grade, "explained_grade": grade,
            "probabilities": probabilities.tolist(), "views_png_base64": views,
            "display_evidence": prepared.display_evidence,
            "explanation_status": result["explanation_status"],
            "checkpoint_sha256": checkpoint_sha, "synthetic_only": synthetic,
            "meaning": "Model attention, not clinical inflammation boundaries",
            "healthy_mgi0_supported": False, "final_model": False}


@dataclass(frozen=True)
class PhotoRuntime:
    model: object
    cam_layer: object
    checkpoint_sha256: str
    allowed_inputs: dict
    profile_sha256: str = QUALIFIED_PROFILE_SHA
    synthetic_only: bool = False

    def __post_init__(self):
        if (type(self.synthetic_only) is not bool or not _digest(self.checkpoint_sha256)
                or not _digest(self.profile_sha256) or not isinstance(self.allowed_inputs, dict)):
            raise ValueError("Invalid runtime hash/scope bindings")
        origin = "generated" if self.synthetic_only else "owner_supplied_nonstudy"
        if any(not _digest(key) or value != origin for key, value in self.allowed_inputs.items()):
            raise ValueError("Invalid input registry provenance")
        object.__setattr__(self, "allowed_inputs", MappingProxyType(dict(self.allowed_inputs)))

    def status(self):
        return {"ready": bool(self.allowed_inputs), "version": VERSION,
                "notice": NOTICE, "synthetic_only": self.synthetic_only,
                "registered_count": len(self.allowed_inputs),
                "message": ("Generated-image verification only; not a dental performance result"
                            if self.synthetic_only else "Local registered non-study photo demo"),
                "accepted_format": "registered RGB JPEG with qualified ICC and identity orientation",
                "maximum_bytes": MAX_BYTES, "healthy_mgi0_supported": False}

    def explain(self, payload):
        # The runtime owner registers byte hashes before upload. Browser data
        # cannot self-approve an input or supply its own provenance claims.
        if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_BYTES:
            raise ValueError("Invalid image payload size")
        origin = self.allowed_inputs.get(sha256(payload).hexdigest())
        expected_origin = "generated" if self.synthetic_only else "owner_supplied_nonstudy"
        if origin != expected_origin:
            raise ValueError("Photo is not in the separately authorized input registry")
        if not self.synthetic_only and self.checkpoint_sha256 != V3_CHECKPOINT_SHA:
            raise ValueError("Unverified exploratory checkpoint")
        prepared = prepare_jpeg(payload, self.profile_sha256)
        result = pilot.gradcam(self.model, self.cam_layer, prepared)
        return _checked_result(result, prepared, self.checkpoint_sha256, self.synthetic_only)


def load_v3_runtime(checkpoint, allowed_inputs, *, synthetic_only=False):
    """Explicit caller only: load the pinned model, never ImageNet weights/downloads.

    This is not called by the default demo, packaging or any training gate.
    Input registration requires a separate owner-origin decision; this helper
    does not authenticate clinical consent or discover study/Test photographs.
    """
    if type(synthetic_only) is not bool:
        raise ValueError("Explicit runtime scope required")
    origin = "generated" if synthetic_only else "owner_supplied_nonstudy"
    if (not isinstance(allowed_inputs, dict) or not allowed_inputs
            or any(not _digest(k) or v != origin for k, v in allowed_inputs.items())):
        raise ValueError("Explicit new-photo input registration required; study images forbidden")
    model, cam_layer = load_v3_model(checkpoint)
    return PhotoRuntime(model, cam_layer, V3_CHECKPOINT_SHA,
                        dict(allowed_inputs), synthetic_only=synthetic_only)


def load_v3_model(checkpoint):
    """Load only the pinned PP1 checkpoint; shared by separately gated local runtimes."""
    path = Path(checkpoint)
    if path.is_symlink() or not path.is_file():
        raise ValueError("A regular local pinned checkpoint is required")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != V3_CHECKPOINT_SHA:
        raise ValueError("Checkpoint SHA mismatch before deserialization")
    torch = pilot.models._torch()
    state = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
    if state.get("version") != "pp1-b1-last-bottleneck-v3" or state.get("schema") != list(GRADES):
        raise ValueError("Checkpoint schema/version mismatch")
    context = state.get("context", {})
    if (context.get("qualified_labels_approved") is not False
            or context.get("participant_independence_verified") is not False):
        raise ValueError("Expected explicit provisional checkpoint context")
    network = pilot.make_model(pretrained=False)
    network["model"].load_state_dict(state["model"], strict=True)
    network["model"].eval()
    return network["model"], network["cam_layer"]
