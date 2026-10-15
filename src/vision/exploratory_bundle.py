"""Development-only pilot bundle preparation; dry-run never decodes images.

Real packaging needs separate owner authorisation. No qualified approval is made.
"""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import zipfile
import zlib

import numpy as np
from PIL import Image, ImageCms, PngImagePlugin

from src.vision import model_pipeline as vp

NOTICE = "Provisional labels; non-clinical; non-final; participant independence unverified."
DRAFT_SHA = "b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1"
CANDIDATE_IDENTITY_SHA = "7e1e0d05015f41b20d472cb46c9dcda2867b6452e1361ecce75252fde4afc81f"
CAM_IDS = ("Validation/00733", "Validation/00734", "Validation/00766")
EXPECTED_COUNTS = {"Training": 680, "Validation": 53}
EXPECTED_GRADES = {"Training": [0, 12, 84, 223, 361], "Validation": [0, 1, 13, 22, 17]}
ACKS = ("provisional_labels", "non_clinical_non_final", "participant_independence_unverified",
        "no_test_access", "missing_mgi0_scarce_mgi1", "no_final_approval_or_promotion")
NP015_IDS = ("Training/00591", "Validation/00736")
BUNDLE_VERSION = "pp1-exploratory-bundle-v3"
EXPORT_POLICY = "ICC_to_sRGB_relative_intent1_flags0_before_resize_PNG_fixed_sRGB_chunk"
ROUNDTRIP_LIMIT = 2  # Conservative 8-bit numerical guard, not a clinical tolerance.
DATASET_ATTRIBUTION = {
    "title": "A DENTAL INTRAORAL IMAGE DATASET OF GINGIVITIS FOR IMAGE CAPTIONING",
    "creator": "Duy Hoang Bao", "version": 1, "doi": "10.17632/3253gj88rr.1",
    "source_url": "https://data.mendeley.com/datasets/3253gj88rr/1",
    "licence": "CC BY 4.0", "licence_url": "https://creativecommons.org/licenses/by/4.0/",
    "transformation_notice": "Development-only ICC-to-standard-sRGB conversion before RGB resizing, "
        "lossless full-resolution sRGB PNG copies and a fixed non-identifying sRGB chunk; "
        "source metadata removed; provisional caption-derived image-maximum labels, not clinically approved. "
        "ICC conversion may change RGB numbers; no geometry rotation or licensor endorsement claimed.",
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def source_code_hashes():
    directory = Path(__file__).parent
    names = ["exploratory_bundle.py", "exploratory_pilot.py", "model_pipeline.py", "train_pipeline.py"]
    return {name: sha256(directory / name) for name in names}


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Unsafe relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in {"..", "."} or p.casefold() == "test" for p in path.parts):
        raise ValueError("Unsafe or Test path")
    if path.as_posix() != value or ":" in value:
        raise ValueError("Non-canonical relative path")
    return path


def safe_file(root, name):
    """Reject links, traversal and paths outside the dedicated data root."""
    root = Path(root)
    if root.is_symlink():
        raise ValueError("Symlink data root")
    relative = relative_path(name)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink payload path")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError("Payload escapes data root")
    if not current.is_file():
        raise ValueError("Missing payload: " + name)
    return current


def authorise(record, scope, bindings, opt_in=False):
    """Check a recorded owner decision, never fabricate clinical approval.

    This record documents human opt-in; it is not cryptographic identity proof.
    The caller must obtain the owner's actual decision before creating it.
    """
    if not opt_in or not isinstance(record, dict):
        raise ValueError("Explicit owner opt-in required")
    if (record.get("status") != "owner_confirmed" or record.get("scope") != scope
            or not record.get("authorizer") or not record.get("date")
            or not record.get("evidence_reference")):
        raise ValueError("Owner decision scope/provenance missing")
    if any(record.get("acknowledgements", {}).get(key) is not True for key in ACKS):
        raise ValueError("Required provisional limitations not acknowledged")
    if any(record.get(key) != value for key, value in bindings.items()):
        raise ValueError("Authorisation hash/config binding mismatch")


