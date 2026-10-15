"""Generated-only B1 qualification: no dental paths, training or downloads."""
import builtins
from copy import deepcopy
from hashlib import sha256
import io
import math
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageCms
import pytest

from src.vision import colour_b1_prototype as b1
from src.vision import colour_qa as qa
from src.vision import gamut_mapping_feasibility as study
from src.vision import model_pipeline as models


def fixture(gamma=2.2, strength=2**-6):
    profile, matrix = study._generated_profile(gamma, strength)
    pixels = np.array([[[255, 0, 0], [0, 0, 255], [224, 48, 0], [0, 48, 224]],
                       [[0, 0, 0], [255, 255, 255], [1, 7, 10], [127, 128, 129]]], dtype=np.uint8)
    return pixels, profile, matrix


def tag_offset(raw, target):
    for index in range(int.from_bytes(raw[128:132], "big")):
        start = 132 + index * 12
        if raw[start:start + 4] == target:
            return start, int.from_bytes(raw[start + 4:start + 8], "big")
    raise AssertionError("Fixture tag missing")


def scalar_reference(pixels, matrix, gamma):
    # Independent scalar equations, generated-fixture matrix, LCMS canonical
    # colourants: no B1 parser, transfer helpers or canonical matrix used here.
    canonical = ImageCms.createProfile("sRGB")
    target = np.column_stack([getattr(canonical, key)[0]
                              for key in ("red_colorant", "green_colorant", "blue_colorant")])
    result = []
    for pixel in pixels.reshape(-1, 3):
        linear = []
        for code in pixel:
            value = int(code) / 255
            if gamma is None:
                g, a, bb, c, d = [round(x * 65536) / 65536
                                  for x in (2.4, 1 / 1.055, .055 / 1.055, 1 / 12.92, .04045)]
                decoded = (a * value + bb)**g if value >= d else c * value
            else:
                decoded = value ** (round(gamma * 65536) / 65536)
            linear.append(decoded)
        xyz = [math.fsum(float(matrix[row, col]) * linear[col] for col in range(3))
               for row in range(3)]
        target_linear = np.linalg.solve(target, xyz)
        encoded = []
        for value in target_linear:
            absolute = abs(value)
            e = 12.92 * absolute if absolute <= .0031308 else 1.055 * absolute**(1 / 2.4) - .055
            encoded.append(math.copysign(e, value))
        result.append(encoded)
    return np.array(result).reshape(pixels.shape)


@pytest.mark.parametrize("gamma", [None, 1., 1.8, 2.2, 3.])
@pytest.mark.parametrize("strength", [0, 2**-6])
def test_conversion_matches_independent_scalar_matrix_trc_and_lcms_lab(gamma, strength):
    pixels, profile, matrix = fixture(gamma, strength)
    before = pixels.tobytes(), sha256(profile).hexdigest()
    actual, evidence = b1.convert_generated(pixels, profile)
    expected = scalar_reference(pixels, matrix, gamma)
    np.testing.assert_allclose(b1._interpret_generated(pixels, profile)[1], expected,
                               atol=1e-10, rtol=0)
    rounded = expected.astype("<f4")
    # Half-ULP storage budget is evaluated against independent float64 values.
    step = np.maximum(np.abs(np.nextafter(rounded, np.float32(np.inf)) - rounded),
                      np.abs(np.nextafter(rounded, np.float32(-np.inf)) - rounded)).astype(float)
    assert np.all(np.abs(actual.astype(float) - expected) <= step / 2 + 1e-14)
    np.testing.assert_allclose(actual, rounded, atol=1e-10, rtol=0)
    assert evidence["xyz_max_abs"] <= 2e-6 and evidence["lab_max_delta_e76"] <= .002
    engine = qa._Transforms(profile)
    try:
        source_lab = engine.run(engine.source_lab, pixels, np.float64)
    finally:
        engine.close()
    # The independent CMS check validates source ICC interpretation in Lab;
    # CMS RGB8 output is not a reference for unbounded canonical RGB.
    source_linear = np.empty_like(pixels, dtype=float)
    for channel in range(3):
        x = pixels[..., channel].astype(float) / 255
        if gamma is None:
            g, a, bb, c, d = [round(v * 65536) / 65536
                              for v in (2.4, 1 / 1.055, .055 / 1.055, 1 / 12.92, .04045)]
            source_linear[..., channel] = np.where(x >= d, (a*x + bb)**g, c*x)
        else:
            source_linear[..., channel] = x**(round(gamma * 65536) / 65536)
    xyz = source_linear @ matrix.T
    ratio = xyz / np.array([.9642, 1, .8249])
    d = 6 / 29
    f = np.where(ratio > d**3, np.cbrt(ratio), ratio / (3*d*d) + 4/29)
    reference_lab = np.stack([116*f[..., 1]-16, 500*(f[..., 0]-f[..., 1]),
                              200*(f[..., 1]-f[..., 2])], axis=-1)
    assert np.linalg.norm(source_lab - reference_lab, axis=2).max() <= .01
    assert (pixels.tobytes(), sha256(profile).hexdigest()) == before


