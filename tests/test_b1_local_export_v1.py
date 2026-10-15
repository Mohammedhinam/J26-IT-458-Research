"""Focused generated JPEG/NPY integration checks; no real sources opened."""
from copy import deepcopy
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from src.vision import b1_jpeg_source_v1 as source
from src.vision import b1_development_bundle_v1 as bundle
from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_streaming as streaming
from src.vision import colour_b1_iccv2_generated as v2
from src.vision import exploratory_bundle as legacy
from test_colour_b1_iccv2_generated import make_profile,pixels,scalar_reference


def jpeg(tmp_path, *, profile=None, orientation=1):
    raw=make_profile()[0] if profile is None else profile
    path=tmp_path/'generated.jpg'
    exif=Image.Exif();exif[274]=orientation;exif[306]='GENERATED_NOT_PRIVATE'
    Image.fromarray(pixels()).save(path,icc_profile=raw,exif=exif)
    return path


def test_generated_jpeg_header_checked_without_decoding_and_source_unchanged(tmp_path,monkeypatch):
    path=jpeg(tmp_path);before=legacy.sha256(path)
    def forbidden(*args,**kwargs):raise AssertionError('header decoded pixels')
    monkeypatch.setattr(Image.Image,'load',forbidden)
    with streaming._open(path) as handle:
        identity=source.identity(handle)
        image,profile=source.checked_header(handle,[16,16])
        assert source.identity(handle)==identity
        assert profile==make_profile()[0]
        # Do not close the caller-owned descriptor while checking headers.
        image.fp=None
        image.close()
    assert legacy.sha256(path)==before


@pytest.mark.parametrize('orientation',[2,3,6,8])
def test_nonidentity_orientation_rejected(tmp_path,orientation):
    path=jpeg(tmp_path,orientation=orientation)
    with streaming._open(path) as handle,pytest.raises(ValueError):
        source.checked_header(handle,[16,16])


def test_real_adapter_opt_in_decoder_integrity_and_pixels_only(tmp_path):
    path=jpeg(tmp_path);h=legacy.sha256(path)
    profile=make_profile()[0];ph=v2.sha256(profile).hexdigest()
    with source.decoded(path,h,[16,16],ph) as image:
        assert image.mode=='RGB'
        converted=source.Converter(profile).convert(np.asarray(image))[0]
        np.testing.assert_allclose(converted,v2.convert_generated(np.asarray(image),profile)[0],atol=2e-7)
    assert h==legacy.sha256(path)
    with pytest.raises(ValueError):
        with source.decoded(path,'0'*64,[16,16],ph):pass
    with pytest.raises(ValueError):
        with source.decoded(path,h,[16,16],'0'*64):pass


@pytest.mark.parametrize('shape',[(1,1),(3,8),(8,3),(16,16),(257,19)])
def test_optimized_model_view_matches_full_canonical_sampling(tmp_path,shape):
    width,height=shape
    rgb=np.random.default_rng(42).integers(0,256,(height,width,3),np.uint8)
    profile=make_profile()[0];converter=source.Converter(profile)
    values=converter.convert(rgb)[0]
    path=tmp_path/'full.npy'
    with streaming._open(path,write=True) as output:np.lib.format.write_array(output,values,version=(1,0),allow_pickle=False)
    with streaming._open(path) as handle:
        _,offset,identity=streaming._inspect(handle,values.shape)
        reference=streaming._model_view(handle,offset,width,height,identity)
    actual=source.model_view(Image.fromarray(rgb),converter)
    np.testing.assert_array_equal(actual,reference)


def test_generated_full_cam_and_model_equivalence_and_no_source_metadata(tmp_path):
    image=Image.fromarray(pixels());image.info['EXIF']='GENERATED'
    converter=source.Converter(make_profile()[0])
    path=tmp_path/'cam.npy';source.write_full_cam(image,converter,path)
    values=np.load(path,allow_pickle=False)
    np.testing.assert_array_equal(values,converter.convert(pixels())[0])
    assert values.min()<0 and values.max()>1
    assert b'EXIF' not in path.read_bytes() and b'ICC_PROFILE' not in path.read_bytes()


@pytest.mark.parametrize('bad',[np.nan,np.inf,-np.inf,-16.01,16.01])
def test_nonfinite_and_range_fail_closed(bad):
    with pytest.raises(ValueError):
        source.validate_values(np.full((1,1,3),bad,dtype='<f4'))


