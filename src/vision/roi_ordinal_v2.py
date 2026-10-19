"""Matched weighted-CE versus rank-consistent ordinal ROI experiment v2.

This module reuses the frozen v1 data protocol and fold-specific tooth detectors.
It never edits source labels, images, folds, or the existing v1 checkpoints.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import shutil
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

try:
    from .roi_colab_train_v1 import (
        CROP_PADDING,
        CROP_SIZE,
        DEFAULT_CLASSIFIER_EPOCHS,
        DETECTOR_CONFIDENCE,
        DETECTOR_IOU,
        IMAGE_SIZE,
        _read_package,
        _sha256_file,
        _torch_device_for_yolo,
    )
    from .roi_workflow_v1 import box_to_xyxy, image_grade_metrics
except ImportError:  # Colab loads these files from one code bundle directory.
    from roi_colab_train_v1 import (
        CROP_PADDING,
        CROP_SIZE,
        DEFAULT_CLASSIFIER_EPOCHS,
        DETECTOR_CONFIDENCE,
        DETECTOR_IOU,
        IMAGE_SIZE,
        _read_package,
        _sha256_file,
        _torch_device_for_yolo,
    )
    from roi_workflow_v1 import box_to_xyxy, image_grade_metrics


EXPERIMENT_NAME = "roi_crop_weighted_ce_vs_coral_v2"
SOURCE_PROTOCOL_SHA256 = "2253db0e89aad06a2fe49a90d313b7ae0e08a806b87845d49753b3d9e48dbc4b"
FOLD_ASSIGNMENT_SHA256 = "e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4"
DATASET_ZIP_SHA256 = "9b1e797f7f593438a5318410ed2aa1cfdd7a66b8db0aac865b3229b63d3a20c8"
IMAGE_MANIFEST_SHA256 = "975f4cde460b69c074b2655910f597623454b774dc27768d75f8002ce2ff1619"
V1_RETURN_ZIP_SHA256 = "ebb41badf4bd2154019dad55ba2f459ad1807c7f42b0722c13d849be2460f9bb"
RESNET18_IMAGENET1K_V1_SHA256 = "f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec"
CLASS_NAMES = ("MGI_0", "MGI_1", "MGI_2", "MGI_3", "MGI_4")
ARMS = ("weighted_ce", "coral")


def write_json(path: Path, value: Any) -> None:
    """Write a small run record in a stable, readable form."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    """Hash files in chunks so large packages do not need to fit in memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CoralHead(nn.Module):
    """Shared score with ordered thresholds for rank-consistent ordinal grades.

    The shared linear score follows the CORAL output structure. Positive gaps
    between threshold biases guarantee descending threshold logits at every
    training step, so predicted grade probabilities cannot reverse order.
    """

    def __init__(self, input_features: int, num_classes: int = 5):
        super().__init__()
        if num_classes < 2:
            raise ValueError("Ordinal classification needs at least two grades.")
        self.num_classes = int(num_classes)
        self.shared_score = nn.Linear(input_features, 1, bias=False)
        self.first_threshold = nn.Parameter(torch.tensor(0.0))
        self.raw_threshold_gaps = nn.Parameter(torch.zeros(num_classes - 2))

    def ordered_biases(self) -> torch.Tensor:
        """Return a strictly decreasing bias for each grade threshold."""

        if self.raw_threshold_gaps.numel() == 0:
            return self.first_threshold.reshape(1)
        positive_gaps = F.softplus(self.raw_threshold_gaps)
        remaining = self.first_threshold - torch.cumsum(positive_gaps, dim=0)
        return torch.cat((self.first_threshold.reshape(1), remaining))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        shared = self.shared_score(features)
        return shared + self.ordered_biases().unsqueeze(0)


def ordinal_targets(grades: torch.Tensor, num_classes: int = 5) -> torch.Tensor:
    """Turn grade y into threshold labels: 1 when y is above each threshold."""

    if grades.ndim != 1:
        raise ValueError("Grades must be a one-dimensional integer tensor.")
    if grades.numel() and (int(grades.min()) < 0 or int(grades.max()) >= num_classes):
        raise ValueError(f"Crop grades must be integers from 0 to {num_classes - 1}.")
    thresholds = torch.arange(num_classes - 1, device=grades.device)
    return (grades.long().unsqueeze(1) > thresholds.unsqueeze(0)).to(torch.float32)


def coral_class_probabilities(logits: torch.Tensor) -> torch.Tensor:
    """Convert ordered P(grade > threshold) logits to five grade probabilities."""

    if logits.ndim != 2 or logits.shape[1] < 1:
        raise ValueError("CORAL logits must have shape [batch, num_classes - 1].")
    threshold_probabilities = torch.sigmoid(logits)
    if torch.any(threshold_probabilities[:, :-1] + 1e-6 < threshold_probabilities[:, 1:]):
        raise ValueError("Ordinal threshold probabilities are not rank-consistent.")
    first = 1.0 - threshold_probabilities[:, :1]
    middle = threshold_probabilities[:, :-1] - threshold_probabilities[:, 1:]
    last = threshold_probabilities[:, -1:]
    probabilities = torch.cat((first, middle, last), dim=1).clamp_min(0.0)
    row_sums = probabilities.sum(dim=1)
    if not torch.allclose(row_sums, torch.ones_like(row_sums), atol=1e-5, rtol=0.0):
        raise ValueError("Ordinal grade probabilities do not sum to one.")
    return probabilities


