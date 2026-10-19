"""Local upload preprocessing checks use generated pixels only."""

from io import BytesIO

import numpy as np
from PIL import Image, ImageCms
import pytest

from src.vision import local_photo_upload_demo as demo


def generated_photo(*, image_format="JPEG", icc=True, mode="RGB", orientation=1):
    pixels = np.zeros((24, 40, 3), dtype=np.uint8)
    pixels[:, :20] = (230, 40, 20)
    pixels[:, 20:] = (20, 180, 220)
    image = Image.fromarray(pixels)
    if mode == "RGBA":
        image.putalpha(128)
    elif mode == "CMYK":
        image = image.convert("CMYK")
    exif = Image.Exif()
    exif[274] = orientation
    output = BytesIO()
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes() if icc else None
    image.save(output, format=image_format, exif=exif, icc_profile=profile)
    image.close()
    return output.getvalue()


def test_untagged_phone_jpeg_is_explicitly_assumed_srgb_and_not_saved():
    payload = generated_photo(icc=False)
    prepared = demo.prepare_local_upload(payload, "image/jpeg")
    try:
        assert prepared.input_colour_policy == (
            "No ICC profile was present; RGB values were assumed to be sRGB for this demo."
        )
        assert prepared.model_input.normalized_chw.shape == (3, 224, 224)
        assert prepared.model_input.display_evidence["photo_saved"] is False
        assert prepared.model_input.display_evidence["icc_profile_present"] is False
    finally:
        prepared.close()


def test_embedded_srgb_icc_is_converted_and_rgba_is_composited():
    payload = generated_photo(image_format="PNG", mode="RGBA")
    prepared = demo.prepare_local_upload(payload, "image/png")
    try:
        assert prepared.input_colour_policy == "Embedded ICC converted to sRGB before inference."
        assert prepared.srgb_image.mode == "RGB"
        assert np.asarray(prepared.srgb_image)[0, 0].mean() > 150
    finally:
        prepared.close()


def test_exif_orientation_is_applied_to_the_display_and_model_input():
    payload = generated_photo(icc=False, orientation=6)
    prepared = demo.prepare_local_upload(payload, "image/jpeg")
    try:
        assert prepared.orientation_applied is True
        assert prepared.srgb_image.size == (24, 40)
        assert prepared.model_input.original_rgb.shape == (40, 24, 3)
    finally:
        prepared.close()


@pytest.mark.parametrize(
    ("payload", "content_type", "message"),
    [
        (b"not an image", "image/jpeg", "readable photo"),
        (generated_photo(), "image/png", "contents do not match"),
        (generated_photo(icc=False, mode="CMYK"), "image/jpeg", "need an embedded colour profile"),
        (b"", "image/jpeg", "nonempty image"),
    ],
)
def test_invalid_photo_uploads_are_rejected(payload, content_type, message):
    with pytest.raises(ValueError, match=message):
        demo.prepare_local_upload(payload, content_type)


def test_local_upload_runtime_returns_four_grade_output_and_colour_policy(monkeypatch):
    payload = generated_photo(icc=False)

    def fake_gradcam(model, layer, prepared):
        shape = prepared.original_rgb.shape
        image = prepared.original_rgb.copy()
        return {
            "probabilities": [0.1, 0.2, 0.4, 0.3],
            "predicted_mgi_grade": 3,
            "explanation_status": "ok",
            "original": image,
            "heatmap": np.zeros(shape, dtype=np.uint8),
            "overlay": image.copy(),
        }

    monkeypatch.setattr(demo.pilot, "gradcam", fake_gradcam)
    runtime = demo.LocalUploadPhotoRuntime(object(), object(), "1" * 64)
    result = runtime.explain_upload(payload, "image/jpeg")
    assert result["predicted_grade"] == 3
    assert result["mgi_grades"] == [1, 2, 3, 4]
    assert result["input_colour_policy"].endswith("assumed to be sRGB for this demo.")
    assert result["photo_saved"] is False
    assert runtime.status()["upload_mode"] == "local_user_upload_demo"
