"""Generated ICC v2 qualification. Never reads dataset files or source ICCs."""
import builtins
from copy import deepcopy
from hashlib import sha256
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageCms
import pytest

from src.vision import colour_b1_iccv2_generated as v2
from src.vision import colour_b1_prototype as b1
from src.vision import colour_qa as qa


# Independent fixtures: derive RGB matrices from xy primaries and tabulated
# whites, not from the extension's parser/constants or any source ICC payload.
WHITE = {"D50": np.array([.9642, 1., .8249]),
         "D65": np.array([.95047, 1., 1.08883]),
         "D65_xy": np.array([.3127/.329, 1., (1-.3127-.329)/.329])}


def cat(white):
    cone = np.array([[.8951, .2664, -.1614], [-.7502, 1.7135, .0367],
                     [.0389, -.0685, 1.0296]])
    return np.linalg.inv(cone) @ np.diag((cone @ WHITE["D50"]) / (cone @ white)) @ cone


def make_profile(gamma=2.2, wide=True, white="D65", fault=None):
    primaries = [( .64, .33), (.21, .71) if wide else (.30, .60), (.15, .06)]
    columns = np.array([[x/y, 1., (1-x-y)/y] for x, y in primaries]).T
    media_white = WHITE[white]
    native = columns @ np.diag(np.linalg.solve(columns, media_white))
    matrix = cat(media_white) @ native
    if fault == "unadapted":
        matrix = native
    elif fault == "double_adapted":
        matrix = cat(media_white) @ matrix
    elif fault == "singular":
        matrix[:, 1] = matrix[:, 0]
    matrix = np.rint(matrix*65536) / 65536

    def xyz(value):
        return b"XYZ " + bytes(4) + struct.pack(">3i", *np.rint(value*65536).astype(int))

    curve = b"curv" + bytes(4) + struct.pack(">IH", 1, round(gamma*256))
    if fault == "ambiguous_white":
        media_white = np.array([1., 1., 1.])
    description = b"Generated qualification only\0"
    desc = (b"desc" + bytes(4) + struct.pack(">I", len(description)) + description
            + bytes(8) + bytes(2) + bytes(1) + bytes(67))
    tags = {b"desc": desc, b"cprt": b"text" + bytes(4) + b"Generated fixture\0",
            b"wtpt": xyz(media_white)}
    for channel, name in enumerate((b"rXYZ", b"gXYZ", b"bXYZ")):
        tags[name] = xyz(matrix[:, channel])
    for name in (b"rTRC", b"gTRC", b"bTRC"):
        tags[name] = curve
    if fault == "chad":
        tags[b"chad"] = b"sf32" + bytes(4) + struct.pack(">9i", *np.rint(cat(media_white)*65536).astype(int).flat)
    if fault == "lut":
        tags[b"A2B0"] = b"mft2" + bytes(8)
    header = bytearray(128)
    header[4:8] = b"TEST"
    header[8:12] = bytes([2, 0x10, 0, 0])
    header[12:24] = b"mntrRGB XYZ "
    header[24:36] = struct.pack(">6H", 2026, 1, 1, 0, 0, 0)
    header[36:40] = b"acsp"
    header[64:68] = (1).to_bytes(4, "big")
    header[68:80] = struct.pack(">3i", *np.rint(WHITE["D50"]*65536).astype(int))
    table = bytearray(struct.pack(">I", len(tags)))
    data = bytearray()
    offset = 132 + 12*len(tags)
    for name, tag in tags.items():
        table.extend(struct.pack(">4sII", name, offset + len(data), len(tag)))
        data.extend(tag)
        data.extend(bytes((-len(data)) % 4))
    raw = header + table + data
    raw[:4] = len(raw).to_bytes(4, "big")
    return bytes(raw), matrix, round(gamma*256)/256


def pixels():
    # All corners, neutral shadows and deterministic saturated/interior colours.
    corners = np.array([[r, g, b] for r in (0, 255) for g in (0, 255)
                        for b in (0, 255)], dtype=np.uint8)
    shadows = np.repeat(np.arange(32, dtype=np.uint8)[:, None], 3, axis=1)
    random = np.random.default_rng(42).integers(0, 256, (216, 3), dtype=np.uint8)
    return np.vstack([corners, shadows, random]).reshape(16, 16, 3)


