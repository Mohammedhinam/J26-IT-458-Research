import csv
import json
import random
from pathlib import Path

import numpy as np
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "raw" / "crooked_detection"
V1_DIR = ROOT / "models" / "crooked_baseline"

OUT_DIR = ROOT / "models" / "openbite_binary"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 15

random.seed(SEED)
np.random.seed(SEED)
tf.keras.utils.set_random_seed(SEED)

excluded = set(json.loads(
    (V1_DIR / "excluded_leakage.json").read_text(
        encoding="utf-8"
    )
))


def normalize_path(path):
    return str(Path(path).resolve()).lower()


def load_split(split):
    folder = DATA_DIR / split
    csv_path = folder / "_classes.csv"

    paths = []
    labels = []

    stats = {
        "openbite": 0,
        "normal": 0,
        "excluded_other_conditions": 0,
        "excluded_duplicate": 0,
        "unlabeled": 0,
    }

    with csv_path.open(
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            path = folder / row["filename"]

            if not path.is_file():
                continue

            if normalize_path(path) in excluded:
                stats["excluded_duplicate"] += 1
                continue

            if row.get("Unlabeled", "0").strip() == "1":
                stats["unlabeled"] += 1
                continue

            openbite = int(row["openbite"])
            normal = int(row["normal"])

            crossbite = int(row["crossbite"])
            overbite = int(row["overbite"])
            underbite = int(row["underbite"])

            # Pure Open Bite positive
            if openbite == 1 and normal == 0:
                if crossbite or overbite or underbite:
                    stats["excluded_other_conditions"] += 1
                    continue

                paths.append(str(path))
                labels.append(1.0)
                stats["openbite"] += 1

            # Pure Normal negative
            elif normal == 1 and openbite == 0:
                if crossbite or overbite or underbite:
                    stats["excluded_other_conditions"] += 1
                    continue

                paths.append(str(path))
                labels.append(0.0)
                stats["normal"] += 1

            else:
                stats["excluded_other_conditions"] += 1

    return (
        paths,
        np.asarray(labels, dtype=np.float32),
        stats
    )


train_paths, train_y, train_stats = load_split("train")
valid_paths, valid_y, valid_stats = load_split("valid")
test_paths, test_y, test_stats = load_split("test")

print("=" * 55)
print("OPEN BITE VS NORMAL - MobileNetV2")
print("=" * 55)

for split, paths, labels, stats in [
    ("TRAIN", train_paths, train_y, train_stats),
    ("VALID", valid_paths, valid_y, valid_stats),
    ("TEST", test_paths, test_y, test_stats),
]:
    print(f"\n{split}")
    print("Images:", len(paths))
    print("Open Bite:", int(labels.sum()))
    print("Normal:", int(len(labels) - labels.sum()))
    print("Stats:", stats)

if len(train_paths) == 0:
    raise RuntimeError("No training data available.")

if len(valid_paths) == 0:
    raise RuntimeError("No validation data available.")

if len(test_paths) == 0:
    raise RuntimeError("No test data available.")


def read_image(path, label):
    data = tf.io.read_file(path)

    image = tf.io.decode_image(
        data,
        channels=3,
        expand_animations=False
    )

    image.set_shape((None, None, 3))

    image = tf.image.resize(
        image,
        IMAGE_SIZE
    )

    image = tf.cast(image, tf.float32)

    return image, label


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

    dataset = dataset.batch(BATCH_SIZE)

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset


train_ds = make_dataset(
    train_paths,
    train_y,
    training=True
)

valid_ds = make_dataset(
    valid_paths,
    valid_y
)

test_ds = make_dataset(
    test_paths,
    test_y
)


augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomRotation(0.04),
    tf.keras.layers.RandomZoom(0.08),
    tf.keras.layers.RandomContrast(0.08),
], name="augmentation")


base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False


inputs = tf.keras.Input(
    shape=(224, 224, 3),
    name="image"
)

