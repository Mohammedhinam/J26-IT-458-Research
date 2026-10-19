"""Generated-photo checks for the pinned candidate; no study image or training."""
from hashlib import sha256
from io import BytesIO

import numpy as np
from PIL import Image
import pytest
import torch

from src.vision import efficientnet_live as efficient
from src.vision.local_photo_upload_demo import prepare_local_upload
from test_local_photo_upload_demo import generated_photo


def test_tampered_checkpoint_rejected_before_deserialization(tmp_path,monkeypatch):
    path=tmp_path/'bad.pt';path.write_bytes(b'generated-not-weights')
    def forbidden(*args,**kwargs):
        raise AssertionError('Deserialization must not happen before the SHA check')
    monkeypatch.setattr(torch,'load',forbidden)
    with pytest.raises(ValueError,match='SHA mismatch'):
        efficient.load_runtime(path)


@pytest.mark.parametrize('key,value',[
    ('fold',1),('arm','head_only'),('grades',[0,1,2,3]),('bindings',{})])
def test_wrong_provenance_rejected_before_network_loading(tmp_path,monkeypatch,key,value):
    state={'version':'training680-matched-efficientnet-adaptation-v1',
           'grades':[1,2,3,4],'fold':0,'arm':'last_block',
           'bindings':efficient.EXPECTED_BINDINGS,'model':{}}
    state[key]=value;path=tmp_path/'generated.pt';torch.save(state,path)
    monkeypatch.setattr(efficient,'CHECKPOINT_SHA',sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError,match='schema|provenance'):
        efficient.load_runtime(path)


@pytest.fixture(scope='module')
def runtime():
    torch.set_num_threads(2)
    return efficient.load_runtime()


@pytest.mark.parametrize('image_format,mode,icc,orientation',[
    ('JPEG','RGB',False,1),('JPEG','RGB',True,6),('PNG','RGBA',True,1)])
def test_real_checkpoint_generated_photo_cam_matches_logits_and_preserves_state(runtime,image_format,mode,icc,orientation):
    payload=generated_photo(image_format=image_format,mode=mode,icc=icc,orientation=orientation)
    kind='image/jpeg' if image_format=='JPEG' else 'image/png'
    prepared=prepare_local_upload(payload,kind)
    before={key:value.clone() for key,value in runtime.model.state_dict().items()}
    try:
        with torch.inference_mode():
            inference=runtime.model(torch.tensor(prepared.model_input.normalized_chw[None])).softmax(1).numpy()[0]
        # Gradient-enabled kernels can differ slightly in float32 accumulation.
        # Check ordinary inference within the shared 1e-6 probability tolerance,
        # and compare CAM against an independent gradient-enabled forward too.
        values=torch.tensor(prepared.model_input.normalized_chw[None],requires_grad=True)
        expected=runtime.model(values).softmax(1).detach().numpy()[0]
        hooks=len(runtime.cam_layer._forward_hooks)
        result=runtime.explain_upload(payload,kind)
        np.testing.assert_allclose(result['probabilities'],expected,atol=1e-7,rtol=0)
        np.testing.assert_allclose(result['probabilities'],inference,atol=1e-6,rtol=0)
        assert result['predicted_grade']==result['explained_grade']==int(expected.argmax())+1
        assert result['mgi_grades']==[1,2,3,4] and result['fold']==0
        assert result['proposal_role']=='main_candidate' and result['photo_saved'] is False
        assert result['cam_target_layer']=='features.8' and runtime.cam_layer is runtime.model.features[-1]
        assert len(runtime.cam_layer._forward_hooks)==hooks
        import base64
        for name,data in result['views_png_base64'].items():
            with Image.open(BytesIO(base64.b64decode(data))) as view:
                assert view.size==prepared.model_input.original_rgb.shape[1::-1]
                if name=='original':
                    np.testing.assert_array_equal(np.asarray(view),prepared.model_input.original_rgb)
        assert all(torch.equal(value,runtime.model.state_dict()[key]) for key,value in before.items())
        assert not any(module.training for module in runtime.model.modules())
    finally:
        prepared.close()
