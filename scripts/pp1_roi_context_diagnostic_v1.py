"""Local ROI coverage review and fixed fold-0 inference ablation. No training.

Prepare uses four fit-only photos. Score compares one declared context change
on the same 136 score photos, with the same detector boxes and frozen weights.
It cannot establish clinical gingival coverage without qualified review.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.vision.roi_dataset_v1 import DEFAULT_SOURCE
from src.vision.roi_workflow_v1 import box_to_xyxy, image_grade_metrics, parse_yolo_label_lines

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data/vision/roi_tooth_v1_20261017/dataset_v4"
RETURN = REPO / "data/vision/roi_tooth_v1_20261017/colab_return/roi_tooth_v1_colab_return"
OUT = REPO / "data/vision/pp1_final_local_20261018_v1/roi_context"
FIT_CASES = ["Training/00055", "Training/00075", "Training/00009", "Training/00015"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def save(name, value):
    with (OUT / name).open("x") as stream:
        json.dump(value, stream, indent=2)


def inputs():
    manifest = json.loads((DATA / "image_manifest.json").read_text())
    records = {row["source_record_id"]: row for row in manifest["records"]}
    fold = json.loads((DATA / "folds.json").read_text())["folds"][0]
    fit, score = set(fold["fit_ids"]), set(fold["score_ids"])
    assert len(fit) == 544 and len(score) == 136 and not fit & score
    assert all(name.startswith("Training/") for name in fit | score)
    assert not ({records[name]["content_group_id"] for name in fit}
                & {records[name]["content_group_id"] for name in score})
    # Cross-check membership against the independently frozen ResNet pilot.
    pilot = json.loads((REPO / "data/vision/resnet50_fold0_pilot_v1_20261018_r2/package/manifest.json").read_text())
    assert fit == {row["id"] for row in pilot["records"] if row["role"] == "fit"}
    assert score == {row["id"] for row in pilot["records"] if row["role"] == "score"}
    return records, fit, score


def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    records, fit, score = inputs()
    assert set(FIT_CASES) <= fit
    with (DATA / "crop_manifest.csv").open() as stream:
        crop_rows = list(csv.DictReader(stream))
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    counts, hashes, review = Counter(), {}, []
    for name in FIT_CASES:
        row = records[name]
        path = DATA / row["model_image_path"]
        label = DEFAULT_SOURCE / "Training/Labels" / (name.split("/")[1] + ".txt")
        assert sha(path) == row["model_image_sha256"]
        assert sha(label) == row["source_label_sha256"]
        hashes[str(path.relative_to(REPO))] = sha(path)
        hashes[str(label.relative_to(REPO))] = sha(label)
        boxes = [box for box in parse_yolo_label_lines(label.read_text().splitlines()) if box.class_id >= 2]
        selected = [crop for crop in crop_rows if crop["parent_record_id"] == name]
        assert len(boxes) == len(selected) == 12
        with Image.open(path) as source:
            source = source.convert("RGB")
            annotated = source.copy()
            draw = ImageDraw.Draw(annotated)
            for box in boxes:
                draw.rectangle(box_to_xyxy(box, source.width, source.height), outline="#146ee8", width=4)
                draw.rectangle(box_to_xyxy(box, source.width, source.height, padding_fraction=.15), outline="#ec9c15", width=3)
            annotated.thumbnail((1120, 730))
            sheet = Image.new("RGB", (1200, 1320), "white")
            header = ImageDraw.Draw(sheet)
            header.text((30, 18), f"{name}  provisional image MGI {row['provisional_image_mgi_grade']}", fill="#123c50", font=font)
            header.text((30, 52), "Blue: source tooth boxes. Orange: training crop window (+15% each side).", fill="#123c50", font=font)
            sheet.paste(annotated, (30, 95))
            y_start = 95 + annotated.height + 20
            for index, (box, crop_row) in enumerate(zip(boxes, selected)):
                crop_path = DATA / crop_row["crop_path"]
                crop = source.crop(box_to_xyxy(box, source.width, source.height, padding_fraction=.15))
                crop = crop.resize((224, 224), Image.Resampling.LANCZOS)
                buffer = BytesIO()
                crop.save(buffer, "JPEG", quality=95, subsampling=0, optimize=True)
                assert buffer.getvalue() == crop_path.read_bytes(), f"Crop export mismatch: {crop_path}"
                hashes[str(crop_path.relative_to(REPO))] = sha(crop_path)
                counts["exact_crop_exports"] += 1
                with Image.open(crop_path) as saved:
                    thumb = saved.resize((160, 160))
                    x = 30 + (index % 6) * 190
                    y = y_start + (index // 6) * 195
                    sheet.paste(thumb, (x, y))
                    header.text((x, y + 163), f"ROI {index + 1}, MGI {box.class_id - 2}", fill="#123c50", font=font)
            sheet = sheet.crop((0, 0, 1200, y_start + 395))
            sheet.save(OUT / (name.replace("/", "_") + "_coverage.png"))
        review.append({"record_id": name, "label_status": "provisional",
                       "qualified_reviewer": None, "gum_margin_visible": None,
                       "crop_clips_relevant_tissue": None, "notes": ""})
    save("coverage_review_pending.json", review)
    save("coverage_preservation.json", hashes)
    save("preparation.json", {"fit_count": len(fit), "score_count": len(score),
         "fit_review_cases": FIT_CASES, "crop_export_exact_matches": counts["exact_crop_exports"],
         "clinical_gingival_coverage_verified": False, "score_pixels_accessed": 0,
         "fit_support": dict(Counter(records[n]["provisional_image_mgi_grade"] for n in fit)),
         "score_support": dict(Counter(records[n]["provisional_image_mgi_grade"] for n in score))})
    # The reviewer may later add verified grades, but this file never changes labels.
    queue = [{"record_id": n, "provisional_grade": records[n]["provisional_image_mgi_grade"],
              "role": "fit", "qualified_grade": None, "reviewer": None,
              "consent_and_source_verification": None, "notes": ""}
             for n in sorted(fit) if records[n]["provisional_image_mgi_grade"] in (1, 2)]
    assert len(queue) == 76
    save("grade12_fit_review_queue.json", queue)
    print(json.dumps({"status": "prepared", "fit_cases": 4, "exact_training_crops": 48,
                      "grade12_review_queue": len(queue), "clinical_review": "pending"}))


def crop_bounds(box, width, height, padding):
    """Match the historical v1 scoring crop geometry exactly."""
    x1, y1, x2, y2 = box
    px, py = max(1., (x2 - x1) * padding), max(1., (y2 - y1) * padding)
    geometry = type("Box", (), {"center_x": (x1 + x2) / (2 * width),
                   "center_y": (y1 + y2) / (2 * height),
                   "width": (x2 - x1 + 2 * px) / width,
                   "height": (y2 - y1 + 2 * py) / height})()
    return box_to_xyxy(geometry, width, height)


def score_fixed():
    import torch
    from torchvision import transforms
    from sklearn.metrics import cohen_kappa_score, mean_absolute_error
    from src.vision.roi_inference_v1 import load_roi_checkpoint_models

    protocol = json.loads((OUT / "fixed_protocol.json").read_text())
    assert protocol["baseline_padding"] == .15 and protocol["candidate_padding"] == .30
    assert protocol["training"] is False and protocol["fold"] == 0
    records, fit, score = inputs()
    integrity = {row["path"]: row["sha256"] for row in csv.DictReader((RETURN / "return_integrity_manifest.csv").open())}
    names = ["fold_00/detector_last.pt", "fold_00/crop_classifier_last.pt"]
    for name in names:
        assert sha(RETURN / name) == integrity[name]
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    torch.set_num_threads(2)
    detector, classifier, _ = load_roi_checkpoint_models(*(RETURN / name for name in names), device=device)
    transform = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                 transforms.Normalize((.485, .456, .406), (.229, .224, .225))])
    rows = {"baseline": [], "expanded_context": []}
    source_hashes = {}
    started = time.monotonic()
    with (OUT / "per_image_predictions.jsonl").open("x") as log:
        for index, name in enumerate(sorted(score)):
            row = records[name]
            path = DATA / row["model_image_path"]
            assert sha(path) == row["model_image_sha256"]
            source_hashes[name] = sha(path)
            result = detector.predict(source=[str(path)], imgsz=640, conf=.25, iou=.70,
                                      device=device, save=False, verbose=False)[0]
            boxes = result.boxes.xyxy.cpu().tolist() if result.boxes is not None else []
            assert result.boxes is None or set(result.boxes.cls.cpu().tolist()) <= {0.}
            item = {"record_id": name, "true_grade": row["provisional_image_mgi_grade"],
                    "shared_detector_boxes": boxes, "arms": {}}
            with Image.open(path) as image:
                image = image.convert("RGB")
                for arm, padding in [("baseline", .15), ("expanded_context", .30)]:
                    crops = [transform(image.crop(crop_bounds(box, image.width, image.height, padding))) for box in boxes]
                    grades = []
                    for offset in range(0, len(crops), 32):
                        with torch.inference_mode():
                            logits = classifier(torch.stack(crops[offset:offset + 32]).to(device))
                        grades.extend(logits.argmax(1).cpu().tolist())
                    prediction = max(grades) if grades else None
                    record = {"source_record_id": name, "true_image_grade": item["true_grade"],
                              "predicted_image_grade": prediction, "predicted_tooth_roi_count": len(boxes)}
                    rows[arm].append(record)
                    item["arms"][arm] = {"image_grade": prediction, "crop_grades": grades}
            log.write(json.dumps(item) + "\n")
            log.flush()
            if (index + 1) % 16 == 0:
                print(json.dumps({"scored": index + 1, "total": 136}), flush=True)
    metrics = {}
    for arm, values in rows.items():
        metrics[arm] = image_grade_metrics(values)
        detected = [r for r in values if r["predicted_image_grade"] is not None]
        true = [r["true_image_grade"] for r in detected]
        pred = [r["predicted_image_grade"] for r in detected]
        metrics[arm]["ordinal_mae_detected_only"] = mean_absolute_error(true, pred) if true else None
        metrics[arm]["qwk_detected_only"] = cohen_kappa_score(true, pred, weights="quadratic", labels=[0, 1, 2, 3, 4]) if true else None
    old = {r["source_record_id"]: int(r["predicted_image_grade"]) if r["predicted_image_grade"] else None
           for r in csv.DictReader((RETURN / "oof_predictions.csv").open())}
    agreement = sum(old[r["source_record_id"]] == r["predicted_image_grade"] for r in rows["baseline"])
    changed = sum(a["predicted_image_grade"] != b["predicted_image_grade"] for a, b in zip(*rows.values()))
    save("results.json", {"status": "complete", "experiment": "frozen_weight_inference_context_ablation",
         "protocol_sha256": sha(OUT / "fixed_protocol.json"), "device": device,
         "n_images_each_arm": 136, "fit_images_used_for_context_selection": FIT_CASES,
         "original_colab_baseline_prediction_agreement": agreement, "changed_predictions": changed,
         "elapsed_seconds": time.monotonic() - started, "metrics": metrics,
         "checkpoint_sha256": {name: integrity[name] for name in names},
         "source_hashes": source_hashes, "clinical_review": "pending", "test_used": False,
         "training_run": False, "demo_changed": False})
    # Verify every accessed score image and both checkpoints again after inference.
    assert all(sha(DATA / records[n]["model_image_path"]) == value for n, value in source_hashes.items())
    assert all(sha(RETURN / name) == integrity[name] for name in names)
    print(json.dumps({"metrics": metrics, "old_baseline_agreement": agreement, "changed_predictions": changed}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "score"])
    args = parser.parse_args()
    prepare() if args.stage == "prepare" else score_fixed()
