"""Generated image checks: local decoding parity, cleanup, and CAM geometry."""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest

from src.vision import local_photo_upload_demo as upload
from src.vision import model_pipeline as cam
from src.vision import roi_ordinal_v2_live as live
from src.vision.roi_inference_v1 import _load_srgb_photo
from test_local_photo_upload_demo import generated_photo


def runtime():
    scope=SimpleNamespace(synthetic_only=False,status=lambda:{'ready':True,'upload_mode':'local_user_upload_demo'})
    return live.ROIV2PhotoRuntime(detector=object(),classifier=object(),device='cpu',fold=0,
        receipt={'zip_sha256':'a'*64},detector_sha256='b'*64,classifier_sha256='c'*64,
        photo_runtime=scope,checkpoint_temp=None)


@pytest.mark.parametrize('image_format,mode,icc,orientation',[
    ('JPEG','RGB',False,1),('JPEG','RGB',True,1),('JPEG','RGB',False,6),
    ('PNG','RGBA',False,1),('PNG','RGBA',True,1),('PNG','RGB',True,1)])
def test_v2_uses_exact_shared_validated_pixels_and_cleans_temporary_file(monkeypatch,image_format,mode,icc,orientation):
    raw=generated_photo(image_format=image_format,mode=mode,icc=icc,orientation=orientation)
    kind='image/jpeg' if image_format=='JPEG' else 'image/png'
    prepared=upload.prepare_local_upload(raw,kind)
    expected=np.asarray(prepared.srgb_image).copy();prepared.close()
    seen=[]
    def predict(detector,classifier,path,*,device):
        seen.append(Path(path))
        actual=_load_srgb_photo(path)
        np.testing.assert_array_equal(np.asarray(actual),expected)
        with Image.open(path) as saved:
            assert saved.format=='PNG' and not saved.info.get('icc_profile')
        return {'detections':[],'no_detection':True,'image_mgi_grade':None}
    monkeypatch.setattr(live,'predict_coral_tooth_rois',predict)
    monkeypatch.setattr(live,'_render_preview',lambda *_:'generated')
    result=runtime().predict_upload(raw,kind)
    assert result['input_format']==image_format and result['photo_saved'] is False
    assert result['image_mgi_grade'] is None and not seen[0].exists()
    # Existing opaque RGB path remains pixel-compatible with its original decoding.
    if mode=='RGB':
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            path=Path(directory)/('source.jpg' if image_format=='JPEG' else 'source.png')
            path.write_bytes(raw)
            np.testing.assert_array_equal(np.asarray(_load_srgb_photo(path)),expected)


def test_v2_temporary_photo_is_removed_when_inference_fails(monkeypatch):
    seen=[]
    def fail(*args,**kwargs):
        seen.append(Path(args[2]));raise RuntimeError('generated failure')
    monkeypatch.setattr(live,'predict_coral_tooth_rois',fail)
    with pytest.raises(RuntimeError,match='generated failure'):
        runtime().predict_upload(generated_photo(icc=False),'image/jpeg')
    assert seen and not seen[0].exists()


@pytest.mark.parametrize('size,orientation', [((400,200),1),((200,400),1),((400,200),6)])
def test_cam_non_square_upload_alignment_preserves_landmark(size,orientation):
    image=Image.new('RGB',size,(80,120,140));exif=Image.Exif();exif[274]=orientation
    stream=BytesIO();image.save(stream,format='JPEG',exif=exif)
    prepared=upload.prepare_local_upload(stream.getvalue(),'image/jpeg')
    try:
        view=prepared.model_input
        left,top,width,height=view.valid_box
        # Supply an asymmetric known spatial marker inside the unpadded input.
        values=np.zeros((224,224),dtype=np.float32)
        x=left+width//4;y=top+height*3//4;values[y,x]=1
        aligned=cam.align_cam(values,view)
        peak_y,peak_x=np.unravel_index(aligned.argmax(),aligned.shape)
        expected_x=((x-left+.5)/width)*aligned.shape[1]-.5
        expected_y=((y-top+.5)/height)*aligned.shape[0]-.5
        assert abs(peak_x-expected_x)<=2 and abs(peak_y-expected_y)<=2
        original=view.original_rgb.copy();rendered=cam.render_gradcam(original,aligned)
        np.testing.assert_array_equal(rendered['original'],original)
        assert rendered['overlay'].shape==original.shape
    finally:
        prepared.close()
