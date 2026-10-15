"""Isolated Option A qualification; no export, data access or approval authority."""
from decimal import Decimal
import hashlib
import json
import math

POLICY_ID = "pp1-option-a-isolated-v1-20261015"
PREREQUISITES = (
    "source_hash_verified", "source_unchanged", "geometry_verified",
    "metadata_allowlist_verified", "profile_verified", "runtime_reference_verified",
    "development_only", "holds_excluded", "np015_excluded",
    "content_groups_isolated", "test_isolation_verified", "owner_scope_verified",
    "labels_splits_unchanged",
)


def measurement_digest(measurements):
    """Bind supplied prerequisite evidence to these exact aggregate measurements."""
    data = json.dumps(measurements, sort_keys=True, allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def _finite_tree(value):
    if type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_finite_tree(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _finite_tree(item) for key, item in value.items())
    return False


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("Invalid diagnostic number")
    return value


def _count(value, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("Invalid diagnostic count")
    return value


def _validate(measurements):
    """Reject missing/inconsistent summaries, not just obvious threshold failures."""
    if type(measurements) is not dict or not _finite_tree(measurements):
        raise ValueError("Invalid diagnostic tree")
    n = measurements["pixels"]
    if type(n) is not int or n <= 0:
        raise ValueError("Invalid pixel coverage")
    dimensions = measurements["dimensions"]
    if (type(dimensions) is not list or len(dimensions) != 2
            or any(type(v) is not int or v <= 0 for v in dimensions)
            or dimensions[0] * dimensions[1] != n):
        raise ValueError("Inconsistent geometry")
    settings = measurements["settings"]
    if (type(settings["intent"]) is not int or settings["intent"] != 1
            or type(settings["flags"]) is not int or settings["flags"] != 0
            or type(settings["lcms_encoded_version"]) is not int
            or settings["lcms_encoded_version"] <= 0
            or settings["source_interpretation"] not in
            ("embedded_ICC", "explicit_untagged_as_srgb_contract")
            or measurements["diagnostic_only"] is not True
            or measurements["acceptance_decision"] != "not_evaluated"
            or measurements["output_mode"] not in ("measured_supplied_srgb", "simulated_srgb_in_memory")):
        raise ValueError("Unexpected diagnostic settings")
    delta = measurements["forward_delta_e76_D50"]
    if type(delta["count"]) is not int or delta["count"] != n:
        raise ValueError("Partial colour coverage")
    minimum, mean, maximum = [_number(delta[k]) for k in ("min", "mean", "max")]
    if not minimum <= mean <= maximum:
        raise ValueError("Inconsistent colour summary")
    if (delta["percentile_method"] != "nearest-rank, enclosing bins"
            or delta["bin_width"] != 0.001):
        raise ValueError("Unqualified percentile representation")
    previous = minimum
    for q in ("50", "90", "95", "99", "99.9"):
        low, high = delta["percentile_bounds"][q]
        if not minimum <= _number(low) <= _number(high) <= maximum or low < previous:
            raise ValueError("Inconsistent percentile bounds")
        previous = low
    overflow = _count(delta["overflow_count_ge_512"], n)
    if bool(overflow) != (maximum >= 512):
        raise ValueError("Inconsistent histogram overflow")
    gamut = measurements["gamut"]
    c = _count(gamut["pixels_outside"], n)
    excursion = _number(gamut["max_excursion_normalized"])
    channel_max = gamut["max_excursion_per_channel_normalized"]
    channel_count = gamut["channel_counts"]
    if (gamut["epsilon_normalized_rgb"] != 1e-6 or len(channel_max) != 3 or len(channel_count) != 3
            or max(map(_number, channel_max)) != excursion
            or any(_count(v, n) > c for v in channel_count) or sum(channel_count) < c
            or (c > 0) != (excursion > 1e-6)
            or _count(gamut["raw_pixels_outside_zero_epsilon"], n) < c
            or _number(gamut["mean_excursion_all_channel_samples"]) > excursion):
        raise ValueError("Inconsistent gamut summary")
    below, above = [_count(gamut[k], c) for k in ("pixels_below", "pixels_above")]
    if below + above < c or not math.isclose(
            _number(gamut["percentage_outside"]), 100 * c / n, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("Inconsistent gamut fraction")
    reverse = measurements["reverse_rgb"]
    if type(reverse["current_limit"]) is not int or reverse["current_limit"] != 2:
        raise ValueError("Production guard evidence changed")
    for stats in [reverse["per_pixel_max"], *[reverse["channels"][ch] for ch in ("R", "G", "B")]]:
        if not 0 <= _number(stats["mean"]) <= _count(stats["max"], 255):
            raise ValueError("Inconsistent reverse diagnostic")
        _count(stats["count_gt_current_limit"], n)
    return n, delta, gamut


def _prerequisites_verified(measurements, evidence):
    # These are caller-verified evidence references, NOT checks performed here.
    # No default passing record, human/clinical approval or dataset read is made.
    if (type(evidence) is not dict or evidence.get("qa_sha256") != measurement_digest(measurements)
            or type(evidence.get("checks")) is not dict):
        return False
    for name in PREREQUISITES:
        item = evidence["checks"].get(name)
        if (type(item) is not dict or item.get("passed") is not True
                or type(item.get("reference")) is not str or not item["reference"].strip()):
            return False
    return True


def evaluate_option_a(measurements, evidence=None):
    """Evaluate frozen budgets in isolation; a pass NEVER authorizes packaging.

    Prerequisite evidence must come from independent checks and be bound to the
    QA digest. This pure evaluator cannot attest that a caller's claims are true.
    Production must continue to run its actual guards; this is not wired to it.
    """
    checks = dict.fromkeys(("measurements_valid", "mean_delta_e", "tail_delta_e", "max_delta_e",
                            "gamut_count", "gamut_fraction", "gamut_excursion", "prerequisites"), False)
    try:
        n, delta, gamut = _validate(measurements)
        checks["measurements_valid"] = True
        # Algebraically subtract the fixed .01 reserve first. Decimal string
        # comparisons prevent next-float-above-boundary passing after addition.
        checks["mean_delta_e"] = Decimal(str(delta["mean"])) <= Decimal("0.49")
        checks["tail_delta_e"] = Decimal(str(delta["percentile_bounds"]["99.9"][1])) <= Decimal("0.99")
        checks["max_delta_e"] = Decimal(str(delta["max"])) <= Decimal("1.99")
        c = gamut["pixels_outside"]
        checks["gamut_count"] = c <= n // 1000
        # Exact rational comparison, not the rounded displayed percentage.
        checks["gamut_fraction"] = c * 1000 <= n
        checks["gamut_excursion"] = gamut["max_excursion_normalized"] <= 2 / 255
        checks["prerequisites"] = _prerequisites_verified(measurements, evidence)
    except (KeyError, TypeError, ValueError, OverflowError):
        # Do not leak private input values or return a partially passing record.
        checks = dict.fromkeys(checks, False)
    return {"policy_id": POLICY_ID, "scope": "isolated_candidate_qualification",
            "isolated_policy_pass": all(checks.values()), "checks": checks,
            "failed_checks": [name for name, passed in checks.items() if not passed],
            "production_policy_active": False, "export_authorized": False,
            "clinical_approved": False,
            "notice": "Engineering qualification only; not clinical validation or packaging permission."}
