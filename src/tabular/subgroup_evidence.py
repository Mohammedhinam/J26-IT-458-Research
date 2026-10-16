"""Prespecified descriptive age/sex checks on existing development OOF scores.

No model fits or threshold tuning. Patient-level bootstrap is conditional on
saved predictions, not survey-design or independently held-out uncertainty.
"""
import hashlib
import json
import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss, confusion_matrix
from .baseline_nhanes import ROOT, DATA_DIR, read_development_xpt
from .pp1_questionnaire_workflow import MANIFEST_HASH, LOCAL

# Fixed before reading demographic results. The final bin includes released 80+.
AGE_BINS=((30,44),(45,59),(60,80))


def summary(labels, probabilities, repetitions=1000):
    y=np.asarray(labels);p=np.asarray(probabilities)
    if (y.ndim!=1 or p.shape!=y.shape or not len(y) or not np.isin(y,[0,1]).all()
            or not np.isfinite(p).all() or np.any((p<0)|(p>1))):
        raise ValueError('Aligned finite binary outcomes/probabilities required')
    tn,fp,fn,tp=map(int,confusion_matrix(y,p>=.5,labels=[0,1]).ravel())
    auc=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None
    rng=np.random.default_rng(42);aucs=[];briers=[];undefined=0
    for _ in range(repetitions):
        index=rng.integers(0,len(y),len(y));a,b=y[index],p[index]
        briers.append(float(np.mean((a-b)**2)))
        if len(np.unique(a))<2: undefined+=1
        else: aucs.append(float(roc_auc_score(a,b)))
    return {'n':len(y),'positive':int(y.sum()),'negative':int(len(y)-y.sum()),
            'AUROC':auc,'Brier':float(brier_score_loss(y,p)),
            'sensitivity_at_050':tp/(tp+fn) if tp+fn else None,
            'specificity_at_050':tn/(tn+fp) if tn+fp else None,
            'TN':tn,'FP':fp,'FN':fn,'TP':tp,
            'conditional_AUROC_95':np.quantile(aucs,[.025,.975]).tolist() if aucs else None,
            'conditional_Brier_95':np.quantile(briers,[.025,.975]).tolist(),
            'bootstrap_repetitions':repetitions,'undefined_AUROC_draws':undefined,
            'small_outcome_support':min(tn+fp,tp+fn)<20}


def subgroup_rows(labels, probabilities, ages, sex, repetitions=1000):
    y,p,age,sex=map(np.asarray,(labels,probabilities,ages,sex))
    if any(a.shape!=y.shape for a in (p,age,sex)) or not np.isfinite(age).all():
        raise ValueError('Missing/misaligned subgroup evidence')
    if not np.isin(sex,[1,2]).all() or np.any((age<30)|(age>80)):
        raise ValueError('Unexpected age/recorded-sex codes')
    masks={f'age_{lo}_{hi}':(age>=lo)&(age<=hi) for lo,hi in AGE_BINS}
    masks.update(recorded_sex_1=sex==1,recorded_sex_2=sex==2)
    return {name:summary(y[mask],p[mask],repetitions) if mask.any() else {'n':0,'status':'no_support'}
            for name,mask in masks.items()}


def main():
    evidence=ROOT/'docs/tabular_subgroup_evidence_v1.json';report=evidence.with_suffix('.md')
    if evidence.exists() or report.exists(): raise FileExistsError('Preserve historical subgroup evidence')
    manifest=ROOT/'data/preprocessing/split_manifest.json';raw=manifest.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_HASH: raise ValueError('Split hash mismatch')
    ids=json.loads(raw)['development']
    aggregate=json.loads((ROOT/'docs/tabular_pp1_completion_results_v1.json').read_text())
    pred=LOCAL/'development_oof.npz'
    if hashlib.sha256(pred.read_bytes()).hexdigest()!=aggregate['oof_sha256']: raise ValueError('OOF hash mismatch')
    with np.load(pred,allow_pickle=False) as d:
        if d['SEQN'].tolist()!=ids: raise ValueError('OOF membership mismatch')
        y,p=d['y'].copy(),d['A_reference'].copy()
    demo=read_development_xpt(DATA_DIR/'P_DEMO.xpt',ids).set_index('SEQN').loc[ids]
    rows=subgroup_rows(y,p,demo['RIDAGEYR'].to_numpy(),demo['RIAGENDR'].to_numpy())
    if manifest.read_bytes()!=raw: raise ValueError('Split changed')
    result={'version':'development-subgroups-v1','model':'Full XGBoost A reference',
            'n':len(y),'age_bins':AGE_BINS,'manifest_sha256':MANIFEST_HASH,'oof_sha256':aggregate['oof_sha256'],
            'subgroups':rows,'new_model_fits':0,'held_out_payloads_accessed':False,
            'survey_design_uncertainty':False,'external_fairness_proven':False}
    evidence.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# Development-only age/recorded-sex evidence — 2026-10-16','',
      'Signed proposal §3.5. Fixed age bins 30–44, 45–59 and 60–80 (80 means 80+); released sex codes 1/2. No data-driven subgroup selection, model refit or threshold tuning. Reused hash-bound A-reference OOF probabilities and selective development-only demographics.', '',
      '| Group | N | Yes | AUROC | Brier | Sensitivity @0.50 | Specificity @0.50 |',
      '| --- | --- | --- | --- | --- | --- | --- |']
    for name,r in rows.items():
        lines.append(f"| {name} | {r['n']} | {r['positive']} | {r['AUROC']:.6f} | {r['Brier']:.6f} | {r['sensitivity_at_050']:.6f} | {r['specificity_at_050']:.6f} |")
    lines+=['','JSON includes TN/FP/FN/TP and 1,000 seed-42 respondent bootstrap AUROC/Brier intervals, conditional on saved predictions. These omit model-selection/refitting and complex-survey uncertainty. Group differences do not establish discrimination, fairness or transportability. No final clinical cutoff, protected Test evaluation or causal claim.']
    report.write_text('\n'.join(lines)+'\n');print('\n'.join(lines))


if __name__=='__main__':main()
