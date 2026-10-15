"""Generated RGB/metadata only. Fixture authorisations never approve dental data."""
from copy import deepcopy
import json
from pathlib import Path
import stat
import zipfile

import numpy as np
from PIL import Image, PngImagePlugin
import pytest

from src.vision import exploratory_bundle as eb


def draft_fixture():
    rows = []
    for i,(split,grade) in enumerate([("Training",1),("Training",4),("Validation",1),("Validation",2)],1):
        rows.append({"source_record_id":f"{split}/{i:05}", "image_path":f"Dataset/{split}/Images/{i:05}.jpg",
                     "original_split":split, "technical_candidate":True,
                     "qualified_label_approved":False,"training_eligible":False,"mgi_grade":None,
                     "participant_id":None,"analysis_split":None,"content_group_id":f"synthetic-{i}",
                     "group_source_member_count":1,"group_original_split_presence":[split],
                     "candidate_mgi_grade":grade,"cached_qa_requires_review":False,
                     "cached_qa_issues":[],"cached_original_issues":[],"draft_exclusion_reasons":[],
                     "candidate_label_status":"strict_technically_consistent_unapproved",
                     "proposed_analysis_split":split})
    return {"status":"draft_not_approved","activated":False,"training_ready":False,"mgi_schema":[0,1,2,3,4],
            "policy":{"optional_upper_partial_policy_activated":False},
            "approval":{k:False for k in ['labels_approved','split_approved','duplicate_review_complete','participant_independence_verified']},
            "sealed_boundary":{"protected_test_content_group_ids":["sealed"],"unresolved_NP015_group_ids":["possible"]},"records":rows}


def authorization(scope, **bindings):
    # Synthetic ownership fixture; no qualified approval or participant identity.
    return {"scope":scope,"status":"owner_confirmed","authorizer":"synthetic fixture",
            "date":"synthetic","evidence_reference":"generated test only",
            "acknowledgements":{k:True for k in eb.ACKS},**bindings}


@pytest.fixture
def plan(tmp_path):
    records=eb.select_candidates(draft_fixture())
    for i,row in enumerate(records):
        path=tmp_path/'sources'/row['image_path'];path.parent.mkdir(parents=True,exist_ok=True)
        Image.new('RGB',(8,4),(40+i*40,10+i*20,90)).save(path)
        row.update(source_sha256=eb.sha256(path),source_dimensions=[8,4])
    return {"source_draft_sha256":"synthetic-draft","records":records,"protected_groups":["sealed"],
            "uncertain_groups":["possible"],"cam_ids":["Validation/00003"]}


@pytest.fixture
def package(tmp_path,plan,monkeypatch):
    monkeypatch.setattr(eb,'new_ignored_output',lambda p,category:Path(p))
    auth=authorization('package_development',source_draft_sha256=plan['source_draft_sha256'],source_plan_sha256=eb.json_digest(plan),
                       code_sha256=eb.json_digest(eb.source_code_hashes()),bundle_id='bundle')
    result=eb.package_development(plan,tmp_path/'sources',tmp_path/'bundle',auth,True)
    return tmp_path/'bundle',result


def test_select_preserves_provisional_source_and_final_fields():
    draft=draft_fixture();before=deepcopy(draft)
    candidates=eb.select_candidates(draft)
    assert len(candidates)==4 and draft==before
    candidates[0]['candidate_mgi_grade']=3
    assert draft==before and all(r['participant_id'] is None for r in candidates)


@pytest.mark.parametrize('change', ['test','cross_group','protected','np015','multi','review','historical','policy','approved','bool_grade','duplicate'])
def test_invalid_or_leaking_manifest_is_rejected(change):
    draft=draft_fixture();r=draft['records'][0]
    if change=='test':r['original_split']='Test'
    elif change=='cross_group':draft['records'][2]['content_group_id']=r['content_group_id']
    elif change=='protected':r['content_group_id']='sealed'
    elif change=='np015':r['content_group_id']='possible'
    elif change=='multi':r['group_source_member_count']=2
    elif change=='review':r['cached_qa_requires_review']=True
    elif change=='historical':r['original_cached_status']='needs_review'
    elif change=='policy':draft['policy']['optional_upper_partial_policy_activated']=True
    elif change=='approved':draft['approval']['labels_approved']=True
    elif change=='bool_grade':r['candidate_mgi_grade']=True
    elif change=='duplicate':draft['records'].append(deepcopy(r))
    with pytest.raises(ValueError):eb.select_candidates(draft)


