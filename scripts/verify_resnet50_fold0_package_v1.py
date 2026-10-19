"""Independent local extraction/import/preflight check. No study model fitting."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "data/vision/resnet50_fold0_pilot_v1_20261018_r2"


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            result.update(chunk)
    return result.hexdigest()


def main():
    receipt = json.loads((ROOT / "preparation.json").read_text())
    notebook = json.loads(Path(receipt["notebook"]).read_text())
    code = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    for text in code:
        ast.parse(text)
    schema_checked = False
    if importlib.util.find_spec("nbformat"):
        import nbformat
        nbformat.validate(nbformat.read(receipt["notebook"], as_version=4))
        schema_checked = True
    namespace = {}
    exec(code[0], namespace)
    assert namespace["CLOUD_UPLOAD_APPROVED"] is False and namespace["RUN_TRAINING"] is False
    try:
        exec(code[1], namespace)
    except PermissionError:
        pass
    else:
        raise AssertionError("Default notebook gate did not stop before dependency install")
    assert namespace["ARCHIVE_SHA"] == sha(Path(receipt["archive"]))
    assert namespace["MANIFEST_SHA"] == receipt["manifest_sha256"]
    extracted = ROOT / "portable_local_check"
    extracted.mkdir()
    with zipfile.ZipFile(receipt["archive"]) as archive:
        entries = archive.infolist()
        names = archive.namelist()
        assert len(names) == len(set(names)) == 699
        assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in names)
        manifest_bytes = archive.read("manifest.json")
        assert hashlib.sha256(manifest_bytes).hexdigest() == receipt["manifest_sha256"]
        manifest = json.loads(manifest_bytes)
        assert set(names) == set(manifest["files"]) | {"manifest.json"}
        assert archive.testzip() is None
        archive.extractall(extracted)
    # -I/-B and an unrelated cwd ensure no checkout imports or bytecode files are needed.
    script = '''import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from src.vision import resnet50_fold0_pilot_v1 as p
import torch, numpy as np
root = Path(sys.argv[1])
assert Path(p.__file__).resolve().is_relative_to(root)
receipt = p.preflight(root, sys.argv[2])
torch.set_num_threads(2)
model = p.model_factory(root/'weights/resnet50-11ad3fa6.pth').eval()
before = p.state_hashes(model)
with torch.no_grad():
    logits = model(torch.zeros(1,3,224,224))
assert tuple(logits.shape) == (1,4) and torch.isfinite(logits).all()
prepared = p.cam.RGBInput(np.full((12,18,3), 180, np.uint8),
                          np.zeros((3,224,224), np.float32), (0,37,224,150))
views, detail = p.gradcam(model, prepared, target_index=1)
assert detail['native_feature_shape'] == [1,2048,7,7]
assert detail['explained_grade'] == 2 and views['overlay'].shape == (12,18,3)
assert before == p.state_hashes(model)
assert all(parameter.grad is None for parameter in model.parameters())
try:
    p.run(root, root.parent/'FORBIDDEN_NO_APPROVAL_RUN')
except PermissionError:
    pass
else:
    raise AssertionError('Training gate failed')
assert not (root.parent/'FORBIDDEN_NO_APPROVAL_RUN').exists()
print(json.dumps({'isolated_import':True, 'preflight':receipt, 'official_weights_load':True,
    'generated_forward_shape':list(logits.shape), 'generated_forward_finite':True,
    'generated_cam_geometry_and_target':True, 'weights_unchanged':True,
    'unapproved_run_blocked':True, 'real_training':False, 'dental_inference':False}))
'''
    completed = subprocess.run([sys.executable, "-I", "-B", "-c", script, str(extracted),
                                receipt["manifest_sha256"]], cwd="/tmp", capture_output=True, text=True)
    if completed.returncode:
        print(completed.stderr)
        raise RuntimeError("Isolated portable check failed")
    result = json.loads(completed.stdout)
    result.update(notebook_code_cells_syntax_valid=len(code), notebook_schema_validated=schema_checked,
                  default_notebook_gate_blocks_install=True, zip_entries=len(entries), zip_crc_passed=True,
                  clean_colab_gpu_execution_verified=False)
    with (ROOT / "portable_verification.json").open("x") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
