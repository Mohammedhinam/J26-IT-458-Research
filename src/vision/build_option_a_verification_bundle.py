"""Build code-only v4.1 verification artifacts; never access image data.

This is an artifact revision, not a change to the v4 export or approval policy.
"""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import zipfile


TARGETS = ["tests/test_exploratory_bundle_v4.py", "tests/test_exploratory_bundle.py",
           "tests/test_icc_colour_export.py"]
HELPERS = ["tests/test_colour_qa.py", "tests/test_colour_policy.py"]
ZIP_NAME = "vision_option_a_export_code_v4_1.zip"
NOTEBOOK_NAME = "vision_option_a_export_verification_v4_1.ipynb"


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def hash_dependencies(root, module):
    """Read the real hash dependency declaration without executing project code."""
    tree = ast.parse((root / module).read_text())
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "source_code_hashes")
    assignment = next(node for node in function.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "names"
                              for target in node.targets))
    names = ast.literal_eval(assignment.value)
    if not isinstance(names, (list, tuple)) or any(
            not isinstance(name, str) or Path(name).name != name or not name.endswith(".py")
            for name in names):
        raise ValueError("Unsupported hash dependency declaration; stop")
    return ["src/vision/" + name for name in names]


def isolated_test_cell():
    # A fresh Python process must resolve local code from the extracted ZIP only.
    runner = '''import json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from src.vision import exploratory_bundle as legacy, exploratory_bundle_v4 as v4
manifest = json.loads((root / "code_manifest.json").read_text())
for module in (legacy, v4):
    for name, digest in module.source_code_hashes().items():
        if manifest["files"].get("src/vision/" + name) != digest:
            raise RuntimeError("Missing or changed runtime hash dependency: " + name)
import pytest
status = pytest.main(sys.argv[2:])
origins = {name: str(Path(module.__file__).resolve())
           for name, module in list(sys.modules.items())
           if (name.startswith("src.vision.") or name.startswith("test_"))
           and getattr(module, "__file__", None)}
if not all(Path(path).is_relative_to(root) for path in origins.values()):
    raise RuntimeError("Local module escaped extracted code root")
(root / "synthetic_evidence/import_origins.json").write_text(json.dumps(origins, indent=2))
raise SystemExit(status)
'''
    return '''import subprocess, os, xml.etree.ElementTree as ET
TARGETS = ''' + repr(TARGETS) + '''
EVIDENCE = WORK / "synthetic_evidence"
EVIDENCE.mkdir()
def source_hashes():
    return {name: hashlib.sha256((WORK/name).read_bytes()).hexdigest() for name in EXPECTED_FILES}
before = source_hashes()
assert before == EXPECTED_FILES
RUNNER = ''' + repr(runner) + '''
command = [sys.executable, "-I", "-B", "-c", RUNNER, str(WORK), *TARGETS,
           "-q", "-p", "no:cacheprovider", "-c", os.devnull,
           "--rootdir=" + str(WORK), "--confcutdir=" + str(WORK),
           "--basetemp=" + str(WORK/"generated_tmp"),
           "--junitxml=" + str(EVIDENCE/"junit.xml")]
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
env.pop("PYTHONPATH", None)
run = subprocess.run(command, cwd=WORK, env=env, text=True, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, timeout=180)
(EVIDENCE/"pytest.log").write_text(run.stdout)
print(run.stdout)
after = source_hashes()
cases = list(ET.parse(EVIDENCE/"junit.xml").iter("testcase")) if (EVIDENCE/"junit.xml").exists() else []
failed = sum(c.find("failure") is not None for c in cases)
errors = sum(c.find("error") is not None for c in cases)
skipped = sum(c.find("skipped") is not None for c in cases)
result = {"versions": VERSIONS, "zip_sha256": EXPECTED_ZIP_SHA, "source_before": before,
          "source_after": after, "source_unchanged": before == after == EXPECTED_FILES,
          "test_targets": TARGETS, "total": len(cases), "passed": len(cases)-failed-errors-skipped,
          "failed": failed, "errors": errors, "skipped": skipped, "exit_code": run.returncode,
          "RUN_PILOT": RUN_PILOT, "real_images_accessed": False,
          "python_isolated": True,
          "scope": "Selected generated-image portability checks; not clinical/model validation"}
(EVIDENCE/"verification.json").write_text(json.dumps(result, indent=2)+"\\n")
print({key: result[key] for key in ("total", "passed", "failed", "errors", "skipped", "source_unchanged")})
'''


