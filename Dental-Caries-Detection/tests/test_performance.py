"""Real API timings on CPU; no speed thresholds or mocked inference.

From Dental-Caries-Detection:
    backend/.venv/Scripts/python.exe -m pytest -s tests/test_performance.py

Each endpoint receives exactly three sequential timed requests. Models preload
once in a shared local server process; startup is excluded from measurements.
The first inference may still include lazy initialization. Timings cover the
HTTP upload, inference, and response transfer, excluding response validation.
Use --junitxml=performance.xml to retain the recorded timing properties.
Requires the existing backend dependencies (including httpx), models, and JPG.
"""

import base64
import io
import os
from pathlib import Path
import socket
import statistics
import subprocess
import sys
import time

import httpx
import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
IMAGE_PATH = ROOT / "backend/test_image.jpg"
CLASS_NAMES = {"AdvanceEnamel_Caries", "EarlyStageEnamel_Caries", "NoEnamel_Caries"}
REQUEST_TIMEOUT = httpx.Timeout(connect=10, read=300, write=60, pool=10)

# Runs only when the user executes this test file. One worker shares the cached
# models across both endpoints. Framework settings apply only to this child.
SERVER_SCRIPT = """
import sys
import torch
import tensorflow as tf
import uvicorn

torch.set_num_threads(2)
torch.set_num_interop_threads(1)
tf.config.set_visible_devices([], 'GPU')
tf.config.threading.set_intra_op_parallelism_threads(2)
tf.config.threading.set_inter_op_parallelism_threads(1)
from app.services.caries_prediction import load_models
load_models()
uvicorn.run('app.main:app', host='127.0.0.1', port=int(sys.argv[1]),
            workers=1, access_log=False, log_level='warning')
"""


@pytest.fixture(scope="module")
def performance_client(tmp_path_factory):
    assert IMAGE_PATH.is_file(), f"Missing reference image: {IMAGE_PATH}"
    for filename in ("best.pt", "mobilenetv2.keras", "efficientnetb0.keras"):
        path = ROOT / "models" / filename
        assert path.is_file(), f"Missing trained model: {path}"
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    environment = os.environ.copy()
    environment.update({
        "CUDA_VISIBLE_DEVICES": "-1", "OMP_NUM_THREADS": "2",
        "MKL_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2",
        "TF_NUM_INTRAOP_THREADS": "2", "TF_NUM_INTEROP_THREADS": "1",
    })
    log_path = tmp_path_factory.mktemp("performance") / "server.log"
    with log_path.open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-c", SERVER_SCRIPT, str(port)],
            cwd=ROOT / "backend", env=environment, stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}",
                              timeout=REQUEST_TIMEOUT, trust_env=False) as client:
                deadline = time.monotonic() + 300
                while time.monotonic() < deadline:
                    if server.poll() is not None:
                        pytest.fail(f"Performance server exited; see {log_path}")
                    try:
                        health = client.get("/health", timeout=2)
                        if health.status_code == 200 and health.json() == {"status": "ok"}:
                            break
                    except httpx.RequestError:
                        pass
                    time.sleep(0.2)
                else:
                    pytest.fail(f"Server not ready after 300 seconds; see {log_path}")
                yield client
        finally:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=15)


def validate_prediction(body):
    assert set(body) == {"image", "total_regions", "regions"}
    assert body["image"] == IMAGE_PATH.name
    assert isinstance(body["regions"], list)
    assert body["total_regions"] == len(body["regions"]) > 0
    with Image.open(IMAGE_PATH) as image:
        width, height = image.size
    for number, region in enumerate(body["regions"], start=1):
        assert region["region"] == number
        x1, y1, x2, y2 = region["bounding_box"]
        assert 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height
        assert 0 <= region["detection_confidence"] <= 1
        for name in ("MobileNetV2", "EfficientNetB0"):
            assert region[name]["prediction"] in CLASS_NAMES
            assert 0 <= region[name]["confidence"] <= 1
        mobile = region["MobileNetV2"]["prediction"]
        efficient = region["EfficientNetB0"]["prediction"]
        assert region["status"] == (
            "Agreement" if mobile == efficient else "Uncertain - Review Required"
        )
        assert region["final_prediction"] == (mobile if mobile == efficient else "Uncertain")


def validate_gradcam(body):
    assert set(body) == {"region", "MobileNetV2", "EfficientNetB0"}
    assert body["region"] == 1
    for name in ("MobileNetV2", "EfficientNetB0"):
        result = body[name]
        assert set(result) == {"predicted_class", "heatmap_shape", "overlay"}
        assert type(result["predicted_class"]) is int
        assert 0 <= result["predicted_class"] < 3
        assert len(result["heatmap_shape"]) == 2
        assert all(type(size) is int and size > 0 for size in result["heatmap_shape"])
        prefix = "data:image/png;base64,"
        assert result["overlay"].startswith(prefix)
        png = base64.b64decode(result["overlay"][len(prefix):], validate=True)
        with Image.open(io.BytesIO(png)) as overlay:
            assert overlay.format == "PNG" and overlay.size == (224, 224)
            overlay.verify()


@pytest.mark.parametrize("endpoint", ["predict", "gradcam"])
def test_real_api_response_times(performance_client, record_property, endpoint):
    payload = IMAGE_PATH.read_bytes()
    durations = []
    for request_number in range(1, 4):
        started = time.perf_counter()
        response = performance_client.post(
            f"/api/caries/{endpoint}",
            files={"file": (IMAGE_PATH.name, payload, "image/jpeg")},
            data={"region": "1"} if endpoint == "gradcam" else {},
        )
        elapsed = time.perf_counter() - started
        durations.append(elapsed)
        record_property(f"{endpoint}_request_{request_number}_seconds", elapsed)
        print(f"\n{endpoint} request {request_number}: {elapsed:.3f} seconds")
        assert response.status_code == 200, response.text
        validator = validate_prediction if endpoint == "predict" else validate_gradcam
        validator(response.json())
    average = statistics.mean(durations)
    record_property(f"{endpoint}_average_seconds", average)
    print(f"\n{endpoint} average over 3 requests: {average:.3f} seconds")
