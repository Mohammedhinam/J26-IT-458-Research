
from pathlib import Path
import csv

import cv2
import numpy as np
from ultralytics import YOLO


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE = Path(
    r"C:\Users\MSI\Documents\Research\DentalImages\archive\datasets"
)

MODEL_PATH = (
    BASE / "runs" / "segment"
    / "plaque_yolov8n_baseline" / "weights" / "best.pt"
)

DATASET = BASE / "Plaque_Segmentation" / "Plaque_YOLO_Clean"

# IMPORTANT: Use VALIDATION data, not TEST data.
VALID_IMAGES = DATASET / "valid" / "images"
VALID_LABELS = DATASET / "valid" / "labels"

OUTPUT_DIR = BASE / "Plaque_Evaluation_Results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DETAIL_CSV = (
    OUTPUT_DIR / "plaque_validation_threshold_per_image.csv"
)

SUMMARY_CSV = (
    OUTPUT_DIR / "plaque_validation_threshold_comparison.csv"
)

CONFIDENCE_THRESHOLDS = [0.10, 0.25, 0.40, 0.50]

IMAGE_SIZE = 640
DEVICE = 0

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp"
}


# ============================================================
# 2. VERIFY INPUTS
# ============================================================

if not MODEL_PATH.is_file():
    raise FileNotFoundError(
        f"Trained model not found: {MODEL_PATH}"
    )

if not VALID_IMAGES.is_dir():
    raise FileNotFoundError(
        f"Validation images not found: {VALID_IMAGES}"
    )

if not VALID_LABELS.is_dir():
    raise FileNotFoundError(
        f"Validation labels not found: {VALID_LABELS}"
    )

image_files = sorted(
    path
    for path in VALID_IMAGES.iterdir()
    if path.is_file()
    and path.suffix.lower() in IMAGE_EXTENSIONS
)

if not image_files:
    raise RuntimeError("No validation images found.")

print("=" * 70)
print("PLAQUE SEGMENTATION - CONFIDENCE THRESHOLD OPTIMIZATION")
print("=" * 70)
print(f"Model: {MODEL_PATH}")
print(f"Validation images: {len(image_files)}")
print(f"Thresholds: {CONFIDENCE_THRESHOLDS}")
print(f"Image size: {IMAGE_SIZE}")
print("=" * 70)

model = YOLO(str(MODEL_PATH))


# ============================================================
# 3. LOAD GROUND-TRUTH SEGMENTATION MASK
# ============================================================

def load_ground_truth_mask(image_path, height, width):

    label_path = (
        VALID_LABELS / f"{image_path.stem}.txt"
    )

    if not label_path.is_file():
        raise FileNotFoundError(
            f"Missing validation label: {label_path}"
        )

    gt_mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    with label_path.open(
        "r", encoding="utf-8-sig"
    ) as file:

        for line_number, line in enumerate(
            file, start=1
        ):

            values = line.strip().split()

            if not values:
                continue

            if (
                len(values) < 7
                or (len(values) - 1) % 2 != 0
            ):
                raise ValueError(
                    f"Invalid polygon in "
                    f"{label_path.name}, "
                    f"line {line_number}"
                )

            class_id = int(values[0])

            if class_id != 0:
                raise ValueError(
                    f"Unexpected class {class_id} "
                    f"in {label_path.name}"
                )

            coordinates = np.array(
                [
                    float(value)
                    for value in values[1:]
                ],
                dtype=np.float32
            ).reshape(-1, 2)

            if not np.isfinite(coordinates).all():
                raise ValueError(
                    f"Invalid coordinates in "
                    f"{label_path.name}"
                )

            coordinates[:, 0] *= width
            coordinates[:, 1] *= height

            polygon = np.round(
                coordinates
            ).astype(np.int32)

            cv2.fillPoly(
                gt_mask,
                [polygon],
                1
            )

    return gt_mask


