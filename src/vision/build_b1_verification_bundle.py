"""Snapshot only the B1 verification dependency closure into new artifacts."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile


ZIP_NAME = "vision_b1_runtime_code_v1.zip"
NOTEBOOK_NAME = "vision_b1_colab_verification_v1.ipynb"
TARGET = "tests/test_colour_b1_prototype.py"
RUNNER = "src/vision/verify_b1_runtime.py"
BACKENDS = ["test_resnet50_unclipped_forward_weights_none",
            "test_resnet50_gradcam_frozen_backbone_hooks_and_alignment_weights_none"]


def digest(content):
    return hashlib.sha256(content).hexdigest()


def dependency_files(root):
    """Follow local imports plus declared runtime hash dependencies, before ZIP IO."""
    pending, found, reasons = [TARGET, RUNNER], {}, {}
    while pending:
        name = pending.pop()
        if name in found:
            continue
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing/unsafe required code-only dependency: " + name)
        content = path.read_bytes()
        tree = ast.parse(content, filename=name)
        dependencies = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "src.vision":
                dependencies.update("src/vision/" + alias.name + ".py" for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src.vision."):
                dependencies.add(node.module.replace(".", "/") + ".py")
            elif isinstance(node, ast.Import):
                dependencies.update(alias.name.replace(".", "/") + ".py" for alias in node.names
                                    if alias.name.startswith("src.vision."))
            elif isinstance(node, ast.FunctionDef) and node.name == "source_code_hashes":
                assignment = next(n for n in node.body if isinstance(n, ast.Assign)
                                  and any(isinstance(t, ast.Name) and t.id == "names" for t in n.targets))
                names = ast.literal_eval(assignment.value)
                if not isinstance(names, (list, tuple)) or any(
                        type(n) is not str or Path(n).name != n or not n.endswith(".py") for n in names):
                    raise ValueError("Unsupported runtime hash declaration; STOP")
                dependencies.update("src/vision/" + n for n in names)
        found[name] = content
        reasons[name] = sorted(dependencies)
        pending.extend(sorted(dependencies))
    test_tree = ast.parse(found[TARGET])
    if not set(BACKENDS) <= {n.name for n in test_tree.body if isinstance(n, ast.FunctionDef)}:
        raise ValueError("Required backend test missing before packaging")
    return dict(sorted(found.items())), reasons


UPLOAD = '''from google.colab import files
from pathlib import Path, PurePosixPath
import hashlib, io, json, os, stat, sys, tempfile, zipfile
UPLOADED = files.upload()
if set(UPLOADED) != {ZIP_NAME}:
    raise RuntimeError("Upload only the matching B1 code-only ZIP; no datasets")
archive_bytes = UPLOADED[ZIP_NAME]
if hashlib.sha256(archive_bytes).hexdigest() != ZIP_SHA256:
    raise RuntimeError("Whole ZIP SHA-256 mismatch; STOP")
WORK = Path(tempfile.mkdtemp(prefix="vision_b1_generated_v1_", dir="/content"))
with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
    entries = archive.infolist()
    expected = set(EXPECTED_FILES) | {"code_manifest.json"}
    if len(entries) != len(expected) or {e.filename for e in entries} != expected:
        raise RuntimeError("Missing, duplicate or extra archive entry; STOP")
    if sum(e.file_size for e in entries) > 2_000_000 or archive.testzip() is not None:
        raise RuntimeError("Archive size/CRC failure; STOP")
    for entry in entries:
        name = entry.filename
        path = PurePosixPath(name)
        mode = entry.external_attr >> 16
        if path.is_absolute() or ".." in path.parts or "\\\\" in name or not stat.S_ISREG(mode):
            raise RuntimeError("Unsafe code archive path/type; STOP")
        content = archive.read(entry)
        expected_hash = MANIFEST_SHA256 if name == "code_manifest.json" else EXPECTED_FILES[name]
        if hashlib.sha256(content).hexdigest() != expected_hash:
            raise RuntimeError("File hash mismatch: " + name)
        destination = WORK/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(content)
manifest = json.loads((WORK/"code_manifest.json").read_text())
if manifest["files"] != EXPECTED_FILES:
    raise RuntimeError("Manifest file allowlist mismatch; STOP")
print("Fresh code-only extraction:", WORK)
print("SHA-256 verified:", len(EXPECTED_FILES), "code/test files plus manifest")
'''

EXECUTE = '''import subprocess
EVIDENCE = WORK/"synthetic_evidence"
env = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
           PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
env.pop("PYTHONPATH", None)
command = [sys.executable, "-I", "-B", str(WORK/"src/vision/verify_b1_runtime.py"), str(WORK)]
try:
    run = subprocess.run(command, cwd=WORK, env=env, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, timeout=600)
    output, process_exit = run.stdout, run.returncode
except subprocess.TimeoutExpired as error:
    output = error.stdout or ""
    if isinstance(output, bytes): output = output.decode("utf-8", errors="replace")
    output += "\\nRuntime verification exceeded 600 seconds; STOP, not PASS."
    process_exit = -1
EVIDENCE.mkdir(exist_ok=True)
(EVIDENCE/"pytest.log").write_text(output)
print(output)
if not (EVIDENCE/"verification.json").is_file():
    (EVIDENCE/"verification.json").write_text(json.dumps(
        {"status":"FAIL", "blocker":"Runner interrupted before final evidence", "process_exit":process_exit}, indent=2))
print("Next cell downloads evidence for PASS, FAIL or dependency STOP.")
'''

DOWNLOAD = '''result = json.loads((EVIDENCE/"verification.json").read_text())
(EVIDENCE/"code_manifest.json").write_bytes((WORK/"code_manifest.json").read_bytes())
(EVIDENCE/"handoff_binding.json").write_text(json.dumps(
    {"zip_sha256":ZIP_SHA256, "manifest_sha256":MANIFEST_SHA256,
     "runner_process_exit":process_exit, "generated_only":True}, indent=2))
evidence_files = sorted(p for p in EVIDENCE.iterdir() if p.is_file())
evidence_hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence_files}
(EVIDENCE/"evidence_hashes.json").write_text(json.dumps(evidence_hashes, indent=2))
evidence_zip = WORK/"vision_b1_runtime_evidence_v1.zip"
with zipfile.ZipFile(evidence_zip, "x", compression=zipfile.ZIP_DEFLATED) as target:
    for path in sorted(EVIDENCE.iterdir()):
        if path.is_file(): target.write(path, path.name)
print("Evidence ZIP SHA-256:", hashlib.sha256(evidence_zip.read_bytes()).hexdigest())
files.download(str(evidence_zip))
if process_exit != 0 or result.get("status") != "PASS" or result.get("acceptance_passed") is not True:
    raise RuntimeError("B1 runtime verification NOT PASSED. Retain downloaded evidence; no install or fallback.")
print("77 PASSED, 0 failed/errors/skipped; both B1 ResNet-50 tests executed; code unchanged.")
print("Synthetic software verification only, not dental/clinical performance or training approval.")
'''


def cell(kind, text):
    value = {"cell_type": kind, "metadata": {}, "source": text.splitlines(True)}
    if kind == "code":
        value.update(execution_count=None, outputs=[])
        ast.parse(text)
    return value


def build(root):
    root = Path(root).resolve()
    archive, notebook_path = root/"docs"/ZIP_NAME, root/"docs"/NOTEBOOK_NAME
    if archive.exists() or notebook_path.exists():
        raise ValueError("Versioned handoff artifacts already exist; no overwrite")
    payloads, dependencies = dependency_files(root)
    hashes = {name:digest(content) for name, content in payloads.items()}
    manifest = {"version":"b1-runtime-code-v1", "files":hashes, "dependency_closure":dependencies,
                "test_target":TARGET, "expected_cases":77, "backend_tests":BACKENDS,
                "runner":RUNNER, "scope":"generated-only CPU; weights=None; no installs/data/training"}
    manifest_bytes = (json.dumps(manifest, indent=2)+"\n").encode()
    manifest_sha = digest(manifest_bytes)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as target:
        for name, content in {**payloads, "code_manifest.json":manifest_bytes}.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            target.writestr(info, content)
    zip_sha = digest(archive.read_bytes())
    config = ("ZIP_NAME = " + repr(ZIP_NAME) + "\nZIP_SHA256 = " + repr(zip_sha)
              + "\nMANIFEST_SHA256 = " + repr(manifest_sha) + "\nEXPECTED_FILES = " + repr(hashes) + "\n")
    notebook = {"nbformat":4, "nbformat_minor":5,
                "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                            "language_info":{"name":"python"}},
                "cells":[cell("markdown", "# B1 generated-only CPU verification v1\n\n"
                    "In Colab select **Runtime → Change runtime type → CPU**. Run all cells. "
                    "Upload only `" + ZIP_NAME + "` when prompted. No Drive mount, dental images, "
                    "weights, installs or network downloads. Existing dependencies must import and "
                    "pass a CPU torch/torchvision compiled-operator check; otherwise STOP.\n\n"
                    "Acceptance: exactly77 pass, zero failures/errors/skips, both ResNet tests pass, "
                    "all pinned source hashes unchanged and isolated imports. The tests use weights=None. "
                    "Evidence downloads even after a dependency/test failure. Colab success is pending execution.\n"),
                    cell("code", config + UPLOAD), cell("code", EXECUTE), cell("code", DOWNLOAD)]}
    for index, item in enumerate(notebook["cells"]):
        item["id"] = "b1-v1-cell-" + str(index)
    notebook_path.write_text(json.dumps(notebook, indent=2)+"\n")
    return {"zip_path":str(archive), "zip_sha256":zip_sha, "zip_bytes":archive.stat().st_size,
            "notebook_path":str(notebook_path), "manifest_sha256":manifest_sha,
            "hashed_files":len(hashes), "files":hashes}


if __name__ == "__main__":
    print(json.dumps(build(Path(__file__).resolve().parents[2]), indent=2))
