"""Option A generated-only qualification; no clinical or packaging approvals."""
from copy import deepcopy
from decimal import Decimal
import math
import struct

import numpy as np
from PIL import Image, ImageCms
import pytest

from src.vision import colour_policy as policy
from src.vision import colour_qa as qa
from src.vision import exploratory_bundle as export
from test_colour_qa import profile_fixture, pillow_reference, analytic_lab_distance


def synthetic_evidence(report):
    # These unit-test markers are not genuine human/dataset approval records.
    return {"qa_sha256": policy.measurement_digest(report),
            "checks": {name: {"passed": True, "reference": "generated-test-only:" + name}
                       for name in policy.PREREQUISITES}}


@pytest.fixture
def report():
    return qa.diagnose_forward_colour(Image.new("RGB", (100, 100), (128, 128, 128)))


def evaluate(report):
    return policy.evaluate_option_a(report, synthetic_evidence(report))


def set_distribution(report, criterion, value):
    """Summaries of explicitly known toy distributions, not clinical pixels."""
    n = report["pixels"]
    if criterion == "mean_delta_e":
        minimum = mean = maximum = value  # All N values equal value.
        bounds = {q: [value, value] for q in ("50", "90", "95", "99", "99.9")}
    elif criterion == "tail_delta_e":
        # 9989 samples of .2 and 11 of value: rank 9990 lands in the tail.
        minimum, maximum = .2, value
        mean = .2 + 11 * (value - .2) / n
        bounds = {q: [.2, .2] for q in ("50", "90", "95", "99")}
        bounds["99.9"] = [math.floor(value * 1000) / 1000, value]
    else:
        minimum, maximum = .2, value  # Only one outlier; P99.9 stays at .2.
        mean = .2 + (value - .2) / n
        bounds = {q: [.2, .2] for q in ("50", "90", "95", "99", "99.9")}
    report["forward_delta_e76_D50"].update(
        min=minimum, mean=mean, max=maximum, percentile_bounds=bounds)


def set_gamut(report, count, excursion):
    n = report["pixels"]
    report["gamut"].update(pixels_outside=count, percentage_outside=100 * count / n,
        pixels_below=count, pixels_above=0, raw_pixels_outside_zero_epsilon=max(count, int(excursion > 0)),
        channel_counts=[count, 0, 0], max_excursion_per_channel_normalized=[excursion, 0, 0],
        max_excursion_normalized=excursion, mean_excursion_all_channel_samples=excursion * max(count, 1) / (3 * n))


@pytest.mark.parametrize("criterion,limit", [("mean_delta_e", .49), ("tail_delta_e", .99), ("max_delta_e", 1.99)])
@pytest.mark.parametrize("direction", [-1, 0, 1])
def test_exact_forward_boundaries_and_one_failure(report, criterion, limit, direction):
    value = limit if direction == 0 else math.nextafter(limit, -math.inf if direction < 0 else math.inf)
    set_distribution(report, criterion, value)
    result = evaluate(report)
    # Independent decimal arithmetic of the documented expression.
    nominal = {"mean_delta_e": ".50", "tail_delta_e": "1.00", "max_delta_e": "2.00"}[criterion]
    expected = Decimal(str(value)) + Decimal(".01") <= Decimal(nominal)
    assert result["isolated_policy_pass"] is expected
    assert result["failed_checks"] == ([] if expected else [criterion])


def test_tail_uses_enclosing_upper_not_lower_or_midpoint(report):
    set_distribution(report, "tail_delta_e", .9905)
    report["forward_delta_e76_D50"]["percentile_bounds"]["99.9"] = [.9895, .9905]
    assert evaluate(report)["failed_checks"] == ["tail_delta_e"]


@pytest.mark.parametrize("n", [999, 1000, 1001, 10000])
@pytest.mark.parametrize("excess", [0, 1])
def test_integer_gamut_extent_and_fraction_equivalence(report, n, excess):
    report["pixels"] = report["forward_delta_e76_D50"]["count"] = n
    report["dimensions"] = [n, 1]
    c = n // 1000 + excess
    set_gamut(report, c, .001 if c else 0)
    result = evaluate(report)
    # Integer arithmetic cannot hide a single excess pixel behind % rounding.
    expected = Decimal(c) / Decimal(n) <= Decimal(".001")
    assert result["checks"]["gamut_count"] is expected
    assert result["checks"]["gamut_fraction"] is expected
    assert result["failed_checks"] == ([] if expected else ["gamut_count", "gamut_fraction"])


