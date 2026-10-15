"""Actual focused synthetic evidence; never initiates real pilot training."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

from src.vision import exploratory_bundle as legacy


BACKENDS = (
    "test_weighted_mean_matches_independent_reference_and_all_one_gradients",
    "test_weighted_resnet_step_keeps_initialization_backbone_and_batchnorm",
    "test_generated_weighted_fit_checkpoint_probabilities_and_reproducibility",
    "test_weighted_epoch_uses_weight_sum_and_validation_does_not_update")
TEST_FILE = "tests/test_exploratory_pilot_b1_balanced_v2.py"


def snapshot(root, files):
    return {name: legacy.sha256(legacy.safe_file(root, name)) for name in files}


def case_results(xml_path):
    cases = ET.parse(xml_path).getroot().findall(".//testcase")
    ids = [case.get("classname", "") + "::" + case.get("name", "") for case in cases]
    counts = {"total": len(cases), "failed": sum(c.find("failure") is not None for c in cases),
              "errors": sum(c.find("error") is not None for c in cases),
              "skipped": sum(c.find("skipped") is not None for c in cases)}
    counts["passed"] = counts["total"] - counts["failed"] - counts["errors"] - counts["skipped"]
    backends = {name: any(c.get("name") == name and not any(
        c.find(tag) is not None for tag in ("failure", "error", "skipped")) for c in cases) for name in BACKENDS}
    return ids, counts, backends


def require_pass(evidence_directory):
    """Check actual XML, payload hashes and unchanged sources, not a PASS bool alone."""
    directory = Path(evidence_directory)
    root = Path(__file__).resolve().parents[2]
    code_manifest = json.loads(legacy.safe_file(root, "verification_manifest.json").read_text())
    expected = code_manifest["files"]
    receipt = json.loads(legacy.safe_file(directory, "evidence_manifest.json").read_text())
    names = {"summary.json", "junit.xml", "pytest.log", "source_hashes_before.json", "source_hashes_after.json"}
    if set(receipt["files"]) != names:
        raise ValueError("Synthetic evidence payload coverage mismatch")
    for name, digest in receipt["files"].items():
        if legacy.sha256(legacy.safe_file(directory, name)) != digest:
            raise ValueError("Synthetic evidence payload changed")
    summary = json.loads((directory / "summary.json").read_text())
    ids, counts, backends = case_results(directory / "junit.xml")
    before = json.loads((directory / "source_hashes_before.json").read_text())
    after = json.loads((directory / "source_hashes_after.json").read_text())
    if (len(ids) != len(set(ids)) or sorted(ids) != sorted(code_manifest["expected_case_ids"])
            or counts["failed"] or counts["errors"] or counts["skipped"] or not all(backends.values())
            or summary.get("pytest_exit_code") != 0 or summary.get("status") != "PASS"
            or summary.get("counts") != counts or before != expected or after != expected
            or snapshot(root, expected) != expected):
        raise ValueError("All exact focused cases/backends must pass with unchanged code; no skips")
    return legacy.sha256(directory / "evidence_manifest.json")


def run(root):
    root = Path(root)
    directory = root / "balanced_synthetic_evidence_v2"
    directory.mkdir(mode=0o700, exist_ok=False)
    manifest = json.loads((root / "verification_manifest.json").read_text())
    before = snapshot(root, manifest["files"])
    if before != manifest["files"]:
        raise ValueError("Code hash mismatch before synthetic tests")
    environment = {"python": platform.python_version(), "platform": platform.system()}
    error = None
    for name in ("torch", "torchvision", "numpy", "Pillow", "pytest"):
        try:
            environment[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            environment[name] = None
    try:
        import torch
        import torchvision
        torch.set_num_threads(1)
        torchvision.ops.nms(torch.tensor([[0., 0., 1., 1.]]), torch.tensor([1.]), .5)
        environment.update(cuda_available=torch.cuda.is_available(),
                           gpu=torch.cuda.get_device_name() if torch.cuda.is_available() else None)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    if error:
        summary = {"status": "STOP_DEPENDENCY", "dependency_error": error, "environment": environment}
        (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        return summary
    process = subprocess.run([sys.executable, "-B", "-m", "pytest", TEST_FILE, "-q", "-p", "no:cacheprovider",
                              "--junitxml=" + str(directory / "junit.xml")], cwd=root, capture_output=True, text=True,
                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                                  "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    (directory / "pytest.log").write_text(process.stdout + process.stderr)
    print(process.stdout + process.stderr, flush=True)
    ids, counts, backends = case_results(directory / "junit.xml")
    after = snapshot(root, manifest["files"])
    passed = (process.returncode == 0 and sorted(ids) == sorted(manifest["expected_case_ids"])
              and len(ids) == len(set(ids)) and not any(counts[k] for k in ("failed", "errors", "skipped"))
              and all(backends.values()) and before == after)
    summary = {"status": "PASS" if passed else "FAIL", "scope": "generated-only balanced-loss qualification",
               "environment": environment, "counts": counts, "backend_checks": backends,
               "pytest_exit_code": process.returncode, "source_unchanged": before == after,
               "dental_images_accessed": False, "real_training_performed": False, "pretrained_weights": None}
    for name, value in (("summary.json", summary), ("source_hashes_before.json", before), ("source_hashes_after.json", after)):
        (directory / name).write_text(json.dumps(value, indent=2) + "\n")
    payloads = {p.name: legacy.sha256(p) for p in directory.iterdir() if p.is_file()}
    (directory / "evidence_manifest.json").write_text(json.dumps({"files": payloads}, indent=2) + "\n")
    return summary


def evidence_zip(root):
    root = Path(root)
    path = root / "vision_b1_balanced_runtime_evidence_v2.zip"
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for payload in sorted((root / "balanced_synthetic_evidence_v2").iterdir()):
            archive.write(payload, payload.name)
    return path
