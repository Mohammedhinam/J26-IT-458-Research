"""Bounded extraction/integrity audit only. No label adjudication or training."""

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from src.vision.audit_gingivitis import CAPTIONS, EXPECTED, audit_inventory, caption_grades

MAX_TOTAL_BYTES = 10 * 1024**3
MAX_FILE_BYTES = 100 * 1024**2
MAX_ENTRIES = 3000
DISK_RESERVE = 2 * 1024**3
MAX_PIXELS = 80_000_000


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_entries(entries, free_bytes):
    """Fail closed on links, unexpected paths, collisions and size limits."""
    if len(entries) > MAX_ENTRIES:
        raise ValueError("Archive entry limit exceeded")
    seen = set()
    folded = set()
    total = 0
    image_counts = Counter()
    allowed_directories = {"Dataset"}
    for split in EXPECTED:
        allowed_directories.update({f"Dataset/{split}", f"Dataset/{split}/Images", f"Dataset/{split}/Labels"})
    for entry in entries:
        name, kind, size = entry["name"], entry["type"], entry["size"]
        path = PurePosixPath(name)
        if (path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name
                or " link to " in name or " -> " in name
                or str(path) != name or name in seen or name.casefold() in folded):
            raise ValueError(f"Unsafe or duplicate path: {name}")
        seen.add(name)
        folded.add(name.casefold())
        if kind == "d":
            if name not in allowed_directories or size != 0:
                raise ValueError(f"Unexpected directory: {name}")
        elif kind == "-":
            parts = path.parts
            is_payload = (len(parts) == 4 and parts[0] == "Dataset" and parts[1] in EXPECTED
                          and ((parts[2] == "Images" and path.suffix.lower() == ".jpg")
                               or (parts[2] == "Labels" and path.suffix == ".txt")))
            is_caption = name in {f"Dataset/{s}/{stem}_captions.csv" for s, stem in CAPTIONS.items()}
            if not (is_payload or is_caption):
                raise ValueError(f"Unexpected file/link metadata: {name}")
            if not 0 <= size <= MAX_FILE_BYTES:
                raise ValueError(f"Member size limit exceeded: {name}")
            total += size
            if is_payload and parts[2] == "Images":
                image_counts[parts[1]] += 1
        else:
            raise ValueError(f"Link or special entry prohibited: {name}")
    if total > MAX_TOTAL_BYTES or free_bytes < total + DISK_RESERVE:
        raise ValueError("Extraction size or free-space limit exceeded")
    if dict(image_counts) != EXPECTED:
        raise ValueError(f"Image entry counts differ from proposal: {dict(image_counts)}")
    # A regular file must never be an ancestor of another member.
    regular = {e["name"] for e in entries if e["type"] == "-"}
    if any(str(parent) in regular for e in entries for parent in PurePosixPath(e["name"]).parents):
        raise ValueError("File/directory ancestor collision")
    return total


def scan_archive(archive):
    output = subprocess.run(["/usr/bin/bsdtar", "-tvf", str(archive)],
                            check=True, capture_output=True, text=True).stdout
    entries = []
    for line in output.splitlines():
        fields = line.split(maxsplit=8)
        if len(fields) != 9 or not fields[4].isdigit():
            raise ValueError("Unrecognised bsdtar metadata; stop rather than guess")
        entries.append({"name": fields[8], "type": fields[0][0], "size": int(fields[4])})
    return entries


def integrity_read(archive, expected_bytes, regular_names):
    """Read every member before extraction; fail on decoder/CRC errors or overflow."""
    with tempfile.TemporaryFile() as errors:
        # RAR directories have metadata but no payload. Ask for every regular file explicitly.
        process = subprocess.Popen(["/usr/bin/bsdtar", "-xOf", str(archive), *regular_names],
                                   stdout=subprocess.PIPE, stderr=errors)
        total = 0
        try:
            for chunk in iter(lambda: process.stdout.read(1024**2), b""):
                total += len(chunk)
                if total > expected_bytes or total > MAX_TOTAL_BYTES:
                    raise ValueError("Integrity stream exceeded declared extraction size")
            code = process.wait()
            errors.seek(0)
            error_text = errors.read().decode("utf-8", errors="replace")
            if code != 0 or error_text or total != expected_bytes:
                raise ValueError(f"Integrity read failed: exit={code}, bytes={total}, stderr={error_text}")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdout.close()
    return total


