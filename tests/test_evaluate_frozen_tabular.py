"""Generated-only evaluator qualification. No real Test data or model access."""
import json
import numpy as np
import pytest
from sklearn.pipeline import Pipeline

from test_baseline_nhanes import synthetic_inputs
from src.tabular import evaluate_frozen_tabular as evaluate


def approvals(output):
    owner = {'status': 'owner_confirmed', 'authorizer': 'generated owner',
             'date': '2026-10-16', 'evidence_reference': 'synthetic fixture only',
             'receipt_sha256': evaluate.RECEIPT_SHA}
    freeze = {**owner, 'scope': evaluate.FREEZE_SCOPE}
    test = {**owner, 'scope': evaluate.EVALUATE_SCOPE, 'test_access_authorized': True,
            **evaluate.bindings(output),
            'freeze_approval_sha256': evaluate.hashlib.sha256(json.dumps(freeze, sort_keys=True).encode()).hexdigest()}
    return freeze, test


@pytest.mark.parametrize('fault', ['opt_in', 'freeze', 'scope', 'test_permission', 'receipt', 'code', 'output', 'freeze_binding'])
def test_two_permissions_and_bindings_before_any_payload(tmp_path, monkeypatch, fault):
    out = tmp_path / 'output'
    freeze, test = approvals(out)
    if fault == 'freeze': freeze = {}
    if fault == 'scope': test['scope'] = evaluate.prep.SCOPE
    if fault == 'test_permission': test['test_access_authorized'] = False
    if fault == 'receipt': freeze['receipt_sha256'] = 'stale'
    if fault == 'code': test['evaluator_sha256'] = 'stale'
    if fault == 'output': test['output_path_sha256'] = 'stale'
    if fault == 'freeze_binding': test['freeze_approval_sha256'] = 'stale'
    monkeypatch.setattr(evaluate, 'verified_models', lambda *_: pytest.fail('Model loaded before authorization'))
    monkeypatch.setattr(evaluate, 'load_held_out', lambda: pytest.fail('Real Test loader reached'))
    with pytest.raises(ValueError): evaluate.run(out, freeze, test, opt_in=fault != 'opt_in')


def test_once_only_claim_survives_failure_and_no_overwrite(tmp_path):
    path = tmp_path / 'claim.json'
    evaluate.claim_once(path, {'state': 'started'})
    with pytest.raises(FileExistsError): evaluate.claim_once(path, {'state': 'retry'})
    assert json.loads(path.read_text()) == {'state': 'started'}


def test_direct_heldout_loader_rejected_without_reading_any_file(monkeypatch):
    monkeypatch.setattr(evaluate.prep.MANIFEST.__class__, 'read_bytes', lambda *_: pytest.fail('File read'))
    with pytest.raises(ValueError, match='authorized claimed run'): evaluate.load_held_out()


def test_prediction_has_no_fit_or_label_input(monkeypatch):
    x, _ = synthetic_inputs(20)
    class Frozen:
        def predict_proba(self, frame): return np.tile([.7, .3], (len(frame), 1))
        def fit(self, *_): pytest.fail('Predictive model fit')
    p = evaluate.predict_frozen({'XGBoost_A_raw': Frozen(), 'Logistic_C1_raw': Frozen()}, x, .248)
    assert np.all(p['XGBoost_A_raw'] == .3) and np.all(p['Training_rate'] == .248)
    with pytest.raises(ValueError): evaluate.predict_frozen({}, x.assign(OHQ850=1), .2)


def test_metric_correctness_and_fixed_cutoffs():
    y, p = np.array([0, 0, 1, 1]), np.array([.1, .4, .3, .9])
    result = evaluate.score(y, p, .26)
    assert [result[k + ' frozen'] for k in ['TN', 'FP', 'FN', 'TP']] == [1, 1, 0, 2]
    assert result['Sensitivity frozen'] == 1 and result['Specificity frozen'] == .5
    assert [result[k] for k in ['TN', 'FP', 'FN', 'TP']] == [2, 0, 1, 1]
    assert result['Brier'] == pytest.approx(np.mean((y - p)**2))


