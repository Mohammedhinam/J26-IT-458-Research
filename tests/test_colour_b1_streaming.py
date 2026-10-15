"""New generated-only full-resolution tests; no repeat of prior backend suite."""
from hashlib import sha256
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_streaming as full


def convert(tmp_path, width=513, height=259, **kwargs):
    source = full.GeneratedSource(width, height, **kwargs)
    result = full.convert_generated_full(source, tmp_path / "generated")
    return source, result


def read_array(path):
    # Only tiny generated test arrays. Production never loads a full NPY array.
    return np.load(path, allow_pickle=False)


@pytest.mark.parametrize("profile", ["srgb", "gamma18", "wide_red"])
@pytest.mark.parametrize("pattern", ["primaries", "shadows", "ramp", "mixed"])
def test_streamed_small_data_matches_frozen_converter_and_geometry(tmp_path, profile, pattern):
    source, result = convert(tmp_path, 31, 17, profile_kind=profile, pattern=pattern)
    original = source.pixels(0, 31*17).reshape(17, 31, 3)
    expected, _ = b1.convert_generated(original, source.profile())
    np.testing.assert_array_equal(read_array(tmp_path / "generated/full_rgb.npy"), expected)
    verified = full.verify_generated_outputs(result["directory"], result["receipt_sha256"])
    model, box = b1.letterbox(expected)
    np.testing.assert_array_equal(model, verified["model_rgb"])
    np.testing.assert_array_equal(b1.normalize(model), verified["normalized_chw"])
    assert box == result["receipt"]["valid_box"]
    assert sha256(original.tobytes()).hexdigest() == result["receipt"]["source_rgb_sha256"]
    assert result["receipt"]["numeric"]["peak_chunk_pixels"] <= 65536


def test_large_generated_geometry_independent_scalar_and_unclipped_reference(tmp_path):
    source, result = convert(tmp_path, 513, 259, pattern="primaries")
    data = read_array(Path(result["directory"]) / "full_rgb.npy")
    # Independent scalar reference already qualified in v1; importing helper
    # definitions does not collect/rerun its77 tests or execute a backend model.
    from test_colour_b1_prototype import scalar_reference
    from src.vision.gamut_mapping_feasibility import _generated_profile
    _, matrix = _generated_profile(2.2, 2**-6)
    indices = np.array([0, 6, 511, 512, 513, 60001, 513*259-1])
    pixels = np.array([source.pixels(int(i), 1)[0] for i in indices], dtype=np.uint8).reshape(1, -1, 3)
    expected = scalar_reference(pixels, matrix, 2.2).astype("<f4")[0]
    np.testing.assert_array_equal(data.reshape(-1, 3)[indices], expected)
    assert data.min() < 0 and data.max() > 1
    verified = full.verify_generated_outputs(result["directory"], result["receipt_sha256"])
    assert verified["model_rgb"].min() < 0 and verified["model_rgb"].max() > 1
    # Independent large-image pixel sampling, not the old size-limited resizer.
    left, top, w, h = result["receipt"]["valid_box"]
    row, col = 23, 101
    x = max(0., min((col+.5)*source.width/w-.5, source.width-1))
    y = max(0., min((row+.5)*source.height/h-.5, source.height-1))
    x0, y0 = int(x), int(y)
    x1, y1 = min(x0+1, source.width-1), min(y0+1, source.height-1)
    upper = data[y0, x0].astype(float)*(1-(x-x0)) + data[y0, x1].astype(float)*(x-x0)
    lower = data[y1, x0].astype(float)*(1-(x-x0)) + data[y1, x1].astype(float)*(x-x0)
    expected_pixel = (upper*(1-(y-y0)) + lower*(y-y0)).astype("<f4")
    np.testing.assert_array_equal(verified["model_rgb"][top+row, left+col], expected_pixel)


