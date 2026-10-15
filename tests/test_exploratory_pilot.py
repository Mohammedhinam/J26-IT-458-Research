"""Synthetic pilot contract tests; no dental data, weights or Test inference."""
from copy import deepcopy
from dataclasses import asdict, replace
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from src.vision import exploratory_bundle as eb
from src.vision import exploratory_pilot as ep
from src.vision import train_pipeline as tp


def test_exact_bounded_profile_and_five_class_mapping():
    config=ep.configuration();config.validate()
    assert (config.architecture,config.seed,config.batch_size,config.learning_rate,config.epochs,config.patience)==('resnet50',42,16,0.001,5,2)
    assert config.freeze_backbone and config.batchnorm=='frozen' and config.class_weight=='none'
    assert ep.vp.MGI_GRADES==(0,1,2,3,4)
    for grade in range(5):
        logits=np.zeros(5);logits[grade]=1
        assert ep.vp.map_model_output(logits)['mgi_schema_grade']==grade


def test_majority_uses_training_only_and_lowest_grade_tie():
    a=ep.majority_baseline([1,1,4,4],[4,4])
    b=ep.majority_baseline([1,1,4,4],[1,1])
    assert a['majority_grade']==b['majority_grade']==1
    assert a['notice']==a['validation']['notice']==eb.NOTICE
    assert a['validation']['confusion_matrix'][4][1]==2


def test_missing_zero_and_single_validation_case_are_not_validated():
    result=ep.majority_baseline([1,2,3,4,4],[1,2,3,4])
    metrics=result['validation']
    assert metrics['per_grade_recall'][0] is None
    assert metrics['per_grade_auroc'][0] is None and metrics['macro_auroc_five_schema'] is None
    assert metrics['missing_grades']==[0] and np.asarray(metrics['confusion_matrix']).shape==(5,5)
    warnings=ep.support_warnings([1,2,3,4,4],[1,2,3,4])
    assert warnings['unsupported_training_grades']==warnings['unsupported_validation_grades']==[0]
    assert 1 in warnings['scarce_validation_grades'] and not warnings['five_class_validity_established']


@pytest.mark.parametrize('labels',[[],[True],[1.1],[-1],[5]])
def test_invalid_grade_values_are_never_coerced(labels):
    with pytest.raises(ValueError):ep.majority_baseline(labels,[1,2])


def test_owner_optin_precedes_any_file_or_model_access(tmp_path,monkeypatch):
    monkeypatch.setattr(eb,'safe_file',lambda *a:pytest.fail('data accessed before opt-in'))
    monkeypatch.setattr(ep.vp,'make_model',lambda *a,**k:pytest.fail('model created'))
    with pytest.raises(ValueError,match='opt-in'):ep.run_pilot(tmp_path,None,tmp_path/'out',False)


@pytest.mark.parametrize('change',['scope','hash','ack','name','opt_in'])
def test_auth_scope_hash_acknowledgements_are_required(change):
    authorization={'status':'owner_confirmed','scope':'run_exploratory','authorizer':'synthetic only',
                   'date':'test','evidence_reference':'synthetic fixture','bundle_sha':'good',
                   'acknowledgements':{k:True for k in eb.ACKS}}
    if change=='scope':authorization['scope']='implement_only'
    elif change=='hash':authorization['bundle_sha']='bad'
    elif change=='ack':authorization['acknowledgements'][eb.ACKS[0]]=False
    elif change=='name':authorization['authorizer']=''
    with pytest.raises(ValueError):eb.authorise(authorization,'run_exploratory',{'bundle_sha':'good'},change!='opt_in')


def test_production_training_gate_still_rejects_exploratory_metadata(monkeypatch):
    monkeypatch.setattr(Image,'open',lambda *a:pytest.fail('production opened provisional data'))
    with pytest.raises(ValueError,match='External'):tp.approved_partitions({'status':'provisional_exploratory_only'},None)


