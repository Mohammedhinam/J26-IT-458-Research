"""Local code-only Colab handoff builder. No image IO or cloud execution."""
import ast
from hashlib import sha256
import json
from pathlib import Path,PurePosixPath
import stat
import zipfile


ROOT=Path(__file__).resolve().parents[2]
INITIAL={"src/vision/verify_b1_pilot_runtime_v1.py","src/vision/exploratory_pilot_b1_v1.py",
         "tests/test_b1_local_export_v1.py","tests/test_exploratory_pilot_b1_v1.py"}


def closure():
    selected=set();pending=list(INITIAL)
    while pending:
        name=pending.pop()
        if name in selected:continue
        path=ROOT/name
        if not path.is_file() or path.is_symlink():raise FileNotFoundError('Missing code-only dependency: '+name)
        selected.add(name)
        for node in ast.walk(ast.parse(path.read_text())):
            required=[]
            if isinstance(node,ast.ImportFrom):
                if node.module=='src.vision':required=['src/vision/'+x.name+'.py' for x in node.names]
                elif node.module and node.module.startswith('src.vision.'):
                    required=[node.module.replace('.','/')+'.py']
                elif node.module and node.module.startswith('test_'):
                    required=['tests/'+node.module+'.py']
            elif isinstance(node,ast.Import):
                required=[x.name.replace('.','/')+'.py' for x in node.names if x.name.startswith('src.vision.')]
            pending.extend(required)
    return sorted(selected)


def build_code_zip(path):
    files={n:sha256((ROOT/n).read_bytes()).hexdigest() for n in closure()}
    manifest={"version":"b1-pilot-runtime-code-v1","scope":"code_only_generated_verification",
              "files":files,"expected_cases":71,"RUN_PILOT":False,"dental_data_included":False}
    path=Path(path)
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:archive.writestr(name,(ROOT/name).read_bytes())
        archive.writestr('verification_manifest.json',json.dumps(manifest,indent=2)+'\n')
    return {"zip":str(path),"bytes":path.stat().st_size,"sha256":sha256(path.read_bytes()).hexdigest(),
            "file_count":len(files),"files":files}


def extract_code_zip(path,destination,expected_sha):
    path=Path(path);destination=Path(destination)
    if sha256(path.read_bytes()).hexdigest()!=expected_sha:raise ValueError('Code ZIP SHA mismatch')
    if destination.exists():raise ValueError('Fresh extraction required')
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP names')
        manifest=json.loads(archive.read('verification_manifest.json'))
        if set(names)!=set(manifest['files'])|{'verification_manifest.json'}:raise ValueError('Full allowlist mismatch')
        for info in archive.infolist():
            p=PurePosixPath(info.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in info.filename or info.is_dir()
                    or stat.S_ISLNK(info.external_attr>>16) or info.file_size>1024*1024):
                raise ValueError('Unsafe code ZIP entry')
        destination.mkdir(mode=0o700)
        for name in names:
            data=archive.read(name)
            if name!='verification_manifest.json' and sha256(data).hexdigest()!=manifest['files'][name]:
                raise ValueError('Source SHA mismatch')
            target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return manifest


