"""Explicit Option A development-export path; fresh packaging permission required.

No version dispatch/fallback, auto-authorization, training or dataset scan.
"""
from copy import deepcopy
import json
from pathlib import Path
import platform
import zipfile

import numpy as np
from PIL import Image, ImageCms, __version__ as PILLOW_VERSION

from src.vision import exploratory_bundle as legacy
from src.vision import colour_qa as qa
from src.vision import colour_policy as policy

BUNDLE_VERSION = "pp1-exploratory-bundle-v4-option-a"
EXPORT_POLICY = "ICC_to_sRGB_relative_intent1_flags0_OptionA_v1_PNG_fixed_sRGB_chunk"
SCOPE = "package_development_option_a_v4"
EXPECTED_HELD = 181
MAX_MANIFEST_BYTES = 16 * 1024**2
DATASET_ATTRIBUTION = deepcopy(legacy.DATASET_ATTRIBUTION)
DATASET_ATTRIBUTION["transformation_notice"] += (
    " Version 4 uses explicitly bounded lossy Option A colour acceptance; "
    "reverse RGB errors are diagnostic only; no clinical colour validation.")


def policy_spec():
    return {"id": policy.POLICY_ID, "mean_delta_e_plus_reserve_max": "0.50",
            "p99_9_upper_plus_reserve_max": "1.00", "max_delta_e_plus_reserve_max": "2.00",
            "delta_e_reserve": "0.01", "gamut_count_denominator": 1000,
            "gamut_fraction_max": "0.001", "excursion_max": "2/255", "gamut_epsilon": "0.000001"}


def source_code_hashes():
    root = Path(__file__).parent
    names = ("exploratory_bundle.py", "exploratory_bundle_v4.py", "colour_qa.py",
             "colour_policy.py", "model_pipeline.py", "train_pipeline.py")
    return {name: legacy.sha256(root / name) for name in names}


def _runtime_reference():
    """Run a tiny generated sRGB/Lab reference check, not a dataset/test suite."""
    pixels = np.array([[[0, 0, 0], [255, 255, 255], [64, 128, 192], [192, 96, 48]]], dtype=np.uint8)
    profile = ImageCms.createProfile("sRGB")
    matrix = np.column_stack([getattr(profile, key)[0]
                             for key in ("red_colorant", "green_colorant", "blue_colorant")])
    encoded = pixels.astype(np.float64) / 255
    linear = np.where(encoded <= .04045, encoded / 12.92, ((encoded + .055) / 1.055) ** 2.4)
    xyz = linear @ matrix.T / np.array([.9642, 1, .8249])
    delta = 6 / 29
    f = np.where(xyz > delta**3, np.cbrt(xyz), xyz / (3 * delta**2) + 4 / 29)
    expected = np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]),
                         200 * (f[..., 1] - f[..., 2])], axis=-1)
    engine = qa._Transforms(None)
    try:
        measured = engine.run(engine.source_lab, pixels, np.float64)
        identity = engine.run(engine.forward, pixels, np.uint8)
        error = float(np.linalg.norm(measured - expected, axis=2).max())
        if not np.isfinite(measured).all() or not np.isfinite(error) or error > .01 or not np.array_equal(identity, pixels):
            raise ValueError("Runtime generated reference qualification failed")
        return {"python": platform.python_version(), "pillow": PILLOW_VERSION,
                "numpy": np.__version__, "lcms_encoded": engine.version(),
                "generated_reference_max_delta_e": error, "reference_limit": .01}
    finally:
        engine.close()


def _identity(records):
    values = [{"source_record_id": r["source_record_id"], "original_image_path": r["image_path"],
               "original_split": r["original_split"], "content_group_id": r["content_group_id"],
               "provisional_mgi_grade": r["candidate_mgi_grade"]} for r in records]
    return legacy.json_digest(sorted(values, key=lambda r: r["source_record_id"]))


def _prepare(draft_path, inventory_path):
    # Rebuild from pinned evidence; never accept an arbitrary caller plan/flags.
    plan = legacy.prepare_plan(draft_path, inventory_path)
    draft = json.loads(Path(draft_path).read_text())
    held = len(draft["records"]) - len(plan["records"])
    if held != EXPECTED_HELD or _identity(plan["records"]) != legacy.CANDIDATE_IDENTITY_SHA:
        raise ValueError("Frozen holds/cohort identity mismatch")
    legacy.validate_source_plan(plan)
    return plan, held