def test_no_weight_download_when_cache_missing(tmp_path,monkeypatch):
    monkeypatch.setattr(ep.vp,'make_model',lambda *a,**k:pytest.fail('weight download/model call'))
    result=ep.pretrained_status(tmp_path)
    assert result['status']=='missing_or_invalid' and not result['download_attempted'] and result['sha256'] is None


def test_invalid_named_cached_weight_is_not_accepted(tmp_path):
    (tmp_path/ep.WEIGHTS_NAME).write_bytes(b'not the official checkpoint')
    assert ep.pretrained_status(tmp_path)['status']=='missing_or_invalid'


def test_checkpoint_hash_failure_precedes_deserialisation(tmp_path,monkeypatch):
    checkpoint=tmp_path/'bad.pt';checkpoint.write_bytes(b'changed')
    monkeypatch.setattr(ep.vp,'_torch',lambda:pytest.fail('unsafe checkpoint loaded'))
    with pytest.raises(ValueError,match='byte integrity'):ep.verify_checkpoint(checkpoint,'wrong',{},ep.configuration('cpu'))


def test_provisional_adapter_preserves_metadata_and_reads_only_rgb(tmp_path):
    path=tmp_path/'images/Validation/00001.png';path.parent.mkdir(parents=True)
    Image.new('RGB',(8,4),(40,90,130)).save(path)
    row={'original_split':'Validation','image_path':'images/Validation/00001.png',
         'label_status':'provisional','qualified_label_approved':False,'provisional_mgi_grade':2}
    before=deepcopy(row)
    ds=ep.ProvisionalDevelopmentDataset(tmp_path,[row],'Validation');image,grade=ds[0]
    assert image.shape==(3,224,224) and grade==2 and row==before
    assert ds.records[0]['label_status']=='provisional' and not ds.records[0]['qualified_label_approved']


def test_provisional_adapter_never_accepts_test(tmp_path):
    row={'original_split':'Test','label_status':'provisional','qualified_label_approved':False}
    with pytest.raises(ValueError):ep.ProvisionalDevelopmentDataset(tmp_path,[row],'Training')


def test_cam_artifacts_always_carry_notice_and_unsupported_prediction(tmp_path,monkeypatch):
    # Generated pixels under a prescribed ID exercise output provenance only.
    source=tmp_path/'cam/Validation/00733.png';source.parent.mkdir(parents=True)
    payload=eb.export_rgb_png(Image.new('RGB',(8,4),(40,90,130)),source)
    row={'source_record_id':'Validation/00733','original_split':'Validation',
         'cam_original_path':'cam/Validation/00733.png','source_sha256':'a'*64,
         'cam_payload_sha256':payload['sha256'],'cam_rgb_sha256':payload['rgb_sha256'],
         'cam_dimensions':payload['dimensions']}
    def fake_cam(model,layer,prepared):
        rgb=prepared.original_rgb.copy()
        return {'original':rgb,'heatmap':rgb,'overlay':rgb,'cam':np.zeros((4,8)),
                'mgi_schema_grade':0,'model_class_index':0,'explanation_status':'synthetic_only'}
    monkeypatch.setattr(ep.vp,'class_gradcam',fake_cam)
    result=ep.save_cam(None,None,tmp_path,row,tmp_path/'out','synthetic-checkpoint')
    assert result['notice']==eb.NOTICE and result['unsupported_prediction'] and not result['clinical_validation']
    for name in ['original','heatmap','overlay','three_panel']:
        with Image.open(tmp_path/'out/gradcam/Validation_00733'/f'{name}.png') as image:
            assert image.info['notice']==eb.NOTICE
            assert image.info['srgb']==1


def test_unlisted_cam_example_blocked_before_image_read(tmp_path,monkeypatch):
    monkeypatch.setattr(Image,'open',lambda *a:pytest.fail('unlisted CAM original opened'))
    row={'source_record_id':'Validation/09999','original_split':'Validation','cam_original_path':'cam/Validation/09999.jpg'}
    with pytest.raises(ValueError,match='fixed'):ep.save_cam(None,None,tmp_path,row,tmp_path/'out','none')


