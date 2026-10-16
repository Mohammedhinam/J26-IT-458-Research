"""Prepared one-shot evaluator. Importing never loads held-out data or models."""
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from . import finalise_development as prep
from .calibration_threshold_nhanes import calibration_diagnostic, operating_metrics, reliability_rows
from .subgroup_evidence import subgroup_rows

FREEZE_DIR = prep.ROOT / 'data/tabular_final_freeze_v1_20261016T143007292661Z'
RECEIPT_SHA = 'e08073b43e89ba99982483344e2612f577f46ae8ee0988b2458e5cfc2b8c6e0c'
FREEZE_SCOPE = 'approve_tabular_numerical_freeze_v1'
EVALUATE_SCOPE = 'evaluate_frozen_tabular_1563_once_v1'
CLAIM = prep.ROOT / 'data/tabular_final_test_once_v1/evaluation_claim.json'
_LOAD_CAPABILITY = object()
INTERVAL_METRICS = ['AUROC', 'PR-AUC (trapezoidal)', 'Average precision', 'Brier',
                    'Sensitivity @0.50', 'Specificity @0.50',
                    'Sensitivity frozen', 'Specificity frozen']


def bindings(output):
    return {'receipt_sha256': RECEIPT_SHA, 'evaluator_sha256': prep.digest(__file__),
            'subgroup_code_sha256': prep.digest(Path(__file__).with_name('subgroup_evidence.py')),
            'output_path_sha256': hashlib.sha256(str(Path(output).resolve()).encode()).hexdigest()}


def authorize(freeze, evaluation, output, *, opt_in=False):
    """Numerical freeze approval and Test permission are two distinct scopes."""
    if not opt_in:
        raise ValueError('Explicit final-evaluation opt-in required')
    for record, scope in [(freeze, FREEZE_SCOPE), (evaluation, EVALUATE_SCOPE)]:
        if (not isinstance(record, dict) or record.get('scope') != scope
                or record.get('status') != 'owner_confirmed'
                or not all(record.get(k) for k in ['authorizer', 'date', 'evidence_reference'])
                or record.get('receipt_sha256') != RECEIPT_SHA):
            raise ValueError('Separate numerical freeze and final Test approvals required')
    if evaluation.get('test_access_authorized') is not True:
        raise ValueError('Explicit Test access permission missing')
    freeze_sha = hashlib.sha256(json.dumps(freeze, sort_keys=True).encode()).hexdigest()
    if evaluation.get('freeze_approval_sha256') != freeze_sha:
        raise ValueError('Test permission must bind the separate numerical freeze approval')
    if any(evaluation.get(k) != v for k, v in bindings(output).items()):
        raise ValueError('Final evaluator/output binding mismatch')