def authorization_bindings(plan, output_dir):
    """No authorization is created: return bindings for a real owner decision."""
    return {"source_draft_sha256": plan["source_draft_sha256"], "source_plan_sha256": legacy.json_digest(plan),
            "code_sha256": legacy.json_digest(source_code_hashes()), "bundle_id": Path(output_dir).name,
            "export_version": BUNDLE_VERSION, "colour_policy_sha256": legacy.json_digest(policy_spec())}


def _receipt_evidence(measurements, receipt):
    """Derive references only from successful internal checks, never input flags."""
    reference = "v4-checked-receipt:" + legacy.json_digest(receipt)
    return {"qa_sha256": policy.measurement_digest(measurements),
            "checks": {name: {"passed": True, "reference": reference + ":" + name}
                       for name in policy.PREREQUISITES}}


def _require_policy(measurements, receipt):
    result = policy.evaluate_option_a(measurements, _receipt_evidence(measurements, receipt))
    if not result["isolated_policy_pass"]:
        raise ValueError("Option A colour rejection: " + ",".join(result["failed_checks"]))
    return result


def _managed(image):
    profile = legacy.check_source_colour(image)
    converted = image if profile is None else ImageCms.profileToProfile(
        image, profile, ImageCms.createProfile("sRGB"), outputMode="RGB", renderingIntent=1, flags=0)
    clean = Image.frombytes("RGB", converted.size, converted.tobytes())
    clean.info["srgb"] = 1
    return clean, "untagged_srgb_identity" if profile is None else "icc_to_srgb"


def _export_row(row, source_root, output, cam_ids, context):
    source = legacy.safe_file(source_root, row["image_path"])
    before = legacy.sha256(source)
    if before != row["source_sha256"]:
        raise ValueError("Source changed before v4 export")
    with Image.open(source) as image:
        if list(image.size) != row["source_dimensions"]:
            raise ValueError("Source geometry mismatch")
        clean, conversion = _managed(image)
        if clean.size != image.size or clean.info != {"srgb": 1}:
            raise ValueError("Unsafe managed geometry/metadata")
        measurements = qa.diagnose_forward_colour(image, clean)
        source_rgb, managed_rgb = legacy.rgb_digest(image), legacy.rgb_digest(clean)
        after = legacy.sha256(source)
        if after != before:
            raise ValueError("Source changed during colour QA")
        receipt = {"context": deepcopy(context), "source_record_id": row["source_record_id"],
                   "source_sha256": before, "source_after_qa_sha256": after,
                   "source_rgb_sha256": source_rgb, "managed_rgb_sha256": managed_rgb,
                   "dimensions": list(clean.size), "clean_metadata": {"srgb": 1}}
        _require_policy(measurements, receipt)  # Every condition before first write.
        name = "images/" + row["source_record_id"] + ".png"
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        small = legacy.resized_rgb(clean)
        derivative = legacy._write_srgb_png(small, destination)
        # Check actual decoded exported pixels against the approved conversion.
        if derivative["rgb_sha256"] != legacy.rgb_digest(small):
            raise ValueError("Export differs from checked resized pixels")
        item = {"source_record_id": row["source_record_id"], "original_split": row["original_split"],
                "image_path": name, "content_group_id": row["content_group_id"],
                "provisional_mgi_grade": row["candidate_mgi_grade"], "label_status": "provisional",
                "qualified_label_approved": False, "participant_id": None,
                "original_image_path": row["image_path"], "source_sha256": before,
                "source_dimensions": row["source_dimensions"], "source_rgb_sha256": source_rgb,
                "colour_managed_rgb_sha256": managed_rgb, "colour_conversion": conversion,
                "colour_roundtrip_max_channel_error": measurements["reverse_rgb"]["per_pixel_max"]["max"],
                "colour_measurements": measurements, "colour_receipt": receipt,
                "image_payload_sha256": derivative["sha256"], "image_rgb_sha256": derivative["rgb_sha256"],
                "image_dimensions": derivative["dimensions"]}
        files = {name: derivative["sha256"]}
        if row["source_record_id"] in cam_ids:
            cam_name = "cam/" + row["source_record_id"] + ".png"
            (output / cam_name).parent.mkdir(parents=True, exist_ok=True)
            cam = legacy._write_srgb_png(clean, output / cam_name)
            if cam["rgb_sha256"] != managed_rgb:
                raise ValueError("CAM differs from checked full-resolution pixels")
            item.update(cam_original_path=cam_name, cam_payload_sha256=cam["sha256"],
                        cam_rgb_sha256=cam["rgb_sha256"], cam_dimensions=cam["dimensions"])
            files[cam_name] = cam["sha256"]
    final_source_sha = legacy.sha256(source)
    if final_source_sha != before:
        raise ValueError("Source changed after writing")
    receipt["source_after_export_sha256"] = final_source_sha
    receipt["verified_payloads"] = deepcopy(files)
    item["colour_evidence"] = _receipt_evidence(measurements, receipt)
    _validate_colour(item)  # Same acceptance rule again on the final stored record.
    return item, files


