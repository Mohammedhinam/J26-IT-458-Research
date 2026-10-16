"""One opt-in Training-only encoder comparison; no implicit download or tuning."""
import io
import json
from pathlib import Path

import numpy as np

from . import frozen_feature_probe as base

VERSION = 'training680-frozen-efficientnet-b0-probe-v1'
SCOPE = 'run_training680_efficientnet_probe_v1'
WEIGHTS_URL = 'https://download.pytorch.org/models/efficientnet_b0_rwightman-7f5810bc.pth'
WEIGHTS_PREFIX = '7f5810bc'
REFERENCE_RESULTS_SHA = '7c3f788ecb629d34da2f31b1e8fd29091745fa10c33cff4d9f59ef227fd9edf4'
REFERENCE_OOF_SHA = '18318980b1cfa216d535633ff57067d4456b39b150335a8abfdf2dc16c8174ea'
FOLD_SHA = 'e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4'
CONFIG = {**base.CONFIG, 'version': VERSION,
          'encoder': 'EfficientNet_B0_Weights.IMAGENET1K_V1', 'dimensions': 1280}


def code_hashes():
    return {**base.code_hashes(), 'efficientnet_feature_probe.py': base.legacy.sha256(__file__)}


def extract_features(model, arrays, batch_size=16):
    """Same B1 input contract, with the B0 average-pool feature dimension."""
    import torch
    if not 1 <= batch_size <= 32:
        raise ValueError('Bounded batch size required')
    if any(p.requires_grad for p in model.parameters()) or any(m.training for m in model.modules()):
        raise ValueError('Frozen eval encoder required')
    initial = {name: value.detach().clone() for name, value in model.state_dict().items()}
    output, batch = [], []

    def forward():
        with torch.no_grad():
            features = model(torch.from_numpy(np.stack(batch))).cpu().numpy()
        if features.shape != (len(batch), 1280) or features.dtype != np.float32 or not np.isfinite(features).all():
            raise ValueError('Expected finite float32 1280-dimensional features')
        output.append(features)
        batch.clear()

    for array in arrays:
        if array.shape != (224, 224, 3):
            raise ValueError('Expected B1 model-view geometry')
        batch.append(base.b1.normalize(base.b1._array(array)))
        if len(batch) == batch_size:
            forward()
    if batch:
        forward()
    if not output:
        raise ValueError('No features extracted')
    if any(not torch.equal(value, initial[name]) for name, value in model.state_dict().items()):
        raise ValueError('Frozen encoder/BatchNorm changed')
    return np.concatenate(output)


def load_cache(path, expected_sha, ids, labels, groups, folds):
    """Numeric-only cache bound to the exact source membership and dimensions."""
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 64 * 1024**2:
        raise ValueError('Unsafe feature cache')
    raw = path.read_bytes()
    if base.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Feature cache SHA mismatch')
    with np.load(io.BytesIO(raw), allow_pickle=False) as cache:
        if set(cache.files) != {'features', 'ids', 'labels', 'groups', 'folds'}:
            raise ValueError('Unexpected cache fields')
        for key, value in [('ids', ids), ('labels', labels), ('groups', groups), ('folds', folds)]:
            if not np.array_equal(cache[key], value):
                raise ValueError('Feature cache membership mismatch')
        features = cache['features']
        if features.shape != (len(ids), 1280) or features.dtype != np.float32 or not np.isfinite(features).all():
            raise ValueError('Invalid cached features')
    return features


def read_reference(root, ids, labels, folds):
    """Only cached Training OOF predictions; never re-extract the old encoder."""
    result_path = base.legacy.safe_file(root, 'results.json')
    oof_path = base.legacy.safe_file(root, 'oof.npz')
    if base.legacy.sha256(result_path) != REFERENCE_RESULTS_SHA or base.legacy.sha256(oof_path) != REFERENCE_OOF_SHA:
        raise ValueError('Reference evidence SHA mismatch')
    reference = base.bundle.load_json(result_path)
    if reference['config'] != base.CONFIG or reference['bindings']['code_sha256'] != base.b1.digest_json(base.code_hashes()):
        raise ValueError('Reference config/code changed')
    with np.load(oof_path, allow_pickle=False) as saved:
        if set(saved.files) != {'ids', 'labels', 'folds', 'linear', 'majority', 'prior'}:
            raise ValueError('Reference OOF fields mismatch')
        for key, value in [('ids', ids), ('labels', labels), ('folds', folds)]:
            if not np.array_equal(saved[key], value):
                raise ValueError('Reference membership/folds mismatch')
        probabilities = {name: saved[name] for name in ['linear', 'majority', 'prior']}
    return reference, probabilities


def paired_comparison(labels, groups, probabilities, repetitions=1000):
    """Paired fixed-OOF intervals; not participant-independent/refitting intervals."""
    labels, groups = np.asarray(labels), np.asarray(groups)
    unique = np.unique(groups)
    members = {group: np.flatnonzero(groups == group) for group in unique}
    rng = np.random.default_rng(42)
    keys = ['macro_f1_four_grades', 'balanced_accuracy', 'quadratic_weighted_kappa']
    differences = {name: {key: [] for key in keys} for name in ['resnet', 'majority', 'prior']}
    undefined = 0
    for _ in range(repetitions):
        index = np.concatenate([members[g] for g in rng.choice(unique, len(unique), replace=True)])
        if set(labels[index]) != {1, 2, 3, 4}:
            undefined += 1
            continue
        scored = {name: base.measure(labels[index], values[index]) for name, values in probabilities.items()}
        for name in differences:
            for key in keys:
                differences[name][key].append(scored['efficientnet'][key] - scored[name][key])
    return {'repetitions': repetitions, 'undefined_draws': undefined, 'conditional_only': True,
            'participant_independence_verified': False,
            'efficientnet_minus_reference_95': {
                name: {key: np.quantile(values, [.025, .975]).tolist() if values else None
                       for key, values in metrics.items()} for name, metrics in differences.items()}}


