
import base64
import io

import cv2
import numpy as np
from PIL import Image

from explainability.compare_gradcam_layers import (
    make_gradcam,
    normalize_heatmap,
    create_overlay,
)


# Layer selections from previous exploratory comparisons.
GRADCAM_LAYERS = {
    "crossbite": "block_14_expand_relu",
    "open_bite": "block_13_expand_relu",
    "crowding": "block_14_expand_relu",
}

IMAGE_SIZE = (224, 224)
MAX_IMAGE_PIXELS = 10_000_000


def decode_image(image_bytes):
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.load()

        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ValueError("Image dimensions are too large.")

        original_rgb = np.asarray(
            image.convert("RGB"),
            dtype=np.uint8
        ).copy()

    resized = cv2.resize(
        original_rgb,
        IMAGE_SIZE,
        interpolation=cv2.INTER_AREA
    )

    image_batch = np.expand_dims(
        resized.astype(np.float32),
        axis=0
    )

    return original_rgb, image_batch


def encode_png(image_rgb):
    image_bgr = cv2.cvtColor(
        image_rgb,
        cv2.COLOR_RGB2BGR
    )

    success, buffer = cv2.imencode(
        ".png",
        image_bgr
    )

    if not success:
        raise RuntimeError("PNG encoding failed.")

    encoded = base64.b64encode(
        buffer.tobytes()
    ).decode("ascii")

    return "data:image/png;base64," + encoded


def generate_explanation(
    model,
    condition,
    image_bytes
):
    if condition not in GRADCAM_LAYERS:
        raise ValueError(
            f"Grad-CAM is not available for: {condition}"
        )

    original_rgb, image_batch = decode_image(
        image_bytes
    )

    layer_name = GRADCAM_LAYERS[condition]

    # Prediction and Grad-CAM use the same input batch.
    prediction = model(
        image_batch,
        training=False
    )

    probability = float(
        np.asarray(prediction).reshape(-1)[0]
    )

    raw_heatmap = make_gradcam(
        model=model,
        image_batch=image_batch,
        target_layer_name=layer_name
    )

    if raw_heatmap is None:
        raise RuntimeError(
            "Gradients could not be calculated."
        )

    if not np.all(np.isfinite(raw_heatmap)):
        raise RuntimeError(
            "Grad-CAM produced non-finite values."
        )

    heatmap = normalize_heatmap(
        raw_heatmap
    )

    if heatmap is None:
        raise RuntimeError(
            "Heatmap normalization failed."
        )

    has_activation = bool(
        np.any(heatmap > 0)
    )

    height, width = original_rgb.shape[:2]

    resized_heatmap = cv2.resize(
        heatmap,
        (width, height),
        interpolation=cv2.INTER_CUBIC
    )

    resized_heatmap = np.clip(
        resized_heatmap,
        0,
        1
    )

    heatmap_uint8 = np.uint8(
        resized_heatmap * 255
    )

    colored_heatmap_bgr = cv2.applyColorMap(
        heatmap_uint8,
        cv2.COLORMAP_JET
    )

    colored_heatmap_rgb = cv2.cvtColor(
        colored_heatmap_bgr,
        cv2.COLOR_BGR2RGB
    )

    overlay_rgb = create_overlay(
        original_rgb,
        heatmap
    )

    return {
        "condition": condition,
        "status": (
            "generated"
            if has_activation
            else "weak_or_empty_activation"
        ),
        "probability": round(probability, 4),
        "target_layer": layer_name,
        "images": {
            "original": encode_png(original_rgb),
            "heatmap": encode_png(colored_heatmap_rgb),
            "overlay": encode_png(overlay_rgb),
        },
        "interpretation": (
            "Grad-CAM visualizes regions influencing "
            "the selected model output."
        ),
        "limitations": (
            "This exploratory visualization is not "
            "clinically validated. Highlighted regions "
            "may include lips, image boundaries, or "
            "background and do not establish that "
            "the prediction is clinically correct."
        ),
    }