def select_candidates(draft):
    if (draft.get("status") != "draft_not_approved" or draft.get("activated") is not False
            or draft.get("training_ready") is not False or draft.get("mgi_schema") != list(vp.MGI_GRADES)):
        raise ValueError("An unchanged, unapproved five-grade DRAFT is required")
    if draft.get("policy", {}).get("optional_upper_partial_policy_activated") is not False:
        raise ValueError("Partial-caption policy must remain inactive")
    if any(draft.get("approval", {}).get(key) is not False for key in
           ["labels_approved", "split_approved", "duplicate_review_complete", "participant_independence_verified"]):
        raise ValueError("Keep final research approvals false")
    blocked = set(draft["sealed_boundary"]["protected_test_content_group_ids"])
    blocked.update(draft["sealed_boundary"]["unresolved_NP015_group_ids"])
    selected, paths, groups = [], set(), set()
    for row in draft.get("records", []):
        # Check split before inspecting a label; Test records are forbidden.
        split = row.get("original_split")
        if split not in EXPECTED_COUNTS:
            raise ValueError("Test/nondevelopment record is forbidden")
        name = row.get("image_path")
        relative_path(name)
        if not re.fullmatch(r"Dataset/" + split + r"/Images/\d{5}\.jpg", name):
            raise ValueError("Original source path/split mismatch")
        if name in paths:
            raise ValueError("Duplicate source record")
        paths.add(name)
        if (row.get("qualified_label_approved") is not False or row.get("training_eligible") is not False
                or row.get("mgi_grade") is not None or row.get("participant_id") is not None
                or row.get("analysis_split") is not None):
            raise ValueError("Do not invent approvals, final labels or participant IDs")
        if row.get("technical_candidate") is not True:
            if not row.get("draft_exclusion_reasons"):
                raise ValueError("Held record must preserve exclusion reasons")
            continue
        group = row.get("content_group_id")
        if (row.get("source_record_id") in NP015_IDS
                or not isinstance(group, str) or not group or group in blocked or group in groups
                or row.get("group_source_member_count") != 1
                or row.get("group_original_split_presence") != [split]):
            raise ValueError("Content overlap, protected/NP015 or unresolved multi-image group")
        grade = row.get("candidate_mgi_grade")
        if (type(grade) is not int or grade not in vp.MGI_GRADES
                or row.get("cached_qa_requires_review") is not False
                or row.get("original_cached_status") == "needs_review"
                or row.get("cached_qa_issues") or row.get("cached_original_issues")
                or row.get("draft_exclusion_reasons")
                or row.get("candidate_label_status") != "strict_technically_consistent_unapproved"
                or row.get("proposed_analysis_split") != split):
            raise ValueError("Not a strict technically consistent provisional candidate")
        if row.get("source_record_id") != split + "/" + Path(name).stem:
            raise ValueError("Source identifier mismatch")
        groups.add(group)
        selected.append(deepcopy(row))
    if not selected:
        raise ValueError("Empty provisional cohort")
    return selected


def fixed_cohort(records):
    for split, expected in EXPECTED_COUNTS.items():
        rows = [r for r in records if r["original_split"] == split]
        grades = [sum(r["candidate_mgi_grade"] == grade for r in rows) for grade in range(5)]
        if len(rows) != expected or grades != EXPECTED_GRADES[split]:
            raise ValueError("Frozen candidate counts/grades do not match the planned pilot")
    if not set(CAM_IDS).issubset({r["source_record_id"] for r in records}):
        raise ValueError("A fixed Grad-CAM example is ineligible")