def _validate_colour(row):
    measurements, receipt = row["colour_measurements"], row["colour_receipt"]
    if (receipt["source_record_id"] != row["source_record_id"]
            or receipt["source_sha256"] != row["source_sha256"]
            or receipt["source_after_qa_sha256"] != row["source_sha256"]
            or receipt["source_after_export_sha256"] != row["source_sha256"]
            or receipt["source_rgb_sha256"] != row["source_rgb_sha256"]
            or receipt["managed_rgb_sha256"] != row["colour_managed_rgb_sha256"]
            or receipt["dimensions"] != row["source_dimensions"]
            or measurements["dimensions"] != row["source_dimensions"]
            or receipt["clean_metadata"] != {"srgb": 1}
            or row["colour_evidence"] != _receipt_evidence(measurements, receipt)
            or row["colour_roundtrip_max_channel_error"] != measurements["reverse_rgb"]["per_pixel_max"]["max"]):
        raise ValueError("V4 source/QA/metadata evidence binding mismatch")
    expected = {row["image_path"]: row["image_payload_sha256"]}
    if "cam_original_path" in row:
        expected[row["cam_original_path"]] = row["cam_payload_sha256"]
    if receipt["verified_payloads"] != expected:
        raise ValueError("V4 QA/export payload binding mismatch")
    _require_policy(measurements, receipt)
    if row.get("colour_conversion") not in {"untagged_srgb_identity", "icc_to_srgb"}:
        raise ValueError("V4 colour conversion provenance missing")
    expected_interpretation = ("embedded_ICC" if row["colour_conversion"] == "icc_to_srgb"
                               else "explicit_untagged_as_srgb_contract")
    if (measurements["output_mode"] != "measured_supplied_srgb"
            or measurements["settings"]["source_interpretation"] != expected_interpretation):
        raise ValueError("V4 requires measured exported-colour evidence")
    if row["colour_conversion"] == "untagged_srgb_identity" and (
            row["source_rgb_sha256"] != row["colour_managed_rgb_sha256"]
            or row["colour_roundtrip_max_channel_error"] != 0):
        raise ValueError("Identity source pixels changed")


def bundle_records(bundle):
    if bundle.get("colour_policy") != policy_spec() or bundle.get("colour_policy_sha256") != legacy.json_digest(policy_spec()):
        raise ValueError("V4 frozen policy mismatch")
    if bundle.get("cam_ids") != list(legacy.CAM_IDS):
        raise ValueError("V4 fixed CAM membership mismatch")
    records = legacy._bundle_records(bundle, BUNDLE_VERSION, EXPORT_POLICY, DATASET_ATTRIBUTION, _validate_colour)
    bindings = authorization_bindings({"source_draft_sha256": bundle["source_draft_sha256"]}, "unused")
    # Source-plan binding is stored, not reconstructed from a reduced export manifest.
    bindings.update(source_plan_sha256=bundle["source_plan_sha256"], bundle_id=bundle["bundle_id"])
    legacy.authorise(bundle["packaging_authorization"], SCOPE, bindings, opt_in=True)
    context = bundle["checked_context"]
    if (context["source_draft_sha256"] != legacy.DRAFT_SHA
            or bundle["source_draft_sha256"] != context["source_draft_sha256"]
            or context["held_count"] != EXPECTED_HELD
            or context["cohort_identity_sha256"] != legacy.CANDIDATE_IDENTITY_SHA
            or context["source_plan_sha256"] != bundle["source_plan_sha256"]
            or context["authorization_sha256"] != legacy.json_digest(bundle["packaging_authorization"])
            or context["protected_groups_sha256"] != legacy.json_digest(bundle["protected_groups"])
            or context["uncertain_groups_sha256"] != legacy.json_digest(bundle["uncertain_groups"])
            or context["runtime_sha256"] != legacy.json_digest(bundle["runtime_reference"])):
        raise ValueError("V4 pinned source context mismatch")
    runtime = bundle["runtime_reference"]
    if (runtime["reference_limit"] != .01 or not np.isfinite(runtime["generated_reference_max_delta_e"])
            or not 0 <= runtime["generated_reference_max_delta_e"] <= .01):
        raise ValueError("V4 runtime reference evidence failed")
    for row in records:
        if (row["colour_receipt"]["context"] != context
                or row["colour_measurements"]["settings"]["lcms_encoded_version"] != runtime["lcms_encoded"]):
            raise ValueError("V4 record context mismatch")
    projected = [{"source_record_id": r["source_record_id"], "image_path": r["original_image_path"],
                  "original_split": r["original_split"], "content_group_id": r["content_group_id"],
                  "candidate_mgi_grade": r["provisional_mgi_grade"]} for r in records]
    legacy.fixed_cohort(projected)
    if _identity(projected) != legacy.CANDIDATE_IDENTITY_SHA:
        raise ValueError("V4 candidate identity changed")
    return records


