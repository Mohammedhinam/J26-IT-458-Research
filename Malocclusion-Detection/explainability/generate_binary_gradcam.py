import csv
import json
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    ROOT
    / "explainability"
    / "binary_outputs_v2"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

IMAGE_SIZE = (224, 224)

MAX_IMAGES_PER_CONDITION = 3


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

        "threshold":
            0.5,
    },

    {
        "condition":
            "openbite",

        "display_name":
            "Open Bite",

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

        "threshold":
            0.5,
    },

    {
        "condition":
            "crowding",

        "display_name":
            "Crowding",

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

        "threshold":
            0.5,
    },
]


def load_examples_from_crooked_csv(
    csv_path,
    image_dir,
    positive_column,
    limit=3
):
    selected = []

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

            filename = (
                row["filename"]
                .strip()
            )

            image_path = (
                image_dir
                / filename
            )

            if image_path.is_file():
                selected.append(
                    image_path
                )

            if len(selected) >= limit:
                break

    return selected


def load_examples_from_manifest(
    manifest_path,
    split_name,
    label_name,
    limit=3
):
    selected = []

    with open(
        manifest_path,
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            current_split = (
                row.get(
                    "split",
                    ""
                )
                .strip()
                .lower()
            )

            current_label = (
                row.get(
                    "label",
                    ""
                )
                .strip()
                .lower()
            )

            if (
                current_split
                != split_name.lower()
            ):
                continue

            if (
                current_label
                != label_name.lower()
            ):
                continue

            image_path = Path(
                row["image"]
            )

            if image_path.is_file():
                selected.append(
                    image_path
                )

            if len(selected) >= limit:
                break

    return selected


def collect_images(config):

    if (
        config["dataset_type"]
        == "crooked_detection_csv"
    ):

        return (
            load_examples_from_crooked_csv(
                csv_path=
                    config["csv_path"],

                image_dir=
                    config["image_dir"],

                positive_column=
                    config[
                        "positive_column"
                    ],

                limit=
                    MAX_IMAGES_PER_CONDITION
            )
        )

    if (
        config["dataset_type"]
        == "manifest_csv"
    ):

        return (
            load_examples_from_manifest(
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

                limit=
                    MAX_IMAGES_PER_CONDITION
            )
        )

    raise ValueError(
        "Unsupported dataset type."
    )


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

    return (
        image_rgb,
        batch
    )


def find_backbone_and_last_conv(
    model
):

    for layer in model.layers:

        if isinstance(
            layer,
            tf.keras.Model
        ):

            conv_layers = [
                sub_layer
                for sub_layer
                in layer.layers
                if isinstance(
                    sub_layer,
                    tf.keras.layers.Conv2D
                )
            ]

            if conv_layers:

                return (
                    layer,
                    conv_layers[-1]
                )

    raise RuntimeError(
        "CNN backbone not found."
    )


def make_gradcam_heatmap(
    model,
    image_batch
):

    backbone, last_conv = (
        find_backbone_and_last_conv(
            model
        )
    )

    print(
        "Backbone:",
        backbone.name
    )

    print(
        "Grad-CAM layer:",
        last_conv.name
    )

    backbone_index = (
        model.layers.index(
            backbone
        )
    )

    feature_model = (
        tf.keras.Model(
            inputs=
                backbone.input,

            outputs=[
                last_conv.output,
                backbone.output
            ]
        )
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

        conv_outputs, x = (
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
        conv_outputs
    )

    if grads is None:
        raise RuntimeError(
            "Gradients could not "
            "be calculated."
        )

    weights = tf.reduce_mean(
        grads,
        axis=(0, 1, 2)
    )

    activation_map = (
        conv_outputs[0]
    )

    heatmap = tf.reduce_sum(
        activation_map
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
        30
    )

    high = np.percentile(
        positive,
        99
    )

    if high <= low:
        high = np.max(
            positive
        )

    if high <= 0:
        return np.zeros_like(
            heatmap
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


def build_overlay(
    original_rgb,
    heatmap
):

    height, width = (
        original_rgb.shape[:2]
    )

    heatmap_resized = cv2.resize(
        heatmap,
        (width, height),
        interpolation=
            cv2.INTER_CUBIC
    )

    heatmap_uint8 = np.uint8(
        heatmap_resized * 255
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
        heatmap_resized >= 0.35
    ).astype(
        np.float32
    )

    alpha = (
        heatmap_resized
        * mask
        * 0.65
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

    return (
        heatmap_resized,
        color_map,
        overlay
    )


def add_text_banner(
    image_rgb,
    title,
    probability,
    predicted_label
):

    image_bgr = cv2.cvtColor(
        image_rgb,
        cv2.COLOR_RGB2BGR
    )

    banner_height = 70

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
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    text = (
        f"Prediction: "
        f"{predicted_label} | "
        f"Probability: "
        f"{probability:.3f}"
    )

    cv2.putText(
        canvas,
        text,
        (10, 53),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    return canvas


def create_side_by_side(
    original_rgb,
    overlay_rgb,
    display_name,
    probability,
    predicted_label
):

    original = cv2.resize(
        original_rgb,
        (500, 350)
    )

    overlay = cv2.resize(
        overlay_rgb,
        (500, 350)
    )

    combined = np.hstack(
        [
            original,
            overlay
        ]
    )

    combined_bgr = cv2.cvtColor(
        combined,
        cv2.COLOR_RGB2BGR
    )

    banner_height = 80

    canvas = np.zeros(
        (
            combined_bgr.shape[0]
            + banner_height,

            combined_bgr.shape[1],

            3
        ),
        dtype=np.uint8
    )

    canvas[
        banner_height:
    ] = combined_bgr

    cv2.putText(
        canvas,
        f"{display_name} - Grad-CAM",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    cv2.putText(
        canvas,
        (
            f"Prediction: "
            f"{predicted_label} | "
            f"Probability: "
            f"{probability:.3f}"
        ),
        (20, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    return canvas


def save_rgb(
    path,
    image_rgb
):

    image_bgr = cv2.cvtColor(
        image_rgb,
        cv2.COLOR_RGB2BGR
    )

    cv2.imwrite(
        str(path),
        image_bgr
    )


def run_condition(
    config
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"{config['display_name']} "
        "GRAD-CAM V2"
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

        return {
            "condition":
                config["condition"],

            "status":
                "skipped",

            "reason":
                "model_not_found"
        }

    images = collect_images(
        config
    )

    if not images:

        print(
            "[SKIP] No images found."
        )

        return {
            "condition":
                config["condition"],

            "status":
                "skipped",

            "reason":
                "no_images"
        }

    model = (
        tf.keras.models
        .load_model(
            model_path,
            compile=False
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

    outputs = []

    for index, image_path in enumerate(
        images,
        start=1
    ):

        print(
            f"\nProcessing "
            f"{index}: "
            f"{image_path.name}"
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

        predicted_label = (
            config["condition"]
            if probability
            >= config["threshold"]
            else "normal"
        )

        raw_heatmap = (
            make_gradcam_heatmap(
                model,
                batch
            )
        )

        normalized_heatmap = (
            normalize_heatmap(
                raw_heatmap
            )
        )

        (
            heatmap_resized,
            color_heatmap,
            overlay
        ) = build_overlay(
            original_rgb,
            normalized_heatmap
        )

        stem = (
            image_path.stem
        )

        original_path = (
            condition_dir
            / f"{stem}_original.png"
        )

        heatmap_path = (
            condition_dir
            / f"{stem}_heatmap.png"
        )

        overlay_path = (
            condition_dir
            / f"{stem}_overlay.png"
        )

        comparison_path = (
            condition_dir
            / f"{stem}_comparison.png"
        )

        save_rgb(
            original_path,
            original_rgb
        )

        cv2.imwrite(
            str(
                heatmap_path
            ),
            np.uint8(
                heatmap_resized
                * 255
            )
        )

        save_rgb(
            overlay_path,
            overlay
        )

        comparison = (
            create_side_by_side(
                original_rgb=
                    original_rgb,

                overlay_rgb=
                    overlay,

                display_name=
                    config[
                        "display_name"
                    ],

                probability=
                    probability,

                predicted_label=
                    predicted_label
            )
        )

        cv2.imwrite(
            str(
                comparison_path
            ),
            comparison
        )

        print(
            "Probability:",
            round(
                probability,
                4
            )
        )

        print(
            "Prediction:",
            predicted_label
        )

        print(
            "Comparison:",
            comparison_path
        )

        outputs.append(
            {
                "image":
                    str(
                        image_path
                    ),

                "probability":
                    probability,

                "predicted_label":
                    predicted_label,

                "original":
                    str(
                        original_path
                    ),

                "heatmap":
                    str(
                        heatmap_path
                    ),

                "overlay":
                    str(
                        overlay_path
                    ),

                "comparison":
                    str(
                        comparison_path
                    ),
            }
        )

    return {
        "condition":
            config[
                "condition"
            ],

        "status":
            "completed",

        "threshold":
            config[
                "threshold"
            ],

        "outputs":
            outputs
    }


def main():

    print(
        "=" * 70
    )

    print(
        "IMPROVED BINARY GRAD-CAM GENERATION"
    )

    print(
        "=" * 70
    )

    report = {
        "component":
            "Malocclusion Detection",

        "method":
            "Grad-CAM V2",

        "interpretation_note":
            (
                "Highlighted regions indicate "
                "areas contributing to the model "
                "prediction. They do not provide "
                "clinical proof or diagnosis."
            ),

        "conditions":
            []
    }

    for config in CONFIGS:

        result = run_condition(
            config
        )

        report[
            "conditions"
        ].append(
            result
        )

    report_path = (
        OUTPUT_DIR
        / "binary_gradcam_v2_report.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "GRAD-CAM V2 COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "Output:",
        OUTPUT_DIR
    )

    print(
        "Report:",
        report_path
    )


if __name__ == "__main__":
    main()