def extract_new(archive, staging, entries):
    """Existing staging is a blocker. Approved metadata contains no links."""
    if staging.exists() or staging.is_symlink():
        raise FileExistsError(f"Do not overwrite existing staging: {staging}")
    for parent in staging.parents:
        if parent.is_symlink():
            raise ValueError(f"Symlink staging ancestor prohibited: {parent}")
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir()
    subprocess.run(["/usr/bin/bsdtar", "-xkf", str(archive), "-C", str(staging),
                    "--no-same-owner", "--no-same-permissions", "--no-acls", "--no-xattrs", "--no-fflags",
                    *[entry["name"] for entry in entries if entry["type"] == "-"]],
                   check=True, capture_output=True)
    verify_extraction(staging, entries)


def verify_extraction(staging, entries):
    expected = {e["name"]: e["size"] for e in entries if e["type"] == "-"}
    actual = {}
    for path in staging.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Extracted symlink prohibited: {path}")
        if path.is_file():
            actual[path.relative_to(staging).as_posix()] = path.stat().st_size
    if actual != expected:
        raise ValueError("Extracted file paths/sizes differ from archive metadata; preserve staging for inspection")
    return actual


def image_evidence(path):
    """Verify the original, decode RGB in memory, and compute audit fingerprints."""
    from PIL import Image

    byte_hash = sha256_file(path)
    with Image.open(path) as image:
        if image.width * image.height > MAX_PIXELS:
            raise ValueError("Image pixel limit exceeded")
        image.verify()
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        mode = image.mode
        format_name = image.format
        exif_image_id_present = bool(image.getexif().get(42016))
        rgb = image.convert("RGB")
        # Include shape: equal pixels at a different geometry are not identical images.
        pixel_hash = hashlib.sha256(f"{width}x{height}:RGB:".encode() + rgb.tobytes()).hexdigest()
        small = rgb.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(small.get_flattened_data())
        bits = 0
        for y in range(8):
            for x in range(8):
                bits = (bits << 1) | int(pixels[y * 9 + x] > pixels[y * 9 + x + 1])
    return {"sha256": byte_hash, "pixel_sha256": pixel_hash, "dhash": f"{bits:016x}",
            "width": width, "height": height, "mode": mode, "format": format_name,
            "exif_image_id_present": exif_image_id_present, "decode_ok": True}


def yolo_evidence(path):
    """Inspect raw annotation codes; the published mapping remains a hypothesis."""
    counts = Counter()
    issues = []
    if not path.is_file():
        return counts, ["missing_annotation"]
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        fields = line.split()
        try:
            values = [float(value) for value in fields]
            if len(values) != 5 or not all(math.isfinite(value) for value in values):
                raise ValueError()
            code, x, y, width, height = values
            if not code.is_integer() or not 0 <= code <= 6:
                raise ValueError()
            counts[int(code)] += 1
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1 and 0 < height <= 1):
                issues.append("invalid_annotation_coordinates")
        except ValueError:
            issues.append("invalid_annotation_row")
    if not counts:
        issues.append("empty_annotation")
    if counts and (counts[0] != 1 or counts[1] != 1):
        issues.append("annotation_roi_count_review")
    if counts and sum(count for code, count in counts.items() if code >= 2) != 12:
        issues.append("annotation_tooth_count_review")
    return counts, sorted(set(issues))


def duplicate_groups(rows, key):
    groups = defaultdict(list)
    for row in rows:
        if row.get(key):
            groups[row[key]].append(row)
    results = []
    for digest, group in groups.items():
        if len(group) > 1:
            results.append({"key": key, "fingerprint": digest, "cross_split": len({r['split'] for r in group}) > 1,
                            "paths": [row["image_path"] for row in group]})
    return results


def identity_metadata_review(staging, image_rows):
    """Inspect metadata headers; image/camera IDs are never assumed to be patient IDs."""
    from PIL import Image

    records = []
    fields = {270: "ImageDescription", 37510: "UserComment", 42016: "ImageUniqueID",
              42032: "CameraOwnerName", 42033: "BodySerialNumber"}
    for row in image_rows:
        with Image.open(staging / row["image_path"]) as image:
            exif = image.getexif()
            nested = exif.get_ifd(34665)
            record = {"image_path": row["image_path"], "split": row["split"],
                      "gps_metadata_present": bool(exif.get_ifd(34853)), "participant_id": "",
                      "participant_status": "no_documented_participant_identifier"}
            for code, name in fields.items():
                value = nested.get(code, exif.get(code, ""))
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="replace").replace("ASCII", "")
                text = str(value).replace("\x00", "").strip()
                record[name + "_nonempty"] = bool(text)
                record[name + "_value_sha256"] = hashlib.sha256(text.encode()).hexdigest() if text else ""
            records.append(record)
    return records