def scalar_reference(rgb, matrix, gamma):
    # Scalar dot-products and independent LCMS target colourants. The source
    # matrix/gamma come from fixture construction, never the tested parser.
    target = ImageCms.createProfile("sRGB")
    srgb = np.column_stack([getattr(target, name)[0]
                            for name in ("red_colorant", "green_colorant", "blue_colorant")])
    expected_xyz, expected_rgb = [], []
    for pixel in rgb.reshape(-1, 3):
        linear = [(int(code)/255)**gamma for code in pixel]
        xyz = [math.fsum(float(matrix[i, j])*linear[j] for j in range(3)) for i in range(3)]
        components = np.linalg.solve(srgb, xyz)
        encoded = []
        for value in components:
            a = abs(value)
            result = 12.92*a if a <= .0031308 else 1.055*a**(1/2.4)-.055
            encoded.append(math.copysign(result, value))
        expected_xyz.append(xyz)
        expected_rgb.append(encoded)
    return np.array(expected_xyz).reshape(rgb.shape), np.array(expected_rgb).reshape(rgb.shape)


def independent_lab(xyz):
    result = []
    d = 6/29
    for sample in xyz.reshape(-1, 3):
        f = []
        for v, w in zip(sample, (.9642, 1., .8249)):
            t = float(v/w)
            f.append(t**(1/3) if t > d**3 else t/(3*d*d)+4/29)
        result.append([116*f[1]-16, 500*(f[0]-f[1]), 200*(f[1]-f[2])])
    return np.array(result).reshape(xyz.shape)


def measure_case(gamma, wide, white):
    profile, matrix, quantized_gamma = make_profile(gamma, wide, white)
    rgb = pixels()
    xyz, encoded = v2.interpret_generated(rgb, profile)
    ref_xyz, ref_rgb = scalar_reference(rgb, matrix, quantized_gamma)
    canonical, evidence = v2.convert_generated(rgb, profile)
    engine = qa._Transforms(profile)
    try:
        cms_lab = engine.run(engine.source_lab, rgb, np.float64)
    finally:
        engine.close()
    return {"gamma": quantized_gamma, "wide": wide, "white": white,
            "xyz_reference_abs": float(np.abs(xyz-ref_xyz).max()),
            "rgb_reference_abs": float(np.abs(encoded-ref_rgb).max()),
            "lcms_lab_delta_e76": float(np.linalg.norm(cms_lab-independent_lab(ref_xyz), axis=-1).max()),
            "float32_xyz_abs": evidence["xyz_max_abs"],
            "float32_lab_delta_e76": evidence["lab_max_delta_e76"],
            "minimum": float(canonical.min()), "maximum": float(canonical.max())}


@pytest.mark.parametrize("white", ["D50", "D65", "D65_xy"])
@pytest.mark.parametrize("wide", [False, True])
@pytest.mark.parametrize("gamma", [1., 2.2, 3.])
def test_independent_matrix_trc_and_littlecms_lab(gamma, wide, white):
    result = measure_case(gamma, wide, white)
    assert result["xyz_reference_abs"] <= 1e-12
    assert result["rgb_reference_abs"] <= 1e-10
    assert result["lcms_lab_delta_e76"] <= .01
    assert result["float32_xyz_abs"] <= 2e-6
    assert result["float32_lab_delta_e76"] <= .002


def test_d65_adaptation_is_not_identity_and_is_not_applied_twice():
    profile, matrix, _ = make_profile()
    parsed = v2.read_generated_profile(profile)
    assert not np.allclose(parsed.inferred_adaptation, np.eye(3), atol=.01)
    np.testing.assert_allclose(parsed.inferred_adaptation @ parsed.media_white,
                               WHITE["D50"], atol=1e-14)
    np.testing.assert_array_equal(parsed.matrix, matrix)
    white_xyz = v2.interpret_generated(np.full((1, 1, 3), 255, np.uint8), profile)[0][0, 0]
    np.testing.assert_allclose(white_xyz, WHITE["D50"], atol=3/65536, rtol=0)
    twice = parsed.inferred_adaptation @ matrix @ np.ones(3)
    assert np.max(np.abs(twice-white_xyz)) > .1