def test_held_records_are_never_selected_or_silently_cleared():
    draft=draft_fixture();draft['records'][0].update(technical_candidate=False,draft_exclusion_reasons=['NP015 unresolved'])
    assert len(eb.select_candidates(draft))==3
    assert draft['records'][0]['draft_exclusion_reasons']==['NP015 unresolved']


@pytest.mark.parametrize('name',['/absolute.jpg','../escape.jpg','Test/a.jpg','TEST/a.jpg','images\\a.jpg','a/./b.jpg','C:/a.jpg'])
def test_paths_reject_test_traversal_and_noncanonical_names(name):
    with pytest.raises(ValueError):eb.relative_path(name)


def test_path_symlink_is_rejected_without_reading_target(tmp_path):
    (tmp_path/'secret').write_text('do not read')
    (tmp_path/'link').symlink_to(tmp_path/'secret')
    with pytest.raises(ValueError,match='Symlink'):eb.safe_file(tmp_path,'link')


def test_cache_projects_only_development_hash_fields(tmp_path,monkeypatch):
    entries=[{'split':'Training','image_path':'Dataset/Training/Images/00001.jpg','sha256':'a'*64,'width':8,'height':4,'mgi_max':'DO_NOT_DECODE'},
             {'split':'Test','image_path':'DO_NOT_DECODE','sha256':'DO_NOT_DECODE','width':10,'mgi_max':'DO_NOT_DECODE'}]
    path=tmp_path/'cache.json';path.write_text(json.dumps({'result':{'manifest':entries}},indent=2)+'\n')
    original=json.loads
    def guard(value):
        assert 'DO_NOT_DECODE' not in value
        return original(value)
    monkeypatch.setattr(eb.json,'loads',guard)
    found=eb.read_hash_inventory(path)
    assert list(found)==['Dataset/Training/Images/00001.jpg'] and 'mgi_max' not in next(iter(found.values()))


def test_dry_run_hashes_sources_without_decoding_or_packaging(tmp_path,plan,monkeypatch):
    monkeypatch.setattr(Image,'open',lambda *a,**k:pytest.fail('dry-run decoded an image'))
    result=eb.dry_run(plan,tmp_path/'sources')
    assert result['source_hashes_verified']==4 and result['images_decoded']==result['images_packaged']==0
    assert result['notice']==eb.NOTICE and not result['real_packaging_authorised']


def test_corrupt_source_is_rejected(tmp_path,plan):
    (tmp_path/'sources'/plan['records'][0]['image_path']).write_bytes(b'changed')
    with pytest.raises(ValueError,match='Source hash mismatch'):eb.dry_run(plan,tmp_path/'sources')


def test_packaging_requires_separate_scope_before_image_access(tmp_path,plan,monkeypatch):
    monkeypatch.setattr(Image,'open',lambda *a,**k:pytest.fail('unauthorised image open'))
    with pytest.raises(ValueError,match='opt-in'):eb.package_development(plan,tmp_path/'sources',tmp_path/'out',None)
    with pytest.raises(ValueError,match='scope'):eb.package_development(plan,tmp_path/'sources',tmp_path/'out',authorization('implement_only'),True)
    assert not (tmp_path/'out').exists()


def test_derivative_preserves_existing_preprocessing_and_rgb():
    image=Image.fromarray(np.arange(301*203*3,dtype=np.uint8).reshape(203,301,3))
    before=np.asarray(image).copy();small=eb.resized_rgb(image)
    assert small.mode=='RGB' and max(small.size)==224
    assert np.array_equal(eb.vp.preprocess_rgb(image).normalized_chw,eb.vp.preprocess_rgb(small).normalized_chw)
    assert np.array_equal(np.asarray(image),before)


def test_synthetic_package_is_allowlisted_and_provisional(package):
    root,result=package;bundle,records=eb.validate_bundle(root)
    assert len(records)==4 and len(bundle['files'])==5 and all(r['label_status']=='provisional' for r in records)
    assert bundle['notice']==eb.NOTICE and not bundle['qualified_labels_approved']
    with zipfile.ZipFile(result['archive']) as z:
        assert set(z.namelist())==set(bundle['files'])|{'bundle_manifest.json'}
        assert not any('Test' in name or name.endswith('.txt') for name in z.namelist())


@pytest.mark.parametrize('change',['extra','corrupt','empty_test_dir'])
def test_bundle_rejects_extra_corrupted_or_test_contents(package,change):
    root,_=package
    if change=='extra':(root/'extra.jpg').write_bytes(b'bad')
    elif change=='empty_test_dir':(root/'Test').mkdir()
    else:(root/'images/Training/00001.png').write_bytes(b'bad')
    with pytest.raises(ValueError):eb.validate_bundle(root)