def flag_duplicate_caption_conflicts(result):
    """Same bytes with different caption maxima need review, never a voting repair."""
    lookup = {row["image_path"]: row for row in result["manifest"]}
    for group in result["duplicate_groups"]:
        if group["key"] != "sha256":
            continue
        maxima = set()
        for path in group["paths"]:
            maxima.update(value for value in lookup[path]["caption_maxima"] if value is not None)
        if len(maxima) > 1:
            for path in group["paths"]:
                row = lookup[path]
                row["status"] = "needs_review"
                row["issues"].append("duplicate_caption_target_disagreement")
                result["anomalies"].append({"kind": "duplicate_caption_target_disagreement",
                                             "split": row["split"], "file": path})


def audit_extracted(staging, entries):
    captions = {}
    for split, stem in CAPTIONS.items():
        with (staging / f"Dataset/{split}/{stem}_captions.csv").open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"FileName", "#", "BS1"} <= set(reader.fieldnames or []):
                raise ValueError("Required caption fields missing")
            captions[split] = list(reader)
    result = audit_inventory([entry["name"] for entry in entries], captions)
    anomalies = list(result["anomalies"])
    grouped_captions = defaultdict(list)
    for split, rows in captions.items():
        for row in rows:
            grouped_captions[(split, row["FileName"])].append(row)
    annotation_totals = {split: Counter() for split in EXPECTED}
    for i, row in enumerate(result["manifest"]):
        path = staging / row["image_path"]
        try:
            row.update(image_evidence(path))
        except Exception as error:
            row.update({"sha256": sha256_file(path), "decode_ok": False, "decode_error": str(error)})
            row["status"] = "needs_review"
            row["issues"].append("image_decode_failed")
            anomalies.append({"kind": "image_decode_failed", "split": row["split"], "file": path.name})
        annotation = staging / "Dataset" / row["split"] / "Labels" / (path.stem + ".txt")
        codes, issues = yolo_evidence(annotation)
        annotation_totals[row["split"]].update(codes)
        row["raw_yolo_codes"] = sorted(codes)
        row["raw_yolo_code_counts"] = dict(codes)
        mgi_codes = [code for code in codes if code >= 2]
        row["hypothetical_yolo_max_if_table2"] = max(mgi_codes) - 2 if mgi_codes else None
        row["annotation_issues"] = issues
        row["participant_id"] = ""
        row["participant_status"] = "not_supplied"
        variants = sorted(grouped_captions[(row["split"], path.name)], key=lambda r: r["#"])
        row["caption_grade_sets"] = [sorted(caption_grades(r["BS1"])[0]) for r in variants]
        row["caption_maxima"] = [max(s) if s else None for s in row["caption_grade_sets"]]
        row["non_inflamed_wording"] = any("non-inflamed" in r["BS1"].lower() or "not inflamed" in r["BS1"].lower() for r in variants)
        for issue in issues:
            row["status"] = "needs_review"
            row["issues"].append(issue)
            anomalies.append({"kind": issue, "split": row["split"], "file": path.name})
        if row["mgi_max"] is not None and row["hypothetical_yolo_max_if_table2"] != row["mgi_max"]:
            row["status"] = "needs_review"
            row["issues"].append("caption_yolo_hypothesis_disagreement")
            anomalies.append({"kind": "caption_yolo_hypothesis_disagreement", "split": row["split"], "file": path.name})
        if (i + 1) % 100 == 0:
            print(f"Audited {i + 1}/{len(result['manifest'])} images", flush=True)
    duplicates = []
    for key in ["sha256", "pixel_sha256", "dhash"]:
        duplicates.extend(duplicate_groups(result["manifest"], key))
    for group in duplicates:
        for row in result["manifest"]:
            if row["image_path"] in group["paths"]:
                row["status"] = "needs_review"
                reason = "near_duplicate_candidate" if group["key"] == "dhash" else "duplicate_content"
                row["issues"].append(reason)
                anomalies.append({"kind": reason, "split": row["split"], "file": row["image_path"]})
    result.update({"anomalies": anomalies, "duplicate_groups": duplicates,
                   "annotation_totals": {s: dict(c) for s, c in annotation_totals.items()}})
    flag_duplicate_caption_conflicts(result)
    return result


