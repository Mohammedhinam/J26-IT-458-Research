"""Expose frozen aggregate evidence without reading participant data or fitting."""
from hashlib import sha256
import json
import math
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / 'docs'
REPORT = 'tabular_final_test_results_v1.json'
REPORT_SHA = '5e1e54d69244bdfe2e93d7e9b6221ac8dbc63bf9b6692e4dcd495ddc23602945'
MODEL_ID = 'd70458a47011e8332c4911effc768c4efdf642a62384f97557d8295ab238e078'


def load_evidence(model_id, root=DOCS):
    """Only a matching demo model may display this previously measured evidence."""
    if model_id != MODEL_ID:
        raise ValueError('Final evidence does not describe the current demo model')
    path = Path(root) / REPORT
    if path.is_symlink() or path.stat().st_size > 1024**2:
        raise ValueError('Unsafe questionnaire evidence file')
    payload = path.read_bytes()
    if sha256(payload).hexdigest() != REPORT_SHA:
        raise ValueError('Questionnaire evidence SHA mismatch')
    result = json.loads(payload)['results']
    if (result['status'] != 'completed_single_frozen_evaluation'
            or result['n'] != 1563 or result['yes'] + result['no'] != 1563
            or result['clinical_validation'] is not False):
        raise ValueError('Invalid frozen evaluation status or population')
    rows = []
    # Construct an allowlist: execution paths and participant IDs never leave here.
    for name in ['XGBoost_A_raw', 'Logistic_C1_raw', 'Training_rate']:
        metrics = result['metrics'][name]
        values = {key: metrics[key] for key in ['AUROC', 'Average precision', 'Brier',
                    'Sensitivity frozen', 'Specificity frozen']}
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values.values()):
            raise ValueError('Invalid aggregate metric')
        rows.append({'name': name, 'cutoff': result['thresholds'][name], **values})
    return {'scope': 'Previously completed frozen questionnaire final evaluation',
            'n': result['n'], 'yes': result['yes'], 'no': result['no'], 'models': rows,
            'outcome': 'Self-reported previous gum treatment; not current disease or future risk.',
            'limitations': ['Overall AUROC 0.80 target was not achieved.',
                'Paired intervals do not establish a clear XGBoost advantage over Logistic.',
                'Statistical cutoffs are not clinically approved; no clinical validation.',
                'No further Test-driven tuning or automatic repeat evaluation.'],
            'model_id': model_id, 'new_evaluation': False, 'clinical_validation': False}
