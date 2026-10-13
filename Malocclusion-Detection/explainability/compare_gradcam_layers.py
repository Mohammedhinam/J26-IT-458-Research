import csv
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    ROOT
    / "explainability"
    / "layer_comparisons"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

IMAGE_SIZE = (224, 224)

LAYERS_TO_TEST = [
    "block_13_expand_relu",
    "block_14_expand_relu",
    "block_15_project",
    "block_16_project",
    "Conv_1",
]


CONFIGS = [
    {
        "condition": "crossbite",
        "display_name": "Crossbite",

        "model_path":
            ROOT
            / "models"
            / "crossbite_binary"
            / "best_model.keras",

        "dataset_type":
            "crooked_detection_csv",

        "csv_path":
            ROOT
            / "data"
            / "raw"
            / "crooked_detection"
            / "test"
            / "_classes.csv",

        "image_dir":
            ROOT
            / "data"
            / "raw"
            / "crooked_detection"
            / "test",

        "positive_column":
            "crossbite",
    },

    {
        "condition": "openbite",
        "display_name": "Open Bite",

        "model_path":
            ROOT
            / "models"
            / "openbite_binary"
            / "best_model.keras",

        "dataset_type":
            "crooked_detection_csv",

        "csv_path":
            ROOT
            / "data"
            / "raw"
            / "crooked_detection"
            / "test"
            / "_classes.csv",

        "image_dir":
            ROOT
            / "data"
            / "raw"
            / "crooked_detection"
            / "test",

        "positive_column":
            "openbite",
    },

    {
        "condition": "crowding",
        "display_name": "Crowding",

        "model_path":
            ROOT
            / "models"
            / "crowding_binary_stratified"
            / "best_model.keras",

        "dataset_type":
            "manifest_csv",

        "manifest_path":
            ROOT
            / "data"
            / "processed"
            / "crowding_stratified"
            / "crowding_split_manifest.csv",

        "split_name":
            "test",

        "label_name":
            "crowding",
    },
]


