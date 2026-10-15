"""Build a minimal hash-bound code-only weighted-comparison handoff."""
import ast
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_pilot_b1_balanced_v2 as weighted


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = "docs/vision_b1_unweighted_reference_v1.json"
OWNER = "docs/vision_b1_balanced_owner_authorization_20261015.json"


def required_files():
    selected = set()
    pending = ["src/vision/exploratory_pilot_b1_balanced_v2.py", "src/vision/verify_b1_balanced_runtime_v2.py",
               "tests/test_exploratory_pilot_b1_balanced_v2.py"]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        path = legacy.safe_file(ROOT, name)
        selected.add(name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                if node.module == "src.vision":
                    pending.extend("src/vision/" + item.name + ".py" for item in node.names)
                elif node.module and node.module.startswith("src.vision."):
                    pending.append(node.module.replace(".", "/") + ".py")
    # Hash-binding dependencies can be named in lists instead of import statements.
    selected.update("src/vision/" + name for name in weighted.code_hashes())
    selected.update((REFERENCE, OWNER))
    for name in selected:
        legacy.safe_file(ROOT, name)
    return sorted(selected)


def build(path, local_junit):
    cases = ET.parse(local_junit).getroot().findall(".//testcase")
    ids = [case.get("classname", "") + "::" + case.get("name", "") for case in cases]
    if len(ids) != 27 or len(set(ids)) != 27:
        raise ValueError("Expected exact27 focused cases, including four local backend skips")
    files = {name: legacy.sha256(ROOT / name) for name in required_files()}
    manifest = {"version": "b1-balanced-comparison-code-v2", "files": files, "expected_case_ids": sorted(ids),
                "expected_cases": 27, "reference": REFERENCE, "owner_record": OWNER,
                "dental_images_included": False, "weights_included": False,
                "qualification_requires": "27passed,0failed/errors/skipped,all4backendchecks"}
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            archive.writestr(name, (ROOT / name).read_bytes())
        archive.writestr("verification_manifest.json", json.dumps(manifest, indent=2) + "\n")
    return {"path": str(path), "bytes": Path(path).stat().st_size, "sha256": legacy.sha256(path),
            "files": files, "manifest": manifest}
