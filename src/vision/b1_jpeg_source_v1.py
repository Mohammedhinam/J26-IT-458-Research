"""Explicit B1 JPEG adapter. Source reads require an authorized caller.

No dataset scanning, packaging dispatch, downloads or source writes. Reuses
qualified mathematics, not the generated-only export authorization API.
"""
from contextlib import contextmanager
from hashlib import sha256
import os

import numpy as np
from PIL import Image

from src.vision import colour_b1_iccv2_generated as v2
from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_streaming as stream
from src.vision import colour_qa as qa


VERSION = "b1-jpeg-source-v1"
CONTRACT = {
    "version": VERSION, "scope": "local_provisional_development_only",
    "interpretation_sha256": v2.contract_hash(),
    "representation_sha256": b1.contract_hash(),
    "max_side": stream.MAX_SIDE, "max_pixels": stream.MAX_PIXELS,
    "tile_pixels": stream.TILE_PIXELS, "jpeg": "RGB8_orientation1_embedded_supported_ICCv2",
    "cube_codes": 256**3, "lcms_lab_limit": .01,
    "xyz_limit": 2e-6, "lab_limit": .002, "range": [-16., 16.],
    "model_view": "float32_source_samples_then_frozen_B1_bilinear224",
    "option_a_fallback": False,
}


def identity(handle):
    st = os.fstat(handle.fileno())
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def checked_header(handle, dimensions):
    handle.seek(0)
    image = Image.open(handle)
    if (image.format != "JPEG" or image.mode != "RGB" or image.size != tuple(dimensions)
            or image.getexif().get(274, 1) != 1):
        raise ValueError("JPEG/RGB/geometry/orientation not supported")
    stream._size(*image.size)
    profile = image.info.get("icc_profile")
    parsed = v2.read_generated_profile(profile)  # Pure structural parser, no generated IO/dispatch.
    if not np.all(parsed.gammas == parsed.gammas[0]):
        raise ValueError("Unequal-channel real profile family not independently qualified")
    return image, profile


@contextmanager
def decoded(path, expected_hash, dimensions, profile_hash):
    with stream._open(path) as handle:
        before = identity(handle)
        digest = sha256()
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            digest.update(chunk)
        if digest.hexdigest() != expected_hash:
            raise ValueError("Source SHA mismatch before JPEG decoding")
        image, profile = checked_header(handle, dimensions)
        if sha256(profile).hexdigest() != profile_hash:
            raise ValueError("Source ICC differs from qualified profile")
        image.load()
        try:
            if identity(handle) != before:
                raise ValueError("Source identity changed while decoding")
            yield image
        finally:
            image.close()
        if identity(handle) != before:
            raise ValueError("Source identity changed during B1 conversion")


class Converter:
    def __init__(self, profile):
        self.parsed = v2.read_generated_profile(profile)
        self.lookup = (np.arange(256, dtype=float)[:, None]/255) ** self.parsed.gammas
        self.inverse = np.linalg.inv(b1.SRGB_D50)

    def convert(self, pixels, *, precision=False):
        if (not isinstance(pixels, np.ndarray) or pixels.dtype != np.uint8
                or pixels.ndim != 3 or pixels.shape[-1] != 3
                or not 0 < pixels.shape[0]*pixels.shape[1] <= stream.TILE_PIXELS):
            raise ValueError("Bounded RGB8 tile required")
        linear = np.empty(pixels.shape, dtype=np.float64)
        for channel in range(3):
            linear[..., channel] = self.lookup[pixels[..., channel], channel]
        xyz = linear @ self.parsed.matrix.T
        encoded = b1.encode_extended(xyz @ self.inverse.T)
        values = np.ascontiguousarray(encoded, dtype="<f4")
        validate_values(values)
        evidence = {}
        if precision:
            recovered = b1.decode_extended(values) @ b1.SRGB_D50.T
            evidence = {"xyz_max_abs": float(np.abs(recovered-xyz).max()),
                        "lab_max_delta_e76": float(np.linalg.norm(b1._lab(recovered)-b1._lab(xyz), axis=-1).max())}
            if evidence["xyz_max_abs"] > CONTRACT["xyz_limit"] or evidence["lab_max_delta_e76"] > CONTRACT["lab_limit"]:
                raise ValueError("B1 float32 precision failure")
        return values, xyz, evidence