@pytest.mark.parametrize("direction", [-1, 0, 1])
def test_exact_excursion_boundary_and_severity_only_failure(report, direction):
    limit = 2 / 255
    value = limit if direction == 0 else math.nextafter(limit, -math.inf if direction < 0 else math.inf)
    set_gamut(report, 1, value)
    result = evaluate(report)
    assert result["failed_checks"] == (["gamut_excursion"] if direction > 0 else [])


@pytest.mark.parametrize("direction", [-1, 0, 1])
def test_gamut_reporting_epsilon_is_not_zero_loss_rule(report, direction):
    value = 1e-6 if direction == 0 else math.nextafter(1e-6, -math.inf if direction < 0 else math.inf)
    set_gamut(report, int(value > 1e-6), value)
    assert evaluate(report)["isolated_policy_pass"]


@pytest.mark.parametrize("name", policy.PREREQUISITES)
def test_each_mandatory_prerequisite_is_required(report, name):
    evidence = synthetic_evidence(report)
    evidence["checks"][name]["passed"] = False
    assert policy.evaluate_option_a(report, evidence)["failed_checks"] == ["prerequisites"]


@pytest.mark.parametrize("change", ["missing", "empty_reference", "truthy_string", "stale_binding", "no_evidence"])
def test_missing_or_unbound_evidence_never_defaults_to_pass(report, change):
    evidence = synthetic_evidence(report)
    if change == "missing": del evidence["checks"]["source_hash_verified"]
    elif change == "empty_reference": evidence["checks"]["source_hash_verified"]["reference"] = " "
    elif change == "truthy_string": evidence["checks"]["source_hash_verified"]["passed"] = "True"
    elif change == "stale_binding": evidence["qa_sha256"] = "0" * 64
    else: evidence = None
    assert policy.evaluate_option_a(report, evidence)["failed_checks"] == ["prerequisites"]


