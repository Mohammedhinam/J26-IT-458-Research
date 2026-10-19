"""Generated JPEG bytes only: no dental data, profiles or external packages."""
import builtins
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms
from PIL.TiffImagePlugin import IFDRational
import pytest

from src.vision import jpeg_metadata_qualification as j
from test_colour_b1_iccv2_generated import make_profile


RECORD = dict(image_id='Training/SYN001', filename='SYN001.jpg',
              original_split='Training', caption_filename='SYN001.jpg',
              annotation_filename='SYN001.txt', review_status='pending')
XMP = (j.XMP + b'<x:xmpmeta xmlns:x="adobe:ns:meta/" '
       b'xmlns:dc="http://purl.org/dc/elements/1.1/" '
       b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
       b'<rdf:RDF><rdf:Description dc:creator="SYNTHETIC-PRIVATE"/>'
       b'</rdf:RDF></x:xmpmeta>')


def fixture(quality=92, subsampling=0, orientation=1, progressive=False):
    # Shadows, saturated regions and random detail exercise decoder equality.
    rgb = np.random.default_rng(42).integers(0, 256, (43, 61, 3), dtype=np.uint8)
    rgb[:8] = np.arange(61, dtype=np.uint8)[None, :, None]
    rgb[8:16] = [255, 0, 0]
    profile = make_profile()[0]
    exif = Image.Exif()
    exif[274] = orientation
    exif[306] = '2026:01:01 00:00:00'
    exif[34665] = {36867: '2026:01:01 00:00:00', 37500: b'SYNTHETIC-MAKER'}
    exif[34853] = {0: b'\x02\x03\x00\x00', 1: 'N',
                   2: (IFDRational(6, 1), IFDRational(12, 1), IFDRational(30, 1)),
                   3: 'E',
                   4: (IFDRational(79, 1), IFDRational(51, 1), IFDRational(0, 1))}
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, 'JPEG', quality=quality, subsampling=subsampling,
                             progressive=progressive, icc_profile=profile, exif=exif)
    raw = buf.getvalue()
    raw = raw[:2] + j.segment(0xE1, XMP) + j.segment(0xFE, b'SYNTHETIC-COMMENT') + raw[2:]
    return raw, profile


def clean(raw, profile, record=RECORD):
    return j.strip_generated(raw, j.digest(raw), {j.digest(profile)}, record)


def rewrite(raw, mutate):
    headers, scan, _ = j.parts(raw)
    return b'\xff\xd8' + b''.join(j.segment(m, p) for m, p in mutate(headers)) + scan


@pytest.mark.parametrize('quality,subsampling', [(55,0), (92,0), (98,2)])
def test_pixels_profile_colour_and_source_integrity(quality, subsampling, tmp_path):
    raw, profile = fixture(quality, subsampling)
    source = tmp_path / 'source' / RECORD['filename']
    source.parent.mkdir(); source.write_bytes(raw)
    initial = j.digest(source.read_bytes())
    generated_source = Image.open(io.BytesIO(raw))
    assert generated_source.getexif().get(306) is not None
    assert generated_source.getexif().get_ifd(34665).get(37500) == b'SYNTHETIC-MAKER'
    gps = generated_source.getexif().get_ifd(34853)
    assert 2 in gps and 4 in gps
    output, receipt = clean(raw, profile)
    a = Image.open(io.BytesIO(raw)); b = Image.open(io.BytesIO(output))
    assert np.array_equal(np.asarray(a), np.asarray(b))
    assert a.size == b.size == (61,43)
    assert b.info['icc_profile'] == profile
    assert not b.getexif()
    assert all(s not in output for s in (b'SYNTHETIC-PRIVATE', b'SYNTHETIC-MAKER', b'SYNTHETIC-COMMENT', b'Exif\0\0', j.XMP))
    # Independent CMS execution: colour-managed Lab interpretation unchanged.
    lab = ImageCms.createProfile('LAB')
    original_lab = ImageCms.profileToProfile(a, ImageCms.ImageCmsProfile(io.BytesIO(profile)), lab, outputMode='LAB')
    output_lab = ImageCms.profileToProfile(b, ImageCms.ImageCmsProfile(io.BytesIO(profile)), lab, outputMode='LAB')
    assert np.array_equal(np.asarray(original_lab), np.asarray(output_lab))
    assert source.read_bytes() == raw and j.digest(source.read_bytes()) == initial
    assert receipt['source_sha256'] == initial
    assert receipt['output_sha256'] == j.digest(output) != initial
    assert receipt['image_id'] == RECORD['image_id']
    assert not receipt['real_data_authorized'] and not receipt['upload_authorized']


def test_no_encoder_or_dataset_access(monkeypatch):
    raw, profile = fixture()
    real_open = builtins.open
    root = Path(__file__).resolve().parents[1]
    def guarded_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)):
            resolved = Path(path).resolve()
            if resolved.is_relative_to(root/'data') or resolved.is_relative_to(root/'models'):
                pytest.fail('Real dataset/model read attempted')
        return real_open(path, *args, **kwargs)
    monkeypatch.setattr(builtins, 'open', guarded_open)
    monkeypatch.setattr(Image.Image, 'save', lambda *a, **k: pytest.fail('JPEG re-encoding attempted'))
    output, _ = clean(raw, profile)
    assert clean(raw, profile)[0] == output
    assert clean(output, profile)[0] == output