def write_csv(path, rows, fields):
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row.get(key), ensure_ascii=False) if isinstance(row.get(key), (list, dict))
                             else row.get(key, "") for key in fields})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    args = parser.parse_args()
    repo = Path.cwd().resolve()
    if subprocess.check_output(["git", "branch", "--show-current"], text=True).strip() != "vinuthan":
        raise ValueError("Stop: branch must be vinuthan")
    base = repo / "data/vision/gingivitis"
    subprocess.run(["git", "check-ignore", "--quiet", str(base / "staging-probe/Dataset/example.jpg")], check=True)
    originals = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in [args.archive, args.backup]}
    entries = scan_archive(args.archive)
    free = shutil.disk_usage(repo).free
    total = validate_entries(entries, free)
    print(f"Preflight: {len(entries)} entries; unpacked={total}; free={free}; no links/unsafe paths", flush=True)
    primary_hash = sha256_file(args.archive)
    print("Primary SHA256:", primary_hash, flush=True)
    backup_hash = sha256_file(args.backup)
    print("Backup SHA256:", backup_hash, "MATCH" if backup_hash == primary_hash else "MISMATCH", flush=True)
    checked = integrity_read(args.archive, total, [e["name"] for e in entries if e["type"] == "-"])
    print(f"Full archive integrity read PASS; {checked} bytes; no bsdtar errors", flush=True)
    if shutil.disk_usage(repo).free < total + DISK_RESERVE:
        raise ValueError("Disk space changed; stop before extraction")
    for path, state in originals.items():
        current = Path(path).stat()
        if (current.st_size, current.st_mtime_ns) != state:
            raise ValueError("Source archive changed during preflight")
    staging = base / f"staging-{primary_hash}"
    print("Extracting to new staging:", staging, flush=True)
    extract_new(args.archive, staging, entries)
    print("Extracted paths and sizes MATCH archive metadata", flush=True)
    result = audit_extracted(staging, entries)
    identity = identity_metadata_review(staging, result["manifest"])
    write_csv(staging / "metadata_identity_review.csv", identity, list(identity[0]))
    audit = staging / "audit"
    audit.mkdir()
    metadata = {"primary": str(args.archive), "backup": str(args.backup), "primary_sha256": primary_hash,
                "backup_sha256": backup_hash, "archives_identical": primary_hash == backup_hash,
                "unpacked_bytes": total, "integrity_read_bytes": checked, "disk_free_before": free,
                "limits": {"total": MAX_TOTAL_BYTES, "file": MAX_FILE_BYTES, "entries": MAX_ENTRIES,
                           "reserve": DISK_RESERVE, "pixels": MAX_PIXELS},
                "staging": str(staging), "entries": entries, "participant_overlap": "NOT LOCALLY VERIFIABLE",
                "training_started": False, "labels_adjudicated": False}
    with (audit / "integrity_results.json").open("x", encoding="utf-8") as handle:
        json.dump({"metadata": metadata, "result": result}, handle, indent=2)
    fields = sorted({key for row in result["manifest"] for key in row})
    write_csv(audit / "split_manifest.csv", result["manifest"], fields)
    write_csv(audit / "duplicates_anomalies.csv", result["anomalies"], ["kind", "split", "file"])
    distribution = []
    for split in EXPECTED:
        rows = [r for r in result["manifest"] if r["split"] == split]
        for grade in range(5):
            distribution.append({"split": split, "grade": grade,
                                 "caption_provisional_count": sum(r["mgi_max"] == grade for r in rows),
                                 "no_current_issue_count": sum(r["mgi_max"] == grade and r["status"] == "provisional" for r in rows)})
    write_csv(audit / "label_distribution.csv", distribution, list(distribution[0]))
    review = [{"image_path": r["image_path"], "issues": r["issues"], "decision": "pending", "reviewer": ""}
              for r in result["manifest"] if r["status"] == "needs_review"]
    write_csv(audit / "label_review.csv", review, ["image_path", "issues", "decision", "reviewer"])
    for path, state in originals.items():
        current = Path(path).stat()
        if (current.st_size, current.st_mtime_ns) != state:
            raise ValueError("Original archive changed; investigate")
    print("AUDIT_COMPLETE", audit, flush=True)
    print("Decode successes:", sum(r["decode_ok"] for r in result["manifest"]), flush=True)
    print("Duplicate groups:", Counter(g["key"] for g in result["duplicate_groups"]), flush=True)
    print("Annotation totals:", result["annotation_totals"], flush=True)
    print("Needs review:", sum(r["status"] == "needs_review" for r in result["manifest"]), flush=True)


if __name__ == "__main__":
    main()