def test_new_converter_matches_independent_scalar_and_keeps_precision():
    profile,matrix,gamma=make_profile()
    values,xyz,measured=source.Converter(profile).convert(pixels(),precision=True)
    ref_xyz,ref_rgb=scalar_reference(pixels(),matrix,gamma)
    np.testing.assert_allclose(xyz,ref_xyz,atol=1e-12,rtol=0)
    np.testing.assert_array_equal(values,ref_rgb.astype('<f4'))
    assert measured['xyz_max_abs']<2e-6 and measured['lab_max_delta_e76']<.002


@pytest.mark.parametrize('fault',['test','np015','duplicate_group','review','grade0'])
def test_selection_preserves_held_group_and_test_rules(fault):
    from test_exploratory_bundle_b1 import generated_inputs
    draft,_=generated_inputs()
    row=draft['records'][0]
    if fault=='test':row['original_split']='Test'
    elif fault=='np015':row['source_record_id']=legacy.NP015_IDS[0]
    elif fault=='duplicate_group':row['content_group_id']=draft['records'][1]['content_group_id']
    elif fault=='review':row['cached_qa_requires_review']=True
    else:row['candidate_mgi_grade']=0
    with pytest.raises(ValueError):
        selected=legacy.select_candidates(draft)
        legacy.fixed_cohort(selected)


@pytest.mark.parametrize('change',['status','version','contract','count'])
def test_missing_stale_preflight_rejected(change):
    with pytest.raises(ValueError):
        bundle.require_preflight({}, {change:'wrong'})


@pytest.mark.parametrize('fault',['trailing','truncated','nan','float64','metadata_header'])
def test_model_npy_corruption_rejected_even_with_fresh_file_hash(tmp_path,fault):
    path=tmp_path/'model.npy';array=np.zeros((224,224,3),dtype='<f4')
    if fault=='nan':array[0,0,0]=np.nan
    if fault=='float64':array=array.astype(float)
    with path.open('wb') as handle:np.lib.format.write_array(handle,array,version=(1,0),allow_pickle=False)
    if fault=='trailing':path.write_bytes(path.read_bytes()+b'x')
    if fault=='truncated':path.write_bytes(path.read_bytes()[:-1])
    if fault=='metadata_header':
        raw=path.read_bytes();path.write_bytes(raw[:10]+b'!'+raw[11:])
    with pytest.raises(ValueError):bundle.model_array(path,legacy.sha256(path))


def test_symlink_and_duplicate_json_fields_fail_closed(tmp_path):
    path=tmp_path/'x.json';path.write_text('{"x":1,"x":2}')
    with pytest.raises(ValueError):bundle.load_json(path)
    link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises((ValueError,OSError)):bundle.load_json(link)


def test_new_contract_separate_from_old_guards():
    from src.vision import exploratory_bundle_v4 as old
    before=deepcopy(old.policy_spec()),b1.contract_hash()
    assert bundle.SCOPE!=old.SCOPE
    assert source.CONTRACT['xyz_limit']==2e-6 and source.CONTRACT['lab_limit']==.002
    assert source.CONTRACT['option_a_fallback'] is False
    source.Converter(make_profile()[0]).convert(pixels())
    assert before==(old.policy_spec(),b1.contract_hash())
    assert legacy.ROUNDTRIP_LIMIT==2


@pytest.fixture(scope='module')
def generated_package(tmp_path_factory):
    # Exact-count synthetic end-to-end integration. All source pixels, IDs,
    # provenance and authorizations here are explicit test doubles.
    from test_exploratory_bundle_b1 import generated_inputs
    from src.vision import exploratory_bundle_v4 as frozen
    draft,_=generated_inputs();rows=legacy.select_candidates(draft)
    scratch=tmp_path_factory.mktemp('b1_jpeg_generated').resolve()
    root=scratch/'sources';root.mkdir()
    profile=make_profile()[0]
    for index,row in enumerate(rows):
        rgb=pixels().copy()
        for bit in range(10):rgb[0,bit]=255 if (index>>bit)&1 else 0
        path=root/row['image_path'];path.parent.mkdir(parents=True,exist_ok=True)
        Image.fromarray(rgb).save(path,quality=100,subsampling=0,icc_profile=profile)
        row['source_sha256']=legacy.sha256(path);row['source_dimensions']=[16,16]
    plan={'version':'synthetic_test_only','source_draft_sha256':legacy.DRAFT_SHA,
          'cam_ids':list(legacy.CAM_IDS),'records':rows,
          'protected_groups':['SYN_PROTECTED_TEST'],'uncertain_groups':['SYN_NP015_Training','SYN_NP015_Validation']}
    patch=pytest.MonkeyPatch()
    patch.setattr(legacy,'CANDIDATE_IDENTITY_SHA',frozen._identity(rows))
    def scratch_output(path,category):
        assert Path(path).parent==scratch and category=='data/vision'
        return Path(path)
    patch.setattr(legacy,'new_ignored_output',scratch_output)
    try:
        evidence=bundle.preflight(plan,root)
        output=scratch/'synthetic_b1_complete'
        permission={'status':'owner_confirmed','scope':bundle.SCOPE,'authorizer':'SYNTHETIC_TEST_ONLY',
                    'date':'2026-10-15','evidence_reference':'generated unit-test double only',
                    'acknowledgements':{k:True for k in legacy.ACKS},'local_only':True,'maximum_attempts':1,
                    'cloud_authorized':False,'training_authorized':False,
                    **bundle.bindings(plan,evidence,output,'f'*64)}
        result=bundle.package(plan,root,evidence,output,permission,opt_in=True)
        yield {'result':result,'plan':plan,'evidence':evidence,'root':root,'permission':permission}
    finally:
        patch.undo()


