"""Synthetic-only study tests, never approval or clinical validation."""
import builtins
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms
import pytest

from src.vision import gamut_mapping_feasibility as study
from src.vision import colour_qa as qa
from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_bundle_v4 as v4


def lab(xyz):
    ratio = xyz / np.array([.9642, 1, .8249])
    d = 6 / 29
    f = np.where(ratio > d**3, np.cbrt(ratio), ratio / (3*d*d) + 4/29)
    return np.stack([116*f[..., 1]-16, 500*(f[..., 0]-f[..., 1]),
                     200*(f[..., 1]-f[..., 2])], axis=-1)


def decode_srgb(values):
    return np.where(values <= .04045, values/12.92, ((values+.055)/1.055)**2.4)


@pytest.mark.parametrize("name", study.CASES)
def test_fixed_fixtures_are_generated_and_byte_deterministic(name):
    a, b = study.make_fixture(name), study.make_fixture(name)
    assert a["provenance"] == "fixed_generated_only"
    assert a["image"].size == (100, 100) and a["image"].mode == "RGB"
    assert a["image"].tobytes() == b["image"].tobytes()
    assert a["image"].info == b["image"].info
    assert np.array_equal(a["matrix"], b["matrix"])


@pytest.mark.parametrize("value", ["data/Training/00004.jpg", "unknown", Path("data/forbidden"), None])
def test_public_runner_rejects_paths_and_unknown_data_inputs(value):
    with pytest.raises(ValueError, match="Unknown generated"):
        study.evaluate_fixture(value)


@pytest.mark.parametrize("name", ["identity", "interior", "shadows", "red_weak_1", "red_strong_1", "red_dense", "mixed"])
def test_generated_measurements_have_independent_matrix_trc_reference(name):
    fixture = study.make_fixture(name)
    source = fixture["image"]
    output = study._convert_intent(source, 1)
    measured = study._measure(source, output)
    original = np.asarray(source).astype(float)/255
    linear = decode_srgb(original) if fixture["gamma"] is None else original**fixture["gamma"]
    xyz = linear @ fixture["matrix"].T
    target = ImageCms.createProfile("sRGB")
    matrix = np.column_stack([getattr(target, k)[0] for k in ("red_colorant", "green_colorant", "blue_colorant")])
    expected = np.linalg.norm(lab(xyz) - lab(decode_srgb(np.asarray(output)/255) @ matrix.T), axis=2)
    # Numerical reference allowance from earlier generated qualification, not a
    # clinical tolerance or adjustment of any frozen image acceptance budget.
    assert measured["mean_delta_e"] == pytest.approx(expected.mean(), abs=.01)
    assert measured["max_delta_e"] == pytest.approx(expected.max(), abs=.01)
    target_linear = xyz @ np.linalg.inv(matrix).T
    extended = np.empty_like(target_linear)
    low = target_linear <= .0031308
    extended[low] = 12.92*target_linear[low]
    extended[~low] = 1.055*target_linear[~low]**(1/2.4)-.055
    excursion = np.maximum(-extended, 0) + np.maximum(extended-1, 0)
    assert measured["source_gamut_pixels"] == int((excursion > 1e-6).any(axis=2).sum())
    assert measured["source_max_excursion"] == pytest.approx(excursion.max(), abs=1e-6)


@pytest.mark.parametrize("name", ["red_strong_1", "red_dense", "mixed"])
def test_local_search_never_increases_per_pixel_lab_error_and_is_bounded(name):
    source = study.make_fixture(name)["image"]
    original = source.tobytes(), dict(source.info)
    baseline = study._convert_intent(source, 1)
    output = study._local_search(source, baseline)
    engine = qa._Transforms(source.info["icc_profile"])
    try:
        target = qa._finite_transform(engine, engine.source_lab, np.asarray(source), np.float64)
        before = np.linalg.norm(target - qa._finite_transform(engine, engine.output_lab, np.asarray(baseline), np.float64), axis=2)
        after = np.linalg.norm(target - qa._finite_transform(engine, engine.output_lab, np.asarray(output), np.float64), axis=2)
        extended = qa._finite_transform(engine, engine.extended_srgb, np.asarray(source)/255, np.float64)
    finally:
        engine.close()
    outside = ((extended < -1e-6) | (extended > 1+1e-6)).any(axis=2)
    assert np.all(after <= before + 1e-12)
    assert np.array_equal(np.asarray(output)[~outside], np.asarray(baseline)[~outside])
    assert output.mode == "RGB" and output.size == source.size and output.info == {"srgb": 1}
    assert np.asarray(output).dtype == np.uint8
    assert (source.tobytes(), source.info) == original


