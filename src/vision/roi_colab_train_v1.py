"""Leakage-safe YOLO + tooth-ROI classifier training for Colab or a small pilot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
from collections import Counter
from pathlib import Path

try:
    from .roi_workflow_v1 import box_to_xyxy, image_grade_metrics
except ImportError:  # Running as a copied script beside roi_workflow_v1.py.
    from roi_workflow_v1 import box_to_xyxy, image_grade_metrics


DEFAULT_DETECTOR = "yolo26n.pt"
DEFAULT_DETECTOR_EPOCHS = 30
DEFAULT_CLASSIFIER_EPOCHS = 12
IMAGE_SIZE = 640
DETECTOR_CONFIDENCE = 0.25
DETECTOR_IOU = 0.70
CROP_PADDING = 0.15
CROP_SIZE = 224
CROP_CLASS_NAMES = ["MGI_0", "MGI_1", "MGI_2", "MGI_3", "MGI_4"]
DETECTOR_CLASS_NAMES = ["tooth_roi"]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_package(package_root: Path) -> tuple[dict, dict, list[dict]]:
    image_manifest = json.loads((package_root / "image_manifest.json").read_text())
    folds = json.loads((package_root / "folds.json").read_text())
    with (package_root / "crop_manifest.csv").open(encoding="utf-8", newline="") as stream:
        crop_rows = list(csv.DictReader(stream))
    if image_manifest.get("qualified_labels_approved") is not False:
        raise ValueError("This workflow accepts only provisional labels, not a changed approval state.")
    if image_manifest.get("participant_independence_verified") is not False:
        raise ValueError("Unexpected participant-independence status; inspect before training.")
    if image_manifest.get("derived_detector_classes") != {"0": "tooth_roi"}:
        raise ValueError("Expected the isolated one-class tooth-ROI detector labels.")
    if image_manifest.get("source_class_mapping") != {str(raw): raw - 2 for raw in range(2, 7)}:
        raise ValueError("Source IDs 2-6 do not match the frozen provisional MGI mapping.")
    records = image_manifest.get("records", [])
    ids = [row["source_record_id"] for row in records]
    if len(ids) != 733 or len(ids) != len(set(ids)):
        raise ValueError(f"Expected exactly 733 unique allowlisted records, got {len(ids)}.")
    if any("Test" in record_id or "held" in record_id.lower() for record_id in ids):
        raise ValueError("Protected or held identifiers cannot enter the training package.")
    if sum(row["original_split"] == "Training" for row in records) != 680:
        raise ValueError("Training allowlist no longer has the frozen 680 records.")
    if sum(row["original_split"] == "Validation" for row in records) != 53:
        raise ValueError("Validation allowlist no longer has the frozen 53 records.")
    if len(folds.get("folds", [])) != 5:
        raise ValueError("The experiment requires the existing five fixed folds.")
    if len(crop_rows) != int(image_manifest["selected_tooth_roi_boxes_and_crops"]):
        raise ValueError("Crop rows do not match the dataset build report.")
    return image_manifest, folds, crop_rows


def _fold_by_record(folds: dict) -> dict[str, int]:
    output: dict[str, int] = {}
    for fold in folds["folds"]:
        for record_id in fold["score_ids"]:
            if record_id in output:
                raise ValueError(f"Record appears in more than one score fold: {record_id}")
            output[record_id] = int(fold["fold"])
    return output


def _write_yolo_yaml(
    package_root: Path,
    fold_root: Path,
    train_ids: list[str],
    score_ids: list[str],
) -> Path:
    import yaml

    split_root = fold_root / "data_lists"
    split_root.mkdir(parents=True, exist_ok=True)
    list_paths = {}
    for split_name, ids in (("train", train_ids), ("score", score_ids)):
        list_path = split_root / f"{split_name}.txt"
        image_paths = [
            package_root / "images" / "Training" / f"{record_id.split('/')[-1]}.jpg"
            for record_id in ids
        ]
        if any(not path.is_file() for path in image_paths):
            raise FileNotFoundError(f"Missing {split_name} image in fold {fold_root.name}")
        list_path.write_text("\n".join(str(path.resolve()) for path in image_paths) + "\n")
        list_paths[split_name] = str(list_path.resolve())
    yaml_path = split_root / "dataset.yaml"
    yaml_path.write_text(yaml.safe_dump({
        "path": str(package_root.resolve()),
        "train": list_paths["train"],
        "val": list_paths["score"],
        "names": {index: name for index, name in enumerate(DETECTOR_CLASS_NAMES)},
    }, sort_keys=False))
    return yaml_path


def _torch_device_for_yolo(device: str) -> str:
    """Ultralytics accepts GPU indices like '0'; PyTorch needs 'cuda:0'."""
    if device.isdigit():
        return f"cuda:{device}"
    return device


def _classify_crop_model(package_root: Path, fit_rows: list[dict], score_rows: list[dict],
                         output_dir: Path, *, device: str, epochs: int, batch_size: int,
                         workers: int, seed: int, pretrained: bool) -> tuple[object, dict]:
    import numpy as np
    import torch
    from PIL import Image
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
    from torchvision import models, transforms

    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    transform = transforms.Compose([
        transforms.Resize((CROP_SIZE, CROP_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])

    class RoiCropDataset(Dataset):
        def __init__(self, rows: list[dict]):
            self.rows = rows

        def __len__(self) -> int:
            return len(self.rows)

        def __getitem__(self, index: int):
            row = self.rows[index]
            with Image.open(package_root / row["crop_path"]) as image:
                tensor = transform(image.convert("RGB"))
            return tensor, int(row["provisional_mgi_grade"])

    counts = Counter(int(row["provisional_mgi_grade"]) for row in fit_rows)
    if set(counts) != set(range(5)):
        raise ValueError(f"All five tooth grades must occur in training crops, found {dict(counts)}")
    count_tensor = torch.tensor([counts[grade] for grade in range(5)], dtype=torch.float32)
    class_weights = count_tensor.sum() / (len(CROP_CLASS_NAMES) * count_tensor)
    generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        RoiCropDataset(fit_rows), batch_size=batch_size, shuffle=True,
        num_workers=workers, generator=generator, pin_memory=device.startswith("cuda"),
    )
    score_loader = DataLoader(
        RoiCropDataset(score_rows), batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=device.startswith("cuda"),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint_last.pt"
    if checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(CROP_CLASS_NAMES))
        model.load_state_dict(checkpoint["model_state"])
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
        optimizer.load_state_dict(checkpoint["optimizer_state"])
        start_epoch = int(checkpoint["epoch"])
        history = list(checkpoint.get("history", []))
    else:
        weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        model = models.resnet18(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, len(CROP_CLASS_NAMES))
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
        start_epoch = 0
        history = []
    model = model.to(device)
    loss_function = nn.CrossEntropyLoss(weight=class_weights.to(device))

    def save_checkpoint(epoch: int) -> None:
        # Save after each epoch so Drive/runtime interruptions can resume safely.
        state = {
            "epoch": epoch,
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "optimizer_state": optimizer.state_dict(),
            "history": history,
            "class_counts_fit_only": dict(counts),
            "class_weights_fit_only": class_weights.tolist(),
            "seed": seed,
        }
        temporary = checkpoint_path.with_suffix(".tmp")
        torch.save(state, temporary)
        os.replace(temporary, checkpoint_path)

    for epoch in range(start_epoch, epochs):
        model.train()
        loss_sum = 0.0
        sample_count = 0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = loss_function(logits, labels)
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach().cpu()) * len(labels)
            sample_count += len(labels)
        history.append({"epoch": epoch + 1, "fit_loss": loss_sum / max(sample_count, 1)})
        save_checkpoint(epoch + 1)

    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for images, labels in score_loader:
            predictions = model(images.to(device)).argmax(dim=1).cpu().tolist()
            y_true.extend(labels.tolist())
            y_pred.extend(predictions)
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
    crop_recalls = {
        str(grade): (
            sum(true == grade and pred == grade for true, pred in zip(y_true, y_pred))
            / sum(true == grade for true in y_true)
            if any(true == grade for true in y_true) else None
        )
        for grade in range(5)
    }
    supported_recalls = [value for value in crop_recalls.values() if value is not None]
    crop_metrics = {
        "protocol": "oracle crop classifier using source ground-truth tooth boxes",
        "n_crops": len(y_true),
        "accuracy": accuracy_score(y_true, y_pred) if y_true else None,
        "macro_f1": f1_score(y_true, y_pred, labels=list(range(5)), average="macro", zero_division=0) if y_true else None,
        "balanced_accuracy": sum(supported_recalls) / len(supported_recalls) if supported_recalls else None,
        "per_grade_recall": crop_recalls,
        "confusion_matrix_labels": list(range(5)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(range(5))).tolist(),
        "class_counts_fit_only": dict(counts),
        "class_weights_fit_only": class_weights.tolist(),
    }
    return model, crop_metrics


def _predicted_roi_grades(detector: object, classifier: object, image_paths: list[Path],
                          *, device: str, confidence: float, iou: float) -> dict[str, list[int]]:
    import torch
    from PIL import Image
    from torchvision import transforms

    transform = transforms.Compose([
        transforms.Resize((CROP_SIZE, CROP_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])
    results = detector.predict(
        source=[str(path) for path in image_paths], imgsz=IMAGE_SIZE,
        conf=confidence, iou=iou, device=device, save=False, verbose=False,
    )
    output: dict[str, list[int]] = {}
    classifier.eval()
    for result in results:
        image_path = Path(result.path)
        record_id = f"Training/{image_path.stem}"
        boxes = result.boxes.xyxy.detach().cpu().tolist() if result.boxes is not None else []
        if result.boxes is not None and any(
            int(value) != 0 for value in result.boxes.cls.detach().cpu().tolist()
        ):
            raise ValueError("The detector must return the single tooth_roi class only.")
        crops = []
        if boxes:
            with Image.open(image_path) as source:
                source = source.convert("RGB")
                for x1, y1, x2, y2 in boxes:
                    padding_x = max(1.0, (x2 - x1) * CROP_PADDING)
                    padding_y = max(1.0, (y2 - y1) * CROP_PADDING)
                    box = type("Box", (), {
                        "center_x": (x1 + x2) / (2 * source.width),
                        "center_y": (y1 + y2) / (2 * source.height),
                        "width": ((x2 - x1) + 2 * padding_x) / source.width,
                        "height": ((y2 - y1) + 2 * padding_y) / source.height,
                    })()
                    left, top, right, bottom = box_to_xyxy(box, source.width, source.height)
                    crops.append(transform(source.crop((left, top, right, bottom))))
        grades = []
        for start in range(0, len(crops), 64):
            batch = torch.stack(crops[start:start + 64]).to(device)
            with torch.no_grad():
                grades.extend(classifier(batch).argmax(dim=1).cpu().tolist())
        output[record_id] = grades
    return output


def run_fold(package_root: Path, output_root: Path, fold_number: int, *, device: str,
             detector_epochs: int, classifier_epochs: int, detector_batch: int,
             crop_batch: int, workers: int, seed: int, detector_weights: str,
             train_ids_override: list[str] | None = None,
             score_ids_override: list[str] | None = None,
             run_name: str | None = None, pretrained_crop: bool = True) -> dict:
    import torch
    from ultralytics import YOLO

    package_root = package_root.resolve()
    output_root = output_root.resolve()
    image_manifest, folds_data, crop_rows = _read_package(package_root)
    fold_data = next((item for item in folds_data["folds"] if int(item["fold"]) == fold_number), None)
    if fold_data is None:
        raise ValueError(f"No saved fold {fold_number}")
    train_ids = list(train_ids_override if train_ids_override is not None else fold_data["fit_ids"])
    score_ids = list(score_ids_override if score_ids_override is not None else fold_data["score_ids"])
    if set(train_ids) & set(score_ids):
        raise ValueError("Fold training and score groups overlap.")
    if not train_ids or not score_ids:
        raise ValueError("Both training and score subsets must be non-empty.")
    output_name = run_name or f"fold_{fold_number:02d}"
    torch_device = _torch_device_for_yolo(device)
    fold_root = output_root / output_name
    completion = fold_root / "fold_complete.json"
    if completion.is_file() and run_name is None:
        return json.loads(completion.read_text())

    record_by_id = {row["source_record_id"]: row for row in image_manifest["records"]}
    for record_id in train_ids + score_ids:
        if record_id not in record_by_id or not record_id.startswith("Training/"):
            raise ValueError(f"ID is not part of the approved Training allowlist: {record_id}")
    train_groups = {record_by_id[item]["content_group_id"] for item in train_ids}
    score_groups = {record_by_id[item]["content_group_id"] for item in score_ids}
    if train_groups & score_groups:
        raise ValueError("Content-group overlap detected between fit and score data.")

    crop_train = [row for row in crop_rows if row["parent_record_id"] in set(train_ids)]
    crop_score = [row for row in crop_rows if row["parent_record_id"] in set(score_ids)]
    yaml_path = _write_yolo_yaml(package_root, fold_root, train_ids, score_ids)
    detector_project = fold_root / "detector"
    last_weights = detector_project / "detector_run" / "weights" / "last.pt"
    detector_project.mkdir(parents=True, exist_ok=True)
    completed_detector_epochs = 0
    if last_weights.exists():
        saved_detector_state = torch.load(last_weights, map_location="cpu", weights_only=False)
        completed_detector_epochs = int(saved_detector_state.get("epoch", -1)) + 1
        results_csv = last_weights.parent.parent / "results.csv"
        if results_csv.is_file():
            with results_csv.open(encoding="utf-8", newline="") as stream:
                completed_rows = max(0, sum(1 for _ in csv.reader(stream)) - 1)
            completed_detector_epochs = max(completed_detector_epochs, completed_rows)
        if completed_detector_epochs > detector_epochs:
            raise ValueError("Detector checkpoint has more epochs than this run configuration.")
    if last_weights.exists() and completed_detector_epochs < detector_epochs:
        detector = YOLO(str(last_weights))
        detector.train(resume=True, device=device, workers=workers)
    elif not last_weights.exists():
        detector = YOLO(detector_weights)
        detector.train(
            data=str(yaml_path), epochs=detector_epochs, imgsz=IMAGE_SIZE,
            batch=detector_batch, workers=workers, device=device,
            project=str(detector_project), name="detector_run", exist_ok=True,
            save=True, save_period=1, val=False, patience=10000, plots=False,
            seed=seed, deterministic=True, pretrained=True, verbose=True,
        )
    if not last_weights.is_file():
        raise FileNotFoundError(f"YOLO did not save resumable last.pt: {last_weights}")

    detector = YOLO(str(last_weights))
    detector_eval = detector.val(
        data=str(yaml_path), imgsz=IMAGE_SIZE, batch=detector_batch,
        workers=workers, device=device, plots=False, verbose=True,
    )
    detector_metrics = {
        "map50_95": float(detector_eval.box.map),
        "map50": float(detector_eval.box.map50),
        "map75": float(detector_eval.box.map75),
        "per_class_map50_95": [float(value) for value in detector_eval.box.maps],
        "class_names": DETECTOR_CLASS_NAMES,
        "score_images": len(score_ids),
    }

    classifier, crop_metrics = _classify_crop_model(
        package_root, crop_train, crop_score,
        fold_root / "roi_classifier", device=torch_device, epochs=classifier_epochs,
        batch_size=crop_batch, workers=workers, seed=seed + fold_number,
        pretrained=pretrained_crop,
    )
    score_paths = [package_root / "images" / "Training" / f"{record_id.split('/')[-1]}.jpg" for record_id in score_ids]
    predicted_grades = _predicted_roi_grades(
        detector, classifier, score_paths, device=torch_device,
        confidence=DETECTOR_CONFIDENCE, iou=DETECTOR_IOU,
    )
    true_grades = {row["source_record_id"]: int(row["provisional_image_mgi_grade"])
                   for row in image_manifest["records"]}
    image_records = []
    for record_id in score_ids:
        grades = predicted_grades.get(record_id, [])
        image_records.append({
            "source_record_id": record_id,
            "true_image_grade": true_grades[record_id],
            "predicted_image_grade": max(grades) if grades else None,
            "predicted_tooth_roi_count": len(grades),
        })
    image_metrics = image_grade_metrics(image_records)
    image_metrics["protocol"] = "OOF image-level max over detected ROI-classifier grades; no detection is an incorrect abstention"
    image_metrics["confidence_threshold"] = DETECTOR_CONFIDENCE
    image_metrics["image_target_support"] = {str(grade): sum(r["true_image_grade"] == grade for r in image_records) for grade in range(5)}
    image_metrics["predicted_records"] = image_records

    # A separate mAP pass scores class-aware tooth detection. It is never called
    # image-level classification accuracy.
    fold_result = {
        "status": "completed_engineering_pilot" if run_name is not None else "completed_experimental_oof_fold",
        "fold": fold_number,
        "run_name": output_name,
        "fit_images": len(train_ids),
        "score_images": len(score_ids),
        "fit_crops": len(crop_train),
        "score_crops": len(crop_score),
        "fit_id_sha256": hashlib.sha256("\n".join(sorted(train_ids)).encode()).hexdigest(),
        "score_id_sha256": hashlib.sha256("\n".join(sorted(score_ids)).encode()).hexdigest(),
        "source_protocol_sha256": folds_data["source_protocol_sha256"],
        "device": device,
        "torch_device": torch_device,
        "torch_version": torch.__version__,
        "mps_available": bool(torch.backends.mps.is_available()),
        "detector_checkpoint": str(last_weights),
        "crop_classifier_checkpoint": str(fold_root / "roi_classifier" / "checkpoint_last.pt"),
        "detector_mAP": detector_metrics,
        "oracle_crop_classifier_metrics": crop_metrics,
        "image_level_mgi_metrics": image_metrics,
        "qualified_labels_approved": False,
        "clinical_validation": False,
        "full_model_selection_on_score_fold": False,
    }
    _write_json(fold_root / "fold_metrics.json", fold_result)
    if run_name is None:
        _write_json(completion, fold_result)
    return fold_result


def run_experiment(package_root: Path, output_root: Path, *, device: str = "0",
                   detector_epochs: int = DEFAULT_DETECTOR_EPOCHS,
                   classifier_epochs: int = DEFAULT_CLASSIFIER_EPOCHS,
                   detector_batch: int = 16, crop_batch: int = 64,
                   workers: int = 2, seed: int = 42,
                   detector_weights: str = DEFAULT_DETECTOR,
                   folds: list[int] | None = None) -> dict:
    import torch
    import torchvision
    import ultralytics
    from ultralytics import YOLO

    package_root = package_root.resolve()
    output_root = output_root.resolve()
    image_manifest, folds_data, _ = _read_package(package_root)
    fold_numbers = folds or [int(row["fold"]) for row in folds_data["folds"]]
    output_root.mkdir(parents=True, exist_ok=True)
    base_detector = YOLO(detector_weights)
    base_detector_path = Path(base_detector.ckpt_path)
    if not base_detector_path.is_file():
        raise FileNotFoundError(f"Could not resolve the pretrained detector weights: {detector_weights}")
    configuration = {
        "experiment": "tooth_roi_detector_plus_crop_classifier_v1",
        "package_root": str(package_root.resolve()),
        "dataset_manifest_sha256": _sha256_file(package_root / "image_manifest.json"),
        "fold_protocol_sha256": folds_data["source_protocol_sha256"],
        "training_images": 680,
        "frozen_validation_images_not_used_for_model_selection": 53,
        "detector_weights": detector_weights,
        "detector_weights_sha256": _sha256_file(base_detector_path),
        "crop_classifier_initial_weights": "torchvision ResNet18_Weights.IMAGENET1K_V1",
        "detector_epochs": detector_epochs,
        "classifier_epochs": classifier_epochs,
        "detector_batch": detector_batch,
        "crop_batch": crop_batch,
        "detector_image_size": IMAGE_SIZE,
        "detector_confidence": DETECTOR_CONFIDENCE,
        "detector_nms_iou": DETECTOR_IOU,
        "crop_padding_fraction_each_side": CROP_PADDING,
        "crop_size": CROP_SIZE,
        "detector_class_names": DETECTOR_CLASS_NAMES,
        "crop_class_names": CROP_CLASS_NAMES,
        "workers": workers,
        "seed": seed,
        "device": device,
        "requested_folds": fold_numbers,
        "grade_label_status": "provisional",
        "protected_test_payloads_used": False,
        "ultralytics_version": ultralytics.__version__,
        "torch_version": torch.__version__,
        "torchvision_version": torchvision.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    configuration_path = output_root / "run_configuration.json"
    if configuration_path.exists():
        previous = json.loads(configuration_path.read_text())
        if previous != configuration:
            raise ValueError(
                "Output folder already belongs to a different run configuration. "
                "Use a new versioned output directory instead of mixing checkpoints."
            )
    else:
        if any(output_root.glob("fold_*/fold_complete.json")):
            raise ValueError("Completed fold outputs exist without a run configuration; refusing to mix runs.")
        _write_json(configuration_path, configuration)
    results = []
    for fold_number in fold_numbers:
        result = run_fold(
            package_root, output_root, fold_number, device=device,
            detector_epochs=detector_epochs, classifier_epochs=classifier_epochs,
            detector_batch=detector_batch, crop_batch=crop_batch,
            workers=workers, seed=seed, detector_weights=detector_weights,
        )
        results.append(result)
        # Keep partial OOF evidence if a later fold is interrupted.
        _write_json(output_root / "completed_folds.json", {"folds": results})
        oof_rows = [
            record
            for completed in results
            for record in completed["image_level_mgi_metrics"]["predicted_records"]
        ]
        oof_ids = [row["source_record_id"] for row in oof_rows]
        if len(oof_ids) != len(set(oof_ids)):
            raise ValueError("A Training image was scored more than once across folds.")
        summary = image_grade_metrics(oof_rows)
        summary["status"] = "complete_680_image_oof" if len(oof_rows) == 680 else "partial_oof_not_final"
        summary["detector_map50_95_by_fold"] = {
            str(item["fold"]): item["detector_mAP"]["map50_95"] for item in results
        }
        summary["detector_map50_by_fold"] = {
            str(item["fold"]): item["detector_mAP"]["map50"] for item in results
        }
        _write_json(output_root / "oof_metrics.json", summary)
        with (output_root / "oof_predictions.csv").open("w", encoding="utf-8", newline="") as stream:
            fields = ["source_record_id", "true_image_grade", "predicted_image_grade", "predicted_tooth_roi_count"]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(oof_rows)
    _write_json(output_root / "experiment_complete.json", {
        "status": "all_requested_folds_completed",
        "completed_fold_numbers": [result["fold"] for result in results],
        "n_oof_image_predictions": sum(len(row["image_level_mgi_metrics"]["predicted_records"]) for row in results),
        "qualified_labels_approved": False,
        "test_split_used": False,
    })
    return {"status": "complete", "folds": results, "records": len(image_manifest["records"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="0", help="Colab GPU index or mps/cpu for a local pilot")
    parser.add_argument("--detector-epochs", type=int, default=DEFAULT_DETECTOR_EPOCHS)
    parser.add_argument("--classifier-epochs", type=int, default=DEFAULT_CLASSIFIER_EPOCHS)
    parser.add_argument("--detector-batch", type=int, default=16)
    parser.add_argument("--crop-batch", type=int, default=64)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--detector-weights", default=DEFAULT_DETECTOR)
    parser.add_argument("--folds", default="0,1,2,3,4")
    args = parser.parse_args()
    fold_numbers = [int(value.strip()) for value in args.folds.split(",") if value.strip()]
    result = run_experiment(
        args.package, args.output, device=args.device,
        detector_epochs=args.detector_epochs,
        classifier_epochs=args.classifier_epochs,
        detector_batch=args.detector_batch, crop_batch=args.crop_batch,
        workers=args.workers, seed=args.seed,
        detector_weights=args.detector_weights, folds=fold_numbers,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
