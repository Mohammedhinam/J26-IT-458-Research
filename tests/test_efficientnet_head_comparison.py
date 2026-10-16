"""Generated numeric features only; no image/model inference or downloads."""
import json

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.vision import efficientnet_head_comparison as head


def small_fixture():
    labels = np.repeat(np.arange(1, 5), [10, 20, 30, 40])
    ids = [f'generated/{i:03}' for i in range(len(labels))]
    groups = [f'g{i:03}' for i in range(len(labels))]
    x = np.eye(4)[labels - 1] + np.random.default_rng(42).normal(0, .8, (len(labels), 4))
    folds = head.base.make_folds(ids, labels, groups)
    return x, ids, labels, groups, folds


def generated_cache(tmp_path, monkeypatch, fault=None):
    root = tmp_path / 'reference'
    root.mkdir()
    y = np.repeat(np.arange(1, 5), [12, 84, 223, 361])
    ids = np.array([f'Training/synthetic_{i:04}' for i in range(680)])
    groups = np.array([f'g{i:04}' for i in range(680)])
    folds = head.base.make_folds(ids.tolist(), y, groups.tolist())
    features = np.zeros((680, 1280), np.float32)
    features[:, :4] = np.eye(4)[y - 1]
    cache = {'features': features, 'ids': ids.copy(), 'labels': y.copy(),
             'groups': groups.copy(), 'folds': folds.copy()}
    probability = np.eye(4)[y - 1] * .8 + .05
    oof = {'ids': ids.copy(), 'labels': y.copy(), 'folds': folds.copy(),
           'linear': probability, 'majority': np.tile([0., 0., 0., 1.], (680, 1)),
           'prior': np.tile(np.bincount(y, minlength=5)[1:] / 680, (680, 1))}
    result = {'config': dict(head.encoder.CONFIG),
              'bindings': {'code_sha256': head.base.b1.digest_json(head.encoder.code_hashes())}}
    if fault == 'feature_membership': cache['ids'][0] = 'Validation/synthetic'
    if fault == 'oof_membership': oof['ids'][0] = 'Training/wrong'
    if fault == 'folds': cache['folds'] = (folds + 1) % 5
    if fault == 'labels': cache['labels'][0] = 0
    if fault == 'groups': cache['groups'][0] = cache['groups'][1]
    if fault == 'fields': cache['other'] = np.zeros(1)
    if fault == 'dtype': cache['features'] = features.astype(np.float64)
    if fault == 'nan': cache['features'][0, 0] = np.nan
    if fault == 'reference_config': result['config']['C'] = 10
    if fault == 'np015': cache['ids'][0] = head.base.legacy.NP015_IDS[0]
    np.savez(root / 'features.npz', **cache)
    np.savez(root / 'oof.npz', **oof)
    (root / 'results.json').write_text(json.dumps(result))
    # Pin fixture digests only in this generated unit-test process.
    monkeypatch.setattr(head, 'FEATURES_SHA', head.base.legacy.sha256(root / 'features.npz'))
    monkeypatch.setattr(head, 'RESULTS_SHA', head.base.legacy.sha256(root / 'results.json'))
    monkeypatch.setattr(head, 'OOF_SHA', head.base.legacy.sha256(root / 'oof.npz'))
    monkeypatch.setattr(head.encoder, 'FOLD_SHA', head.base.b1.digest_json(folds.tolist()))
    if fault == 'features_hash': monkeypatch.setattr(head, 'FEATURES_SHA', '0' * 64)
    if fault == 'reference_hash': monkeypatch.setattr(head, 'RESULTS_SHA', '0' * 64)
    if fault == 'oof_hash': monkeypatch.setattr(head, 'OOF_SHA', '0' * 64)
    return root


def test_unweighted_fit_matches_independent_pipeline_and_fold_scaler():
    x, ids, y, groups, folds = small_fixture()
    a, evidence = head.fit_unweighted(x, ids, y, groups, folds)
    b, repeated = head.fit_unweighted(x, ids, y, groups, folds)
    np.testing.assert_array_equal(a, b)
    assert evidence == repeated
    for f, info in enumerate(evidence):
        fit, score = folds != f, folds == f
        reference = make_pipeline(StandardScaler(), LogisticRegression(
            C=1., class_weight=None, solver='lbfgs', max_iter=2000, random_state=42))
        reference.fit(x[fit], y[fit])
        np.testing.assert_allclose(a[score], reference.predict_proba(x[score]), rtol=0, atol=1e-12)
        np.testing.assert_allclose(info['scaler_mean'], x[fit].mean(0), rtol=0, atol=1e-12)
        assert info['class_weight'] is None
        assert not set(np.array(groups)[fit]) & set(np.array(groups)[score])