def coral_grade_predictions(logits: torch.Tensor) -> torch.Tensor:
    """Use the ordinal median: count thresholds with probability above 0.5."""

    probabilities = torch.sigmoid(logits)
    if torch.any(probabilities[:, :-1] + 1e-6 < probabilities[:, 1:]):
        raise ValueError("Ordinal threshold probabilities are not rank-consistent.")
    return (probabilities >= 0.5).sum(dim=1).long()


def coral_loss(logits: torch.Tensor, grades: torch.Tensor) -> torch.Tensor:
    """Average binary cross-entropy across the batch and ordinal thresholds."""

    targets = ordinal_targets(grades, num_classes=logits.shape[1] + 1)
    return F.binary_cross_entropy_with_logits(logits, targets, reduction="mean")


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def _build_model(arm: str, *, pretrained: bool):
    from torchvision import models

    if arm not in ARMS:
        raise ValueError(f"Unknown classifier arm: {arm}")
    weights = models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
    model = models.resnet18(weights=weights)
    input_features = model.fc.in_features
    if arm == "weighted_ce":
        model.fc = nn.Linear(input_features, len(CLASS_NAMES))
    else:
        model.fc = CoralHead(input_features, num_classes=len(CLASS_NAMES))
    return model


def _image_transform():
    from torchvision import transforms

    return transforms.Compose([
        transforms.Resize((CROP_SIZE, CROP_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
    ])


def _dataset_loader(package_root: Path, rows: list[dict], *, batch_size: int,
                    workers: int, shuffle: bool, seed: int, device: str):
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset

    transform = _image_transform()

    class RoiCropDataset(Dataset):
        def __len__(self):
            return len(rows)

        def __getitem__(self, index):
            row = rows[index]
            crop_path = package_root / row["crop_path"]
            with Image.open(crop_path) as image:
                crop = transform(image.convert("RGB"))
            return crop, int(row["provisional_mgi_grade"])

    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        RoiCropDataset(), batch_size=batch_size, shuffle=shuffle,
        num_workers=workers, pin_memory=device.startswith("cuda"), generator=generator,
    )


def _fit_class_weights(fit_rows: list[dict], device: str) -> tuple[dict[str, int], torch.Tensor]:
    counts = Counter(int(row["provisional_mgi_grade"]) for row in fit_rows)
    if set(counts) != set(range(len(CLASS_NAMES))):
        raise ValueError(f"Every fit fold must contain all five crop grades: {dict(counts)}")
    weights = torch.tensor(
        [len(fit_rows) / (len(CLASS_NAMES) * counts[grade]) for grade in range(len(CLASS_NAMES))],
        dtype=torch.float32,
        device=device,
    )
    return {str(key): int(value) for key, value in sorted(counts.items())}, weights


def _checkpoint_payload(model: nn.Module, optimizer, epoch: int, history: list[dict],
                        *, config_sha256: str, arm: str, fold: int, seed: int,
                        fit_counts: dict[str, int], ce_weights: list[float] | None) -> dict:
    return {
        "status": "resumable_roi_ordinal_v2",
        "config_sha256": config_sha256,
        "arm": arm,
        "fold": int(fold),
        "epoch": int(epoch),
        "seed": int(seed),
        "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
        "optimizer_state": optimizer.state_dict(),
        "history": list(history),
        "class_counts_fit_only": fit_counts,
        "class_weights_fit_only": ce_weights,
    }


def _atomic_save_checkpoint(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    torch.save(payload, temporary)
    os.replace(temporary, path)


def _predict_crop_rows(model: nn.Module, package_root: Path, rows: list[dict], *,
                       arm: str, device: str, batch_size: int, workers: int,
                       seed: int) -> dict:
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

    loader = _dataset_loader(
        package_root, rows, batch_size=batch_size, workers=workers,
        shuffle=False, seed=seed, device=device,
    )
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    probability_rows: list[list[float]] = []
    with torch.no_grad():
        for crops, grades in loader:
            logits = model(crops.to(device))
            if arm == "coral":
                probabilities = coral_class_probabilities(logits)
                predictions = coral_grade_predictions(logits)
            else:
                probabilities = torch.softmax(logits, dim=1)
                predictions = logits.argmax(dim=1)
            probability_rows.extend(probabilities.cpu().tolist())
            y_true.extend(grades.tolist())
            y_pred.extend(predictions.cpu().tolist())
    recalls = {
        str(grade): (sum(t == grade and p == grade for t, p in zip(y_true, y_pred))
                     / sum(t == grade for t in y_true) if any(t == grade for t in y_true) else None)
        for grade in range(len(CLASS_NAMES))
    }
    present_recalls = [value for value in recalls.values() if value is not None]
    return {
        "n_crops": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)) if y_true else None,
        "macro_f1": float(f1_score(y_true, y_pred, labels=list(range(5)), average="macro", zero_division=0)) if y_true else None,
        "balanced_accuracy": float(sum(present_recalls) / len(present_recalls)) if present_recalls else None,
        "per_grade_recall": recalls,
        "confusion_matrix_labels": list(range(5)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(range(5))).tolist(),
        "probability_rows": probability_rows,
    }


