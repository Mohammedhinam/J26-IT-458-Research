"""Generated profiles/pixels only; analytic references are not clinical bounds."""
from copy import deepcopy
from io import BytesIO
import json
import math
import struct

import numpy as np
from PIL import Image, ImageCms
import pytest

from src.vision import colour_qa as qa
from src.vision import exploratory_bundle as export


def profile_fixture(gamma=2.2, wide=False):
    """Generate a pure-power TRC profile, optionally widen red/green primaries.

    Return its explicitly encoded XYZ matrix for independent NumPy references.
    No camera profile, patient pixels or real source metadata is used.
    """
    raw = bytearray(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    tags = {}
    for index in range(int.from_bytes(raw[128:132], "big")):
        start = 132 + index * 12
        name = bytes(raw[start:start + 4])
        offset = int.from_bytes(raw[start + 4:start + 8], "big")
        tags[name] = offset
        if name in (b"rTRC", b"gTRC", b"bTRC"):
            # ICC parametric type 0 is exactly Y = X**gamma.
            raw[start + 8:start + 12] = (16).to_bytes(4, "big")
            raw[offset:offset + 16] = b"para" + bytes(8) + struct.pack(">i", round(gamma * 65536))
    matrix = np.column_stack([np.array(struct.unpack(">3i", raw[tags[t] + 8:tags[t] + 20])) / 65536
                              for t in (b"rXYZ", b"gXYZ", b"bXYZ")])
    if wide:
        # Extend red/green while retaining positive XYZ primaries and white.
        matrix = matrix @ np.array([[1.1, -.1, 0], [-.1, 1.1, 0], [0, 0, 1]])
        matrix = np.rint(matrix * 65536) / 65536
        for column, tag in enumerate((b"rXYZ", b"gXYZ", b"bXYZ")):
            raw[tags[tag] + 8:tags[tag] + 20] = struct.pack(">3i", *np.rint(matrix[:, column] * 65536).astype(int))
    return bytes(raw), matrix, round(gamma * 65536) / 65536


def source_fixture(values, gamma=2.2, wide=False):
    raw, matrix, exponent = profile_fixture(gamma, wide)
    image = Image.fromarray(np.asarray(values, dtype=np.uint8).reshape(-1, 3)[None, ...])
    image.info["icc_profile"] = raw
    return image, matrix, exponent


def srgb_matrix():
    # sRGB D50 profile colourants, read independently of the diagnostic engine.
    _, matrix, _ = profile_fixture(1)
    return matrix


def xyz_to_lab(xyz):
    ratio = xyz / np.array([.9642, 1, .8249])
    delta = 6 / 29
    f = np.where(ratio > delta ** 3, np.cbrt(ratio), ratio / (3 * delta ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], axis=-1)


def analytic_lab_distance(source, output, matrix, gamma):
    original = np.asarray(source).astype(float) / 255
    current = np.asarray(output).astype(float) / 255
    linear_srgb = np.where(current <= .04045, current / 12.92, ((current + .055) / 1.055) ** 2.4)
    left = xyz_to_lab((original ** gamma) @ matrix.T)
    right = xyz_to_lab(linear_srgb @ srgb_matrix().T)
    return np.linalg.norm(left - right, axis=-1)


def pillow_reference(source):
    converted = ImageCms.profileToProfile(source, ImageCms.ImageCmsProfile(BytesIO(source.info["icc_profile"])),
                                         ImageCms.createProfile("sRGB"), outputMode="RGB", renderingIntent=1, flags=0)
    # Mimic a metadata-safe supplied derivative, not ImageCms' attached profile.
    clean = Image.frombytes("RGB", converted.size, converted.tobytes())
    clean.info["srgb"] = 1
    return clean


@pytest.mark.parametrize("tagged", [False, True])
def test_identity_and_source_immutability(tagged):
    image = Image.new("RGB", (11, 7), (80, 120, 160))
    if tagged:
        image.info["icc_profile"] = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    image.info["comment"] = b"synthetic private metadata"
    before = image.tobytes(), deepcopy(image.info)
    result = qa.diagnose_forward_colour(image, tile_pixels=13)
    assert result["pixels"] == 77 and result["diagnostic_only"]
    assert result["acceptance_decision"] == "not_evaluated"
    assert result["reverse_rgb"]["per_pixel_max"]["max"] == 0
    assert result["forward_delta_e76_D50"]["max"] < .01
    assert result["gamut"]["pixels_outside"] == 0
    assert (image.tobytes(), image.info) == before
    assert "synthetic private" not in json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("gamma", [1.0, 1.8, 2.2])
def test_forward_lab_agrees_with_independent_matrix_trc_reference(gamma):
    source, matrix, exponent = source_fixture([[40, 80, 140], [90, 120, 160], [200, 110, 70]], gamma)
    output = pillow_reference(source)
    expected = analytic_lab_distance(source, output, matrix, exponent)
    result = qa.diagnose_forward_colour(source, output, tile_pixels=2)
    # .01 covers LCMS versus analytic matrix/TRC precision for THESE fixtures.
    # It is not an image acceptance policy or clinical delta-E tolerance.
    assert result["forward_delta_e76_D50"]["mean"] == pytest.approx(expected.mean(), abs=.01)
    assert result["forward_delta_e76_D50"]["max"] == pytest.approx(expected.max(), abs=.01)
    assert result["output_mode"] == "measured_supplied_srgb"
    # C packed RGB and Pillow's RGBX path must agree with the SAME generated sRGB.
    simulated = qa.diagnose_forward_colour(source, tile_pixels=2)
    assert simulated["forward_delta_e76_D50"] == result["forward_delta_e76_D50"]
    assert simulated["reverse_rgb"] == result["reverse_rgb"]


def test_reverse_statistics_match_full_pillow_reference():
    source, _, _ = source_fixture([[i, i, i] for i in range(32)])
    output = pillow_reference(source)
    restored = ImageCms.profileToProfile(output, ImageCms.createProfile("sRGB"),
                                         ImageCms.ImageCmsProfile(BytesIO(source.info["icc_profile"])),
                                         outputMode="RGB", renderingIntent=1, flags=0)
    difference = np.abs(np.asarray(restored).astype(np.int16) - np.asarray(source).astype(np.int16))
    result = qa.diagnose_forward_colour(source, tile_pixels=5)
    for index, name in enumerate(("R", "G", "B")):
        stats = result["reverse_rgb"]["channels"][name]
        assert stats["max"] == int(difference[..., index].max())
        assert stats["mean"] == pytest.approx(difference[..., index].mean())
        assert stats["count_gt_current_limit"] == int((difference[..., index] > 2).sum())
    assert result["reverse_rgb"]["per_pixel_max"]["max"] > 2
    assert result["forward_delta_e76_D50"]["max"] < 1  # Fixture property only.


def test_synthetic_shadow_diagnostics_do_not_bypass_existing_production_guard(tmp_path):
    source, _, _ = source_fixture([[i, i, i] for i in range(32)])
    result = qa.diagnose_forward_colour(source)
    assert result["reverse_rgb"]["current_limit"] == export.ROUNDTRIP_LIMIT == 2
    with pytest.raises(ValueError, match="round-trip"):
        export.export_rgb_png(source, tmp_path / "must-not-exist.png")
    assert not (tmp_path / "must-not-exist.png").exists()


def test_gamut_clipping_has_independent_linear_matrix_reference():
    source, matrix, gamma = source_fixture([[255, 0, 0], [0, 255, 0], [128, 128, 128]], gamma=1, wide=True)
    linear = ((np.asarray(source) / 255) ** gamma) @ matrix.T @ np.linalg.inv(srgb_matrix()).T
    # Extended sRGB's negative branch uses its linear toe, not fractional powers.
    expected = np.empty_like(linear)
    low = linear <= .0031308
    expected[low] = 12.92 * linear[low]
    expected[~low] = 1.055 * linear[~low] ** (1 / 2.4) - .055
    excursion = np.maximum(-expected, 0) + np.maximum(expected - 1, 0)
    count = int((excursion > qa.GAMUT_EPSILON).any(axis=2).sum())
    result = qa.diagnose_forward_colour(source, tile_pixels=1)
    assert count == result["gamut"]["pixels_outside"] == 2
    assert result["gamut"]["max_excursion_normalized"] == pytest.approx(excursion.max(), abs=.002)
    assert result["gamut"]["pixels_below"] == 2 and result["gamut"]["pixels_above"] == 2
    assert result["forward_delta_e76_D50"]["max"] > 1  # No acceptance implied.


@pytest.mark.parametrize("mistake", ["discarded_icc", "incorrect_profile"])
def test_wrong_colour_interpretation_is_measured_not_automatically_approved(mistake):
    source, matrix, gamma = source_fixture([[64, 80, 96], [80, 120, 180]], gamma=1)
    correct = qa.diagnose_forward_colour(source)
    if mistake == "discarded_icc":
        wrong = Image.fromarray(np.asarray(source))  # ICC discarded without conversion.
    else:
        incorrect = source.copy()
        incorrect.info["icc_profile"] = profile_fixture(2.2)[0]
        wrong = pillow_reference(incorrect)  # Generated wrong-profile conversion.
    result = qa.diagnose_forward_colour(source, wrong)
    expected = analytic_lab_distance(source, wrong, matrix, gamma)
    assert result["forward_delta_e76_D50"]["mean"] == pytest.approx(expected.mean(), abs=.01)
    assert result["forward_delta_e76_D50"]["mean"] > correct["forward_delta_e76_D50"]["mean"] + 10
    assert result["acceptance_decision"] == "not_evaluated"


def test_tile_independence_reproducibility_and_bounded_transform_buffers(monkeypatch):
    rng = np.random.default_rng(42)
    source = Image.fromarray(rng.integers(10, 220, (5, 137, 3), dtype=np.uint8))
    source.info["icc_profile"] = profile_fixture()[0]
    original = qa._Transforms.run
    seen = []
    def bounded(self, handle, values, dtype):
        seen.append(values.size // 3)
        assert values.size // 3 <= 31
        return original(self, handle, values, dtype)
    monkeypatch.setattr(qa._Transforms, "run", bounded)
    first = qa.diagnose_forward_colour(source, tile_pixels=31)
    assert max(seen) <= 31 and first == qa.diagnose_forward_colour(source, tile_pixels=31)
    monkeypatch.setattr(qa._Transforms, "run", original)
    second = qa.diagnose_forward_colour(source, tile_pixels=512)
    assert first["reverse_rgb"] == second["reverse_rgb"] and first["gamut"] == pytest.approx(second["gamut"])
    assert first["forward_delta_e76_D50"]["mean"] == pytest.approx(second["forward_delta_e76_D50"]["mean"], abs=1e-12)
    assert first["forward_delta_e76_D50"]["percentile_bounds"] == second["forward_delta_e76_D50"]["percentile_bounds"]


def test_fixed_memory_histogram_reports_honest_percentile_bounds_and_overflow():
    values = np.array([0, .0001, .5, 1.2345, 900.0])
    distribution = qa._Distribution()
    distribution.add(values)
    result = distribution.result()
    assert distribution.histogram.nbytes == 512001 * 8
    assert result["overflow_count_ge_512"] == 1
    for q, (lower, upper) in result["percentile_bounds"].items():
        expected = sorted(values)[math.ceil(len(values) * float(q) / 100) - 1]
        assert lower <= expected <= upper


def test_helper_does_not_save_or_package_and_preserves_generated_file_hash(tmp_path, monkeypatch):
    path = tmp_path / "generated.png"
    source, _, _ = source_fixture([[80, 120, 160]], gamma=1.8)
    source.save(path, icc_profile=source.info["icc_profile"])
    before = path.read_bytes()
    def forbidden(*args, **kwargs):
        pytest.fail("diagnostic attempted to write/package")
    monkeypatch.setattr(Image.Image, "save", forbidden)
    monkeypatch.setattr(export, "export_rgb_png", forbidden)
    monkeypatch.setattr(export, "package_development", forbidden)
    with Image.open(path) as opened:
        result = qa.diagnose_forward_colour(opened)
    assert path.read_bytes() == before and list(tmp_path.iterdir()) == [path]
    assert result["acceptance_decision"] == "not_evaluated"


@pytest.mark.parametrize("profile", [b"", b"broken", ImageCms.ImageCmsProfile(ImageCms.createProfile("LAB")).tobytes()])
def test_malformed_or_non_rgb_profile_fails_closed(profile):
    source = Image.new("RGB", (2, 2))
    source.info["icc_profile"] = profile
    with pytest.raises(ValueError):
        qa.diagnose_forward_colour(source)


@pytest.mark.parametrize("kind", [b"prtr", b"link", b"abst"])
def test_unsupported_profile_class_is_rejected(kind):
    raw = bytearray(profile_fixture()[0]); raw[12:16] = kind
    source = Image.new("RGB", (1, 1)); source.info["icc_profile"] = bytes(raw)
    with pytest.raises(ValueError):
        qa.diagnose_forward_colour(source)


@pytest.mark.parametrize("case", ["size", "mode", "icc", "opaque", "intent"])
def test_supplied_output_cannot_be_misaligned_or_ambiguous(case):
    source = Image.new("RGB", (2, 2))
    output = source.copy()
    if case == "size": output = Image.new("RGB", (3, 2))
    elif case == "mode": output = output.convert("L")
    elif case == "icc": output.info["icc_profile"] = b"wrong profile"
    elif case == "opaque": output.info["comment"] = b"private metadata"
    else: output.info["srgb"] = 0
    with pytest.raises(ValueError):
        qa.diagnose_forward_colour(source, output)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, qa.MAX_TILE_PIXELS + 1])