def read_hash_inventory(path):
    """Project only development file metadata from the cached audit layout.

    No annotation/label fields are decoded; Test rows are skipped by split.
    """
    inventory, active, row = {}, False, None
    fields = {"split", "image_path", "sha256", "width", "height"}
    with Path(path).open() as source:
        for line in source:
            if not active:
                active = line == '    "manifest": [\n'
                continue
            if line == '    ],\n':
                break
            if line == '      {\n':
                row = {}
            elif line in {'      },\n', '      }\n'}:
                if row and row.get("split") in EXPECTED_COUNTS:
                    name = row["image_path"]
                    if name in inventory:
                        raise ValueError("Duplicate cached source metadata")
                    inventory[name] = row
                row = None
            elif row is not None:
                match = re.match(r'        "([a-z_0-9]+)": (.*?)(?:,)?\n$', line)
                if not match or match.group(1) not in fields:
                    continue
                key, value = match.groups()
                if key != "split" and row.get("split") not in EXPECTED_COUNTS:
                    continue
                row[key] = json.loads(value.removesuffix(","))
    if not inventory:
        raise ValueError("Cached development hash inventory unavailable")
    return inventory


def prepare_plan(draft_path, hash_inventory_path):
    if sha256(draft_path) != DRAFT_SHA:
        raise ValueError("Frozen DRAFT checksum mismatch")
    draft = json.loads(Path(draft_path).read_text())
    for name, expected in draft["input_sha256"].items():
        if sha256(name) != expected:
            raise ValueError("DRAFT source evidence/code changed: " + name)
    records = select_candidates(draft)
    fixed_cohort(records)
    inventory = read_hash_inventory(hash_inventory_path)
    for row in records:
        metadata = inventory[row["image_path"]]
        if not re.fullmatch(r"[0-9a-f]{64}", metadata["sha256"]):
            raise ValueError("Cached source SHA-256 missing")
        row["source_sha256"] = metadata["sha256"]
        row["source_dimensions"] = [metadata["width"], metadata["height"]]
    return {"version": "pp1-development-bundle-plan-v1", "notice": NOTICE,
            "source_draft_sha256": DRAFT_SHA, "hash_inventory_sha256": sha256(hash_inventory_path),
            "protected_groups": draft["sealed_boundary"]["protected_test_content_group_ids"],
            "uncertain_groups": draft["sealed_boundary"]["unresolved_NP015_group_ids"],
            "cam_ids": list(CAM_IDS), "records": records}


def dry_run(plan, source_root):
    """Read selected source bytes for SHA checks only; never call Image.open."""
    sizes, verified = [], 0
    for row in plan["records"]:
        source = safe_file(source_root, row["image_path"])
        before = source.stat()
        if sha256(source) != row["source_sha256"]:
            raise ValueError("Source hash mismatch: " + row["source_record_id"])
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("Source changed during dry-run")
        sizes.append(after.st_size)
        verified += 1
    return {"notice": NOTICE, "mode": "dry_run", "source_hashes_verified": verified,
            "candidate_counts": {s: sum(r["original_split"] == s for r in plan["records"]) for s in EXPECTED_COUNTS},
            "raw_source_bytes": sum(sizes), "images_decoded": 0, "images_packaged": 0,
            "test_payloads_accessed": False, "clinical_approvals_created": False,
            "source_plan_sha256": json_digest(plan), "real_packaging_authorised": False}


def resized_rgb(image):
    prepared = vp.preprocess_rgb(image)
    _, _, width, height = prepared.valid_box
    small = image.resize((width, height), Image.Resampling.LANCZOS)
    if not np.array_equal(prepared.normalized_chw, vp.preprocess_rgb(small).normalized_chw):
        raise ValueError("Derivative preprocessing is not equivalent")
    return small


