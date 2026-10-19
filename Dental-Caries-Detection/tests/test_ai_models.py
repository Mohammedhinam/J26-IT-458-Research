"""Direct checks of the existing trained models, without HTTP/system assertions.

From Dental-Caries-Detection:
    backend/.venv/Scripts/python.exe -m pytest tests/test_ai_models.py

Requires backend dependencies, the three existing weights, and test_image.jpg.
Inference is real. Numeric tolerances allow small hardware-dependent differences.
"""

import importlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
IMAGE_PATH = ROOT / "backend/test_image.jpg"
EXPECTED_CLASSES = (
    "AdvanceEnamel_Caries", "EarlyStageEnamel_Caries", "NoEnamel_Caries",
)


@pytest.fixture(scope="module")
def models():
    assert IMAGE_PATH.is_file(), f"Missing reference image: {IMAGE_PATH}"
    for filename in ("best.pt", "mobilenetv2.keras", "efficientnetb0.keras"):
        path = ROOT / "models" / filename
        assert path.is_file(), f"Missing trained model: {path}"
    with pytest.MonkeyPatch.context() as imports:
        imports.syspath_prepend(str(ROOT / "backend"))
        prediction = importlib.import_module("app.services.caries_prediction")
        gradcam = importlib.import_module("app.services.gradcam")
        yolo, mobile, efficient = prediction.load_models()
        yield SimpleNamespace(
            yolo=yolo, mobile=mobile, efficient=efficient,
            prediction=prediction, prepare_crop=gradcam.prepare_region_crop,
        )


@pytest.fixture(scope="module")
def detector_runs(models):
    return tuple(models.yolo.predict(
        source=str(IMAGE_PATH), conf=0.25, verbose=False,
    )[0] for _ in range(2))


@pytest.fixture(scope="module")
def crop(models):
    # Reuse production padding, resizing, RGB conversion, and float32 conversion.
    # No external normalization: the saved classifier preprocessing is retained.
    return models.prepare_crop(IMAGE_PATH, 1)


def test_existing_models_load_with_expected_interfaces(models):
    assert models.yolo.task == "detect"
    assert callable(models.yolo.predict)
    for classifier in (models.mobile, models.efficient):
        assert callable(classifier.predict)
        assert len(classifier.inputs) == len(classifier.outputs) == 1
        assert tuple(classifier.input_shape) == (None, 224, 224, 3)
        assert tuple(classifier.output_shape) == (None, 3)
    # These are the backbones used by the production Grad-CAM implementation.
    assert models.mobile.get_layer("mobilenetv2_1.00_224") is not None
    assert models.efficient.get_layer("efficientnetb0") is not None


def test_classifier_mapping_preserves_trained_output_order(models):
    assert tuple(models.prediction.CLASS_NAMES) == EXPECTED_CLASSES
    assert len(set(models.prediction.CLASS_NAMES)) == 3
    for classifier in (models.mobile, models.efficient):
        assert classifier.output_shape[-1] == len(EXPECTED_CLASSES)


def test_yolo_rgb_input_and_detection_output_shapes(models, detector_runs):
    first, _ = detector_runs
    with Image.open(IMAGE_PATH) as image:
        width, height = image.size
    assert first.orig_shape == (height, width)
    assert first.orig_img.shape == (height, width, 3)
    # The loaded detector's first convolution accepts three color channels.
    assert models.yolo.model.model[0].conv.in_channels == 3
    assert first.boxes is not None
    boxes = first.boxes.xyxy.cpu().numpy()
    scores = first.boxes.conf.cpu().numpy()
    classes = first.boxes.cls.cpu().numpy()
    count = len(boxes)
    assert count > 0, "Reference image must exercise nonempty detector outputs"
    assert boxes.shape == (count, 4)
    assert scores.shape == classes.shape == (count,)
    assert np.isfinite(boxes).all()
    assert np.isfinite(scores).all()
    assert np.isfinite(classes).all()
    assert ((scores >= 0.25) & (scores <= 1)).all()
    np.testing.assert_array_equal(classes, classes.astype(int))
    names = models.yolo.names
    assert names
    # Detector labels are separate from the classifiers' severity-label mapping.
    for index in classes.astype(int):
        assert 0 <= index < len(names)
        assert isinstance(names[int(index)], str) and names[int(index)].strip()


def test_yolo_inference_is_repeatable(detector_runs):
    first, second = detector_runs
    np.testing.assert_array_equal(
        first.boxes.cls.cpu().numpy(), second.boxes.cls.cpu().numpy(),
    )
    np.testing.assert_allclose(
        first.boxes.xyxy.cpu().numpy(), second.boxes.xyxy.cpu().numpy(),
        rtol=1e-5, atol=1e-3,
    )
    np.testing.assert_allclose(
        first.boxes.conf.cpu().numpy(), second.boxes.conf.cpu().numpy(),
        rtol=1e-5, atol=1e-6,
    )


@pytest.mark.parametrize("name", ["mobile", "efficient"])
@pytest.mark.parametrize("batch_size", [1, 2])
def test_classifier_scores_shapes_and_repeatability(models, crop, name, batch_size):
    assert crop.shape == (224, 224, 3)
    assert crop.dtype == np.float32
    assert np.isfinite(crop).all()
    assert crop.min() >= 0 and crop.max() <= 255
    batch = np.stack([crop] * batch_size)
    original = batch.copy()
    classifier = getattr(models, name)
    first = np.asarray(classifier.predict(batch, verbose=0))
    second = np.asarray(classifier.predict(batch, verbose=0))
    np.testing.assert_array_equal(batch, original)
    for scores in (first, second):
        assert scores.shape == (batch_size, 3)
        assert np.issubdtype(scores.dtype, np.floating)
        assert np.isfinite(scores).all()
        assert ((scores >= 0) & (scores <= 1)).all()
        np.testing.assert_allclose(scores.sum(axis=1), 1, rtol=1e-5, atol=1e-5)
        for index in np.argmax(scores, axis=1):
            assert models.prediction.CLASS_NAMES[int(index)] == EXPECTED_CLASSES[int(index)]
    np.testing.assert_allclose(first, second, rtol=1e-5, atol=1e-6)
    np.testing.assert_array_equal(first.argmax(axis=1), second.argmax(axis=1))
    if batch_size == 2:
        # Identical crops must retain identical predictions within a batch.
        np.testing.assert_allclose(first[0], first[1], rtol=1e-5, atol=1e-6)