# ============================================================
# 4. GENERATE PREDICTED PLAQUE MASK
# ============================================================

def predict_plaque_mask(
    model, image_path, height, width, confidence
):

    results = model.predict(
        source=str(image_path),
        imgsz=IMAGE_SIZE,
        conf=confidence,
        device=DEVICE,
        verbose=False
    )

    predicted_mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    result = results[0]

    if result.masks is not None:

        for polygon in result.masks.xy:

            if len(polygon) >= 3:

                polygon = np.round(
                    polygon
                ).astype(np.int32)

                cv2.fillPoly(
                    predicted_mask,
                    [polygon],
                    1
                )

    return predicted_mask


# ============================================================
# 5. CALCULATE PIXEL-LEVEL METRICS
# ============================================================

def calculate_metrics(gt_mask, pred_mask):

    gt_positive = gt_mask.astype(bool)
    pred_positive = pred_mask.astype(bool)

    tp = int(
        np.logical_and(
            gt_positive,
            pred_positive
        ).sum()
    )

    fp = int(
        np.logical_and(
            ~gt_positive,
            pred_positive
        ).sum()
    )

    fn = int(
        np.logical_and(
            gt_positive,
            ~pred_positive
        ).sum()
    )

    union = tp + fp + fn

    iou = (
        tp / union
        if union > 0
        else 1.0
    )

    dice_denominator = 2 * tp + fp + fn

    dice = (
        2 * tp / dice_denominator
        if dice_denominator > 0
        else 1.0
    )

    precision = (
        tp / (tp + fp)
        if tp + fp > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0
        else 0.0
    )

    # Binary foreground pixel F1 equals Dice.
    f1 = dice

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "iou": float(iou),
        "dice": float(dice),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1)
    }


# ============================================================
# 6. EVALUATE ALL CONFIDENCE THRESHOLDS
# ============================================================

all_records = []
summary_records = []

for confidence in CONFIDENCE_THRESHOLDS:

    print()
    print("=" * 70)
    print(f"TESTING VALIDATION CONFIDENCE: {confidence:.2f}")
    print("=" * 70)

    threshold_records = []

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for index, image_path in enumerate(
        image_files, start=1
    ):

        image = cv2.imread(str(image_path))

        if image is None:
            raise RuntimeError(
                f"Cannot read image: {image_path}"
            )

        height, width = image.shape[:2]

        gt_mask = load_ground_truth_mask(
            image_path,
            height,
            width
        )

        pred_mask = predict_plaque_mask(
            model,
            image_path,
            height,
            width,
            confidence
        )

        metrics = calculate_metrics(
            gt_mask,
            pred_mask
        )

        total_tp += metrics["tp"]
        total_fp += metrics["fp"]
        total_fn += metrics["fn"]

        record = {
            "confidence": confidence,
            "image": image_path.name,
            **metrics
        }

        threshold_records.append(record)
        all_records.append(record)

        print(
            f"[{index}/{len(image_files)}] "
            f"{image_path.name} | "
            f"IoU: {metrics['iou']:.4f} | "
            f"Dice: {metrics['dice']:.4f} | "
            f"Precision: {metrics['precision']:.4f} | "
            f"Recall: {metrics['recall']:.4f}"
        )

    # --------------------------------------------------------
    # MACRO AVERAGES: Mean across validation images
    # --------------------------------------------------------

    mean_iou = float(np.mean(
        [r["iou"] for r in threshold_records]
    ))

    mean_dice = float(np.mean(
        [r["dice"] for r in threshold_records]
    ))

    mean_precision = float(np.mean(
        [r["precision"] for r in threshold_records]
    ))

    mean_recall = float(np.mean(
        [r["recall"] for r in threshold_records]
    ))

    mean_f1 = float(np.mean(
        [r["f1"] for r in threshold_records]
    ))

    # --------------------------------------------------------
    # MICRO AVERAGES: Combine pixels from all images
    # --------------------------------------------------------

    micro_iou_den = total_tp + total_fp + total_fn

    micro_iou = (
        total_tp / micro_iou_den
        if micro_iou_den > 0
        else 1.0
    )

    micro_dice_den = (
        2 * total_tp + total_fp + total_fn
    )

    micro_dice = (
        2 * total_tp / micro_dice_den
        if micro_dice_den > 0
        else 1.0
    )

    micro_precision = (
        total_tp / (total_tp + total_fp)
        if total_tp + total_fp > 0
        else 0.0
    )

    micro_recall = (
        total_tp / (total_tp + total_fn)
        if total_tp + total_fn > 0
        else 0.0
    )

    summary = {
        "confidence": confidence,
        "images_evaluated": len(threshold_records),
        "macro_iou": mean_iou,
        "macro_dice": mean_dice,
        "macro_precision": mean_precision,
        "macro_recall": mean_recall,
        "macro_f1": mean_f1,
        "micro_iou": micro_iou,
        "micro_dice": micro_dice,
        "micro_precision": micro_precision,
        "micro_recall": micro_recall,
        "micro_f1": micro_dice,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn
    }

    summary_records.append(summary)

    print()
    print(f"RESULTS FOR CONFIDENCE {confidence:.2f}")
    print(f"Macro IoU       : {mean_iou:.4f}")
    print(f"Macro Dice      : {mean_dice:.4f}")
    print(f"Macro Precision : {mean_precision:.4f}")
    print(f"Macro Recall    : {mean_recall:.4f}")
    print(f"Macro F1        : {mean_f1:.4f}")
    print(f"Micro IoU       : {micro_iou:.4f}")
    print(f"Micro Dice      : {micro_dice:.4f}")
    print(f"Micro Precision : {micro_precision:.4f}")
    print(f"Micro Recall    : {micro_recall:.4f}")


