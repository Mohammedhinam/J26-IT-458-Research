"""Code-only generated verification. Never runs the dental pilot or downloads."""
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile


TEST_FILES = ["tests/test_b1_local_export_v1.py","tests/test_exploratory_pilot_b1_v1.py"]
BACKENDS = ["test_resnet50_four_output_optimization_and_frozen_batchnorm_weights_none",
            "test_four_class_gradcam_geometry_and_hook_cleanup_weights_none",
            "test_four_class_synthetic_checkpoint_loading_and_reproducibility"]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def run(root,*,local_diagnostic=False):
    root=Path(root).resolve();evidence=root/'synthetic_evidence'
    evidence.mkdir(exist_ok=False)
    manifest=json.loads((root/'verification_manifest.json').read_text())
    before={n:digest(root/n) for n in manifest['files']}
    if before!=manifest['files']:raise ValueError('Bundled source hash mismatch')
    env={'python':platform.python_version(),'platform':platform.system()}
    dependency_error=None
    for name in ('numpy','Pillow','pytest','torch','torchvision'):
        try:env[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:env[name]=None
    try:
        import torch,torchvision
        torch.set_num_threads(1)
        # A real compiled torchvision operation catches mismatched installations.
        torchvision.ops.nms(torch.tensor([[0.,0.,1.,1.]]),torch.tensor([1.]),.5)
        env.update(torch=str(torch.__version__),torchvision=str(torchvision.__version__),
                   cuda_available=torch.cuda.is_available(),gpu=torch.cuda.get_device_name() if torch.cuda.is_available() else None)
    except Exception as error:
        dependency_error=type(error).__name__+': '+str(error)
    if dependency_error and not local_diagnostic:
        result={'status':'STOP_DEPENDENCY','dependency_error':dependency_error,'environment':env,
                'RUN_PILOT':False,'dental_images_accessed':False,'dental_training_performed':False}
        (evidence/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    command=[sys.executable,'-B','-m','pytest',*TEST_FILES,'-q','-p','no:cacheprovider',
             '--junitxml='+str(evidence/'junit.xml')]
    # For local preparation only, pytest is already installed as pure Python
    # in the existing project venv. No package is installed or copied.
    if local_diagnostic:
        pytest_site=os.environ.get('B1_EXISTING_PYTEST_SITE')
        if not pytest_site:raise RuntimeError('Set existing local pure-Python pytest path; no installation')
        command=[sys.executable,'-I','-B','-c',
                 'import sys;sys.path.insert(0,'+repr(str(root))+');sys.path.append('+repr(pytest_site)+');import pytest;raise SystemExit(pytest.main('+repr(command[4:])+'))']
    process=subprocess.run(command,cwd=root,capture_output=True,text=True,
                           env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1',
                                'OPENBLAS_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'})
    (evidence/'pytest.log').write_text(process.stdout+process.stderr)
    print(process.stdout,flush=True)
    tree=ET.parse(evidence/'junit.xml').getroot();cases=tree.findall('.//testcase')
    failed=sum(c.find('failure') is not None for c in cases)
    errors=sum(c.find('error') is not None for c in cases)
    skipped=sum(c.find('skipped') is not None for c in cases)
    backend={name:next(('skipped' if c.find('skipped') is not None else 'failed' if
                        c.find('failure') is not None or c.find('error') is not None else 'passed'
                        for c in cases if c.get('name')==name),'missing') for name in BACKENDS}
    after={n:digest(root/n) for n in manifest['files']}
    counts={'total':len(cases),'passed':len(cases)-failed-errors-skipped,'failed':failed,'errors':errors,'skipped':skipped}
    passed=(process.returncode==0 and counts=={'total':71,'passed':71,'failed':0,'errors':0,'skipped':0}
            and all(x=='passed' for x in backend.values()) and before==after)
    result={'status':'PASS' if passed else 'INCOMPLETE' if local_diagnostic and not failed and not errors else 'FAIL',
            'scope':'generated-only local-export and four-grade pilot runtime verification',
            'local_diagnostic':local_diagnostic,'environment':env,'dependency_error':dependency_error,
            'counts':counts,'backend_tests':backend,'pytest_exit_code':process.returncode,
            'source_unchanged':before==after,'RUN_PILOT':False,'dental_images_accessed':False,
            'dental_training_performed':False,'synthetic_optimizer_checks_requested':True,
            'synthetic_optimizer_checks_executed':any(backend[n]=='passed' for n in (BACKENDS[0],BACKENDS[2])),
            'pretrained_weights':None,
            'acceptance_passed':passed}
    for name,value in [('summary.json',result),('source_hashes_before.json',before),('source_hashes_after.json',after)]:
        (evidence/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2),flush=True)
    return result


def evidence_zip(root):
    root=Path(root);directory=root/'synthetic_evidence'
    destination=root/'vision_b1_pilot_runtime_evidence_v1.zip'
    files={p.name:digest(p) for p in directory.iterdir() if p.is_file()}
    (directory/'evidence_manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.iterdir()):
            archive.write(path,path.name)
    return destination