def _train_arm(package_root: Path, fit_rows: list[dict], score_rows: list[dict],
               arm_root: Path, *, arm: str, fold: int, seed: int, device: str,
               epochs: int, batch_size: int, workers: int, learning_rate: float,
               config_sha256: str, pretrained: bool = True) -> dict:
    """Fit one classifier arm and score its held-fold source-annotation crops."""

    from torch.utils.data import DataLoader

    _seed_everything(seed)
    fit_counts, class_weights = _fit_class_weights(fit_rows, device)
    train_loader = _dataset_loader(
        package_root, fit_rows, batch_size=batch_size, workers=workers,
        shuffle=True, seed=seed, device=device,
    )
    checkpoint_path = arm_root / "checkpoint_last.pt"
    model = _build_model(arm, pretrained=pretrained and not checkpoint_path.exists()).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    start_epoch = 0
    history: list[dict] = []
    if checkpoint_path.is_file():
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if state.get("config_sha256") != config_sha256 or state.get("arm") != arm or int(state.get("fold", -1)) != fold:
            raise ValueError(f"Checkpoint does not match this run: {checkpoint_path}")
        model.load_state_dict(state["model_state"])
        optimizer.load_state_dict(state["optimizer_state"])
        start_epoch = int(state["epoch"])
        history = list(state.get("history", []))
        if start_epoch > epochs:
            raise ValueError("Checkpoint epoch exceeds the fixed training budget.")

    ce_weight_values = class_weights.detach().cpu().tolist() if arm == "weighted_ce" else None
    for epoch in range(start_epoch, epochs):
        # Recreate this epoch's shuffle after a runtime restart, not epoch one's order.
        train_loader.generator.manual_seed(seed + epoch)
        model.train()
        loss_sum = 0.0
        sample_count = 0
        for crops, grades in train_loader:
            crops = crops.to(device, non_blocking=device.startswith("cuda"))
            grades = grades.to(device, non_blocking=device.startswith("cuda"))
            optimizer.zero_grad(set_to_none=True)
            logits = model(crops)
            if arm == "weighted_ce":
                loss = F.cross_entropy(logits, grades, weight=class_weights)
            else:
                loss = coral_loss(logits, grades)
            if not torch.isfinite(loss):
                raise FloatingPointError(f"Non-finite {arm} loss in fold {fold}, epoch {epoch + 1}.")
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach().cpu()) * len(grades)
            sample_count += len(grades)
        history.append({"epoch": epoch + 1, "fit_loss": loss_sum / max(sample_count, 1)})
        _atomic_save_checkpoint(
            checkpoint_path,
            _checkpoint_payload(
                model, optimizer, epoch + 1, history,
                config_sha256=config_sha256, arm=arm, fold=fold, seed=seed,
                fit_counts=fit_counts, ce_weights=ce_weight_values,
            ),
        )

    crop_metrics = _predict_crop_rows(
        model, package_root, score_rows, arm=arm, device=device,
        batch_size=batch_size, workers=workers, seed=seed,
    )
    crop_metrics.pop("probability_rows")
    result = {
        "status": "complete",
        "arm": arm,
        "fold": fold,
        "epochs_completed": len(history),
        "fit_images": len({row["parent_record_id"] for row in fit_rows}),
        "fit_crops": len(fit_rows),
        "score_crops": len(score_rows),
        "class_counts_fit_only": fit_counts,
        "class_weights_fit_only": ce_weight_values,
        "history": history,
        "oracle_crop_metrics": crop_metrics,
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": file_sha256(checkpoint_path),
        "config_sha256": config_sha256,
    }
    write_json(arm_root / "arm_metrics.json", result)
    del model, optimizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def _load_trained_arm(arm_root: Path, arm: str, *, device: str):
    state = torch.load(arm_root / "checkpoint_last.pt", map_location="cpu", weights_only=False)
    model = _build_model(arm, pretrained=False)
    model.load_state_dict(state["model_state"])
    return model.to(device).eval()


def _image_crop_tensors(image_path: Path, xyxy_boxes: list[list[float]]) -> list[torch.Tensor]:
    from PIL import Image

    transform = _image_transform()
    crops: list[torch.Tensor] = []
    with Image.open(image_path) as source:
        source = source.convert("RGB")
        for x1, y1, x2, y2 in xyxy_boxes:
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
    return crops