@pytest.mark.parametrize("fault", ["unadapted", "double_adapted", "singular", "ambiguous_white", "chad", "lut"])
def test_wrong_adaptation_and_unsupported_families_rejected(fault):
    with pytest.raises(ValueError):
        v2.convert_generated(pixels(), make_profile(fault=fault)[0])


def find_tag(raw, name):
    for i in range(int.from_bytes(raw[128:132], "big")):
        row = 132+12*i
        if raw[row:row+4] == name:
            return row, int.from_bytes(raw[row+4:row+8], "big")
    raise AssertionError("Missing fixture tag")


@pytest.mark.parametrize("fault", ["empty", "size", "version", "class", "space", "pcs", "signature",
                                    "illuminant", "intent", "count", "duplicate", "unaligned",
                                    "outside", "overlap", "missing", "curve_kind", "curve_count",
                                    "gamma_zero", "gamma_large", "xyz_type", "metadata_type"])
def test_malformed_icc_fails_closed(fault):
    raw = bytearray(make_profile()[0])
    row, offset = find_tag(raw, b"rTRC")
    if fault == "empty": raw = bytearray()
    elif fault == "size": raw[:4] = (len(raw)+1).to_bytes(4, "big")
    elif fault == "version": raw[8] = 4
    elif fault == "class": raw[12:16] = b"scnr"
    elif fault == "space": raw[16:20] = b"CMYK"
    elif fault == "pcs": raw[20:24] = b"Lab "
    elif fault == "signature": raw[36:40] = b"nope"
    elif fault == "illuminant": raw[68:80] = bytes(12)
    elif fault == "intent": raw[64:68] = (4).to_bytes(4, "big")
    elif fault == "count": raw[128:132] = (33).to_bytes(4, "big")
    elif fault == "duplicate": raw[row:row+4] = b"gTRC"
    elif fault == "unaligned": raw[row+4:row+8] = (offset+1).to_bytes(4, "big")
    elif fault == "outside": raw[row+4:row+8] = (len(raw)+4).to_bytes(4, "big")
    elif fault == "overlap": raw[row+8:row+12] = (18).to_bytes(4, "big")
    elif fault == "missing": raw[row:row+4] = b"cXYZ"
    elif fault == "curve_kind": raw[offset:offset+4] = b"para"
    elif fault == "curve_count": raw[offset+8:offset+12] = bytes(4)
    elif fault == "gamma_zero": raw[offset+12:offset+14] = bytes(2)
    elif fault == "gamma_large": raw[offset+12:offset+14] = (6*256).to_bytes(2, "big")
    elif fault == "xyz_type":
        _, xyz_offset = find_tag(raw, b"wtpt")
        raw[xyz_offset:xyz_offset+4] = b"sf32"
    elif fault == "metadata_type":
        _, desc_offset = find_tag(raw, b"desc")
        raw[desc_offset:desc_offset+4] = b"mluc"
    with pytest.raises(ValueError):
        v2.read_generated_profile(bytes(raw))


@pytest.mark.parametrize("bad", [None, "data/not_allowed.jpg", np.zeros((2, 2, 3)),
                                np.full((2, 2, 3), np.nan), np.full((2, 2, 3), np.inf),
                                np.zeros((257, 1, 3), np.uint8), np.zeros((2, 2), np.uint8)])
def test_invalid_nonfinite_or_path_pixels_rejected(bad):
    with pytest.raises(ValueError):
        v2.convert_generated(bad, make_profile()[0])


def test_unclipped_values_survive_storage_loading_and_normalization():
    rgb, profile = pixels(), make_profile()[0]
    canonical, _ = v2.convert_generated(rgb, profile)
    assert canonical.min() < -.1 and canonical.max() > 1.01
    payload, receipt, _ = v2.build_generated_payload(rgb, profile)
    loaded = v2.load_generated_payload(payload, receipt, b1.digest_json(receipt))
    expected, _ = b1.letterbox(canonical)
    np.testing.assert_array_equal(loaded, expected)
    normalized = b1.normalize(loaded)
    restored = normalized.transpose(1, 2, 0)*b1.models.STD+b1.models.MEAN
    np.testing.assert_allclose(restored, loaded, atol=3e-7)
    assert loaded.min() < 0 and loaded.max() > 1
    assert restored.min() < 0 and restored.max() > 1
    assert not loaded.flags.writeable
    assert profile not in payload and b"icc_profile" not in payload and b"EXIF" not in payload


