import csv
import json
from pathlib import Path

import numpy as np
import tensorflow as tf


ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT
    / "data"
    / "processed"
    / "crowding_stratified"
    / "crowding_split_manifest.csv"
)

MODEL_PATH = (
    ROOT
    / "models"
    / "crowding_binary_stratified"
    / "best_model.keras"
)

OUT_DIR = (
    ROOT
    / "evaluation"
    / "reports"
)
OUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_JSON = (
    OUT_DIR
    / "crowding_threshold_evaluation.json"
)

OUTPUT_CSV = (
    OUT_DIR
    / "crowding_threshold_predictions.csv"
)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 8


def load_split(split_name):
    paths = []
    labels = []

    with MANIFEST.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["split"] != split_name:
                continue

            image_path = Path(
                row["image"]
            )

            label_name = (
                row["label"]
                .strip()
                .lower()
            )

            if label_name == "crowding":
                label = 1

            elif label_name == "normal":
                label = 0

            else:
                raise ValueError(
                    f"Unexpected label: {label_name}"
                )

            paths.append(
                str(image_path)
            )
            labels.append(label)

    return (
        paths,
        np.asarray(
            labels,
            dtype=np.int32
        )
    )


def read_image(path, label):
    data = tf.io.read_file(path)

    image = tf.io.decode_image(
        data,
        channels=3,
        expand_animations=False
    )

    image.set_shape(
        (None, None, 3)
    )

    image = tf.image.resize(
        image,
        IMAGE_SIZE
    )

    image = tf.cast(
        image,
        tf.float32
    )

    return image, label


def make_dataset(
    paths,
    labels
):
    dataset = (
        tf.data.Dataset
        .from_tensor_slices(
            (paths, labels)
        )
    )

    dataset = dataset.map(
        read_image,
        num_parallel_calls=tf.data.AUTOTUNE
    )

    dataset = dataset.batch(
        BATCH_SIZE
    )

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset


