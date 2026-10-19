"""Aggregate-only evidence schema, hash rejection and private-field filtering."""
from hashlib import sha256
import json

import pytest

from src.vision import vision_evidence as evidence


def fixture_files(tmp_path, monkeypatch):
    def metrics(support):
        return {'support': support, 'confusion_matrix': [[n if i == j else 0 for j in range(4)]
                                                         for i, n in enumerate(support)],
                'private_record_ids': ['DO_NOT_EXPOSE']}
    small, large = metrics([1, 13, 22, 17]), metrics([12, 84, 223, 361])
    documents = [
        {'overall': {'v3': small}, 'grade2_cases': ['DO_NOT_EXPOSE']},
        {'metrics': {'linear': large, 'majority': large}},
        {'metrics': {'efficientnet': large}},
        {'metrics': {'unweighted': large}},
        {'metrics': {'linear': large}},
        {'status': 'verified_680_image_oof_comparison',
         'rows': [{'support': [12, 84, 223, 361]} for _ in range(4)]}]
    hashes = {}
    for name, document in zip(evidence.SOURCES, documents):
        path = tmp_path / name
        path.write_text(json.dumps(document))
        hashes[name] = sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(evidence, 'SOURCES', hashes)
    return list(hashes)


def test_population_separation_and_no_private_fields(tmp_path, monkeypatch):
    fixture_files(tmp_path, monkeypatch)
    result = evidence.load_evidence(tmp_path)
    assert result['historical_validation53']['n'] == 53
    assert all(row['n'] == 680 for row in result['training680_oof'])
    assert len(result['training680_oof']) == 5
    assert len(result['photo_model_comparison_680']['rows']) == 4
    assert 'DO_NOT_EXPOSE' not in json.dumps(result)
    assert result['final_model_selected'] is result['test_used'] is result['new_photo_runtime_activated'] is False
    for row in result['training680_oof']:
        assert row['accuracy'] == row['macro_f1'] == row['balanced_accuracy'] == 1


@pytest.mark.parametrize('fault', ['tamper', 'symlink', 'missing'])
def test_untrusted_report_fails_closed(tmp_path, monkeypatch, fault):
    names = fixture_files(tmp_path, monkeypatch)
    path = tmp_path / names[0]
    if fault == 'tamper': path.write_text('{}')
    if fault == 'symlink':
        path.rename(tmp_path / 'target.json')
        path.symlink_to(tmp_path / 'target.json')
    if fault == 'missing': path.unlink()
    with pytest.raises((ValueError, FileNotFoundError)): evidence.load_evidence(tmp_path)


@pytest.mark.parametrize('matrix', [[], [[1] * 3] * 4, [[-1] * 4] * 4, [[1.] * 4] * 4])
def test_invalid_confusion_matrix_rejected(matrix):
    with pytest.raises(ValueError): evidence.card('generated', {'confusion_matrix': matrix, 'support': [4] * 4})
