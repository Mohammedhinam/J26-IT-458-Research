"""GENERATED-ONLY B1 prototype. No image/file ingestion or production exporter.

Pure matrix/TRC interpretation preserves extended values; Pillow RGB8 output
is not used. This module grants no packaging, clinical or training approval.
"""
import ast
from dataclasses import dataclass
from hashlib import sha256
import io
import json
import struct

import numpy as np

from src.vision import model_pipeline as models


VERSION = "b1-generated-v1"
MAX_SIDE = 256
RANGE = (-16.0, 16.0)
SIZE = 224
# D50-adapted sRGB colourants from the generated canonical LCMS sRGB profile.
# Keep full precision; do not re-adapt already-D50 ICC matrix colourants.
SRGB_D50 = np.array([[.4360412516160509, .3851129107981555, .14304583758579362],
                     [.22248454022947742, .7169050786084573, .06061038116206527],
                     [.013920187471375372, .09706723869712398, .7139125738315005]])
D50 = np.array([.9642, 1., .8249])
CONTRACT = {
    "version": VERSION, "scope": "generated_only_not_production",
    "primaries_xy": [[.64, .33], [.30, .60], [.15, .06]], "white": "D65",
    "pcs": "D50_relative", "srgb_d50": SRGB_D50.tolist(),
    "transfer": "odd_srgb_linear_abs_le_.0031308_inverse_.04045",
    "dtype": "<f4", "layout": "HWC_C", "npy_version": [1, 0],
    "max_side": MAX_SIDE, "range": list(RANGE), "model_size": SIZE,
    "resize": "half_pixel_bilinear_edge_replicate_float64_round_even_geometry",
    "padding": models.MEAN.tolist(), "normalization_std": models.STD.tolist(),
    "display": "clip_0_1_round_even_rgb8_display_only",
    "float32_xyz_abs": 2e-6, "float32_lab_de76": .002,
    "reference_rgb_abs": 1e-10, "lcms_lab_de76": .01,
    "transfer_inverse_abs": 5e-9,
}


def digest_json(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("ascii")).hexdigest()


def contract_hash():
    return digest_json(CONTRACT)


def _finite(values):
    if not np.isfinite(values).all():
        raise ValueError("Non-finite colour values")
    return values


def encode_extended(linear):
    """Explicit odd extension: negative light stays negative, never clamped."""
    values = _finite(np.asarray(linear, dtype=np.float64))
    absolute = np.abs(values)
    encoded = 12.92 * absolute
    high = absolute > .0031308
    encoded[high] = 1.055 * absolute[high] ** (1 / 2.4) - .055
    return _finite(np.copysign(encoded, values))


def decode_extended(encoded):
    values = _finite(np.asarray(encoded, dtype=np.float64))
    absolute = np.abs(values)
    linear = absolute / 12.92
    high = absolute > .04045
    linear[high] = ((absolute[high] + .055) / 1.055) ** 2.4
    return _finite(np.copysign(linear, values))


