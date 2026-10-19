"""HTTP tests for the existing app, with AI services replaced before import.

From Dental-Caries-Detection:
    backend/.venv/Scripts/python.exe -m pytest tests/test_api.py
"""

import importlib.util
import io
import sys
import tempfile
from functools import partial
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from PIL import Image


def image_bytes(image_format="PNG"):
    buffer = io.BytesIO()
    with Image.new("RGB", (8, 8), "white") as image:
        image.save(buffer, format=image_format)
    return buffer.getvalue()


@pytest.fixture
def api(monkeypatch, tmp_path):
    prediction = ModuleType("app.services.caries_prediction")
    prediction.predict_dental_caries = Mock(return_value={
        "image": "temporary.png", "total_regions": 1, "regions": [{
            "region": 1, "bounding_box": [0, 0, 8, 8],
            "detection_confidence": 0.9,
            "MobileNetV2": {"prediction": "NoEnamel_Caries", "confidence": 0.8},
            "EfficientNetB0": {"prediction": "NoEnamel_Caries", "confidence": 0.85},
            "status": "Agreement", "final_prediction": "NoEnamel_Caries",
        }],
    })
    gradcam = ModuleType("app.services.gradcam")
    gradcam.generate_region_gradcams = Mock(return_value={
        "region": 2, "mobile_class": "NoEnamel_Caries",
        "efficient_class": "EarlyStageEnamel_Caries",
        "mobile_heatmap": SimpleNamespace(shape=(8, 8)),
        "efficient_heatmap": SimpleNamespace(shape=(7, 7)),
        "mobile_overlay": "mobile-overlay", "efficient_overlay": "efficient-overlay",
    })
    root = Path(__file__).resolve().parents[1] / "backend/app"
    # Import the real app and routers in an isolated package namespace. Restore
    # every substituted module afterward so other tests keep their own imports.
    with monkeypatch.context() as imports:
        for name, directory in [("app", root), ("app.routes", root / "routes"),
                                ("app.services", root / "services")]:
            package = ModuleType(name)
            package.__path__ = [str(directory)]
            imports.setitem(sys.modules, name, package)
        imports.setitem(sys.modules, prediction.__name__, prediction)
        imports.setitem(sys.modules, gradcam.__name__, gradcam)

        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            imports.setitem(sys.modules, name, module)
            spec.loader.exec_module(module)
            return module

        routes = load("app.routes.caries", root / "routes/caries.py")
        load("app.routes.health", root / "routes/health.py")
        main = load("app.main", root / "main.py")
    monkeypatch.setattr(routes, "tempfile", SimpleNamespace(
        NamedTemporaryFile=partial(tempfile.NamedTemporaryFile, dir=tmp_path),
    ))
    with TestClient(main.app) as client:
        yield SimpleNamespace(
            client=client, predict=prediction.predict_dental_caries,
            gradcam=gradcam.generate_region_gradcams,
        )
    assert list(tmp_path.iterdir()) == []


@pytest.fixture(params=["predict", "gradcam"])
def endpoint(request):
    return request.param


def post_image(api, endpoint, payload=None, content_type="image/png", **kwargs):
    return api.client.post(
        f"/api/caries/{endpoint}",
        files={"file": ("dental.png", image_bytes() if payload is None else payload,
                        content_type)},
        data={"region": "2"} if endpoint == "gradcam" else {},
        **kwargs,
    )


def assert_no_inference(api):
    api.predict.assert_not_called()
    api.gradcam.assert_not_called()


def test_health(api):
    response = api.client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert_no_inference(api)


