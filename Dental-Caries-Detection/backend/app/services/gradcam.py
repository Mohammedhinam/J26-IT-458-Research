
import numpy as np
import tensorflow as tf
from PIL import Image
from pathlib import Path
from app.services.caries_prediction import load_models
import io
import base64
import matplotlib
matplotlib.use("Agg")
from matplotlib import cm


def generate_gradcam(model, image_array, model_type):
    """
    Generate a Grad-CAM heatmap for a saved Keras classifier.

    image_array: RGB image resized to 224x224
    model_type: 'mobilenet' or 'efficientnet'
    """

    if model_type == "mobilenet":
        backbone_name = "mobilenetv2_1.00_224"
    elif model_type == "efficientnet":
        backbone_name = "efficientnetb0"
    else:
        raise ValueError("Unsupported model type")

    backbone = model.get_layer(backbone_name)

    # Prepare input: RGB float32 in the 0-255 range
    image_array = np.asarray(image_array, dtype=np.float32)
    image_tensor = tf.convert_to_tensor(
        np.expand_dims(image_array, axis=0)
    )

    # Apply the saved preprocessing layers
    x = image_tensor

    for layer in model.layers[1:]:
        if layer.name == backbone_name:
            break
        x = layer(x, training=False)

    # Extract backbone feature maps and calculate prediction
    with tf.GradientTape() as tape:
        feature_maps = backbone(x, training=False)
        tape.watch(feature_maps)

        y = feature_maps

        backbone_index = model.layers.index(backbone)

        for layer in model.layers[backbone_index + 1:]:
            y = layer(y, training=False)

        predicted_class = tf.argmax(y[0])
        class_score = tf.gather(y[0], predicted_class)

    # Calculate gradients
    gradients = tape.gradient(class_score, feature_maps)

    if gradients is None:
        raise RuntimeError("Grad-CAM gradients could not be computed")

    # Global average pooling of gradients
    pooled_gradients = tf.reduce_mean(
        gradients, axis=(0, 1, 2)
    )

    # Weighted combination of feature maps
    heatmap = tf.reduce_sum(
        feature_maps[0] * pooled_gradients,
        axis=-1
    )

    heatmap = tf.maximum(heatmap, 0)

    max_value = tf.reduce_max(heatmap)

    heatmap = heatmap / (max_value + 1e-8)

    return heatmap.numpy(), int(predicted_class.numpy())


def resize_heatmap(heatmap, size=(224, 224)):
    """Resize normalized heatmap for visualization."""

    heatmap_uint8 = np.uint8(
        np.clip(heatmap, 0, 1) * 255
    )

    return np.asarray(
        Image.fromarray(heatmap_uint8).resize(
            size, Image.Resampling.BILINEAR
        ),
        dtype=np.float32
    ) / 255.0

def prepare_region_crop(image_path, region_number):
    """
    Detect caries regions and prepare the selected
    region crop for Grad-CAM.
    """

    # Reuse the existing cached YOLO model
    yolo_model, _, _ = load_models()

    image_path = Path(image_path)

    with Image.open(image_path) as img:
        image = img.convert("RGB")

    width, height = image.size

    # Match the existing prediction endpoint settings
    detection = yolo_model.predict(
        source=str(image_path),
        conf=0.25,
        verbose=False
    )[0]

    boxes = detection.boxes.xyxy.cpu().numpy()

    if region_number < 1 or region_number > len(boxes):
        raise ValueError(
            f"Invalid region number. Detected regions: {len(boxes)}"
        )

    # Region R1 corresponds to boxes[0]
    x1, y1, x2, y2 = boxes[region_number - 1]

    # Apply the existing 30% crop padding
    pad_x = (x2 - x1) * 0.30
    pad_y = (y2 - y1) * 0.30

    crop = image.crop((
        max(0, int(x1 - pad_x)),
        max(0, int(y1 - pad_y)),
        min(width, int(x2 + pad_x)),
        min(height, int(y2 + pad_y))
    ))

    # Same classifier input preprocessing
    image_array = np.asarray(
        crop.resize((224, 224)),
        dtype=np.float32
    )

    return image_array


def generate_region_gradcams(image_path, region_number):
    """
    Generate MobileNetV2 and EfficientNet-B0
    Grad-CAM heatmaps for one YOLO-detected region.
    """

    # Load existing trained models
    _, mobile_model, efficient_model = load_models()

    # Prepare selected YOLO region crop
    image_array = prepare_region_crop(
        image_path,
        region_number
    )

    # MobileNetV2 Grad-CAM
    mobile_heatmap, mobile_class = generate_gradcam(
        mobile_model,
        image_array,
        "mobilenet"
    )

    # EfficientNet-B0 Grad-CAM
    efficient_heatmap, efficient_class = generate_gradcam(
        efficient_model,
        image_array,
        "efficientnet"
    )
# Create displayable Grad-CAM overlays for the selected crop
    mobile_overlay = create_gradcam_overlay(
        image_array,
        mobile_heatmap
    )

    efficient_overlay = create_gradcam_overlay(
        image_array,
        efficient_heatmap
    )

    return {
    "region": region_number,
    "mobile_heatmap": mobile_heatmap,
    "mobile_class": mobile_class,
    "mobile_overlay": mobile_overlay,
    "efficient_heatmap": efficient_heatmap,
    "efficient_class": efficient_class,
    "efficient_overlay": efficient_overlay
}


def create_gradcam_overlay(image_array, heatmap):
    """
    Create a colored Grad-CAM overlay and return
    it as a Base64-encoded PNG data URL.
    """

    original = np.asarray(image_array, dtype=np.uint8)

    # Resize the existing 7x7 heatmap
    resized = resize_heatmap(
        heatmap,
        size=(224, 224)
    )

    # Apply the jet color map
    colored = matplotlib.colormaps["jet"](resized)[..., :3]
    colored = np.uint8(colored * 255)

    # Blend the original crop and heatmap
    blended = np.uint8(
        np.clip(
            original.astype(np.float32) * 0.6
            + colored.astype(np.float32) * 0.4,
            0,
            255
        )
    )

    # Convert to PNG in memory
    buffer = io.BytesIO()

    Image.fromarray(blended).save(
        buffer,
        format="PNG"
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return f"data:image/png;base64,{encoded}"