def test_invalid_tile_limit_rejected(limit):
    with pytest.raises(ValueError):
        qa.diagnose_forward_colour(Image.new("RGB", (1, 1)), tile_pixels=limit)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("target", ["source_lab", "output_lab", "extended_srgb"])
def test_nonfinite_transform_fails_and_releases_handles(monkeypatch, value, target):
    original = qa._Transforms.run
    captured = []
    def invalid(self, handle, pixels, dtype):
        captured.append(self)
        output = original(self, handle, pixels, dtype)
        if handle == getattr(self, target): output.flat[0] = value
        return output
    monkeypatch.setattr(qa._Transforms, "run", invalid)
    with pytest.raises(ValueError, match="no decision"):
        qa.diagnose_forward_colour(Image.new("RGB", (2, 2)))
    assert captured and not captured[-1].transforms and not captured[-1].profiles


def test_unavailable_cms_has_no_fallback_and_hides_exception_details(monkeypatch):
    def unavailable(*args):
        raise OSError("synthetic private diagnostic marker")
    monkeypatch.setattr(qa.ctypes, "CDLL", unavailable)
    with pytest.raises(ValueError, match="no decision") as error:
        qa.diagnose_forward_colour(Image.new("RGB", (1, 1)))
    assert "private" not in str(error.value) and error.value.__suppress_context__


def test_partial_transform_initialisation_releases_existing_handles(monkeypatch):
    original = qa._Transforms._new
    captured = []
    def fail_second(self, *args):
        captured.append(self)
        if len(captured) == 2: raise ValueError("generated transform setup failure")
        return original(self, *args)
    monkeypatch.setattr(qa._Transforms, "_new", fail_second)
    with pytest.raises(ValueError, match="no decision"):
        qa.diagnose_forward_colour(Image.new("RGB", (1, 1)))
    assert not captured[0].transforms and not captured[0].profiles