def check_source_colour(image):
    """Validate interpretation without decoding pixels or printing profile metadata."""
    if image.mode != "RGB" or image.getexif().get(274, 1) != 1:
        raise ValueError("RGB with identity EXIF orientation required; no silent rotation")
    if any(k in image.info for k in ("gamma", "chromaticity")):
        raise ValueError("Ambiguous colour gamma/chromaticity metadata")
    if "icc_profile" in image.info:
        raw = image.info["icc_profile"]
        if (not isinstance(raw, bytes) or not 132 <= len(raw) <= 4 * 1024**2
                or int.from_bytes(raw[:4], "big") != len(raw) or raw[36:40] != b"acsp"):
            raise ValueError("Malformed ICC colour profile")
        try:
            profile = ImageCms.ImageCmsProfile(BytesIO(raw))
            if (profile.profile.xcolor_space.strip() != "RGB"
                    or profile.profile.connection_space.strip() not in {"XYZ", "Lab"}
                    or profile.profile.device_class.strip() not in {"mntr", "scnr"}
                    or not profile.profile.is_matrix_shaper
                    or any(ImageCms.isIntentSupported(profile, 1, direction) != 1 for direction in (0, 1))):
                raise ValueError("Unsupported ICC colour profile")
            return profile
        except (ImageCms.PyCMSError, OSError, TypeError, ValueError, AttributeError):
            raise ValueError("Unsupported or malformed ICC colour profile") from None
    colour_space = image.getexif().get_ifd(34665).get(40961)
    if colour_space not in (None, 1):
        raise ValueError("Missing ICC for non-sRGB colour interpretation")
    return None  # Existing untagged/sRGB input contract; contradictory declarations fail above.


def managed_srgb(image):
    """Convert supported ICC once at full resolution; never inherit private metadata."""
    profile = check_source_colour(image)
    conversion, error = "untagged_srgb_identity", 0
    pixels = image
    if profile is not None:
        try:
            srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
            pixels = ImageCms.profileToProfile(image, profile, srgb, outputMode="RGB", renderingIntent=1, flags=0)
            restored = ImageCms.profileToProfile(pixels, srgb, profile, outputMode="RGB", renderingIntent=1, flags=0)
        except (ImageCms.PyCMSError, OSError, TypeError, ValueError):
            raise ValueError("ICC colour conversion failed; no export") from None
        error = int(np.abs(np.asarray(restored).astype(np.int16) - np.asarray(image).astype(np.int16)).max())
        if error > ROUNDTRIP_LIMIT:
            raise ValueError("ICC colour round-trip exceeds quantisation/gamut guard; review required")
        conversion = "icc_to_srgb"
    clean = Image.frombytes("RGB", pixels.size, pixels.tobytes())
    clean.info["srgb"] = 1  # Fixed rendering-intent byte, no source profile/date/identity.
    return clean, {"conversion": conversion, "roundtrip_max_channel_error": error}


def rgb_digest(image):
    return hashlib.sha256(image.tobytes()).hexdigest()


def verify_rgb_export(path, expected):
    """Only RGB pixels, structural chunks and a fixed sRGB byte may leave."""
    if sha256(path) != expected["sha256"]:
        raise ValueError("Export payload hash mismatch")
    # Reject even opaque chunks Pillow might not expose through image.info.
    with Path(path).open("rb") as source:
        if source.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Lossless PNG export required")
        seen_header, seen_srgb, seen_data = False, False, False
        while True:
            header = source.read(8)
            if len(header) != 8 or header[4:] not in (b"IHDR", b"sRGB", b"IDAT", b"IEND"):
                raise ValueError("Metadata or invalid PNG chunk in export")
            length = int.from_bytes(header[:4], "big")
            if source.tell() + length + 4 > Path(path).stat().st_size:
                raise ValueError("Truncated PNG export")
            if header[4:] == b"IHDR" and (seen_header or length != 13):
                raise ValueError("Invalid PNG header")
            data = source.read(length)
            crc = int.from_bytes(source.read(4), "big")
            if zlib.crc32(header[4:] + data) != crc:
                raise ValueError("PNG chunk CRC mismatch")
            if header[4:] == b"IHDR":
                if data[8:] != b"\x08\x02\x00\x00\x00":
                    raise ValueError("Only canonical 8-bit RGB PNG geometry allowed")
                seen_header = True
            elif header[4:] == b"sRGB":
                if not seen_header or seen_srgb or seen_data or data != b"\x01":
                    raise ValueError("Invalid or identifying/noncanonical sRGB declaration")
                seen_srgb = True
            else:
                if not seen_header or not seen_srgb:
                    raise ValueError("PNG header or fixed sRGB declaration missing")
                if header[4:] == b"IDAT":
                    seen_data = True
            if header[4:] == b"IEND":
                if length or not seen_data or source.read(1):
                    raise ValueError("Trailing data in PNG export")
                break
    with Image.open(path) as exported:
        if (exported.format != "PNG" or exported.mode != "RGB"
                or list(exported.size) != expected["dimensions"] or exported.info != {"srgb": 1}):
            raise ValueError("Unsafe export metadata, mode or geometry")
        exported.verify()  # Also checks PNG chunk CRCs.
    with Image.open(path) as exported:
        if rgb_digest(exported) != expected["rgb_sha256"]:
            raise ValueError("Export RGB pixel mismatch")


