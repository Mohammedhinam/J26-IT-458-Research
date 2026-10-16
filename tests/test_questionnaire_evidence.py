"""Generated report fixtures only; never load participant data or models."""
from hashlib import sha256
import json

import pytest

from src.tabular import questionnaire_evidence as evidence


def write_fixture(tmp_path, monkeypatch, **changes):
    metrics = {'AUROC': .7, 'Average precision': .4, 'Brier': .2,
               'Sensitivity frozen': .5, 'Specificity frozen': .8}
    result = {'status': 'completed_single_frozen_evaluation', 'n': 1563,
              'yes': 388, 'no': 1175, 'clinical_validation': False,
              'metrics': {name: dict(metrics) for name in
                          ['XGBoost_A_raw', 'Logistic_C1_raw', 'Training_rate']},
              'thresholds': {'XGBoost_A_raw': .26, 'Logistic_C1_raw': .28, 'Training_rate': .5},
              'private_ids': ['DO_NOT_EXPOSE'], **changes}
    path = tmp_path / evidence.REPORT
    path.write_text(json.dumps({'results': result, 'private_paths': ['DO_NOT_EXPOSE']}))
    monkeypatch.setattr(evidence, 'REPORT_SHA', sha256(path.read_bytes()).hexdigest())
    return path


def test_aggregate_only_output_preserves_fixed_results(tmp_path, monkeypatch):
    write_fixture(tmp_path, monkeypatch)
    result = evidence.load_evidence(evidence.MODEL_ID, tmp_path)
    assert result['n'] == 1563 and len(result['models']) == 3
    assert result['models'][0]['cutoff'] == .26
    assert result['models'][1]['cutoff'] == .28
    assert result['models'][0]['AUROC'] == .7
    assert result['clinical_validation'] is result['new_evaluation'] is False
    assert 'DO_NOT_EXPOSE' not in json.dumps(result)


@pytest.mark.parametrize('fault', ['hash', 'symlink', 'missing', 'different_model'])
def test_untrusted_report_or_mismatched_model_rejected(tmp_path, monkeypatch, fault):
    path = write_fixture(tmp_path, monkeypatch)
    if fault == 'hash': path.write_text('{}')
    if fault == 'symlink':
        path.rename(tmp_path / 'target.json')
        path.symlink_to(tmp_path / 'target.json')
    if fault == 'missing': path.unlink()
    model_id = 'different' if fault == 'different_model' else evidence.MODEL_ID
    with pytest.raises((ValueError, FileNotFoundError)):
        evidence.load_evidence(model_id, tmp_path)


@pytest.mark.parametrize('changes', [
    {'status': 'pending'}, {'n': 1562}, {'yes': 389}, {'clinical_validation': True}])
def test_false_status_and_population_rejected(tmp_path, monkeypatch, changes):
    write_fixture(tmp_path, monkeypatch, **changes)
    with pytest.raises(ValueError): evidence.load_evidence(evidence.MODEL_ID, tmp_path)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -.1, 1.1])
def test_nonfinite_or_invalid_metrics_rejected(tmp_path, monkeypatch, value):
    path = write_fixture(tmp_path, monkeypatch)
    result = json.loads(path.read_text())
    result['results']['metrics']['XGBoost_A_raw']['AUROC'] = value
    path.write_text(json.dumps(result))
    monkeypatch.setattr(evidence, 'REPORT_SHA', sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError): evidence.load_evidence(evidence.MODEL_ID, tmp_path)