@pytest.mark.parametrize('field,value', [('original_split','Test'),('filename','../SYN001.jpg'),
    ('caption_filename','OTHER.jpg'),('annotation_filename','OTHER.txt'),
    ('image_id','Validation/SYN001'),('review_status','approved')])
def test_annotation_binding_failures(field,value):
    raw, profile = fixture()
    with pytest.raises(ValueError): clean(raw, profile, {**RECORD, field:value})


@pytest.mark.parametrize('orientation', [2,3,6,8])
def test_orientation_fail_closed(orientation):
    raw, profile = fixture(orientation=orientation)
    with pytest.raises(ValueError, match='orientation'): clean(raw, profile)


def test_progressive_rejected():
    raw, profile = fixture(progressive=True)
    with pytest.raises(ValueError): clean(raw, profile)


@pytest.mark.parametrize('suffix', [b'PRIVATE', b'\xff\xd9', b'\xff\xe1\x00\x02'])
def test_trailing_data_rejected(suffix):
    raw, profile = fixture()
    with pytest.raises(ValueError): clean(raw+suffix, profile)


def test_source_hash_binding_and_unknown_icc():
    raw, profile = fixture()
    with pytest.raises(ValueError, match='SHA'):
        j.strip_generated(raw, '0'*64, {j.digest(profile)}, RECORD)
    with pytest.raises(ValueError, match='allowlisted'):
        j.strip_generated(raw, j.digest(raw), set(), RECORD)


@pytest.mark.parametrize('marker,payload', [(0xED,b'opaque'), (0xE1,b'unknown'),
    (0xE2,b'MPF\0'),(0xEE,b'Adobe-invalid'),
    (0xE1,j.XMP+b'<bad/>'),(0xE1,j.XMP+b'<!DOCTYPE x><x/>'),
    (0xE1,j.XMP+b'<x'),(0xE0,b'JFXX\0unknown')])
def test_unknown_rendering_metadata_rejected(marker,payload):
    raw, profile = fixture()
    raw = raw[:2]+j.segment(marker,payload)+raw[2:]
    with pytest.raises(ValueError): clean(raw, profile)


def test_multipart_icc_and_missing_duplicate_chunks():
    raw, profile = fixture()
    pieces = [profile[:100], profile[100:]]
    def chunks(h):
        return [(m,p) for m,p in h if m!=0xE2]+[(0xE2,j.ICC+bytes([i+1,2])+p) for i,p in enumerate(pieces)]
    multipart = rewrite(raw,chunks)
    assert clean(multipart,profile)[1]['ICC_sha256']==j.digest(profile)
    for mutate in (lambda h:[(m,p) for m,p in chunks(h) if not(m==0xE2 and p[12]==2)],
                   lambda h:chunks(h)+[(0xE2,j.ICC+b'\x01\x02'+pieces[0])]):
        with pytest.raises(ValueError): clean(rewrite(raw,mutate),profile)


def test_malformed_allowlisted_profile_rejected():
    raw, _ = fixture()
    bad = b'not-a-valid-profile'
    raw = rewrite(raw,lambda h:[(m,p) for m,p in h if m!=0xE2]+[(0xE2,j.ICC+b'\x01\x01'+bad)])
    with pytest.raises(ValueError, match='Malformed'): clean(raw,bad)


@pytest.mark.parametrize('mode', ['metadata','coding','ICC','density','scan'])
def test_post_sanitisation_tampering(mode):
    raw, profile = fixture(); output,_=clean(raw,profile)
    def mutate(h):
        result=[]
        for m,p in h:
            if (mode=='coding' and m==0xDB) or (mode=='ICC' and m==0xE2):
                p=p[:-1]+bytes([p[-1]^1])
            if mode=='density' and m==0xE0: p=p[:9]+b'\x00\x02'+p[11:]
            result.append((m,p))
        return result
    changed = rewrite(output,mutate)
    if mode=='metadata': changed=changed[:2]+j.segment(0xFE,b'private')+changed[2:]
    if mode=='scan': changed=changed[:-10]+bytes([changed[-10]^1])+changed[-9:]
    with pytest.raises(ValueError): j.verify_generated_pair(raw,changed,j.digest(raw),{j.digest(profile)},RECORD)


def test_thumbnail_removed_without_display_geometry_change():
    raw,profile=fixture()
    raw=rewrite(raw,lambda h:[(m,p[:12]+b'\x01\x01'+b'\xff\0\0') if m==0xE0 else(m,p) for m,p in h])
    output,receipt=clean(raw,profile)
    assert 'JFIF_thumbnail' in receipt['removed_containers']
    assert all(len(p)==14 for m,p in j.parts(output)[0] if m==0xE0)
