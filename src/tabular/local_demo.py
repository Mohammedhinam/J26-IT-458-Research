"""Local-only PP1 interface: live questionnaire, separate saved Vision evidence.

Run: .venv/bin/python -B -m src.tabular.local_demo
This standard-library development server is not a deployment server.
"""

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

import joblib

from .audit_nhanes import ROOT
from .questionnaire_explain import CAT_CODES, EXAMPLE_PROFILE, FEATURE_LABELS, FEATURES, NOTICE


MODEL_PATH = ROOT / "models/questionnaire_pp1_v1/model.joblib"
MODEL_SHA256 = "c3f7458d1f6681fb4db18aa9d064a9d69baa75b16e634daa262210cbd91a9213"
VISION_DIR = ROOT / "data/pp1_demo_saved_vision_v1"
PAGE = ROOT / "docs/component2_local_demo_v1.html"
OPTIONS = {
    "RIAGENDR": ["Male", "Female"],
    "DMDEDUC2": ["Less than 9th grade", "9–11th grade / no high-school diploma", "High school / GED",
                  "Some college / associate degree", "College graduate or above"],
    "DMDMARTZ": ["Married / living with partner", "Widowed / divorced / separated", "Never married"],
    "OHQ030": ["6 months or less", "Over 6 months to 1 year", "Over 1 to 2 years", "Over 2 to 3 years",
               "Over 3 to 5 years", "More than 5 years", "Never visited"],
    "OHQ845": ["Excellent", "Very good", "Good", "Fair", "Poor"],
    "OHQ860": ["Yes", "No"], "OHQ835": ["Yes", "No"], "DIQ010": ["Yes", "No", "Borderline"],
    "SMOKING_STATUS": ["Fewer than 100 lifetime cigarettes", "Former smoker", "Current smoker"],
}


def load_verified_prototype(path=MODEL_PATH, expected_sha256=MODEL_SHA256):
    """Deserialize only the locally generated, explicitly hash-pinned artifact."""
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("Local reference model hash mismatch; do not load")
    prototype = joblib.load(path)
    if prototype.provenance.get("final_model") is not False or prototype.provenance.get("held_out_evaluated") is not False:
        raise ValueError("Expected a development-only reference bundle")
    return prototype


