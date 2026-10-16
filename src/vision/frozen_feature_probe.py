"""Training-only fixed-encoder probe. No automatic real-data run or download.

Synthetic callers may test fold and feature helpers. run_authorized requires
fresh owner scope and immutable bindings; old pilot permissions do not apply.
"""
from hashlib import sha256
import json
import io
from pathlib import Path
import warnings

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import exploratory_pilot_b1_v1 as pilot
from . import exploratory_bundle as legacy
from . import b1_development_bundle_v1 as bundle
from . import colour_b1_prototype as b1

VERSION = 'training680-frozen-resnet-probe-v1'
SCOPE = 'run_training680_frozen_probe_v1'
MANIFEST_SHA = '8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f'
WEIGHTS_SHA = '11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca'
CONFIG = {'version': VERSION, 'encoder': 'ResNet50_Weights.IMAGENET1K_V2',
          'dimensions': 2048, 'resolution': 224, 'folds': 5, 'seed': 42,
          'C': 1.0, 'class_weight': 'balanced', 'solver': 'lbfgs', 'max_iter': 2000,
          'scaler': 'StandardScaler_fit_inside_each_fold', 'bootstrap': 1000,
          'grades': [1,2,3,4], 'scope': 'Training_only', 'fine_tuning': False}


def code_hashes():
    return {**pilot.code_hashes(), 'frozen_feature_probe.py': legacy.sha256(__file__)}


def make_folds(ids, labels, groups):
    """Each record scores once; content groups cannot cross a fold boundary."""
    labels = pilot.checked_grades(labels)
    if (len(ids) != len(labels) or len(groups) != len(labels) or len(set(ids)) != len(ids)
            or list(ids) != sorted(ids) or any(not isinstance(g,str) or not g for g in groups)):
        raise ValueError('Sorted unique IDs and complete content groups required')
    if any(np.sum(labels==g)<5 for g in CONFIG['grades']):
        raise ValueError('Insufficient grade support for five folds')
    groups = np.asarray(groups)
    folds = np.full(len(labels), -1, int)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    for fold, (fit, score) in enumerate(splitter.split(np.zeros(len(labels)),labels,groups)):
        if set(groups[fit]) & set(groups[score]) or np.any(folds[score]!=-1):
            raise ValueError('Group leakage or repeated score assignment')
        if set(labels[fit]) != {1,2,3,4} or set(labels[score]) != {1,2,3,4}:
            raise ValueError('Every fitting/scoring fold must retain all four grades')
        folds[score]=fold
    if np.any(folds<0): raise ValueError('Incomplete OOF membership')
    return folds


def measure(labels, probabilities):
    result=pilot.metrics(labels,probabilities)
    pred=np.argmax(probabilities,axis=1)+1
    result.update(balanced_accuracy=float(balanced_accuracy_score(labels,pred)),
                  within_one_accuracy=float(np.mean(np.abs(labels-pred)<=1)),
                  predicted_counts=np.bincount(pred,minlength=5)[1:].tolist())
    return result


def probe(features, ids, labels, groups):
    """No encoder tuning. Fit all learned transformations on fitting rows only."""
    x=np.asarray(features); y=pilot.checked_grades(labels)
    if x.ndim!=2 or x.shape[0]!=len(y) or not np.isfinite(x).all():
        raise ValueError('Finite aligned feature matrix required')
    folds=make_folds(ids,y,groups)
    predictions={name:np.full((len(y),4),np.nan) for name in ('linear','majority','prior')}
    checks=[]
    for fold in range(5):
        fit,score=np.flatnonzero(folds!=fold),np.flatnonzero(folds==fold)
        model=make_pipeline(StandardScaler(), LogisticRegression(C=1.,class_weight='balanced',
                           solver='lbfgs',max_iter=2000,random_state=42))
        with warnings.catch_warnings():
            warnings.simplefilter('error',ConvergenceWarning)
            model.fit(x[fit],y[fit])
        if model.classes_.tolist()!=[1,2,3,4]: raise ValueError('Grade order mismatch')
        predictions['linear'][score]=model.predict_proba(x[score])
        for name,strategy in (('majority','most_frequent'),('prior','prior')):
            baseline=DummyClassifier(strategy=strategy).fit(x[fit],y[fit])
            predictions[name][score]=baseline.predict_proba(x[score])
        checks.append({'fold':fold,'fit_count':len(fit),'score_count':len(score),
                       'fit_support':np.bincount(y[fit],minlength=5)[1:].tolist(),
                       'scaler_mean':model[0].mean_.tolist()})
    if any(not np.isfinite(p).all() for p in predictions.values()):
        raise ValueError('Incomplete OOF predictions')
    return {'folds':folds,'probabilities':predictions,'fold_checks':checks,
            'metrics':{name:measure(y,p) for name,p in predictions.items()}}