x = augmentation(inputs)

x = tf.keras.applications.mobilenet_v2.preprocess_input(x)

x = base_model(
    x,
    training=False
)

x = tf.keras.layers.GlobalAveragePooling2D()(x)

x = tf.keras.layers.Dropout(0.3)(x)

outputs = tf.keras.layers.Dense(
    1,
    activation="sigmoid",
    name="openbite_probability"
)(x)

model = tf.keras.Model(
    inputs,
    outputs,
    name="Openbite_Normal_MobileNetV2"
)

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=1e-4
    ),
    loss="binary_crossentropy",
    metrics=[
        tf.keras.metrics.BinaryAccuracy(
            name="accuracy"
        ),
        tf.keras.metrics.Precision(
            name="precision"
        ),
        tf.keras.metrics.Recall(
            name="recall"
        ),
        tf.keras.metrics.AUC(
            name="auc"
        ),
    ]
)

model.summary()


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
        min_lr=1e-6
    )
]


print("\n===== TRAINING =====")

history = model.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)


best_model = tf.keras.models.load_model(
    checkpoint
)


print("\n===== TEST EVALUATION =====")

test_result = best_model.evaluate(
    test_ds,
    return_dict=True,
    verbose=1
)

probabilities = best_model.predict(
    test_ds,
    verbose=0
).reshape(-1)

predictions = (
    probabilities >= 0.5
).astype(int)

actual = test_y.astype(int)

tp = int(np.sum(
    (actual == 1) & (predictions == 1)
))

fp = int(np.sum(
    (actual == 0) & (predictions == 1)
))

fn = int(np.sum(
    (actual == 1) & (predictions == 0)
))

tn = int(np.sum(
    (actual == 0) & (predictions == 0)
))

precision = (
    tp / (tp + fp)
    if (tp + fp) else 0.0
)

recall = (
    tp / (tp + fn)
    if (tp + fn) else 0.0
)

f1 = (
    2 * precision * recall
    / (precision + recall)
    if (precision + recall)
    else 0.0
)

print("\nConfusion Matrix")
print("TP:", tp)
print("FP:", fp)
print("FN:", fn)
print("TN:", tn)

print("\nFinal Metrics")
print("Precision:", round(precision, 4))
print("Recall:", round(recall, 4))
print("F1:", round(f1, 4))
print(
    "Accuracy:",
    round(float(test_result["accuracy"]), 4)
)
print(
    "AUC:",
    round(float(test_result["auc"]), 4)
)


report = {
    "experiment": "openbite_vs_normal_binary",
    "model": "MobileNetV2",
    "threshold": 0.5,

    "split_sizes": {
        "train": len(train_paths),
        "valid": len(valid_paths),
        "test": len(test_paths),
    },

    "split_stats": {
        "train": train_stats,
        "valid": valid_stats,
        "test": test_stats,
    },

    "test_metrics": {
        key: float(value)
        for key, value in test_result.items()
    },

    "confusion_matrix": {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    },

    "precision": precision,
    "recall": recall,
    "f1": f1,

    "limitations": [
        "Uses original public dataset annotations.",
        "Labels were not clinically revalidated.",
        "Only clean Open Bite and Normal examples are used.",
        "Small test set limits reliability.",
        "This is an experimental research baseline.",
        "Not suitable for clinical diagnosis."
    ]
}

(OUT_DIR / "metrics.json").write_text(
    json.dumps(
        report,
        indent=2
    ),
    encoding="utf-8"
)

(OUT_DIR / "training_history.json").write_text(
    json.dumps(
        {
            key: [
                float(value)
                for value in values
            ]
            for key, values
            in history.history.items()
        },
        indent=2
    ),
    encoding="utf-8"
)

print("\n================================")
print("OPEN BITE BINARY TRAINING COMPLETE")
print("Model:", checkpoint)
print(
    "Metrics:",
    OUT_DIR / "metrics.json"
)
print("================================")