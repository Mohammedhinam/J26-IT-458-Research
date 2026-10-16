"""Prepare only already-produced v3 demonstration outputs; never run a model.

This reads the verified result archive, not source dental images or checkpoints.
"""

import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib


CASE_IDS = ("00733", "00734", "00766")
VIEWS = ("original", "heatmap", "overlay")
ARCHIVE_SHA256 = "c79f16cf59b268f86a5a4c4b6a3482636e374cb67629895f38e55dbb1eaf0d70"
ARCHIVE_NAME = "pp1_b1_lastblock_v3_20261015T155608744170Z_results.zip"


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_preview_png(payload):
    """Check structure/geometry/opaque-metadata absence without decoding pixels."""
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Expected saved PNG preview")
    offset, width, height, ended, seen_data = 8, None, None, False, False
    while offset < len(payload):
        if len(payload) - offset < 12:
            raise ValueError("Truncated PNG")
        length = struct.unpack(">I", payload[offset:offset + 4])[0]
        kind = payload[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(payload) or kind not in (b"IHDR", b"IDAT", b"IEND"):
            raise ValueError("Unsafe/truncated saved PNG or opaque metadata")
        data = payload[offset + 8:offset + 8 + length]
        expected = struct.unpack(">I", payload[offset + 8 + length:end])[0]
        if zlib.crc32(kind + data) & 0xffffffff != expected:
            raise ValueError("PNG checksum mismatch")
        if kind == b"IHDR":
            if offset != 8 or length != 13:
                raise ValueError("Invalid PNG header")
            width, height, depth, colour, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            if not (0 < width <= 2400 and 0 < height <= 2400) or (depth, colour, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise ValueError("Expected bounded RGB8 saved preview")
        elif kind == b"IDAT":
            if width is None:
                raise ValueError("Image data before header")
            seen_data = True
        else:
            if length or end != len(payload) or not seen_data:
                raise ValueError("Unexpected trailing/missing PNG payload")
            ended = True
        offset = end
    if not ended:
        raise ValueError("Incomplete PNG")
    return [width, height]


def prepare_saved_examples(archive_path, output_dir, expected_sha256=ARCHIVE_SHA256):
    """Fail before writing unless the pinned archive and every selected item pass."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError("Saved-demo output already exists; preserve it")
    if digest_file(archive_path) != expected_sha256:
        raise ValueError("Result archive hash mismatch")
    assets, examples = {}, []
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Duplicate archive member")
        hashes = json.loads(archive.read("results_file_hashes.json"))

        def verified(name):
            info = archive.getinfo(name)
            if info.file_size > 16 * 1024 * 1024:
                raise ValueError("Unexpected saved-preview size")
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != hashes.get(name):
                raise ValueError("Saved output hash mismatch: " + name)
            return payload

        predictions = json.loads(verified("validation_predictions_best.json"))
        if predictions["grades"] != [1, 2, 3, 4]:
            raise ValueError("Unexpected exploratory grade mapping")
        records = predictions["records"]
        by_id = {row["source_record_id"]: row for row in records}
        if len(by_id) != len(records) or any(row["original_split"] != "Validation" for row in records):
            raise ValueError("Expected unique saved Validation records only")
        for case in CASE_IDS:
            row = by_id["Validation/" + case]
            dimensions = []
            for view in VIEWS:
                source = f"gradcam/Validation_{case}/{view}.png"
                payload = verified(source)
                dimensions.append(check_preview_png(payload))
                assets[f"{case}_{view}.png"] = payload
            if len({tuple(d) for d in dimensions}) != 1:
                raise ValueError("Saved Grad-CAM views are misaligned")
            examples.append({"id": "Validation/" + case, "predicted_grade": row["predicted_mgi_grade"],
                             "provisional_label": row["provisional_mgi_grade"],
                             "probabilities": row["probabilities_mgi1_to4"],
                             "dimensions": dimensions[0],
                             "views": {view: f"{case}_{view}.png" for view in VIEWS}})
    manifest = {
        "mode": "saved completed experiment only; no new prediction or training",
        "notice": "Provisional labels; non-clinical; non-final; participant independence unverified.",
        "whole_image_mgi0_supported": False, "source_archive_sha256": expected_sha256,
        "examples": examples,
        "files": {name: hashlib.sha256(payload).hexdigest() for name, payload in assets.items()},
        "attribution": "Duy et al. (2024), Mendeley 10.17632/3253gj88rr.1, CC BY 4.0.",
        "licence_url": "https://creativecommons.org/licenses/by/4.0/",
        "transformation_notice": "Existing B1 display previews and model Grad-CAM outputs; original source files untouched.",
        "heatmap_meaning": "Model attention for the predicted grade, not clinical inflammation boundaries.",
    }
    output_dir.mkdir(parents=True)
    for name, payload in assets.items():
        (output_dir / name).write_bytes(payload)
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
