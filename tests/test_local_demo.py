"""HTTP behaviour with generated questionnaire data; no real participants."""

import hashlib
import http.client
import json
import threading

import joblib
import pytest

from test_questionnaire_explain import generated_inputs
from test_saved_pilot_demo import generated_archive
from src.tabular import local_demo
from src.tabular.questionnaire_explain import EXAMPLE_PROFILE, QuestionnairePrototype, fit_support
from src.tabular.xgboost_comparison_nhanes import make_xgboost_pipeline
from src.vision.saved_pilot_demo import prepare_saved_examples


@pytest.fixture(scope="module")
def server():
    x, y = generated_inputs()
    model = make_xgboost_pipeline(("Full", "A"))
    model.fit(x, y)
    prototype = QuestionnairePrototype(model, fit_support(x), {"final_model": False, "held_out_evaluated": False})
    service = local_demo.make_server(prototype, port=0)
    thread = threading.Thread(target=service.serve_forever, daemon=True)
    thread.start()
    yield service, prototype
    service.shutdown()
    service.server_close()
    thread.join()


def request(server, path, data=None, extra=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    headers = {"Content-Type": "application/json", "X-Component2-Demo": "1", **(extra or {})}
    connection.request("GET" if data is None else "POST", path, None if data is None else json.dumps(data), headers)
    response = connection.getresponse()
    raw = response.read()
    result = json.loads(raw) if response.getheader("Content-Type").startswith("application/json") else raw
    status = response.status
    connection.close()
    return status, result


def test_prediction_scenario_reset_and_error_routes(server):
    service, prototype = server
    code, predicted = request(service, "/api/predict", {"profile": EXAMPLE_PROFILE})
    assert code == 200 and len(predicted["contributions"]) == 12
    payload = {"original": EXAMPLE_PROFILE, "model_id": prototype.model_id}
    code, scenario = request(service, "/api/what-if", {**payload, "changes": {"OHQ870": 7}})
    assert code == 200 and scenario["original"] == predicted
    code, reset = request(service, "/api/reset", payload)
    assert code == 200 and reset["scenario"] == predicted
    assert request(service, "/api/predict", {"profile": {**EXAMPLE_PROFILE, "OHQ850": 1}})[0] == 422
    assert request(service, "/api/what-if", {**payload, "changes": {"RIDAGEYR": 40}})[0] == 422
    assert request(service, "/api/reset", {**payload, "model_id": "stale"})[0] == 422
    assert request(service, "/api/predict", {"profile": {**EXAMPLE_PROFILE, "INDFMPIR": float("nan")}})[0] == 422


def test_local_only_server_and_no_arbitrary_file_routes(server):
    service, _ = server
    assert service.server_address[0] == "127.0.0.1"
    assert request(service, "/api/schema")[0] == 200
    assert request(service, "/api/predict", {"profile": EXAMPLE_PROFILE}, {"Origin": "https://untrusted.example"})[0] == 403
    assert request(service, "/api/predict", {"profile": EXAMPLE_PROFILE}, {"X-Component2-Demo": "0"})[0] == 415
    assert request(service, "/api/schema", extra={"Host": "untrusted.example"})[0] == 403
    for path in ("/../../AGENTS.md", "/vision/../../data/Test.png", "/models/model.joblib", "/api/test"):
        assert request(service, path)[0] == 404
    assert request(service, "/api/vision")[0] == 503


def test_model_hash_checked_before_deserialization(tmp_path, server, monkeypatch):
    _, prototype = server
    path = tmp_path / "own_generated.joblib"
    joblib.dump(prototype, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert local_demo.load_verified_prototype(path, digest).model_id == prototype.model_id
    monkeypatch.setattr(local_demo.joblib, "load", lambda *_: pytest.fail("Do not deserialize tampered bytes"))
    with pytest.raises(ValueError, match="hash mismatch"):
        local_demo.load_verified_prototype(path, "0" * 64)


def test_saved_manifest_and_view_tampering_rejected(tmp_path, monkeypatch):
    archive, digest = generated_archive(tmp_path)
    directory = tmp_path / "saved"
    prepare_saved_examples(archive, directory, digest)
    # Only the synthetic archive hash replaces the published result binding here.
    monkeypatch.setattr("src.vision.saved_pilot_demo.ARCHIVE_SHA256", digest)
    manifest_hash = hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
    manifest, assets = local_demo.load_vision_assets(directory, manifest_hash)
    assert len(assets) == 9
    with pytest.raises(ValueError, match="manifest hash"):
        local_demo.load_vision_assets(directory, "0" * 64)
    (directory / next(iter(assets))).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="view hash"):
        local_demo.load_vision_assets(directory, manifest_hash)