def test_authorised_synthetic_extraction_roundtrip(package,tmp_path):
    root,result=package;auth=authorization('run_exploratory',archive_sha256=result['archive_sha256'],bundle_manifest_sha256=result['bundle_manifest_sha256'])
    dest=eb.extract_bundle(result['archive'],tmp_path/'unpacked',auth,True)
    assert eb.validate_bundle(dest)[0]==eb.validate_bundle(root)[0]


@pytest.mark.parametrize('name,symlink',[('../escape',False),('Test/secret.jpg',False),('payload.png',True)])
def test_zip_traversal_test_and_links_blocked_before_extraction(tmp_path,name,symlink):
    archive=tmp_path/'malicious.zip'
    with zipfile.ZipFile(archive,'w') as z:
        entry=zipfile.ZipInfo(name)
        if symlink:entry.external_attr=(stat.S_IFLNK|0o777)<<16
        z.writestr(entry,b'bad')
    auth=authorization('run_exploratory',archive_sha256=eb.sha256(archive))
    with pytest.raises(ValueError):eb.extract_bundle(archive,tmp_path/'out',auth,True)
    assert not (tmp_path/'out').exists()


def test_frozen_draft_checksum_precedes_source_access(tmp_path):
    draft=tmp_path/'draft.json';draft.write_text('{}')
    with pytest.raises(ValueError,match='checksum'):eb.prepare_plan(draft,tmp_path/'missing-cache')


def test_local_output_must_be_new_and_ignored(tmp_path):
    with pytest.raises(ValueError,match='ignored'):eb.new_ignored_output(tmp_path/'outside','data')


def test_lossless_export_strips_private_metadata_preserves_decoded_source(tmp_path):
    # All metadata and pixels here are generated; these are not patient records.
    source=tmp_path/'generated.jpg'
    exif=Image.Exif();exif[274]=1;exif[306]='synthetic_timestamp'
    exif[34853]={0:b'\x02\x03\x00\x00'}
    exif[34665]={37500:b'synthetic_opaque_makernote',40961:1}
    image=Image.fromarray(np.arange(31*17*3,dtype=np.uint8).reshape(17,31,3))
    image.save(source,exif=exif,comment=b'synthetic_comment',xmp=b'synthetic_xmp')
    source_bytes=source.read_bytes(); source_sha=eb.sha256(source)
    with Image.open(source) as decoded:
        pixels=np.asarray(decoded).copy(); dimensions=decoded.size
        payload=eb.export_rgb_png(decoded,tmp_path/'clean.png')
        assert decoded.getexif().get(306)=='synthetic_timestamp'
    with Image.open(tmp_path/'clean.png') as clean:
        assert clean.size==dimensions and clean.mode=='RGB'
        assert np.array_equal(np.asarray(clean),pixels)
        assert clean.info=={'srgb':1} and not clean.getexif()
    assert source.read_bytes()==source_bytes and eb.sha256(source)==source_sha
    assert payload['sha256']!=source_sha and payload['dimensions']==list(dimensions)


def test_resized_export_preserves_frozen_tensor_and_no_inherited_info(tmp_path):
    image=Image.fromarray(np.arange(301*203*3,dtype=np.uint8).reshape(203,301,3))
    exif=Image.Exif();exif[306]='synthetic_only'
    image.info.update(exif=exif.tobytes(),xmp=b'opaque',comment=b'opaque',private_blob=b'opaque')
    before=deepcopy(image.info)
    result=eb.export_rgb_png(eb.resized_rgb(image),tmp_path/'small.png')
    with Image.open(tmp_path/'small.png') as small:
        assert np.array_equal(eb.vp.preprocess_rgb(image).normalized_chw,eb.vp.preprocess_rgb(small).normalized_chw)
        assert small.info=={'srgb':1} and result['dimensions']==list(small.size)
    assert image.info==before


@pytest.mark.parametrize('orientation',range(2,9))
def test_orientation_is_not_silently_rotated_or_stripped(tmp_path,orientation):
    image=Image.new('RGB',(31,17));exif=Image.Exif();exif[274]=orientation
    image.info['exif']=exif.tobytes()
    with pytest.raises(ValueError,match='orientation'):eb.export_rgb_png(image,tmp_path/'out.png')
    assert not (tmp_path/'out.png').exists() and image.getexif()[274]==orientation


