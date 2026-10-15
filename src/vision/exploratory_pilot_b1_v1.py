"""Opt-in four-output PP1 pilot, separate from five-grade research training.

No automatic downloads/uploads, Test loader or clinical approval. Real training
requires a future explicit cloud/training authorization and verified package.
"""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
import shutil
import stat
import zipfile

import numpy as np
from PIL import Image

from src.vision import b1_development_bundle_v1 as bundle
from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_streaming as stream
from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_pilot as original_pilot
from src.vision import model_pipeline as models
from src.vision import train_pipeline as trainer


VERSION = "pp1-b1-mgi1to4-pilot-v1"
GRADES = (1,2,3,4)
SCOPE = "run_cloud_exploratory_b1_mgi1to4_v1"


def extract_verified_zip(archive,destination,expected_archive_sha256,trusted_manifest_sha256):
    """Future explicitly authorized upload only; bounded exact-manifest extraction."""
    archive=Path(archive);destination=Path(destination)
    if legacy.sha256(archive)!=expected_archive_sha256:
        raise ValueError("Data archive SHA mismatch")
    if destination.exists() or any(p.is_symlink() for p in (destination,*destination.parents)):
        raise ValueError("Fresh canonical extraction path required")
    with zipfile.ZipFile(archive) as zipped:
        names=zipped.namelist()
        if len(names)!=737 or len(set(names))!=737:
            raise ValueError("Exact737 archive entries required")
        for info in zipped.infolist():
            legacy.relative_path(info.filename)
            if (info.is_dir() or not stat.S_ISREG(info.external_attr>>16)
                    or info.file_size>stream.MAX_PIXELS*12+1024):
                raise ValueError("Unsafe archive entry")
        if sum(info.file_size for info in zipped.infolist())>2*1024**3:
            raise ValueError("Archive uncompressed size exceeds2GiB")
        info=zipped.getinfo('bundle_manifest.json')
        if info.file_size>8*1024**2:raise ValueError("Manifest too large")
        raw=zipped.read('bundle_manifest.json')
        if sha256(raw).hexdigest()!=trusted_manifest_sha256:raise ValueError("Manifest SHA mismatch")
        manifest=json.loads(raw,object_pairs_hook=stream._unique_json_pairs)
        _,expected=bundle.validate_manifest(manifest)
        if set(names)!=expected:raise ValueError("Archive extra/missing/Test material")
        destination.mkdir(mode=0o700,parents=True,exist_ok=False)
        for name in sorted(names):
            path=destination/name;path.parent.mkdir(parents=True,exist_ok=True)
            with zipped.open(name) as source,stream._open(path,write=True) as target:
                shutil.copyfileobj(source,target,1024*1024)
    return bundle.verify(destination,trusted_manifest_sha256)


def configuration(device="cuda"):
    return trainer.TrainingConfig("resnet50",16,5,.001,2,seed=42,
                                  freeze_backbone=True,batchnorm="frozen",class_weight="none",device=device)


def protocol():
    return {"version":VERSION,"grades":list(GRADES),"research_schema_unchanged":[0,1,2,3,4],
            "training":asdict(configuration()),"early_stopping":"Validation_four_grade_macro_F1",
            "augmentation":"none_for_bounded_initial_head_only_pilot",
            "weights":"ResNet50_Weights.IMAGENET1K_V2","notice":legacy.NOTICE,
            "healthy_mgi0_supported":False,"final_research":False}


def code_hashes():
    return {**bundle.code_hashes(),"exploratory_pilot_b1_v1.py":legacy.sha256(__file__),
            "exploratory_pilot.py":legacy.sha256(original_pilot.__file__)}


def checked_grades(labels):
    values=np.asarray(labels)
    if (values.ndim!=1 or not values.size or values.dtype.kind not in "iu"
            or not np.isin(values,GRADES).all()):
        raise ValueError("This pilot supports original MGI grades1..4 only")
    return values