def test_negative_red_blue_and_above_one_survive_every_model_stage():
    pixels, profile, _ = fixture()
    canonical, _ = b1.convert_generated(pixels, profile)
    assert canonical[0, 0, 2] < 0 and canonical[0, 1, 0] < 0
    assert canonical[0, 0, 0] > 1 and canonical[0, 1, 2] > 1
    payload, receipt, _ = b1.build_generated_payload(pixels, profile)
    loaded = b1.load_generated_payload(payload, receipt, b1.digest_json(receipt))
    expected, _ = b1.letterbox(canonical)
    np.testing.assert_array_equal(loaded, expected)
    assert loaded.min() < 0 and loaded.max() > 1
    normalized = b1.normalize(loaded)
    restored = normalized.transpose(1, 2, 0) * models.STD + models.MEAN
    np.testing.assert_allclose(restored, loaded, atol=2e-7)
    assert restored.min() < 0 and restored.max() > 1
    assert not loaded.flags.writeable


def test_explicit_transfer_inverse_and_odd_extension():
    linear = np.array([-4., -1., -.1, -.0031308, -1e-8, 0., .0031308, .1, 1., 4.])
    encoded = b1.encode_extended(linear)
    np.testing.assert_allclose(b1.decode_extended(encoded), linear, atol=5e-9, rtol=0)
    np.testing.assert_array_equal(b1.encode_extended(-linear), -encoded)
    assert encoded[0] < -1 and encoded[-1] > 1


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nonfinite_transform_and_array_rejected(bad):
    with pytest.raises(ValueError):
        b1.encode_extended(np.array([bad]))
    with pytest.raises(ValueError):
        b1.decode_extended(np.array([bad]))
    values = np.zeros((224, 224, 3), dtype="<f4")
    values[0, 0, 0] = bad
    with pytest.raises(ValueError):
        b1.normalize(values)


@pytest.mark.parametrize("problem", ["empty", "signature", "version", "class", "rgb", "pcs",
                                    "size", "table", "offset", "overlap", "duplicate_tag",
                                    "lut", "missing_trc", "curve", "gamma", "matrix", "white", "chad"])
def test_unsupported_or_malformed_profiles_fail_closed(problem):
    pixels, profile, _ = fixture()
    raw = bytearray(profile)
    if problem == "empty":raw = bytearray()
    elif problem == "signature":raw[36:40] = b"nope"
    elif problem == "version":raw[8] = 2
    elif problem == "class":raw[12:16] = b"prtr"
    elif problem == "rgb":raw[16:20] = b"GRAY"
    elif problem == "pcs":raw[20:24] = b"Lab "
    elif problem == "size":raw[:4] = (len(raw) + 1).to_bytes(4, "big")
    elif problem == "table":raw[128:132] = (100).to_bytes(4, "big")
    elif problem == "offset":raw[136:140] = (len(raw) + 4).to_bytes(4, "big")
    elif problem == "overlap":
        table, offset = tag_offset(raw, b"rXYZ")
        raw[table + 4:table + 8] = (offset + 4).to_bytes(4, "big")
    elif problem == "duplicate_tag":raw[144:148] = raw[132:136]
    elif problem == "lut":raw[132:136] = b"A2B0"
    elif problem == "missing_trc":
        table, _ = tag_offset(raw, b"rTRC")
        raw[table:table + 4] = b"xxxx"
    elif problem in ("curve", "gamma"):
        _, offset = tag_offset(raw, b"rTRC")
        if problem == "curve":raw[offset + 8:offset + 10] = (4).to_bytes(2, "big")
        else:raw[offset + 12:offset + 16] = bytes(4)
    elif problem == "matrix":
        _, offset = tag_offset(raw, b"rXYZ")
        raw[offset + 8:offset + 20] = bytes(12)
    elif problem == "white":raw[68:80] = bytes(12)
    elif problem == "chad":
        _, offset = tag_offset(raw, b"chad")
        raw[offset + 8:offset + 44] = bytes(36)
    with pytest.raises(ValueError):
        b1.convert_generated(pixels, bytes(raw))


