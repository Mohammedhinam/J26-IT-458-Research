"""Generated inputs only; no real checkpoint, dataset or pretrained download."""
from dataclasses import asdict, replace
import json

import numpy as np
import pytest

from src.vision import exploratory_pilot_b1_lastblock_v3 as stage
from src.vision import exploratory_pilot_b1_balanced_v2 as weighted
from src.vision import exploratory_pilot_b1_v1 as base
from src.vision import verify_b1_lastblock_runtime_v3 as verification
from src.vision import train_pipeline as trainer


def test_exact_approved_protocol_and_historical_schema():
    config = stage.configuration()
    assert config.freeze_backbone is False and config.unfreeze_prefixes == ('layer4.2',)
    assert config.batchnorm == 'frozen' and config.class_weight == 'balanced'
    assert (config.seed, config.batch_size, config.epochs, config.patience) == (42, 16, 5, 2)
    assert stage.protocol()['optimizer_groups'] == {'head': .001, 'last_bottleneck': .00001}
    assert stage.protocol()['research_schema_unchanged'] == [0, 1, 2, 3, 4]
    assert stage.protocol()['grades'] == [1, 2, 3, 4]
    assert weighted.configuration().freeze_backbone is True
    assert len(stage.HEAD_NAMES + stage.BLOCK_NAMES) == 5


def generated_prior_metadata():
    config = asdict(weighted.configuration())
    context = {'protocol': weighted.protocol(), 'manifest_sha256': weighted.MANIFEST_SHA,
               'weights': {'sha256': weighted.WEIGHTS_SHA}, 'source_hashes': weighted.code_hashes()}
    return {'version': weighted.VERSION, 'schema': [1, 2, 3, 4], 'epoch': 1,
            'context': context, 'config': config,
            'identity': trainer.digest({'context': context, 'config': config})}


def test_generated_prior_metadata_accepts_exact_bindings():
    stage.validate_initial_metadata(generated_prior_metadata())


@pytest.mark.parametrize('field', ['version', 'schema', 'epoch', 'config', 'context', 'identity'])
def test_prior_metadata_rejects_stale_or_wrong_provenance(field):
    state = generated_prior_metadata()
    state[field] = {} if field in ('config', 'context') else 'stale'
    with pytest.raises(ValueError):
        stage.validate_initial_metadata(state)


@pytest.mark.parametrize('name', ['conv1.weight', 'bn1.weight', 'layer4.2.bn3.running_mean'])
def test_frozen_proof_rejects_earlier_layers_and_bn_changes(name):
    before = {n: 'a' for n in (*stage.HEAD_NAMES, *stage.BLOCK_NAMES, name)}
    after = {**before, name: 'b'}
    with pytest.raises(ValueError, match='Frozen'):
        stage.check_frozen(before, after)


def test_frozen_proof_accepts_only_approved_changes_and_rejects_missing_coverage():
    before = {n: 'a' for n in (*stage.HEAD_NAMES, *stage.BLOCK_NAMES, 'bn1.weight')}
    after = {**before, stage.BLOCK_NAMES[0]: 'b'}
    assert stage.check_frozen(before, after)['frozen_tensors_compared'] == 1
    after.pop('bn1.weight')
    with pytest.raises(ValueError, match='coverage'):
        stage.check_frozen(before, after)


def auth_example():
    return {'status': 'owner_confirmed', 'scope': stage.SCOPE, 'authorizer': 'generated-test-owner',
            'date': 'synthetic', 'evidence_reference': 'generated test, not human approval',
            'acknowledgements': {n: True for n in base.legacy.ACKS},
            'cloud_upload_authorized': True, 'training_authorized': True,
            'bundle_manifest_sha256': weighted.MANIFEST_SHA,
            'protocol_sha256': trainer.digest(stage.protocol()),
            'code_sha256': trainer.digest(stage.code_hashes()), 'initial_checkpoint_sha256': stage.INITIAL_SHA,
            'weights_sha256': weighted.WEIGHTS_SHA, 'verification_sha256': 'a'*64,
            'output_run_id': 'generated_run'}


def test_authorization_accepts_exact_generated_bindings():
    stage.validate_execution(auth_example(), 'generated_run', 'a'*64)


@pytest.mark.parametrize('field', ['scope', 'bundle_manifest_sha256', 'protocol_sha256', 'code_sha256',
                                 'initial_checkpoint_sha256', 'weights_sha256', 'verification_sha256',
                                 'output_run_id', 'cloud_upload_authorized', 'training_authorized'])
def test_authorization_rejects_stale_bindings(field):
    record = auth_example()
    record[field] = 'stale'
    with pytest.raises(ValueError):
        stage.validate_execution(record, 'generated_run', 'a'*64)


def test_no_opt_in_before_any_data_or_backend_access():
    with pytest.raises(ValueError, match='opt-in'):
        stage.run_pilot('/nonexistent', '/nonexistent', {}, '/nonexistent', '/nonexistent')


