"""One opt-in, cached-feature class-weight comparison. No image/model loader."""
import json
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import efficientnet_feature_probe as encoder

base = encoder.base
VERSION = 'training680-efficientnet-unweighted-head-v1'
SCOPE = 'run_training680_cached_unweighted_head_v1'
FEATURES_SHA = 'd8cda6807e7954e2dd8d7cf20be77b46e5063f89910436df294381901231d838'
RESULTS_SHA = 'd450ea6a9e21d560a3e21b51df707a538b676783575e9ebe25b4d3ca84bf0eb8'
OOF_SHA = 'c78fd5be1507c0e4b18b9cafff2a8f63ef12fac2d584c1fea52d1ae1b863d8cb'
CONFIG = {**encoder.CONFIG, 'version': VERSION, 'class_weight': None,
          'new_classifier_fits': 5, 'encoder_execution': False}
INTERVAL_METRICS = ['accuracy', 'macro_f1_four_grades', 'balanced_accuracy',
                    'quadratic_weighted_kappa', 'multiclass_brier']


def code_hashes():
    return {**encoder.code_hashes(), 'efficientnet_head_comparison.py': base.legacy.sha256(__file__)}


def bindings(root, output):
    """Check authorization against fixed hashes before reading numeric payloads."""
    return {'features_sha256': FEATURES_SHA, 'reference_results_sha256': RESULTS_SHA,
            'reference_oof_sha256': OOF_SHA, 'fold_sha256': encoder.FOLD_SHA,
            'config_sha256': base.b1.digest_json(CONFIG), 'code_sha256': base.b1.digest_json(code_hashes()),
            'input_path_sha256': base.sha256(str(Path(root).resolve()).encode()).hexdigest(),
            'output_path_sha256': base.sha256(str(Path(output).resolve()).encode()).hexdigest()}


def cached_inputs(root):
    """Trusted original Training cache only; no dataset manifest/image access."""
    paths = {name: base.legacy.safe_file(root, name) for name in ['features.npz', 'results.json', 'oof.npz']}
    for name, digest in [('features.npz', FEATURES_SHA), ('results.json', RESULTS_SHA), ('oof.npz', OOF_SHA)]:
        if base.legacy.sha256(paths[name]) != digest:
            raise ValueError('Cached reference SHA mismatch: ' + name)
    reference = base.bundle.load_json(paths['results.json'])
    if reference['config'] != encoder.CONFIG or reference['bindings']['code_sha256'] != base.b1.digest_json(encoder.code_hashes()):
        raise ValueError('Reference configuration/code changed')
    # Membership metadata is decoded before features, and exact old folds are required.
    with np.load(paths['features.npz'], allow_pickle=False) as cache:
        ids, labels, groups, folds = cache['ids'], cache['labels'], cache['groups'], cache['folds']
    if (len(ids) != 680 or len(set(ids)) != 680 or ids.tolist() != sorted(ids.tolist())
            or any(not value.startswith('Training/') for value in ids)
            or set(ids) & set(base.legacy.NP015_IDS)
            or np.bincount(base.pilot.checked_grades(labels), minlength=5).tolist() != [0, 12, 84, 223, 361]
            or len(set(groups)) != 680):
        raise ValueError('Pinned Training680 membership/support mismatch')
    if (base.b1.digest_json(folds.tolist()) != encoder.FOLD_SHA
            or not np.array_equal(folds, base.make_folds(ids.tolist(), labels, groups.tolist()))):
        raise ValueError('Frozen fold membership mismatch')
    features = encoder.load_cache(paths['features.npz'], FEATURES_SHA, ids, labels, groups, folds)
    with np.load(paths['oof.npz'], allow_pickle=False) as saved:
        if set(saved.files) != {'ids', 'labels', 'folds', 'linear', 'majority', 'prior'}:
            raise ValueError('Reference OOF fields mismatch')
        for key, expected in [('ids', ids), ('labels', labels), ('folds', folds)]:
            if not np.array_equal(saved[key], expected):
                raise ValueError('Reference OOF membership mismatch')
        probabilities = {'balanced': saved['linear'], 'majority': saved['majority'], 'prior': saved['prior']}
    for values in probabilities.values():
        base.measure(labels, values)
    return features, ids, labels, groups, folds, probabilities