def export_rgb_png(image, destination):
    """Fresh pixels-only lossless export; never mutate source bytes or PIL info."""
    clean, _ = managed_srgb(image)
    return _write_srgb_png(clean, destination)


def _write_srgb_png(clean, destination):
    """Shared encoding only; each version must run its own colour gate first."""
    if clean.mode != "RGB" or clean.info != {"srgb": 1}:
        raise ValueError("Canonical metadata-safe sRGB pixels required")
    expected = {"dimensions": list(clean.size), "rgb_sha256": rgb_digest(clean)}
    metadata = PngImagePlugin.PngInfo()
    metadata.add(b"sRGB", b"\x01")
    with Path(destination).open("xb") as target:
        clean.save(target, format="PNG", pnginfo=metadata)
    expected["sha256"] = sha256(destination)
    verify_rgb_export(destination, expected)
    return expected


def validate_source_plan(plan):
    """Reuse the strict source gate before any synthetic or future real export."""
    gate = {"status": "draft_not_approved", "activated": False, "training_ready": False,
            "mgi_schema": list(vp.MGI_GRADES), "policy": {"optional_upper_partial_policy_activated": False},
            "approval": {k: False for k in ("labels_approved", "split_approved", "duplicate_review_complete",
                                           "participant_independence_verified")},
            "sealed_boundary": {"protected_test_content_group_ids": plan["protected_groups"],
                                "unresolved_NP015_group_ids": plan["uncertain_groups"]},
            "records": plan["records"]}
    selected = select_candidates(gate)
    if len(selected) != len(plan["records"]) or not set(plan["cam_ids"]).issubset(
            {r["source_record_id"] for r in selected}):
        raise ValueError("Held or ineligible CAM record in source plan")


def new_ignored_output(path, category):
    repo = Path(__file__).resolve().parents[2]
    output = Path(path)
    parent = repo / category
    if output.exists() or output.is_symlink() or not output.resolve().is_relative_to(parent.resolve()) or output.resolve() == parent.resolve():
        raise ValueError("Use a new ignored versioned " + category + " output location")
    current = output.parent
    while current != repo and current != current.parent:
        if current.is_symlink():
            raise ValueError("Symlink output parent")
        current = current.parent
    return output