def build(root):
    root = Path(root).resolve()
    modules = ["src/vision/exploratory_bundle.py", "src/vision/exploratory_bundle_v4.py"]
    dependencies = {module: hash_dependencies(root, module) for module in modules}
    names = sorted(set(TARGETS + HELPERS + modules + sum(dependencies.values(), [])))
    payloads = {name: (root / name).read_bytes() for name in names}
    hashes = {name: sha256(content) for name, content in payloads.items()}
    manifest = {"version": "option-a-v4.1-portability-code-only", "files": hashes,
                "hash_dependencies": dependencies, "test_targets": TARGETS,
                "expected_selected_cases": 131,
                "scope": "Generated images only; no data, permission record, weights or training."}
    archive = root / "docs" / ZIP_NAME
    notebook_path = root / "docs" / NOTEBOOK_NAME
    if archive.exists() or notebook_path.exists():
        raise ValueError("Versioned outputs already exist; no overwrite")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as target:
        for name, content in {**payloads, "code_manifest.json":
                              (json.dumps(manifest, indent=2) + "\n").encode()}.items():
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            target.writestr(entry, content)
    archive_sha = sha256(archive.read_bytes())
    notebook = deepcopy(json.loads((root / "docs/vision_option_a_export_verification_v4.ipynb").read_text()))
    for cell in notebook["cells"]:
        text = "".join(cell["source"])
        text = text.replace("vision_option_a_export_code_v4.zip", ZIP_NAME)
        text = text.replace("vision_option_a_v4_generated_verification", "vision_option_a_v4_1_generated_verification")
        text = text.replace("vision_option_a_export_runtime_evidence_v4.zip", "vision_option_a_export_runtime_evidence_v4_1.zip")
        if cell["cell_type"] == "code":
            if "EXPECTED_FILES = " in text:
                lines = text.splitlines()
                lines = ["EXPECTED_ZIP_SHA = " + repr(archive_sha) if line.startswith("EXPECTED_ZIP_SHA = ")
                         else "EXPECTED_FILES = " + repr(hashes) if line.startswith("EXPECTED_FILES = ")
                         else line for line in lines]
                text = "\n".join(lines) + "\n"
            elif "TARGETS = " in text:
                text = isolated_test_cell()
            elif 'for name in ("pytest.log", "junit.xml", "verification.json")' in text:
                text = text.replace('("pytest.log", "junit.xml", "verification.json")',
                                    '("pytest.log", "junit.xml", "verification.json", "import_origins.json")')
            ast.parse(text)
        cell["source"] = text.splitlines(True)
    first = "".join(notebook["cells"][0]["source"])
    first = first.replace("# Option A v4 —", "# Option A v4.1 portability revision —")
    first += ("\nIncludes 12 hashed code/test files: legacy and v4 hash dependencies are both complete. "
              "The pilot module is included for hashing only; it is not executed. "
              "The underlying v4 export policy and all test assertions are unchanged.\n")
    notebook["cells"][0]["source"] = first.splitlines(True)
    notebook_path.write_text(json.dumps(notebook, indent=2) + "\n")
    return {"archive": str(archive), "archive_sha256": archive_sha,
            "archive_bytes": archive.stat().st_size, "notebook": str(notebook_path),
            "hashed_files": len(names), "source_hashes": hashes}


if __name__ == "__main__":
    print(json.dumps(build(Path(__file__).resolve().parents[2]), indent=2))