@pytest.mark.parametrize('fault', ['nan', 'folds', 'labels', 'ids'])
def test_invalid_fit_membership_rejected(fault):
    x, ids, y, groups, folds = small_fixture()
    if fault == 'nan': x[0, 0] = np.nan
    if fault == 'folds': folds = (folds + 1) % 5
    if fault == 'labels': y[0] = 0
    if fault == 'ids': ids[0] = ids[1]
    with pytest.raises(ValueError): head.fit_unweighted(x, ids, y, groups, folds)


def test_generated_cache_roundtrip(tmp_path, monkeypatch):
    root = generated_cache(tmp_path, monkeypatch)
    features, ids, y, groups, folds, prior = head.cached_inputs(root)
    assert features.shape == (680, 1280) and features.dtype == np.float32
    assert len(ids) == len(set(groups)) == 680
    assert np.bincount(y, minlength=5).tolist() == [0, 12, 84, 223, 361]
    assert set(prior) == {'balanced', 'majority', 'prior'}


@pytest.mark.parametrize('fault', ['features_hash', 'reference_hash', 'oof_hash', 'feature_membership',
                                 'oof_membership', 'folds', 'labels', 'groups', 'fields', 'dtype',
                                 'nan', 'reference_config', 'np015'])
def test_generated_cache_corruption_rejected(tmp_path, monkeypatch, fault):
    root = generated_cache(tmp_path, monkeypatch, fault)
    with pytest.raises(ValueError): head.cached_inputs(root)


def test_no_data_read_without_scope_or_current_bindings(monkeypatch):
    monkeypatch.setattr(head, 'cached_inputs', lambda *_: pytest.fail('Numeric payload read before authorization'))
    with pytest.raises(ValueError, match='opt-in'):
        head.run_authorized('/Test', '/out', {})
    with pytest.raises(ValueError, match='scope'):
        head.run_authorized('/Test', '/out', {'status': 'owner_confirmed', 'scope': head.encoder.SCOPE}, opt_in=True)
    owner = {'status': 'owner_confirmed', 'scope': head.SCOPE, 'authorizer': 'synthetic',
             'date': '2026-10-16', 'evidence_reference': 'generated unit fixture',
             'acknowledgements': {k: True for k in head.base.legacy.ACKS}}
    with pytest.raises(ValueError, match='binding'):
        head.run_authorized('/Test', '/out', owner, opt_in=True)


def test_paired_intervals_identity_and_determinism():
    x, ids, y, groups, folds = small_fixture()
    p, _ = head.fit_unweighted(x, ids, y, groups, folds)
    values = {name: p for name in ['unweighted', 'balanced', 'majority', 'prior']}
    a = head.paired_intervals(y, groups, values, repetitions=20)
    assert a == head.paired_intervals(y, groups, values, repetitions=20)
    assert a['undefined_draws'] == 0 and a['conditional_only']
    for difference in a['unweighted_minus_reference_95'].values():
        assert all(v == [0., 0.] for v in difference.values())


def test_generated_authorized_run_without_image_or_encoder_access(tmp_path, monkeypatch):
    root = generated_cache(tmp_path, monkeypatch)
    output = tmp_path / 'output'
    monkeypatch.setattr(head.base.bundle, 'model_array', lambda *_: pytest.fail('Image array accessed'))
    monkeypatch.setattr(head.encoder, 'extract_features', lambda *_: pytest.fail('Encoder executed'))
    monkeypatch.setattr(head.base.legacy, 'new_ignored_output', lambda path, prefix: None)
    original = head.paired_intervals
    monkeypatch.setattr(head, 'paired_intervals', lambda y, g, p: original(y, g, p, repetitions=10))
    authorization = {'status': 'owner_confirmed', 'scope': head.SCOPE, 'authorizer': 'synthetic fixture',
                     'date': '2026-10-16', 'evidence_reference': 'generated unit test only',
                     'acknowledgements': {k: True for k in head.base.legacy.ACKS},
                     **head.bindings(root, output)}
    result = head.run_authorized(root, output, authorization, opt_in=True)
    assert result['new_classifier_fits'] == 5 and result['encoder_executed'] is False
    assert result['test_used'] is False and result['validation53_used'] is False
    assert result['oof_sha256'] == head.base.legacy.sha256(output / 'oof.npz')
    with pytest.raises(ValueError, match='Fresh separate'):
        head.run_authorized(root, output, authorization, opt_in=True)
