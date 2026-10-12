
import csv
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
import tensorflow as tf

# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = ROOT / "data" / "raw" / "crooked_detection"
DUPLICATE_GROUPS_FILE = (
    ROOT / "data" / "processed" / "duplicate_groups.json"
)

OUTPUT_DIR = ROOT / "models" / "crooked_baseline"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LABELS = [
    "crossbite",
    "normal",
    "openbite",
    "overbite",
    "underbite",
]

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 12
SEED = 42

tf.keras.utils.set_random_seed(SEED)
random.seed(SEED)
np.random.seed(SEED)

print("=" * 55)
print("MALOCCLUSION DETECTION - MobileNetV2 BASELINE")
print("=" * 55)
print("TensorFlow:", tf.__version__)
print("Dataset:", DATASET_DIR)
print("Labels:", LABELS)


# ==========================================
# 2. EXCLUDE CROSS-SPLIT DUPLICATES
# ==========================================

def normalized_path(path):
    return str(Path(path).resolve()).lower()


def load_excluded_images():
    if not DUPLICATE_GROUPS_FILE.exists():
        raise FileNotFoundError(
            "Duplicate groups report missing: "
            + str(DUPLICATE_GROUPS_FILE)
        )

    with open(
        DUPLICATE_GROUPS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        report = json.load(file)

    excluded = set()

    # Conservatively exclude confirmed duplicate
    # groups that span different dataset splits.
    for group in report.get("duplicate_groups", []):
        members = [Path(p) for p in group]

        splits = {
            p.parent.name.lower()
            for p in members
            if p.parent.name.lower() in
            {"train", "valid", "test"}
        }

        if len(splits) > 1:
            for path in members:
                excluded.add(normalized_path(ROOT / path))

    # Keep uncertain images out of this baseline
    # until their identity/relationship is resolved.
    for pair in report.get("uncertain_pairs", []):
        for key in ("image_a", "image_b"):
            if pair.get(key):
                excluded.add(
                    normalized_path(ROOT / pair[key])
                )

    return excluded


excluded_images = load_excluded_images()

print(
    "Images in exclusion reference:",
    len(excluded_images)
)


# ==========================================
# 3. READ ORIGINAL CLASSIFICATION LABELS
# ==========================================

def load_split(split):
    folder = DATASET_DIR / split
    csv_path = folder / "_classes.csv"

    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    paths = []
    targets = []

    stats = Counter()

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        missing_columns = [
            label for label in LABELS
            if label not in (reader.fieldnames or [])
        ]

        if missing_columns:
            raise ValueError(
                f"Missing CSV labels: {missing_columns}"
            )

        for row in reader:
            path = folder / row["filename"]

            if not path.is_file():
                stats["missing_file"] += 1
                continue

            if normalized_path(path) in excluded_images:
                stats["excluded_duplicate"] += 1
                continue

            if row.get("Unlabeled", "0").strip() == "1":
                stats["unlabeled"] += 1
                continue

            values = []

            for label in LABELS:
                value = row[label].strip()

                if value not in ("0", "1"):
                    raise ValueError(
                        f"Invalid label {label}={value} "
                        f"in {path.name}"
                    )

                values.append(float(value))

            if not any(values):
                stats["no_target_label"] += 1
                continue

            paths.append(str(path))
            targets.append(values)

    if not paths:
        raise RuntimeError(
            f"No usable images in split: {split}"
        )

    return (
        paths,
        np.asarray(targets, dtype=np.float32),
        stats
    )


train_paths, train_labels, train_stats = load_split("train")
valid_paths, valid_labels, valid_stats = load_split("valid")
test_paths, test_labels, test_stats = load_split("test")

print("\n===== DATASET SUMMARY =====")

for split, paths, labels, stats in [
    ("train", train_paths, train_labels, train_stats),
    ("valid", valid_paths, valid_labels, valid_stats),
    ("test", test_paths, test_labels, test_stats),
]:
    print(f"\n{split.upper()}: {len(paths)} images")
    print("Positive labels:")
    for name, count in zip(
        LABELS,
        labels.sum(axis=0).astype(int)
    ):
        print(f"  {name}: {count}")

    print("Skipped:", dict(stats))


# ==========================================
# 4. FINAL SPLIT SAFETY CHECK
# ==========================================

train_set = set(map(normalized_path, train_paths))
valid_set = set(map(normalized_path, valid_paths))
test_set = set(map(normalized_path, test_paths))

assert not (train_set & valid_set)
assert not (train_set & test_set)
assert not (valid_set & test_set)

print("\nNo identical file paths across splits.")


# ==========================================
# 5. TENSORFLOW DATA PIPELINE
# ==========================================

def decode_image(path, labels):
    image_bytes = tf.io.read_file(path)

    image = tf.io.decode_image(
        image_bytes,
        channels=3,
        expand_animations=False
    )

    image.set_shape((None, None, 3))

    image = tf.image.resize(
        image,
        IMAGE_SIZE,
        method="bilinear"
    )

    image = tf.cast(image, tf.float32)

    return image, labels


def create_dataset(paths, targets, training=False):
    dataset = tf.data.Dataset.from_tensor_slices(
        (paths, targets)
    )

    if training:
        dataset = dataset.shuffle(
            buffer_size=len(paths),
            seed=SEED,
            reshuffle_each_iteration=True
        )

    dataset = dataset.map(
        decode_image,
        num_parallel_calls=tf.data.AUTOTUNE
    )

    dataset = dataset.batch(BATCH_SIZE)

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset


train_ds = create_dataset(
    train_paths, train_labels, training=True
)

valid_ds = create_dataset(
    valid_paths, valid_labels
)

test_ds = create_dataset(
    test_paths, test_labels
)


# ==========================================
# 6. BUILD MobileNetV2 MODEL
# ==========================================

print("\nLoading MobileNetV2 pretrained weights...")

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False

inputs = tf.keras.Input(
    shape=(224, 224, 3),
    name="dental_image"
)

# MobileNetV2 expects pixels in [-1, 1].
# Input images arrive in [0, 255].
x = tf.keras.layers.Rescaling(
    scale=1.0 / 127.5,
    offset=-1.0
)(inputs)

x = base_model(x, training=False)

x = tf.keras.layers.GlobalAveragePooling2D()(x)

x = tf.keras.layers.Dropout(0.3)(x)

outputs = tf.keras.layers.Dense(
    len(LABELS),
    activation="sigmoid",
    name="dental_conditions"
)(x)

model = tf.keras.Model(
    inputs=inputs,
    outputs=outputs,
    name="Malocclusion_MobileNetV2_Baseline"
)

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.0001
    ),
    loss="binary_crossentropy",
    metrics=[
        tf.keras.metrics.BinaryAccuracy(
            name="binary_accuracy"
        ),
        tf.keras.metrics.AUC(
            name="auc",
            multi_label=True,
            num_labels=len(LABELS)
        )
    ]
)