def _predict_two_arms_with_detector(detector, ce_model: nn.Module, coral_model: nn.Module,
                                    image_paths: list[Path], *, device: str,
                                    detector_batch: int, crop_batch: int) -> dict[str, list[dict]]:
    """Run one frozen detector pass and score each detected crop with both heads."""

    ce_records: list[dict] = []
    coral_records: list[dict] = []
    yolo_device = device.split(":", 1)[1] if device.startswith("cuda:") else device
    for start in range(0, len(image_paths), detector_batch):
        batch_paths = image_paths[start:start + detector_batch]
        detections = detector.predict(
            source=[str(path) for path in batch_paths], imgsz=IMAGE_SIZE,
            conf=DETECTOR_CONFIDENCE, iou=DETECTOR_IOU,
            device=yolo_device, save=False, verbose=False,
        )
        for result in detections:
            image_path = Path(result.path)
            record_id = f"Training/{image_path.stem}"
            boxes = result.boxes.xyxy.detach().cpu().tolist() if result.boxes is not None else []
            if result.boxes is not None and any(
                int(value) != 0 for value in result.boxes.cls.detach().cpu().tolist()
            ):
                raise ValueError("The frozen v1 detector must contain only tooth_roi class 0.")
            crops = _image_crop_tensors(image_path, boxes) if boxes else []
            ce_grades: list[int] = []
            coral_grades: list[int] = []
            for crop_start in range(0, len(crops), crop_batch):
                crop_tensor = torch.stack(crops[crop_start:crop_start + crop_batch]).to(device)
                with torch.no_grad():
                    ce_logits = ce_model(crop_tensor)
                    coral_logits = coral_model(crop_tensor)
                    ce_grades.extend(ce_logits.argmax(dim=1).cpu().tolist())
                    coral_grades.extend(coral_grade_predictions(coral_logits).cpu().tolist())
            ce_records.append({
                "source_record_id": record_id,
                "predicted_image_grade": max(ce_grades) if ce_grades else None,
                "predicted_tooth_roi_count": len(ce_grades),
            })
            coral_records.append({
                "source_record_id": record_id,
                "predicted_image_grade": max(coral_grades) if coral_grades else None,
                "predicted_tooth_roi_count": len(coral_grades),
            })
    return {"weighted_ce": ce_records, "coral": coral_records}


def _add_image_metrics(records: list[dict], true_grade_by_id: dict[str, int]) -> dict:
    from sklearn.metrics import cohen_kappa_score, mean_absolute_error

    completed = []
    for row in records:
        completed.append({
            **row,
            "true_image_grade": int(true_grade_by_id[row["source_record_id"]]),
        })
    metrics = image_grade_metrics(completed)
    y_true = [row["true_image_grade"] for row in completed]
    has_abstention = any(row["predicted_image_grade"] is None for row in completed)
    if has_abstention:
        metrics["quadratic_weighted_kappa"] = None
        metrics["ordinal_mae"] = None
        metrics["ordinal_metrics_note"] = (
            "Not computed because an ROI abstention has no ordinal image-grade value; abstentions remain incorrect in accuracy."
        )
    else:
        y_pred = [int(row["predicted_image_grade"]) for row in completed]
        qwk = cohen_kappa_score(y_true, y_pred, labels=[0, 1, 2, 3, 4], weights="quadratic")
        metrics["quadratic_weighted_kappa"] = float(qwk) if math.isfinite(float(qwk)) else None
        metrics["ordinal_mae"] = float(mean_absolute_error(y_true, y_pred)) if y_true else None
    metrics["probability_metrics_note"] = (
        "Image-level AUROC/Brier omitted: max-over-ROIs does not define a validated image probability."
    )
    metrics["predicted_records"] = completed
    return metrics


def _paired_group_bootstrap(ce_rows: list[dict], coral_rows: list[dict],
                            group_by_id: dict[str, str], *, repetitions: int = 1000,
                            seed: int = 42) -> dict:
    from sklearn.metrics import accuracy_score, f1_score

    ce_by_id = {row["source_record_id"]: row for row in ce_rows}
    coral_by_id = {row["source_record_id"]: row for row in coral_rows}
    ids = sorted(set(ce_by_id) & set(coral_by_id) & set(group_by_id))
    grouped: dict[str, list[str]] = defaultdict(list)
    for record_id in ids:
        grouped[group_by_id[record_id]].append(record_id)
    groups = sorted(grouped)
    rng = np.random.default_rng(seed)
    metric_values: dict[str, list[float]] = {
        "accuracy": [], "macro_f1": [], "balanced_accuracy": [],
        "grade1_recall": [], "grade2_recall": [],
    }
    undefined = 0
    for _ in range(repetitions):
        sampled_groups = rng.choice(groups, size=len(groups), replace=True)
        sampled_ids = [record_id for group_id in sampled_groups for record_id in grouped[str(group_id)]]
        y = [int(ce_by_id[item]["true_image_grade"]) for item in sampled_ids]
        ce = [ce_by_id[item]["predicted_image_grade"] for item in sampled_ids]
        coral = [coral_by_id[item]["predicted_image_grade"] for item in sampled_ids]
        if any(value is None for value in ce + coral) or not all(any(value == grade for value in y) for grade in (1, 2, 3, 4)):
            undefined += 1
            continue
        ce = [int(value) for value in ce]
        coral = [int(value) for value in coral]
        metric_values["accuracy"].append(float(accuracy_score(y, coral) - accuracy_score(y, ce)))
        metric_values["macro_f1"].append(float(
            f1_score(y, coral, labels=[1, 2, 3, 4], average="macro", zero_division=0)
            - f1_score(y, ce, labels=[1, 2, 3, 4], average="macro", zero_division=0)
        ))
        recalls = {}
        for predictions, prefix in ((ce, "ce"), (coral, "coral")):
            for grade in (1, 2, 3, 4):
                support = sum(value == grade for value in y)
                recalls[f"{prefix}_{grade}"] = sum(
                    true == grade and predicted == grade for true, predicted in zip(y, predictions)
                ) / support
        metric_values["balanced_accuracy"].append(float(
            sum(recalls[f"coral_{grade}"] - recalls[f"ce_{grade}"] for grade in (1, 2, 3, 4)) / 4
        ))
        metric_values["grade1_recall"].append(recalls["coral_1"] - recalls["ce_1"])
        metric_values["grade2_recall"].append(recalls["coral_2"] - recalls["ce_2"])
    intervals = {}
    for name, values in metric_values.items():
        intervals[name] = (
            [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]
            if values else None
        )
    return {
        "repetitions": repetitions,
        "seed": seed,
        "groups": len(groups),
        "undefined_draws": undefined,
        "interpretation": "Conditional intervals for fixed paired OOF predictions; they do not include refitting uncertainty.",
        "coral_minus_weighted_ce_95_percent_intervals": intervals,
    }