def test_storage_is_deterministic_and_original_generated_bytes_unchanged():
    rgb, profile = pixels(), make_profile()[0]
    before = sha256(rgb.tobytes()).hexdigest(), sha256(profile).hexdigest()
    assert v2.build_generated_payload(rgb, profile) == v2.build_generated_payload(rgb, profile)
    assert before == (sha256(rgb.tobytes()).hexdigest(), sha256(profile).hexdigest())


@pytest.mark.parametrize("fault", ["payload", "contract", "version", "metadata", "inner", "trust"])
def test_versioned_receipts_and_tampering_rejected(fault):
    payload, receipt, _ = v2.build_generated_payload(pixels(), make_profile()[0])
    trusted = b1.digest_json(receipt)
    if fault == "payload": payload += b"extra"
    elif fault == "contract": receipt["contract_sha256"] = "0"*64
    elif fault == "version": receipt["version"] = b1.VERSION
    elif fault == "metadata": receipt["ICC"] = "forbidden"
    elif fault == "inner": receipt["storage_receipt"]["EXIF"] = "forbidden"
    else: trusted = "0"*64
    if fault not in ("payload", "trust"):
        trusted = b1.digest_json(receipt)
    with pytest.raises(ValueError):
        v2.load_generated_payload(payload, receipt, trusted)


def test_unmodified_old_profile_reader_still_rejects_v2_no_automatic_dispatch():
    with pytest.raises(ValueError):
        b1.convert_generated(pixels(), make_profile()[0])
    from src.vision.gamut_mapping_feasibility import _generated_profile
    generated_v4, _ = _generated_profile(2.2, 0)
    with pytest.raises(ValueError):
        v2.convert_generated(pixels(), generated_v4)


def test_generated_path_performs_no_file_image_or_packaging_io(monkeypatch):
    from src.vision import exploratory_bundle as legacy
    from src.vision import exploratory_bundle_v4 as option_a
    from src.vision import exploratory_bundle_b1 as bundle
    rgb, profile = pixels(), make_profile()[0]
    def forbidden(*args, **kwargs):
        pytest.fail("Generated extension attempted filesystem/image/production IO")
    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Image, "open", forbidden)
    monkeypatch.setattr(Image.Image, "save", forbidden)
    monkeypatch.setattr(legacy, "package_development", forbidden)
    monkeypatch.setattr(option_a, "package_development", forbidden)
    for name in dir(bundle):
        if name.startswith("package") and callable(getattr(bundle, name)):
            monkeypatch.setattr(bundle, name, forbidden)
    payload, receipt, _ = v2.build_generated_payload(rgb, profile)
    assert v2.load_generated_payload(payload, receipt, b1.digest_json(receipt)).shape == (224, 224, 3)


def test_nonfinite_transform_failure_is_not_encoded(monkeypatch):
    def nonfinite(values):
        return np.full_like(values, np.nan)
    monkeypatch.setattr(b1, "encode_extended", nonfinite)
    with pytest.raises(ValueError):
        v2.convert_generated(pixels(), make_profile()[0])


def test_existing_option_a_specs_and_training_gates_not_changed():
    from src.vision import exploratory_bundle as old
    from src.vision import exploratory_bundle_v4 as option_a
    from src.vision import model_pipeline as models
    before = deepcopy(option_a.policy_spec()), b1.contract_hash()
    assert old.ROUNDTRIP_LIMIT == 2
    v2.build_generated_payload(pixels(), make_profile()[0])
    assert before == (option_a.policy_spec(), b1.contract_hash())
    assert not v2.CONTRACT["production_active"]
    with pytest.raises(ValueError):
        models.approved_training_records({"status": v2.CONTRACT["scope"]})
