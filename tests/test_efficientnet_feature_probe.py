"""Generated-only encoder, cache and comparison regressions. No downloads."""
import json

import numpy as np
import pytest
import torch
from torchvision.models import efficientnet_b0

from src.vision import efficientnet_feature_probe as probe


def synthetic():
    labels = np.repeat(np.arange(1, 5), 20)
    ids = [f'generated/{i:03}' for i in range(len(labels))]
    groups = [f'g{i // 2:03}' for i in range(len(labels))]
    x = np.eye(4)[labels - 1] * 3 + np.random.default_rng(42).normal(0, .1, (len(labels), 4))
    return x, ids, labels, groups


def test_same_recipe_and_identical_folds():
    expected = {**probe.base.CONFIG, 'version': probe.VERSION,
                'encoder': 'EfficientNet_B0_Weights.IMAGENET1K_V1', 'dimensions': 1280}
    assert probe.CONFIG == expected
    x, ids, y, groups = synthetic()
    reference = probe.base.probe(x, ids, y, groups)
    candidate = probe.base.probe(np.pad(x, ((0, 0), (0, 1276))), ids, y, groups)
    np.testing.assert_array_equal(reference['folds'], candidate['folds'])
    for name in ['majority', 'prior']:
        np.testing.assert_array_equal(reference['probabilities'][name], candidate['probabilities'][name])
    for fold, evidence in enumerate(candidate['fold_checks']):
        np.testing.assert_allclose(evidence['scaler_mean'][:4], x[candidate['folds'] != fold].mean(0))


def test_real_b0_generated_forward_frozen_bn_and_unclipped_normalization():
    torch.manual_seed(42)
    torch.set_num_threads(2)
    model = efficientnet_b0(weights=None)
    model.classifier = torch.nn.Identity()
    model.requires_grad_(False)
    model.eval()
    array = np.zeros((224, 224, 3), dtype='<f4')
    array[:112, :, 0] = 1.1
    array[112:, :, 2] = -.1
    inputs = []
    hook = model.register_forward_pre_hook(lambda _, args: inputs.append(args[0].detach().numpy().copy()))
    try:
        a = probe.extract_features(model, [array], 1)
        b = probe.extract_features(model, [array], 1)
    finally:
        hook.remove()
    np.testing.assert_array_equal(a, b)
    assert a.shape == (1, 1280) and a.dtype == np.float32
    np.testing.assert_array_equal(inputs[0][0], probe.base.b1.normalize(array))
    assert array.min() < 0 and array.max() > 1