@pytest.mark.parametrize('split,identifier', [('Test', 'Test/00999'), ('Validation', 'Validation/00736'),
                                            ('Training', 'Training/00591')])
def test_existing_dataset_guards_preserved(split, identifier):
    row = {'original_split': split, 'source_record_id': identifier, 'label_status': 'provisional',
           'qualified_label_approved': False, 'provisional_mgi_grade': 2}
    with pytest.raises(ValueError):
        base.Dataset('/nonexistent', [row], split)


def test_synthetic_gate_requires_actual_cases_no_skips_and_unchanged_payloads(tmp_path, monkeypatch):
    project = tmp_path/'project'
    project.mkdir()
    (project/'synthetic.py').write_text('# generated fixture\n')
    monkeypatch.setattr(verification, '__file__', str(project/'src/vision/runtime.py'))
    files = {'synthetic.py': base.legacy.sha256(project/'synthetic.py')}
    ids = ['generated::'+name for name in verification.BACKENDS]
    (project/'verification_manifest.json').write_text(json.dumps({'files': files, 'expected_case_ids': ids}))
    evidence = tmp_path/'evidence'
    evidence.mkdir()
    xml = '<testsuites><testsuite>'+''.join('<testcase classname="generated" name="'+n+'"/>' for n in verification.BACKENDS)+'</testsuite></testsuites>'
    def write_receipt(xml):
        (evidence/'junit.xml').write_text(xml)
        _, counts, _ = verification.case_results(evidence/'junit.xml')
        for name, value in [('summary.json', {'status': 'PASS', 'pytest_exit_code': 0, 'counts': counts}),
                            ('source_hashes_before.json', files), ('source_hashes_after.json', files)]:
            (evidence/name).write_text(json.dumps(value))
        (evidence/'pytest.log').write_text('Generated gate fixture only')
        payloads = {p.name: base.legacy.sha256(p) for p in evidence.iterdir() if p.name != 'evidence_manifest.json'}
        (evidence/'evidence_manifest.json').write_text(json.dumps({'files': payloads}))
    write_receipt(xml)
    assert len(verification.require_pass(evidence)) == 64
    write_receipt(xml.replace('/>', '><skipped/></testcase>', 1))
    with pytest.raises(ValueError): verification.require_pass(evidence)
    write_receipt(xml)
    (project/'synthetic.py').write_text('# changed\n')
    with pytest.raises(ValueError): verification.require_pass(evidence)


def backend():
    torch = pytest.importorskip('torch', reason='Colab backend required; no local install')
    pytest.importorskip('torchvision')
    torch.set_num_threads(1)
    return torch


def tiny(torch):
    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            for i in (1, 2, 3):
                setattr(self, 'conv'+str(i), torch.nn.Conv2d(4, 4, 1, bias=False))
                setattr(self, 'bn'+str(i), torch.nn.BatchNorm2d(4))
        def forward(self, values):
            for i in (1, 2, 3):
                values = getattr(self, 'bn'+str(i))(getattr(self, 'conv'+str(i))(values))
                values = torch.relu(values)
            return values
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.features = torch.nn.Sequential(torch.nn.Conv2d(3,4,1), torch.nn.BatchNorm2d(4))
            self.layer4 = torch.nn.Sequential(torch.nn.Identity(), torch.nn.Identity(), Block())
            self.fc = torch.nn.Linear(4,4)
        def forward(self, values):
            return self.fc(self.layer4(self.features(values)).mean((2,3)))
    return Tiny()


def generated_data(torch, split):
    class Data:
        records = [{'source_record_id': split+'/'+str(100+i).zfill(5), 'original_split': split,
                    'provisional_mgi_grade': i%4+1} for i in range(8)]
        def __len__(self): return 8
        def __getitem__(self, i): return torch.full((3,8,8), (i+1)/8), i%4
    return Data()


def test_initial_checkpoint_restore_hash_and_provenance(tmp_path):
    torch = backend()
    trainer.seed_everything(42)
    network = base.make_model(pretrained=False)
    state = generated_prior_metadata()
    state['model'] = network['model'].state_dict()
    path = tmp_path/'generated_prior.pt'
    torch.save(state, path)
    digest = base.legacy.sha256(path)
    loaded = stage.read_initial_checkpoint(path, digest)
    restored = base.make_model(pretrained=False)['model']
    restored.load_state_dict(loaded['model'], strict=True)
    assert stage.tensor_hashes(restored) == stage.tensor_hashes(network['model'])
    with pytest.raises(ValueError): stage.read_initial_checkpoint(path, '0'*64)
    state['epoch'] = 3
    torch.save(state, path)
    with pytest.raises(ValueError): stage.read_initial_checkpoint(path, base.legacy.sha256(path))
    state['epoch'] = 1
    state['model']['fc.weight'][0,0] = float('nan')
    torch.save(state, path)
    with pytest.raises(ValueError, match='Finite'): stage.read_initial_checkpoint(path, base.legacy.sha256(path))