def metrics(labels,probabilities):
    labels=checked_grades(labels);probabilities=np.asarray(probabilities,dtype=float)
    if probabilities.shape!=(len(labels),4):raise ValueError("Exactly four ordered probabilities required")
    # Reuse verified confusion/AUC/Brier/ordinal math. The zero column is only
    # an internal metric adapter, not a fifth model output or fabricated label.
    measured=trainer.validation_metrics(labels,np.pad(probabilities,((0,0),(1,0))))
    recalls=measured["per_grade_recall"][1:];aucs=measured["per_grade_auroc"][1:]
    f1=[0. if x is None else x for x in measured["per_grade_f1"][1:]]
    return {"notice":legacy.NOTICE,"mgi_grades":list(GRADES),"n":len(labels),
            "support":measured["support"][1:],"accuracy":measured["accuracy"],
            "confusion_matrix":[row[1:] for row in measured["confusion_matrix"][1:]],
            "macro_f1_four_grades":float(np.mean(f1)),"per_grade_f1":measured["per_grade_f1"][1:],
            "per_grade_recall":recalls,"per_grade_auroc":aucs,
            "macro_auroc":None if None in aucs else float(np.mean(aucs)),
            "multiclass_brier":measured["multiclass_brier"],"ordinal_mae":measured["ordinal_mae"],
            "quadratic_weighted_kappa":measured["quadratic_weighted_kappa"],
            "clinical_validation":False,"healthy_mgi0_supported":False}


def majority_baseline(training,validation):
    training=checked_grades(training);validation=checked_grades(validation)
    counts=np.bincount(training,minlength=5)[1:]
    index=int(counts.argmax());prob=np.zeros((len(validation),4));prob[:,index]=1
    return {"derived_from":"Training_only","majority_mgi_grade":GRADES[index],
            "training_support":counts.tolist(),"validation":metrics(validation,prob)}


def make_model(*,pretrained=False):
    # Preserve the original factory and research model. Replace its temporary
    # head only in this explicitly versioned exploratory model instance.
    result=models.make_model("resnet50",pretrained=pretrained,allow_download=False,freeze_backbone=True)
    torch=models._torch();model=result["model"]
    model.fc=torch.nn.Linear(model.fc.in_features,4)
    result.update(spec={**result["spec"],"exploratory_version":VERSION,"mgi_grades":GRADES},
                  five_class_validity_established=False)
    return result


class Dataset:
    def __init__(self,root,rows,split):
        if split not in legacy.EXPECTED_COUNTS or not rows:
            raise ValueError("Nonempty development split required")
        self.root=Path(root);self.records=list(rows)
        for row in self.records:
            if (row["original_split"]!=split or row["source_record_id"] in legacy.NP015_IDS
                    or row["label_status"]!="provisional" or row["qualified_label_approved"] is not False):
                raise ValueError("Held/Test/mixed/approved record forbidden")
        checked_grades([r["provisional_mgi_grade"] for r in self.records])

    def __len__(self):return len(self.records)

    def __getitem__(self,index):
        row=self.records[index]
        values=bundle.model_array(legacy.safe_file(self.root,row["model_path"]),row["model_sha256"])
        return b1.normalize(values),GRADES.index(row["provisional_mgi_grade"])


def run_epoch(model,loader,config,optimizer=None):
    torch=models._torch()
    trainer.training_mode(model,config) if optimizer is not None else model.eval()
    criterion=torch.nn.CrossEntropyLoss(reduction="sum")
    labels=[];probabilities=[];loss_sum=0.
    with torch.set_grad_enabled(optimizer is not None):
        for values,target in loader:
            values=values.to(config.device,dtype=torch.float32);target=target.to(config.device,dtype=torch.long)
            if not torch.isfinite(values).all() or torch.any((target<0)|(target>3)):
                raise ValueError("Unsafe four-grade tensor input")
            if optimizer is not None:optimizer.zero_grad(set_to_none=True)
            logits=model(values)
            if logits.shape!=(len(target),4) or not torch.isfinite(logits).all():
                raise ValueError("Four finite exploratory logits required")
            loss=criterion(logits,target)
            if not torch.isfinite(loss):raise ValueError("Nonfinite pilot loss")
            if optimizer is not None:
                (loss/len(target)).backward();optimizer.step()
            loss_sum+=float(loss.detach())
            labels.extend((target.detach().cpu()+1).tolist())
            probabilities.extend(logits.detach().softmax(dim=1).cpu().tolist())
    if not labels:raise ValueError("Empty pilot epoch")
    return {"loss":loss_sum/len(labels),**metrics(labels,probabilities)}


