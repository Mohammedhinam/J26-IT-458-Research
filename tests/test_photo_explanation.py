"""Generated-only photo adapter tests; no checkpoint or dental dataset access."""
import base64
from hashlib import sha256
import io

import numpy as np
from PIL import Image
import pytest

from test_colour_b1_iccv2_generated import make_profile
from src.vision import photo_explanation as photo


def generated_jpeg(orientation=1, profile=True, format='JPEG'):
    icc = make_profile()[0]
    pixels = np.zeros((24, 40, 3), np.uint8)
    pixels[:, :20] = [240, 15, 5]
    pixels[:, 20:] = [15, 220, 60]
    out = io.BytesIO()
    exif = Image.Exif(); exif[274] = orientation; exif[306] = 'generated only'
    Image.fromarray(pixels).save(out, format=format, icc_profile=icc if profile else None, exif=exif)
    return out.getvalue(), sha256(icc).hexdigest()


def test_shared_preprocessing_extended_values_geometry_and_private_metadata():
    raw, profile = generated_jpeg()
    before = sha256(raw).hexdigest()
    prepared = photo.prepare_jpeg(raw, profile)
    with Image.open(io.BytesIO(raw)) as image:
        expected = photo.source.model_view(image, photo.source.Converter(image.info['icc_profile']))
    np.testing.assert_array_equal(prepared.normalized_chw, photo.b1.normalize(expected))
    assert expected.min() < 0 and expected.max() > 1
    assert prepared.original_rgb.shape == (24, 40, 3)
    assert prepared.normalized_chw.shape == (3, 224, 224)
    preview = Image.open(io.BytesIO(base64.b64decode(photo._png(prepared.original_rgb))))
    assert not preview.info and not preview.getexif()
    assert sha256(raw).hexdigest() == before
    np.testing.assert_array_equal(prepared.normalized_chw, photo.prepare_jpeg(raw, profile).normalized_chw)


@pytest.mark.parametrize('variant', ['missing_profile','wrong_profile','orientation','png','empty','malformed'])
def test_unsupported_inputs_fail_closed(variant):
    raw, profile = generated_jpeg(orientation=6 if variant=='orientation' else 1,
                                  profile=variant!='missing_profile', format='PNG' if variant=='png' else 'JPEG')
    if variant=='wrong_profile': profile='0'*64
    if variant=='empty': raw=b''
    if variant=='malformed': raw=b'not an image'
    with pytest.raises((ValueError, OSError)):
        photo.prepare_jpeg(raw,profile)


def test_registry_checked_before_any_decode_and_copied(monkeypatch):
    raw, profile = generated_jpeg()
    registry={sha256(raw).hexdigest():'generated'}
    runtime=photo.PhotoRuntime(None,None,'1'*64,registry,profile,True)
    registry.clear()
    assert runtime.status()['ready']
    monkeypatch.setattr(photo,'prepare_jpeg',lambda *_:pytest.fail('Unregistered image decoded'))
    with pytest.raises(ValueError,match='registry'): runtime.explain(raw+b'changed')
    with pytest.raises(ValueError,match='provenance'):
        photo.PhotoRuntime(None,None,'1'*64,{'2'*64:'owner_supplied_nonstudy'},profile,True)


def test_checkpoint_hash_before_deserialization(tmp_path,monkeypatch):
    path=tmp_path/'generated.pt'; path.write_bytes(b'not trusted')
    monkeypatch.setattr(photo.pilot.models,'_torch',lambda:pytest.fail('Untrusted checkpoint loaded'))
    with pytest.raises(ValueError,match='SHA'): photo.load_v3_runtime(path,{'1'*64:'owner_supplied_nonstudy'})


@pytest.mark.parametrize('fault',['probability','grade','shape','original','status'])
def test_output_contract_rejects_corruption(fault):
    raw,profile=generated_jpeg(); prepared=photo.prepare_jpeg(raw,profile)
    result={name:prepared.original_rgb.copy() for name in ('original','heatmap','overlay')}
    result.update(probabilities=[.1,.2,.3,.4],predicted_mgi_grade=4,explanation_status='ok')
    if fault=='probability': result['probabilities']=[0,0,0,float('nan')]
    if fault=='grade': result['predicted_mgi_grade']=0
    if fault=='shape': result['heatmap']=result['heatmap'][:1]
    if fault=='original': result['original'][0,0]=[0,0,0]
    if fault=='status': result['explanation_status']='clinical_validated'
    with pytest.raises(ValueError): photo._checked_result(result,prepared,'1'*64,True)


@pytest.mark.parametrize('device',['cpu','mps'])
def test_resnet50_generated_photo_forward_gradcam_no_updates_or_hooks(device):
    import torch
    torch.set_num_threads(2); torch.manual_seed(42)
    if device=='mps' and not torch.backends.mps.is_available():
        pytest.skip('MPS unavailable; CPU remains required')
    network=photo.pilot.make_model(pretrained=False)
    model,layer=network['model'].to(device),network['cam_layer']
    for p in model.parameters(): p.requires_grad_(False)
    before={key:value.clone() for key,value in model.state_dict().items()}
    hooks=len(layer._forward_hooks)
    raw,profile=generated_jpeg()
    runtime=photo.PhotoRuntime(model,layer,'1'*64,{sha256(raw).hexdigest():'generated'},profile,True)
    result=runtime.explain(raw)
    assert result['mgi_grades']==[1,2,3,4] and result['synthetic_only']
    assert result['predicted_grade']==result['explained_grade']
    assert len(layer._forward_hooks)==hooks
    for key,value in model.state_dict().items(): assert torch.equal(value,before[key])
    for value in result['views_png_base64'].values():
        with Image.open(io.BytesIO(base64.b64decode(value))) as view:
            assert view.size==(40,24) and view.mode=='RGB' and not view.info
