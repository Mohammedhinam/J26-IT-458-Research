"""Generated signal/provenance tests. No real feature extraction is authorized."""
import copy
from hashlib import sha256
import numpy as np
import pytest
from sklearn.metrics import confusion_matrix
from src.vision import frozen_feature_probe as probe


def fixture():
    labels=np.repeat(np.arange(1,5),20)
    ids=[f'generated/{i:03}' for i in range(len(labels))]
    groups=[f'g{i//2:03}' for i in range(len(labels))]
    features=np.eye(4)[labels-1]*3+np.random.default_rng(42).normal(0,.2,(len(labels),4))
    return features,ids,labels,groups


def test_deterministic_group_isolation_complete_oof_and_metrics():
    x,ids,y,groups=fixture()
    a=probe.probe(x,ids,y,groups); b=probe.probe(x,ids,y,groups)
    np.testing.assert_array_equal(a['folds'],b['folds'])
    for name in a['probabilities']:
        np.testing.assert_array_equal(a['probabilities'][name],b['probabilities'][name])
    for group in set(groups): assert len(set(a['folds'][np.array(groups)==group]))==1
    for fold in range(5):
        fit=a['folds']!=fold; score=~fit
        np.testing.assert_allclose(a['fold_checks'][fold]['scaler_mean'],x[fit].mean(0))
        expected=np.bincount(y[fit],minlength=5)[1:]/fit.sum()
        np.testing.assert_allclose(a['probabilities']['prior'][score],np.tile(expected,(score.sum(),1)))
    measured=a['metrics']['linear']; pred=a['probabilities']['linear'].argmax(1)+1
    assert measured['accuracy']==np.mean(pred==y)
    assert measured['confusion_matrix']==confusion_matrix(y,pred,labels=[1,2,3,4]).tolist()
    assert measured['accuracy']==1 # Known separable generated fixture only.
    ci=probe.paired_intervals(y,groups,a['probabilities'],repetitions=20)
    assert ci==probe.paired_intervals(y,groups,a['probabilities'],repetitions=20)
    assert ci['undefined_draws']==0


@pytest.mark.parametrize('fault',['nan','ids','labels','group','small'])
def test_invalid_feature_membership_rejected(fault):
    x,ids,y,groups=fixture()
    if fault=='nan': x[0,0]=np.nan
    if fault=='ids': ids[1]=ids[0]
    if fault=='labels': y[0]=0
    if fault=='group': groups[0]=''
    if fault=='small': y[:18]=2
    with pytest.raises(ValueError): probe.probe(x,ids,y,groups)


def test_no_real_paths_accessed_without_opt_in(monkeypatch):
    monkeypatch.setattr(probe.legacy,'safe_file',lambda *_:pytest.fail('File access before opt-in'))
    with pytest.raises(ValueError,match='opt-in'):
        probe.run_authorized('/data/Test','/weights','/out',{})


def test_untrusted_manifest_rejected_before_arrays(tmp_path,monkeypatch):
    (tmp_path/'bundle_manifest.json').write_text('{}')
    monkeypatch.setattr(probe.bundle,'model_array',lambda *_:pytest.fail('Payload accessed'))
    with pytest.raises(ValueError,match='manifest SHA'):
        probe.run_authorized(tmp_path,tmp_path/'weights',tmp_path/'out',{},opt_in=True)


def test_frozen_encoder_generated_resnet_features_and_no_bn_updates():
    import torch
    from torchvision.models import resnet50
    torch.manual_seed(42); torch.set_num_threads(2)
    model=resnet50(weights=None); model.fc=torch.nn.Identity(); model.requires_grad_(False); model.eval()
    values=np.zeros((224,224,3),dtype='<f4'); values[:112,:,0]=1.1; values[112:,:,2]=-.1
    a=probe.extract_features(model,[values],1); b=probe.extract_features(model,[values],1)
    assert a.shape==(1,2048)
    np.testing.assert_array_equal(a,b)
    model.train()
    with pytest.raises(ValueError,match='eval'): probe.extract_features(model,[values])


def test_future_real_run_requires_distinct_scope_and_current_bindings():
    with pytest.raises(ValueError,match='scope'):
        probe.legacy.authorise({'status':'owner_confirmed','scope':'run_cloud_exploratory_b1_mgi1to4_v1'},probe.SCOPE,{},opt_in=True)


@pytest.mark.parametrize('fault',['hash','ids','nan','object','shape','extra'])
def test_cache_corruption_and_membership_rejected(tmp_path,fault):
    x,ids,y,groups=fixture();folds=probe.make_folds(ids,y,groups)
    features=np.zeros((len(ids),2048),np.float32)
    values={'features':features,'ids':np.array(ids),'labels':y,'groups':np.array(groups),'folds':folds}
    path=tmp_path/'features.npz'
    np.savez(path,**values);digest=sha256(path.read_bytes()).hexdigest()
    np.testing.assert_array_equal(probe.load_feature_cache(path,digest,ids,y,groups,folds),features)
    if fault=='hash': digest='0'*64
    if fault=='ids':values['ids'][0]='changed'
    if fault=='nan':values['features'][0,0]=np.nan
    if fault=='object':values['features']=np.array([object()],dtype=object)
    if fault=='shape':values['features']=features[:1]
    if fault=='extra':values['unknown']=np.zeros(1)
    np.savez(path,**values)
    if fault!='hash':digest=sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):probe.load_feature_cache(path,digest,ids,y,groups,folds)