def load_checkpoint(path,expected_sha,context,config):
    if legacy.sha256(path)!=expected_sha:raise ValueError("Checkpoint SHA mismatch")
    state=models._torch().load(path,map_location="cpu",weights_only=True)
    if (state.get("version")!=VERSION or state.get("schema")!=list(GRADES)
            or state.get("identity")!=trainer.digest({"context":context,"config":asdict(config)})
            or state.get("context")!=context):
        raise ValueError("Wrong exploratory checkpoint provenance/configuration")
    return state


def fit(model,training,validation,config,output,context):
    """Bounded four-grade loop. Does not call or weaken fit_approved()."""
    torch=models._torch();config.validate();trainer.seed_everything(config.seed)
    trainer.configure_trainable_layers(model,config);model.to(config.device)
    output=Path(output);output.mkdir(mode=0o700,parents=True,exist_ok=False)
    optimizer=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=config.learning_rate)
    loaders={"Training":torch.utils.data.DataLoader(training,batch_size=config.batch_size,shuffle=True,
                         num_workers=0,generator=torch.Generator().manual_seed(config.seed)),
             "Validation":torch.utils.data.DataLoader(validation,batch_size=config.batch_size,shuffle=False,num_workers=0)}
    history=[];best=-float("inf");bad=0
    identity=trainer.digest({"context":context,"config":asdict(config)})
    for epoch in range(config.epochs):
        train=run_epoch(model,loaders["Training"],config,optimizer)
        val=run_epoch(model,loaders["Validation"],config)
        best,bad,improved=trainer.stopping_update(val["macro_f1_four_grades"],best,bad,config.patience,config.min_delta)
        history.append({"epoch":epoch+1,"training":train,"validation":val,"notice":legacy.NOTICE})
        state={"version":VERSION,"schema":list(GRADES),"identity":identity,"context":context,
               "config":asdict(config),"epoch":epoch+1,"history":history,"model":model.state_dict(),
               "optimizer":optimizer.state_dict(),"best":best,"bad_epochs":bad}
        trainer._save_checkpoint(output/"last.pt",state)
        if improved:trainer._save_checkpoint(output/"best.pt",state)
        if bad>=config.patience:break
    state=load_checkpoint(output/"best.pt",legacy.sha256(output/"best.pt"),context,config)
    model.load_state_dict(state["model"]);model.eval()
    return {"notice":legacy.NOTICE,"history":history,"best_epoch":state["epoch"],
            "best_validation_macro_f1_four_grades":state["best"],"test_used":False}


def gradcam(model,layer,prepared):
    torch=models._torch();states=[(m,m.training) for m in model.modules()];captured=[]
    hook=layer.register_forward_hook(lambda module,inputs,output:captured.append(output))
    try:
        model.eval()
        with torch.enable_grad():
            values=torch.tensor(prepared.normalized_chw[None],device=next(model.parameters()).device,requires_grad=True)
            logits=model(values)
            if logits.shape!=(1,4) or not torch.isfinite(logits).all():raise ValueError("Four finite CAM logits required")
            selected=int(logits.argmax())
            if len(captured)!=1:raise ValueError("Ambiguous CAM capture")
            gradients=torch.autograd.grad(logits[0,selected],captured[0])[0]
            views=models.gradcam_views(captured[0].detach().cpu().numpy()[0],
                                       gradients.detach().cpu().numpy()[0],prepared)
        return {**views,"predicted_mgi_grade":GRADES[selected],"probabilities":logits.detach().softmax(1).cpu().tolist()[0],
                "notice":legacy.NOTICE,"display_notice":"Display-only clipped sRGB preview; not colour-identical source or clinical boundary"}
    finally:
        hook.remove()
        for module,state in states:module.training=state