def _verify_detector_return(detector_root: Path) -> dict[str, str]:
    manifest_path = detector_root / "return_integrity_manifest.csv"
    completion_path = detector_root / "experiment_complete.json"
    if not manifest_path.is_file() or not completion_path.is_file():
        raise FileNotFoundError("The extracted v1 return bundle is incomplete.")
    completion = json.loads(completion_path.read_text())
    if completion.get("status") != "all_requested_folds_completed" or completion.get("test_split_used") is not False:
        raise ValueError("The source v1 return bundle is incomplete or has unexpected Test use.")
    entries = {}
    with manifest_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            file_path = detector_root / row["path"]
            if not file_path.is_file() or file_path.stat().st_size != int(row["bytes"]):
                raise ValueError(f"Missing or wrong-sized source return file: {row['path']}")
            digest = file_sha256(file_path)
            if digest != row["sha256"]:
                raise ValueError(f"Source return file hash mismatch: {row['path']}")
            entries[row["path"]] = digest
    detector_hashes = {}
    for fold in range(5):
        name = f"fold_{fold:02d}/detector_last.pt"
        if name not in entries:
            raise ValueError(f"The source return bundle has no detector for fold {fold}.")
        detector_hashes[str(fold)] = entries[name]
    return detector_hashes


def _validate_data_protocol(package_root: Path) -> tuple[dict, dict, list[dict]]:
    image_manifest, folds_data, crop_rows = _read_package(package_root)
    if file_sha256(package_root / "image_manifest.json") != IMAGE_MANIFEST_SHA256:
        raise ValueError("Image manifest hash changed; do not continue with altered labels or source records.")
    if folds_data.get("source_protocol_sha256") != SOURCE_PROTOCOL_SHA256:
        raise ValueError("Unexpected fold protocol; do not regenerate or alter the published folds.")
    if folds_data.get("fold_assignment_sha256") != FOLD_ASSIGNMENT_SHA256:
        raise ValueError("Fold assignments do not match the verified 680-image reference.")
    if image_manifest.get("qualified_labels_approved") is not False:
        raise ValueError("Provisional labels must remain unapproved for this experiment.")
    training_ids = [row["source_record_id"] for row in image_manifest["records"] if row["original_split"] == "Training"]
    validation_ids = [row["source_record_id"] for row in image_manifest["records"] if row["original_split"] == "Validation"]
    if len(training_ids) != 680 or len(set(training_ids)) != 680 or len(validation_ids) != 53:
        raise ValueError("The allowlisted 680/53 development inventory changed.")
    if any(not item.startswith("Training/") for item in training_ids + [
        record_id for fold in folds_data["folds"] for record_id in fold["fit_ids"] + fold["score_ids"]
    ]):
        raise ValueError("Only the frozen Training records may be fit or scored.")
    return image_manifest, folds_data, crop_rows