def _fixed(raw):
    if len(raw) % 4:
        raise ValueError("Invalid ICC fixed-point values")
    return np.array(struct.unpack(">" + "i" * (len(raw) // 4), raw)) / 65536


def _curve(tag):
    if tag[:4] != b"para" or tag[4:8] != bytes(4) or tag[10:12] != bytes(2):
        raise ValueError("Unsupported ICC TRC")
    kind = int.from_bytes(tag[8:10], "big")
    if kind not in (0, 3) or len(tag) != {0: 16, 3: 32}[kind]:
        raise ValueError("Unsupported ICC TRC")
    parameters = _fixed(tag[12:])
    gamma = parameters[0]
    if not .1 <= gamma <= 5:
        raise ValueError("Unsupported ICC gamma")
    if kind == 3:
        # Qualify only the generated sRGB-shaped curve, not arbitrary breakpoints.
        reference = [2.4, 1 / 1.055, .055 / 1.055, 1 / 12.92, .04045]
        if not np.allclose(parameters, reference, atol=1 / 65536, rtol=0):
            raise ValueError("Unsupported ICC piecewise TRC")
    return kind, parameters


def read_matrix_profile(raw):
    """Narrow ICC subset; metadata stays in memory and is never emitted."""
    if type(raw) is not bytes or not 132 <= len(raw) <= 65536:
        raise ValueError("Missing/malformed ICC")
    if (int.from_bytes(raw[:4], "big") != len(raw) or raw[8] != 4
            or raw[12:24] != b"mntrRGB XYZ " or raw[36:40] != b"acsp"
            or not np.allclose(_fixed(raw[68:80]), D50, atol=2 / 65536, rtol=0)):
        raise ValueError("Unsupported ICC header/PCS")
    count = int.from_bytes(raw[128:132], "big")
    if not 1 <= count <= 32 or 132 + 12 * count > len(raw):
        raise ValueError("Invalid ICC tag table")
    allowed = {b"desc", b"cprt", b"wtpt", b"chad", b"chrm",
               b"rXYZ", b"gXYZ", b"bXYZ", b"rTRC", b"gTRC", b"bTRC"}
    tags, spans = {}, []
    for index in range(count):
        name, offset, length = struct.unpack(">4sII", raw[132 + 12 * index:144 + 12 * index])
        if (name not in allowed or name in tags or offset % 4
                or offset < 132 + 12 * count or length < 8 or offset + length > len(raw)):
            raise ValueError("Unsupported/malformed ICC tag")
        span = (offset, offset + length)
        for previous in spans:
            # Shared identical TRCs are legal; partial overlapping structures are not.
            if max(span[0], previous[0]) < min(span[1], previous[1]) and span != previous:
                raise ValueError("Overlapping ICC tags")
        spans.append(span)
        tags[name] = raw[offset:offset + length]
    required = {b"wtpt", b"chad", b"rXYZ", b"gXYZ", b"bXYZ", b"rTRC", b"gTRC", b"bTRC"}
    if not required <= tags.keys():
        raise ValueError("Missing ICC matrix/TRC/adaptation evidence")
    def xyz(name):
        tag = tags[name]
        if len(tag) != 20 or tag[:8] != b"XYZ " + bytes(4):
            raise ValueError("Invalid ICC XYZ tag")
        return _fixed(tag[8:])
    matrix = np.column_stack([xyz(name) for name in (b"rXYZ", b"gXYZ", b"bXYZ")])
    chad = tags[b"chad"]
    if len(chad) != 44 or chad[:8] != b"sf32" + bytes(4):
        raise ValueError("Unsupported ICC adaptation")
    adaptation = _fixed(chad[8:]).reshape(3, 3)
    if (np.linalg.det(matrix) <= 1e-6 or np.linalg.cond(matrix) >= 100
            or (matrix <= 0).any() or not np.allclose(matrix.sum(axis=1), D50, atol=.002, rtol=0)
            or not np.allclose(xyz(b"wtpt"), D50, atol=2 / 65536, rtol=0)
            or np.linalg.det(adaptation) <= 0 or np.linalg.cond(adaptation) >= 100):
        raise ValueError("Unsupported ICC matrix/white/adaptation")
    # In this subset, D50 colourants are used directly; applying chad again is wrong.
    return matrix, [_curve(tags[name]) for name in (b"rTRC", b"gTRC", b"bTRC")]


def _lab(xyz):
    ratio = xyz / D50
    delta = 6 / 29
    values = np.where(ratio > delta**3, np.cbrt(ratio), ratio / (3 * delta**2) + 4 / 29)
    return np.stack([116 * values[..., 1] - 16,
                     500 * (values[..., 0] - values[..., 1]),
                     200 * (values[..., 1] - values[..., 2])], axis=-1)


def _array(values):
    array = np.asarray(values)
    if (array.dtype.str != "<f4" or array.ndim != 3 or array.shape[2] != 3
            or not all(1 <= side <= MAX_SIDE for side in array.shape[:2])
            or not array.flags.c_contiguous or not np.isfinite(array).all()
            or array.min() < RANGE[0] or array.max() > RANGE[1]):
        raise ValueError("Invalid finite/range/dtype/shape/order B1 array")
    return array


def _interpret_generated(rgb, profile):
    """Float64 interpretation kept separate for independent arithmetic tests."""
    if (not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8 or rgb.ndim != 3
            or rgb.shape[2] != 3 or not all(1 <= x <= MAX_SIDE for x in rgb.shape[:2])):
        raise ValueError("Expected bounded generated uint8 RGB array")
    matrix, curves = read_matrix_profile(profile)
    values = rgb.astype(np.float64) / 255
    linear = np.empty_like(values)
    for channel, (kind, parameters) in enumerate(curves):
        current = values[..., channel]
        if kind == 0:
            linear[..., channel] = current ** parameters[0]
        else:
            gamma, a, b, c, d = parameters
            linear[..., channel] = np.where(current >= d, (a * current + b) ** gamma, c * current)
    xyz = linear @ matrix.T
    extended = encode_extended(xyz @ np.linalg.inv(SRGB_D50).T)
    return xyz, extended


def convert_generated(rgb, profile):
    """Caller-owned GENERATED arrays only. No path, image decoder or fallback."""
    xyz, extended = _interpret_generated(rgb, profile)
    stored = _array(np.ascontiguousarray(extended, dtype="<f4"))
    reconstructed = decode_extended(stored) @ SRGB_D50.T
    xyz_error = float(np.max(np.abs(reconstructed - xyz)))
    lab_error = float(np.max(np.linalg.norm(_lab(reconstructed) - _lab(xyz), axis=-1)))
    if xyz_error > CONTRACT["float32_xyz_abs"] or lab_error > CONTRACT["float32_lab_de76"]:
        raise ValueError("Float representation precision qualification failed")
    return stored, {"source_rgb_sha256": sha256(rgb.tobytes(order="C")).hexdigest(),
                    "profile_sha256": sha256(profile).hexdigest(),
                    "xyz_max_abs": xyz_error, "lab_max_delta_e76": lab_error,
                    "minimum": float(stored.min()), "maximum": float(stored.max()),
                    "negative_samples": int((stored < 0).sum()),
                    "above_one_samples": int((stored > 1).sum())}


def geometry(width, height):
    if any(type(x) is not int or not 1 <= x <= MAX_SIDE for x in (width, height)):
        raise ValueError("Generated geometry out of bounds")
    scale = SIZE / max(width, height)
    w, h = max(1, round(width * scale)), max(1, round(height * scale))
    return [(SIZE - w) // 2, (SIZE - h) // 2, w, h]


def letterbox(values):
    source = _array(values)
    height, width = source.shape[:2]
    left, top, w, h = geometry(width, height)
    x = np.maximum(0, np.minimum((np.arange(w) + .5) * width / w - .5, width - 1))
    y = np.maximum(0, np.minimum((np.arange(h) + .5) * height / h - .5, height - 1))
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, width - 1), np.minimum(y0 + 1, height - 1)
    dx, dy = (x - x0)[None, :, None], (y - y0)[:, None, None]
    # Convex bilinear weights preserve range; no clipping or uint8 conversion.
    upper = source[y0[:, None], x0] * (1 - dx) + source[y0[:, None], x1] * dx
    lower = source[y1[:, None], x0] * (1 - dx) + source[y1[:, None], x1] * dx
    resized = upper * (1 - dy) + lower * dy
    canvas = np.broadcast_to(models.MEAN, (SIZE, SIZE, 3)).copy()
    canvas[top:top + h, left:left + w] = resized.astype("<f4")
    return _array(canvas), [left, top, w, h]


def normalize(values):
    extended = _array(values)
    if extended.shape != (SIZE, SIZE, 3):
        raise ValueError("Expected fixed B1 model view")
    return ((extended - models.MEAN) / models.STD).transpose(2, 0, 1).copy()


def display_preview(values):
    """Bounded display derivative ONLY; never substitute for the model array."""
    extended = _array(values)
    preview = np.rint(np.clip(extended, 0, 1) * 255).astype(np.uint8)
    return preview, {"meaning": "unoverlaid display preview; gamut conversion may lose colour",
                     "clipped_pixels": int(((extended < 0) | (extended > 1)).any(axis=2).sum())}


def build_generated_payload(rgb, profile):
    canonical, evidence = convert_generated(rgb, profile)
    view, box = letterbox(canonical)
    stream = io.BytesIO()
    np.lib.format.write_array(stream, view, version=(1, 0), allow_pickle=False)
    payload = stream.getvalue()
    receipt = {"version": VERSION, "scope": "generated_only_not_production",
               "contract_sha256": contract_hash(), "payload_sha256": sha256(payload).hexdigest(),
               "source_rgb_sha256": evidence["source_rgb_sha256"],
               "profile_sha256": evidence["profile_sha256"],
               "source_size_wh": [rgb.shape[1], rgb.shape[0]], "valid_box": box}
    return payload, receipt, evidence


def _sha(value):
    return type(value) is str and len(value) == 64 and all(x in "0123456789abcdef" for x in value)


def load_generated_payload(payload, receipt, trusted_receipt_sha256):
    """Strict bytes-only NPY loader; caller must separately trust receipt digest."""
    keys = {"version", "scope", "contract_sha256", "payload_sha256", "source_rgb_sha256",
            "profile_sha256", "source_size_wh", "valid_box"}
    if (type(receipt) is not dict or set(receipt) != keys or not _sha(trusted_receipt_sha256)
            or digest_json(receipt) != trusted_receipt_sha256
            or receipt["version"] != VERSION or receipt["scope"] != CONTRACT["scope"]
            or receipt["contract_sha256"] != contract_hash()
            or not all(_sha(receipt[k]) for k in keys if k.endswith("sha256"))):
        raise ValueError("Untrusted/stale/invalid B1 receipt")
    dims = receipt["source_size_wh"]
    if type(dims) is not list or len(dims) != 2 or receipt["valid_box"] != geometry(*dims):
        raise ValueError("Invalid B1 receipt geometry")
    if (type(payload) is not bytes or not 10 <= len(payload) <= SIZE * SIZE * 12 + 522
            or sha256(payload).hexdigest() != receipt["payload_sha256"]
            or payload[:8] != b"\x93NUMPY\x01\x00"):
        raise ValueError("Invalid B1 NPY bytes/hash/version")
    header_size = int.from_bytes(payload[8:10], "little")
    header_bytes = payload[10:10 + header_size]
    if (not 1 <= header_size <= 512 or (10 + header_size) % 16
            or not header_bytes.endswith(b"\n")):
        raise ValueError("Invalid B1 NPY header length")
    try:
        parsed = ast.parse(header_bytes.decode("ascii").strip(), mode="eval").body
        if not isinstance(parsed, ast.Dict) or len(parsed.keys) != 3:
            raise ValueError("Invalid B1 NPY header fields")
        header = ast.literal_eval(parsed)
    except (ValueError, SyntaxError, UnicodeError):
        raise ValueError("Malformed B1 NPY header") from None
    if (type(header) is not dict or set(header) != {"descr", "fortran_order", "shape"}
            or header["descr"] != "<f4" or header["fortran_order"] is not False
            or type(header["shape"]) is not tuple or header["shape"] != (SIZE, SIZE, 3)
            or any(type(x) is not int for x in header["shape"])
            or len(payload) != 10 + header_size + SIZE * SIZE * 12):
        raise ValueError("Unsafe B1 NPY schema/length")
    # All structural bounds are checked before NumPy allocation; never unpickle.
    array = np.load(io.BytesIO(payload), allow_pickle=False, max_header_size=512)
    _array(array)
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class B1Input:
    original_rgb: np.ndarray  # Explicit display preview, not canonical data.
    normalized_chw: np.ndarray
    valid_box: tuple
    display_evidence: dict


def prepare_generated(rgb, profile):
    """Use unchanged Grad-CAM math with float model data and separate preview."""
    canonical, _ = convert_generated(rgb, profile)
    view, box = letterbox(canonical)
    preview, display_evidence = display_preview(canonical)
    return B1Input(preview, normalize(view), tuple(box), display_evidence)


def generated_gradcam(model, target_layer, prepared, class_index=None):
    """Retain preview disclosure in results without changing historical CAM code."""
    if not isinstance(prepared, B1Input):
        raise ValueError("B1 generated input required")
    return {**models.class_gradcam(model, target_layer, prepared, class_index),
            "display_evidence": dict(prepared.display_evidence),
            "scope": CONTRACT["scope"]}


def run_generated_smoke():
    """Fixed synthetic colours/profile only. No paths, dataset or model execution."""
    from src.vision.gamut_mapping_feasibility import _generated_profile
    profile, _ = _generated_profile(2.2, 2**-6)
    rgb = np.array([[[255, 0, 0], [0, 0, 255]], [[224, 48, 0], [0, 48, 224]]], dtype=np.uint8)
    payload, receipt, evidence = build_generated_payload(rgb, profile)
    loaded = load_generated_payload(payload, receipt, digest_json(receipt))
    model_input = normalize(loaded)
    return {"scope": CONTRACT["scope"], "contract_sha256": contract_hash(),
            "conversion": evidence, "loaded_min": float(loaded.min()),
            "loaded_max": float(loaded.max()), "normalized_min": float(model_input.min()),
            "normalized_max": float(model_input.max()), "payload_bytes": len(payload),
            "receipt_sha256": digest_json(receipt), "payload_sha256": receipt["payload_sha256"],
            "production_active": False, "real_data_accessed": False}


if __name__ == "__main__":
    print(json.dumps(run_generated_smoke(), indent=2, allow_nan=False))