def fit_unweighted(features, ids, labels, groups, folds):
    """Each scoring record is excluded from its scaler and classifier fitting."""
    features = np.asarray(features)
    labels = base.pilot.checked_grades(labels)
    if features.ndim != 2 or features.shape[0] != len(labels) or not np.isfinite(features).all():
        raise ValueError('Finite aligned features required')
    if not np.array_equal(folds, base.make_folds(ids, labels, groups)):
        raise ValueError('Fold membership changed')
    predictions = np.full((len(labels), 4), np.nan)
    evidence = []
    for fold in range(5):
        fitting, scoring = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        model = make_pipeline(StandardScaler(), LogisticRegression(
            C=1., class_weight=None, solver='lbfgs', max_iter=2000, random_state=42))
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            model.fit(features[fitting], labels[fitting])
        if model.classes_.tolist() != [1, 2, 3, 4]:
            raise ValueError('Class mapping mismatch')
        predictions[scoring] = model.predict_proba(features[scoring])
        evidence.append({'fold': fold, 'fit_n': len(fitting), 'score_n': len(scoring),
                         'scaler_mean': model[0].mean_.tolist(),
                         'class_weight': model[1].class_weight, 'iterations': model[1].n_iter_.tolist()})
    base.measure(labels, predictions)
    return predictions, evidence


def paired_intervals(labels, groups, probabilities, repetitions=1000):
    """Paired bootstrap of saved OOF; class and model-selection uncertainty remain."""
    labels, groups = np.asarray(labels), np.asarray(groups)
    unique = np.unique(groups)
    members = {group: np.flatnonzero(groups == group) for group in unique}
    rng = np.random.default_rng(42)
    draws = {name: {key: [] for key in INTERVAL_METRICS} for name in ['balanced', 'majority', 'prior']}
    undefined = 0
    for _ in range(repetitions):
        index = np.concatenate([members[group] for group in rng.choice(unique, len(unique), replace=True)])
        if set(labels[index]) != {1, 2, 3, 4}:
            undefined += 1
            continue
        measured = {name: base.measure(labels[index], values[index]) for name, values in probabilities.items()}
        for name in draws:
            for key in INTERVAL_METRICS:
                draws[name][key].append(measured['unweighted'][key] - measured[name][key])
    return {'repetitions': repetitions, 'undefined_draws': undefined, 'conditional_only': True,
            'participant_independence_verified': False,
            'unweighted_minus_reference_95': {
                name: {key: np.quantile(values, [.025, .975]).tolist() if values else None
                       for key, values in metrics.items()} for name, metrics in draws.items()}}


def run_authorized(root, output, authorization, *, opt_in=False):
    """Exactly one cached-head run; no image access or reuse of old permission."""
    if not opt_in:
        raise ValueError('Fresh owner opt-in required before data access')
    root, output = Path(root), Path(output)
    expected = bindings(root, output)
    base.legacy.authorise(authorization, SCOPE, expected, opt_in=True)
    base.legacy.new_ignored_output(output, 'data')
    if output.exists() or output.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(output.resolve()):
        raise ValueError('Fresh separate output required')
    features, ids, labels, groups, folds, reference = cached_inputs(root)
    output.mkdir(parents=True, exist_ok=False)
    # Persist settings before any fitting; do not rerun the balanced reference.
    (output / 'protocol.json').write_text(json.dumps({'config': CONFIG, 'bindings': expected,
                                                    'ids': ids.tolist(), 'folds': folds.tolist()}, indent=2))
    probabilities, evidence = fit_unweighted(features, ids.tolist(), labels, groups.tolist(), folds)
    predictions = {'unweighted': probabilities, **reference}
    np.savez(output / 'oof.npz', ids=ids, labels=labels, groups=groups, folds=folds, **predictions)
    (output / 'fold_checks.json').write_text(json.dumps(evidence, indent=2))
    summary = {'notice': base.legacy.NOTICE, 'config': CONFIG, 'bindings': expected,
               'metrics': {name: base.measure(labels, values) for name, values in predictions.items()},
               'uncertainty': paired_intervals(labels, groups, predictions),
               'oof_sha256': base.legacy.sha256(output / 'oof.npz'),
               'new_classifier_fits': 5, 'encoder_executed': False, 'test_used': False,
               'validation53_used': False, 'real_run': True}
    (output / 'results.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    return summary