def notebook(path,code,package):
    def md(text):return {"cell_type":"markdown","metadata":{},"source":text.splitlines(keepends=True)}
    def cell(text):return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text.splitlines(keepends=True)}
    upload=f'''# Upload ONLY vision_b1_pilot_code_v1.zip. No dental data in this step.
from google.colab import files
import hashlib, json, pathlib, tempfile, zipfile, stat, sys, os
uploaded = files.upload()
assert set(uploaded) == {{"vision_b1_pilot_code_v1.zip"}}, "Upload the code-only ZIP only"
raw = uploaded["vision_b1_pilot_code_v1.zip"]
assert hashlib.sha256(raw).hexdigest() == "{code['sha256']}", "Wrong code ZIP"
import io
archive = zipfile.ZipFile(io.BytesIO(raw))
manifest = json.loads(archive.read("verification_manifest.json"))
EXPECTED_FILES = {json.dumps(code['files'],sort_keys=True)}
assert manifest["files"] == EXPECTED_FILES
assert len(archive.namelist()) == len(EXPECTED_FILES)+1
assert set(archive.namelist()) == set(EXPECTED_FILES)|{{"verification_manifest.json"}}
root = pathlib.Path(tempfile.mkdtemp(prefix="b1_pilot_generated_", dir="/content"))
for info in archive.infolist():
    name=info.filename; p=pathlib.PurePosixPath(name)
    assert not p.is_absolute() and ".." not in p.parts and "\\\\" not in name
    assert not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16) and info.file_size <= 1048576
    data=archive.read(name)
    if name in EXPECTED_FILES: assert hashlib.sha256(data).hexdigest()==EXPECTED_FILES[name]
    target=root/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(data)
sys.path.insert(0,str(root)); os.chdir(root)
os.environ["PYTHONDONTWRITEBYTECODE"]="1"; sys.dont_write_bytecode=True
print("Fresh code extraction and",len(EXPECTED_FILES),"source hashes verified:",root)
'''
    verification='''# Generated synthetic checks only. Compatible existing dependencies required; NO installs.
from src.vision.verify_b1_pilot_runtime_v1 import run, evidence_zip
summary=run(root)
print(json.dumps(summary,indent=2))
RUNTIME_VERIFIED=summary.get("acceptance_passed") is True
# Download actual evidence for PASS, FAIL or dependency STOP.
evidence=evidence_zip(root)
print("Evidence SHA256:",hashlib.sha256(evidence.read_bytes()).hexdigest())
files.download(str(evidence))
assert RUNTIME_VERIFIED, "STOP: require 71 passed, zero failed/errors/skipped; no dental pilot"
'''
    controls=f'''# STOP HERE after generated verification until separate owner cloud/training permission.
RUN_PILOT = False
CLOUD_DATA_AUTHORIZATION = None
TRAINING_AUTHORIZATION = None
ALLOW_WEIGHT_DOWNLOAD = False
EXPECTED_DATA_ZIP = {json.dumps(Path(package['archive']).name if package.get('archive') else None)}
EXPECTED_DATA_SHA256 = {repr(package.get('sha256'))}
EXPECTED_MANIFEST_SHA256 = {repr(package.get('manifest_sha256'))}
assert not RUN_PILOT
print("No dental upload/training authorized by this notebook or local package.")
'''
    data='''# Execute only AFTER separately recorded owner cloud-upload authorization.
assert RUNTIME_VERIFIED and CLOUD_DATA_AUTHORIZATION is not None, "Separate cloud permission missing"
assert CLOUD_DATA_AUTHORIZATION.get("status")=="owner_confirmed"
assert CLOUD_DATA_AUTHORIZATION.get("scope")=="upload_exploratory_b1_development_v1"
assert CLOUD_DATA_AUTHORIZATION.get("archive_sha256")==EXPECTED_DATA_SHA256
assert CLOUD_DATA_AUTHORIZATION.get("bundle_manifest_sha256")==EXPECTED_MANIFEST_SHA256
assert CLOUD_DATA_AUTHORIZATION.get("date") and CLOUD_DATA_AUTHORIZATION.get("authorizer")
assert not pathlib.Path("/content/drive").exists(), "Use isolated runtime, no Drive mount"
uploaded_data=files.upload()
assert set(uploaded_data)=={EXPECTED_DATA_ZIP}
archive_path=pathlib.Path("/content")/EXPECTED_DATA_ZIP
archive_path.write_bytes(uploaded_data[EXPECTED_DATA_ZIP])
from src.vision.exploratory_bundle import sha256 as file_sha256
assert file_sha256(archive_path)==EXPECTED_DATA_SHA256
from src.vision.exploratory_pilot_b1_v1 import extract_verified_zip
data_root=pathlib.Path("/content/b1_pp1_pilot/development")
extract_verified_zip(archive_path,data_root,EXPECTED_DATA_SHA256,EXPECTED_MANIFEST_SHA256)
del uploaded_data
print("Development-only payload verified; training still requires separate permission.")
'''
    weights='''# No automatic weight download. Use an explicitly approved official cached checkpoint.
from src.vision.exploratory_pilot import pretrained_status
print(json.dumps(pretrained_status(),indent=2))
print("Required: ResNet50_Weights.IMAGENET1K_V2, resnet50-11ad3fa6.pth")
print("Official provenance: https://download.pytorch.org/models/resnet50-11ad3fa6.pth")
assert ALLOW_WEIGHT_DOWNLOAD is False, "No download implementation is included; obtain separate approval"
'''
    training='''# Real exploratory training is OFF by default and requires fresh hash-bound owner approval.
from src.vision import exploratory_pilot_b1_v1 as pilot
from src.vision import train_pipeline as trainer
if not RUN_PILOT:
    print("RUN_PILOT=False: no real training or Grad-CAM inference performed")
else:
    assert RUNTIME_VERIFIED and TRAINING_AUTHORIZATION is not None
    print("Required bindings:",json.dumps({"scope":pilot.SCOPE,
        "bundle_manifest_sha256":EXPECTED_MANIFEST_SHA256,
        "protocol_sha256":trainer.digest(pilot.protocol()),
        "code_sha256":trainer.digest(pilot.code_hashes()),
        "weights_sha256":pretrained_status()["sha256"],"output_run_id":"pp1_b1_four_grade_run_v1"},indent=2))
    results=pilot.run_pilot(data_root,EXPECTED_MANIFEST_SHA256,TRAINING_AUTHORIZATION,
                            "/content/b1_pp1_pilot/results/pp1_b1_four_grade_run_v1",opt_in=True)
    print(json.dumps(results,indent=2))
'''
    final='''# Future authorized results download only. Generated runtime evidence was downloaded above.
if RUN_PILOT:
    import shutil
    result_dir="/content/b1_pp1_pilot/results/pp1_b1_four_grade_run_v1"
    result_zip=shutil.make_archive("/content/vision_b1_four_grade_pilot_results_v1","zip",result_dir)
    print("Result ZIP SHA256:",hashlib.sha256(pathlib.Path(result_zip).read_bytes()).hexdigest())
    files.download(result_zip)
'''
    intro='''# B1 MGI 1–4 exploratory pilot — v1
First run **code-only generated verification**, download its evidence, then stop.
Local Mac passes/skips are not Colab verification. Required:71 passed,0 failed/errors/skipped, including all3 backend tests.

**Provisional labels; non-clinical; non-final; participant independence unverified.**
MGI0/healthy detection is unsupported. Original five-grade research architecture is unchanged.
Local package permission does not grant cloud upload, weights download or dental training.
Use a fresh Colab GPU runtime for the eventual pilot; synthetic verification may use CPU.
No installs, Drive mounts or automatic pretrained downloads.
'''
    value={"nbformat":4,"nbformat_minor":5,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
           "language_info":{"name":"python"},"colab":{"name":"vision_b1_pilot_colab_v1.ipynb"}},
           "cells":[md(intro),cell(upload),cell(verification),cell(controls),cell(data),cell(weights),cell(training),cell(final)]}
    for index,item in enumerate(value['cells']):item['id']='b1-cell-'+str(index)
    Path(path).write_text(json.dumps(value,indent=2)+'\n')
    return value