@pytest.mark.parametrize("bad", ["data/forbidden.jpg", None, np.zeros((2, 2, 3)),
                                np.zeros((2, 2), dtype=np.uint8), np.zeros((257, 2, 3), dtype=np.uint8)])
def test_no_implicit_source_decode_or_unbounded_inputs(bad):
    with pytest.raises(ValueError):
        b1.convert_generated(bad, fixture()[1])


@pytest.mark.parametrize("shape,box", [((8, 4), [0, 56, 224, 112]),
                                      ((4, 8), [56, 0, 112, 224]),
                                      ((3, 1), [0, 74, 224, 75]),
                                      ((224, 224), [0, 0, 224, 224])])
def test_deterministic_letterbox_geometry_and_no_range_clipping(shape, box):
    width, height = shape
    original = np.broadcast_to(np.array([-.1, 1.1, .5], dtype="<f4"), (height, width, 3)).copy()
    view, actual_box = b1.letterbox(original)
    assert actual_box == box
    left, top, w, h = box
    expected = np.broadcast_to(original[0, 0], (h, w, 3))
    np.testing.assert_allclose(view[top:top + h, left:left + w], expected, atol=1e-7)
    np.testing.assert_array_equal(b1.letterbox(original)[0], view)
    if top:assert np.all(b1.normalize(view)[:, :top] == 0)
    if left:assert np.all(b1.normalize(view)[:, :, :left] == 0)


def test_half_pixel_interpolation_independent_midpoint():
    source = np.array([[[0., -.2, 1.2], [1., .2, .8]]], dtype="<f4")
    result, (left, top, width, height) = b1.letterbox(source)
    j = 100
    fraction = (j + .5) * 2 / 224 - .5
    expected = source[0, 0].astype(float) * (1-fraction) + source[0, 1].astype(float) * fraction
    np.testing.assert_allclose(result[top, j], expected, atol=3e-8)
    assert result[0, 0, 0] == models.MEAN[0]


def test_display_preview_is_separate_and_does_not_alter_canonical_input():
    pixels, profile, _ = fixture()
    canonical, _ = b1.convert_generated(pixels, profile)
    before = canonical.copy()
    preview, evidence = b1.display_preview(canonical)
    assert preview.dtype == np.uint8 and preview.shape == canonical.shape
    assert evidence["clipped_pixels"] > 0 and "may lose colour" in evidence["meaning"]
    assert preview[0, 0, 2] == 0 and preview[0, 0, 0] == 255
    np.testing.assert_array_equal(canonical, before)
    prepared = b1.prepare_generated(pixels, profile)
    assert prepared.original_rgb.shape == pixels.shape
    assert prepared.display_evidence == evidence
    cam = np.zeros((224, 224), dtype=np.float32)
    left, top, width, height = prepared.valid_box
    cam[top:top + height, left:left + width] = 1
    aligned = models.align_cam(cam, prepared)
    assert aligned.shape == pixels.shape[:2] and aligned.min() == 1
    views = models.render_gradcam(prepared.original_rgb, aligned)
    assert views["overlay"].shape == pixels.shape


@pytest.mark.parametrize("problem", ["payload_tamper", "receipt_tamper", "stale_contract", "metadata",
                                    "geometry", "wrong_profile_hash", "wrong_scope", "bad_trusted_hash"])
def test_receipt_hash_bindings_and_no_metadata(problem):
    payload, receipt, _ = b1.build_generated_payload(*fixture()[:2])
    trusted = b1.digest_json(receipt)
    if problem == "payload_tamper":payload = payload[:-1] + bytes([payload[-1] ^ 1])
    elif problem == "receipt_tamper":receipt["source_rgb_sha256"] = "0"*64
    elif problem == "stale_contract":receipt["contract_sha256"] = "0"*64;trusted = b1.digest_json(receipt)
    elif problem == "metadata":receipt["EXIF"] = "forbidden";trusted = b1.digest_json(receipt)
    elif problem == "geometry":receipt["valid_box"] = [0, 0, 224, 224];trusted = b1.digest_json(receipt)
    elif problem == "wrong_profile_hash":receipt["profile_sha256"] = "bad";trusted = b1.digest_json(receipt)
    elif problem == "wrong_scope":receipt["scope"] = "approved_real";trusted = b1.digest_json(receipt)
    else:trusted = "invalid"
    with pytest.raises(ValueError):
        b1.load_generated_payload(payload, receipt, trusted)


