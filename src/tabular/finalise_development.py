"""One authorized six-fit preparation; never evaluate or load Test payloads."""
import hashlib
import json
from pathlib import Path
import platform
import warnings

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import StratifiedKFold

from . import baseline_nhanes as baseline
from .calibration_threshold_nhanes import operating_metrics, select_threshold
from .logistic_comparison_nhanes import (
    BASELINE_CONFIGURATION, fit_configuration, historical_metrics,
    make_comparison_pipeline, metric_text, verify_reproduction,
)
from .preprocess_nhanes import FEATURES
from .xgboost_comparison_nhanes import FIXED_SETTINGS, PROFILES, fold_fingerprint, xgboost

ROOT = baseline.ROOT
SCOPE = 'prepare_tabular_final_freeze_v1_six_logistic_fits_no_test'
MANIFEST_SHA = '4d0f82149cb20485186ad929fca0a070a72fe4e4a3032b1cf8da37954c131551'
FOLD_SHA = '0822ca63d5ffa57375141ae15d97ca08333a207463eae909237892dbe9e3adb0'
REVIEW = ROOT / 'docs/tabular_finalisation_decision_evidence_v1.json'
MODEL = ROOT / 'models/questionnaire_pp1_v1/model.joblib'
OOF = ROOT / 'data/tabular_pp1_v1/development_oof.npz'
MANIFEST = ROOT / 'data/preprocessing/split_manifest.json'
PROTOCOL = {
    'version': 'tabular-final-preparation-v1', 'positive_label': 1,
    'outcome': 'self_reported_previous_gum_treatment', 'seed': 42,
    'source_label_mapping': {'OHQ850=1': 1, 'OHQ850=2': 0}, 'feature_order': list(FEATURES),
    'development_n': 6251, 'development_yes': 1553, 'held_out_n': 1563,
    'logistic_fits': 6, 'xgboost_fits': 0, 'calibration': 'none_raw',
    'threshold_grid': '0.00..1.00 step0.01',
    'threshold_selection': 'max_Youden_J_then_higher_sensitivity_then_larger_threshold',
    'positive_decision': 'probability>=threshold', 'clinical_cutoff': False,
    'evaluation_metrics': ['AUROC', 'trapezoidal_PR_AUC', 'AP', 'Brier',
        'calibration_slope_intercept', 'reliability', 'sensitivity_specificity_confusion'],
    'future_test_bootstrap': {'draws': 1000, 'seed': 42, 'paired_participant_resamples': True,
                              'complex_survey_uncertainty': False},
    'test_access_authorized': False, 'demo_activation_authorized': False}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bindings(output):
    return {'review_sha256': digest(REVIEW), 'code_sha256': digest(__file__),
            'protocol_sha256': hashlib.sha256(json.dumps(PROTOCOL, sort_keys=True).encode()).hexdigest(),
            'output_path_sha256': hashlib.sha256(str(Path(output).resolve()).encode()).hexdigest()}


def authorize(record, output, *, opt_in=False):
    # New scope is preparation only. It never grants the final Test operation.
    if not opt_in or not isinstance(record, dict):
        raise ValueError('Explicit preparation opt-in required')
    if (record.get('scope') != SCOPE or record.get('status') != 'owner_confirmed'
            or not all(record.get(k) for k in ['authorizer', 'date', 'evidence_reference'])
            or record.get('test_access_authorized') is not False):
        raise ValueError('Preparation scope/provenance/no-Test boundary required')
    if any(record.get(k) != value for k, value in bindings(output).items()):
        raise ValueError('Preparation authorization binding mismatch')


