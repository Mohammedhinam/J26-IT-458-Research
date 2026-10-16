"""Prepared cached-feature experiment. Real execution requires fresh owner scope."""
import json
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import efficientnet_head_comparison as cached

base = cached.base
SCOPE = 'run_training680_nested_efficientnet_head_v1'
CONFIG = {
    'version': 'training680-nested-efficientnet-head-v1', 'seed': 42,
    'outer_folds': 5, 'inner_folds': 3, 'C': [.01, .1, 1.],
    'class_weight': [None, 'balanced'], 'solver': 'lbfgs', 'max_iter': 2000,
    'selection': 'mean_inner_macro_f1_then_mean_qwk_then_smaller_C_then_unweighted',
    'maximum_fits': 95, 'bootstrap': 1000, 'encoder_execution': False}


def configurations():
    return [{'C': c, 'class_weight': weight}
            for c in CONFIG['C'] for weight in CONFIG['class_weight']]


def pipeline(config):
    # Scaling and balanced weights are learned from each fitting subset only.
    return make_pipeline(StandardScaler(), LogisticRegression(
        **config, solver='lbfgs', max_iter=2000, random_state=42))


def fit(model, features, labels):
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        model.fit(features, labels)
    if model.classes_.tolist() != [1, 2, 3, 4]:
        raise ValueError('Four-grade class mapping required')
    return model


def inner_splits(labels, groups):
    """This function receives outer-fitting rows only, never outer scoring rows."""
    splitter = StratifiedGroupKFold(3, shuffle=True, random_state=42)
    splits = list(splitter.split(np.zeros(len(labels)), labels, groups))
    for fitting, scoring in splits:
        if (set(groups[fitting]) & set(groups[scoring])
                or set(labels[fitting]) != {1, 2, 3, 4}
                or set(labels[scoring]) != {1, 2, 3, 4}):
            raise ValueError('Inner group leakage or insufficient grade support')
    return splits


def selection_key(row):
    return (-row['mean_macro_f1'], -row['mean_qwk'], row['config']['C'],
            row['config']['class_weight'] is not None)


def select(features, labels, groups):
    splits = inner_splits(labels, groups)
    rows = []
    for config in configurations():
        f1, kappa = [], []
        for fitting, scoring in splits:
            model = fit(pipeline(config), features[fitting], labels[fitting])
            prediction = model.predict(features[scoring])
            f1.append(f1_score(labels[scoring], prediction, labels=[1, 2, 3, 4],
                               average='macro', zero_division=0))
            kappa.append(cohen_kappa_score(labels[scoring], prediction,
                                          labels=[1, 2, 3, 4], weights='quadratic'))
        if not np.isfinite([*f1, *kappa]).all():
            raise ValueError('Undefined inner selection metric')
        rows.append({'config': config, 'mean_macro_f1': float(np.mean(f1)),
                     'mean_qwk': float(np.mean(kappa))})
    return min(rows, key=selection_key)['config'], rows


def nested_predictions(features, ids, labels, groups, folds):
    """Outer labels are used for scoring only after all predictions are fixed."""
    features = np.asarray(features)
    labels = base.pilot.checked_grades(labels)
    groups, folds = np.asarray(groups), np.asarray(folds)
    if (features.ndim != 2 or len(features) != len(labels)
            or not np.isfinite(features).all()
            or not np.array_equal(folds, base.make_folds(list(ids), labels, groups.tolist()))):
        raise ValueError('Finite aligned features and original folds required')
    probabilities = np.full((len(labels), 4), np.nan)
    evidence = []
    for fold in range(5):
        fitting, scoring = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        config, candidates = select(features[fitting], labels[fitting], groups[fitting])
        model = fit(pipeline(config), features[fitting], labels[fitting])
        probabilities[scoring] = model.predict_proba(features[scoring])
        evidence.append({'outer_fold': fold, 'fitting_indices': fitting.tolist(),
                         'scoring_indices': scoring.tolist(), 'selected': config,
                         'inner_results': candidates, 'fit_count': 19,
                         'scaler_mean': model[0].mean_.tolist(),
                         'iterations': model[1].n_iter_.tolist()})
    base.measure(labels, probabilities)
    return probabilities, evidence


def bindings(root, output):
    return {**cached.bindings(root, output),
            'config_sha256': base.b1.digest_json(CONFIG),
            'code_sha256': base.b1.digest_json({**cached.code_hashes(),
                'nested_feature_probe.py': base.legacy.sha256(__file__)})}


def run_authorized(root, output, authorization, *, opt_in=False):
    """No real inputs read without exact new scope, current hashes and fresh path."""
    if not opt_in:
        raise ValueError('Fresh nested-experiment owner opt-in required')
    root, output = Path(root), Path(output)
    expected = bindings(root, output)
    base.legacy.authorise(authorization, SCOPE, expected, opt_in=True)
    base.legacy.new_ignored_output(output, 'data')
    if (output.exists() or output.resolve().is_relative_to(root.resolve())
            or root.resolve().is_relative_to(output.resolve())):
        raise ValueError('Fresh separate output required')
    features, ids, labels, groups, folds, reference = cached.cached_inputs(root)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'protocol.json').write_text(json.dumps(
        {'config': CONFIG, 'bindings': expected}, indent=2) + '\n')
    probabilities, evidence = nested_predictions(features, ids, labels, groups, folds)
    np.savez(output / 'oof.npz', ids=ids, labels=labels, groups=groups,
             folds=folds, nested=probabilities, **reference)
    (output / 'fold_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    scores = {'linear': probabilities, **reference}
    result = {'notice': base.legacy.NOTICE, 'config': CONFIG, 'bindings': expected,
              'metrics': {name: base.measure(labels, values) for name, values in scores.items()},
              'uncertainty': base.paired_intervals(labels, groups, scores),
              'fit_count': sum(row['fit_count'] for row in evidence),
              'oof_sha256': base.legacy.sha256(output / 'oof.npz'),
              'test_used': False, 'validation53_used': False,
              'encoder_executed': False, 'final_model': False}
    (output / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result
