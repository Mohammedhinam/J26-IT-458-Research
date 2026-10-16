"""Generated numeric features only; real cache/image loading is forbidden."""
import numpy as np
import pytest
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import f1_score

from src.vision import nested_feature_probe as nested


def generated():
    y = np.repeat(np.arange(1, 5), 20)
    ids = [f'generated/{i:03}' for i in range(len(y))]
    groups = np.array([f'group{i:03}' for i in range(len(y))])
    x = np.eye(4)[y - 1] + np.random.default_rng(42).normal(0, .8, (len(y), 4))
    return x, ids, y, groups, nested.base.make_folds(ids, y, groups.tolist())


def test_generated_nested_coverage_reproducibility_and_isolation(monkeypatch):
    x, ids, y, groups, folds = generated()
    original = nested.select
    calls = []
    def checked_select(features, labels, selected_groups):
        f = len(calls) % 5
        fitting = folds != f
        np.testing.assert_array_equal(features, x[fitting])
        np.testing.assert_array_equal(labels, y[fitting])
        np.testing.assert_array_equal(selected_groups, groups[fitting])
        calls.append(f)
        return original(features, labels, selected_groups)
    monkeypatch.setattr(nested, 'select', checked_select)
    monkeypatch.setattr(nested.cached, 'cached_inputs', lambda *_: pytest.fail('Real cache read'))
    a, evidence = nested.nested_predictions(x, ids, y, groups, folds)
    b, repeated = nested.nested_predictions(x, ids, y, groups, folds)
    np.testing.assert_array_equal(a, b)
    assert evidence == repeated and len(calls) == 10
    assert sum(row['fit_count'] for row in evidence) == 95
    assert sorted(i for row in evidence for i in row['scoring_indices']) == list(range(80))
    for row in evidence:
        fit, score = row['fitting_indices'], row['scoring_indices']
        assert not set(groups[fit]) & set(groups[score])
        np.testing.assert_allclose(row['scaler_mean'], x[fit].mean(0), atol=1e-12)
        assert len(row['inner_results']) == 6


def test_inner_scaler_and_class_weight_fit_only_on_inner_rows(monkeypatch):
    x, _, y, groups, _ = generated()
    original = nested.fit
    seen = []
    expected = nested.inner_splits(y, groups)
    def checked(model, features, labels):
        fitting = expected[len(seen) % 3][0]
        np.testing.assert_array_equal(features, x[fitting])
        np.testing.assert_array_equal(labels, y[fitting])
        answer = original(model, features, labels)
        np.testing.assert_allclose(answer[0].mean_, features.mean(0), atol=1e-12)
        seen.append(model[1].class_weight)
        return answer
    monkeypatch.setattr(nested, 'fit', checked)
    selected, rows = nested.select(x, y, groups)
    assert len(seen) == 18 and seen.count('balanced') == seen.count(None) == 9
    assert selected in nested.configurations()
    # One independently assembled inner metric agrees with the saved selector score.
    scores = []
    for fitting, scoring in expected:
        model = original(nested.pipeline(rows[0]['config']), x[fitting], y[fitting])
        scores.append(f1_score(y[scoring], model.predict(x[scoring]),
                               labels=[1, 2, 3, 4], average='macro', zero_division=0))
    assert rows[0]['mean_macro_f1'] == np.mean(scores)


def test_tie_break_is_predeclared_and_deterministic():
    rows = [{'config': config, 'mean_macro_f1': .2, 'mean_qwk': .1}
            for config in nested.configurations()]
    assert min(reversed(rows), key=nested.selection_key)['config'] == {'C': .01, 'class_weight': None}


@pytest.mark.parametrize('fault', ['nan', 'folds', 'labels', 'ids', 'groups'])
def test_bad_membership_fails_before_fitting(monkeypatch, fault):
    x, ids, y, groups, folds = generated()
    if fault == 'nan': x[0, 0] = np.nan
    if fault == 'folds': folds = (folds + 1) % 5
    if fault == 'labels': y[0] = 0
    if fault == 'ids': ids[0] = ids[1]
    if fault == 'groups': groups[:] = 'one'
    monkeypatch.setattr(nested, 'fit', lambda *_: pytest.fail('Invalid input reached fitting'))
    with pytest.raises(ValueError): nested.nested_predictions(x, ids, y, groups, folds)


def test_convergence_failure_stops_without_fallback(monkeypatch):
    class Failing:
        def fit(self, *_):
            import warnings
            warnings.warn('generated convergence failure', ConvergenceWarning)
    with pytest.raises(ConvergenceWarning): nested.fit(Failing(), np.zeros((4, 2)), np.arange(1, 5))


def test_no_cache_access_without_fresh_owner_scope(monkeypatch):
    monkeypatch.setattr(nested.cached, 'cached_inputs', lambda *_: pytest.fail('Cache read'))
    with pytest.raises(ValueError, match='opt-in'): nested.run_authorized('/x', '/y', {})
    with pytest.raises(ValueError, match='scope'):
        nested.run_authorized('/x', '/y', {'status': 'owner_confirmed', 'scope': nested.cached.SCOPE}, opt_in=True)
