"""Generated registration/configuration tests; no dental files or checkpoint loads."""

from hashlib import sha256
import http.client
import json
import socket
import threading
import time
from types import SimpleNamespace

import pytest
import uvicorn

from src.vision import live_photo_demo as live
from src.vision import photo_explanation as photo


def registration(scope="generated_verification"):
    generated = scope == "generated_verification"
    return {
        "version": "pp1-live-photo-registration-v1",
        "scope": scope,
        "checkpoint_sha256": photo.V3_CHECKPOINT_SHA,
        "profile_sha256": "1" * 64 if generated else photo.QUALIFIED_PROFILE_SHA,
        "inputs": {sha256(b"generated jpeg fixture").hexdigest():
                   "generated" if generated else "owner_supplied_nonstudy"},
        "provenance": {"kind": "generated"} if generated else {
            "kind": "owner_supplied_nonstudy", "reviewer": "Generated reviewer fixture",
            "date": "2026-10-17", "evidence_reference": "generated-only-owner-record",
        },
    }


def save_registration(tmp_path, value):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode("utf-8")
    path = tmp_path / "generated_registration.json"
    path.write_bytes(raw)
    return path, sha256(raw).hexdigest()


@pytest.mark.parametrize("scope", ["generated_verification", "local_nonstudy_demo"])
def test_exact_versioned_registration_is_returned_without_source_reads(tmp_path, scope):
    expected = registration(scope)
    path, digest = save_registration(tmp_path, expected)
    assert live.VERSION == expected["version"]
    assert live.load_registration(path, digest) == expected
    assert sha256(path.read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("digest", [None, "", "0" * 64, "A" * 64, "g" * 64])
def test_absent_stale_or_malformed_trusted_hash_rejected(tmp_path, digest):
    path, _ = save_registration(tmp_path, registration())
    with pytest.raises((ValueError, OSError)):
        live.load_registration(path, digest)


@pytest.mark.parametrize("fault", [
    "version", "scope", "checkpoint", "profile", "empty_inputs", "bad_input_hash",
    "wrong_origin", "extra_field", "missing_field", "provenance_kind",
    "provenance_extra", "inputs_list", "provenance_list",
])
def test_generated_registration_contract_fails_closed(tmp_path, fault):
    value = registration()
    if fault == "version": value["version"] = "stale-version"
    if fault == "scope": value["scope"] = "train_or_study_inference"
    if fault == "checkpoint": value["checkpoint_sha256"] = "0" * 64
    if fault == "profile": value["profile_sha256"] = "not-a-hash"
    if fault == "empty_inputs": value["inputs"] = {}
    if fault == "bad_input_hash": value["inputs"] = {"not-a-hash": "generated"}
    if fault == "wrong_origin": value["inputs"] = {"2" * 64: "owner_supplied_nonstudy"}
    if fault == "extra_field": value["labels_approved"] = True
    if fault == "missing_field": del value["provenance"]
    if fault == "provenance_kind": value["provenance"] = {"kind": "owner_supplied_nonstudy"}
    if fault == "provenance_extra": value["provenance"]["clinical_approval"] = True
    if fault == "inputs_list": value["inputs"] = []
    if fault == "provenance_list": value["provenance"] = []
    path, digest = save_registration(tmp_path, value)
    with pytest.raises((ValueError, OSError)):
        live.load_registration(path, digest)


@pytest.mark.parametrize("fault", [
    "profile", "origin", "reviewer", "reviewer_whitespace", "date",
    "impossible_date", "evidence", "extra_provenance", "missing_provenance",
])
def test_nonstudy_scope_requires_pinned_profile_and_complete_provenance(tmp_path, fault):
    value = registration("local_nonstudy_demo")
    if fault == "profile": value["profile_sha256"] = "1" * 64
    if fault == "origin": value["inputs"] = {"2" * 64: "generated"}
    if fault == "reviewer": value["provenance"]["reviewer"] = ""
    if fault == "reviewer_whitespace": value["provenance"]["reviewer"] = "   "
    if fault == "date": value["provenance"]["date"] = "October 17"
    if fault == "impossible_date": value["provenance"]["date"] = "2026-02-30"
    if fault == "evidence": value["provenance"]["evidence_reference"] = ""
    if fault == "extra_provenance": value["provenance"]["labels_approved"] = True
    if fault == "missing_provenance": del value["provenance"]["reviewer"]
    path, digest = save_registration(tmp_path, value)
    with pytest.raises((ValueError, OSError)):
        live.load_registration(path, digest)


@pytest.mark.parametrize("payload", [
    b"not json", b"[]", b"null", b'{"version":1,"version":2}',
    b'{"provenance":{"kind":"generated","kind":"other"}}',
    b'{"inputs":{"same":"generated","same":"generated"}}',
    b'{"version":NaN}', b'\xff', b" " * (64 * 1024 + 1),
])
def test_malformed_duplicate_nonfinite_or_oversized_json_rejected(tmp_path, payload):
    path, digest = save_registration(tmp_path, payload)
    with pytest.raises((ValueError, OSError, UnicodeError)):
        live.load_registration(path, digest)


@pytest.mark.parametrize("level", ["root", "inputs", "provenance"])
def test_duplicate_fields_rejected_in_otherwise_valid_registration(tmp_path, level):
    value = registration()
    raw = json.dumps(value)
    if level == "root":
        text = json.dumps(value["version"])
        raw = raw.replace('"version": ' + text, '"version": ' + text + ', "version": ' + text)
    elif level == "inputs":
        key = next(iter(value["inputs"]))
        text = json.dumps(key) + ': "generated"'
        raw = raw.replace(text, text + ', ' + text)
    else:
        text = '"kind": "generated"'
        raw = raw.replace(text, text + ', ' + text)
    path, digest = save_registration(tmp_path, raw.encode("utf-8"))
    with pytest.raises((ValueError, OSError)):
        live.load_registration(path, digest)


def test_missing_and_symlink_registration_rejected(tmp_path):
    with pytest.raises((ValueError, OSError)):
        live.load_registration(tmp_path / "missing.json", "1" * 64)
    path, digest = save_registration(tmp_path, registration())
    link = tmp_path / "linked.json"
    link.symlink_to(path)
    with pytest.raises((ValueError, OSError)):
        live.load_registration(link, digest)


@pytest.mark.parametrize("scope", ["generated_verification", "local_nonstudy_demo"])
def test_runtime_loader_receives_validated_scope_and_profile_only(tmp_path, monkeypatch, scope):
    value = registration(scope)
    path, digest = save_registration(tmp_path, value)
    calls = []

    def load(checkpoint, inputs, *, synthetic_only=False):
        calls.append((checkpoint, inputs, synthetic_only))
        return photo.PhotoRuntime(None, None, photo.V3_CHECKPOINT_SHA, inputs,
                                  synthetic_only=synthetic_only)

    monkeypatch.setattr(photo, "load_v3_runtime", load)
    checkpoint = tmp_path / "not-opened-generated-checkpoint.pt"
    runtime = live.build_runtime(checkpoint, path, digest)
    assert calls == [(checkpoint, value["inputs"], scope == "generated_verification")]
    assert runtime.profile_sha256 == value["profile_sha256"]
    assert runtime.synthetic_only is (scope == "generated_verification")
    assert dict(runtime.allowed_inputs) == value["inputs"]
    assert not checkpoint.exists()


def test_bad_registration_stops_before_checkpoint_loader(tmp_path, monkeypatch):
    path, _ = save_registration(tmp_path, registration())
    monkeypatch.setattr(photo, "load_v3_runtime",
                        lambda *_args, **_kwargs: pytest.fail("Checkpoint was reached"))
    with pytest.raises((ValueError, OSError)):
        live.build_runtime(tmp_path / "unused.pt", path, "0" * 64)


@pytest.mark.parametrize("raw,expected_status", [
    (b"generated jpeg fixture", 200), (b"unregistered", 422), (b"invalid-jpeg", 422),
])
def test_generated_runtime_injected_into_existing_local_photo_route(tmp_path, monkeypatch, raw, expected_status):
    """One generated payload exercises registration -> API without model/data IO."""
    from src.tabular import api

    payload = b"generated jpeg fixture"
    path, digest = save_registration(tmp_path, registration())

    class Runtime(photo.PhotoRuntime):
        def status(self): return {"ready": True, "synthetic_only": True}

        def explain(self, raw):
            if raw == b"invalid-jpeg": raise OSError("private generated decoder diagnostic")
            if raw != payload: raise ValueError("Unregistered generated fixture")
            return {"synthetic_only": True, "predicted_grade": 2, "explained_grade": 2}

    def load(_checkpoint, inputs, *, synthetic_only=False):
        return Runtime(None, None, photo.V3_CHECKPOINT_SHA, inputs, synthetic_only=synthetic_only)

    monkeypatch.setattr(photo, "load_v3_runtime", load)
    runtime = live.build_runtime(tmp_path / "not-opened.pt", path, digest)
    app = api.create_app(SimpleNamespace(model_id="generated"), vision_runtime=runtime)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                           access_log=False, log_level="critical"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started: break
            time.sleep(.01)
        assert server.started
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        connection.request("POST", "/api/vision/photo", raw, {
            "Content-Type": "image/jpeg", "X-Component2-Demo": "1",
        })
        response = connection.getresponse()
        result = json.loads(response.read())
        assert response.status == expected_status
        if expected_status == 200:
            assert result["synthetic_only"] is True
            assert result["predicted_grade"] == result["explained_grade"] == 2
        if raw == b"invalid-jpeg":
            assert result == {"error": "Invalid or unsupported JPEG payload"}
            assert "private" not in json.dumps(result)
        connection.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize("flag,value", [
    ("--vision-checkpoint", "generated.pt"),
    ("--vision-registration", "generated.json"),
    ("--vision-registration-sha256", "1" * 64),
])
def test_partial_cli_bindings_rejected_before_any_model_load(monkeypatch, capsys, flag, value):
    from src.tabular import api

    monkeypatch.setattr("sys.argv", ["component2-demo", flag, value])
    monkeypatch.setattr(live, "build_runtime",
                        lambda *_args: pytest.fail("Partial registration reached runtime loader"))
    monkeypatch.setattr(api.local, "load_verified_prototype",
                        lambda: pytest.fail("Partial registration reached questionnaire loader"))
    monkeypatch.setattr(uvicorn, "run",
                        lambda *_args, **_kwargs: pytest.fail("Partial registration started a server"))
    with pytest.raises(SystemExit) as stopped:
        api.main()
    assert stopped.value.code == 2
    assert "All three --vision-* bindings are required together" in capsys.readouterr().err