@pytest.mark.parametrize("image_format,content_type", [
    ("PNG", "image/png"), ("JPEG", "image/jpeg"),
])
def test_valid_upload_and_response(api, endpoint, image_format, content_type):
    response = post_image(api, endpoint, image_bytes(image_format), content_type)
    assert response.status_code == 200
    body = response.json()
    if endpoint == "predict":
        api.predict.assert_called_once()
        api.gradcam.assert_not_called()
        assert body == {**api.predict.return_value, "image": "dental.png"}
        assert set(body) == {"image", "total_regions", "regions"}
        assert body["total_regions"] == len(body["regions"]) == 1
        region = body["regions"][0]
        assert region["region"] == 1
        assert region["status"] == "Agreement"
        assert region["final_prediction"] == "NoEnamel_Caries"
        for model in ("MobileNetV2", "EfficientNetB0"):
            assert set(region[model]) == {"prediction", "confidence"}
    else:
        api.predict.assert_not_called()
        api.gradcam.assert_called_once()
        assert api.gradcam.call_args.args[1] == 2
        assert body == {
            "region": 2,
            "MobileNetV2": {"predicted_class": "NoEnamel_Caries",
                            "heatmap_shape": [8, 8], "overlay": "mobile-overlay"},
            "EfficientNetB0": {"predicted_class": "EarlyStageEnamel_Caries",
                               "heatmap_shape": [7, 7], "overlay": "efficient-overlay"},
        }


def test_missing_file(api, endpoint):
    response = api.client.post(f"/api/caries/{endpoint}", data={"region": "2"})
    assert response.status_code == 422
    assert any(item["loc"] == ["body", "file"] for item in response.json()["detail"])
    assert_no_inference(api)


@pytest.mark.parametrize("payload", [b"", b"not an image", image_bytes()[:40]])
def test_invalid_image(api, endpoint, payload):
    response = post_image(api, endpoint, payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid or corrupted image."}
    assert_no_inference(api)


@pytest.mark.parametrize("content_type", ["image/gif", "image/bmp", "application/octet-stream"])
def test_unsupported_mime_type(api, endpoint, content_type):
    response = post_image(api, endpoint, content_type=content_type)
    assert response.status_code == 400
    assert response.json() == {"detail": "Only JPG and PNG images are supported."}
    assert_no_inference(api)


def test_unsupported_image_disguised_as_png(api, endpoint):
    response = post_image(api, endpoint, image_bytes("GIF"))
    assert response.status_code == 400
    detail = ("Invalid image format. Upload JPG or PNG."
              if endpoint == "predict" else "Invalid image format.")
    assert response.json() == {"detail": detail}
    assert_no_inference(api)


def test_oversized_upload(api, endpoint):
    png = image_bytes()
    payload = png + b"\0" * (10 * 1024 * 1024 + 1 - len(png))
    response = post_image(api, endpoint, payload)
    assert response.status_code == 413
    assert response.json() == {"detail": "Image upload exceeds the maximum size of 10 MB."}
    assert_no_inference(api)


@pytest.mark.parametrize("region", ["0", "-1"])
def test_gradcam_nonpositive_region(api, region):
    response = api.client.post(
        "/api/caries/gradcam", data={"region": region},
        files={"file": ("dental.png", image_bytes(), "image/png")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Region number must be 1 or greater."}
    assert_no_inference(api)


@pytest.mark.parametrize("data", [{}, {"region": "abc"}, {"region": "1.5"}])
def test_gradcam_missing_or_noninteger_region(api, data):
    response = api.client.post(
        "/api/caries/gradcam", data=data,
        files={"file": ("dental.png", image_bytes(), "image/png")},
    )
    assert response.status_code == 422
    assert any(item["loc"] == ["body", "region"] for item in response.json()["detail"])
    assert_no_inference(api)


def test_gradcam_region_not_detected(api):
    api.gradcam.side_effect = ValueError("Region number out of range")
    response = post_image(api, "gradcam")
    assert response.status_code == 400
    assert response.json() == {"detail": "Region number out of range"}
    api.gradcam.assert_called_once()
    api.predict.assert_not_called()


def test_prediction_without_detections(api):
    api.predict.return_value = {
        "image": "temporary.png", "total_regions": 0, "regions": [],
        "message": "No suspected regions detected",
    }
    response = post_image(api, "predict")
    assert response.status_code == 200
    assert response.json() == {
        "image": "dental.png", "total_regions": 0, "regions": [],
        "message": "No suspected regions detected",
    }
