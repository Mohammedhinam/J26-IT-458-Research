"""Real-model system checks; these deliberately perform expensive inference.

From Dental-Caries-Detection:
    backend/.venv/Scripts/python.exe -m pytest tests/test_system.py

Requires the existing backend dependencies, all three trained model files, and
backend/test_image.jpg. The reference image is expected to yield six regions.
The blank-image case expects no detections at the production threshold (0.25);
a false positive is a test failure, not a reason to substitute mocked results.
"""

import base64
import importlib
import io
import math
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_IMAGE = PROJECT_ROOT / "backend/test_image.jpg"
CLASS_NAMES = {
    "AdvanceEnamel_Caries", "EarlyStageEnamel_Caries", "NoEnamel_Caries",
}


@pytest.fixture(scope="module")
def system():
    assert REFERENCE_IMAGE.is_file(), f"Missing reference image: {REFERENCE_IMAGE}"
    for filename in ("best.pt", "mobilenetv2.keras", "efficientnetb0.keras"):
        path = PROJECT_ROOT / "models" / filename
        assert path.is_file(), f"Missing trained model: {path}"
    # Only adjust import discovery; application functions and models stay real.
    with pytest.MonkeyPatch.context() as imports:
        imports.syspath_prepend(str(PROJECT_ROOT / "backend"))
        main = importlib.import_module("app.main")
        prediction = importlib.import_module("app.services.caries_prediction")
        with TestClient(main.app) as client:
            yield SimpleNamespace(client=client, prediction=prediction)


@pytest.fixture(scope="module")
def reference_prediction(system):
    with REFERENCE_IMAGE.open("rb") as image:
        response = system.client.post(
            "/api/caries/predict",
            files={"file": (REFERENCE_IMAGE.name, image, "image/jpeg")},
        )
    assert response.status_code == 200, response.text
    return response.json()


def test_complete_prediction_returns_six_regions(reference_prediction):
    body = reference_prediction
    assert set(body) == {"image", "total_regions", "regions"}
    assert body["image"] == REFERENCE_IMAGE.name
    assert body["total_regions"] == 6
    assert isinstance(body["regions"], list)
    assert len(body["regions"]) == 6
    assert [region["region"] for region in body["regions"]] == list(range(1, 7))


def test_real_model_fields_and_agreement(reference_prediction):
    regions = reference_prediction["regions"]
    assert len(regions) == 6
    for region in regions:
        assert set(region) == {
            "region", "bounding_box", "detection_confidence", "MobileNetV2",
            "EfficientNetB0", "status", "final_prediction",
        }
        for name in ("MobileNetV2", "EfficientNetB0"):
            model = region[name]
            assert set(model) == {"prediction", "confidence"}
            assert model["prediction"] in CLASS_NAMES
            assert isinstance(model["confidence"], (int, float))
            assert math.isfinite(model["confidence"])
            assert 0 <= model["confidence"] <= 1
        mobile = region["MobileNetV2"]["prediction"]
        efficient = region["EfficientNetB0"]["prediction"]
        if mobile == efficient:
            assert region["status"] == "Agreement"
            assert region["final_prediction"] == mobile
        else:
            assert region["status"] == "Uncertain - Review Required"
            assert region["final_prediction"] == "Uncertain"


def test_detected_bounding_boxes_are_valid(reference_prediction):
    with Image.open(REFERENCE_IMAGE) as image:
        width, height = image.size
    assert len(reference_prediction["regions"]) == 6
    for region in reference_prediction["regions"]:
        box = region["bounding_box"]
        assert isinstance(box, list) and len(box) == 4
        assert all(type(coordinate) is int for coordinate in box)
        x1, y1, x2, y2 = box
        assert 0 <= x1 < x2 <= width
        assert 0 <= y1 < y2 <= height
        confidence = region["detection_confidence"]
        assert isinstance(confidence, (int, float))
        assert math.isfinite(confidence)
        assert 0.25 <= confidence <= 1


def test_real_detector_no_detection_response(system):
    buffer = io.BytesIO()
    with Image.new("RGB", (640, 640), "white") as blank:
        blank.save(buffer, format="PNG")
    response = system.client.post(
        "/api/caries/predict",
        files={"file": ("blank.png", buffer.getvalue(), "image/png")},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "image": "blank.png", "total_regions": 0, "regions": [],
        "message": "No suspected regions detected",
    }, "The real detector must return no suspected regions for the blank image."


def test_real_gradcam_endpoint(system, reference_prediction):
    assert reference_prediction["total_regions"] == 6
    with REFERENCE_IMAGE.open("rb") as image:
        response = system.client.post(
            "/api/caries/gradcam", data={"region": "1"},
            files={"file": (REFERENCE_IMAGE.name, image, "image/jpeg")},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"region", "MobileNetV2", "EfficientNetB0"}
    assert body["region"] == 1
    for name in ("MobileNetV2", "EfficientNetB0"):
        result = body[name]
        assert set(result) == {"predicted_class", "heatmap_shape", "overlay"}
        # The current endpoint serializes class indices rather than class names.
        index = result["predicted_class"]
        assert type(index) is int and 0 <= index < 3
        assert system.prediction.CLASS_NAMES[index] == (
            reference_prediction["regions"][0][name]["prediction"]
        )
        shape = result["heatmap_shape"]
        assert isinstance(shape, list) and len(shape) == 2
        assert all(type(dimension) is int and dimension > 0 for dimension in shape)
        prefix = "data:image/png;base64,"
        assert result["overlay"].startswith(prefix)
        raw_png = base64.b64decode(result["overlay"][len(prefix):], validate=True)
        with Image.open(io.BytesIO(raw_png)) as overlay:
            assert overlay.format == "PNG"
            assert overlay.size == (224, 224)
            overlay.verify()