def cam_input(root,row):
    if row["source_record_id"] not in legacy.CAM_IDS or row["original_split"]!="Validation":
        raise ValueError("Only three fixed Validation CAM examples")
    path=legacy.safe_file(root,row["cam_path"]);width,height=row["source_dimensions"]
    with stream._open(path) as handle:
        evidence,offset,identity=stream._inspect(handle,(height,width,3))
        if evidence["sha256"]!=row["cam_sha256"]:raise ValueError("CAM payload changed")
        array=np.memmap(handle,dtype="<f4",mode="r",offset=offset,shape=(height,width,3))
        scale=min(1.,1200/max(width,height));w,h=max(1,round(width*scale)),max(1,round(height*scale))
        xs=np.minimum(((np.arange(w)+.5)*width/w).astype(int),width-1)
        ys=np.minimum(((np.arange(h)+.5)*height/h).astype(int),height-1)
        preview=np.rint(np.clip(array[ys[:,None],xs],0,1)*255).astype(np.uint8)
        del array
        if stream._identity(handle)!=identity:raise ValueError("CAM identity changed")
    model=bundle.model_array(legacy.safe_file(root,row["model_path"]),row["model_sha256"])
    return b1.B1Input(preview,b1.normalize(model),tuple(row["valid_box"]),
                      {"display_only":True,"source_dimensions":[width,height],"preview_dimensions":[w,h]})


def run_pilot(root,trusted_manifest_sha256,authorization,output,*,opt_in=False):
    root=Path(root);output=Path(output)
    weights=original_pilot.pretrained_status()
    bound={"bundle_manifest_sha256":trusted_manifest_sha256,"protocol_sha256":trainer.digest(protocol()),
           "code_sha256":trainer.digest(code_hashes()),"weights_sha256":weights["sha256"],"output_run_id":output.name}
    legacy.authorise(authorization,SCOPE,bound,opt_in)
    if authorization.get("cloud_upload_authorized") is not True or authorization.get("training_authorized") is not True:
        raise ValueError("Separate explicit cloud and exploratory training permission required")
    if (not root.resolve().is_relative_to(Path('/content/b1_pp1_pilot')) or Path('/content/drive').exists()):
        raise ValueError("Fresh isolated Colab root without Drive mount required")
    if weights["status"]!="documented_cache_present":raise FileNotFoundError("Approved cached ImageNet V2 weights required; no download")
    torch=models._torch()
    if not torch.cuda.is_available():raise RuntimeError("GPU required for this bounded pilot")
    bundle.verify(root,trusted_manifest_sha256)
    manifest=bundle.load_json(legacy.safe_file(root,'bundle_manifest.json'))
    split={s:[r for r in manifest['records'] if r['original_split']==s] for s in legacy.EXPECTED_COUNTS}
    datasets={s:Dataset(root,rows,s) for s,rows in split.items()}
    labels={s:[r['provisional_mgi_grade'] for r in rows] for s,rows in split.items()}
    config=configuration();trainer.seed_everything(config.seed)
    network=make_model(pretrained=True)
    context={"version":VERSION,"notice":legacy.NOTICE,"manifest_sha256":trusted_manifest_sha256,
             "protocol":protocol(),"source_hashes":code_hashes(),"weights":weights,
             "runtime":{"python":platform.python_version(),"torch":str(torch.__version__),
                        "numpy":np.__version__,"gpu":torch.cuda.get_device_name()},
             "qualified_labels_approved":False,"participant_independence_verified":False,
             "final_research_approved":False,"test_used":False}
    result=fit(network['model'],datasets['Training'],datasets['Validation'],config,output,context)
    result.update(majority_baseline=majority_baseline(labels['Training'],labels['Validation']),protocol=protocol(),
                  weights=weights,cam=[],warning='Only one provisional Validation MGI1; no healthy MGI0 detection or participant-independent accuracy')
    for identifier in legacy.CAM_IDS:
        row=next(r for r in split['Validation'] if r['source_record_id']==identifier)
        views=gradcam(network['model'],network['cam_layer'],cam_input(root,row))
        directory=output/'gradcam'/identifier.replace('/','_');directory.mkdir(parents=True)
        for name in ('original','heatmap','overlay'):
            Image.fromarray(views[name]).save(directory/(name+'.png'))
        result['cam'].append({k:v for k,v in views.items() if k not in ('original','heatmap','overlay','cam')})
    bundle.write_json(output/'pilot_results.json',result)
    return result
