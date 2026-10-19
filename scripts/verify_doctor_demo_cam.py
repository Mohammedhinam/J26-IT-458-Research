"""Bounded check on one explicitly supplied non-study photo; no training or data scan."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

from src.vision import local_photo_upload_demo as upload
from src.vision import photo_explanation as photo
from src.vision import exploratory_pilot_b1_v1 as pilot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--photo',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():
        raise FileExistsError('Preserve an existing verification report')
    model,layer=photo.load_v3_model(Path('models/vision_live_demo_v1/v3_best.pt'))
    raw=args.photo.read_bytes()
    kind='image/png' if args.photo.suffix.lower()=='.png' else 'image/jpeg'
    prepared=upload.prepare_local_upload(raw,kind)
    before={name:tensor.clone() for name,tensor in model.state_dict().items()}
    captured=[]
    hook=layer.register_forward_hook(lambda module,inputs,output:captured.append(output))
    try:
        values=torch.tensor(prepared.model_input.normalized_chw[None],requires_grad=True)
        logits=model(values);target=int(logits.argmax())
        features=captured[0]
        gradients=torch.autograd.grad(logits[0,target],features)[0]
        # Independent torch version of the channel-weighted positive CAM algebra.
        reference=(features*gradients.mean(dim=(2,3),keepdim=True)).sum(dim=1)[0].relu()
        reference=reference-reference.min()
        if reference.max()>torch.finfo(torch.float32).eps:
            reference=reference/reference.max()
        reference=reference.detach().numpy()
    finally:
        hook.remove()
    captured.clear()
    actual=pilot.gradcam(model,layer,prepared.model_input)
    from src.vision.model_pipeline import align_cam
    aligned_reference=align_cam(reference,prepared.model_input)
    error=float(np.max(np.abs(actual['cam']-aligned_reference)))
    assert error<3e-6,error
    assert actual['predicted_mgi_grade']==target+1
    assert np.allclose(actual['probabilities'],logits.detach().softmax(1).numpy()[0],atol=1e-7)
    assert not layer._forward_hooks
    assert all(parameter.grad is None for parameter in model.parameters())
    assert all(torch.equal(before[name],value) for name,value in model.state_dict().items())
    assert actual['original'].shape==actual['overlay'].shape==actual['heatmap'].shape
    peak=np.unravel_index(actual['cam'].argmax(),actual['cam'].shape)
    report={'status':'passed','checks':6,'source_sha256':sha256(raw).hexdigest(),
        'checkpoint_sha256':photo.V3_CHECKPOINT_SHA,'target_layer':'layer4[-1]',
        'feature_shape':list(features.shape),'predicted_and_explained_mgi':actual['predicted_mgi_grade'],
        'explanation_status':actual['explanation_status'],'independent_cam_max_abs_error':error,
        'peak_preview_yx':[int(x) for x in peak],'preview_hw':list(actual['cam'].shape),
        'weights_unchanged':True,'parameter_gradients_unset':True,'hooks_removed':True,
        'clinical_localisation_validated':False,'new_accuracy_estimate':False}
    prepared.close()
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