@pytest.mark.parametrize("name", ["red_strong_1", "red_strong_11"])
def test_bounded_mapping_cannot_launder_original_gamut_failures(name):
    rows = [r for r in study.evaluate_fixture(name)["methods"] if r["status"] == "measured"]
    keys = ("source_gamut_pixels", "source_gamut_fraction", "source_max_excursion")
    assert len({tuple(r[k] for k in keys) for r in rows}) == 1
    assert all(not r["frozen_colour_budget_pass"] for r in rows)
    assert all("gamut_excursion" in r["failed_numeric_checks"] for r in rows)
    assert all(not r["production_eligible"] and not r["export_authorized"] for r in rows)


def test_study_is_reproducible():
    assert json.dumps(study.run_study(), sort_keys=True) == json.dumps(study.run_study(), sort_keys=True)


def test_invalid_and_wrong_profile_negative_controls_fail():
    result = study.negative_controls()
    assert len(result["invalid_profiles"]) == 3
    assert set(result["invalid_profiles"].values()) == {"rejected_before_measurement"}
    assert not result["wrong_profile"]["frozen_colour_budget_pass"]
    assert not result["wrong_profile"]["production_eligible"]


def test_unsupported_intent_is_reported_without_fallback(monkeypatch):
    original = ImageCms.isIntentSupported
    monkeypatch.setattr(ImageCms, "isIntentSupported", lambda p, i, d: 0 if i == 2 else original(p, i, d))
    rows = study.evaluate_fixture("interior")["methods"]
    row = next(r for r in rows if r["method"] == "saturation")
    assert row["status"] == "unsupported" and "qa" not in row
    assert next(r for r in rows if r["method"] == "relative")["status"] == "measured"


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nonfinite_colour_measurement_stops(monkeypatch, bad):
    run = qa._Transforms.run
    def invalid(self, handle, values, dtype):
        result = run(self, handle, values, dtype)
        if dtype == np.float64:
            result[0, 0, 0] = bad
        return result
    monkeypatch.setattr(qa._Transforms, "run", invalid)
    with pytest.raises(ValueError):
        study.evaluate_fixture("interior")


def test_complete_study_never_reads_files_opens_images_exports_or_authorizes(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Study attempted forbidden IO or production action")
    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", forbidden)
        patch.setattr(Path, "open", forbidden)
        patch.setattr(Image, "open", forbidden)
        patch.setattr(Image.Image, "save", forbidden)
        patch.setattr(legacy, "authorise", forbidden)
        patch.setattr(legacy, "package_development", forbidden)
        patch.setattr(v4, "package_development", forbidden)
        result = study.run_study()
    assert not result["production_active"] and not result["real_data_accessed"]
    assert len(result["fixtures"]) == 10


def test_production_configuration_and_source_bytes_remain_unchanged():
    directory = Path(study.__file__).parent
    names = ("exploratory_bundle.py", "exploratory_bundle_v4.py", "colour_qa.py",
             "colour_policy.py", "model_pipeline.py", "train_pipeline.py")
    before = {name: sha256((directory/name).read_bytes()).hexdigest() for name in names}
    policy_before = v4.policy_spec()
    study.evaluate_fixture("red_strong_1")
    assert before == {name: sha256((directory/name).read_bytes()).hexdigest() for name in names}
    assert v4.policy_spec() == policy_before
    assert legacy.ROUNDTRIP_LIMIT == 2
    assert v4.SCOPE == "package_development_option_a_v4"
