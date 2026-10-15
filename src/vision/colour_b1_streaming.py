"""Versioned GENERATED-ONLY B1 full-resolution engineering prototype.

No real-source path/ICC ingestion, dataset selection, packaging or approval.
Pixels are generated on demand; canonical NPY data are streamed, never mmap'd.
"""
import ast
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import stat

import numpy as np

from src.vision import colour_b1_prototype as b1


VERSION = "b1-generated-full-v2"
MAX_SIDE = 16384
MAX_PIXELS = 40000000
TILE_PIXELS = 65536
CONTRACT = {"version": VERSION, "scope": "generated_only_not_production",
            "base_contract_sha256": b1.contract_hash(), "max_side": MAX_SIDE,
            "max_pixels": MAX_PIXELS, "tile_pixels": TILE_PIXELS,
            "full_dtype": "<f4", "layout": "HWC_C", "npy_version": [1, 0],
            "source_hash": "generated_uint8_rgb_row_major_bytes",
            "model_sampling": "same_v1_float32_before_bilinear",
            "stress_peak_rss_limit_bytes": 512 * 1024**2}
FILES = {"full_rgb.npy", "model_rgb.npy", "receipt.json"}


def _size(width, height):
    if (any(type(v) is not int or not 1 <= v <= MAX_SIDE for v in (width, height))
            or width * height > MAX_PIXELS):
        raise ValueError("Generated full geometry exceeds qualified bounds")


