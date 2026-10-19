"""Upload validation units; run this file explicitly to avoid legacy model scripts.

From Dental-Caries-Detection:
    backend/.venv/Scripts/python.exe -m pytest tests/test_unit.py
Inference imports are stubbed before loading the routes; no models are loaded.
"""

import importlib.util
import io
import sys
import tempfile
from functools import partial
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image
from starlette.datastructures import Headers


@pytest.fixture
def routes(monkeypatch, tmp_path):
    prediction = ModuleType("app.services.caries_prediction")
    prediction.predict_dental_caries = Mock(return_value={"regions": []})
    gradcam = ModuleType("app.services.gradcam")
    gradcam.generate_region_gradcams = Mock(return_value={
        "region": 1,
        "mobile_class": "NoEnamel_Caries",
        "efficient_class": "NoEnamel_Caries",
        "mobile_heatmap": SimpleNamespace(shape=(8, 8)),
        "efficient_heatmap": SimpleNamespace(shape=(8, 8)),
        "mobile_overlay": "mobile-overlay",
        "efficient_overlay": "efficient-overlay",
    })
    # Scope import stubs to module loading so other test imports are unaffected.
    with monkeypatch.context() as imports:
        imports.setitem(sys.modules, prediction.__name__, prediction)
        imports.setitem(sys.modules, gradcam.__name__, gradcam)
        path = Path(__file__).resolve().parents[1] / "backend/app/routes/caries.py"
        spec = importlib.util.spec_from_file_location("_upload_validation_routes", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    monkeypatch.setattr(module, "tempfile", SimpleNamespace(
        NamedTemporaryFile=partial(tempfile.NamedTemporaryFile, dir=tmp_path),
    ))
    return module


@pytest.fixture(params=["predict", "gradcam"])
def endpoint(request, routes):
    if request.param == "predict":
        return routes.predict_caries
    return partial(routes.predict_gradcam, region=1)


def image_bytes(image_format="PNG"):
    buffer = io.BytesIO()
    with Image.new("RGB", (8, 8), color="white") as image:
        image.save(buffer, format=image_format)
    return buffer.getvalue()


@pytest.fixture
def upload_factory():
    streams = []

    def make(payload, content_type="image/png", filename="dental.png"):
        stream = io.BytesIO(payload)
        streams.append(stream)
        return UploadFile(
            file=stream, filename=filename,
            headers=Headers({"content-type": content_type}),
        )

    yield make
    for stream in streams:
        stream.close()


def assert_no_inference(routes):
    routes.predict_dental_caries.assert_not_called()
    routes.generate_region_gradcams.assert_not_called()


@pytest.mark.parametrize("image_format,content_type,filename", [
    ("JPEG", "image/jpeg", "dental.jpg"),
    ("PNG", "image/png", "dental.png"),
])
def test_valid_image_reaches_inference(
    routes, endpoint, upload_factory, tmp_path, image_format, content_type, filename,
):
    upload = upload_factory(image_bytes(image_format), content_type, filename)
    result = endpoint(file=upload)
    assert isinstance(result, dict)
    calls = (routes.predict_dental_caries.call_count
             + routes.generate_region_gradcams.call_count)
    assert calls == 1
    if routes.predict_dental_caries.called:
        assert result["image"] == filename
    else:
        assert result["region"] == 1
    assert upload.file.closed
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("payload", [b"", b"not an image", image_bytes()[:40]])
def test_corrupted_image_is_rejected(
    routes, endpoint, upload_factory, tmp_path, payload,
):
    upload = upload_factory(payload)
    with pytest.raises(HTTPException) as error:
        endpoint(file=upload)
    assert error.value.status_code == 400
    assert error.value.detail == "Invalid or corrupted image."
    assert_no_inference(routes)
    assert upload.file.closed
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("content_type", [
    "image/gif", "image/bmp", "image/webp", "application/octet-stream",
])
def test_unsupported_mime_type_is_rejected(
    routes, endpoint, upload_factory, tmp_path, content_type,
):
    upload = upload_factory(image_bytes(), content_type)
    with pytest.raises(HTTPException) as error:
        endpoint(file=upload)
    assert error.value.status_code == 400
    assert error.value.detail == "Only JPG and PNG images are supported."
    assert upload.file.tell() == 0
    assert_no_inference(routes)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("image_format", ["GIF", "BMP"])
def test_unsupported_content_with_allowed_mime_type_is_rejected(
    routes, endpoint, upload_factory, tmp_path, image_format,
):
    upload = upload_factory(image_bytes(image_format))
    with pytest.raises(HTTPException) as error:
        endpoint(file=upload)
    assert error.value.status_code == 400
    assert error.value.detail.startswith("Invalid image format.")
    assert_no_inference(routes)
    assert upload.file.closed
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_upload_byte_limit(routes, endpoint, upload_factory, tmp_path, offset):
    # PNG permits trailing bytes; preserve a real, verifiable image at the limit.
    png = image_bytes()
    size = 10 * 1024 * 1024 + offset
    upload = upload_factory(png + b"\0" * (size - len(png)))
    if offset <= 0:
        endpoint(file=upload)
        assert (routes.predict_dental_caries.call_count
                + routes.generate_region_gradcams.call_count) == 1
    else:
        with pytest.raises(HTTPException) as error:
            endpoint(file=upload)
        assert error.value.status_code == 413
        assert error.value.detail == "Image upload exceeds the maximum size of 10 MB."
        assert_no_inference(routes)
    assert upload.file.closed
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("width,height,accepted", [
    (3999, 5000, True), (4000, 5000, True), (4001, 5000, False),
    (5000, 4001, False),
    (20_000_000 - 1, 1, True), (20_000_000 + 1, 1, False),
])
def test_resolution_limit(
    routes, endpoint, upload_factory, monkeypatch, tmp_path, width, height, accepted,
):
    # Mock dimensions to exercise the real guard without allocating huge rasters.
    image = MagicMock()
    image.format = "PNG"
    image.width, image.height = width, height
    image.__enter__.return_value = image
    monkeypatch.setattr(routes.Image, "open", Mock(return_value=image))
    upload = upload_factory(image_bytes())
    if accepted:
        endpoint(file=upload)
        image.verify.assert_called_once_with()
        assert (routes.predict_dental_caries.call_count
                + routes.generate_region_gradcams.call_count) == 1
    else:
        with pytest.raises(HTTPException) as error:
            endpoint(file=upload)
        assert error.value.status_code == 413
        assert "20 megapixels" in error.value.detail
        image.verify.assert_not_called()
        assert_no_inference(routes)
    assert upload.file.closed
    assert list(tmp_path.iterdir()) == []


def test_decompression_bomb_is_rejected(
    routes, endpoint, upload_factory, monkeypatch, tmp_path,
):
    upload = upload_factory(image_bytes())
    monkeypatch.setattr(routes.Image, "open", Mock(
        side_effect=Image.DecompressionBombError("image is too large"),
    ))
    with pytest.raises(HTTPException) as error:
        endpoint(file=upload)
    assert error.value.status_code == 413
    assert "20 megapixels" in error.value.detail
    assert_no_inference(routes)
    assert upload.file.closed
    assert list(tmp_path.iterdir()) == []
