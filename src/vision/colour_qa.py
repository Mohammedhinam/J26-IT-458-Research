"""Aggregate-only colour diagnostics, never an export or approval gate.

Accepts caller-owned full-resolution PIL RGB images. Does not open paths, write
pixels, scan datasets or call packaging. The production reverse limit stays 2.
"""
import ctypes
import math

import numpy as np
from PIL import Image, _imagingcms

from src.vision import exploratory_bundle as export

# LCMS 2 format bit fields: RGB=4, Lab=10, three channels, double bytes=0.
RGB8 = (4 << 16) | (3 << 3) | 1
RGB_DOUBLE = (1 << 22) | (4 << 16) | (3 << 3)
LAB_DOUBLE = (1 << 22) | (10 << 16) | (3 << 3)
GAMUT_EPSILON = 1e-6  # Numerical reporting precision, NOT an acceptance bound.
MAX_TILE_PIXELS = 262144


class _Transforms:
    """Use Pillow's already-linked LittleCMS, including floating-point output.

    Pillow exposes only 8-bit Lab. Bind the small LCMS C API needed for double
    Lab/extended RGB instead; unavailable symbols fail closed, with no fallback.
    """
    def __init__(self, source_icc):
        self.profiles = []
        self.transforms = []
        self.library = ctypes.CDLL(_imagingcms.__file__)
        pointer, integer = ctypes.c_void_p, ctypes.c_uint32
        self.open_profile = self._bind("cmsOpenProfileFromMem", pointer, [pointer, integer])
        self.new_srgb = self._bind("cmsCreate_sRGBProfile", pointer, [])
        self.new_lab = self._bind("cmsCreateLab4Profile", pointer, [pointer])
        self.create = self._bind("cmsCreateTransform", pointer,
                                 [pointer, integer, pointer, integer, integer, integer])
        self.apply = self._bind("cmsDoTransform", None, [pointer, pointer, pointer, integer])
        self.delete = self._bind("cmsDeleteTransform", None, [pointer])
        self.close_profile = self._bind("cmsCloseProfile", ctypes.c_int, [pointer])
        self.version = self._bind("cmsGetEncodedCMMversion", integer, [])
        try:
            # Generate sRGB directly: serialising it first can round ICC fields.
            srgb = self._profile(self.new_srgb())
            lab = self._profile(self.new_lab(None))
            if source_icc is None:
                source = srgb  # Reuse the exporter's explicit untagged contract.
            else:
                self.source_buffer = ctypes.create_string_buffer(source_icc)
                source = self._profile(self.open_profile(self.source_buffer, len(source_icc)))
            self.forward = self._new(source, RGB8, srgb, RGB8)
            self.reverse = self._new(srgb, RGB8, source, RGB8)
            self.source_lab = self._new(source, RGB8, lab, LAB_DOUBLE)
            self.output_lab = self._new(srgb, RGB8, lab, LAB_DOUBLE)
            self.extended_srgb = self._new(source, RGB_DOUBLE, srgb, RGB_DOUBLE)
        except Exception:
            self.close()
            raise

    def _bind(self, name, result, arguments):
        function = getattr(self.library, name)
        function.restype, function.argtypes = result, arguments
        return function

    def _profile(self, handle):
        if not handle:
            raise ValueError("Colour QA profile creation failed")
        self.profiles.append(handle)
        return handle

    def _new(self, source, input_format, target, output_format):
        handle = self.create(source, input_format, target, output_format, 1, 0)
        if not handle:
            raise ValueError("Colour QA transform creation failed")
        self.transforms.append(handle)
        return handle

    def run(self, handle, values, dtype):
        values = np.ascontiguousarray(values)
        if values.ndim != 3 or values.shape[2] != 3 or values.size // 3 > MAX_TILE_PIXELS:
            raise ValueError("Colour QA tile shape/size invalid")
        output = np.empty(values.shape, dtype=dtype)
        self.apply(handle, values.ctypes.data, output.ctypes.data, values.size // 3)
        return output

    def close(self):
        for handle in reversed(self.transforms):
            self.delete(handle)
        for handle in reversed(self.profiles):
            self.close_profile(handle)
        self.transforms.clear()
        self.profiles.clear()


class _Distribution:
    """Fixed-memory Lab histogram; means/extrema exact, quantile bins bounded."""
    def __init__(self):
        self.width = 0.001
        self.bins = 512000
        self.histogram = np.zeros(self.bins + 1, dtype=np.int64)
        self.count, self.total = 0, 0.0
        self.minimum, self.maximum = math.inf, 0.0

    def add(self, values):
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("Colour QA non-finite distance")
        self.count += values.size
        self.total = math.fsum((self.total, float(values.sum(dtype=np.float64))))
        self.minimum = min(self.minimum, float(values.min()))
        self.maximum = max(self.maximum, float(values.max()))
        # An overflow bin avoids growing RAM or hiding very large discrepancies.
        indices = np.floor(np.minimum(values / self.width, self.bins)).astype(np.int64)
        bins, counts = np.unique(indices, return_counts=True)
        self.histogram[bins] += counts

    def result(self):
        cumulative = self.histogram.cumsum()
        bounds = {}
        for percentile in (50, 90, 95, 99, 99.9):
            rank = math.ceil(self.count * percentile / 100)
            index = int(np.searchsorted(cumulative, rank))
            lower = max(self.minimum, index * self.width)
            upper = self.maximum if index == self.bins else min(self.maximum, (index + 1) * self.width)
            bounds[str(percentile)] = [lower, upper]
        return {"count": self.count, "mean": self.total / self.count,
                "min": self.minimum, "max": self.maximum,
                "percentile_bounds": bounds, "percentile_method": "nearest-rank, enclosing bins",
                "bin_width": self.width, "overflow_count_ge_512": int(self.histogram[-1])}


def _rgb_statistics(histogram):
    count = int(histogram.sum())
    cumulative = histogram.cumsum()
    return {"max": int(np.flatnonzero(histogram)[-1]),
            "mean": float(np.dot(histogram, np.arange(256)) / count),
            "percentiles": {str(q): int(np.searchsorted(cumulative, math.ceil(count * q / 100)))
                            for q in (50, 90, 95, 99, 99.9)},
            "count_gt_current_limit": int(histogram[export.ROUNDTRIP_LIMIT + 1:].sum())}


def _finite_transform(engine, transform, pixels, dtype):
    values = engine.run(transform, pixels, dtype)
    if not np.isfinite(values).all():
        raise ValueError("Colour QA non-finite transform result")
    return values


def _measure(source, output, tile_pixels, engine):
    distance = _Distribution()
    reverse_histogram = np.zeros((4, 256), dtype=np.int64)
    gamut_count, below_count, above_count = 0, 0, 0
    channel_counts = np.zeros(3, dtype=np.int64)
    excursion_max = np.zeros(3)
    excursion_sum = 0.0
    raw_outside_count = 0
    tiles, peak_pixels = 0, 0
    tile_width = min(source.width, tile_pixels)
    tile_height = max(1, tile_pixels // tile_width)
    for top in range(0, source.height, tile_height):
        for left in range(0, source.width, tile_width):
            box = (left, top, min(left + tile_width, source.width), min(top + tile_height, source.height))
            original = np.asarray(source.crop(box))
            if output is None:
                current = _finite_transform(engine, engine.forward, original, np.uint8)
            else:
                current = np.asarray(output.crop(box))
            restored = _finite_transform(engine, engine.reverse, current, np.uint8)
            differences = np.abs(restored.astype(np.int16) - original.astype(np.int16))
            for channel in range(3):
                reverse_histogram[channel] += np.bincount(differences[..., channel].ravel(), minlength=256)
            reverse_histogram[3] += np.bincount(differences.max(axis=2).ravel(), minlength=256)

            # Compare the ACTUAL output interpretation with the source in D50 Lab.
            source_lab = _finite_transform(engine, engine.source_lab, original, np.float64)
            output_lab = _finite_transform(engine, engine.output_lab, current, np.float64)
            distance.add(np.linalg.norm(source_lab - output_lab, axis=2))
            extended = _finite_transform(engine, engine.extended_srgb, original.astype(np.float64) / 255, np.float64)
            excursion = np.maximum(-extended, 0) + np.maximum(extended - 1, 0)
            outside = excursion > GAMUT_EPSILON
            gamut_count += int(outside.any(axis=2).sum())
            below_count += int((extended < -GAMUT_EPSILON).any(axis=2).sum())
            above_count += int((extended > 1 + GAMUT_EPSILON).any(axis=2).sum())
            raw_outside_count += int((excursion > 0).any(axis=2).sum())
            channel_counts += outside.sum(axis=(0, 1))
            excursion_max = np.maximum(excursion_max, excursion.max(axis=(0, 1)))
            excursion_sum = math.fsum((excursion_sum, float(excursion.sum(dtype=np.float64))))
            tiles += 1
            peak_pixels = max(peak_pixels, original.size // 3)
    pixels = source.width * source.height
    return {"diagnostic_only": True, "acceptance_decision": "not_evaluated",
            "output_mode": "measured_supplied_srgb" if output is not None else "simulated_srgb_in_memory",
            "dimensions": list(source.size), "pixels": pixels,
            "settings": {"intent": 1, "flags": 0, "lcms_encoded_version": engine.version(),
                         "source_interpretation": "embedded_ICC" if "icc_profile" in source.info else "explicit_untagged_as_srgb_contract"},
            "forward_delta_e76_D50": distance.result(),
            "gamut": {"epsilon_normalized_rgb": GAMUT_EPSILON, "pixels_outside": gamut_count,
                      "percentage_outside": 100 * gamut_count / pixels,
                      "pixels_below": below_count, "pixels_above": above_count,
                      "raw_pixels_outside_zero_epsilon": raw_outside_count,
                      "channel_counts": channel_counts.tolist(),
                      "max_excursion_per_channel_normalized": excursion_max.tolist(),
                      "max_excursion_normalized": float(excursion_max.max()),
                      "mean_excursion_all_channel_samples": excursion_sum / (pixels * 3)},
            "reverse_rgb": {"current_limit": export.ROUNDTRIP_LIMIT,
                            "channels": dict(zip(("R", "G", "B"), map(_rgb_statistics, reverse_histogram[:3]))),
                            "per_pixel_max": _rgb_statistics(reverse_histogram[3])},
            "processing": {"tile_pixel_limit": tile_pixels, "max_tile_pixels": peak_pixels, "tiles": tiles},
            "limitations": ["Numerical ICC-profile diagnostics, not clinical colour validation.",
                            "No packaging/label/manifest approval; production guard unchanged."]}


def diagnose_forward_colour(source, exported_srgb=None, *, tile_pixels=65536):
    """Measure full-resolution aligned RGB images without saving/approving them.

    If output is omitted, simulate the current forward conversion per tile in
    RAM. Supplied output must already be declared standard sRGB, same geometry,
    with no source/private metadata. Lossless file/hash verification is separate.
    Pillow may decode each caller-owned input fully; helper arrays are bounded
    by tile_pixels (<=262144), plus a fixed ~4 MB percentile histogram.
    """
    if type(tile_pixels) is not int or not 1 <= tile_pixels <= MAX_TILE_PIXELS:
        raise ValueError("Colour QA tile pixel limit invalid")
    if not isinstance(source, Image.Image) or source.width < 1 or source.height < 1:
        raise ValueError("Colour QA requires a nonempty PIL RGB source")
    export.check_source_colour(source)  # Reuse existing profile/orientation rules.
    if exported_srgb is not None:
        if (not isinstance(exported_srgb, Image.Image) or exported_srgb.mode != "RGB"
                or exported_srgb.size != source.size or set(exported_srgb.info) - {"srgb"}
                or exported_srgb.info.get("srgb", 1) != 1):
            raise ValueError("Colour QA requires aligned, metadata-safe declared sRGB output")
    engine = None
    try:
        engine = _Transforms(source.info.get("icc_profile"))
        return _measure(source, exported_srgb, tile_pixels, engine)
    except (OSError, AttributeError, TypeError, ValueError, OverflowError, ctypes.ArgumentError):
        # Never expose ICC bytes, private metadata or a partial successful result.
        raise ValueError("Colour QA unavailable or invalid/non-finite transform; no decision") from None
    finally:
        if engine is not None:
            engine.close()