def validate_values(values):
    if (values.dtype.str != "<f4" or values.ndim != 3 or values.shape[-1] != 3
            or not values.flags.c_contiguous or not np.isfinite(values).all()
            or values.min() < b1.RANGE[0] or values.max() > b1.RANGE[1]):
        raise ValueError("Unsafe B1 float values")


def qualify_profile(profile, progress=None):
    """All generated RGB8 triplets, bounded tiles. No photograph pixels."""
    converter = Converter(profile)
    engine = qa._Transforms(profile)
    result = {"profile_sha256": sha256(profile).hexdigest(), "codes_checked": 0,
              "xyz_max_abs": 0., "lab_max_delta_e76": 0., "lcms_lab_delta_e76": 0.,
              "minimum": float("inf"), "maximum": -float("inf")}
    gb = np.indices((256, 256), dtype=np.uint16)
    pixels = np.zeros((256, 256, 3), np.uint8)
    pixels[..., 1], pixels[..., 2] = gb[0], gb[1]
    try:
        for red in range(256):
            pixels[..., 0] = red
            values, xyz, evidence = converter.convert(pixels, precision=True)
            cms_lab = engine.run(engine.source_lab, pixels, np.float64)
            if not np.isfinite(cms_lab).all():
                raise ValueError("Non-finite LittleCMS reference")
            difference = float(np.linalg.norm(cms_lab-b1._lab(xyz), axis=-1).max())
            if difference > CONTRACT["lcms_lab_limit"]:
                raise ValueError("Source ICC numerical/reference incompatibility")
            result["codes_checked"] += 65536
            for key in evidence:
                result[key] = max(result[key], evidence[key])
            result["lcms_lab_delta_e76"] = max(result["lcms_lab_delta_e76"], difference)
            result["minimum"] = min(result["minimum"], float(values.min()))
            result["maximum"] = max(result["maximum"], float(values.max()))
            if progress and red % 32 == 0:
                progress({"generated_cube_red": red})
    finally:
        engine.close()
    return result


def model_view(image, converter):
    """Sample float32 canonical source values before bilinear interpolation."""
    width, height = image.size
    left, top, w, h = stream.full_geometry(width, height)
    x = np.clip((np.arange(w)+.5)*width/w-.5, 0, width-1)
    x0 = np.floor(x).astype(int)
    x1 = np.minimum(x0+1, width-1)
    needed = np.unique(np.concatenate([x0,x1]))
    first, second = np.searchsorted(needed,x0), np.searchsorted(needed,x1)
    dx = (x-x0)[:, None]
    canvas = np.broadcast_to(b1.models.MEAN, (224, 224, 3)).copy()
    cache = {}
    for row in range(h):
        y = max(0., min((row+.5)*height/h-.5, height-1))
        y0, y1 = int(np.floor(y)), min(int(np.floor(y))+1, height-1)
        rows = []
        for index in (y0, y1):
            if index not in cache:
                with image.crop((0,index,width,index+1)) as cropped:
                    pixels = np.asarray(cropped)[:,needed,:]
                    cache[index] = converter.convert(pixels)[0][0]
            rows.append(cache[index])
        upper = rows[0][first]*(1-dx)+rows[0][second]*dx
        lower = rows[1][first]*(1-dx)+rows[1][second]*dx
        canvas[top+row, left:left+w] = (upper*(1-(y-y0))+lower*(y-y0)).astype("<f4")
        cache = {index:cache[index] for index in (y0,y1)}
    return b1._array(canvas)


def write_full_cam(image, converter, destination):
    width, height = image.size
    with stream._open(destination, write=True) as target:
        np.lib.format.write_array_header_1_0(target, {
            "descr": "<f4", "fortran_order": False, "shape": (height, width, 3)})
        rows_per_tile = max(1, stream.TILE_PIXELS//width)
        for y in range(0, height, rows_per_tile):
            pixels = np.asarray(image.crop((0, y, width, min(y+rows_per_tile, height))))
            values = converter.convert(pixels)[0]
            target.write(values.tobytes(order="C"))
