"""Build an isolated, allowlisted sRGB tooth-ROI data package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import os
import zipfile
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageCms

from src.vision.audit_gingivitis import caption_grades
from src.vision.roi_workflow_v1 import (
    RAW_CLASS_TO_MGI,
    box_to_xyxy,
    detector_label_for_tooth_box,
    parse_yolo_label_lines,
)


REPO = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO / "data/vision/roi_tooth_v1_20261017"
DEFAULT_BUNDLE = REPO / "data/vision/pp1_b1_dev_v1_20261015T085436527238Z/bundle_manifest.json"
DEFAULT_PROTOCOL = REPO / "data/vision/training680_efficientnet_probe_v1_20261016T151400472912/protocol.json"
DEFAULT_SOURCE = REPO / "data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/Dataset"
MAX_IMAGE_SIDE = 1600
CROP_SIZE = 224
CROP_PADDING = 0.15
JPEG_QUALITY = 95
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _selected_rows(bundle: dict) -> tuple[list[dict], dict[str, int]]:
    """Select only the frozen safe Training and Validation manifest records."""

    selected = [
        row for row in bundle["records"]
        if row.get("original_split") in ("Training", "Validation")
    ]
    split_counts = Counter(row["original_split"] for row in selected)
    if dict(split_counts) != {"Training": 680, "Validation": 53}:
        raise ValueError(f"expected the frozen 680/53 selection; got {dict(split_counts)}")
    if any("Test" in row.get("source_record_id", "") for row in selected):
        raise ValueError("protected split names are not allowed in this package")
    if any(row.get("qualified_label_approved") for row in selected):
        raise ValueError("the manifest status changed; stop and review before packaging")
    if any(row.get("label_status") != "provisional" for row in selected):
        raise ValueError("all package labels must retain the provisional status")
    if any(row.get("provisional_mgi_grade") not in (1, 2, 3, 4) for row in selected):
        raise ValueError("the current safe bundle has no supported whole-image grade 0")
    if any(row.get("source_record_id") in bundle.get("np015_excluded", []) for row in selected):
        raise ValueError("an identity-excluded source record appeared in the selection")
    group_ids = [row["content_group_id"] for row in selected]
    if len(group_ids) != len(set(group_ids)):
        raise ValueError("duplicate content group found in the package selection")
    if set(group_ids) & set(bundle.get("protected_groups", [])):
        raise ValueError("a protected content group appeared in the package selection")
    if set(group_ids) & set(bundle.get("uncertain_groups", [])):
        raise ValueError("an uncertain content group appeared in the package selection")
    if len({r["content_group_id"] for r in selected if r["original_split"] == "Training"}
           & {r["content_group_id"] for r in selected if r["original_split"] == "Validation"}):
        raise ValueError("a content group crosses the selected source splits")
    return sorted(selected, key=lambda row: row["source_record_id"]), dict(split_counts)


def _read_captions(path: Path, selected_ids: set[str], split: str) -> dict[str, list[dict]]:
    """Keep caption text only for image IDs present in the safe manifest."""

    output: dict[str, list[dict]] = {source_id: [] for source_id in selected_ids}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"caption CSV has no header: {path}")
        filename_key = next((key for key in reader.fieldnames if key.lstrip("\ufeff") == "FileName"), None)
        caption_key = next((key for key in reader.fieldnames if key.lstrip("\ufeff") == "BS1"), None)
        if filename_key is None or caption_key is None:
            raise ValueError(f"caption CSV is missing FileName or BS1: {path}")
        for row in reader:
            filename = (row.get(filename_key) or "").strip()
            record_id = f"{split}/{Path(filename).stem}"
            if record_id not in output:
                continue
            text = row.get(caption_key) or ""
            grade_set, parse_issue = caption_grades(text)
            if parse_issue:
                raise ValueError(
                    f"caption parsing requires review for {record_id}, variant {row.get('#')}: {parse_issue}"
                )
            grades = sorted(grade_set)
            maximum = max(grades) if grades else None
            output[record_id].append({
                "caption_index": (row.get("#") or "").strip(),
                "caption_text": text,
                "parsed_grades": grades,
                "caption_max": maximum,
            })
    for record_id, rows in output.items():
        if len(rows) != 3:
            raise ValueError(f"{record_id}: expected three caption variants, got {len(rows)}")
    return output


def _convert_to_srgb(source: Image.Image, output_profile: ImageCms.ImageCmsProfile) -> Image.Image:
    """Honor the embedded source profile before the detector sees 8-bit RGB."""

    profile_bytes = source.info.get("icc_profile")
    if not profile_bytes:
        raise ValueError("source JPEG has no embedded ICC profile")
    source_profile = ImageCms.ImageCmsProfile(BytesIO(profile_bytes))
    converted = ImageCms.profileToProfile(
        source.convert("RGB"),
        source_profile,
        output_profile,
        renderingIntent=0,
        outputMode="RGB",
    )
    return converted


def _save_model_image(source_path: Path, destination: Path, srgb_profile: ImageCms.ImageCmsProfile) -> tuple[int, int, str, str]:
    with Image.open(source_path) as source:
        if source.format != "JPEG" or source.mode != "RGB":
            raise ValueError(f"expected RGB JPEG, found {source.format}/{source.mode}: {source_path}")
        if source.getexif().get(274, 1) != 1:
            raise ValueError(f"non-identity EXIF orientation is not supported: {source_path}")
        source_icc = source.info.get("icc_profile", b"")
        converted = _convert_to_srgb(source, srgb_profile)
        converted.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        converted.save(
            destination,
            format="JPEG",
            quality=JPEG_QUALITY,
            subsampling=0,
            optimize=True,
            icc_profile=srgb_profile.tobytes(),
        )
        return (
            converted.width,
            converted.height,
            hashlib.sha256(source_icc).hexdigest(),
            hashlib.sha256(srgb_profile.tobytes()).hexdigest(),
        )


def _save_roi_crops(
    model_image: Path,
    boxes,
    record_id: str,
    split: str,
    group_id: str,
    outer_fold: int | None,
    output_root: Path,
    crop_rows: list[dict],
) -> None:
    with Image.open(model_image) as source:
        image = source.convert("RGB")
        for tooth_index, box in enumerate(box for box in boxes if box.mgi_grade is not None):
            x1, y1, x2, y2 = box_to_xyxy(
                box, image.width, image.height, padding_fraction=CROP_PADDING
            )
            crop = image.crop((x1, y1, x2, y2)).resize(
                (CROP_SIZE, CROP_SIZE), Image.Resampling.LANCZOS
            )
            crop_id = f"{record_id.replace('/', '_')}_{tooth_index:02d}"
            crop_path = output_root / "crops" / split / f"{crop_id}.jpg"
            crop_path.parent.mkdir(parents=True, exist_ok=True)
            crop.save(crop_path, format="JPEG", quality=JPEG_QUALITY, subsampling=0, optimize=True)
            crop_rows.append({
                "crop_id": crop_id,
                "crop_path": crop_path.relative_to(output_root).as_posix(),
                "parent_record_id": record_id,
                "source_split": split,
                "content_group_id": group_id,
                "outer_fold": outer_fold,
                "tooth_index": tooth_index,
                "raw_source_class_id": box.class_id,
                "provisional_mgi_grade": box.mgi_grade,
                "source_box_xywh_normalized": [
                    box.center_x, box.center_y, box.width, box.height
                ],
                "crop_padding_fraction": CROP_PADDING,
                "crop_size": CROP_SIZE,
            })


def build_package(
    bundle_path: Path = DEFAULT_BUNDLE,
    protocol_path: Path = DEFAULT_PROTOCOL,
    source_root: Path = DEFAULT_SOURCE,
    output_root: Path = DEFAULT_ROOT / "dataset",
) -> dict:
    """Create a new package using the pinned 680/53 development allowlist."""

    if output_root.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {output_root}")
    bundle_bytes = bundle_path.read_bytes()
    bundle = json.loads(bundle_bytes)
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes)
    bundle_sha = hashlib.sha256(bundle_bytes).hexdigest()
    protocol_sha = hashlib.sha256(protocol_bytes).hexdigest()
    if protocol.get("bindings", {}).get("manifest_sha256") != bundle_sha:
        raise ValueError("the existing 680-fold protocol is not bound to this bundle manifest")
    selected, split_counts = _selected_rows(bundle)
    training_ids = sorted(row["source_record_id"] for row in selected if row["original_split"] == "Training")
    if sorted(protocol.get("ids", [])) != training_ids:
        raise ValueError("the existing five-fold IDs do not equal the 680 Training allowlist")
    if len(protocol.get("folds", [])) != len(training_ids):
        raise ValueError("the saved fold assignment does not cover every Training ID once")
    if protocol.get("config", {}).get("folds") != 5:
        raise ValueError("the saved comparison protocol is not five-fold")
    fold_by_id = dict(zip(protocol["ids"], protocol["folds"]))
    if set(fold_by_id) != set(training_ids):
        raise ValueError("duplicate or missing image IDs exist in the fold assignment")

    output_root.mkdir(parents=True, exist_ok=False)
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    selected_ids = {row["source_record_id"] for row in selected}
    caption_rows: dict[str, list[dict]] = {}
    for split, filename in (("Training", "Train_captions.csv"), ("Validation", "Validation_captions.csv")):
        split_ids = {record_id for record_id in selected_ids if record_id.startswith(split + "/")}
        caption_rows.update(_read_captions(source_root / split / filename, split_ids, split))

    class_counts = Counter()
    detector_box_counts = Counter()
    image_targets = Counter()
    profile_counts = Counter()
    source_modes = Counter()
    crop_rows: list[dict] = []
    exported_records: list[dict] = []
    arch_rows: list[dict] = []
    raw_label_rows = 0
    clipped_box_count = 0
    source_label_root = output_root / "source_annotations"
    for row in selected:
        record_id = row["source_record_id"]
        split, image_id = record_id.split("/")
        if split not in ("Training", "Validation"):
            raise ValueError("only the two approved development splits can be exported")
        caption_set = caption_rows[record_id]
        variant_maxima = [entry["caption_max"] for entry in caption_set]
        expected_grade = int(row["provisional_mgi_grade"])
        if any(value is None for value in variant_maxima) or set(variant_maxima) != {expected_grade}:
            raise ValueError(f"caption variants do not agree with the frozen provisional label: {record_id}")

        source_image = source_root / split / "Images" / f"{image_id}.jpg"
        source_label = source_root / split / "Labels" / f"{image_id}.txt"
        if not source_image.is_file() or not source_label.is_file():
            raise FileNotFoundError(f"eligible image/label pair missing for {record_id}")
        source_hash = sha256_file(source_image)
        if source_hash != row["source_sha256"]:
            raise ValueError(f"source image hash does not match the frozen manifest: {record_id}")
        with Image.open(source_image) as image:
            source_width, source_height = image.size
            source_modes[(image.format, image.mode)] += 1
            if image.format != "JPEG" or image.mode != "RGB":
                raise ValueError(f"unsupported source image format for {record_id}")

        source_lines = source_label.read_text(encoding="utf-8").splitlines()
        boxes = parse_yolo_label_lines(source_lines)
        raw_label_rows += len(boxes)
        raw_class_frequency = Counter(box.class_id for box in boxes)
        for class_id in range(7):
            class_counts[(split, class_id)] += raw_class_frequency[class_id]
        if raw_class_frequency[0] != 1 or raw_class_frequency[1] != 1:
            raise ValueError(f"expected one maxilla and one mandible ROI box in {record_id}")
        tooth_boxes = [box for box in boxes if box.mgi_grade is not None]
        if len(tooth_boxes) not in (11, 12, 13):
            raise ValueError(f"unexpected per-tooth box count in {record_id}: {len(tooth_boxes)}")
        mapped_max = max(box.mgi_grade for box in tooth_boxes)
        if mapped_max != expected_grade:
            raise ValueError(f"mapped tooth-box maximum disagrees with caption grade: {record_id}")
        image_targets[(split, expected_grade)] += 1

        model_image = output_root / "images" / split / f"{image_id}.jpg"
        out_width, out_height, source_profile_sha, output_profile_sha = _save_model_image(
            source_image, model_image, srgb
        )
        profile_counts[source_profile_sha] += 1

        detector_lines = []
        for box in tooth_boxes:
            x1 = (box.center_x - box.width / 2.0) * source_width
            y1 = (box.center_y - box.height / 2.0) * source_height
            x2 = (box.center_x + box.width / 2.0) * source_width
            y2 = (box.center_y + box.height / 2.0) * source_height
            if x1 < 0 or y1 < 0 or x2 > source_width or y2 > source_height:
                clipped_box_count += 1
            detector_line = detector_label_for_tooth_box(box, out_width, out_height)
            if detector_line is None:
                raise AssertionError("tooth box did not produce a detector label")
            detector_lines.append(detector_line)
            class_counts[(split, box.mgi_grade)] += 0  # Keep grade bins explicit in output.
            detector_box_counts[(split, box.mgi_grade)] += 1
        detector_label = output_root / "labels" / split / f"{image_id}.txt"
        detector_label.parent.mkdir(parents=True, exist_ok=True)
        detector_label.write_text("\n".join(detector_lines) + "\n", encoding="utf-8")

        archived_label = source_label_root / split / f"{image_id}.txt"
        archived_label.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_label, archived_label)

        for box in boxes:
            if box.class_id in (0, 1):
                arch_rows.append({
                    "source_record_id": record_id,
                    "roi_name": "maxilla" if box.class_id == 0 else "mandible",
                    "source_class_id": box.class_id,
                    "center_xywh_normalized": [box.center_x, box.center_y, box.width, box.height],
                    "used_for_grade_training": False,
                })

        outer_fold = fold_by_id.get(record_id) if split == "Training" else None
        _save_roi_crops(
            model_image,
            boxes,
            record_id,
            split,
            row["content_group_id"],
            outer_fold,
            output_root,
            crop_rows,
        )
        exported_records.append({
            "source_record_id": record_id,
            "original_split": split,
            "content_group_id": row["content_group_id"],
            "outer_fold": outer_fold,
            "provisional_image_mgi_grade": expected_grade,
            "caption_variant_maxima": variant_maxima,
            "mapped_tooth_box_max_grade": mapped_max,
            "label_status": "provisional_not_clinically_verified",
            "qualified_label_approved": False,
            "participant_independence_verified": False,
            "source_sha256": source_hash,
            "source_label_sha256": sha256_file(source_label),
            "model_image_path": model_image.relative_to(output_root).as_posix(),
            "model_image_sha256": sha256_file(model_image),
            "model_dimensions": [out_width, out_height],
            "source_dimensions": [source_width, source_height],
            "source_profile_sha256": source_profile_sha,
            "model_profile_sha256": output_profile_sha,
            "source_box_count": len(boxes),
            "tooth_box_count": len(tooth_boxes),
        })
        for caption_index, caption in enumerate(caption_set, start=1):
            caption["source_record_id"] = record_id
            caption["original_split"] = split
            caption["caption_variant"] = caption_index
            caption["provisional_image_grade"] = expected_grade

    if len(crop_rows) != sum(r["tooth_box_count"] for r in exported_records):
        raise AssertionError("crop count does not equal the eligible per-tooth box count")

    folds_output = []
    for fold in range(5):
        score_ids = [image_id for image_id in protocol["ids"] if fold_by_id[image_id] == fold]
        fit_ids = [image_id for image_id in protocol["ids"] if fold_by_id[image_id] != fold]
        fit_groups = {next(r["content_group_id"] for r in exported_records if r["source_record_id"] == image_id) for image_id in fit_ids}
        score_groups = {next(r["content_group_id"] for r in exported_records if r["source_record_id"] == image_id) for image_id in score_ids}
        if fit_groups & score_groups:
            raise ValueError(f"content groups cross the saved fold boundary {fold}")
        folds_output.append({"fold": fold, "fit_ids": fit_ids, "score_ids": score_ids})

    with (output_root / "captions_selected.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["source_record_id", "original_split", "caption_variant", "caption_text", "parsed_grades", "caption_max", "provisional_image_grade"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record_id in sorted(caption_rows):
            for caption in caption_rows[record_id]:
                writer.writerow({
                    "source_record_id": record_id,
                    "original_split": "Training" if record_id.startswith("Training/") else "Validation",
                    "caption_variant": caption["caption_variant"],
                    "caption_text": caption["caption_text"],
                    "parsed_grades": json.dumps(caption["parsed_grades"]),
                    "caption_max": caption["caption_max"],
                    "provisional_image_grade": caption["provisional_image_grade"],
                })

    crop_manifest = output_root / "crop_manifest.csv"
    with crop_manifest.open("w", encoding="utf-8", newline="") as handle:
        fields = list(crop_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for crop in crop_rows:
            item = crop.copy()
            item["source_box_xywh_normalized"] = json.dumps(item["source_box_xywh_normalized"])
            writer.writerow(item)

    write_json(output_root / "image_manifest.json", {
        "version": "roi-tooth-v1",
        "evidence_date": "2026-10-17",
        "source_bundle_sha256": bundle_sha,
        "source_protocol_sha256": protocol_sha,
        "selection_policy": "frozen safe provisional development allowlist: 680 Training + 53 Validation only",
        "not_included": ["all 181 held records", "all 182 protected Test records", "NP015 excluded records", "uncertain/protected content groups"],
        "qualified_labels_approved": False,
        "participant_independence_verified": False,
        "final_research_approved": False,
        "source_class_mapping": {str(raw): grade for raw, grade in RAW_CLASS_TO_MGI.items()},
        "source_arch_classes": {"0": "maxilla ROI", "1": "mandible ROI"},
        "arch_boxes_used_for_grade_training": False,
        "detector_target": "one class: tooth/perigingival ROI; derived class 0 has no MGI meaning",
        "derived_detector_classes": {"0": "tooth_roi"},
        "crop_classifier_target": "provisional MGI grade 0-4 from audited source TXT IDs 2-6",
        "image_target": "maximum caption-derived MGI grade among visible teeth",
        "color_transform": {
            "input": "embedded opRGB ICC profile; RGB8; EXIF orientation 1",
            "output": "ICC color-managed 8-bit sRGB using relative colorimetric intent",
            "resize_max_side": MAX_IMAGE_SIDE,
            "jpeg_quality": JPEG_QUALITY,
            "note": "new model view only; source JPEG bytes are unchanged",
        },
        "roi_classifier_crop": {
            "padding_fraction_each_side": CROP_PADDING,
            "output_size": [CROP_SIZE, CROP_SIZE],
            "crop_unit": "one source per-tooth box plus nearby gingiva; not a gum-only mask",
        },
        "split_counts": split_counts,
        "image_grade_counts": {f"{split}:{grade}": count for (split, grade), count in sorted(image_targets.items())},
        "raw_source_class_counts": {f"{split}:{class_id}": count for (split, class_id), count in sorted(class_counts.items()) if class_id <= 6 and count},
        "mapped_tooth_grade_box_counts": {f"{split}:{grade}": count for (split, grade), count in sorted(detector_box_counts.items())},
        "selected_caption_rows": sum(len(value) for value in caption_rows.values()),
        "source_annotation_rows": raw_label_rows,
        "selected_arch_roi_boxes": len(arch_rows),
        "selected_tooth_roi_boxes_and_crops": len(crop_rows),
        "edge_clipped_source_boxes": clipped_box_count,
        "source_icc_profile_sha256_counts": dict(profile_counts),
        "source_format_mode_counts": {f"{fmt}:{mode}": count for (fmt, mode), count in source_modes.items()},
        "records": exported_records,
    })
    write_json(output_root / "folds.json", {
        "version": "training680-stratified-group-kfold-v1",
        "source_protocol_sha256": protocol_sha,
        "source_manifest_sha256": bundle_sha,
        "fold_assignment_sha256": hashlib.sha256(json.dumps(protocol["folds"], separators=(",", ":")).encode()).hexdigest(),
        "folds": folds_output,
    })
    write_json(output_root / "arch_roi_annotations.json", {
        "note": "Classes 0/1 are broad maxilla/mandible ROIs. Kept as context; excluded from tooth-grade detector training and mAP.",
        "annotations": arch_rows,
    })
    write_json(output_root / "color_transform.json", {
        "version": "roi-srgb-v1",
        "input_profile_description": "opRGB",
        "input_profile_sha256": next(iter(profile_counts)) if len(profile_counts) == 1 else "multiple",
        "output_profile_description": "sRGB",
        "output_profile_sha256": hashlib.sha256(srgb.tobytes()).hexdigest(),
        "rendering_intent": "relative_colorimetric (0)",
        "max_image_side": MAX_IMAGE_SIDE,
        "jpeg_quality": JPEG_QUALITY,
        "color_managed_input_count": len(selected),
    })
    write_json(output_root / "folds_protocol_snapshot.json", {
        "config": protocol["config"],
        "ids": protocol["ids"],
        "folds": protocol["folds"],
        "note": "Only the existing Training IDs and fold IDs are copied; no protected Test/held rows are included.",
    })
    _write_readme(output_root)

    report = {
        "status": "package_built_provisional_only",
        "output_root": str(output_root),
        "split_counts": split_counts,
        "source_manifest_sha256": bundle_sha,
        "source_protocol_sha256": protocol_sha,
        "source_icc_profiles": dict(profile_counts),
        "source_format_modes": {f"{fmt}:{mode}": count for (fmt, mode), count in source_modes.items()},
        "raw_source_annotation_rows": raw_label_rows,
        "mapped_detector_boxes": dict({f"{s}:{g}": n for (s, g), n in sorted(detector_box_counts.items())}),
        "crop_count": len(crop_rows),
        "edge_clipped_source_boxes": clipped_box_count,
        "caption_variants_checked": sum(len(value) for value in caption_rows.values()),
        "caption_max_mapping_mismatches": 0,
        "source_class_mapping_mismatches": 0,
        "qualified_labels_approved": False,
        "held_or_test_payloads_packaged": False,
    }
    write_json(output_root.parent / "dataset_build_report.json", report)
    return report


def _write_readme(root: Path) -> None:
    readme = """# Isolated tooth ROI dataset v1