def _run_fold(package_root: Path, detector_root: Path, output_root: Path,
              fold_data: dict, image_manifest: dict, crop_rows: list[dict], *,
              device: str, epochs: int, batch_size: int, detector_batch: int,
              workers: int, seed: int, learning_rate: float, config_sha256: str) -> dict:
    from ultralytics import YOLO

    fold = int(fold_data["fold"])
    fit_ids = list(fold_data["fit_ids"])
    score_ids = list(fold_data["score_ids"])
    if len(fit_ids) != 544 or len(score_ids) != 136 or set(fit_ids) & set(score_ids):
        raise ValueError(f"Fold {fold} no longer has the frozen 544/136 no-overlap split.")
    record_by_id = {row["source_record_id"]: row for row in image_manifest["records"]}
    fit_groups = {record_by_id[item]["content_group_id"] for item in fit_ids}
    score_groups = {record_by_id[item]["content_group_id"] for item in score_ids}
    if fit_groups & score_groups:
        raise ValueError(f"Known content group crosses fold {fold}.")
    fit_rows = [row for row in crop_rows if row["parent_record_id"] in set(fit_ids)]
    score_rows = [row for row in crop_rows if row["parent_record_id"] in set(score_ids)]
    if len(fit_rows) != 6528 or len(score_rows) != 1632:
        raise ValueError(f"Fold {fold} crop counts differ from the frozen package.")
    if {int(row["outer_fold"]) for row in score_rows} != {fold}:
        raise ValueError(f"Crop manifest disagrees with score fold {fold}.")

    fold_root = output_root / f"fold_{fold:02d}"
    arm_metrics = {}
    for arm in ARMS:
        arm_root = fold_root / arm
        metrics_path = arm_root / "arm_metrics.json"
        if metrics_path.is_file():
            result = json.loads(metrics_path.read_text())
            if result.get("config_sha256") != config_sha256 or result.get("status") != "complete":
                raise ValueError(f"Existing {arm} output does not match this run configuration.")
            checkpoint_path = arm_root / "checkpoint_last.pt"
            if not checkpoint_path.is_file() or file_sha256(checkpoint_path) != result.get("checkpoint_sha256"):
                raise ValueError(f"Existing {arm} checkpoint failed its saved hash check.")
            arm_metrics[arm] = result
        else:
            arm_metrics[arm] = _train_arm(
                package_root, fit_rows, score_rows, arm_root,
                arm=arm, fold=fold, seed=seed + fold, device=device,
                epochs=epochs, batch_size=batch_size, workers=workers,
                learning_rate=learning_rate, config_sha256=config_sha256,
            )

    ce_model = _load_trained_arm(fold_root / "weighted_ce", "weighted_ce", device=device)
    coral_model = _load_trained_arm(fold_root / "coral", "coral", device=device)
    detector_path = detector_root / f"fold_{fold:02d}" / "detector_last.pt"
    detector = YOLO(str(detector_path))
    score_paths = [
        package_root / "images" / "Training" / f"{record_id.split('/')[-1]}.jpg"
        for record_id in score_ids
    ]
    if any(not path.is_file() for path in score_paths):
        raise FileNotFoundError(f"Fold {fold} score image is missing from the approved package.")
    image_predictions = _predict_two_arms_with_detector(
        detector, ce_model, coral_model, score_paths,
        device=device, detector_batch=detector_batch, crop_batch=batch_size,
    )
    true_grade = {row["source_record_id"]: int(row["provisional_image_mgi_grade"])
                  for row in image_manifest["records"]}
    enriched = {}
    for arm in ARMS:
        rows = image_predictions[arm]
        if {row["source_record_id"] for row in rows} != set(score_ids):
            raise ValueError(f"Fold {fold} {arm} output does not cover each score image exactly once.")
        enriched[arm] = _add_image_metrics(rows, true_grade)
    result = {
        "status": "complete",
        "fold": fold,
        "fit_images": len(fit_ids),
        "score_images": len(score_ids),
        "fit_crops": len(fit_rows),
        "score_crops": len(score_rows),
        "detector_checkpoint_sha256": file_sha256(detector_path),
        "detector_source": "fixed v1 fold-specific checkpoint; no detector training in v2",
        "full_model_selection_on_score_fold": False,
        "weighted_ce": {**arm_metrics["weighted_ce"], "image_level_metrics": enriched["weighted_ce"]},
        "coral": {**arm_metrics["coral"], "image_level_metrics": enriched["coral"]},
    }
    write_json(fold_root / "fold_metrics.json", result)
    del detector, ce_model, coral_model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return result


