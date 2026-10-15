"""Code-only B1 runtime evidence runner; generated tests, no installs/downloads.

Default verification is strict. --local-diagnostic documents unavailable local
backends but can NEVER produce PASS or replace actual Colab execution.
"""
from hashlib import sha256
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import traceback
import xml.etree.ElementTree as ET


TARGET = "tests/test_colour_b1_prototype.py"
BACKEND_TESTS = ["test_resnet50_unclipped_forward_weights_none",
                 "test_resnet50_gradcam_frozen_backbone_hooks_and_alignment_weights_none"]
EXPECTED_CASES = 77


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def source_hashes(root, files):
    hashes = {}
    for name in files:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing/unsafe required code file: " + name)
        hashes[name] = sha256(path.read_bytes()).hexdigest()
    return hashes


def environment_check(require_backend):
    """Probe real imports/CPU binary compatibility, never version numbers alone."""
    versions = {"python": platform.python_version(), "platform": platform.platform(),
                "executable": sys.executable, "execution_device": "cpu"}
    failures = []
    for package in ("numpy", "Pillow", "pytest", "torch", "torchvision"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    for name in ("numpy", "PIL", "pytest"):
        try:
            importlib.import_module(name)
        except Exception as error:
            failures.append(name + ": " + type(error).__name__ + ": " + str(error))
    try:
        from PIL import features, ImageCms
        versions["littlecms2"] = features.version("littlecms2")
        ImageCms.createProfile("sRGB")
    except Exception as error:
        failures.append("Pillow CMS: " + type(error).__name__ + ": " + str(error))
    backend_errors = []
    try:
        import torch
        import torchvision
        torch.set_num_threads(1)
        versions["torch_runtime"] = torch.__version__
        versions["torchvision_runtime"] = torchvision.__version__
        # CPU nms checks the torch/torchvision compiled operator pairing.
        boxes = torch.tensor([[0., 0., 1., 1.]], device="cpu")
        scores = torch.tensor([1.], device="cpu")
        result = torchvision.ops.nms(boxes, scores, .5)
        if result.tolist() != [0] or not callable(torchvision.models.resnet50):
            raise RuntimeError("CPU torch/torchvision compatibility probe failed")
        versions["cpu_binary_compatibility"] = "PASS"
        def block_download(*args, **kwargs):
            raise RuntimeError("Weight/network downloads are forbidden in B1 verification")
        torch.hub.download_url_to_file = block_download
        torch.hub.load_state_dict_from_url = block_download
    except Exception as error:
        backend_errors.append(type(error).__name__ + ": " + str(error))
        versions["cpu_binary_compatibility"] = "FAIL"
    versions["backend_errors"] = backend_errors
    if require_backend:
        failures.extend(backend_errors)
    versions["dependency_errors"] = failures
    return versions


def junit_summary(path):
    cases = list(ET.parse(path).iter("testcase")) if path.is_file() else []
    counts = {"total": len(cases), "failed": 0, "errors": 0, "skipped": 0, "passed": 0}
    backend = {name: "missing" for name in BACKEND_TESTS}
    for case in cases:
        status = ("failed" if case.find("failure") is not None else
                  "errors" if case.find("error") is not None else
                  "skipped" if case.find("skipped") is not None else "passed")
        counts[status] += 1
        name = case.get("name")
        if name in backend:
            backend[name] = status if backend[name] == "missing" else "duplicate"
    return counts, backend


def acceptance(counts, backend, exit_code, unchanged, isolated, dependency_ok):
    """All conditions required; no skip/partial-run may become a PASS."""
    return (counts == {"total": EXPECTED_CASES, "passed": EXPECTED_CASES,
                       "failed": 0, "errors": 0, "skipped": 0}
            and set(backend) == set(BACKEND_TESTS) and all(v == "passed" for v in backend.values())
            and exit_code == 0 and unchanged and isolated and dependency_ok)


class ExactCollection:
    def __init__(self, evidence):
        self.evidence = evidence

    def pytest_collection_finish(self, session):
        import pytest
        nodes = [item.nodeid for item in session.items]
        write_json(self.evidence / "collected_tests.json", nodes)
        required = {TARGET + "::" + name for name in BACKEND_TESTS}
        if len(nodes) != EXPECTED_CASES or len(set(nodes)) != EXPECTED_CASES or not required <= set(nodes):
            raise pytest.UsageError("Expected exact 77 B1 cases including both backend tests; STOP")


def main(root, *, local_diagnostic=False):
    root = Path(root).resolve()
    evidence = root / "synthetic_evidence"
    evidence.mkdir(exist_ok=False)
    expected = {}
    result = {"status": "FAIL", "scope": "generated-only B1 runtime verification",
              "local_diagnostic": local_diagnostic, "RUN_PILOT": False,
              "real_images_accessed": False, "training_performed": False,
              "pretrained_weights": None, "production_active": False,
              "colab_execution_claimed_by_this_preparation": False}
    before, after, versions = {}, {}, {}
    try:
        manifest = json.loads((root / "code_manifest.json").read_text())
        expected = manifest["files"]
        if (manifest["test_target"] != TARGET or manifest["expected_cases"] != EXPECTED_CASES
                or manifest["backend_tests"] != BACKEND_TESTS):
            raise ValueError("Stale or unexpected test manifest")
        before = source_hashes(root, expected)
        write_json(evidence / "source_hashes_before.json", before)
        if before != expected:
            raise ValueError("Code hashes differ from pinned manifest")
        versions = environment_check(require_backend=not local_diagnostic)
        write_json(evidence / "environment.json", versions)
        if versions["dependency_errors"]:
            raise RuntimeError("Dependencies unavailable/incompatible; STOP, do not auto-install: "
                               + "; ".join(versions["dependency_errors"]))
        sys.path.insert(0, str(root))
        import pytest
        # No repo/global config, conftest, plugins, cache, bytecode or path fallback.
        exit_code = int(pytest.main([TARGET, "-q", "-rs", "-p", "no:cacheprovider", "-c", os.devnull,
                                    "--rootdir=" + str(root), "--confcutdir=" + str(root),
                                    "--basetemp=" + str(root / "generated_tmp"),
                                    "--junitxml=" + str(evidence / "junit.xml")],
                                   plugins=[ExactCollection(evidence)]))
        counts, backend = junit_summary(evidence / "junit.xml")
        origins = {name: str(Path(module.__file__).resolve()) for name, module in list(sys.modules.items())
                   if (name.startswith("src.vision.") or name == "test_colour_b1_prototype")
                   and getattr(module, "__file__", None)}
        isolated = bool(origins) and all(Path(value).is_relative_to(root) for value in origins.values())
        write_json(evidence / "import_origins.json", origins)
        after = source_hashes(root, expected)
        unchanged = before == after == expected
        passed = acceptance(counts, backend, exit_code, unchanged, isolated,
                            not versions["backend_errors"])
        # Diagnostic mode is explicitly non-authoritative, even on a capable host.
        result.update(counts=counts, backend_tests=backend, pytest_exit_code=exit_code,
                      imports_isolated=isolated, source_unchanged=unchanged,
                      acceptance_passed=passed and not local_diagnostic,
                      status="PASS" if passed and not local_diagnostic else "INCOMPLETE" if local_diagnostic else "FAIL")
    except Exception as error:
        result["blocker"] = type(error).__name__ + ": " + str(error)
        print(result["blocker"], flush=True)
        traceback.print_exc()
    finally:
        if expected:
            try:
                after = source_hashes(root, expected)
            except Exception as error:
                result["post_hash_error"] = type(error).__name__ + ": " + str(error)
        result["source_unchanged"] = bool(before) and before == after == expected
        if not result["source_unchanged"]:
            result["status"] = "FAIL"
            result["acceptance_passed"] = False
        write_json(evidence / "source_hashes_after.json", after)
        write_json(evidence / "verification.json", result)
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result["status"] == "PASS" else 3


if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--local-diagnostic"):
        raise SystemExit("Usage: verify_b1_runtime.py EXTRACTED_ROOT [--local-diagnostic]")
    raise SystemExit(main(sys.argv[1], local_diagnostic=len(sys.argv) == 3))