def test_paired_bootstrap_reproducible_and_identical_model_delta_zero():
    y = np.array([0, 0, 1, 1])
    p = np.array([.1, .4, .3, .9])
    values = {name: p.copy() for name in ['XGBoost_A_raw', 'Logistic_C1_raw', 'Training_rate']}
    thresholds = {name: .26 for name in values}
    a = evaluate.paired_intervals(y, values, thresholds, repetitions=30)
    assert a == evaluate.paired_intervals(y, values, thresholds, repetitions=30)
    assert a['undefined_draws'] > 0
    assert all(interval == [0, 0] for row in a['XGBoost_minus_comparator_95'].values() for interval in row.values())


@pytest.mark.parametrize('p', [np.array([0., 1., .3, .7]), np.array([.3] * 4)])
def test_undefined_diagnostics_are_explicit_json_null_and_scores_unchanged(p):
    original = p.copy()
    result = evaluate.calibration_summary(np.array([0, 1, 0, 1]), p)
    json.dumps(result, allow_nan=False)
    np.testing.assert_array_equal(original, p)
    if np.ptp(p) == 0:
        assert result['intercept'] is result['slope'] is None
        assert 'constant' in result['status']


def test_generated_end_to_end_fixed_predictions_only_and_one_shot(tmp_path, monkeypatch):
    import subprocess
    x, y = synthetic_inputs(100)
    # The shared numeric fixture spans age0..99; this cohort test needs30..80.
    x['RIDAGEYR'] = 30 + np.arange(len(x)) % 51
    x['RIAGENDR'] = np.where(np.arange(len(x)) % 4 < 2, '1', '2')
    model = evaluate.prep.make_comparison_pipeline(evaluate.prep.BASELINE_CONFIGURATION)
    model.fit(x, y)  # Generated fixture setup; evaluator may not fit this model.
    models = {'XGBoost_A_raw': model, 'Logistic_C1_raw': model}
    out = tmp_path / 'data/output'
    monkeypatch.setattr(evaluate.prep, 'ROOT', tmp_path)
    monkeypatch.setattr(evaluate, 'CLAIM', tmp_path / 'data/claim.json')
    monkeypatch.setattr(subprocess, 'run', lambda *_args, **_kwargs: None)
    monkeypatch.setattr(evaluate, 'verified_models', lambda load=True: ({'baseline': {'probability': .248}}, models if load else {}))
    calls = []
    def generated_loader(**_):
        calls.append('generated_only')
        return x, y
    monkeypatch.setattr(evaluate, 'load_held_out', generated_loader)
    monkeypatch.setattr(Pipeline, 'fit', lambda *_args, **_kwargs: pytest.fail('Evaluator refit predictive model'))
    original = evaluate.paired_intervals
    monkeypatch.setattr(evaluate, 'paired_intervals', lambda a, b, c: original(a, b, c, repetitions=10))
    original_groups = evaluate.subgroup_rows
    monkeypatch.setattr(evaluate, 'subgroup_rows', lambda *args: original_groups(*args, repetitions=10))
    freeze, test = approvals(out)
    result = evaluate.run(out, freeze, test, opt_in=True)
    assert result['predictive_fits'] == 0 and result['threshold_tuning'] is False
    assert result['thresholds'] == {'XGBoost_A_raw': .26, 'Logistic_C1_raw': .28, 'Training_rate': .5}
    assert calls == ['generated_only']
    assert (out / 'results.json').is_file()
    out2 = tmp_path / 'data/another_output'
    freeze2, test2 = approvals(out2)
    with pytest.raises(FileExistsError): evaluate.run(out2, freeze2, test2, opt_in=True)
    assert calls == ['generated_only']  # No second decode, even with a fresh output.