def altered_payload(array, *, version=(1, 0)):
    stream = io.BytesIO()
    np.lib.format.write_array(stream, array, version=version, allow_pickle=True)
    return stream.getvalue()


@pytest.mark.parametrize("problem", ["object", "float64", "big_endian", "fortran", "shape", "nonfinite",
                                    "range", "trailing", "truncated", "version", "huge_header", "bad_header",
                                    "no_newline", "unaligned_header", "structured_dtype"])
def test_hostile_npy_rejected_even_when_payload_hash_matches(problem):
    payload, receipt, _ = b1.build_generated_payload(*fixture()[:2])
    array = np.zeros((224, 224, 3), dtype="<f4")
    if problem == "object":payload = altered_payload(np.array([{"unsafe": True}], dtype=object))
    elif problem == "float64":payload = altered_payload(array.astype(float))
    elif problem == "big_endian":payload = altered_payload(array.astype(">f4"))
    elif problem == "fortran":payload = altered_payload(np.asfortranarray(array))
    elif problem == "shape":payload = altered_payload(array[:2])
    elif problem == "nonfinite":array[0, 0, 0] = np.inf;payload = altered_payload(array)
    elif problem == "range":array[0, 0, 0] = 16.01;payload = altered_payload(array)
    elif problem == "trailing":payload += b"extra"
    elif problem == "truncated":payload = payload[:-1]
    elif problem == "version":payload = altered_payload(array, version=(2, 0))
    elif problem == "huge_header":payload = payload[:8] + bytes([255, 255]) + payload[10:]
    elif problem == "bad_header":payload = payload[:10] + b"!" + payload[11:]
    elif problem == "no_newline":
        end = 10 + int.from_bytes(payload[8:10], "little")
        payload = payload[:end - 1] + b" " + payload[end:]
    elif problem == "unaligned_header":
        count = int.from_bytes(payload[8:10], "little")
        payload = payload[:8] + (count + 1).to_bytes(2, "little") + b" " + payload[10:]
    elif problem == "structured_dtype":payload = altered_payload(np.zeros((224, 224, 3), dtype=[("x", "<f4")]))
    receipt["payload_sha256"] = sha256(payload).hexdigest()
    with pytest.raises(ValueError):
        b1.load_generated_payload(payload, receipt, b1.digest_json(receipt))


def test_metadata_not_copied_and_payloads_deterministic():
    pixels, profile, _ = fixture()
    a = b1.build_generated_payload(pixels, profile)
    b = b1.build_generated_payload(pixels, profile)
    assert a == b
    assert profile not in a[0] and b"icc_profile" not in a[0] and b"EXIF" not in a[0]
    assert set(a[1]) == {"version", "scope", "contract_sha256", "payload_sha256", "source_rgb_sha256",
                         "profile_sha256", "source_size_wh", "valid_box"}
    assert b1.run_generated_smoke() == b1.run_generated_smoke()


@pytest.mark.parametrize("extra", ["'EXIF': 'forbidden', ", "'descr': '<f4', "])
def test_extra_or_duplicate_header_fields_rejected(extra):
    payload, receipt, _ = b1.build_generated_payload(*fixture()[:2])
    end = 10 + int.from_bytes(payload[8:10], "little")
    header = extra + "'descr': '<f4', 'fortran_order': False, 'shape': (224, 224, 3), "
    raw_header = ("{" + header + "}").encode("ascii")
    padding = (-(10 + len(raw_header) + 1)) % 16
    raw_header += b" " * padding + b"\n"
    altered = payload[:8] + len(raw_header).to_bytes(2, "little") + raw_header + payload[end:]
    receipt["payload_sha256"] = sha256(altered).hexdigest()
    with pytest.raises(ValueError):
        b1.load_generated_payload(altered, receipt, b1.digest_json(receipt))