This package contains only 680 frozen provisional Training records and 53
provisional Validation records from the existing development allowlist. It
does not contain the 181 held records or any protected Test records.

Raw source labels are preserved under `source_annotations/`. `labels/` contains
one-class YOLO detector labels using only source classes 2-6. In this derived
detector dataset, class 0 means tooth_roi and does not mean MGI 0. The preserved
raw TXT IDs 2-6 map provisionally to crop-classifier grades 0-4. Broad
maxilla/mandible classes 0 and 1 are stored in `arch_roi_annotations.json` and
are excluded from detector training.

Images are new sRGB-converted views with a maximum side of 1600 pixels. Their
source files remain unchanged. Per-tooth crop files and their parent-image,
group, fold, source-class and provisional-grade metadata are in
`crops/` and `crop_manifest.csv`.

The labels have not received clinical approval, participant identity is not
verified, and the source mapping remains provisional. A per-tooth detector mAP
is not image-level MGI accuracy. The five saved Training folds are unchanged
from the prior 680-image development protocol.

Dataset source: Duy et al., *A Dental Intraoral Image Dataset of Gingivitis for
Image Captioning*, Mendeley Data v1, CC BY 4.0. The Ultralytics training code
has its own license; see the experiment handoff before deployment.
"""
    destination = root / "README_roi_dataset.md"
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(readme, encoding="utf-8")
    os.replace(temporary, destination)


def create_zip(package_dir: Path, zip_path: Path) -> str:
    """Create an immutable ZIP once; refuse to replace a prior package."""

    if zip_path.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {zip_path}")
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file() and ".DS_Store" not in path.name:
                archive.write(path, Path("roi_tooth_v1") / path.relative_to(package_dir))
    return sha256_file(zip_path)


def derive_one_class_detector_package(source_package: Path, output_root: Path) -> dict:
    """Derive a single-class ROI detector view without recopying image pixels.

    The 5-grade detector export remains untouched. This new experiment label
    view uses the same tooth boxes with derived detector class 0, while the
    raw source TXT IDs continue to define separate crop-classifier grades.
    """

    if output_root.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {output_root}")
    manifest_path = source_package / "image_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if len(manifest.get("records", [])) != 733:
        raise ValueError("source ROI package is not the frozen 680/53 development set")
    if manifest.get("split_counts") != {"Training": 680, "Validation": 53}:
        raise ValueError("source ROI package split counts changed")
    records = manifest["records"]
    if any("Test" in row["source_record_id"] for row in records):
        raise ValueError("protected Test identifier found in package")
    if any(row["label_status"] != "provisional_not_clinically_verified" for row in records):
        raise ValueError("unexpected label-approval state in package")

    # Recheck source-tooth mapping and exact box geometry before changing labels.
    detector_lines_by_id = {}
    source_class_counts = Counter()
    for row in records:
        record_id = row["source_record_id"]
        split, image_id = record_id.split("/")
        source_label = source_package / "source_annotations" / split / f"{image_id}.txt"
        image_path = source_package / row["model_image_path"]
        if sha256_file(source_label) != row["source_label_sha256"]:
            raise ValueError(f"source label hash changed: {record_id}")
        if sha256_file(image_path) != row["model_image_sha256"]:
            raise ValueError(f"model image hash changed: {record_id}")
        boxes = parse_yolo_label_lines(source_label.read_text(encoding="utf-8").splitlines())
        tooth_boxes = [box for box in boxes if box.mgi_grade is not None]
        if len(tooth_boxes) != row["tooth_box_count"]:
            raise ValueError(f"source tooth box count changed: {record_id}")
        grades = [box.mgi_grade for box in tooth_boxes]
        if max(grades) != row["provisional_image_mgi_grade"]:
            raise ValueError(f"source TXT maximum no longer matches captions: {record_id}")
        width, height = row["model_dimensions"]
        new_lines = []
        for box in tooth_boxes:
            line = detector_label_for_tooth_box(box, width, height)
            if line is None:
                raise AssertionError("tooth box did not produce a one-class detector row")
            new_lines.append(line)
            source_class_counts[box.class_id] += 1
        detector_lines_by_id[record_id] = new_lines

    # Hard links avoid a second expensive JPEG conversion; every changed file
    # below is replaced atomically so the earlier export remains unchanged.
    output_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_package, output_root, copy_function=os.link)
    for record_id, lines in detector_lines_by_id.items():
        split, image_id = record_id.split("/")
        label_path = output_root / "labels" / split / f"{image_id}.txt"
        temporary = label_path.with_suffix(".oneclass.tmp")
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(temporary, label_path)

    manifest["version"] = "roi-tooth-v1-oneclass-detector"
    manifest["detector_target"] = "one class: tooth/perigingival ROI; derived class 0 has no MGI meaning"
    manifest["derived_detector_classes"] = {"0": "tooth_roi"}
    manifest["crop_classifier_target"] = "provisional MGI grade 0-4 from audited source TXT IDs 2-6"
    manifest["grade_source_for_crop_classifier"] = "source_annotations TXT class_id minus 2"
    manifest["one_class_detector_label_rows"] = sum(map(len, detector_lines_by_id.values()))
    updated_manifest = output_root / "image_manifest.json"
    temp_manifest = updated_manifest.with_suffix(".tmp")
    temp_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_manifest, updated_manifest)

    arch_path = output_root / "arch_roi_annotations.json"
    arch_data = json.loads(arch_path.read_text(encoding="utf-8"))
    arch_data["note"] = (
        "Source classes 0/1 are broad maxilla/mandible ROIs. Kept as context; "
        "excluded from one-class tooth_roi detector training and mAP."
    )
    temp_arch = arch_path.with_suffix(".tmp")
    temp_arch.write_text(json.dumps(arch_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp_arch, arch_path)

    _write_readme(output_root)
    code_root = output_root / "code"
    code_root.mkdir(exist_ok=True)
    for name in ("roi_workflow_v1.py", "roi_colab_train_v1.py", "roi_inference_v1.py", "roi_demo_v1.py"):
        shutil.copy2(REPO / "src" / "vision" / name, code_root / name)
    shutil.copy2(REPO / "requirements-vision-roi-v1.txt", code_root / "requirements-vision-roi-v1.txt")

    report = {
        "status": "oneclass_roi_package_built_provisional_only",
        "source_experimental_export": str(source_package),
        "output_root": str(output_root),
        "records": len(records),
        "split_counts": manifest["split_counts"],
        "oneclass_detector_labels": sum(map(len, detector_lines_by_id.values())),
        "crop_classifier_grade_box_counts_by_raw_source_class": dict(sorted(source_class_counts.items())),
        "crop_count": manifest["selected_tooth_roi_boxes_and_crops"],
        "caption_max_mapping_mismatches": 0,
        "source_class_mapping_mismatches": 0,
        "qualified_labels_approved": False,
        "held_or_test_payloads_packaged": False,
        "source_manifest_sha256": manifest["source_bundle_sha256"],
        "source_protocol_sha256": manifest["source_protocol_sha256"],
        "earlier_grade_detector_export_preserved": True,
    }
    write_json(output_root / "dataset_build_report.json", report)
    write_json(output_root.parent / "dataset_build_report_oneclass.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT / "dataset")
    parser.add_argument("--zip", type=Path, default=DEFAULT_ROOT / "roi_tooth_dataset_v1.zip")
    args = parser.parse_args()
    report = build_package(args.bundle, args.protocol, args.source_root, args.output_root)
    archive_sha = create_zip(args.output_root, args.zip)
    report["archive_path"] = str(args.zip)
    report["archive_bytes"] = args.zip.stat().st_size
    report["archive_sha256"] = archive_sha
    write_json(args.output_root.parent / "dataset_build_report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