def test_deterministic_bytes_hashes_and_source_independent_of_chunk_size(tmp_path):
    source = full.GeneratedSource(517, 263)
    a = full.convert_generated_full(source, tmp_path / "a", tile_pixels=4096)
    b = full.convert_generated_full(source, tmp_path / "b", tile_pixels=65536)
    for name in ("full_rgb.npy", "model_rgb.npy"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    assert a["receipt"]["source_rgb_sha256"] == b["receipt"]["source_rgb_sha256"]
    assert a["receipt"]["files"] == b["receipt"]["files"]
    assert {p.name for p in (tmp_path / "a").iterdir()} == full.FILES


@pytest.mark.parametrize("size", [(0, 2), (True, 2), (16385, 1), (10000, 10000), (1.5, 2)])
def test_prospective_dimension_and_payload_caps(size):
    with pytest.raises(ValueError):full.GeneratedSource(*size)


@pytest.mark.parametrize("value", ["data/Training/00004.jpg", None, Path("forbidden"), {}])
def test_no_source_path_or_callback_accepted(tmp_path, value):
    with pytest.raises(ValueError):full.convert_generated_full(value, tmp_path / "forbidden")
    assert not (tmp_path / "forbidden").exists()


@pytest.mark.parametrize("tile", [0, 255, 257, 65537, True])
def test_invalid_tile_limit_fails_before_output(tmp_path, tile):
    with pytest.raises(ValueError):full.convert_generated_full(full.GeneratedSource(7, 4), tmp_path / "bad", tile_pixels=tile)
    assert not (tmp_path / "bad").exists()


def test_original_sources_and_metadata_not_copied(tmp_path):
    source = full.GeneratedSource(300, 270)
    before = source.pixels(0, 65536).tobytes(), source.profile()
    result = full.convert_generated_full(source, tmp_path / "clean")
    assert before == (source.pixels(0, 65536).tobytes(), source.profile())
    receipt = (tmp_path / "clean/receipt.json").read_bytes()
    assert before[1] not in receipt
    assert set(json.loads(receipt)) == {"version", "scope", "base_contract_sha256", "contract_sha256",
        "generated_source", "source_rgb_sha256", "profile_sha256", "numeric", "files", "valid_box"}
    assert result["receipt"]["scope"] == "generated_only_not_production"


@pytest.mark.parametrize("problem", ["flip", "trailing", "truncated", "nonfinite", "range", "float64",
    "fortran", "big_endian", "header_extra", "stale_contract", "metadata", "wrong_model", "extra_file", "symlink"])
def test_tamper_corruption_schema_and_privacy_fail_closed(tmp_path, problem):
    source, result = convert(tmp_path, 19, 13)
    directory = Path(result["directory"])
    path = directory / "full_rgb.npy"
    receipt = result["receipt"]
    if problem in {"stale_contract", "metadata"}:
        if problem == "stale_contract":receipt["contract_sha256"] = "0"*64
        else:receipt["EXIF"] = "forbidden"
    elif problem == "extra_file":(directory / "unexpected.txt").write_text("extra")
    elif problem == "symlink":
        target = tmp_path / "copy.npy";target.write_bytes(path.read_bytes());path.unlink();path.symlink_to(target)
    elif problem == "wrong_model":
        small = directory / "model_rgb.npy"
        current = read_array(small);current[0, 0] = .5
        np.save(small, current, allow_pickle=False)
        # Even self-consistent forged file evidence cannot change canonical geometry.
        with full._open(small) as stream:receipt["files"]["model_rgb.npy"], _, _ = full._inspect(stream, (224,224,3))
    else:
        data = path.read_bytes()
        if problem == "flip":data = data[:-1] + bytes([data[-1] ^ 1])
        elif problem == "trailing":data += b"extra"
        elif problem == "truncated":data = data[:-1]
        elif problem == "header_extra":
            length = int.from_bytes(data[8:10], "little")
            header = b"{'descr': '<f4', 'fortran_order': False, 'shape': (13, 19, 3), 'EXIF': 0}"
            header += b" "*((-(10+len(header)+1))%16) + b"\n"
            data = data[:8] + len(header).to_bytes(2,"little") + header + data[10+length:]
        else:
            array = read_array(path)
            if problem == "nonfinite":array[0,0,0] = np.nan
            elif problem == "range":array[0,0,0] = 16.01
            elif problem == "float64":array = array.astype(float)
            elif problem == "fortran":array = np.asfortranarray(array)
            elif problem == "big_endian":array = array.astype(">f4")
            stream = io.BytesIO();np.lib.format.write_array(stream,array,version=(1,0));data = stream.getvalue()
        path.write_bytes(data)
        # Rebinding external digest still cannot bypass intrinsic shape/finite rules.
        receipt["files"]["full_rgb.npy"]["sha256"] = sha256(data).hexdigest()
        receipt["files"]["full_rgb.npy"]["bytes"] = len(data)
    (directory / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises((ValueError, OSError)):
        full.verify_generated_outputs(directory, b1.digest_json(receipt))


def test_no_overwrite_and_failure_leaves_no_success_receipt(tmp_path, monkeypatch):
    source, result = convert(tmp_path, 19, 13)
    before = (tmp_path / "generated/full_rgb.npy").read_bytes()
    with pytest.raises(FileExistsError):full.convert_generated_full(source, result["directory"])
    assert (tmp_path / "generated/full_rgb.npy").read_bytes() == before
    monkeypatch.setattr(full.GeneratedSource, "profile", lambda self: b"invalid")
    with pytest.raises(ValueError):full.convert_generated_full(source, tmp_path / "failed")
    assert not (tmp_path / "failed/receipt.json").exists()


@pytest.mark.parametrize("problem", ["nonfinite", "precision"])
def test_new_conversion_rejects_actual_transform_failures(tmp_path, monkeypatch, problem):
    if problem == "precision":
        original = b1.encode_extended
        monkeypatch.setattr(b1,"encode_extended",lambda values: original(values)+.1)
    else:
        original = b1.convert_generated
        def invalid(*args):
            values,evidence = original(*args);values[0,0,0] = np.inf;return values,evidence
        monkeypatch.setattr(b1,"convert_generated",invalid)
    with pytest.raises(ValueError):full.convert_generated_full(full.GeneratedSource(19,13),tmp_path / "failed")
    assert not (tmp_path / "failed/receipt.json").exists()


def test_no_decoder_full_array_load_or_production_call(tmp_path, monkeypatch):
    from src.vision import exploratory_bundle_v4 as v4
    def forbidden(*args, **kwargs):pytest.fail("Streaming path attempted forbidden operation")
    monkeypatch.setattr(Image,"open",forbidden)
    monkeypatch.setattr(Image.Image,"save",forbidden)
    monkeypatch.setattr(np,"load",forbidden)
    monkeypatch.setattr(np,"memmap",forbidden)
    monkeypatch.setattr(v4,"package_development",forbidden)
    result = full.convert_generated_full(full.GeneratedSource(513,259),tmp_path / "generated")
    assert full.verify_generated_outputs(result["directory"],result["receipt_sha256"])["normalized_chw"].shape == (3,224,224)


def test_production_and_frozen_b1_bytes_and_policy_stay_unchanged(tmp_path):
    from src.vision import exploratory_bundle as legacy
    from src.vision import exploratory_bundle_v4 as v4
    directory=Path(full.__file__).parent
    names=["colour_b1_prototype.py","model_pipeline.py","train_pipeline.py","colour_policy.py",
           "colour_qa.py","exploratory_bundle.py","exploratory_bundle_v4.py"]
    before={name:sha256((directory/name).read_bytes()).hexdigest() for name in names}
    policy=v4.policy_spec()
    full.convert_generated_full(full.GeneratedSource(19,13),tmp_path / "generated")
    assert before == {name:sha256((directory/name).read_bytes()).hexdigest() for name in names}
    assert policy == v4.policy_spec() and legacy.ROUNDTRIP_LIMIT == 2


@pytest.mark.parametrize("problem", ["duplicate_json", "numeric_metadata", "numeric_negative", "numeric_limit",
                                    "source_extra", "source_type", "profile_hash"])
def test_nested_receipt_schema_and_unsupported_claims_rejected(tmp_path, problem):
    _, result = convert(tmp_path,19,13)
    receipt=result["receipt"]
    if problem == "duplicate_json":
        raw=json.dumps(receipt)
        raw='{"scope":"hidden-metadata",'+raw[1:]
        (Path(result["directory"])/"receipt.json").write_text(raw)
    else:
        if problem == "numeric_metadata":receipt["numeric"]["EXIF"]="forbidden"
        elif problem == "numeric_negative":receipt["numeric"]["xyz_max_abs"]=-1
        elif problem == "numeric_limit":receipt["numeric"]["lab_max_delta_e76"]=.003
        elif problem == "source_extra":receipt["generated_source"]["path"]="forbidden"
        elif problem == "source_type":receipt["generated_source"]["pattern"]=[]
        elif problem == "profile_hash":receipt["profile_sha256"]="0"*64
        (Path(result["directory"])/"receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError):full.verify_generated_outputs(result["directory"],b1.digest_json(receipt))


@pytest.mark.parametrize("which", ["full_rgb.npy", "model_rgb.npy"])
def test_identity_bound_between_hash_scan_and_sampling(tmp_path,monkeypatch,which):
    _,result=convert(tmp_path,19,13)
    original=full._inspect
    def race(stream,shape):
        answer=original(stream,shape)
        is_target=(which=="full_rgb.npy" and shape==(13,19,3)) or (which=="model_rgb.npy" and shape==(224,224,3))
        if is_target:
            path=Path(result["directory"])/which
            with path.open("r+b") as output:
                output.seek(-4,2);output.write(np.float32(.25).tobytes())
        return answer
    monkeypatch.setattr(full,"_inspect",race)
    with pytest.raises(ValueError,match="changed"):
        full.verify_generated_outputs(result["directory"],result["receipt_sha256"])
