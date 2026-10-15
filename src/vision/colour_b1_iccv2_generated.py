"""Isolated ICC v2 qualification. Caller-owned GENERATED pixels/profiles only.

No image decoder, filesystem input, exporter dispatch or real-use permission.
Matrix colourants must already express media-relative XYZ in D50 PCS.
"""
from dataclasses import dataclass
from hashlib import sha256
import io
import struct

import numpy as np

from src.vision import colour_b1_prototype as b1


VERSION = "b1-iccv2-generated-v1"
D65 = np.array([.95047, 1., 1.08883])
BRADFORD = np.array([[.8951, .2664, -.1614],
                     [-.7502, 1.7135, .0367], [.0389, -.0685, 1.0296]])
CONTRACT = {
    "version": VERSION, "scope": "generated_only_not_production",
    "representation_sha256": b1.contract_hash(),
    "icc": "v2_mntr_RGB_XYZ_D50_matrix_curv_count1_no_chad",
    "intent": "media_relative_colorimetric_no_black_point_compensation",
    "white": "D50_or_D65_family_no_automatic_white_adaptation",
    "pcs_white_abs": 3 / 65536,
    "d65_white_abs": .0005,
    "gamma_range": [.1, 5.],
    "source_lab_reference_delta_e76": .01,
    "scalar_rgb_reference_abs": 1e-10,
    "production_active": False,
}


@dataclass(frozen=True)
class GeneratedProfile:
    matrix: np.ndarray
    gammas: np.ndarray
    media_white: np.ndarray
    inferred_adaptation: np.ndarray
    white_family: str
    profile_sha256: str


def contract_hash():
    return b1.digest_json(CONTRACT)


def _bradford_to_d50(white):
    # Missing chad does NOT mean identity. Infer a diagnostic CAT from the
    # explicit supported media white, never apply it twice to PCS colourants.
    cone = BRADFORD @ white
    if not np.isfinite(cone).all() or (cone <= 0).any():
        raise ValueError("Invalid adaptation white")
    return np.linalg.solve(BRADFORD, np.diag((BRADFORD @ b1.D50) / cone) @ BRADFORD)


def read_generated_profile(raw):
    """Strict versioned subset; never accepts a path or opens any file."""
    if type(raw) is not bytes or not 132 <= len(raw) <= 65536:
        raise ValueError("Missing/malformed generated ICC v2")
    if (int.from_bytes(raw[:4], "big") != len(raw) or raw[8] != 2
            or raw[12:24] != b"mntrRGB XYZ " or raw[36:40] != b"acsp"
            or int.from_bytes(raw[64:68], "big") > 3
            or not np.allclose(b1._fixed(raw[68:80]), b1.D50, atol=2/65536, rtol=0)):
        raise ValueError("Unsupported ICC v2 header/PCS")
    count = int.from_bytes(raw[128:132], "big")
    end_table = 132 + 12 * count
    if not 1 <= count <= 16 or end_table > len(raw):
        raise ValueError("Invalid ICC v2 tag table")
    required = {b"wtpt", b"rXYZ", b"gXYZ", b"bXYZ", b"rTRC", b"gTRC", b"bTRC"}
    allowed = required | {b"desc", b"cprt"}
    tags, spans = {}, []
    for index in range(count):
        name, offset, size = struct.unpack_from(">4sII", raw, 132 + 12*index)
        if (name not in allowed or name in tags or offset % 4 or offset < end_table
                or size < 8 or offset + size > len(raw)):
            raise ValueError("Unsupported/malformed ICC v2 tag")
        span = (offset, offset + size)
        for previous, previous_name in spans:
            overlap = max(span[0], previous[0]) < min(span[1], previous[1])
            shared_trc = span == previous and name.endswith(b"TRC") and previous_name.endswith(b"TRC")
            if overlap and not shared_trc:
                raise ValueError("Overlapping ICC v2 tags")
        spans.append((span, name))
        tags[name] = raw[offset:offset+size]
    if not required <= tags.keys():
        raise ValueError("Missing ICC v2 colour evidence")

    def xyz(name):
        tag = tags[name]
        if len(tag) != 20 or tag[:8] != b"XYZ " + bytes(4):
            raise ValueError("Invalid ICC v2 XYZ tag")
        return b1._fixed(tag[8:])

    # Metadata text is never decoded, emitted or included in an NPY payload.
    for name, kind in ((b"desc", b"desc"), (b"cprt", b"text")):
        if name in tags and tags[name][:8] != kind + bytes(4):
            raise ValueError("Unsupported ICC v2 metadata type")
    white = xyz(b"wtpt")
    if np.allclose(white, b1.D50, atol=2/65536, rtol=0):
        white_family = "D50"
    elif np.allclose(white, D65, atol=CONTRACT["d65_white_abs"], rtol=0):
        # Covers rounded tabulated D65 and xy(.3127,.3290) conventions only.
        white_family = "D65"
    else:
        raise ValueError("Ambiguous/unsupported ICC v2 media white")
    matrix = np.column_stack([xyz(name) for name in (b"rXYZ", b"gXYZ", b"bXYZ")])
    if (not np.isfinite(matrix).all() or (matrix <= 0).any()
            or np.linalg.det(matrix) <= 1e-6 or np.linalg.cond(matrix) >= 100
            or not np.allclose(matrix.sum(axis=1), b1.D50,
                               atol=CONTRACT["pcs_white_abs"], rtol=0)):
        raise ValueError("Matrix not qualified D50 PCS; wrong/ambiguous adaptation")
    adaptation = _bradford_to_d50(white)
    device_matrix = np.linalg.solve(adaptation, matrix)
    # This is a consistency check, not proof of the camera/profile's truth.
    totals = device_matrix.sum(axis=0)
    if (not np.isfinite(adaptation).all() or np.linalg.det(adaptation) <= 0
            or np.linalg.cond(adaptation) >= 100 or (device_matrix <= 0).any()
            or (totals <= 0).any()):
        raise ValueError("Invalid ICC v2 recovered device colourants")
    gammas = []
    for name in (b"rTRC", b"gTRC", b"bTRC"):
        tag = tags[name]
        if len(tag) != 14 or tag[:12] != b"curv" + bytes(4) + struct.pack(">I", 1):
            raise ValueError("Only ICC v2 curv count-one gamma is qualified")
        gamma = int.from_bytes(tag[12:14], "big") / 256
        if not CONTRACT["gamma_range"][0] <= gamma <= CONTRACT["gamma_range"][1]:
            raise ValueError("Unsupported ICC v2 gamma")
        gammas.append(gamma)
    arrays = [matrix, np.array(gammas), white, adaptation]
    for array in arrays:
        array.setflags(write=False)
    return GeneratedProfile(*arrays, white_family, sha256(raw).hexdigest())