def package_development(plan, source_root, output_dir, authorization, opt_in=False):
    """Future operation, never invoked on dental images by scaffold preparation."""
    authorise(authorization, "package_development", {"source_draft_sha256": plan["source_draft_sha256"],
              "source_plan_sha256": json_digest(plan), "code_sha256": json_digest(source_code_hashes()),
              "bundle_id": Path(output_dir).name}, opt_in)
    output = new_ignored_output(output_dir, "data")
    archive = output.with_suffix(".zip")
    if archive.exists() or archive.is_symlink():
        raise ValueError("Archive already exists; no overwrite")
    # Verify everything before creating/copying any image.
    validate_source_plan(plan)
    dry_run(plan, source_root)
    # Fail before any exports if a selected source needs an unapproved colour/orientation decision.
    for row in plan["records"]:
        with Image.open(safe_file(source_root, row["image_path"])) as image:
            check_source_colour(image)
    output.mkdir(parents=True)
    records, files = [], {}
    for row in plan["records"]:
        source = safe_file(source_root, row["image_path"])
        if sha256(source) != row["source_sha256"]:
            raise ValueError("Source changed before packaging")
        split, identifier = row["source_record_id"].split("/")
        name = f"images/{split}/{identifier}.png"
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            if image.mode != "RGB" or list(image.size) != row["source_dimensions"]:
                raise ValueError("RGB/source dimensions mismatch")
            source_rgb_sha256 = rgb_digest(image)
            managed, colour = managed_srgb(image)
            managed_rgb_sha256 = rgb_digest(managed)
            derivative = export_rgb_png(resized_rgb(managed), destination)
            cam = None
            if row["source_record_id"] in plan["cam_ids"]:
                raw_name = f"cam/{split}/{identifier}.png"
                (output / raw_name).parent.mkdir(parents=True, exist_ok=True)
                cam = export_rgb_png(managed, output / raw_name)
        if sha256(source) != row["source_sha256"]:
            raise ValueError("Source changed during export")
        files[name] = derivative["sha256"]
        item = {"source_record_id": row["source_record_id"], "original_split": split,
                "image_path": name, "content_group_id": row["content_group_id"],
                "provisional_mgi_grade": row["candidate_mgi_grade"], "label_status": "provisional",
                "qualified_label_approved": False, "participant_id": None,
                "original_image_path": row["image_path"], "source_sha256": row["source_sha256"],
                "source_dimensions": row["source_dimensions"], "source_rgb_sha256": source_rgb_sha256,
                "colour_managed_rgb_sha256": managed_rgb_sha256, "colour_conversion": colour["conversion"],
                "colour_roundtrip_max_channel_error": colour["roundtrip_max_channel_error"],
                "image_payload_sha256": derivative["sha256"], "image_rgb_sha256": derivative["rgb_sha256"],
                "image_dimensions": derivative["dimensions"]}
        if cam is not None:
            files[raw_name] = cam["sha256"]
            item.update(cam_original_path=raw_name, cam_payload_sha256=cam["sha256"],
                        cam_rgb_sha256=cam["rgb_sha256"], cam_dimensions=cam["dimensions"])
        records.append(item)
    bundle = {"version": BUNDLE_VERSION, "export_policy": EXPORT_POLICY,
              "dataset_attribution": deepcopy(DATASET_ATTRIBUTION), "status": "provisional_exploratory_only",
              "notice": NOTICE, "mgi_schema": list(vp.MGI_GRADES),
              "qualified_labels_approved": False, "participant_independence_verified": False,
              "final_research_approved": False, "source_draft_sha256": plan["source_draft_sha256"],
              "source_plan_sha256": json_digest(plan), "packaging_authorization": deepcopy(authorization),
              "protected_groups": plan["protected_groups"], "uncertain_groups": plan["uncertain_groups"],
              "cam_ids": plan["cam_ids"], "files": files, "records": records}
    (output / "bundle_manifest.json").write_text(json.dumps(bundle, indent=2, allow_nan=False) + "\n")
    validate_bundle(output)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as target:
        for name in sorted(set(files) | {"bundle_manifest.json"}):
            target.write(output / name, name)
    return {"notice": NOTICE, "archive": str(archive), "archive_sha256": sha256(archive),
            "bundle_manifest_sha256": sha256(output / "bundle_manifest.json")}


def bundle_records(bundle):
    return _bundle_records(bundle, BUNDLE_VERSION, EXPORT_POLICY, DATASET_ATTRIBUTION, _legacy_colour)


def _legacy_colour(row):
    # The v3 API retains its original hard stop; never dispatch by input version.
    if (row.get("colour_conversion") not in {"untagged_srgb_identity", "icc_to_srgb"}
            or type(row.get("colour_roundtrip_max_channel_error")) is not int
            or not 0 <= row["colour_roundtrip_max_channel_error"] <= ROUNDTRIP_LIMIT
            or (row["colour_conversion"] == "untagged_srgb_identity"
                and (row.get("source_rgb_sha256") != row.get("colour_managed_rgb_sha256")
                     or row["colour_roundtrip_max_channel_error"] != 0))):
        raise ValueError("Colour-managed provenance missing or inconsistent")