def validate_bundle(root, expected_manifest_sha256):
    """Offline payload/QA verification requires an independently trusted manifest SHA.

    It verifies recorded QA and actual exported pixels/metadata; without originals
    it cannot remeasure source colour or prove caller-authored provenance truthful.
    """
    manifest = legacy.safe_file(root, "bundle_manifest.json")
    if manifest.stat().st_size > MAX_MANIFEST_BYTES or legacy.sha256(manifest) != expected_manifest_sha256:
        raise ValueError("V4 trusted manifest hash/size mismatch")
    return legacy._validate_bundle(root, bundle_records)


def package_development(draft_path, inventory_path, source_root, output_dir, authorization, opt_in=False):
    # Real image access is gated by a NEW owner scope, never this coding task.
    legacy.authorise(authorization, SCOPE, {}, opt_in)
    plan, held = _prepare(draft_path, inventory_path)
    bindings = authorization_bindings(plan, output_dir)
    legacy.authorise(authorization, SCOPE, bindings, opt_in)
    output = legacy.new_ignored_output(output_dir, "data")
    archive = output.with_suffix(".zip")
    if archive.exists() or archive.is_symlink():
        raise ValueError("Fresh v4 archive/output required")
    runtime = _runtime_reference()
    legacy.dry_run(plan, source_root)
    for row in plan["records"]:
        with Image.open(legacy.safe_file(source_root, row["image_path"])) as image:
            legacy.check_source_colour(image)
    context = {"source_draft_sha256": plan["source_draft_sha256"], "source_plan_sha256": legacy.json_digest(plan),
               "held_count": held, "cohort_identity_sha256": _identity(plan["records"]),
               "authorization_sha256": legacy.json_digest(authorization),
               "protected_groups_sha256": legacy.json_digest(plan["protected_groups"]),
               "uncertain_groups_sha256": legacy.json_digest(plan["uncertain_groups"]),
               "runtime_sha256": legacy.json_digest(runtime)}
    output.mkdir(parents=True)
    records, files = [], {}
    for row in plan["records"]:
        item, payloads = _export_row(row, source_root, output, plan["cam_ids"], context)
        records.append(item); files.update(payloads)
    bundle = {"version": BUNDLE_VERSION, "export_policy": EXPORT_POLICY,
              "colour_policy": policy_spec(), "colour_policy_sha256": legacy.json_digest(policy_spec()),
              "dataset_attribution": deepcopy(DATASET_ATTRIBUTION), "status": "provisional_exploratory_only",
              "notice": legacy.NOTICE, "mgi_schema": list(legacy.vp.MGI_GRADES),
              "qualified_labels_approved": False, "participant_independence_verified": False, "final_research_approved": False,
              "source_draft_sha256": plan["source_draft_sha256"], "source_plan_sha256": legacy.json_digest(plan),
              "packaging_authorization": deepcopy(authorization), "bundle_id": output.name,
              "checked_context": context, "runtime_reference": runtime,
              "protected_groups": plan["protected_groups"], "uncertain_groups": plan["uncertain_groups"],
              "cam_ids": plan["cam_ids"], "files": files, "records": records}
    manifest = output / "bundle_manifest.json"
    manifest.write_text(json.dumps(bundle, indent=2, allow_nan=False) + "\n")
    manifest_sha = legacy.sha256(manifest)
    validate_bundle(output, manifest_sha)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as target:
        for name in sorted(set(files) | {"bundle_manifest.json"}):
            target.write(output / name, name)
    return {"notice": legacy.NOTICE, "archive": str(archive), "archive_sha256": legacy.sha256(archive),
            "bundle_manifest_sha256": manifest_sha, "version": BUNDLE_VERSION}
