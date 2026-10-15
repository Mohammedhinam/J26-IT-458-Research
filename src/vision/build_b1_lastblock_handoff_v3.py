"""Minimal code-only dependency closure for generated v3 qualification."""
import ast
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_pilot_b1_lastblock_v3 as stage
from src.vision import verify_b1_lastblock_runtime_v3 as verification


ROOT = Path(__file__).resolve().parents[2]
OWNER = 'docs/vision_b1_lastblock_owner_authorization_20261015.json'
REFERENCES = ('docs/vision_b1_unweighted_reference_v1.json',
              'docs/vision_b1_balanced_results_verification_v2.json')


def required_files():
    selected = set()
    pending = ['src/vision/exploratory_pilot_b1_lastblock_v3.py',
               'src/vision/verify_b1_lastblock_runtime_v3.py', verification.TEST_FILE]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        path = legacy.safe_file(ROOT, name)
        selected.add(name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'src.vision':
                    pending.extend('src/vision/'+item.name+'.py' for item in node.names)
                elif node.module and node.module.startswith('src.vision.'):
                    pending.append(node.module.replace('.', '/')+'.py')
    # Runtime source bindings include historical files that need not be imported.
    selected.update('src/vision/'+name for name in stage.code_hashes())
    selected.update((OWNER, *REFERENCES))
    for name in selected:
        legacy.safe_file(ROOT, name)
    return sorted(selected)


def build(path, local_junit):
    ids, counts, backends = verification.case_results(local_junit)
    if (len(ids) != 33 or len(set(ids)) != 33 or counts['failed'] or counts['errors']
            or not all(any(i.endswith('::'+name) for i in ids) for name in verification.BACKENDS)):
        raise ValueError('Require exact33 focused cases including all five backend cases')
    files = {name: legacy.sha256(ROOT/name) for name in required_files()}
    manifest = {'version': 'b1-lastblock-code-v3', 'files': files, 'expected_case_ids': sorted(ids),
                'expected_cases': 33, 'owner_record': OWNER, 'references': list(REFERENCES),
                'dental_images_included': False, 'weights_included': False,
                'qualification_requires': '33passed,0failed/errors/skipped,all5backendchecks'}
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            archive.writestr(name, (ROOT/name).read_bytes())
        archive.writestr('verification_manifest.json', json.dumps(manifest,indent=2)+'\n')
    return {'path': str(path), 'bytes': Path(path).stat().st_size, 'sha256': legacy.sha256(path),
            'files': files, 'manifest': manifest}