@pytest.mark.parametrize('fault', ['training', 'gradient', 'batch', 'shape', 'nan', 'empty'])
def test_encoder_rejects_unsafe_inputs(fault):
    class Small(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = torch.nn.Parameter(torch.ones(1))

        def forward(self, values):
            return torch.zeros(len(values), 1280)

    model = Small().eval().requires_grad_(False)
    array = np.zeros((224, 224, 3), np.float32)
    batch_size = 1
    if fault == 'training': model.train()
    if fault == 'gradient': model.requires_grad_(True)
    if fault == 'batch': batch_size = 33
    if fault == 'shape': array = array[:20]
    if fault == 'nan': array[0, 0, 0] = np.nan
    arrays = [] if fault == 'empty' else [array]
    with pytest.raises(ValueError):
        probe.extract_features(model, arrays, batch_size)


@pytest.mark.parametrize('fault', ['mutation', 'dimension', 'nonfinite'])
def test_encoder_rejects_mutation_or_bad_features(fault):
    class Bad(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.register_buffer('count', torch.zeros(1))

        def forward(self, values):
            if fault == 'mutation': self.count.add_(1)
            output = torch.zeros(len(values), 2048 if fault == 'dimension' else 1280)
            if fault == 'nonfinite': output[0, 0] = float('inf')
            return output

    with pytest.raises(ValueError):
        probe.extract_features(Bad().eval(), [np.zeros((224, 224, 3), np.float32)])


@pytest.mark.parametrize('fault', ['hash', 'ids', 'labels', 'groups', 'folds', 'nan', 'dtype', 'shape', 'extra', 'object'])
def test_cache_integrity_and_membership(tmp_path, fault):
    _, ids, y, groups = synthetic()
    folds = probe.base.make_folds(ids, y, groups)
    values = {'features': np.zeros((len(ids), 1280), np.float32), 'ids': np.array(ids),
              'labels': y, 'groups': np.array(groups), 'folds': folds}
    path = tmp_path / 'features.npz'
    np.savez(path, **values)
    digest = probe.base.legacy.sha256(path)
    assert probe.load_cache(path, digest, ids, y, groups, folds).shape == (80, 1280)
    if fault == 'ids': values['ids'][0] = 'changed'
    if fault == 'labels': values['labels'] = y + 1
    if fault == 'groups': values['groups'][0] = 'unknown'
    if fault == 'folds': values['folds'] = (folds + 1) % 5
    if fault == 'nan': values['features'][0, 0] = np.nan
    if fault == 'dtype': values['features'] = values['features'].astype(np.float64)
    if fault == 'shape': values['features'] = values['features'][:1]
    if fault == 'extra': values['other'] = np.zeros(1)
    if fault == 'object': values['features'] = np.array([object()], dtype=object)
    np.savez(path, **values)
    digest = '0' * 64 if fault == 'hash' else probe.base.legacy.sha256(path)
    with pytest.raises(ValueError): probe.load_cache(path, digest, ids, y, groups, folds)


def test_reference_rejects_untrusted_hash_before_npz_loading(tmp_path):
    (tmp_path / 'results.json').write_text('{}')
    (tmp_path / 'oof.npz').write_bytes(b'not trusted')
    with pytest.raises(ValueError, match='SHA'):
        probe.read_reference(tmp_path, [], [], [])


@pytest.mark.parametrize('fault', ['none', 'membership', 'config', 'extra'])
def test_generated_reference_hash_and_alignment(tmp_path, monkeypatch, fault):
    x, ids, y, groups = synthetic()
    scored = probe.base.probe(x, ids, y, groups)
    result = {'config': dict(probe.base.CONFIG), 'bindings': {'code_sha256': probe.base.b1.digest_json(probe.base.code_hashes())}}
    values = {'ids': np.array(ids), 'labels': y, 'folds': scored['folds'], **scored['probabilities']}
    if fault == 'membership': values['ids'][0] = 'changed'
    if fault == 'config': result['config']['C'] = 10
    if fault == 'extra': values['other'] = np.zeros(1)
    (tmp_path / 'results.json').write_text(json.dumps(result))
    np.savez(tmp_path / 'oof.npz', **values)
    monkeypatch.setattr(probe, 'REFERENCE_RESULTS_SHA', probe.base.legacy.sha256(tmp_path / 'results.json'))
    monkeypatch.setattr(probe, 'REFERENCE_OOF_SHA', probe.base.legacy.sha256(tmp_path / 'oof.npz'))
    if fault == 'none':
        _, loaded = probe.read_reference(tmp_path, ids, y, scored['folds'])
        np.testing.assert_array_equal(loaded['linear'], scored['probabilities']['linear'])
    else:
        with pytest.raises(ValueError): probe.read_reference(tmp_path, ids, y, scored['folds'])


def test_paired_comparison_determinism_and_zero_reference_difference():
    x, ids, y, groups = synthetic()
    scored = probe.base.probe(x, ids, y, groups)
    probabilities = {'efficientnet': scored['probabilities']['linear'], 'resnet': scored['probabilities']['linear'],
                     'majority': scored['probabilities']['majority'], 'prior': scored['probabilities']['prior']}
    a = probe.paired_comparison(y, groups, probabilities, repetitions=20)
    assert a == probe.paired_comparison(y, groups, probabilities, repetitions=20)
    assert a['conditional_only'] and a['undefined_draws'] == 0
    assert all(value == [0., 0.] for value in a['efficientnet_minus_reference_95']['resnet'].values())


def test_no_real_file_access_without_new_opt_in(monkeypatch):
    monkeypatch.setattr(probe.base.legacy, 'safe_file', lambda *_: pytest.fail('File access before opt-in'))
    with pytest.raises(ValueError, match='opt-in'):
        probe.run_authorized('/Test', '/weights', '0' * 64, '/reference', '/out', {})


def test_bad_manifest_rejected_before_array_access(tmp_path, monkeypatch):
    (tmp_path / 'bundle_manifest.json').write_text('{}')
    monkeypatch.setattr(probe.base.bundle, 'model_array', lambda *_: pytest.fail('Array accessed'))
    with pytest.raises(ValueError, match='manifest SHA'):
        probe.run_authorized(tmp_path, '/weights', '0' * 64, '/reference', '/out', {}, opt_in=True)


def test_old_execution_scope_rejected():
    with pytest.raises(ValueError, match='scope'):
        probe.base.legacy.authorise({'status': 'owner_confirmed', 'scope': probe.base.SCOPE}, probe.SCOPE, {}, opt_in=True)