@pytest.mark.parametrize('colour_tag',['icc_profile','gamma','chromaticity','non_sRGB_exif'])
def test_colour_profile_requires_review_instead_of_silent_recolour(tmp_path,colour_tag):
    image=Image.new('RGB',(31,17),(100,130,180));before=np.asarray(image).copy()
    if colour_tag=='non_sRGB_exif':
        exif=Image.Exif();exif[34665]={40961:65535};image.info['exif']=exif.tobytes()
    else:image.info[colour_tag]=b'synthetic_profile_only'
    with pytest.raises(ValueError,match='colour'):eb.export_rgb_png(image,tmp_path/'out.png')
    assert not (tmp_path/'out.png').exists() and np.array_equal(np.asarray(image),before)


def test_package_records_separate_source_export_and_pixel_hashes(package,tmp_path,plan):
    root,_=package;bundle,rows=eb.validate_bundle(root)
    assert bundle['version']==eb.BUNDLE_VERSION and bundle['dataset_attribution']==eb.DATASET_ATTRIBUTION
    for row in rows:
        source=tmp_path/'sources'/row['original_image_path']
        assert eb.sha256(source)==row['source_sha256']
        assert row['image_payload_sha256']==bundle['files'][row['image_path']]
    cam=next(r for r in rows if 'cam_original_path' in r)
    assert cam['cam_original_path'].endswith('.png') and cam['cam_payload_sha256']!=cam['source_sha256']
    assert cam['cam_rgb_sha256']==cam['source_rgb_sha256'] and cam['cam_dimensions']==[8,4]
    with Image.open(tmp_path/'sources'/cam['original_image_path']) as source,Image.open(root/cam['cam_original_path']) as copied:
        assert np.array_equal(np.asarray(source),np.asarray(copied))
    assert all(eb.sha256(tmp_path/'sources'/r['image_path'])==r['source_sha256'] for r in plan['records'])


@pytest.mark.parametrize('metadata',['exif','xmp','opaque_chunk'])
def test_metadata_injection_rejected_even_with_updated_byte_hash(package,metadata):
    root,_=package;bundle,_=eb.validate_bundle(root);row=bundle['records'][0];path=root/row['image_path']
    with Image.open(path) as image:clean=image.copy()
    kwargs={};info=PngImagePlugin.PngInfo();info.add(b'sRGB',b'\x01')
    if metadata=='exif':
        exif=Image.Exif();exif[306]='synthetic';kwargs['exif']=exif
    elif metadata=='xmp':info.add_text('XML:com.adobe.xmp','synthetic')
    else:info.add(b'vpAg',b'synthetic_opaque')
    clean.save(path,pnginfo=info,**kwargs)
    row['image_payload_sha256']=bundle['files'][row['image_path']]=eb.sha256(path)
    (root/'bundle_manifest.json').write_text(json.dumps(bundle))
    with pytest.raises(ValueError,match='chunk'):eb.validate_bundle(root)


@pytest.mark.parametrize('change',['pixels','geometry','trailing','crc'])
def test_unsafe_pixel_or_geometry_output_fails_closed(package,change):
    root,_=package;bundle,_=eb.validate_bundle(root);row=bundle['records'][0];path=root/row['image_path']
    with Image.open(path) as image:clean=image.copy()
    metadata=PngImagePlugin.PngInfo();metadata.add(b'sRGB',b'\x01')
    if change=='pixels':clean.putpixel((0,0),(255,0,255));clean.save(path,pnginfo=metadata)
    elif change=='geometry':clean.resize((31,17)).save(path,pnginfo=metadata)
    elif change=='trailing':path.write_bytes(path.read_bytes()+b'synthetic_extra')
    else:
        data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
    row['image_payload_sha256']=bundle['files'][row['image_path']]=eb.sha256(path)
    (root/'bundle_manifest.json').write_text(json.dumps(bundle))
    with pytest.raises(ValueError):eb.validate_bundle(root)


@pytest.mark.parametrize('change',['legacy','attribution','payload_hash','cam_source_hash','cam_geometry','np015'])
def test_required_safety_schema_attribution_and_hash_bindings(package,change):
    root,_=package;bundle,_=eb.validate_bundle(root)
    cam=next(r for r in bundle['records'] if 'cam_original_path' in r)
    if change=='legacy':bundle['version']='pp1-exploratory-bundle-v1'
    elif change=='attribution':bundle['dataset_attribution']['licence_url']='invalid'
    elif change=='payload_hash':bundle['records'][0]['image_payload_sha256']='a'*64
    elif change=='cam_source_hash':cam['cam_payload_sha256']=cam['source_sha256']
    elif change=='cam_geometry':cam['cam_dimensions']=[4,8]
    else:bundle['records'][0]['source_record_id']='Training/00591'
    with pytest.raises(ValueError):eb.bundle_records(bundle)