def test_cam_rejects_payload_tampering_before_explanation(tmp_path,monkeypatch):
    path=tmp_path/'cam/Validation/00733.png';path.parent.mkdir(parents=True)
    payload=eb.export_rgb_png(Image.new('RGB',(8,4)),path)
    row={'source_record_id':'Validation/00733','original_split':'Validation','cam_original_path':'cam/Validation/00733.png',
         'source_sha256':'a'*64,'cam_payload_sha256':payload['sha256'],
         'cam_rgb_sha256':payload['rgb_sha256'],'cam_dimensions':payload['dimensions']}
    path.write_bytes(path.read_bytes()+b'changed')
    monkeypatch.setattr(ep.vp,'class_gradcam',lambda *a:pytest.fail('tampered image reached inference'))
    with pytest.raises(ValueError,match='payload hash'):ep.save_cam(None,None,tmp_path,row,tmp_path/'out','none')


TORCH_AVAILABLE=importlib.util.find_spec('torch') is not None


def tiny_model(torch):
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__();self.backbone=torch.nn.Sequential(torch.nn.Conv2d(3,2,1),torch.nn.BatchNorm2d(2))
            self.fc=torch.nn.Linear(2,5)
        def forward(self,x):return self.fc(self.backbone(x).mean((2,3)))
    return Tiny()


def synthetic_context():
    return {'experiment_kind':ep.KIND,'notice':eb.NOTICE,'qualified_labels_approved':False,
            'participant_independence_verified':False,'purpose':'synthetic only'}


@pytest.mark.skipif(not TORCH_AVAILABLE,reason='PyTorch unavailable; new synthetic pilot backend needs Colab')
def test_synthetic_adapter_fit_checkpoint_reload_and_frozen_bn(tmp_path):
    torch=ep.vp._torch();torch.set_num_threads(2)
    config=replace(ep.configuration('cpu'),epochs=1,patience=1,batch_size=2)
    datasets={}
    for split in ['Training','Validation']:
        rows=[]
        for index in range(4):
            path=f'images/{split}/{index:05}.png';target=tmp_path/path;target.parent.mkdir(parents=True,exist_ok=True)
            Image.new('RGB',(8,4),(30+index*30,50,70)).save(target)
            rows.append({'original_split':split,'image_path':path,'label_status':'provisional',
                         'qualified_label_approved':False,'provisional_mgi_grade':index+1})
        datasets[split]=ep.ProvisionalDevelopmentDataset(tmp_path,rows,split)
    tp.seed_everything(42);model=tiny_model(torch);before=model.backbone[1].running_mean.clone()
    result=tp._fit(model,datasets['Training'],datasets['Validation'],config,tmp_path/'synthetic_run',synthetic_context())
    assert len(result['history'])==1 and not result['five_class_validity_established']
    assert torch.equal(before,model.backbone[1].running_mean)
    path=tmp_path/'synthetic_run/best.pt'
    saved=ep.verify_checkpoint(path,eb.sha256(path),synthetic_context(),config)
    restored=tiny_model(torch);restored.load_state_dict(saved['model']);model.eval();restored.eval()
    inputs=torch.zeros(2,3,8,8)
    assert torch.equal(model(inputs),restored(inputs)) and model(inputs).shape==(2,5)


@pytest.mark.skipif(not TORCH_AVAILABLE,reason='PyTorch unavailable; checkpoint provenance test needs Colab')
def test_foreign_checkpoint_rejected_even_with_matching_byte_hash(tmp_path):
    torch=ep.vp._torch();config=ep.configuration('cpu');context=synthetic_context()
    wrong={**context,'experiment_kind':'final_research'}
    state={'schema':[0,1,2,3,4],'context':wrong,'config':asdict(config),
           'identity':tp.digest({'config':asdict(config),'context':wrong})}
    path=tmp_path/'foreign.pt';torch.save(state,path)
    with pytest.raises(ValueError,match='provenance'):ep.verify_checkpoint(path,eb.sha256(path),context,config)
