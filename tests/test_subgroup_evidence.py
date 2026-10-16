import numpy as np
import pytest
from src.tabular.subgroup_evidence import summary,subgroup_rows


def test_independent_confusion_and_deterministic_intervals():
    y=np.array([0,0,1,1]);p=np.array([.1,.7,.4,.9])
    r=summary(y,p,20)
    assert [r[k] for k in ('TN','FP','FN','TP')]==[1,1,1,1]
    assert r['sensitivity_at_050']==.5 and r['specificity_at_050']==.5
    assert r['Brier']==pytest.approx(np.mean((y-p)**2))
    assert r==summary(y,p,20)


def test_empty_and_one_outcome_groups_are_explicit():
    r=subgroup_rows(np.array([0,0]),np.array([.1,.2]),np.array([30,44]),np.array([1,1]),10)
    assert r['age_30_44']['AUROC'] is None
    assert r['age_30_44']['undefined_AUROC_draws']==10
    assert r['age_45_59']=={'n':0,'status':'no_support'}
    assert r['recorded_sex_2']['n']==0


@pytest.mark.parametrize('fault',['age','sex','nan'])
def test_invalid_demographics_or_probability_rejected(fault):
    age=[55];sex=[1];prob=[.2]
    if fault=='age':age=[29]
    if fault=='sex':sex=[9]
    if fault=='nan':prob=[np.nan]
    with pytest.raises(ValueError):subgroup_rows([1],prob,age,sex,10)
