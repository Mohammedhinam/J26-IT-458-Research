"""Generated-only final-preparation guards and six-fit reproduction tests."""
import json

import numpy as np
import pytest
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from test_baseline_nhanes import synthetic_inputs
from src.tabular import finalise_development as prep


def test_six_fits_fold_isolation_and_exact_saved_reload(tmp_path, monkeypatch):
    x, y = synthetic_inputs(100)
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    original = Pipeline.fit
    ids = []
    def tracked(self, frame, labels, **kwargs):
        ids.append(frame.index.tolist())
        assert tuple(frame.columns) == prep.FEATURES and frame.index.equals(labels.index)
        return original(self, frame, labels, **kwargs)
    monkeypatch.setattr(Pipeline, 'fit', tracked)
    # Independent reference run occurs before the instrumented six-fit preparation.
    monkeypatch.setattr(Pipeline, 'fit', original)
    expected, _, _ = prep.fit_configuration(x, y, folds, prep.BASELINE_CONFIGURATION)
    monkeypatch.setattr(Pipeline, 'fit', tracked)
    model, p, scores, reproduction, width = prep.prepare_logistic(
        x, y, folds, {k: prep.metric_text(v) for k, v in expected.items()})
    assert len(ids) == 6 and ids[-1] == x.index.tolist()
    for call, (fitting, scoring) in zip(ids[:5], folds):
        assert call == x.index[fitting].tolist() and not set(call) & set(x.index[scoring])
    assert all(row[-1] == 'MATCH' for row in reproduction)
    path = tmp_path / 'model.joblib'
    prep.joblib.dump(model, path)
    np.testing.assert_array_equal(prep.joblib.load(path).predict_proba(x), model.predict_proba(x))
    assert prep.baseline.score_predictions(y, p) == scores


def test_reproduction_mismatch_prevents_sixth_fit(monkeypatch):
    x, y = synthetic_inputs(100)
    monkeypatch.setattr(prep, 'fit_configuration', lambda *_: ({'AUROC': .5}, None, 1))
    monkeypatch.setattr(prep, 'make_comparison_pipeline', lambda *_: pytest.fail('Sixth fit reached'))
    with pytest.raises(ValueError, match='reproduction failed'):
        prep.prepare_logistic(x, y, (), {'AUROC': '.900000'})


def test_thresholds_exact_existing_rule_and_no_model_fit(monkeypatch):
    monkeypatch.setattr(Pipeline, 'fit', lambda *_: pytest.fail('Threshold step fitted a model'))
    p = np.array([.1, .6, .4, .9])
    result = prep.thresholds_and_metrics(np.array([0, 0, 1, 1]), {'generated': p})['generated']
    assert result['decision'] == {'threshold': .4, 'J': .5, 'useful': True}
    assert result['apparent_oof_at_selected_threshold']['Sensitivity'] == 1
    assert result['clinical_cutoff'] is False
    assert 'not independent' in result['optimism_warning']


def test_useless_threshold_rejected_without_fallback():
    with pytest.raises(ValueError, match='No useful'):
        prep.thresholds_and_metrics(np.array([0, 0, 1, 1]), {'generated': np.full(4, .3)})


@pytest.mark.parametrize('fault', ['hash', 'ids', 'labels', 'probability'])
def test_untrusted_saved_reference_rejected(tmp_path, fault):
    ids, y = np.arange(4), np.array([0, 0, 1, 1])
    saved_ids, labels, p = ids.copy(), y.copy(), np.array([.1, .2, .8, .9])
    if fault == 'ids': saved_ids[0] = 99
    if fault == 'labels': labels[0] = 1
    if fault == 'probability': p[0] = np.nan
    path = tmp_path / 'oof.npz'
    np.savez(path, SEQN=saved_ids, y=labels, A_reference=p)
    expected = '0' * 64 if fault == 'hash' else prep.digest(path)
    with pytest.raises(ValueError): prep.checked_reference(path, expected, ids, y)


def test_new_scope_and_no_test_authorization_before_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(prep, 'verify_inputs', lambda: pytest.fail('Inputs accessed'))
    with pytest.raises(ValueError, match='opt-in'): prep.run(tmp_path / 'out', {})
    with pytest.raises(ValueError, match='scope'):
        prep.run(tmp_path / 'out', {'scope': 'old', 'status': 'owner_confirmed'}, opt_in=True)
    assert prep.PROTOCOL['test_access_authorized'] is False
    assert prep.PROTOCOL['demo_activation_authorized'] is False


@pytest.mark.parametrize('fault', [None, 'stale_binding', 'test_permission'])
def test_current_preparation_binding_cannot_grant_test_access(tmp_path, monkeypatch, fault):
    monkeypatch.setattr(prep, 'bindings', lambda _: {'code_sha256': 'generated_pinned'})
    owner = {'scope': prep.SCOPE, 'status': 'owner_confirmed', 'authorizer': 'generated owner',
             'date': '2026-10-16', 'evidence_reference': 'synthetic test only',
             'test_access_authorized': False, 'code_sha256': 'generated_pinned'}
    if fault == 'stale_binding': owner['code_sha256'] = 'stale'
    if fault == 'test_permission': owner['test_access_authorized'] = True
    if fault is None:
        prep.authorize(owner, tmp_path / 'output', opt_in=True)
    else:
        with pytest.raises(ValueError): prep.authorize(owner, tmp_path / 'output', opt_in=True)
