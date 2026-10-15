"""Four-grade exploratory configuration; synthetic data and weights=None only."""
from pathlib import Path

import numpy as np
import pytest

from src.vision import exploratory_pilot_b1_v1 as pilot
from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_iccv2_generated as v2
from src.vision import model_pipeline as original
from src.vision import train_pipeline as trainer
from test_colour_b1_iccv2_generated import make_profile,pixels


@pytest.mark.parametrize('bad',[[0],[5],[-1],[1.5],[],[1,0,4]])
def test_original_grades_not_relabelled_to_include_zero(bad):
    with pytest.raises(ValueError):pilot.checked_grades(bad)


def test_four_grade_perfect_metrics_and_no_healthy_claim():
    result=pilot.metrics([1,2,3,4],np.eye(4))
    assert result['macro_f1_four_grades']==1 and result['accuracy']==1
    assert result['multiclass_brier']==0 and result['ordinal_mae']==0
    assert result['quadratic_weighted_kappa']==1 and result['macro_auroc']==1
    assert result['support']==[1,1,1,1] and len(result['confusion_matrix'])==4
    assert not result['clinical_validation'] and not result['healthy_mgi0_supported']


def test_majority_uses_training_only_and_ties_choose_lower_grade():
    result=pilot.majority_baseline([1,2,3,4],[4,4,4])
    assert result['majority_mgi_grade']==1
    assert result['validation']['accuracy']==0
    assert result['validation']['macro_auroc'] is None


@pytest.mark.parametrize('bad',[np.full((4,5),.2),np.full((4,4),np.nan),np.ones((4,4)),np.full((4,4),-.25)])
def test_invalid_probabilities_fail_closed(bad):
    with pytest.raises(ValueError):pilot.metrics([1,2,3,4],bad)


@pytest.mark.parametrize('split',['Test','test','Training/../Test'])
def test_dataset_rejects_test_before_payload_access(split):
    with pytest.raises(ValueError):pilot.Dataset('/nonexistent',[],split)


def test_pilot_requires_future_explicit_training_authorization_before_data_access():
    with pytest.raises(ValueError):pilot.run_pilot('/nonexistent','0'*64,{},'/nonexistent',opt_in=False)


def test_protocol_is_bounded_separate_and_preserves_research_schema():
    p=pilot.protocol();config=pilot.configuration('cpu');config.validate()
    assert p['grades']==[1,2,3,4] and original.MGI_GRADES==(0,1,2,3,4)
    assert config.epochs==5 and config.patience==2 and config.batch_size==16
    assert config.learning_rate==.001 and config.seed==42 and config.batchnorm=='frozen'
    assert not p['healthy_mgi0_supported'] and not p['final_research']


def torch_backend():
    torch=pytest.importorskip('torch',reason='No compatible backend installed locally; no install authorized')
    pytest.importorskip('torchvision')
    torch.set_num_threads(1)
    return torch


def prepared():
    canonical=v2.convert_generated(pixels(),make_profile()[0])[0]
    view,box=b1.letterbox(canonical);preview,notice=b1.display_preview(canonical)
    return b1.B1Input(preview,b1.normalize(view),tuple(box),notice)


def test_resnet50_four_output_optimization_and_frozen_batchnorm_weights_none():
    torch=torch_backend();trainer.seed_everything(42)
    model=pilot.make_model(pretrained=False)['model'];config=pilot.configuration('cpu')
    trainer.configure_trainable_layers(model,config);trainer.training_mode(model,config)
    old_mean=model.bn1.running_mean.clone();old_head=model.fc.weight.detach().clone()
    optimizer=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=.001)
    values=torch.tensor(np.stack([prepared().normalized_chw]*2));labels=torch.tensor([0,3])
    logits=model(values)
    assert tuple(logits.shape)==(2,4) and torch.isfinite(logits).all()
    torch.nn.functional.cross_entropy(logits,labels).backward();optimizer.step()
    assert torch.equal(old_mean,model.bn1.running_mean)
    assert not torch.equal(old_head,model.fc.weight)
    assert all(not p.requires_grad for name,p in model.named_parameters() if not name.startswith('fc.'))


def test_four_class_gradcam_geometry_and_hook_cleanup_weights_none():
    torch=torch_backend();trainer.seed_everything(42)
    model=pilot.make_model(pretrained=False);layer=model['cam_layer']
    count=len(layer._forward_hooks)
    result=pilot.gradcam(model['model'],layer,prepared())
    assert result['predicted_mgi_grade'] in (1,2,3,4) and len(result['probabilities'])==4
    for key in ('original','heatmap','overlay'):assert result[key].shape==(16,16,3)
    assert len(layer._forward_hooks)==count
    np.testing.assert_allclose(sum(result['probabilities']),1,atol=1e-6)


def test_four_class_synthetic_checkpoint_loading_and_reproducibility(tmp_path):
    torch=torch_backend()
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__();self.features=torch.nn.Sequential(torch.nn.Conv2d(3,4,1),torch.nn.BatchNorm2d(4),torch.nn.ReLU())
            self.fc=torch.nn.Linear(4,4)
        def forward(self,x):return self.fc(self.features(x).mean((2,3)))
    data=[(torch.full((3,8,8),i/4),i) for i in range(4)]
    config=trainer.TrainingConfig('resnet50',4,2,.001,2,seed=42,device='cpu')
    context={'notice':pilot.legacy.NOTICE,'generated_only':True}
    results=[]
    for name in ('a','b'):
        trainer.seed_everything(42);model=Tiny()
        result=pilot.fit(model,data,data,config,tmp_path/name,context)
        checkpoint=tmp_path/name/'best.pt';h=pilot.legacy.sha256(checkpoint)
        state=pilot.load_checkpoint(checkpoint,h,context,config)
        assert state['schema']==[1,2,3,4] and result['best_epoch']>=1
        with pytest.raises(ValueError):pilot.load_checkpoint(checkpoint,'0'*64,context,config)
        with pytest.raises(ValueError):pilot.load_checkpoint(checkpoint,h,{'wrong':True},config)
        results.append(result)
    assert results[0]==results[1]