@pytest.mark.parametrize('change',['test','held','np015_id','protected','cross_group'])
def test_source_plan_cannot_package_held_test_np015_or_overlapping_groups(tmp_path,plan,monkeypatch,change):
    row=plan['records'][0]
    if change=='test':row['original_split']='Test'
    elif change=='held':row.update(technical_candidate=False,draft_exclusion_reasons=['held'])
    elif change=='np015_id':row.update(source_record_id='Training/00591',image_path='Dataset/Training/Images/00591.jpg')
    elif change=='protected':row['content_group_id']='sealed'
    else:plan['records'][2]['content_group_id']=row['content_group_id']
    monkeypatch.setattr(eb,'new_ignored_output',lambda p,category:Path(p))
    monkeypatch.setattr(Image,'open',lambda *a,**k:pytest.fail('unsafe plan reached image export'))
    auth=authorization('package_development',source_draft_sha256=plan['source_draft_sha256'],source_plan_sha256=eb.json_digest(plan),
                       code_sha256=eb.json_digest(eb.source_code_hashes()),bundle_id='out')
    with pytest.raises(ValueError):eb.package_development(plan,tmp_path/'sources',tmp_path/'out',auth,True)
    assert not (tmp_path/'out').exists()


def test_profile_blocker_is_detected_before_any_package_files(tmp_path,plan,monkeypatch):
    path=tmp_path/'sources'/plan['records'][-1]['image_path']
    Image.new('RGB',(8,4)).save(path,icc_profile=b'synthetic_ICC')
    plan['records'][-1]['source_sha256']=eb.sha256(path)
    monkeypatch.setattr(eb,'new_ignored_output',lambda p,category:Path(p))
    auth=authorization('package_development',source_draft_sha256=plan['source_draft_sha256'],source_plan_sha256=eb.json_digest(plan),
                       code_sha256=eb.json_digest(eb.source_code_hashes()),bundle_id='out')
    with pytest.raises(ValueError,match='ICC'):eb.package_development(plan,tmp_path/'sources',tmp_path/'out',auth,True)
    assert not (tmp_path/'out').exists() and not (tmp_path/'out.zip').exists()


def test_icc_package_uses_managed_cam_hash_and_convert_before_resize(tmp_path,plan,monkeypatch):
    from io import BytesIO
    from PIL import ImageCms
    from test_icc_colour_export import generated_profile
    profile=generated_profile(1.8)
    row=next(r for r in plan['records'] if r['source_record_id'] in plan['cam_ids'])
    source=tmp_path/'sources'/row['image_path']
    Image.new('RGB',(8,4),(40,90,130)).save(source,icc_profile=profile)
    row['source_sha256']=eb.sha256(source);before=source.read_bytes()
    with Image.open(source) as image:
        expected=ImageCms.profileToProfile(image,ImageCms.ImageCmsProfile(BytesIO(profile)),
                    ImageCms.createProfile('sRGB'),renderingIntent=1,outputMode='RGB',flags=0)
    monkeypatch.setattr(eb,'new_ignored_output',lambda p,category:Path(p))
    auth=authorization('package_development',source_draft_sha256=plan['source_draft_sha256'],source_plan_sha256=eb.json_digest(plan),
                       code_sha256=eb.json_digest(eb.source_code_hashes()),bundle_id='out')
    eb.package_development(plan,tmp_path/'sources',tmp_path/'out',auth,True)
    bundle,rows=eb.validate_bundle(tmp_path/'out');cam=next(r for r in rows if 'cam_original_path' in r)
    assert cam['colour_conversion']=='icc_to_srgb'
    assert cam['source_rgb_sha256']!=cam['colour_managed_rgb_sha256']==cam['cam_rgb_sha256']
    with Image.open(tmp_path/'out'/cam['cam_original_path']) as full,Image.open(tmp_path/'out'/cam['image_path']) as small:
        assert full.tobytes()==expected.tobytes() and full.size==(8,4)
        assert np.array_equal(eb.vp.preprocess_rgb(expected).normalized_chw,eb.vp.preprocess_rgb(small).normalized_chw)
    assert source.read_bytes()==before
    cam['colour_managed_rgb_sha256']=cam['source_rgb_sha256']
    with pytest.raises(ValueError,match='provenance'):eb.bundle_records({**bundle,'records':rows})