def interpret_generated(rgb, profile):
    """Relative PCS math uses D50 matrix directly, without an extra CAT."""
    if (not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8 or rgb.ndim != 3
            or rgb.shape[2] != 3 or not all(1 <= x <= b1.MAX_SIDE for x in rgb.shape[:2])):
        raise ValueError("Expected bounded GENERATED uint8 RGB array")
    parsed = read_generated_profile(profile)
    linear = (rgb.astype(np.float64) / 255) ** parsed.gammas
    xyz = b1._finite(linear @ parsed.matrix.T)
    extended = b1.encode_extended(np.linalg.solve(b1.SRGB_D50, xyz.reshape(-1, 3).T).T.reshape(xyz.shape))
    return xyz, extended


def convert_generated(rgb, profile):
    xyz, extended = interpret_generated(rgb, profile)
    stored = b1._array(np.ascontiguousarray(extended, dtype="<f4"))
    recovered = b1.decode_extended(stored) @ b1.SRGB_D50.T
    xyz_error = float(np.max(np.abs(recovered - xyz)))
    lab_error = float(np.linalg.norm(b1._lab(recovered) - b1._lab(xyz), axis=-1).max())
    if xyz_error > b1.CONTRACT["float32_xyz_abs"] or lab_error > b1.CONTRACT["float32_lab_de76"]:
        raise ValueError("ICC v2 B1 precision qualification failed")
    return stored, {"xyz_max_abs": xyz_error, "lab_max_delta_e76": lab_error,
                    "minimum": float(stored.min()), "maximum": float(stored.max()),
                    "source_rgb_sha256": sha256(rgb.tobytes(order="C")).hexdigest(),
                    "profile_sha256": sha256(profile).hexdigest()}


def build_generated_payload(rgb, profile):
    # Reuse the unchanged strict B1 NPY schema; bind the new interpretation
    # contract in an outer receipt, instead of pretending this is v4 input.
    canonical, evidence = convert_generated(rgb, profile)
    view, box = b1.letterbox(canonical)
    stream = io.BytesIO()
    np.lib.format.write_array(stream, view, version=(1, 0), allow_pickle=False)
    payload = stream.getvalue()
    storage = {"version": b1.VERSION, "scope": b1.CONTRACT["scope"],
               "contract_sha256": b1.contract_hash(), "payload_sha256": sha256(payload).hexdigest(),
               "source_rgb_sha256": evidence["source_rgb_sha256"],
               "profile_sha256": evidence["profile_sha256"],
               "source_size_wh": [rgb.shape[1], rgb.shape[0]], "valid_box": box}
    receipt = {"version": VERSION, "scope": CONTRACT["scope"],
               "contract_sha256": contract_hash(), "storage_receipt": storage}
    return payload, receipt, evidence


def load_generated_payload(payload, receipt, trusted_receipt_sha256):
    if (type(receipt) is not dict
            or set(receipt) != {"version", "scope", "contract_sha256", "storage_receipt"}
            or not b1._sha(trusted_receipt_sha256)
            or b1.digest_json(receipt) != trusted_receipt_sha256
            or receipt["version"] != VERSION or receipt["scope"] != CONTRACT["scope"]
            or receipt["contract_sha256"] != contract_hash()
            or type(receipt["storage_receipt"]) is not dict):
        raise ValueError("Untrusted/stale ICC v2 generated receipt")
    storage = receipt["storage_receipt"]
    return b1.load_generated_payload(payload, storage, b1.digest_json(storage))
