
import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "crooked_baseline_v2"
OUTPUT_DIR = ROOT / "explainability" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LABELS = json.loads(
    (MODEL_DIR / "labels.json").read_text(encoding="utf-8")
)

model = tf.keras.models.load_model(
    MODEL_DIR / "best_model.keras",
    compile=False
)

# V2 model contains the V1 classifier as a nested model.
classifier = next(
    layer for layer in model.layers
    if isinstance(layer, tf.keras.Model)
    and "Malocclusion_MobileNetV2_Baseline".lower()
       in layer.name.lower()
)

backbone = next(
    layer for layer in classifier.layers
    if isinstance(layer, tf.keras.Model)
    and "mobilenetv2" in layer.name.lower()
)

augmentation = model.get_layer("training_augmentation")
rescaling = classifier.get_layer("rescaling")
pooling = classifier.get_layer("global_average_pooling2d")
dropout = classifier.get_layer("dropout")
prediction_head = classifier.get_layer("dental_conditions")

# Extract intermediate convolution features and final backbone output.
feature_model = tf.keras.Model(
    inputs=backbone.input,
    outputs=[
        backbone.get_layer("Conv_1").output,
        backbone.output
    ]
)


def prepare_image(image_path):
    original = Image.open(image_path).convert("RGB")
    resized = original.resize((224, 224))
    array = np.asarray(resized, dtype=np.float32)
    batch = tf.convert_to_tensor(array[None, ...])
    return original, batch


def generate_gradcam(batch, class_index):
    with tf.GradientTape() as tape:
        x = augmentation(batch, training=False)
        x = rescaling(x)

        conv_features, backbone_output = feature_model(
            x, training=False
        )

        tape.watch(conv_features)

        x = pooling(backbone_output)
        x = dropout(x, training=False)
        predictions = prediction_head(x)

        target_score = predictions[:, class_index]

    gradients = tape.gradient(target_score, conv_features)

    if gradients is None:
        raise RuntimeError("Grad-CAM gradients unavailable.")

    weights = tf.reduce_mean(gradients, axis=(1, 2))
    heatmap = tf.reduce_sum(
        conv_features * weights[:, None, None, :],
        axis=-1
    )

    heatmap = tf.nn.relu(heatmap)[0]
    heatmap = heatmap.numpy()

    maximum = float(heatmap.max())
    if maximum > 0:
        heatmap = heatmap / maximum
    else:
        print("Warning: No positive Grad-CAM activation.")

    return heatmap, predictions.numpy()[0]


def create_overlay(original, heatmap):
    heatmap_image = Image.fromarray(
        np.uint8(np.clip(heatmap, 0, 1) * 255)
    ).resize(original.size, Image.Resampling.BILINEAR)

    intensity = np.asarray(
        heatmap_image, dtype=np.float32
    ) / 255.0

    # Red: stronger model activation
    # Blue: weaker model activation
    colored = np.zeros(
        (original.height, original.width, 3),
        dtype=np.uint8
    )
    colored[..., 0] = np.uint8(255 * intensity)
    colored[..., 2] = np.uint8(255 * (1 - intensity))

    color_image = Image.fromarray(colored)
    overlay = Image.blend(original, color_image, alpha=0.4)

    return color_image, overlay


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument(
        "--class-name",
        choices=LABELS,
        default=None
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)

    original, batch = prepare_image(image_path)

    probabilities = model(batch, training=False).numpy()[0]

    if args.class_name:
        index = LABELS.index(args.class_name)
    else:
        index = int(np.argmax(probabilities))

    heatmap, _ = generate_gradcam(batch, index)
    color_image, overlay = create_overlay(original, heatmap)

    prefix = image_path.stem[:50]
    label = LABELS[index]

    color_path = OUTPUT_DIR / f"{prefix}_{label}_heatmap.png"
    overlay_path = OUTPUT_DIR / f"{prefix}_{label}_overlay.png"

    color_image.save(color_path)
    overlay.save(overlay_path)

    print("\n===== PREDICTIONS =====")
    for name, probability in zip(LABELS, probabilities):
        print(f"{name}: {probability:.4f}")

    print("\nGrad-CAM target class:", label)
    print("Heatmap:", color_path)
    print("Overlay:", overlay_path)
    print("\nResearch visualization only; not a clinical diagnosis.")


if __name__ == "__main__":
    main()
