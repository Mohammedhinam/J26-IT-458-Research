
from pathlib import Path
import csv

import cv2
import numpy as np
from ultralytics import YOLO

# -------------------------------------------------
# 1. PATH CONFIGURATION
# -------------------------------------------------
BASE = Path(
    r"C:\Users\MSI\Documents\Research\DentalImages\archive\datasets"
)

MODEL_PATH = (
    BASE / "runs" / "segment"
    / "plaque_yolov8n_baseline" / "weights" / "best.pt"
)

DATASET = BASE / "Plaque_Segmentation" / "Plaque_YOLO_Clean"

TEST_IMAGES = DATASET / "test" / "images"
TEST_LABELS = DATASET / "test" / "labels"

OUTPUT_DIR = BASE / "Plaque_Evaluation_Results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DETAIL_CSV = OUTPUT_DIR / "plaque_test_per_image_metrics.csv"
SUMMARY_CSV = OUTPUT_DIR / "plaque_test_summary_metrics.csv"

CONFIDENCE = 0.25
IMAGE_SIZE = 640
DEVICE = 0

# -------------------------------------------------
# 2. VALIDATE INPUT PATHS
# -------------------------------------------------
if not MODEL_PATH.is_file():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not TEST_IMAGES.is_dir():
    raise FileNotFoundError(f"Test images not found: {TEST_IMAGES}")

if not TEST_LABELS.is_dir():
    raise FileNotFoundError(f"Test labels not found: {TEST_LABELS}")

print("=" * 65)
print("PLAQUE SEGMENTATION - INDEPENDENT TEST EVALUATION")
print("=" * 65)

model = YOLO(str(MODEL_PATH))

valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

image_files = sorted(
    p for p in TEST_IMAGES.iterdir()
    if p.is_file() and p.suffix.lower() in valid_extensions
)

print(f"Model: {MODEL_PATH}")
print(f"Test images found: {len(image_files)}")
print(f"Confidence threshold: {CONFIDENCE}")
print(f"Image size: {IMAGE_SIZE}")
print()

if not image_files:
    raise RuntimeError("No test images found.")

# -------------------------------------------------
# 3. METRIC STORAGE
# -------------------------------------------------
records = []

total_tp = 0
total_fp = 0
total_fn = 0

# -------------------------------------------------
# 4. PROCESS EACH TEST IMAGE
# -------------------------------------------------
for image_path in image_files:

    image = cv2.imread(str(image_path))

    if image is None:
        raise RuntimeError(f"Cannot read image: {image_path}")

    height, width = image.shape[:2]

    # ---------------------------------------------
    # 4A. CREATE GROUND-TRUTH BINARY MASK
    # ---------------------------------------------
    gt_mask = np.zeros((height, width), dtype=np.uint8)

    label_path = TEST_LABELS / f"{image_path.stem}.txt"

    if not label_path.is_file():
        raise FileNotFoundError(
            f"Ground-truth label missing: {label_path}"
        )

    with label_path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):

            values = line.strip().split()

            if not values:
                continue

            if len(values) < 7 or (len(values) - 1) % 2 != 0:
                raise ValueError(
                    f"Invalid polygon in {label_path.name}, "
                    f"line {line_number}"
                )

            class_id = int(values[0])

            if class_id != 0:
                raise ValueError(
                    f"Unexpected class {class_id} in "
                    f"{label_path.name}"
                )

            coords = np.array(
                [float(value) for value in values[1:]],
                dtype=np.float32
            ).reshape(-1, 2)

            if not np.isfinite(coords).all():
                raise ValueError(
                    f"Non-finite coordinates in {label_path.name}"
                )

            coords[:, 0] *= width
            coords[:, 1] *= height

            polygon = np.round(coords).astype(np.int32)

            cv2.fillPoly(gt_mask, [polygon], 1)

    # ---------------------------------------------
    # 4B. GENERATE PREDICTED PLAQUE MASK
    # ---------------------------------------------
    results = model.predict(
        source=str(image_path),
        imgsz=IMAGE_SIZE,
        conf=CONFIDENCE,
        device=DEVICE,
        verbose=False
    )

    pred_mask = np.zeros((height, width), dtype=np.uint8)

    result = results[0]

    if result.masks is not None:
        for polygon in result.masks.xy:

            if len(polygon) >= 3:
                polygon = np.round(polygon).astype(np.int32)
                cv2.fillPoly(pred_mask, [polygon], 1)

    # ---------------------------------------------
    # 4C. PIXEL-LEVEL CONFUSION COUNTS
    # ---------------------------------------------
    gt_positive = gt_mask.astype(bool)
    pred_positive = pred_mask.astype(bool)

    tp = int(np.logical_and(gt_positive, pred_positive).sum())
    fp = int(np.logical_and(~gt_positive, pred_positive).sum())
    fn = int(np.logical_and(gt_positive, ~pred_positive).sum())

    total_tp += tp
    total_fp += fp
    total_fn += fn

    # ---------------------------------------------
    # 4D. CALCULATE METRICS
    # ---------------------------------------------
    union = tp + fp + fn

    iou = tp / union if union > 0 else 1.0

    dice_denominator = 2 * tp + fp + fn
    dice = (
        (2 * tp) / dice_denominator
        if dice_denominator > 0
        else 1.0
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    # Pixel-level F1 equals Dice when foreground
    # pixels are evaluated as a binary class.
    f1 = dice

    # ---------------------------------------------
    # 4E. STORE PER-IMAGE RESULTS
    # ---------------------------------------------
    records.append({
        "image": image_path.name,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "iou": float(iou),
        "dice": float(dice),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1)
    })

    print(
        f"{image_path.name} | "
        f"IoU: {iou:.4f} | "
        f"Dice: {dice:.4f} | "
        f"Precision: {precision:.4f} | "
        f"Recall: {recall:.4f} | "
        f"F1: {f1:.4f}"
    )