def run_authorized(root, weights, weights_sha, reference_root, output, authorization, *, opt_in=False):
    """One new explicit scope, exact old folds and fresh ignored output required."""
    if not opt_in:
        raise ValueError('Fresh owner opt-in required before data access')
    root, weights, output = Path(root), Path(weights), Path(output)
    raw = base.legacy.safe_file(root, 'bundle_manifest.json').read_bytes()
    if base.sha256(raw).hexdigest() != base.MANIFEST_SHA:
        raise ValueError('Pinned manifest SHA mismatch')
    rows = base.training_rows(json.loads(raw))
    ids = [row['source_record_id'] for row in rows]
    labels = np.array([row['provisional_mgi_grade'] for row in rows])
    groups = [row['content_group_id'] for row in rows]
    folds = base.make_folds(ids, labels, groups)
    if base.b1.digest_json(folds.tolist()) != FOLD_SHA:
        raise ValueError('Frozen fold SHA mismatch')
    if not base.b1._sha(weights_sha) or not weights_sha.startswith(WEIGHTS_PREFIX):
        raise ValueError('Official weight provenance/hash required')
    bindings = {'manifest_sha256': base.MANIFEST_SHA, 'weights_sha256': weights_sha,
                'config_sha256': base.b1.digest_json(CONFIG), 'code_sha256': base.b1.digest_json(code_hashes()),
                'selection_sha256': base.b1.digest_json(rows), 'fold_sha256': FOLD_SHA,
                'reference_results_sha256': REFERENCE_RESULTS_SHA, 'reference_oof_sha256': REFERENCE_OOF_SHA,
                'output_path_sha256': base.sha256(str(output.resolve()).encode()).hexdigest()}
    base.legacy.authorise(authorization, SCOPE, bindings, opt_in=True)
    if weights.is_symlink() or not weights.is_file() or base.legacy.sha256(weights) != weights_sha:
        raise ValueError('Trusted cached official weights required; no download')
    _, reference = read_reference(reference_root, ids, labels, folds)
    base.legacy.new_ignored_output(output, 'data')
    if output.exists() or output.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(output.resolve()):
        raise ValueError('Fresh output separate from inputs required')
    reference_path = Path(reference_root).resolve()
    if output.resolve().is_relative_to(reference_path) or reference_path.is_relative_to(output.resolve()):
        raise ValueError('Output must be separate from reference evidence')
    output.mkdir(parents=True, exist_ok=False)
    import torch
    from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
    if EfficientNet_B0_Weights.IMAGENET1K_V1.url != WEIGHTS_URL:
        raise ValueError('Official source URL changed')
    torch.manual_seed(42)
    torch.set_num_threads(2)
    model = efficientnet_b0(weights=None)
    raw_weights = weights.read_bytes()
    if base.sha256(raw_weights).hexdigest() != weights_sha:
        raise ValueError('Weights changed before load')
    model.load_state_dict(torch.load(io.BytesIO(raw_weights), map_location='cpu', weights_only=True), strict=True)
    del raw_weights
    model.classifier = torch.nn.Identity()
    model.requires_grad_(False)
    model.eval()
    (output / 'protocol.json').write_text(json.dumps({'config': CONFIG, 'bindings': bindings, 'ids': ids, 'folds': folds.tolist()}, indent=2))
    arrays = (base.bundle.model_array(base.legacy.safe_file(root, row['model_path']), row['model_sha256']) for row in rows)
    features = extract_features(model, arrays)
    cache = output / 'features.npz'
    np.savez(cache, features=features, ids=np.array(ids), labels=labels, groups=np.array(groups), folds=folds)
    features = load_cache(cache, base.legacy.sha256(cache), ids, labels, groups, folds)
    scored = base.probe(features, ids, labels, groups)
    if not np.array_equal(scored['folds'], folds):
        raise ValueError('Fold drift')
    for name in ['majority', 'prior']:
        if not np.array_equal(scored['probabilities'][name], reference[name]):
            raise ValueError('Baseline drift')
    np.savez(output / 'oof.npz', ids=np.array(ids), labels=labels, folds=folds, **scored['probabilities'])
    predictions = {'efficientnet': scored['probabilities']['linear'], 'resnet': reference['linear'],
                   'majority': reference['majority'], 'prior': reference['prior']}
    summary = {'notice': base.legacy.NOTICE, 'config': CONFIG, 'bindings': bindings,
               'metrics': {name: base.measure(labels, values) for name, values in predictions.items()},
               'uncertainty': paired_comparison(labels, groups, predictions),
               'feature_cache_sha256': base.legacy.sha256(cache), 'oof_sha256': base.legacy.sha256(output / 'oof.npz'),
               'test_used': False, 'validation53_used': False, 'real_run': True, 'fits': 15}
    (output / 'results.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    return summary