def test_generated_complete733_and_three_cam_verification(generated_package):
    item=generated_package;result=item['result']
    verified=bundle.verify(result['directory'],result['manifest_sha256'])
    assert verified['records']==733 and verified['files']==737
    assert verified['model_arrays']==733 and verified['full_cam_arrays']==3
    assert len(item['evidence']['profile_qualification'])==1
    q=next(iter(item['evidence']['profile_qualification'].values()))
    assert q['codes_checked']==256**3


@pytest.mark.parametrize('fault',['version','status','contract','code','records','qualification'])
def test_actual_preflight_tampering_rejected(generated_package,fault):
    item=generated_package;evidence=deepcopy(item['evidence'])
    if fault in ('version','status'):evidence[fault]='bad'
    elif fault in ('contract','code'):evidence[fault+'_sha256']='0'*64
    elif fault=='records':evidence['records'].pop()
    else:next(iter(evidence['profile_qualification'].values()))['lcms_lab_delta_e76']=.0101
    with pytest.raises(ValueError):bundle.require_preflight(item['plan'],evidence)


@pytest.mark.parametrize('fault',['metadata','approved','schema','missing_record','held_count','qualification','stale_binding'])
def test_manifest_semantic_tampering_with_new_hash_rejected(generated_package,fault):
    root=Path(generated_package['result']['directory']);path=root/'bundle_manifest.json'
    original=path.read_bytes();value=json.loads(original)
    if fault=='metadata':value['records'][0]['EXIF']='forbidden'
    elif fault=='approved':value['qualified_labels_approved']=True
    elif fault=='schema':value['pilot_mgi_schema']=[0,1,2,3,4]
    elif fault=='missing_record':value['records'].pop()
    elif fault=='held_count':value['held_count']=180
    elif fault=='qualification':next(iter(value['profile_qualification'].values()))['xyz_max_abs']=2.01e-6
    else:value['bindings']['code_sha256']='0'*64
    try:
        path.write_text(json.dumps(value))
        with pytest.raises(ValueError):bundle.verify(root,legacy.sha256(path))
    finally:path.write_bytes(original)


def test_extra_files_and_empty_directories_rejected(generated_package):
    root=Path(generated_package['result']['directory'])
    trusted=generated_package['result']['manifest_sha256']
    extra=root/'extra';extra.mkdir()
    try:
        with pytest.raises(ValueError):bundle.verify(root,trusted)
    finally:extra.rmdir()
    extra.write_bytes(b'unapproved')
    try:
        with pytest.raises(ValueError):bundle.verify(root,trusted)
    finally:extra.unlink()


def test_consumed_output_cannot_retry(generated_package):
    item=generated_package
    with pytest.raises(ValueError):
        bundle.package(item['plan'],item['root'],item['evidence'],item['result']['directory'],item['permission'],opt_in=True)


def test_generated_archive_crc_membership_and_hashes(generated_package):
    result=generated_package['result']
    archive=bundle.publish_zip(result['directory'],result['manifest_sha256'])
    assert Path(archive['archive']).stat().st_size==archive['bytes']
    assert archive['sha256']==legacy.sha256(archive['archive'])
    from src.vision.exploratory_pilot_b1_v1 import extract_verified_zip
    extracted=Path(result['directory']).with_name('synthetic_verified_extraction')
    checked=extract_verified_zip(archive['archive'],extracted,archive['sha256'],result['manifest_sha256'])
    assert checked==result['verification']
    with pytest.raises(ValueError):bundle.publish_zip(result['directory'],result['manifest_sha256'])
