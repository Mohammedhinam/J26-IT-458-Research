import csv
import json
import random
from pathlib import Path

import numpy as np
import tensorflow as tf


ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT
    / "data"
    / "processed"
    / "spacing_stratified"
    / "spacing_split_manifest.csv"
)

OUT_DIR = (
    ROOT
    / "models"
    / "spacing_binary_stratified"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 8
EPOCHS = 20

random.seed(SEED)
np.random.seed(SEED)
tf.keras.utils.set_random_seed(SEED)


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

            if not image_path.is_file():
                raise FileNotFoundError(
                    image_path
                )

            label_name = (
                row["label"]
                .strip()
                .lower()
            )

            if label_name == "spacing":
                label = 1.0

            elif label_name == "normal":
                label = 0.0

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
            dtype=np.float32
        )
    )


train_paths, train_y = load_split(
    "train"
)

valid_paths, valid_y = load_split(
    "valid"
)

test_paths, test_y = load_split(
    "test"
)


print("=" * 60)
print(
    "SPACING VS NORMAL - STRATIFIED MobileNetV2"
)
print("=" * 60)

for split, paths, labels in [
    ("TRAIN", train_paths, train_y),
    ("VALID", valid_paths, valid_y),
    ("TEST", test_paths, test_y),
]:
    spacing_count = int(
        labels.sum()
    )

    normal_count = int(
        len(labels)
        - labels.sum()
    )

    print(f"\n{split}")
    print("Images:", len(paths))
    print("Spacing:", spacing_count)
    print("Normal:", normal_count)


for name, labels in [
    ("train", train_y),
    ("valid", valid_y),
    ("test", test_y),
]:
    if len(labels) == 0:
        raise RuntimeError(
            f"{name} split is empty."
        )

    if len(np.unique(labels)) < 2:
        raise RuntimeError(
            f"{name} split does not contain both classes."
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
    labels,
    training=False
):
    dataset = (
        tf.data.Dataset
        .from_tensor_slices(
            (paths, labels)
        )
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

    dataset = dataset.batch(
        BATCH_SIZE
    )

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


augmentation = tf.keras.Sequential(
    [
        tf.keras.layers.RandomRotation(
            0.04
        ),
        tf.keras.layers.RandomZoom(
            0.08
        ),
        tf.keras.layers.RandomContrast(
            0.08
        ),
        tf.keras.layers.RandomTranslation(
            0.03,
            0.03
        ),
    ],
    name="augmentation"
)


base_model = (
    tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet"
    )
)

base_model.trainable = False


inputs = tf.keras.Input(
    shape=(224, 224, 3),
    name="image"
)

x = augmentation(inputs)

x = (
    tf.keras.applications
    .mobilenet_v2
    .preprocess_input(x)
)

x = base_model(
    x,
    training=False
)

x = (
    tf.keras.layers
    .GlobalAveragePooling2D()(x)
)

x = tf.keras.layers.Dropout(
    0.3
)(x)

outputs = tf.keras.layers.Dense(
    1,
    activation="sigmoid",
    name="spacing_probability"
)(x)

model = tf.keras.Model(
    inputs,
    outputs,
    name="Spacing_Normal_Stratified_MobileNetV2"
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


checkpoint = (
    OUT_DIR
    / "best_model.keras"
)

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        str(checkpoint),
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=5,
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
    (actual == 1)
    & (predictions == 1)
))

fp = int(np.sum(
    (actual == 0)
    & (predictions == 1)
))

fn = int(np.sum(
    (actual == 1)
    & (predictions == 0)
))

tn = int(np.sum(
    (actual == 0)
    & (predictions == 0)
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
    if precision + recall
    else 0.0
)


print("\nConfusion Matrix")
print("TP:", tp)
print("FP:", fp)
print("FN:", fn)
print("TN:", tn)

print("\nFinal Metrics")
print(
    "Precision:",
    round(precision, 4)
)
print(
    "Recall:",
    round(recall, 4)
)
print(
    "F1:",
    round(f1, 4)
)
print(
    "Accuracy:",
    round(
        float(
            test_result["accuracy"]
        ),
        4
    )
)
print(
    "AUC:",
    round(
        float(
            test_result["auc"]
        ),
        4
    )
)


report = {
    "experiment":
        "spacing_vs_normal_stratified",

    "source_dataset":
        "smile_spacing",

    "model":
        "MobileNetV2",

    "threshold":
        0.5,

    "seed":
        SEED,

    "split_sizes": {
        "train":
            len(train_paths),
        "valid":
            len(valid_paths),
        "test":
            len(test_paths),
    },

    "class_counts": {
        "train": {
            "spacing":
                int(train_y.sum()),
            "normal":
                int(
                    len(train_y)
                    - train_y.sum()
                ),
        },

        "valid": {
            "spacing":
                int(valid_y.sum()),
            "normal":
                int(
                    len(valid_y)
                    - valid_y.sum()
                ),
        },

        "test": {
            "spacing":
                int(test_y.sum()),
            "normal":
                int(
                    len(test_y)
                    - test_y.sum()
                ),
        },
    },

    "test_metrics": {
        key: float(value)
        for key, value
        in test_result.items()
    },

    "confusion_matrix": {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    },

    "precision":
        precision,

    "recall":
        recall,

    "f1":
        f1,

    "limitations": [
        (
            "Only the smile_spacing "
            "dataset is used."
        ),
        (
            "Only 11 usable Spacing-positive "
            "images are available."
        ),
        (
            "The validation split contains "
            "only 1 Spacing-positive image."
        ),
        (
            "The test split contains "
            "only 3 Spacing-positive images."
        ),
        (
            "The split is class-stratified "
            "but not confirmed patient-level."
        ),
        (
            "Labels were not clinically "
            "revalidated."
        ),
        (
            "This is a preliminary "
            "research baseline."
        ),
    ]
}


(
    OUT_DIR
    / "metrics.json"
).write_text(
    json.dumps(
        report,
        indent=2
    ),
    encoding="utf-8"
)


(
    OUT_DIR
    / "training_history.json"
).write_text(
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
print(
    "SPACING STRATIFIED TRAINING COMPLETE"
)
print(
    "Model:",
    checkpoint
)
print(
    "Metrics:",
    OUT_DIR
    / "metrics.json"
)
print("================================")