@pytest.mark.parametrize("value", [-16., 16.])
def test_declared_range_boundary_is_exact_and_never_clipped(value):
    array = np.full((224, 224, 3), value, dtype="<f4")
    normalized = b1.normalize(array)
    np.testing.assert_array_equal(normalized[:, 0, 0], (array[0, 0] - models.MEAN) / models.STD)
    outside = np.nextafter(np.float32(value), np.float32(math.copysign(np.inf, value)))
    array[0, 0, 0] = outside
    with pytest.raises(ValueError):b1.normalize(array)


def test_valid_but_wrong_profile_does_not_become_colour_truth_or_approval():
    pixels, profile, _ = fixture(2.2, 0)
    wrong_profile = fixture(1., 0)[1]
    correct, evidence = b1.convert_generated(pixels, profile)
    wrong, wrong_evidence = b1.convert_generated(pixels, wrong_profile)
    assert np.max(np.abs(correct - wrong)) > .1
    assert evidence["profile_sha256"] != wrong_evidence["profile_sha256"]
    # A numerical converter cannot authenticate whether a camera profile is true.
    assert b1.CONTRACT["scope"] == "generated_only_not_production"


def test_study_entry_never_opens_images_or_files_or_calls_production(monkeypatch):
    from src.vision import exploratory_bundle as old
    from src.vision import exploratory_bundle_v4 as v4
    def forbidden(*args, **kwargs):
        pytest.fail("Generated B1 path attempted external IO/production")
    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Image, "open", forbidden)
    monkeypatch.setattr(Image.Image, "save", forbidden)
    monkeypatch.setattr(old, "package_development", forbidden)
    monkeypatch.setattr(v4, "package_development", forbidden)
    result = b1.run_generated_smoke()
    assert not result["production_active"] and not result["real_data_accessed"]


def test_option_a_and_existing_training_gates_unchanged():
    from src.vision import exploratory_bundle as old
    from src.vision import exploratory_bundle_v4 as v4
    before = deepcopy(v4.policy_spec())
    directory = Path(b1.__file__).parent
    names = ["colour_qa.py", "colour_policy.py", "exploratory_bundle.py", "exploratory_bundle_v4.py",
             "exploratory_pilot.py", "model_pipeline.py", "train_pipeline.py"]
    hashes = {n: sha256((directory/n).read_bytes()).hexdigest() for n in names}
    b1.run_generated_smoke()
    assert before == v4.policy_spec() and old.ROUNDTRIP_LIMIT == 2
    assert hashes == {n: sha256((directory/n).read_bytes()).hexdigest() for n in names}
    assert v4.SCOPE == "package_development_option_a_v4"
    with pytest.raises(ValueError):models.approved_training_records({"status": "generated_only_not_production"})


def test_resnet50_unclipped_forward_weights_none():
    torch = pytest.importorskip("torch", reason="torch unavailable; no install/download authorised")
    pytest.importorskip("torchvision", reason="torchvision unavailable")
    torch.manual_seed(42)
    torch.set_num_threads(1)
    prepared = b1.prepare_generated(*fixture()[:2])
    bundle = models.make_model("resnet50", pretrained=False)
    before = prepared.normalized_chw.copy()
    with torch.no_grad():
        output = bundle["model"](torch.from_numpy(prepared.normalized_chw[None]))
    assert tuple(output.shape) == (1, 5) and torch.isfinite(output).all()
    np.testing.assert_array_equal(prepared.normalized_chw, before)


def test_resnet50_gradcam_frozen_backbone_hooks_and_alignment_weights_none():
    torch = pytest.importorskip("torch", reason="torch unavailable; B1 autograd not verified locally")
    pytest.importorskip("torchvision", reason="torchvision unavailable")
    torch.manual_seed(42)
    torch.set_num_threads(1)
    prepared = b1.prepare_generated(*fixture()[:2])
    bundle = models.make_model("resnet50", pretrained=False, freeze_backbone=True)
    model, target = bundle["model"], bundle["cam_layer"]
    weights = {k: v.clone() for k, v in model.state_dict().items()}
    hooks = len(target._forward_hooks)
    result = b1.generated_gradcam(model, target, prepared, class_index=2)
    assert result["cam"].shape == prepared.original_rgb.shape[:2]
    assert result["overlay"].shape == prepared.original_rgb.shape
    assert result["explained_mgi_schema_grade"] == 2
    assert "may lose colour" in result["display_evidence"]["meaning"]
    assert np.isfinite(result["cam"]).all()
    assert len(target._forward_hooks) == hooks
    assert all(p.grad is None for p in model.parameters())
    assert all(torch.equal(v, model.state_dict()[k]) for k, v in weights.items())