@pytest.mark.parametrize("where", ["mean", "tail", "excursion", "reverse"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nonfinite_input_rejects_without_partial_pass(report, where, value):
    if where == "mean": report["forward_delta_e76_D50"]["mean"] = value
    elif where == "tail": report["forward_delta_e76_D50"]["percentile_bounds"]["99.9"][1] = value
    elif where == "excursion": report["gamut"]["max_excursion_normalized"] = value
    else: report["reverse_rgb"]["per_pixel_max"]["mean"] = value
    result = policy.evaluate_option_a(report)
    assert not result["isolated_policy_pass"] and not any(result["checks"].values())


@pytest.mark.parametrize("change", ["partial", "geometry", "boolean_count", "fraction", "severity", "settings", "missing_tail"])
def test_inconsistent_or_incomplete_measurements_fail_closed(report, change):
    if change == "partial": report["forward_delta_e76_D50"]["count"] -= 1
    elif change == "geometry": report["dimensions"][0] += 1
    elif change == "boolean_count": report["gamut"]["pixels_outside"] = False
    elif change == "fraction": report["gamut"]["percentage_outside"] = .001
    elif change == "severity": report["gamut"]["max_excursion_normalized"] = .01
    elif change == "settings": report["settings"]["flags"] = 256
    else: del report["forward_delta_e76_D50"]["percentile_bounds"]["99.9"]
    assert not policy.evaluate_option_a(report)["checks"]["measurements_valid"]


def sparse_profile_fixture(strength, spots=1):
    """New gamut grid, pinned to binary powers/fixed ICC precision, not real data."""
    raw, matrix, gamma = profile_fixture(1)
    data = bytearray(raw)
    expansion = np.array([[1 + strength, -strength, 0], [-strength, 1 + strength, 0], [0, 0, 1]])
    matrix = np.rint((matrix @ expansion) * 65536) / 65536
    for i in range(int.from_bytes(data[128:132], "big")):
        entry = data[132 + 12 * i:144 + 12 * i]
        if entry[:4] in (b"rXYZ", b"gXYZ", b"bXYZ"):
            column = (b"rXYZ", b"gXYZ", b"bXYZ").index(entry[:4])
            offset = int.from_bytes(entry[4:8], "big")
            data[offset + 8:offset + 20] = struct.pack(">3i", *np.rint(matrix[:, column] * 65536).astype(int))
    pixels = np.full((100, 100, 3), 128, dtype=np.uint8)
    pixels.reshape(-1, 3)[:spots] = [0, 255, 0]
    source = Image.fromarray(pixels)
    source.info["icc_profile"] = bytes(data)
    return source, matrix, gamma


def independent_gamut(source, matrix, gamma):
    # Analytic inverse encoding, independent of colour_qa and its C API.
    # Read the generated destination's functional coefficients, not its
    # serialised fixed-point approximation. No CMS transform supplies answers.
    target = ImageCms.createProfile("sRGB")
    destination_matrix = np.column_stack([getattr(target, name)[0]
        for name in ("red_colorant", "green_colorant", "blue_colorant")])
    linear = ((np.asarray(source) / 255) ** gamma) @ matrix.T @ np.linalg.inv(destination_matrix).T
    rgb = np.empty_like(linear)
    low = linear <= .0031308
    rgb[low] = 12.92 * linear[low]
    rgb[~low] = 1.055 * linear[~low] ** (1 / 2.4) - .055
    excursion = np.maximum(-rgb, 0) + np.maximum(rgb - 1, 0)
    return int((excursion > 1e-6).any(axis=2).sum()), float(excursion.max())


@pytest.mark.parametrize("strength", [2 ** -14, 2 ** -12, 2 ** -11, 2 ** -10, 2 ** -9, .1])
def test_new_generated_gamut_grid_has_independent_reference(strength):
    source, matrix, gamma = sparse_profile_fixture(strength)
    output = pillow_reference(source)
    reference_delta = analytic_lab_distance(source, output, matrix, gamma)
    count, excursion = independent_gamut(source, matrix, gamma)
    report = qa.diagnose_forward_colour(source, output, tile_pixels=511)
    assert report["gamut"]["pixels_outside"] == count == 1
    assert report["gamut"]["max_excursion_normalized"] == pytest.approx(excursion, abs=1e-6)
    assert report["forward_delta_e76_D50"]["mean"] == pytest.approx(reference_delta.mean(), abs=.01)
    assert report["forward_delta_e76_D50"]["max"] == pytest.approx(reference_delta.max(), abs=.01)
    # Classification oracle comes from matrix/TRC maths, not observed QA output.
    expected = (reference_delta.mean() + .01 <= .50
                and float(np.quantile(reference_delta, .999, method="inverted_cdf")) + .011 <= 1
                and reference_delta.max() + .01 <= 2 and count * 1000 <= source.width * source.height
                and excursion <= 2 / 255)
    assert evaluate(report)["isolated_policy_pass"] == bool(expected)
    if strength == 2 ** -9:
        assert evaluate(report)["failed_checks"] == ["gamut_excursion"]


def test_generated_extent_failure_is_not_hidden_by_small_excursion():
    source, matrix, gamma = sparse_profile_fixture(2 ** -12, spots=11)
    count, excursion = independent_gamut(source, matrix, gamma)
    assert count == 11 and excursion < 2 / 255
    report = qa.diagnose_forward_colour(source, tile_pixels=499)
    assert evaluate(report)["failed_checks"] == ["gamut_count", "gamut_fraction"]


def test_wrong_profile_is_rejected_even_with_small_gamut_extent():
    source = Image.new("RGB", (100, 100), (80, 120, 160))
    source.info["icc_profile"] = profile_fixture(1)[0]
    wrong = source.copy(); wrong.info["icc_profile"] = profile_fixture(2.2)[0]
    report = qa.diagnose_forward_colour(source, pillow_reference(wrong))
    assert report["gamut"]["pixels_outside"] == 0
    assert not evaluate(report)["isolated_policy_pass"]


def test_quantisation_only_pass_remains_unusable_as_export_permission(tmp_path):
    ramp = np.repeat(np.arange(32, dtype=np.uint8)[None, :, None], 3, axis=2)
    source = Image.fromarray(ramp); source.info["icc_profile"] = profile_fixture(2.2)[0]
    before = source.tobytes(), deepcopy(source.info)
    result = evaluate(qa.diagnose_forward_colour(source))
    assert result["isolated_policy_pass"] and not result["export_authorized"]
    assert not result["production_policy_active"] and not result["clinical_approved"]
    assert export.ROUNDTRIP_LIMIT == 2
    with pytest.raises(ValueError, match="round-trip"):
        export.export_rgb_png(source, tmp_path / "forbidden.png")
    with pytest.raises(ValueError, match="Owner decision"):
        export.authorise(result, "package_development", {}, opt_in=True)
    assert not (tmp_path / "forbidden.png").exists()
    assert (source.tobytes(), source.info) == before


def test_pure_evaluator_is_reproducible_and_cannot_write_or_package(report, monkeypatch):
    before = deepcopy(report)
    def forbidden(*args, **kwargs): pytest.fail("isolated evaluator attempted IO/export")
    monkeypatch.setattr(Image, "open", forbidden)
    monkeypatch.setattr(Image.Image, "save", forbidden)
    monkeypatch.setattr(export, "package_development", forbidden)
    monkeypatch.setattr(export, "export_rgb_png", forbidden)
    first = evaluate(report)
    assert first == evaluate(report) and report == before
    assert not first["export_authorized"]