model.summary()


# ==========================================
# 7. TRAINING
# ==========================================

print("\n===== STARTING TRAINING =====")

checkpoint_path = OUTPUT_DIR / "best_model.keras"

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        str(checkpoint_path),
        monitor="val_loss",
        save_best_only=True,
        mode="min",
        verbose=1
    ),

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=4,
        restore_best_weights=True
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=1e-6
    )
]

history = model.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)


# ==========================================
# 8. EVALUATE TEST DATASET
# ==========================================

print("\n===== TEST EVALUATION =====")

best_model = tf.keras.models.load_model(
    str(checkpoint_path)
)

test_results = best_model.evaluate(
    test_ds,
    return_dict=True,
    verbose=1
)

probabilities = best_model.predict(
    test_ds,
    verbose=0
)

predictions = (
    probabilities >= 0.5
).astype(np.int32)

actual = test_labels.astype(np.int32)


def calculate_metrics(y_true, y_pred):
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


per_class = {}

for index, label in enumerate(LABELS):
    metrics = calculate_metrics(
        actual[:, index],
        predictions[:, index]
    )

    metrics["test_positive_count"] = int(
        actual[:, index].sum()
    )

    per_class[label] = metrics

    print(
        f"{label}: "
        f"Precision={metrics['precision']:.4f}, "
        f"Recall={metrics['recall']:.4f}, "
        f"F1={metrics['f1']:.4f}"
    )


# ==========================================
# 9. SAVE RESULTS
# ==========================================

metrics_output = {
    "model": "MobileNetV2",
    "experiment": "crooked_detection_baseline",
    "epochs_completed": len(history.history["loss"]),
    "threshold": 0.5,
    "test_evaluation": {
        key: float(value)
        for key, value in test_results.items()
    },
    "per_class_metrics": per_class,
    "split_sizes": {
        "train": len(train_paths),
        "valid": len(valid_paths),
        "test": len(test_paths)
    },
    "limitations": [
        "Original public dataset labels are not clinically verified.",
        "Missing conditions outside this dataset are not assessed.",
        "Potential same-patient leakage may remain.",
        "Small test split limits reliability.",
        "Threshold 0.5 is a baseline choice."
    ]
}

with open(
    OUTPUT_DIR / "metrics.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(metrics_output, file, indent=2)

with open(
    OUTPUT_DIR / "labels.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(LABELS, file, indent=2)

with open(
    OUTPUT_DIR / "excluded_leakage.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        sorted(excluded_images),
        file,
        indent=2
    )

with open(
    OUTPUT_DIR / "training_history.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        {
            key: [float(v) for v in values]
            for key, values in history.history.items()
        },
        file,
        indent=2
    )

print("\n====================================")
print("BASELINE TRAINING COMPLETED")
print("Model saved:", checkpoint_path)
print("Metrics saved:", OUTPUT_DIR / "metrics.json")
print("====================================")