def paired_intervals(labels, groups, probabilities, repetitions=1000):
    """Fixed-prediction content bootstrap; no claim of participant independence."""
    labels=np.asarray(labels); groups=np.asarray(groups)
    unique=np.unique(groups); members={g:np.flatnonzero(groups==g) for g in unique}
    generator=np.random.default_rng(42); undefined=0
    keys=('macro_f1_four_grades','balanced_accuracy','quadratic_weighted_kappa')
    draws={base:{key:[] for key in keys} for base in ('majority','prior')}
    for _ in range(repetitions):
        index=np.concatenate([members[g] for g in generator.choice(unique,len(unique),replace=True)])
        if set(labels[index])!={1,2,3,4}: undefined+=1; continue
        scored={name:measure(labels[index],p[index]) for name,p in probabilities.items()}
        for base in draws:
            for key in keys: draws[base][key].append(scored['linear'][key]-scored[base][key])
    return {'repetitions':repetitions,'undefined_draws':undefined,
            'conditional_only':True,'participant_independence_verified':False,
            'linear_minus_baseline_95':{base:{key:np.quantile(v,[.025,.975]).tolist() if v else None
                for key,v in values.items()} for base,values in draws.items()}}


def training_rows(manifest):
    """Use cached manifest safeguards before any model-array payload access."""
    rows,_=bundle.validate_manifest(manifest)
    selected=sorted((r for r in rows if r['original_split']=='Training'),key=lambda r:r['source_record_id'])
    if len(selected)!=680 or np.bincount([r['provisional_mgi_grade'] for r in selected],minlength=5).tolist()!=[0,12,84,223,361]:
        raise ValueError('Pinned Training membership/support mismatch')
    return selected


def extract_features(model, arrays, batch_size=16):
    """Immutable eval encoder; caller yields only already verified B1 arrays."""
    import torch
    if batch_size<1 or batch_size>32: raise ValueError('Bounded batch size required')
    if any(p.requires_grad for p in model.parameters()) or any(m.training for m in model.modules()):
        raise ValueError('Frozen eval encoder required')
    initial={name:value.detach().clone() for name,value in model.state_dict().items()}
    output=[]; batch=[]
    def forward():
        with torch.no_grad():
            result=model(torch.from_numpy(np.stack(batch))).detach().cpu().numpy()
        if result.shape!=(len(batch),2048) or not np.isfinite(result).all():
            raise ValueError('Expected finite 2048-dimensional frozen features')
        output.append(result); batch.clear()
    for array in arrays:
        if array.shape!=(224,224,3): raise ValueError('Expected B1 model-view geometry')
        batch.append(b1.normalize(b1._array(array)))
        if len(batch)==batch_size: forward()
    if batch: forward()
    if not output: raise ValueError('No features extracted')
    if any(not torch.equal(value,initial[name]) for name,value in model.state_dict().items()):
        raise ValueError('Frozen encoder/BatchNorm changed')
    return np.concatenate(output)