def calculate_metrics(
    actual,
    probabilities,
    threshold
):
    predicted = (
        probabilities >= threshold
    ).astype(int)

    tp = int(np.sum(
        (actual == 1)
        & (predicted == 1)
    ))

    fp = int(np.sum(
        (actual == 0)
        & (predicted == 1)
    ))

    fn = int(np.sum(
        (actual == 1)
        & (predicted == 0)
    ))

    tn = int(np.sum(
        (actual == 0)
        & (predicted == 0)
    ))

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    accuracy = (
        (tp + tn)
        / len(actual)
        if len(actual)
        else 0.0
    )

    return {
        "threshold": float(
            threshold
        ),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


valid_paths, valid_y = load_split(
    "valid"
)

test_paths, test_y = load_split(
    "test"
)

print("=" * 60)
print(
    "CROWDING THRESHOLD EVALUATION"
)
print("=" * 60)

print("\nValidation")
print(
    "Images:",
    len(valid_paths)
)
print(
    "Crowding:",
    int(valid_y.sum())
)
print(
    "Normal:",
    int(
        len(valid_y)
        - valid_y.sum()
    )
)

print("\nTest")
print(
    "Images:",
    len(test_paths)
)
print(
    "Crowding:",
    int(test_y.sum())
)
print(
    "Normal:",
    int(
        len(test_y)
        - test_y.sum()
    )
)


model = tf.keras.models.load_model(
    MODEL_PATH,
    compile=False
)

valid_ds = make_dataset(
    valid_paths,
    valid_y
)

test_ds = make_dataset(
    test_paths,
    test_y
)

valid_probabilities = (
    model.predict(
        valid_ds,
        verbose=0
    )
    .reshape(-1)
)

test_probabilities = (
    model.predict(
        test_ds,
        verbose=0
    )
    .reshape(-1)
)


print(
    "\n===== VALIDATION THRESHOLD SEARCH ====="
)

threshold_results = []

for threshold in np.arange(
    0.10,
    0.91,
    0.05
):
    result = calculate_metrics(
        valid_y,
        valid_probabilities,
        threshold
    )

    threshold_results.append(
        result
    )

    print(
        f"Threshold={threshold:.2f} "
        f"Precision={result['precision']:.4f} "
        f"Recall={result['recall']:.4f} "
        f"F1={result['f1']:.4f}"
    )


# Highest F1 first.
# If tied, prefer higher recall.
# If still tied, prefer higher threshold.
best_validation = max(
    threshold_results,
    key=lambda item: (
        item["f1"],
        item["recall"],
        item["threshold"]
    )
)

best_threshold = (
    best_validation[
        "threshold"
    ]
)


print(
    "\n===== SELECTED THRESHOLD ====="
)

print(
    "Threshold:",
    round(
        best_threshold,
        4
    )
)

print(
    "Validation Precision:",
    round(
        best_validation[
            "precision"
        ],
        4
    )
)

print(
    "Validation Recall:",
    round(
        best_validation[
            "recall"
        ],
        4
    )
)

print(
    "Validation F1:",
    round(
        best_validation[
            "f1"
        ],
        4
    )
)


test_result = calculate_metrics(
    test_y,
    test_probabilities,
    best_threshold
)


print(
    "\n===== HELD-OUT TEST RESULT ====="
)

print(
    "Threshold:",
    round(
        best_threshold,
        4
    )
)

print(
    "TP:",
    test_result["tp"]
)

print(
    "FP:",
    test_result["fp"]
)

print(
    "FN:",
    test_result["fn"]
)

print(
    "TN:",
    test_result["tn"]
)

print(
    "Precision:",
    round(
        test_result[
            "precision"
        ],
        4
    )
)

print(
    "Recall:",
    round(
        test_result[
            "recall"
        ],
        4
    )
)

print(
    "F1:",
    round(
        test_result[
            "f1"
        ],
        4
    )
)

print(
    "Accuracy:",
    round(
        test_result[
            "accuracy"
        ],
        4
    )
)


with OUTPUT_CSV.open(
    "w",
    encoding="utf-8",
    newline=""
) as file:
    fieldnames = [
        "filename",
        "actual_label",
        "probability",
        "threshold",
        "predicted_label",
        "correct",
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    predictions = (
        test_probabilities
        >= best_threshold
    ).astype(int)

    for path, actual, probability, predicted in zip(
        test_paths,
        test_y,
        test_probabilities,
        predictions
    ):
        writer.writerow({
            "filename":
                Path(path).name,

            "actual_label":
                (
                    "crowding"
                    if actual == 1
                    else "normal"
                ),

            "probability":
                float(
                    probability
                ),

            "threshold":
                float(
                    best_threshold
                ),

            "predicted_label":
                (
                    "crowding"
                    if predicted == 1
                    else "normal"
                ),

            "correct":
                int(
                    actual
                    == predicted
                ),
        })


report = {
    "experiment":
        "crowding_threshold_selection",

    "model":
        str(MODEL_PATH),

    "selection_method":
        (
            "Threshold selected only "
            "on validation-set F1."
        ),

    "threshold_search": (
        threshold_results
    ),

    "selected_threshold":
        best_threshold,

    "validation_result":
        best_validation,

    "held_out_test_result":
        test_result,

    "sample_counts": {
        "validation": {
            "total":
                len(valid_y),
            "crowding":
                int(valid_y.sum()),
            "normal":
                int(
                    len(valid_y)
                    - valid_y.sum()
                ),
        },

        "test": {
            "total":
                len(test_y),
            "crowding":
                int(test_y.sum()),
            "normal":
                int(
                    len(test_y)
                    - test_y.sum()
                ),
        },
    },

    "limitations": [
        (
            "Threshold selection uses "
            "only 11 validation images."
        ),
        (
            "Validation contains only "
            "3 Crowding-positive images."
        ),
        (
            "Test contains only "
            "5 Crowding-positive images."
        ),
        (
            "The threshold was not "
            "selected using the test set."
        ),
        (
            "Results are preliminary "
            "and not clinically validated."
        ),
    ],
}


OUTPUT_JSON.write_text(
    json.dumps(
        report,
        indent=2
    ),
    encoding="utf-8"
)


print(
    "\n===== SAVED ====="
)

print(
    "JSON:",
    OUTPUT_JSON
)

print(
    "CSV:",
    OUTPUT_CSV
)