def _bundle_records(bundle, version, export_policy, attribution, colour_validator):
    """Shared structure checks; callers must select one explicit version/policy."""
    if (bundle.get("version") != version or bundle.get("export_policy") != export_policy
            or bundle.get("dataset_attribution") != attribution
            or bundle.get("status") != "provisional_exploratory_only" or bundle.get("notice") != NOTICE
            or bundle.get("mgi_schema") != list(vp.MGI_GRADES)
            or any(bundle.get(k) is not False for k in ["qualified_labels_approved", "participant_independence_verified", "final_research_approved"])):
        raise ValueError("Provisional five-grade bundle required")
    blocked = set(bundle["protected_groups"] + bundle["uncertain_groups"])
    paths, ids, groups, expected_files = set(), set(), set(), set()
    for row in bundle["records"]:
        split = row.get("original_split")
        if split not in EXPECTED_COUNTS:
            raise ValueError("Test/nondevelopment bundle record")
        identifier = row.get("source_record_id", "")
        if not re.fullmatch(split + r"/\d{5}", identifier) or identifier in ids:
            raise ValueError("Invalid/duplicate source ID")
        if (row.get("label_status") != "provisional" or row.get("qualified_label_approved") is not False
                or row.get("participant_id") is not None or type(row.get("provisional_mgi_grade")) is not int
                or row["provisional_mgi_grade"] not in vp.MGI_GRADES):
            raise ValueError("Unverified/invalid provisional label provenance")
        group = row.get("content_group_id")
        if identifier in NP015_IDS or not group or group in blocked or group in groups:
            raise ValueError("Duplicate/protected/uncertain content group")
        name = row["image_path"]
        relative_path(name)
        if name != "images/" + identifier + ".png" or name in paths:
            raise ValueError("Bundle image path mismatch")
        original = row["original_image_path"]
        if original != f"Dataset/{split}/Images/{identifier.split('/')[1]}.jpg":
            raise ValueError("Original development provenance mismatch")
        hashes = ["source_sha256", "source_rgb_sha256", "colour_managed_rgb_sha256", "image_payload_sha256", "image_rgb_sha256"]
        dimensions = ["source_dimensions", "image_dimensions"]
        colour_validator(row)
        expected_files.add(name)
        if identifier in bundle["cam_ids"]:
            raw = row.get("cam_original_path")
            if split != "Validation" or raw != "cam/" + identifier + ".png":
                raise ValueError("Grad-CAM original must be fixed development Validation")
            hashes += ["cam_payload_sha256", "cam_rgb_sha256"]
            dimensions += ["cam_dimensions"]
            if (row.get("cam_dimensions") != row.get("source_dimensions")
                    or row.get("cam_rgb_sha256") != row.get("colour_managed_rgb_sha256")
                    or bundle["files"].get(raw) != row.get("cam_payload_sha256")):
                raise ValueError("Grad-CAM export/source provenance mismatch")
            expected_files.add(raw)
        elif "cam_original_path" in row:
            raise ValueError("Unexpected Grad-CAM original")
        if (any(not isinstance(row.get(k), str) or not re.fullmatch(r"[0-9a-f]{64}", row[k]) for k in hashes)
                or any(not isinstance(row.get(k), list) or len(row[k]) != 2
                       or any(type(v) is not int or v <= 0 for v in row[k]) for k in dimensions)
                or bundle["files"].get(name) != row["image_payload_sha256"]):
            raise ValueError("Export hashes/dimensions missing or inconsistent")
        width, height = row["source_dimensions"]
        scale = min(224 / width, 224 / height)
        if row["image_dimensions"] != [max(1, min(224, round(width * scale))),
                                       max(1, min(224, round(height * scale)))]:
            raise ValueError("Derivative geometry differs from frozen preprocessing")
        ids.add(identifier); paths.add(name); groups.add(group)
    if not paths or not set(bundle["cam_ids"]).issubset(ids) or set(bundle["files"]) != expected_files:
        raise ValueError("Payload inventory mismatch")
    return deepcopy(bundle["records"])