def load_vision_assets(directory=VISION_DIR, expected_manifest_sha256=None):
    """Serve only nine verified saved views, never arbitrary files or checkpoints."""
    from src.vision.saved_pilot_demo import ARCHIVE_SHA256, CASE_IDS, VIEWS, check_preview_png
    directory = Path(directory)
    if expected_manifest_sha256 is None:
        receipt = json.loads((ROOT / "docs/component2_demo_assets_receipt_v1.json").read_text())
        expected_manifest_sha256 = receipt["saved_vision_manifest_sha256"]
    raw_manifest = (directory / "manifest.json").read_bytes()
    if hashlib.sha256(raw_manifest).hexdigest() != expected_manifest_sha256:
        raise ValueError("Saved Vision manifest hash mismatch")
    manifest = json.loads(raw_manifest)
    expected = {f"{case}_{view}.png" for case in CASE_IDS for view in VIEWS}
    if set(manifest["files"]) != expected or manifest["source_archive_sha256"] != ARCHIVE_SHA256:
        raise ValueError("Unexpected saved Vision membership/provenance")
    assets = {}
    for name, digest in manifest["files"].items():
        payload = (directory / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("Saved Vision view hash mismatch")
        check_preview_png(payload)
        assets[name] = payload
    return manifest, assets


def make_server(prototype, port=8765, vision=None, vision_assets=None, vision_runtime=None):
    """Bind loopback, expose fixed routes, and never record submitted profiles."""
    lock = threading.Lock()
    assets = {} if vision_assets is None else dict(vision_assets)
    schema = {"notice": NOTICE, "model_id": prototype.model_id, "example": EXAMPLE_PROFILE,
              "fields": [{"key": field, "label": FEATURE_LABELS[field],
                          "options": list(zip((str(c) for c in CAT_CODES[field]), OPTIONS[field])) if field in CAT_CODES else None}
                         for field in FEATURES]}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Avoid profile/request logging in a personal demo.

        def send(self, status, payload, kind="application/json; charset=utf-8"):
            data = json.dumps(payload, allow_nan=False).encode() if isinstance(payload, (dict, list)) else payload
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def allowed_host(self):
            port = self.server.server_port
            return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def do_GET(self):
            if not self.allowed_host():
                return self.send(403, {"error": "Loopback host required"})
            if self.path == "/favicon.ico":
                return self.send(204, b"", "image/x-icon")
            if self.path == "/":
                return self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/schema":
                return self.send(200, schema)
            if self.path == "/api/vision":
                return self.send(200 if vision is not None else 503, vision or {"error": "Saved Vision views not prepared"})
            if self.path == "/api/vision/runtime":
                status = vision_runtime.status() if vision_runtime is not None else {
                    "ready": False, "synthetic_only": False,
                    "message": "New-photo runtime is not enabled. Saved pilot examples remain available.",
                    "healthy_mgi0_supported": False,
                }
                return self.send(200, status)
            if self.path.startswith("/vision/") and self.path[len("/vision/"):] in assets:
                return self.send(200, assets[self.path[len("/vision/"):]], "image/png")
            return self.send(404, {"error": "Unknown route"})

        def do_POST(self):
            if not self.allowed_host():
                return self.send(403, {"error": "Loopback host required"})
            origin = self.headers.get("Origin")
            if origin is not None and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
                return self.send(403, {"error": "Same-origin request required"})
            if self.path == "/api/vision/photo":
                return self.photo_request()
            if self.headers.get("X-Component2-Demo") != "1" or self.headers.get_content_type() != "application/json":
                return self.send(415, {"error": "Use the local JSON demo interface"})
            if self.path not in ("/api/predict", "/api/what-if", "/api/reset"):
                return self.send(404, {"error": "Unknown route"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192:
                    return self.send(413, {"error": "Invalid request size"})

                def reject_constant(value):
                    raise ValueError("Non-finite JSON number: " + value)

                request = json.loads(self.rfile.read(length), parse_constant=reject_constant)
                if not isinstance(request, dict):
                    raise ValueError("Expected an object")
                with lock:
                    if self.path == "/api/predict":
                        if set(request) != {"profile"}:
                            raise ValueError("Expected profile only")
                        result = prototype.predict(request["profile"])
                    else:
                        required = {"original", "model_id"} | ({"changes"} if self.path == "/api/what-if" else set())
                        if set(request) != required:
                            raise ValueError("Unexpected scenario fields")
                        changes = request.get("changes", {})
                        result = prototype.simulate(request["original"], changes, request["model_id"])
                return self.send(200, result)
            except (ValueError, TypeError, KeyError) as error:
                return self.send(422, {"error": str(error)})
            except Exception:
                return self.send(500, {"error": "Prediction/explanation failed; no result returned"})

        def photo_request(self):
            # Runtime stays opt-in. Do not read or save a photo when inactive.
            if vision_runtime is None or not vision_runtime.status().get("ready"):
                return self.send(503, {"error": "New-photo runtime is not enabled; no image processed"})
            if self.headers.get("X-Component2-Demo") != "1" or self.headers.get_content_type() != "image/jpeg":
                return self.send(415, {"error": "Use the local RGB JPEG interface"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8 * 1024 * 1024:
                    return self.send(413, {"error": "Photo must be at most 8 MiB"})
                payload = self.rfile.read(length)
                if len(payload) != length:
                    raise ValueError("Incomplete image payload")
                with lock:
                    result = vision_runtime.explain(payload)
                return self.send(200, result)
            except (ValueError, TypeError, KeyError, OSError) as error:
                return self.send(422, {"error": str(error)})
            except Exception:
                return self.send(500, {"error": "Vision explanation failed; no result returned"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    prototype = load_verified_prototype()
    vision, assets = load_vision_assets()
    server = make_server(prototype, args.port, vision, assets)
    print(f"Local PP1 demo: http://127.0.0.1:{server.server_port} — Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
