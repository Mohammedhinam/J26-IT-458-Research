"""Known generated probabilities; no actual model or dataset evaluation."""
import copy

import numpy as np
import pytest

from src.vision import saved_grade_diagnostic as diagnostic


def fixture():
    return {'ids': np.array(['g1', 'g2', 'g3', 'g4']), 'labels': np.array([1, 2, 3, 4]),
            'folds': np.array([0, 1, 2, 3]),
            'probabilities': np.array([[.1, .6, .2, .1], [.1, .4, .3, .2], [.01, .01, .97, .01], [.01, .01, .03, .95]])}


def test_independent_rank_margin_and_reliability_arithmetic():
    saved = fixture()
    before = saved['probabilities'].copy()
    result = diagnostic.analyze({'generated': saved})
    record = result['models']['generated']
    assert result['n'] == 4 and result['model_fits'] == 0 and not result['labels_changed']
    assert record['grades']['1']['correct'] == 0
    assert record['grades']['1']['true_grade_rank_counts_1to4'] == [0, 0, 1, 0]
    assert record['grades']['2']['top2_correct'] == 1
    assert record['metrics']['accuracy'] == .75
    row = next(r for r in result['case_rows'] if r['provisional_grade'] == 1)
    assert row['predicted_grade'] == 2 and row['top2_grade'] == 3
    assert row['winning_margin'] == pytest.approx(.4)
    assert row['true_minus_best_other'] == pytest.approx(-.5)
    assert sum(r['n'] for r in record['reliability_bins']) == 4
    np.testing.assert_array_equal(saved['probabilities'], before)


@pytest.mark.parametrize('key', ['ids', 'labels', 'folds'])
def test_different_population_labels_or_folds_rejected(key):
    a, b = fixture(), fixture()
    b[key] = b[key][::-1]
    with pytest.raises(ValueError, match='differ'):
        diagnostic.analyze({'a': a, 'b': b})


@pytest.mark.parametrize('fault', ['nan', 'negative', 'sum', 'duplicate_ids', 'zero_grade'])
def test_invalid_evidence_rejected(fault):
    a = fixture()
    if fault == 'nan': a['probabilities'][0, 0] = np.nan
    if fault == 'negative': a['probabilities'][0, 0] = -.1
    if fault == 'sum': a['probabilities'][0] = 0
    if fault == 'duplicate_ids': a['ids'][0] = a['ids'][1]
    if fault == 'zero_grade': a['labels'][0] = 0
    with pytest.raises(ValueError): diagnostic.analyze({'a': a})


def test_ties_are_deterministic_and_source_probabilities_unchanged():
    a = fixture()
    a['probabilities'][:] = .25
    result = diagnostic.analyze({'a': a})
    assert result['models']['a']['metrics']['predicted_counts'] == [4, 0, 0, 0]
    assert next(r for r in result['case_rows'] if r['provisional_grade'] == 2)['true_grade_rank'] == 2


def test_loader_hash_before_npz_and_no_overwrite(tmp_path):
    source = tmp_path / 'oof.npz'
    source.write_bytes(b'not an archive')
    with pytest.raises(ValueError, match='Untrusted'):
        diagnostic.load_oof(source, '0' * 64, 'linear')
    output = tmp_path / 'cases.csv'
    result = diagnostic.analyze({'a': fixture()})
    diagnostic.write_cases(output, result['case_rows'])
    with pytest.raises(ValueError): diagnostic.write_cases(output, result['case_rows'])