def get_first_positive_crooked(
    csv_path,
    image_dir,
    positive_column
):
    with open(
        csv_path,
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            value = (
                row.get(
                    positive_column,
                    "0"
                )
                .strip()
            )

            if value != "1":
                continue

            image_path = (
                image_dir
                / row["filename"].strip()
            )

            if image_path.is_file():
                return image_path

    return None


def get_first_positive_manifest(
    manifest_path,
    split_name,
    label_name
):
    with open(
        manifest_path,
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            if (
                row["split"]
                .strip()
                .lower()
                != split_name.lower()
            ):
                continue

            if (
                row["label"]
                .strip()
                .lower()
                != label_name.lower()
            ):
                continue

            image_path = Path(
                row["image"]
            )

            if image_path.is_file():
                return image_path

    return None


def get_test_image(config):
    if (
        config["dataset_type"]
        == "crooked_detection_csv"
    ):
        return get_first_positive_crooked(
            csv_path=
                config["csv_path"],

            image_dir=
                config["image_dir"],

            positive_column=
                config[
                    "positive_column"
                ],
        )

    if (
        config["dataset_type"]
        == "manifest_csv"
    ):
        return get_first_positive_manifest(
            manifest_path=
                config[
                    "manifest_path"
                ],

            split_name=
                config[
                    "split_name"
                ],

            label_name=
                config[
                    "label_name"
                ],
        )

    return None


def load_image(image_path):
    image_bgr = cv2.imread(
        str(image_path)
    )

    if image_bgr is None:
        raise FileNotFoundError(
            image_path
        )

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB
    )

    resized = cv2.resize(
        image_rgb,
        IMAGE_SIZE
    )

    batch = np.expand_dims(
        resized.astype(
            np.float32
        ),
        axis=0
    )

    return image_rgb, batch


def find_backbone(model):
    for layer in model.layers:
        if isinstance(
            layer,
            tf.keras.Model
        ):
            try:
                layer.get_layer(
                    "Conv_1"
                )
                return layer
            except Exception:
                pass

    raise RuntimeError(
        "MobileNetV2 backbone not found."
    )


def make_gradcam(
    model,
    image_batch,
    target_layer_name
):
    backbone = find_backbone(
        model
    )

    try:
        target_layer = (
            backbone.get_layer(
                target_layer_name
            )
        )

    except ValueError:
        raise RuntimeError(
            f"Layer not found: "
            f"{target_layer_name}"
        )

    backbone_index = (
        model.layers.index(
            backbone
        )
    )

    feature_model = tf.keras.Model(
        inputs=
            backbone.input,

        outputs=[
            target_layer.output,
            backbone.output,
        ]
    )

    with tf.GradientTape() as tape:
        x = image_batch

        for layer in model.layers[
            1:backbone_index
        ]:
            x = layer(
                x,
                training=False
            )

        activations, x = (
            feature_model(
                x,
                training=False
            )
        )

        for layer in model.layers[
            backbone_index + 1:
        ]:
            x = layer(
                x,
                training=False
            )

        prediction = x[:, 0]

    grads = tape.gradient(
        prediction,
        activations
    )

    if grads is None:
        return None

    weights = tf.reduce_mean(
        grads,
        axis=(0, 1, 2)
    )

    feature_maps = (
        activations[0]
    )

    heatmap = tf.reduce_sum(
        feature_maps
        * weights,
        axis=-1
    )

    heatmap = tf.maximum(
        heatmap,
        0
    )

    heatmap = heatmap.numpy()

    return heatmap


def normalize_heatmap(
    heatmap
):
    if heatmap is None:
        return None

    heatmap = np.asarray(
        heatmap,
        dtype=np.float32
    )

    positive = heatmap[
        heatmap > 0
    ]

    if positive.size == 0:
        return np.zeros_like(
            heatmap
        )

    low = np.percentile(
        positive,
        20
    )

    high = np.percentile(
        positive,
        99
    )

    if high <= low:
        high = np.max(
            positive
        )

    normalized = (
        heatmap - low
    ) / (
        high - low + 1e-8
    )

    normalized = np.clip(
        normalized,
        0,
        1
    )

    return normalized


def create_overlay(
    original_rgb,
    heatmap
):
    height, width = (
        original_rgb.shape[:2]
    )

    resized_heatmap = cv2.resize(
        heatmap,
        (width, height),
        interpolation=
            cv2.INTER_CUBIC
    )

    heatmap_uint8 = np.uint8(
        resized_heatmap
        * 255
    )

    color_map = cv2.applyColorMap(
        heatmap_uint8,
        cv2.COLORMAP_JET
    )

    color_map = cv2.cvtColor(
        color_map,
        cv2.COLOR_BGR2RGB
    )

    mask = (
        resized_heatmap
        >= 0.30
    ).astype(
        np.float32
    )

    alpha = (
        resized_heatmap
        * mask
        * 0.70
    )

    alpha = alpha[
        ...,
        np.newaxis
    ]

    overlay = (
        original_rgb
        * (1 - alpha)
        +
        color_map
        * alpha
    )

    overlay = np.clip(
        overlay,
        0,
        255
    ).astype(
        np.uint8
    )

    return overlay


def resize_panel(
    image_rgb,
    width=320,
    height=240
):
    return cv2.resize(
        image_rgb,
        (width, height)
    )


def add_title(
    image_rgb,
    title
):
    image_bgr = cv2.cvtColor(
        image_rgb,
        cv2.COLOR_RGB2BGR
    )

    banner_height = 45

    canvas = np.zeros(
        (
            image_bgr.shape[0]
            + banner_height,
            image_bgr.shape[1],
            3
        ),
        dtype=np.uint8
    )

    canvas[
        banner_height:
    ] = image_bgr

    cv2.putText(
        canvas,
        title,
        (10, 29),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    return canvas


def compare_condition(
    config
):
    print(
        "\n"
        + "=" * 70
    )

    print(
        f"{config['display_name']} "
        "LAYER COMPARISON"
    )

    print(
        "=" * 70
    )

    model_path = (
        config["model_path"]
    )

    if not model_path.is_file():
        print(
            "[SKIP] Model not found:",
            model_path
        )
        return

    image_path = get_test_image(
        config
    )

    if image_path is None:
        print(
            "[SKIP] Positive test "
            "image not found."
        )
        return

    print(
        "Image:",
        image_path.name
    )

    model = (
        tf.keras.models
        .load_model(
            model_path,
            compile=False
        )
    )

    original_rgb, batch = (
        load_image(
            image_path
        )
    )

    probability = float(
        model.predict(
            batch,
            verbose=0
        )
        .reshape(-1)[0]
    )

    print(
        "Prediction probability:",
        round(
            probability,
            4
        )
    )

    condition_dir = (
        OUTPUT_DIR
        / config["condition"]
    )

    condition_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    panels = []

    original_panel = resize_panel(
        original_rgb
    )

    original_panel = add_title(
        original_panel,
        "Original"
    )

    panels.append(
        original_panel
    )

    for layer_name in (
        LAYERS_TO_TEST
    ):
        print(
            "Testing layer:",
            layer_name
        )

        try:
            heatmap = make_gradcam(
                model,
                batch,
                layer_name
            )

        except Exception as error:
            print(
                "[FAILED]",
                layer_name,
                error
            )
            continue

        normalized = (
            normalize_heatmap(
                heatmap
            )
        )

        overlay = create_overlay(
            original_rgb,
            normalized
        )

        overlay_path = (
            condition_dir
            / (
                f"{image_path.stem}_"
                f"{layer_name}_overlay.png"
            )
        )

        overlay_bgr = (
            cv2.cvtColor(
                overlay,
                cv2.COLOR_RGB2BGR
            )
        )

        cv2.imwrite(
            str(
                overlay_path
            ),
            overlay_bgr
        )

        panel = resize_panel(
            overlay
        )

        panel = add_title(
            panel,
            layer_name
        )

        panels.append(
            panel
        )

    if len(panels) <= 1:
        print(
            "No Grad-CAM panels "
            "were generated."
        )
        return

    comparison = np.hstack(
        panels
    )

    comparison_path = (
        condition_dir
        / (
            f"{image_path.stem}_"
            "layer_comparison.png"
        )
    )

    cv2.imwrite(
        str(
            comparison_path
        ),
        comparison
    )

    print(
        "Comparison saved:",
        comparison_path
    )


def main():
    print(
        "=" * 70
    )

    print(
        "GRAD-CAM LAYER COMPARISON"
    )

    print(
        "=" * 70
    )

    for config in CONFIGS:
        compare_condition(
            config
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "LAYER COMPARISON COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "Output:",
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()