# -------------------------------------------------
# 5. CALCULATE MACRO-AVERAGE METRICS
# -------------------------------------------------
mean_iou = float(np.mean([r["iou"] for r in records]))
mean_dice = float(np.mean([r["dice"] for r in records]))
mean_precision = float(np.mean([r["precision"] for r in records]))
mean_recall = float(np.mean([r["recall"] for r in records]))
mean_f1 = float(np.mean([r["f1"] for r in records]))

# -------------------------------------------------
# 6. CALCULATE MICRO-AVERAGE METRICS
# -------------------------------------------------
micro_iou_den = total_tp + total_fp + total_fn

micro_iou = (
    total_tp / micro_iou_den
    if micro_iou_den > 0
    else 1.0
)

micro_dice_den = 2 * total_tp + total_fp + total_fn

micro_dice = (
    (2 * total_tp) / micro_dice_den
    if micro_dice_den > 0
    else 1.0
)

micro_precision = (
    total_tp / (total_tp + total_fp)
    if (total_tp + total_fp) > 0
    else 0.0
)

micro_recall = (
    total_tp / (total_tp + total_fn)
    if (total_tp + total_fn) > 0
    else 0.0
)

micro_f1 = micro_dice

# -------------------------------------------------
# 7. SAVE PER-IMAGE METRICS TO CSV
# -------------------------------------------------
with DETAIL_CSV.open(
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "image", "tp", "fp", "fn",
            "iou", "dice", "precision",
            "recall", "f1"
        ]
    )

    writer.writeheader()
    writer.writerows(records)

# -------------------------------------------------
# 8. SAVE SUMMARY METRICS TO CSV
# -------------------------------------------------
summary = [
    ("images_evaluated", len(records)),
    ("confidence_threshold", CONFIDENCE),
    ("image_size", IMAGE_SIZE),
    ("macro_mean_iou", mean_iou),
    ("macro_mean_dice", mean_dice),
    ("macro_mean_precision", mean_precision),
    ("macro_mean_recall", mean_recall),
    ("macro_mean_f1", mean_f1),
    ("micro_iou", micro_iou),
    ("micro_dice", micro_dice),
    ("micro_precision", micro_precision),
    ("micro_recall", micro_recall),
    ("micro_f1", micro_f1),
    ("total_tp", total_tp),
    ("total_fp", total_fp),
    ("total_fn", total_fn)
]

with SUMMARY_CSV.open(
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.writer(file)
    writer.writerow(["metric", "value"])
    writer.writerows(summary)

# -------------------------------------------------
# 9. DISPLAY FINAL RESULTS
# -------------------------------------------------
print()
print("=" * 65)
print("FINAL INDEPENDENT TEST RESULTS")
print("=" * 65)

print(f"Images evaluated     : {len(records)}")
print()
print("MACRO AVERAGE (MEAN ACROSS IMAGES)")
print(f"Mean IoU             : {mean_iou:.4f}")
print(f"Mean Dice            : {mean_dice:.4f}")
print(f"Mean Pixel Precision : {mean_precision:.4f}")
print(f"Mean Pixel Recall    : {mean_recall:.4f}")
print(f"Mean Pixel F1        : {mean_f1:.4f}")

print()
print("MICRO AVERAGE (ALL TEST PIXELS)")
print(f"Micro IoU            : {micro_iou:.4f}")
print(f"Micro Dice           : {micro_dice:.4f}")
print(f"Micro Pixel Precision: {micro_precision:.4f}")
print(f"Micro Pixel Recall   : {micro_recall:.4f}")
print(f"Micro Pixel F1       : {micro_f1:.4f}")

print()
print("RESULT FILES")
print(f"Per-image CSV: {DETAIL_CSV}")
print(f"Summary CSV  : {SUMMARY_CSV}")
print("=" * 65)