@dataclass(frozen=True)
class GeneratedSource:
    width: int
    height: int
    pattern: str = "mixed"
    profile_kind: str = "wide_red"

    def __post_init__(self):
        _size(self.width, self.height)
        if (type(self.pattern) is not str or type(self.profile_kind) is not str
                or self.pattern not in {"primaries", "ramp", "shadows", "mixed"}
                or self.profile_kind not in {"srgb", "gamma18", "wide_red"}):
            raise ValueError("Unknown generated fixture; no real source allowed")

    def profile(self):
        from src.vision.gamut_mapping_feasibility import _generated_profile
        gamma, strength = {"srgb": (None, 0), "gamma18": (1.8, 0),
                           "wide_red": (2.2, 2**-6)}[self.profile_kind]
        return _generated_profile(gamma, strength)[0]

    def pixels(self, offset, count):
        """Return only a bounded flat row-major generated RGB segment."""
        if (type(offset) is not int or type(count) is not int or offset < 0
                or not 1 <= count <= TILE_PIXELS or offset + count > self.width * self.height):
            raise ValueError("Invalid generated chunk")
        index = np.arange(offset, offset + count, dtype=np.int64)
        x, y = index % self.width, index // self.width
        primaries = np.array([[255, 0, 0], [0, 0, 255], [0, 255, 0], [255, 255, 255],
                              [0, 0, 0], [224, 48, 0], [0, 48, 224]], dtype=np.uint8)
        if self.pattern == "primaries":
            return primaries[index % len(primaries)]
        if self.pattern == "ramp":
            return np.stack([x % 256, y % 256, (3*x + 5*y) % 256], axis=-1).astype(np.uint8)
        pixels = np.repeat(((x + y) % 32).astype(np.uint8)[:, None], 3, axis=1)
        if self.pattern == "mixed":
            selected = index % 17 == 0
            pixels[selected] = primaries[(index[selected] // 17) % len(primaries)]
        return pixels


def _chunks(total, tile_pixels=TILE_PIXELS):
    if type(tile_pixels) is not int or not 256 <= tile_pixels <= TILE_PIXELS or tile_pixels % 256:
        raise ValueError("Invalid bounded chunk limit")
    offset = 0
    while offset < total:
        count = min(tile_pixels, total - offset)
        height, width = (count // 256, 256) if count >= 256 else (1, count)
        count = height * width
        yield offset, count, (height, width, 3)
        offset += count


def _open(path, write=False):
    flags = os.O_NOFOLLOW | (os.O_WRONLY | os.O_CREAT | os.O_EXCL if write else os.O_RDONLY)
    descriptor = os.open(path, flags, 0o600)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError("Regular generated file required")
    return os.fdopen(descriptor, "wb" if write else "rb")


def _identity(stream):
    value = os.fstat(stream.fileno())
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _header(stream, shape):
    """V1 strict NPY schema with separately versioned full-resolution bounds."""
    height, width, channels = shape
    _size(width, height)
    first = stream.read(10)
    if len(first) != 10 or first[:8] != b"\x93NUMPY\x01\x00" or channels != 3:
        raise ValueError("Invalid streaming NPY version/shape")
    length = int.from_bytes(first[8:10], "little")
    if not 1 <= length <= 512 or (10 + length) % 16:
        raise ValueError("Invalid streaming NPY header length")
    raw = stream.read(length)
    try:
        node = ast.parse(raw.decode("ascii").strip(), mode="eval").body
        if not raw.endswith(b"\n") or not isinstance(node, ast.Dict) or len(node.keys) != 3:
            raise ValueError("Invalid header fields")
        header = ast.literal_eval(node)
    except (SyntaxError, UnicodeError, ValueError):
        raise ValueError("Malformed streaming NPY header") from None
    if (type(header) is not dict or set(header) != {"descr", "fortran_order", "shape"}
            or header["descr"] != "<f4" or header["fortran_order"] is not False
            or type(header["shape"]) is not tuple or header["shape"] != tuple(shape)
            or any(type(v) is not int for v in header["shape"])
            or os.fstat(stream.fileno()).st_size != 10 + length + width * height * 12):
        raise ValueError("Unsafe streaming NPY dtype/order/shape/length")
    return first + raw


def _inspect(stream, shape):
    start_identity = _identity(stream)
    stream.seek(0)
    header = _header(stream, shape)
    digest = sha256(header)
    minimum, maximum, negative, above = float("inf"), -float("inf"), 0, 0
    for _, count, chunk_shape in _chunks(shape[0] * shape[1]):
        raw = stream.read(count * 12)
        if len(raw) != count * 12:
            raise ValueError("Truncated generated NPY payload")
        values = np.frombuffer(raw, dtype="<f4").reshape(chunk_shape)
        b1._array(values)  # Reuse frozen finite/range/layout validation per tile.
        digest.update(raw)
        minimum, maximum = min(minimum, float(values.min())), max(maximum, float(values.max()))
        negative += int((values < 0).sum())
        above += int((values > 1).sum())
    if _identity(stream) != start_identity:
        raise ValueError("Generated payload changed during verification")
    return {"sha256": digest.hexdigest(), "bytes": start_identity[2], "shape": list(shape),
            "minimum": minimum, "maximum": maximum,
            "negative_samples": negative, "above_one_samples": above}, len(header), start_identity


def full_geometry(width, height):
    _size(width, height)
    scale = b1.SIZE / max(width, height)
    w, h = max(1, round(width * scale)), max(1, round(height * scale))
    return [(b1.SIZE - w) // 2, (b1.SIZE - h) // 2, w, h]


def _model_view(stream, offset, width, height, verified_identity):
    """At most two source rows in RAM; same float64 bilinear order as B1 v1."""
    start_identity = _identity(stream)
    if start_identity != verified_identity:
        raise ValueError("Canonical identity changed after hash scan")
    left, top, w, h = full_geometry(width, height)
    x = np.maximum(0, np.minimum((np.arange(w) + .5) * width / w - .5, width - 1))
    x0, x1 = np.floor(x).astype(int), np.minimum(np.floor(x).astype(int) + 1, width - 1)
    dx = (x - x0)[:, None]
    canvas = np.broadcast_to(b1.models.MEAN, (b1.SIZE, b1.SIZE, 3)).copy()
    for row in range(h):
        y = max(0., min((row + .5) * height / h - .5, height - 1))
        y0, y1 = int(np.floor(y)), min(int(np.floor(y)) + 1, height - 1)
        rows = []
        for index in (y0, y1):
            stream.seek(offset + index * width * 12)
            raw = stream.read(width * 12)
            if len(raw) != width * 12:
                raise ValueError("Canonical row truncated")
            rows.append(np.frombuffer(raw, dtype="<f4").reshape(width, 3))
        upper = rows[0][x0] * (1 - dx) + rows[0][x1] * dx
        lower = rows[1][x0] * (1 - dx) + rows[1][x1] * dx
        canvas[top + row, left:left + w] = (upper * (1 - (y - y0)) + lower * (y - y0)).astype("<f4")
    if _identity(stream) != start_identity:
        raise ValueError("Canonical file changed during model sampling")
    return b1._array(canvas)


def _write_full(source, path, tile_pixels):
    profile = source.profile()
    b1.read_matrix_profile(profile)  # Fail before output on unsupported generated ICC.
    source_hash = sha256()
    numeric = {"xyz_max_abs": 0., "lab_max_delta_e76": 0., "peak_chunk_pixels": 0}
    with _open(path, write=True) as stream:
        np.lib.format.write_array_header_1_0(stream, {"descr": "<f4", "fortran_order": False,
                                                   "shape": (source.height, source.width, 3)})
        for offset, count, shape in _chunks(source.width * source.height, tile_pixels):
            pixels = source.pixels(offset, count).reshape(shape)
            values, evidence = b1.convert_generated(pixels, profile)
            b1._array(values)
            source_hash.update(pixels.tobytes(order="C"))
            stream.write(values.tobytes(order="C"))
            for key in ("xyz_max_abs", "lab_max_delta_e76"):
                numeric[key] = max(numeric[key], evidence[key])
            numeric["peak_chunk_pixels"] = max(numeric["peak_chunk_pixels"], count)
    return {"generated_source": asdict(source), "source_rgb_sha256": source_hash.hexdigest(),
            "profile_sha256": sha256(profile).hexdigest(), "numeric": numeric}


def _directory(path, expected):
    if path.is_symlink() or not path.is_dir() or {p.name for p in path.iterdir()} != expected:
        raise ValueError("Unexpected/unsafe generated output directory entries")


def _verify_files(directory, receipt):
    source = GeneratedSource(**receipt["generated_source"])
    shape = (source.height, source.width, 3)
    with _open(directory / "full_rgb.npy") as full:
        evidence, offset, identity = _inspect(full, shape)
        if evidence != receipt["files"]["full_rgb.npy"]:
            raise ValueError("Canonical hash/numerical evidence mismatch")
        expected_model = _model_view(full, offset, source.width, source.height, identity)
    with _open(directory / "model_rgb.npy") as model:
        model_evidence, offset, identity = _inspect(model, (224, 224, 3))
        if model_evidence != receipt["files"]["model_rgb.npy"]:
            raise ValueError("Model hash/numerical evidence mismatch")
        model.seek(offset)
        current = np.frombuffer(model.read(224 * 224 * 12), dtype="<f4").reshape(224, 224, 3)
        if _identity(model) != identity:
            raise ValueError("Model payload changed after hash scan")
    if not np.array_equal(current, expected_model):
        raise ValueError("Model view does not match canonical geometry/content")
    return current.copy()


def _unique_json_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate generated receipt field")
        value[key] = item
    return value


def verify_generated_outputs(directory, trusted_receipt_sha256):
    directory = Path(directory)
    _directory(directory, FILES)
    with _open(directory / "receipt.json") as stream:
        if os.fstat(stream.fileno()).st_size > 16384:
            raise ValueError("Oversized generated receipt")
        receipt = json.loads(stream.read(), object_pairs_hook=_unique_json_pairs)
    keys = {"version", "scope", "base_contract_sha256", "contract_sha256", "generated_source",
            "source_rgb_sha256", "profile_sha256", "numeric", "files", "valid_box"}
    if (not b1._sha(trusted_receipt_sha256) or type(receipt) is not dict or set(receipt) != keys
            or b1.digest_json(receipt) != trusted_receipt_sha256 or receipt["version"] != VERSION
            or receipt["scope"] != CONTRACT["scope"] or receipt["base_contract_sha256"] != b1.contract_hash()
            or receipt["contract_sha256"] != b1.digest_json(CONTRACT)
            or type(receipt["files"]) is not dict
            or set(receipt["files"]) != {"full_rgb.npy", "model_rgb.npy"}
            or not b1._sha(receipt["source_rgb_sha256"]) or not b1._sha(receipt["profile_sha256"])):
        raise ValueError("Untrusted/stale/unsafe generated receipt")
    spec = receipt["generated_source"]
    numeric = receipt["numeric"]
    if (type(spec) is not dict or set(spec) != {"width", "height", "pattern", "profile_kind"}
            or type(numeric) is not dict or set(numeric) != {"xyz_max_abs", "lab_max_delta_e76", "peak_chunk_pixels"}):
        raise ValueError("Unexpected nested generated evidence")
    source = GeneratedSource(**spec)
    if (receipt["profile_sha256"] != sha256(source.profile()).hexdigest()
            or any(type(numeric[key]) not in (int, float) or not math.isfinite(numeric[key])
                   or not 0 <= numeric[key] <= b1.CONTRACT[limit] for key, limit in
                   (("xyz_max_abs", "float32_xyz_abs"), ("lab_max_delta_e76", "float32_lab_de76")))
            or type(numeric["peak_chunk_pixels"]) is not int
            or not 1 <= numeric["peak_chunk_pixels"] <= TILE_PIXELS):
        raise ValueError("Invalid numerical/profile evidence")
    if receipt["valid_box"] != full_geometry(source.width, source.height):
        raise ValueError("Invalid full-resolution geometry evidence")
    model = _verify_files(directory, receipt)
    return {"receipt": receipt, "model_rgb": model, "normalized_chw": b1.normalize(model)}


def convert_generated_full(source, directory, *, tile_pixels=TILE_PIXELS):
    """New private output only; final receipt appears after actual verification."""
    if type(source) is not GeneratedSource:
        raise ValueError("Only fixed generated source descriptors accepted")
    list(_chunks(1, tile_pixels))  # Validate engineering chunk bound before writing.
    directory = Path(directory)
    directory.mkdir(mode=0o700, exist_ok=False)
    evidence = _write_full(source, directory / "full_rgb.npy", tile_pixels)
    with _open(directory / "full_rgb.npy") as stream:
        full, offset, identity = _inspect(stream, (source.height, source.width, 3))
        model = _model_view(stream, offset, source.width, source.height, identity)
    with _open(directory / "model_rgb.npy", write=True) as stream:
        np.lib.format.write_array(stream, model, version=(1, 0), allow_pickle=False)
    with _open(directory / "model_rgb.npy") as stream:
        small, _, _ = _inspect(stream, (224, 224, 3))
    receipt = {"version": VERSION, "scope": CONTRACT["scope"], "base_contract_sha256": b1.contract_hash(),
               "contract_sha256": b1.digest_json(CONTRACT), **evidence,
               "files": {"full_rgb.npy": full, "model_rgb.npy": small},
               "valid_box": full_geometry(source.width, source.height)}
    _directory(directory, FILES - {"receipt.json"})
    _verify_files(directory, receipt)
    with _open(directory / "receipt.json", write=True) as stream:
        stream.write((json.dumps(receipt, indent=2, allow_nan=False) + "\n").encode("ascii"))
    return {"directory": str(directory), "receipt_sha256": b1.digest_json(receipt), "receipt": receipt}
