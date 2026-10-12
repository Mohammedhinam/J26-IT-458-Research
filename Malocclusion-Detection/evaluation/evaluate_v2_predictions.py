
import csv
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data/raw/crooked_detection"
V1_DIR = ROOT / "models/crooked_baseline"
V2_DIR = ROOT / "models/crooked_baseline_v2"
OUTPUT_DIR = ROOT / "evaluation/reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LABELS = json.loads(
    (V2_DIR / "labels.json").read_text(encoding="utf-8")
)

excluded = set(json.loads(
    (V1_DIR / "excluded_leakage.json").read_text(
        encoding="utf-8"
    )
))

THRESHOLD = 0.5


def normalize_path(path):
    return str(Path(path).resolve()).lower()


def load_test_data():
    folder = DATA_DIR / "test"
    paths = []
    targets = []

    with (folder / "_classes.csv").open(
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            path = folder / row["filename"]

            if not path.is_file():
                continue

            if normalize_path(path) in excluded:
                continue

            if row.get("Unlabeled", "0").strip() == "1":
                continue

            target = [int(row[label]) for label in LABELS]

            if not any(target):
                continue

            paths.append(path)
            targets.append(target)

    return paths, np.array(targets, dtype=np.int32)


def prepare_images(paths):
    images = []

    for path in paths:
        image = tf.keras.utils.load_img(
            path, target_size=(224, 224)
        )

        array = tf.keras.utils.img_to_array(image)
        images.append(array)

    return np.array(images, dtype=np.float32)


def calculate_metrics(actual, predicted):
    tp = int(np.sum((actual == 1) & (predicted == 1)))
    fp = int(np.sum((actual == 0) & (predicted == 1)))
    fn = int(np.sum((actual == 1) & (predicted == 0)))
    tn = int(np.sum((actual == 0) & (predicted == 0)))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


print("Loading MobileNetV2 V2 model...")

model = tf.keras.models.load_model(
    V2_DIR / "best_model.keras",
    compile=False
)

paths, actual = load_test_data()

if len(paths) == 0:
    raise RuntimeError("No usable test images found.")

# Ensure evaluation uses the same held-out test size as V2.
training_report = json.loads(
    (V2_DIR / "metrics.json").read_text(encoding="utf-8")
)

expected_test_size = training_report["split_sizes"]["test"]

if len(paths) != expected_test_size:
    raise RuntimeError(
        f"Test set mismatch: expected {expected_test_size}, "
        f"got {len(paths)}"
    )

images = prepare_images(paths)
probabilities = model.predict(images, verbose=0)
predicted = (probabilities >= THRESHOLD).astype(np.int32)

report_rows = []

for i, path in enumerate(paths):
    true_labels = [
        LABELS[j] for j in range(len(LABELS))
        if actual[i, j] == 1
    ]

    predicted_labels = [
        LABELS[j] for j in range(len(LABELS))
        if predicted[i, j] == 1
    ]

    row = {
        "filename": path.name,
        "actual_labels": "; ".join(true_labels),
        "predicted_labels": "; ".join(predicted_labels),
        "exact_label_match": int(
            np.array_equal(actual[i], predicted[i])
        )
    }

    for j, label in enumerate(LABELS):
        row[f"{label}_actual"] = int(actual[i, j])
        row[f"{label}_predicted"] = int(predicted[i, j])
        row[f"{label}_probability"] = round(
            float(probabilities[i, j]), 4
        )

    report_rows.append(row)

csv_path = OUTPUT_DIR / "v2_predictions.csv"

with csv_path.open(
    "w",
    newline="",
    encoding="utf-8"
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=report_rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(report_rows)


print("\n===== V2 PREDICTION EVALUATION =====")
print("Test images:", len(paths))
print("Threshold:", THRESHOLD)

exact_match_accuracy = float(
    np.mean(np.all(actual == predicted, axis=1))
)

print(
    "Exact match accuracy:",
    round(exact_match_accuracy, 4)
)

metrics = {}

for j, label in enumerate(LABELS):
    result = calculate_metrics(
        actual[:, j],
        predicted[:, j]
    )

    metrics[label] = result

    print(
        f"{label}: "
        f"TP={result['tp']}, "
        f"FP={result['fp']}, "
        f"FN={result['fn']}, "
        f"TN={result['tn']}, "
        f"F1={result['f1']:.4f}"
    )

summary = {
    "model": "MobileNetV2 V2",
    "test_images": len(paths),
    "threshold": THRESHOLD,
    "exact_match_accuracy": exact_match_accuracy,
    "per_class_metrics": metrics,
    "limitations": [
        "Small held-out test dataset.",
        "Source labels are not clinically validated.",
        "Patient-level leakage may remain.",
        "Not a clinical diagnostic evaluation."
    ]
}

json_path = OUTPUT_DIR / "v2_evaluation.json"

json_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("\nEvaluation completed.")
print("CSV report:", csv_path)
print("JSON report:", json_path)