# ============================================================
# 7. SAVE PER-IMAGE RESULTS
# ============================================================

with DETAIL_CSV.open(
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "confidence",
            "image",
            "tp",
            "fp",
            "fn",
            "iou",
            "dice",
            "precision",
            "recall",
            "f1"
        ]
    )

    writer.writeheader()
    writer.writerows(all_records)


# ============================================================
# 8. SAVE SUMMARY COMPARISON
# ============================================================

with SUMMARY_CSV.open(
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=list(summary_records[0].keys())
    )

    writer.writeheader()
    writer.writerows(summary_records)


# ============================================================
# 9. SELECT BEST VALIDATION CONFIDENCE
# ============================================================

# Predefined selection criterion:
# Highest macro Dice, with lower confidence breaking ties.
best_result = sorted(
    summary_records,
    key=lambda r: (
        -r["macro_dice"],
        r["confidence"]
    )
)[0]

print()
print("=" * 70)
print("FINAL VALIDATION CONFIDENCE COMPARISON")
print("=" * 70)

print(
    f"{'Confidence':<12}"
    f"{'Macro IoU':<12}"
    f"{'Macro Dice':<13}"
    f"{'Macro Prec':<13}"
    f"{'Macro Recall':<13}"
)

for result in summary_records:

    print(
        f"{result['confidence']:<12.2f}"
        f"{result['macro_iou']:<12.4f}"
        f"{result['macro_dice']:<13.4f}"
        f"{result['macro_precision']:<13.4f}"
        f"{result['macro_recall']:<13.4f}"
    )

print()
print(
    "BEST VALIDATION CONFIDENCE: "
    f"{best_result['confidence']:.2f}"
)

print(
    "BEST VALIDATION MACRO DICE: "
    f"{best_result['macro_dice']:.4f}"
)

print()
print("RESULT FILES")
print(f"Per-image CSV: {DETAIL_CSV}")
print(f"Summary CSV  : {SUMMARY_CSV}")

print()
print(
    "NOTE: Threshold selected using validation data only."
)
print(
    "Do not use test results to choose the threshold."
)

print("=" * 70)