def test_resnet_selected_step_freezes_every_other_tensor():
    torch = backend()
    trainer.seed_everything(42)
    model = base.make_model(pretrained=False)['model']
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    config = stage.configuration(device)
    groups = stage.configure_stage(model, config)
    assert [g['lr'] for g in groups] == [.001, .00001]
    assert {n for n,p in model.named_parameters() if p.requires_grad} == set(stage.HEAD_NAMES+stage.BLOCK_NAMES)
    before = stage.tensor_hashes(model)
    optimizer = torch.optim.Adam(groups)
    values = torch.linspace(-3,3,2*3*32*32,device=device).reshape(2,3,32,32)
    weights = np.array([4.,2.,1.,.5], dtype=np.float32)
    weighted.run_epoch(model, [(values,torch.tensor([0,3]))], config, weights, optimizer)
    proof = stage.check_frozen(before, stage.tensor_hashes(model))
    assert set(proof['changed_trainable_names']) == set(stage.HEAD_NAMES+stage.BLOCK_NAMES)
    assert proof['frozen_tensors_compared'] > 300
    assert all(not p.requires_grad for m in model.modules() if isinstance(m,torch.nn.modules.batchnorm._BatchNorm) for p in m.parameters())
    assert all(not m.training for m in model.modules() if isinstance(m,torch.nn.modules.batchnorm._BatchNorm))
    after_train = stage.tensor_hashes(model)
    weighted.run_epoch(model, [(values,torch.tensor([0,3]))], config, weights)
    assert stage.tensor_hashes(model) == after_train


def test_generated_fit_checkpoint_coverage_and_reproducibility(tmp_path):
    torch = backend()
    config = replace(stage.configuration('cpu'), batch_size=4, epochs=2)
    results = []
    for name in ('a','b'):
        trainer.seed_everything(42)
        model = tiny(torch)
        result = stage.fit(model, generated_data(torch,'Training'), generated_data(torch,'Validation'),
                           config, tmp_path/name, {'generated_only': True})
        checkpoint = tmp_path/name/'best.pt'
        state = stage.load_stage_checkpoint(checkpoint,base.legacy.sha256(checkpoint),{'generated_only':True},config)
        assert state['schema'] == [1,2,3,4] and len(state['optimizer']['param_groups']) == 2
        predictions = json.loads((tmp_path/name/'validation_predictions_best.json').read_text())['records']
        assert len(predictions) == 8 and len({r['source_record_id'] for r in predictions}) == 8
        metrics = base.metrics([r['provisional_mgi_grade'] for r in predictions], [r['probabilities_mgi1_to4'] for r in predictions])
        assert metrics == {k:v for k,v in result['best_validation'].items() if k not in ('loss','weighted_ce_diagnostic')}
        assert result['frozen_tensor_checks']['all_frozen_tensors_unchanged'] is True
        with pytest.raises(ValueError): stage.load_stage_checkpoint(checkpoint,'0'*64,{},config)
        results.append(result)
    assert results[0] == results[1]
    with pytest.raises(FileExistsError):
        stage.fit(tiny(torch), generated_data(torch,'Training'), generated_data(torch,'Validation'),config,tmp_path/'a',{})


def test_configuration_and_batchnorm_guards():
    torch = backend()
    for overrides in ({'freeze_backbone':True,'unfreeze_prefixes':()}, {'unfreeze_prefixes':('layer4',)},
                      {'batchnorm':'train_selected'}, {'learning_rate':.0001}, {'class_weight':'none'}, {'weight_decay':.01}):
        with pytest.raises(ValueError): stage.configure_stage(tiny(torch), replace(stage.configuration('cpu'),**overrides))
    model = tiny(torch)
    model.fc = torch.nn.Linear(4,5)
    with pytest.raises(ValueError): stage.configure_stage(model,stage.configuration('cpu'))
    model = tiny(torch)
    groups = stage.configure_stage(model,stage.configuration('cpu'))
    assert len({id(p) for g in groups for p in g['params']}) == 5


def test_selected_block_gradcam_alignment_and_hook_cleanup():
    torch = backend()
    trainer.seed_everything(42)
    network = base.make_model(pretrained=False)
    model, layer = network['model'], network['cam_layer']
    stage.configure_stage(model,stage.configuration('cpu'))
    model.eval()
    before = stage.tensor_hashes(model)
    hooks = (len(layer._forward_hooks),len(layer._backward_hooks))
    prepared = base.b1.B1Input(np.full((16,16,3),100,dtype=np.uint8),
                               np.linspace(-2.,2.,3*224*224,dtype=np.float32).reshape(3,224,224),
                               (0,0,224,224), {'generated_only':True})
    views = base.gradcam(model,layer,prepared)
    assert views['predicted_mgi_grade'] in (1,2,3,4)
    assert len(views['probabilities']) == 4 and sum(views['probabilities']) == pytest.approx(1,abs=1e-6)
    for name in ('original','heatmap','overlay'):
        assert views[name].shape == (16,16,3) and np.isfinite(views[name]).all()
    assert hooks == (len(layer._forward_hooks),len(layer._backward_hooks))
    assert stage.tensor_hashes(model) == before
