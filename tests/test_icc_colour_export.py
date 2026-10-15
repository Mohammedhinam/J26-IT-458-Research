"""Generated colour profiles only: no dental images, weights or model execution."""
from copy import deepcopy
from io import BytesIO

import numpy as np
from PIL import Image, ImageCms, PngImagePlugin
import pytest

from src.vision import exploratory_bundle as eb


def generated_profile(gamma=None):
    """A generated sRGB-gamut profile with an optional nonidentity tone curve."""
    data = bytearray(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    if gamma is not None:
        # ICC tag-table offsets describe the generated profile; no camera ICC is edited.
        offsets = set()
        for index in range(int.from_bytes(data[128:132], "big")):
            entry = data[132 + 12 * index:144 + 12 * index]
            if entry[:4] in (b"rTRC", b"gTRC", b"bTRC"):
                offsets.add(int.from_bytes(entry[4:8], "big"))
        assert offsets
        for offset in offsets:
            assert data[offset:offset + 4] == b"para"
            data[offset + 12:offset + 16] = round(gamma * 65536).to_bytes(4, "big", signed=True)
    return bytes(data)


def sample_rgb():
    # Interior colours avoid a misleading gamut-clipping success case.
    values = np.array([[64, 96, 128], [96, 128, 160], [160, 96, 64],
                       [128, 160, 96], [80, 112, 144], [144, 112, 80]], dtype=np.uint8)
    return Image.fromarray(np.tile(values.reshape(2, 3, 3), (7, 11, 1)))


def reference_conversion(image, profile):
    return ImageCms.profileToProfile(
        image, ImageCms.ImageCmsProfile(BytesIO(profile)), ImageCms.createProfile("sRGB"),
        renderingIntent=1, outputMode="RGB", flags=0,
    )


@pytest.mark.parametrize("colour_tag", ["missing", "exif_srgb", "standard_icc"])
def test_identity_colour_paths_preserve_pixels_geometry_and_source_info(colour_tag):
    source = sample_rgb()
    if colour_tag == "exif_srgb":
        exif = Image.Exif(); exif[34665] = {40961: 1}
        source.info["exif"] = exif.tobytes()
    elif colour_tag == "standard_icc":
        source.info["icc_profile"] = generated_profile()
    source.info["comment"] = b"generated private marker"
    before = source.tobytes(), deepcopy(source.info)
    managed, details = eb.managed_srgb(source)
    assert managed is not source and managed.mode == "RGB" and managed.size == source.size
    assert managed.tobytes() == before[0] and managed.info == {"srgb": 1}
    assert (source.tobytes(), source.info) == before
    assert details["roundtrip_max_channel_error"] == 0


def test_nonidentity_rgb_profile_matches_independent_lcms_reference():
    source = sample_rgb(); profile = generated_profile(1.8)
    source.info["icc_profile"] = profile
    exif = Image.Exif(); exif[34665] = {40961: 65535}
    source.info["exif"] = exif.tobytes()
    before = source.tobytes(), deepcopy(source.info)
    expected = reference_conversion(source, profile)
    managed, details = eb.managed_srgb(source)
    assert managed.tobytes() == expected.tobytes()
    assert managed.tobytes() != source.tobytes()
    assert managed.size == source.size and managed.info == {"srgb": 1}
    assert details["conversion"] == "icc_to_srgb"
    assert 0 <= details["roundtrip_max_channel_error"] <= 2
    assert (source.tobytes(), source.info) == before


def test_generated_interior_colours_remain_equivalent_in_lab():
    source = sample_rgb(); profile = generated_profile(1.8)
    source.info.update(icc_profile=profile, xmp=b"generated_private", comment=b"generated_private")
    managed, _ = eb.managed_srgb(source)
    lab_profile = ImageCms.createProfile("LAB")
    source_lab = ImageCms.profileToProfile(
        source, ImageCms.ImageCmsProfile(BytesIO(profile)), lab_profile,
        outputMode="LAB", renderingIntent=1, flags=0,
    )
    managed_lab = ImageCms.profileToProfile(
        managed, ImageCms.createProfile("sRGB"), lab_profile,
        outputMode="LAB", renderingIntent=1, flags=0,
    )
    labs = []
    for image in (source_lab, managed_lab):
        encoded = np.asarray(image)
        values = encoded.astype(np.float64)
        values[..., 0] *= 100 / 255
        values[..., 1:] = encoded[..., 1:].view(np.int8).astype(np.float64)
        labs.append(values)
    delta_e = np.sqrt(np.sum((labs[0] - labs[1]) ** 2, axis=-1))
    # This is an eight-bit generated-fixture numerical check, not a clinical tolerance.
    assert float(delta_e.max()) <= 2
    assert managed.info == {"srgb": 1}


def test_lossless_icc_export_preserves_source_bytes_and_separate_payload_hash(tmp_path):
    source_path = tmp_path / "generated-source.png"
    source = sample_rgb(); profile = generated_profile(1.8)
    exif = Image.Exif(); exif[274] = 1; exif[306] = "generated_datetime"
    exif[34853] = {0: b"\x02\x03\x00\x00"}
    exif[34665] = {37500: b"generated_private_makernote", 40961: 65535}
    metadata = PngImagePlugin.PngInfo(); metadata.add_text("XML:com.adobe.xmp", "generated_xmp")
    source.save(source_path, icc_profile=profile, exif=exif, pnginfo=metadata)
    original_bytes = source_path.read_bytes(); original_sha = eb.sha256(source_path)
    destination = tmp_path / "export.png"
    with Image.open(source_path) as decoded:
        expected = reference_conversion(decoded, profile)
        source_pixels = decoded.tobytes()
        result = eb.export_rgb_png(decoded, destination)
        assert decoded.tobytes() == source_pixels
    with Image.open(destination) as exported:
        assert exported.info == {"srgb": 1}
        assert exported.mode == "RGB" and exported.size == source.size
        assert exported.tobytes() == expected.tobytes()
        assert not exported.getexif()
    assert source_path.read_bytes() == original_bytes and eb.sha256(source_path) == original_sha
    assert result["sha256"] == eb.sha256(destination) and result["sha256"] != original_sha
    assert result["rgb_sha256"] == eb.rgb_digest(expected)
    assert result["dimensions"] == list(source.size)
    eb.verify_rgb_export(destination, result)


def test_managed_resize_and_full_resolution_cam_share_one_colour_space(tmp_path):
    source = sample_rgb(); source.info["icc_profile"] = generated_profile(1.8)
    managed, _ = eb.managed_srgb(source)
    full_result = eb.export_rgb_png(source, tmp_path / "cam.png")
    small = eb.resized_rgb(managed)
    small_result = eb.export_rgb_png(small, tmp_path / "derivative.png")
    with Image.open(tmp_path / "cam.png") as full, Image.open(tmp_path / "derivative.png") as derivative:
        assert full.tobytes() == managed.tobytes() and full.size == source.size
        assert derivative.tobytes() == small.tobytes()
        assert np.array_equal(eb.vp.preprocess_rgb(full).normalized_chw,
                              eb.vp.preprocess_rgb(derivative).normalized_chw)
    assert full_result["rgb_sha256"] == eb.rgb_digest(managed)
    assert small_result["rgb_sha256"] == eb.rgb_digest(small)


@pytest.mark.parametrize("profile", [b"", b"not_an_icc", generated_profile()[:80],
                                      ImageCms.ImageCmsProfile(ImageCms.createProfile("LAB")).tobytes()])
def test_empty_malformed_truncated_or_nonrgb_icc_fails_before_output(tmp_path, profile):
    source = sample_rgb(); source.info["icc_profile"] = profile
    before = source.tobytes(), deepcopy(source.info)
    with pytest.raises(ValueError):
        eb.export_rgb_png(source, tmp_path / "unsafe.png")
    assert not (tmp_path / "unsafe.png").exists() and (source.tobytes(), source.info) == before


@pytest.mark.parametrize("device_class", [b"link", b"abst", b"nmcl", b"prtr"])
def test_unsupported_icc_profile_classes_fail_closed(tmp_path, device_class):
    profile = bytearray(generated_profile()); profile[12:16] = device_class
    source = sample_rgb(); source.info["icc_profile"] = bytes(profile)
    with pytest.raises(ValueError):
        eb.export_rgb_png(source, tmp_path / "unsupported.png")
    assert not (tmp_path / "unsupported.png").exists()


@pytest.mark.parametrize("case", ["uncalibrated", "gamma", "chromaticity", "orientation"])
def test_missing_interpretation_or_unapproved_geometry_fails_closed(tmp_path, case):
    source = sample_rgb()
    if case == "uncalibrated":
        exif = Image.Exif(); exif[34665] = {40961: 65535}; source.info["exif"] = exif.tobytes()
    elif case == "orientation":
        exif = Image.Exif(); exif[274] = 6; source.info["exif"] = exif.tobytes()
        source.info["icc_profile"] = generated_profile()
    else:
        source.info[case] = 0.45 if case == "gamma" else (0.3,) * 8
    with pytest.raises(ValueError):
        eb.export_rgb_png(source, tmp_path / "ambiguous.png")
    assert not (tmp_path / "ambiguous.png").exists()


def test_fixed_srgb_chunk_cannot_be_replaced_by_arbitrary_intent(tmp_path):
    path = tmp_path / "safe.png"; expected = eb.export_rgb_png(sample_rgb(), path)
    with Image.open(path) as opened:
        pixels = Image.frombytes("RGB", opened.size, opened.tobytes())
    altered = PngImagePlugin.PngInfo(); altered.add(b"sRGB", b"\x00")
    pixels.save(path, pnginfo=altered)
    expected["sha256"] = eb.sha256(path)
    with pytest.raises(ValueError):
        eb.verify_rgb_export(path, expected)


def test_large_colour_roundtrip_error_fails_before_writing(tmp_path, monkeypatch):
    source = sample_rgb(); source.info["icc_profile"] = generated_profile(1.8)
    original_transform = ImageCms.profileToProfile
    calls = []
    def unreliable_roundtrip(image, *args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            return Image.new("RGB", image.size, (0, 0, 0))
        return original_transform(image, *args, **kwargs)
    monkeypatch.setattr(ImageCms, "profileToProfile", unreliable_roundtrip)
    with pytest.raises(ValueError):
        eb.export_rgb_png(source, tmp_path / "clipped.png")
    assert len(calls) == 2
    assert all(call["renderingIntent"] == 1 and call["flags"] == 0 for call in calls)
    assert not (tmp_path / "clipped.png").exists()