def validate_bundle(root):
    return _validate_bundle(root, bundle_records)


def _validate_bundle(root, record_validator):
    manifest = safe_file(root, "bundle_manifest.json")
    bundle = json.loads(manifest.read_text())
    records = record_validator(bundle)
    expected = set(bundle["files"]) | {"bundle_manifest.json"}
    allowed_directories = {str(p) for name in expected for p in PurePosixPath(name).parents if str(p) != "."}
    actual = set()
    for path in Path(root).rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlink in bundle")
        name = path.relative_to(root).as_posix()
        relative_path(name)
        if path.is_file():
            actual.add(name)
        elif name not in allowed_directories:
            raise ValueError("Unexpected directory in bundle")
    if actual != expected:
        raise ValueError("Unexpected/missing payload; Test and extra files forbidden")
    for name, expected_hash in bundle["files"].items():
        if sha256(safe_file(root, name)) != expected_hash:
            raise ValueError("Bundle payload hash mismatch")
    for row in records:
        verify_rgb_export(safe_file(root, row["image_path"]), {
            "sha256": row["image_payload_sha256"], "rgb_sha256": row["image_rgb_sha256"],
            "dimensions": row["image_dimensions"]})
        if "cam_original_path" in row:
            verify_rgb_export(safe_file(root, row["cam_original_path"]), {
                "sha256": row["cam_payload_sha256"], "rgb_sha256": row["cam_rgb_sha256"],
                "dimensions": row["cam_dimensions"]})
    return bundle, records


def extract_bundle(archive, output, authorization, opt_in=False):
    """Future Colab extraction: only an explicitly run-authorised isolated bundle."""
    authorise(authorization, "run_exploratory", {"archive_sha256": sha256(archive)}, opt_in)
    destination = Path(output)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Fresh extraction directory required")
    if any(parent.is_symlink() for parent in destination.parents):
        raise ValueError("Symlink extraction parent")
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)) or len(names) > 1000 or sum(e.file_size for e in entries) > 1024**3:
            raise ValueError("Archive duplicate/size limit")
        for entry in entries:
            relative_path(entry.filename)
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if entry.is_dir() or mode not in {0, stat.S_IFREG}:
                raise ValueError("Archive links/directories forbidden")
        meta = source.getinfo("bundle_manifest.json")
        if meta.file_size > 8 * 1024**2:
            raise ValueError("Bundle manifest size limit")
        raw = source.read(meta)
        if hashlib.sha256(raw).hexdigest() != authorization.get("bundle_manifest_sha256"):
            raise ValueError("Authorised bundle manifest hash mismatch")
        bundle = json.loads(raw)
        bundle_records(bundle)
        if set(names) != set(bundle["files"]) | {"bundle_manifest.json"}:
            raise ValueError("Unexpected archive contents")
        destination.mkdir(parents=True)
        for entry in entries:
            target = destination / entry.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(entry) as inp, target.open("xb") as out:
                shutil.copyfileobj(inp, out)
    validate_bundle(destination)
    return destination


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dry-run first; no automatic data packaging")
    parser.add_argument("--draft", required=True)
    parser.add_argument("--hash-inventory", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--authorization")
    parser.add_argument("--opt-in", action="store_true")
    args = parser.parse_args()
    plan = prepare_plan(args.draft, args.hash_inventory)
    if args.package:
        authorization = json.loads(Path(args.authorization).read_text()) if args.authorization else None
        result = package_development(plan, args.source_root, args.output, authorization, args.opt_in)
    else:
        result = dry_run(plan, args.source_root)
        output = new_ignored_output(args.output, "data")
        output.mkdir(parents=True)
        (output / "source_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
        (output / "dry_run.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