def load_feature_cache(path, expected_sha, ids, labels, groups, folds):
    """Hashes and exact membership bind a numeric-only feature cache."""
    path=Path(path)
    if path.is_symlink() or path.stat().st_size>64*1024*1024:
        raise ValueError('Unsafe feature cache')
    raw=path.read_bytes()
    if sha256(raw).hexdigest()!=expected_sha: raise ValueError('Feature cache SHA mismatch')
    with np.load(io.BytesIO(raw),allow_pickle=False) as cache:
        if set(cache.files)!={'features','ids','labels','groups','folds'}:
            raise ValueError('Unexpected cache payloads')
        for key,expected in (('ids',ids),('labels',labels),('groups',groups),('folds',folds)):
            if not np.array_equal(cache[key],expected): raise ValueError('Feature cache membership changed')
        features=cache['features']
        if features.shape!=(len(ids),2048) or features.dtype!=np.float32 or not np.isfinite(features).all():
            raise ValueError('Invalid cached features')
    return features


def run_authorized(root, weights, output, authorization, *, opt_in=False):
    """Explicit future local execution; never scans sources or opens Test files."""
    if not opt_in: raise ValueError('Fresh real-run owner opt-in required before data access')
    root,weights,output=Path(root),Path(weights),Path(output)
    manifest_path=legacy.safe_file(root,'bundle_manifest.json')
    raw=manifest_path.read_bytes()
    if sha256(raw).hexdigest()!=MANIFEST_SHA: raise ValueError('Pinned manifest SHA mismatch')
    rows=training_rows(json.loads(raw))
    ids=[r['source_record_id'] for r in rows]; labels=np.array([r['provisional_mgi_grade'] for r in rows])
    groups=[r['content_group_id'] for r in rows]; folds=make_folds(ids,labels,groups)
    bindings={'manifest_sha256':MANIFEST_SHA,'weights_sha256':WEIGHTS_SHA,
              'config_sha256':b1.digest_json(CONFIG),'code_sha256':b1.digest_json(code_hashes()),
              'selection_sha256':b1.digest_json(rows),'fold_sha256':b1.digest_json(folds.tolist()),
              'output_path_sha256':sha256(str(output.resolve()).encode()).hexdigest()}
    legacy.authorise(authorization,SCOPE,bindings,opt_in=True)
    if weights.is_symlink() or not weights.is_file() or legacy.sha256(weights)!=WEIGHTS_SHA:
        raise ValueError('Official fixed ImageNet V2 weights required; no downloads')
    if output.exists(): raise ValueError('Fresh output required')
    # Output can only be local ignored data; never a source/model directory.
    legacy.new_ignored_output(output,'data')
    if output.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(output.resolve()):
        raise ValueError('Output must be separate from the input bundle')
    output.mkdir(parents=True,exist_ok=False)
    import torch
    from torchvision.models import resnet50
    torch.manual_seed(42); torch.set_num_threads(2)
    model=resnet50(weights=None)
    raw_weights=weights.read_bytes()
    if sha256(raw_weights).hexdigest()!=WEIGHTS_SHA: raise ValueError('Weights changed before load')
    model.load_state_dict(torch.load(io.BytesIO(raw_weights),map_location='cpu',weights_only=True),strict=True)
    del raw_weights
    model.fc=torch.nn.Identity(); model.requires_grad_(False); model.eval()
    def arrays():
        for row in rows:
            yield bundle.model_array(legacy.safe_file(root,row['model_path']),row['model_sha256'])
    # Freeze prospective configuration and folds before extracting or fitting.
    (output/'protocol.json').write_text(json.dumps({'config':CONFIG,'bindings':bindings,'ids':ids,'folds':folds.tolist()},indent=2))
    features=extract_features(model,arrays())
    cache=output/'features.npz'
    np.savez(cache,features=features,ids=np.array(ids),labels=labels,groups=np.array(groups),folds=folds)
    features=load_feature_cache(cache,legacy.sha256(cache),ids,labels,groups,folds)
    result=probe(features,ids,labels,groups)
    np.savez(output/'oof.npz',ids=np.array(ids),labels=labels,folds=folds,**result['probabilities'])
    summary={'notice':legacy.NOTICE,'config':CONFIG,'bindings':bindings,'metrics':result['metrics'],
             'uncertainty':paired_intervals(labels,groups,result['probabilities']),
             'feature_cache_sha256':legacy.sha256(cache),'oof_sha256':legacy.sha256(output/'oof.npz'),
             'test_used':False,'validation53_used':False,'real_run':True,'fits':15}
    (output/'results.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    return summary