def _aggregate_oof(results: list[dict], image_manifest: dict, output_root: Path,
                   *, complete: bool) -> dict:
    summaries = {}
    group_by_id = {row["source_record_id"]: row["content_group_id"]
                   for row in image_manifest["records"] if row["original_split"] == "Training"}
    all_rows = {}
    for arm in ARMS:
        rows = [row for result in results for row in result[arm]["image_level_metrics"]["predicted_records"]]
        ids = [row["source_record_id"] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{arm} has duplicate out-of-fold image predictions.")
        all_rows[arm] = rows
        summary = _add_image_metrics(rows, {row["source_record_id"]: int(row["true_image_grade"])
                                            for row in rows}) if rows else {"n_images": 0}
        summary.pop("predicted_records", None)
        summary["status"] = "complete_680_image_oof" if complete and len(rows) == 680 else "partial_oof_not_final"
        summary["n_images"] = len(rows)
        summaries[arm] = summary
        output_path = output_root / f"{arm}_oof_predictions.csv"
        with output_path.open("w", encoding="utf-8", newline="") as stream:
            fields = ["source_record_id", "true_image_grade", "predicted_image_grade", "predicted_tooth_roi_count"]
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    paired = _paired_group_bootstrap(
        all_rows["weighted_ce"], all_rows["coral"], group_by_id,
    ) if complete else None
    output = {
        "status": "complete_680_image_oof" if complete else "partial_oof_not_final",
        "n_images_per_arm": {arm: summaries[arm].get("n_images", 0) for arm in ARMS},
        "metrics": summaries,
        "paired_bootstrap_coral_minus_weighted_ce": paired,
        "detector_metrics_note": "The detector is fixed from v1; v1 localization mAP is unchanged and not re-estimated.",
        "label_status": "provisional caption-derived image grades and source-TXT tooth grades; qualified_labels_approved=false",
        "test_split_used": False,
    }
    write_json(output_root / "oof_metrics.json", output)
    return output


def run_experiment(package_root: Path, detector_root: Path, output_root: Path, *,
                   dataset_zip_sha256: str = DATASET_ZIP_SHA256,
                   v1_return_zip_sha256: str = V1_RETURN_ZIP_SHA256,
                   code_bundle_sha256: str = "",
                   device: str = "cuda:0", epochs: int = DEFAULT_CLASSIFIER_EPOCHS,
                   batch_size: int = 64, detector_batch: int = 16, workers: int = 2,
                   seed: int = 42, learning_rate: float = 1e-4) -> dict:
    """Run both classifier arms on the same five fixed Training folds."""

    from torchvision import models
    import torchvision
    import ultralytics

    if not torch.cuda.is_available() or not device.startswith("cuda"):
        raise RuntimeError("This bounded Colab comparison requires a CUDA GPU; do not fall back to CPU.")
    if epochs != 12 or batch_size != 64 or detector_batch != 16:
        raise ValueError("This experiment uses its predeclared 12-epoch, batch-64/batch-16 configuration.")
    package_root = package_root.resolve()
    detector_root = detector_root.resolve()
    output_root = output_root.resolve()
    image_manifest, folds_data, crop_rows = _validate_data_protocol(package_root)
    detector_hashes = _verify_detector_return(detector_root)
    if dataset_zip_sha256 != DATASET_ZIP_SHA256 or v1_return_zip_sha256 != V1_RETURN_ZIP_SHA256:
        raise ValueError("Input ZIP hash does not match the verified v1 experiment artifacts.")
    if len(code_bundle_sha256) != 64 or any(char not in "0123456789abcdef" for char in code_bundle_sha256):
        raise ValueError("Pass the verified 64-character lowercase SHA-256 for this Colab code bundle.")

    weights = models.ResNet18_Weights.IMAGENET1K_V1
    weight_filename = Path(weights.url.split("/")[-1])
    weight_path = Path(torch.hub.get_dir()) / "checkpoints" / weight_filename
    if not weight_path.is_file():
        weights.get_state_dict(progress=True, check_hash=True)
    weight_sha = file_sha256(weight_path)
    if weight_sha != RESNET18_IMAGENET1K_V1_SHA256:
        raise ValueError("Official ResNet18 ImageNet V1 weight hash changed; stop before fitting.")

    config = {
        "experiment": EXPERIMENT_NAME,
        "dataset_zip_sha256": dataset_zip_sha256,
        "code_bundle_sha256": code_bundle_sha256,
        "dataset_manifest_sha256": file_sha256(package_root / "image_manifest.json"),
        "source_protocol_sha256": folds_data["source_protocol_sha256"],
        "fold_assignment_sha256": folds_data["fold_assignment_sha256"],
        "source_code_sha256": {
            Path(__file__).name: file_sha256(Path(__file__).resolve()),
            "roi_colab_train_v1.py": file_sha256(Path(__file__).with_name("roi_colab_train_v1.py")),
            "roi_workflow_v1.py": file_sha256(Path(__file__).with_name("roi_workflow_v1.py")),
        },
        "v1_return_zip_sha256": v1_return_zip_sha256,
        "detector_checkpoint_sha256_by_fold": detector_hashes,
        "training_images": 680,
        "fit_images_per_fold": 544,
        "score_images_per_fold": 136,
        "fit_crops_per_fold": 6528,
        "score_crops_per_fold": 1632,
        "validation_images_used_for_selection": 0,
        "test_split_used": False,
        "qualified_labels_approved": False,
        "arms": list(ARMS),
        "weighted_ce": "ResNet18 ImageNet1K V1; fit-fold inverse-frequency class weights; five-way cross-entropy",
        "coral": "ResNet18 ImageNet1K V1; shared score with strictly ordered threshold biases; unweighted mean threshold BCE",
        "crop_classifier_initial_weights": weight_sha,
        "epochs": epochs,
        "batch_size": batch_size,
        "detector_batch": detector_batch,
        "learning_rate": learning_rate,
        "optimizer": "AdamW",
        "seed": seed,
        "device": device,
        "gpu_name": torch.cuda.get_device_name(torch.device(device)),
        "torch_version": torch.__version__,
        "torchvision_version": torchvision.__version__,
        "ultralytics_version": ultralytics.__version__,
        "v1_detector_confidence": DETECTOR_CONFIDENCE,
        "v1_detector_iou": DETECTOR_IOU,
        "crop_padding_fraction_each_side": CROP_PADDING,
        "crop_size": CROP_SIZE,
        "source_labels": "unchanged provisional v1 crop labels and caption-derived image grades",
    }
    config_sha256 = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    config_path = output_root / "run_configuration.json"
    if config_path.exists():
        previous = json.loads(config_path.read_text())
        previous_config = {key: value for key, value in previous.items() if key != "config_sha256"}
        if previous_config != config or previous.get("config_sha256") != config_sha256:
            raise ValueError("Output directory belongs to another run. Preserve it and select a new versioned output path.")
    else:
        if any(output_root.glob("fold_*/**/checkpoint_last.pt")):
            raise ValueError("Checkpoints exist without their run configuration; refusing to mix runs.")
        write_json(config_path, {**config, "config_sha256": config_sha256})

    results = []
    for fold_data in sorted(folds_data["folds"], key=lambda row: int(row["fold"])):
        fold_number = int(fold_data["fold"])
        fold_complete = output_root / f"fold_{fold_number:02d}" / "fold_metrics.json"
        if fold_complete.is_file():
            result = json.loads(fold_complete.read_text())
            if result.get("status") != "complete":
                raise ValueError(f"Existing fold {fold_number} output is not complete.")
            results.append(result)
        else:
            result = _run_fold(
                package_root, detector_root, output_root, fold_data,
                image_manifest, crop_rows, device=device, epochs=epochs,
                batch_size=batch_size, detector_batch=detector_batch,
                workers=workers, seed=seed, learning_rate=learning_rate,
                config_sha256=config_sha256,
            )
            results.append(result)
        _aggregate_oof(results, image_manifest, output_root, complete=len(results) == 5)
        write_json(output_root / "completed_folds.json", {
            "completed_fold_numbers": [int(row["fold"]) for row in results],
            "n_completed_folds": len(results),
        })

    metrics = _aggregate_oof(results, image_manifest, output_root, complete=True)
    completion = {
        "status": "all_requested_folds_completed",
        "arms": list(ARMS),
        "n_oof_image_predictions_per_arm": metrics["n_images_per_arm"],
        "test_split_used": False,
        "validation_used_for_model_selection": False,
        "qualified_labels_approved": False,
        "config_sha256": config_sha256,
    }
    write_json(output_root / "experiment_complete.json", completion)
    return {"status": "complete", "output_root": str(output_root), "metrics": metrics,
            "completion": completion}


def create_return_bundle(output_root: Path, detector_root: Path, return_zip: Path) -> dict:
    """Package only the new CORAL checkpoints and evidence, preserving old bundles."""

    output_root = output_root.resolve()
    detector_root = detector_root.resolve()
    return_zip = return_zip.resolve()
    if return_zip.exists():
        with zipfile.ZipFile(return_zip) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"Existing v2 return archive is corrupt at {bad_member}; preserve it.")
            names = set(archive.namelist())
            required = {"run_configuration.json", "experiment_complete.json", "return_integrity_manifest.csv"}
            if not required.issubset(names):
                raise ValueError("Existing v2 return ZIP is not a complete ordinal bundle; preserve it and use a new name.")
            embedded_config = json.loads(archive.read("run_configuration.json"))
            local_config = json.loads((output_root / "run_configuration.json").read_text())
            if embedded_config != local_config:
                raise ValueError("Existing v2 return ZIP belongs to another run; preserve it and use a new name.")
            with archive.open("return_integrity_manifest.csv") as stream:
                for row in csv.DictReader(__import__("io").TextIOWrapper(stream, encoding="utf-8")):
                    if row["path"] not in names:
                        raise ValueError(f"Existing v2 return ZIP is missing {row['path']}.")
                    payload = archive.read(row["path"])
                    digest = hashlib.sha256(payload).hexdigest()
                    if len(payload) != int(row["bytes"]) or digest != row["sha256"]:
                        raise ValueError(f"Existing v2 return ZIP failed its internal hash at {row['path']}.")
        return {"status": "existing_return_preserved", "path": str(return_zip),
                "sha256": file_sha256(return_zip)}
    completion = json.loads((output_root / "experiment_complete.json").read_text())
    if completion.get("status") != "all_requested_folds_completed":
        raise ValueError("All five folds must finish before a return ZIP can be created.")
    bundle = output_root / "return_bundle"
    if bundle.exists():
        raise FileExistsError("A partial return_bundle exists. Preserve it and use a new versioned output folder.")
    bundle.mkdir(parents=True)
    for name in ("run_configuration.json", "oof_metrics.json", "weighted_ce_oof_predictions.csv",
                 "coral_oof_predictions.csv", "experiment_complete.json", "completed_folds.json"):
        shutil.copy2(output_root / name, bundle / name)
    for fold in range(5):
        fold_name = f"fold_{fold:02d}"
        target = bundle / fold_name
        target.mkdir()
        shutil.copy2(output_root / fold_name / "coral" / "checkpoint_last.pt", target / "coral_classifier_last.pt")
        shutil.copy2(detector_root / fold_name / "detector_last.pt", target / "detector_last.pt")
        shutil.copy2(output_root / fold_name / "fold_metrics.json", target / "fold_metrics.json")
    manifest_path = bundle / "return_integrity_manifest.csv"
    manifest_rows = []
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path != manifest_path:
            manifest_rows.append({
                "path": str(path.relative_to(bundle)),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            })
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    temporary_zip = return_zip.with_suffix(".tmp")
    with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=str(path.relative_to(bundle)))
    with zipfile.ZipFile(temporary_zip) as archive:
        bad_member = archive.testzip()
    if bad_member is not None:
        temporary_zip.unlink(missing_ok=True)
        raise ValueError(f"New return archive CRC failed at {bad_member}.")
    os.replace(temporary_zip, return_zip)
    return {"status": "created", "path": str(return_zip), "bytes": return_zip.stat().st_size,
            "sha256": file_sha256(return_zip), "manifest_entries": len(manifest_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--detector-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dataset-zip-sha256", default=DATASET_ZIP_SHA256)
    parser.add_argument("--v1-return-zip-sha256", default=V1_RETURN_ZIP_SHA256)
    parser.add_argument("--code-bundle-sha256", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--epochs", type=int, default=DEFAULT_CLASSIFIER_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--detector-batch", type=int, default=16)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = run_experiment(
        args.package_root, args.detector_root, args.output_root,
        dataset_zip_sha256=args.dataset_zip_sha256,
        v1_return_zip_sha256=args.v1_return_zip_sha256,
        code_bundle_sha256=args.code_bundle_sha256,
        device=args.device, epochs=args.epochs, batch_size=args.batch_size,
        detector_batch=args.detector_batch, workers=args.workers, seed=args.seed,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