def verify_inputs():
    """Hash history and artifacts before selective participant loading/deserialization."""
    review = json.loads(REVIEW.read_text())
    for name, expected in review['source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise ValueError('Historical source/evidence changed: ' + name)
    for name, path in [('model', MODEL), ('saved_oof', OOF), ('manifest', MANIFEST)]:
        if path.is_symlink() or digest(path) != review['artifact_hash_checks'][name]['sha256']:
            raise ValueError('Trusted artifact hash mismatch: ' + name)
    return review


def checked_reference(path, expected_sha, ids, labels):
    if Path(path).is_symlink() or digest(path) != expected_sha:
        raise ValueError('Reference OOF hash mismatch')
    with np.load(path, allow_pickle=False) as saved:
        if not np.array_equal(saved['SEQN'], ids) or not np.array_equal(saved['y'], labels):
            raise ValueError('Reference OOF participant/label mismatch')
        probability = saved['A_reference']
    baseline.score_predictions(labels, probability)
    return probability


def prepare_logistic(x, y, folds, reference):
    """Gate the sixth fit on reproduction of all ten historical OOF measures."""
    scores, probability, width = fit_configuration(x, y, folds, BASELINE_CONFIGURATION)
    reproduction = verify_reproduction(scores, reference)
    model = make_comparison_pipeline(BASELINE_CONFIGURATION)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        model.fit(x, y)
    if model.classes_.tolist() != [0, 1] or len(model['preprocess'].get_feature_names_out()) != width:
        raise ValueError('Final Logistic class/feature mapping mismatch')
    return model, probability, scores, reproduction, width


def thresholds_and_metrics(y, probabilities):
    results = {}
    for name, probability in probabilities.items():
        decision = select_threshold(y, probability)
        if not decision['useful']:
            raise ValueError('No useful development J; no automatic fallback: ' + name)
        results[name] = {'decision': decision,
            'oof_reference_050': baseline.score_predictions(y, probability),
            'apparent_oof_at_selected_threshold': operating_metrics(y, probability >= decision['threshold']),
            'optimism_warning': 'Same OOF labels selected this threshold; operating performance is apparent, not independent validation.',
            'clinical_cutoff': False}
    return results


def run(output, authorization, *, opt_in=False):
    output = Path(output).resolve()
    authorize(authorization, output, opt_in=opt_in)
    if output.exists() or not output.is_relative_to((ROOT / 'data').resolve()):
        raise ValueError('Fresh ignored local data output required')
    import subprocess
    subprocess.run(['git', 'check-ignore', '--quiet', str(output)], cwd=ROOT, check=True)
    review = verify_inputs()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'protocol.json').write_text(json.dumps({'protocol': PROTOCOL,
        'bindings': bindings(output), 'owner_authorization': authorization}, indent=2) + '\n')
    # Reuse the audited loader: scan linkage bytes, decode development payloads only.
    x, y, manifest_sha = baseline.load_development()
    if (manifest_sha != MANIFEST_SHA or len(y) != 6251 or int(y.sum()) != 1553
            or tuple(x.columns) != FEATURES or not x.index.equals(y.index)):
        raise ValueError('Frozen development cohort/feature schema mismatch')
    folds = tuple(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    if fold_fingerprint(x, folds) != FOLD_SHA:
        raise ValueError('Original fold membership changed')
    xgb_probability = checked_reference(OOF, review['artifact_hash_checks']['saved_oof']['sha256'], x.index, y)
    previous = json.loads((ROOT / 'docs/tabular_pp1_completion_results_v1.json').read_text())
    verify_reproduction(baseline.score_predictions(y, xgb_probability),
                        {k: metric_text(v) for k, v in previous['scores']['A_reference'].items()})
    reference = historical_metrics((ROOT / 'docs/tabular_baseline.md').read_text())
    model, logistic_probability, scores, reproduction, width = prepare_logistic(x, y, folds, reference)
    decisions = thresholds_and_metrics(y, {'XGBoost_A_raw': xgb_probability,
                                           'Logistic_C1_raw': logistic_probability})
    model_path = output / 'logistic_model.joblib'
    joblib.dump(model, model_path)
    reloaded = joblib.load(model_path)  # Only our own newly created local artifact.
    if not np.array_equal(reloaded.predict_proba(x.iloc[:3]), model.predict_proba(x.iloc[:3])):
        raise ValueError('Saved Logistic reload predictions changed')
    fold_ids = np.full(len(y), -1)
    prior = np.full(len(y), np.nan)
    for number, (fitting, scoring) in enumerate(folds):
        fold_ids[scoring] = number
        prior[scoring] = y.iloc[fitting].mean()
    np.savez(output / 'development_oof.npz', SEQN=x.index.to_numpy(), y=y.to_numpy(),
             folds=fold_ids, XGBoost_A_raw=xgb_probability, Logistic_C1_raw=logistic_probability, prior=prior)
    frozen_prior = {'strategy': 'constant_training_rate', 'probability': float(y.mean()),
                    'development_n': len(y), 'yes_n': int(y.sum()), 'calibration': 'none'}
    (output / 'training_rate.json').write_text(json.dumps(frozen_prior, indent=2) + '\n')
    verify_inputs()  # Fail if original data-membership/evidence changed during preparation.
    receipt = {'status': 'PREPARED_PENDING_OWNER_NUMERICAL_FREEZE_REVIEW', 'protocol': PROTOCOL,
        'bindings': bindings(output), 'manifest_sha256': manifest_sha, 'fold_sha256': FOLD_SHA,
        'encoded_features': width, 'logistic_reproduction': reproduction,
        'decisions': decisions, 'baseline': frozen_prior,
        'baseline_oof_reference_050': baseline.score_predictions(y, prior),
        'primary_artifact': {'path': str(MODEL.relative_to(ROOT)), 'sha256': digest(MODEL),
                             'type': 'QuestionnairePrototype', 'predictor_attribute': 'model'},
        'output_files_sha256': {p.name: digest(p) for p in output.iterdir() if p.is_file()},
        'new_logistic_fits': 6, 'new_xgboost_fits': 0, 'test_evaluated': False,
        'candidate_configurations': {'XGBoost_A_raw': {**FIXED_SETTINGS, **PROFILES['A']},
            'Logistic_C1_raw': {k: model['classifier'].get_params()[k]
                for k in ['C', 'class_weight', 'solver', 'max_iter', 'random_state']}},
        'runtime': {'python': platform.python_version(), 'numpy': np.__version__,
            'pandas': baseline.pd.__version__, 'sklearn': baseline.sklearn.__version__,
            'xgboost': xgboost.__version__, 'joblib': joblib.__version__},
        'demo_changed': False, 'calibration': 'none_raw', 'clinical_validation': False}
    (output / 'freeze_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    return receipt