def claim_once(path, evidence):
    """Claim before decoding; failure retains the claim, never auto-retries."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(evidence, stream, indent=2)


def verified_models(load=True):
    path = FREEZE_DIR / 'freeze_receipt.json'
    if path.is_symlink() or prep.digest(path) != RECEIPT_SHA:
        raise ValueError('Frozen receipt changed')
    receipt = json.loads(path.read_text())
    runtime = {'python': prep.platform.python_version(), 'numpy': np.__version__,
               'pandas': prep.baseline.pd.__version__, 'sklearn': prep.baseline.sklearn.__version__,
               'xgboost': prep.xgboost.__version__, 'joblib': joblib.__version__}
    if runtime != receipt['runtime']:
        raise ValueError('Frozen runtime versions changed; qualify before Test access')
    prep.verify_inputs()
    if receipt['bindings'] != prep.bindings(FREEZE_DIR):
        raise ValueError('Prepared code/protocol bindings changed')
    for name, digest in receipt['output_files_sha256'].items():
        file = FREEZE_DIR / name
        if file.is_symlink() or prep.digest(file) != digest:
            raise ValueError('Prepared artifact changed: ' + name)
    if (receipt['decisions']['XGBoost_A_raw']['decision']['threshold'] != .26
            or receipt['decisions']['Logistic_C1_raw']['decision']['threshold'] != .28
            or receipt['calibration'] != 'none_raw'):
        raise ValueError('Frozen choices differ')
    # Only byte-verified locally created pickle artifacts may be deserialized.
    if prep.MODEL.is_symlink() or prep.digest(prep.MODEL) != receipt['primary_artifact']['sha256']:
        raise ValueError('Primary model changed')
    if not load:
        return receipt, {}
    primary = joblib.load(prep.MODEL).model
    comparator = joblib.load(FREEZE_DIR / 'logistic_model.joblib')
    for model in [primary, comparator]:
        if (model.classes_.tolist() != [0, 1]
                or list(model.feature_names_in_) != list(prep.FEATURES)
                or len(model['preprocess'].get_feature_names_out()) != 47):
            raise ValueError('Frozen class/feature schema mismatch')
    return receipt, {'XGBoost_A_raw': primary, 'Logistic_C1_raw': comparator}


def load_held_out(*, _capability=None):
    """Called only after two approvals and the exclusive once-only claim."""
    if _capability is not _LOAD_CAPABILITY:
        raise ValueError('Held-out loader is only available through the authorized claimed run')
    raw = prep.MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != prep.MANIFEST_SHA:
        raise ValueError('Frozen split changed')
    manifest = json.loads(raw)
    ids, development = manifest['held_out'], manifest['development']
    if len(ids) != 1563 or len(set(ids)) != 1563 or set(ids) & set(development):
        raise ValueError('Held-out membership mismatch')
    # The audited selective reader accepts an explicit ID allowlist. Its legacy
    # name says development, but it decodes only the IDs passed by this caller.
    tables = {name: prep.baseline.read_development_xpt(prep.baseline.DATA_DIR / (name + '.xpt'), ids)
              for name in prep.baseline.FILES}
    if any(not set(frame['SEQN']) <= set(ids) for frame in tables.values()):
        raise ValueError('Reader returned an unselected participant')
    _, cohort, _ = prep.baseline.join_valid_outcomes(tables)
    cleaned, review, log = prep.baseline.clean_cohort(cohort)
    if set(cleaned['SEQN']) != set(ids) or len(cleaned) != 1563 or not review.empty or log['age_exclusions']:
        raise ValueError('Held-out cleaning/membership changed; do not silently exclude')
    x, y = prep.baseline.model_inputs(cleaned.set_index('SEQN').loc[ids])
    if prep.MANIFEST.read_bytes() != raw:
        raise ValueError('Manifest changed during loading')
    return x, y


def predict_frozen(models, x, prior):
    """Prediction only: no fit, fit_transform, calibration or cutoff selector."""
    if tuple(x.columns) != prep.FEATURES or not x.index.is_unique:
        raise ValueError('Unexpected evaluation feature schema or duplicate IDs')
    probabilities = {name: model.predict_proba(x)[:, 1] for name, model in models.items()}
    probabilities['Training_rate'] = np.full(len(x), prior)
    return probabilities


def score(y, probability, threshold):
    metrics = prep.baseline.score_predictions(y, probability)
    operating = operating_metrics(y, probability >= threshold)
    metrics.update({key + ' frozen': value for key, value in operating.items()})
    return metrics


def calibration_summary(y, probability):
    result = calibration_diagnostic(y, probability)
    # Undefined diagnostics are JSON null with their explicit reason, never zero.
    return {k: None if isinstance(v, float) and not np.isfinite(v) else v
            for k, v in result.items()}


def paired_intervals(y, probabilities, thresholds, repetitions=1000):
    """Same participant resamples across models; fixed scores/cutoffs, no refits."""
    y = np.asarray(y)
    if repetitions < 1:
        raise ValueError('Positive bootstrap count required')
    for name, p in probabilities.items():
        score(y, p, thresholds[name])
    names = list(probabilities)
    rng = np.random.default_rng(42)
    draws = []
    undefined = 0
    for _ in range(repetitions):
        index = rng.integers(0, len(y), len(y))
        if len(np.unique(y[index])) < 2:
            undefined += 1
            continue
        measured = {name: score(y[index], probabilities[name][index], thresholds[name]) for name in names}
        draws.append([[measured[name][key] for key in INTERVAL_METRICS] for name in names])
    if not draws:
        raise ValueError('No defined two-class bootstrap draws')
    values = np.asarray(draws)
    absolute = {name: dict(zip(INTERVAL_METRICS,
        np.quantile(values[:, i, :], [.025, .975], axis=0).T.tolist())) for i, name in enumerate(names)}
    primary = names.index('XGBoost_A_raw')
    differences = {name: dict(zip(INTERVAL_METRICS,
        np.quantile(values[:, primary, :] - values[:, i, :], [.025, .975], axis=0).T.tolist()))
        for i, name in enumerate(names) if i != primary}
    return {'draws': repetitions, 'undefined_draws': undefined, 'absolute_95': absolute,
            'XGBoost_minus_comparator_95': differences, 'predictive_refits': 0,
            'complex_survey_variance': False}


def run(output, freeze_approval, test_approval, *, opt_in=False):
    output = Path(output).resolve()
    authorize(freeze_approval, test_approval, output, opt_in=opt_in)
    if output.exists() or not output.is_relative_to((prep.ROOT / 'data').resolve()):
        raise ValueError('Fresh ignored local output required')
    import subprocess
    for path in [output, CLAIM]:
        if not path.resolve().is_relative_to((prep.ROOT / 'data').resolve()):
            raise ValueError('Canonical claim/output must stay in ignored local data')
        subprocess.run(['git', 'check-ignore', '--quiet', str(path)], cwd=prep.ROOT, check=True)
    receipt, models = verified_models()
    claim_once(CLAIM, {'receipt_sha256': RECEIPT_SHA, 'output': str(output),
                       'state': 'started_no_automatic_retry', 'test_approval': test_approval})
    output.mkdir(parents=True, exist_ok=False)
    # No input loading occurs before this point. A later failure preserves CLAIM.
    x, y = load_held_out(_capability=_LOAD_CAPABILITY)
    thresholds = {'XGBoost_A_raw': .26, 'Logistic_C1_raw': .28, 'Training_rate': .5}
    probabilities = predict_frozen(models, x, receipt['baseline']['probability'])
    measured = {name: score(y, p, thresholds[name]) for name, p in probabilities.items()}
    # These regressions describe calibration of fixed predictions; they are not
    # predictive training or probability mappings applied to the Test results.
    diagnostics = {name: calibration_summary(y, p) for name, p in probabilities.items()}
    reliability = {name: reliability_rows(y, p) for name, p in probabilities.items()}
    intervals = paired_intervals(y.to_numpy(), probabilities, thresholds)
    subgroups = {name: subgroup_rows(y, p, x['RIDAGEYR'].to_numpy(),
                                    x['RIAGENDR'].astype(int).to_numpy())
                 for name, p in probabilities.items()}
    np.savez(output / 'held_out_predictions.npz', SEQN=x.index.to_numpy(), y=y.to_numpy(), **probabilities)
    verified_models(load=False)  # Rehash without another deserialization.
    result = {'status': 'completed_single_frozen_evaluation', 'receipt_sha256': RECEIPT_SHA,
        'n': len(y), 'yes': int(y.sum()), 'no': int(len(y) - y.sum()),
        'thresholds': thresholds, 'metrics': measured, 'calibration_diagnostics': diagnostics,
        'reliability': reliability, 'intervals': intervals, 'predictive_fits': 0,
        'age_recorded_sex_subgroups': subgroups,
        'threshold_tuning': False, 'calibration_mapping_fitted': False,
        'calibration_diagnostic_intervals': 'not estimated',
        'clinical_validation': False, 'test_feedback_retuning_allowed': False}
    (output / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result
