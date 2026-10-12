
import csv
import json
import random
from pathlib import Path

import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/raw/crooked_detection"
V1_DIR = ROOT / "models/crooked_baseline"
OUT_DIR = ROOT / "models/crooked_baseline_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LABELS = json.loads(
    (V1_DIR / "labels.json").read_text(encoding="utf-8")
)

excluded = set(json.loads(
    (V1_DIR / "excluded_leakage.json").read_text(
        encoding="utf-8"
    )
))

SEED = 42
BATCH_SIZE = 16
EPOCHS = 15

random.seed(SEED)
np.random.seed(SEED)
tf.keras.utils.set_random_seed(SEED)


def normalize_path(path):
    return str(Path(path).resolve()).lower()


def load_split(split):
    folder = DATA_DIR / split
    paths, targets = [], []

    with (folder / "_classes.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        for row in csv.DictReader(file):
            path = folder / row["filename"]

            if not path.is_file():
                continue

            if normalize_path(path) in excluded:
                continue

            if row.get("Unlabeled", "0").strip() == "1":
                continue

            values = [float(row[label]) for label in LABELS]

            if not any(values):
                continue

            paths.append(str(path))
            targets.append(values)

    return paths, np.asarray(targets, dtype=np.float32)


train_paths, train_y = load_split("train")
valid_paths, valid_y = load_split("valid")
test_paths, test_y = load_split("test")

print("===== BASELINE V2 =====")
print("TensorFlow:", tf.__version__)
print("Train:", len(train_paths))
print("Valid:", len(valid_paths))
print("Test:", len(test_paths))

# Ensure the original V1 baseline splits are preserved.
v1_metrics = json.loads(
    (V1_DIR / "metrics.json").read_text(encoding="utf-8")
)

expected = v1_metrics["split_sizes"]
actual = {
    "train": len(train_paths),
    "valid": len(valid_paths),
    "test": len(test_paths),
}

if actual != expected:
    raise RuntimeError(
        f"Dataset split changed! Expected {expected}, got {actual}"
    )


def read_image(path, label):
    data = tf.io.read_file(path)
    image = tf.io.decode_image(
        data, channels=3, expand_animations=False
    )
    image.set_shape((None, None, 3))
    image = tf.image.resize(image, (224, 224))
    return tf.cast(image, tf.float32), label


def make_dataset(paths, labels, training=False):
    dataset = tf.data.Dataset.from_tensor_slices(
        (paths, labels)
    )

    if training:
        dataset = dataset.shuffle(
            len(paths),
            seed=SEED,
            reshuffle_each_iteration=True
        )

    dataset = dataset.map(
        read_image,
        num_parallel_calls=tf.data.AUTOTUNE
    )

    return dataset.batch(BATCH_SIZE).prefetch(
        tf.data.AUTOTUNE
    )


train_ds = make_dataset(train_paths, train_y, True)
valid_ds = make_dataset(valid_paths, valid_y)
test_ds = make_dataset(test_paths, test_y)

# Use the already trained V1 checkpoint as the starting point.
model = tf.keras.models.load_model(
    V1_DIR / "best_model.keras"
)

# Find the embedded MobileNetV2 model.
base = next(
    layer for layer in model.layers
    if isinstance(layer, tf.keras.Model)
    and "mobilenetv2" in layer.name.lower()
)

# Unfreeze only the final layers.
base.trainable = True

for layer in base.layers[:-30]:
    layer.trainable = False

# Keep BatchNormalization statistics stable for a small dataset.
for layer in base.layers:
    if isinstance(layer, tf.keras.layers.BatchNormalization):
        layer.trainable = False

print("Trainable MobileNetV2 layers:",
      sum(int(layer.trainable) for layer in base.layers))

# Add moderate augmentation before the existing model.
inputs = tf.keras.Input(shape=(224, 224, 3))

augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomRotation(0.04),
    tf.keras.layers.RandomZoom(0.08),
    tf.keras.layers.RandomContrast(0.08),
], name="training_augmentation")

x = augmentation(inputs)
outputs = model(x)

fine_tuned = tf.keras.Model(
    inputs, outputs,
    name="Malocclusion_MobileNetV2_V2"
)

fine_tuned.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=1e-5
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

checkpoint = OUT_DIR / "best_model.keras"

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        str(checkpoint),
        monitor="val_loss",
        save_best_only=True,
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
        min_lr=1e-7
    )
]

print("\n===== STARTING FINE-TUNING =====")

history = fine_tuned.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)

# Evaluate the saved best checkpoint.
best = tf.keras.models.load_model(checkpoint)

evaluation = best.evaluate(
    test_ds,
    return_dict=True,
    verbose=1
)

probabilities = best.predict(test_ds, verbose=0)
predictions = (probabilities >= 0.5).astype(int)
actual_labels = test_y.astype(int)


def class_metrics(actual, predicted):
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


results = {}

print("\n===== V2 TEST RESULTS =====")

for i, label in enumerate(LABELS):
    result = class_metrics(
        actual_labels[:, i],
        predictions[:, i]
    )
    results[label] = result

    print(
        f"{label}: Precision={result['precision']:.4f}, "
        f"Recall={result['recall']:.4f}, "
        f"F1={result['f1']:.4f}"
    )

report = {
    "experiment": "crooked_detection_baseline_v2",
    "starting_checkpoint": str(
        V1_DIR / "best_model.keras"
    ),
    "epochs_completed": len(history.history["loss"]),
    "threshold": 0.5,
    "split_sizes": actual,
    "test_evaluation": {
        k: float(v) for k, v in evaluation.items()
    },
    "per_class_metrics": results,
    "limitations": [
        "Source labels are not clinically validated.",
        "Small held-out test set.",
        "Possible patient-level leakage remains.",
        "Does not evaluate crowding or spacing.",
        "No test-set-based threshold tuning."
    ]
}

(OUT_DIR / "metrics.json").write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

(OUT_DIR / "labels.json").write_text(
    json.dumps(LABELS, indent=2),
    encoding="utf-8"
)

(OUT_DIR / "training_history.json").write_text(
    json.dumps(
        {
            k: [float(v) for v in values]
            for k, values in history.history.items()
        },
        indent=2
    ),
    encoding="utf-8"
)

print("\nBASELINE V2 COMPLETED")
print("Results saved:", OUT_DIR)
