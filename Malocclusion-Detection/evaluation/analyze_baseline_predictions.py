
import csv
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/raw/crooked_detection"
MODEL_DIR = ROOT / "models/crooked_baseline"
REPORT_DIR = ROOT / "evaluation/reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

LABELS = json.loads(
    (MODEL_DIR / "labels.json").read_text(encoding="utf-8")
)

model = tf.keras.models.load_model(
    MODEL_DIR / "best_model.keras"
)

excluded = set(json.loads(
    (MODEL_DIR / "excluded_leakage.json").read_text(
        encoding="utf-8"
    )
))

def normalized_path(path):
    return str(Path(path).resolve()).lower()

def load_split(split):
    folder = DATASET / split
    paths = []
    targets = []

    with (folder / "_classes.csv").open(
        encoding="utf-8-sig",
        newline=""
    ) as f:
        for row in csv.DictReader(f):
            path = folder / row["filename"]

            if not path.is_file():
                continue

            if normalized_path(path) in excluded:
                continue

            if row.get("Unlabeled", "0").strip() == "1":
                continue

            target = [int(row[label]) for label in LABELS]

            if not any(target):
                continue

            paths.append(path)
            targets.append(target)

    return paths, np.array(targets, dtype=np.int32)

def predict_images(paths):
    images = []

    for path in paths:
        image = tf.keras.utils.load_img(
            path,
            target_size=(224, 224)
        )

        array = tf.keras.utils.img_to_array(image)
        images.append(array)

    return model.predict(
        np.array(images, dtype=np.float32),
        verbose=0
    )

def calculate_f1(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    denominator = 2 * tp + fp + fn

    return float(2 * tp / denominator) if denominator else 0.0

valid_paths, valid_true = load_split("valid")
valid_probs = predict_images(valid_paths)

thresholds = {}

print("\n===== VALIDATION THRESHOLD ANALYSIS =====")

for i, label in enumerate(LABELS):
    best_threshold = 0.5
    best_f1 = -1.0

    for threshold in np.arange(0.10, 0.91, 0.05):
        prediction = (
            valid_probs[:, i] >= threshold
        ).astype(int)

        f1 = calculate_f1(valid_true[:, i], prediction)

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = float(round(threshold, 2))

    thresholds[label] = best_threshold

    print(
        f"{label}: threshold={best_threshold:.2f}, "
        f"validation F1={best_f1:.4f}"
    )

with (REPORT_DIR / "baseline_v1_thresholds.json").open(
    "w",
    encoding="utf-8"
) as f:
    json.dump(thresholds, f, indent=2)

print("\n===== HELD-OUT TEST EVALUATION =====")

test_paths, test_true = load_split("test")
test_probs = predict_images(test_paths)

results = {}

for i, label in enumerate(LABELS):
    threshold = thresholds[label]

    predictions = (
        test_probs[:, i] >= threshold
    ).astype(int)

    f1 = calculate_f1(test_true[:, i], predictions)

    results[label] = {
        "threshold": threshold,
        "test_f1": f1,
        "positive_predictions": int(predictions.sum()),
        "actual_positives": int(test_true[:, i].sum())
    }

    print(
        f"{label}: F1={f1:.4f}, "
        f"predicted positives={int(predictions.sum())}, "
        f"actual positives={int(test_true[:, i].sum())}"
    )

with (REPORT_DIR / "baseline_v1_threshold_analysis.json").open(
    "w",
    encoding="utf-8"
) as f:
    json.dump(results, f, indent=2)

print("\nAnalysis complete.")
print("Original model unchanged.")
