"""Exercise the real prediction pipeline with controlled model boundaries.

From Dental-Caries-Detection:
    backend/.venv/Scripts/python.exe -m pytest tests/test_integration.py

Pillow cropping, NumPy batching, class mapping, and response assembly are real.
Model constructors and inference are mocked; trained weights are not required.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from PIL import Image


CLASS_NAMES = (
    "AdvanceEnamel_Caries", "EarlyStageEnamel_Caries", "NoEnamel_Caries",
)


@pytest.fixture
def pipeline(monkeypatch):
    tensorflow = ModuleType("tensorflow")
    tensorflow.keras = SimpleNamespace(models=SimpleNamespace(load_model=Mock()))
    ultralytics = ModuleType("ultralytics")
    ultralytics.YOLO = Mock()
    with monkeypatch.context() as imports:
        imports.setitem(sys.modules, "tensorflow", tensorflow)
        imports.setitem(sys.modules, "ultralytics", ultralytics)
        path = (Path(__file__).resolve().parents[1]
                / "backend/app/services/caries_prediction.py")
        spec = importlib.util.spec_from_file_location("_integration_pipeline", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


@pytest.fixture
def dental_image(tmp_path):
    # Distinct pixel coordinates expose incorrect crops or region ordering.
    y, x = np.indices((80, 100))
    pixels = np.stack((x, y, x + y), axis=-1).astype(np.uint8)
    path = tmp_path / "dental.png"
    Image.fromarray(pixels).save(path)
    return path


def tensor_output(values):
    tensor = Mock()
    tensor.cpu.return_value.numpy.return_value = np.asarray(values, dtype=np.float32)
    return tensor


def configure_models(monkeypatch, pipeline, boxes, confidences, mobile, efficient):
    yolo, mobilenet, efficientnet = Mock(), Mock(), Mock()
    yolo.predict.return_value = [SimpleNamespace(boxes=SimpleNamespace(
        xyxy=tensor_output(np.asarray(boxes).reshape(-1, 4)),
        conf=tensor_output(confidences),
    ))]
    mobilenet.predict.return_value = np.asarray(mobile, dtype=np.float32)
    efficientnet.predict.return_value = np.asarray(efficient, dtype=np.float32)
    monkeypatch.setattr(pipeline, "load_models", Mock(
        return_value=(yolo, mobilenet, efficientnet),
    ))
    return yolo, mobilenet, efficientnet


def assert_response_structure(response, count):
    assert set(response) == {"image", "total_regions", "regions"}
    assert response["image"] == "dental.png"
    assert response["total_regions"] == count
    assert len(response["regions"]) == count
    for number, region in enumerate(response["regions"], start=1):
        assert set(region) == {
            "region", "bounding_box", "detection_confidence", "MobileNetV2",
            "EfficientNetB0", "status", "final_prediction",
        }
        assert region["region"] == number
        assert len(region["bounding_box"]) == 4
        assert all(type(value) is int for value in region["bounding_box"])
        assert isinstance(region["detection_confidence"], float)
        assert 0 <= region["detection_confidence"] <= 1
        for model in ("MobileNetV2", "EfficientNetB0"):
            assert set(region[model]) == {"prediction", "confidence"}
            assert region[model]["prediction"] in CLASS_NAMES
            assert isinstance(region[model]["confidence"], float)
            assert 0 <= region[model]["confidence"] <= 1
    assert json.loads(json.dumps(response)) == response


def test_multiple_regions_crop_batch_and_response(pipeline, monkeypatch, dental_image):
    boxes = [[0, 0, 20, 20], [30, 20, 50, 40], [80, 60, 100, 80]]
    probabilities = [[0.812345, 0.1, 0.087655], [0.1, 0.8, 0.1], [0.1, 0.2, 0.7]]
    yolo, mobile, efficient = configure_models(
        monkeypatch, pipeline, boxes, [0.912345, 0.8, 0.7],
        probabilities, probabilities,
    )

    response = pipeline.predict_dental_caries(dental_image)

    pipeline.load_models.assert_called_once_with()
    yolo.predict.assert_called_once_with(
        source=str(dental_image), conf=0.25, verbose=False,
    )
    mobile.predict.assert_called_once()
    efficient.predict.assert_called_once()
    batch = mobile.predict.call_args.args[0]
    assert batch.shape == (3, 224, 224, 3)
    assert batch.dtype == np.float32
    assert mobile.predict.call_args.kwargs == {"verbose": 0}
    assert efficient.predict.call_args.kwargs == {"verbose": 0}
    np.testing.assert_array_equal(efficient.predict.call_args.args[0], batch)
    # Explicit expected padded bounds include clipping at both image edges.
    with Image.open(dental_image) as image:
        for index, bounds in enumerate([(0, 0, 26, 26), (24, 14, 56, 46),
                                        (74, 54, 100, 80)]):
            expected = np.asarray(image.crop(bounds).resize((224, 224)),
                                  dtype=np.float32)
            np.testing.assert_array_equal(batch[index], expected)
    assert_response_structure(response, 3)
    for index, region in enumerate(response["regions"]):
        assert region["bounding_box"] == boxes[index]
        assert region["MobileNetV2"]["prediction"] == CLASS_NAMES[index]
        assert region["EfficientNetB0"]["prediction"] == CLASS_NAMES[index]
        assert region["status"] == "Agreement"
        assert region["final_prediction"] == CLASS_NAMES[index]
    assert response["regions"][0]["detection_confidence"] == 0.9123
    assert response["regions"][0]["MobileNetV2"]["confidence"] == 0.8123
    assert response["regions"][0]["EfficientNetB0"]["confidence"] == 0.8123


@pytest.mark.parametrize("mobile_index,efficient_index", [
    (0, 0), (1, 1), (2, 2),
    (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1),
])
def test_classifier_mapping_and_final_decision(
    pipeline, monkeypatch, dental_image, mobile_index, efficient_index,
):
    mobile = np.full((1, 3), 0.1)
    efficient = np.full((1, 3), 0.05)
    mobile[0, mobile_index] = 0.8
    efficient[0, efficient_index] = 0.9
    configure_models(monkeypatch, pipeline, [[10, 10, 30, 30]], [0.75],
                     mobile, efficient)

    response = pipeline.predict_dental_caries(dental_image)

    assert_response_structure(response, 1)
    region = response["regions"][0]
    assert region["MobileNetV2"] == {
        "prediction": CLASS_NAMES[mobile_index], "confidence": 0.8,
    }
    assert region["EfficientNetB0"] == {
        "prediction": CLASS_NAMES[efficient_index], "confidence": 0.9,
    }
    if mobile_index == efficient_index:
        assert region["status"] == "Agreement"
        assert region["final_prediction"] == CLASS_NAMES[mobile_index]
    else:
        assert region["status"] == "Uncertain - Review Required"
        assert region["final_prediction"] == "Uncertain"


def test_zero_detections_skip_classifiers(pipeline, monkeypatch, dental_image):
    yolo, mobile, efficient = configure_models(
        monkeypatch, pipeline, [], [], [], [],
    )
    response = pipeline.predict_dental_caries(dental_image)
    assert response == {
        "image": "dental.png", "total_regions": 0, "regions": [],
        "message": "No suspected regions detected",
    }
    yolo.predict.assert_called_once_with(
        source=str(dental_image), conf=0.25, verbose=False,
    )
    mobile.predict.assert_not_called()
    efficient.predict.assert_not_called()
    assert json.loads(json.dumps(response)) == response


def test_load_models_wires_existing_model_paths_and_caches(pipeline, monkeypatch):
    monkeypatch.setattr(Path, "is_file", lambda path: True)
    yolo, mobile, efficient = Mock(), Mock(), Mock()
    pipeline.YOLO.return_value = yolo
    loader = pipeline.tf.keras.models.load_model
    loader.side_effect = [mobile, efficient]

    assert pipeline.load_models() == (yolo, mobile, efficient)
    assert pipeline.load_models() == (yolo, mobile, efficient)

    pipeline.YOLO.assert_called_once()
    yolo_call = pipeline.YOLO.call_args
    assert len(yolo_call.args) == 1
    assert Path(yolo_call.args[0]).resolve() == pipeline.YOLO_PATH.resolve()
    assert yolo_call.kwargs == {}
    # Normalize string and Path arguments while retaining order and cache checks.
    assert loader.call_count == 2
    for model_call, expected_path in zip(
        loader.call_args_list,
        (pipeline.MOBILENET_PATH, pipeline.EFFICIENTNET_PATH),
    ):
        assert len(model_call.args) == 1
        assert Path(model_call.args[0]).resolve() == expected_path.resolve()
        assert model_call.kwargs == {"compile": False}
