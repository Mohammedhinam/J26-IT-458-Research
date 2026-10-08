
from pathlib import Path
from functools import lru_cache

import tensorflow as tf
from ultralytics import YOLO

# Locate the Dental-Caries-Detection component folder
BASE_DIR = Path(__file__).resolve().parents[3]

# Directory containing exported model files
MODEL_DIR = BASE_DIR / "models"

YOLO_PATH = MODEL_DIR / "best.pt"
MOBILENET_PATH = MODEL_DIR / "mobilenetv2.keras"
EFFICIENTNET_PATH = MODEL_DIR / "efficientnetb0.keras"

CLASS_NAMES = [
    "AdvanceEnamel_Caries",
    "EarlyStageEnamel_Caries",
    "NoEnamel_Caries"
]


@lru_cache(maxsize=1)
def load_models():
    """Load the three trained models once."""

    for path in [
        YOLO_PATH,
        MOBILENET_PATH,
        EFFICIENTNET_PATH
    ]:
        if not path.is_file():
            raise FileNotFoundError(
                f"Model file not found: {path}"
            )

    yolo_model = YOLO(str(YOLO_PATH))

    mobile_model = tf.keras.models.load_model(
        MOBILENET_PATH,
        compile=False
    )

    efficient_model = tf.keras.models.load_model(
        EFFICIENTNET_PATH,
        compile=False
    )

    return yolo_model, mobile_model, efficient_model

import numpy as np
from PIL import Image


def predict_dental_caries(image_path):
    """Detect suspected caries and predict severity."""

    yolo_model, mobile_model, efficient_model = load_models()

    image_path = Path(image_path)
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    # Step 1: Detect suspected caries regions
    detection = yolo_model.predict(
        source=str(image_path),
        conf=0.25,
        verbose=False
    )[0]

    boxes = detection.boxes.xyxy.cpu().numpy()
    confidences = detection.boxes.conf.cpu().numpy()

    if len(boxes) == 0:
        return {
            "image": image_path.name,
            "total_regions": 0,
            "regions": [],
            "message": "No suspected regions detected"
        }

    crops = []

    # Step 2: Expand bounding boxes by 30%
    for box in boxes:
        x1, y1, x2, y2 = box

        pad_x = (x2 - x1) * 0.30
        pad_y = (y2 - y1) * 0.30

        crop = image.crop((
            max(0, int(x1 - pad_x)),
            max(0, int(y1 - pad_y)),
            min(width, int(x2 + pad_x)),
            min(height, int(y2 + pad_y))
        ))

        crops.append(
            np.asarray(
                crop.resize((224, 224)),
                dtype=np.float32
            )
        )

    batch = np.stack(crops)

    # Step 3: Run severity classification
    mobile_probs = mobile_model.predict(
        batch, verbose=0
    )

    efficient_probs = efficient_model.predict(
        batch, verbose=0
    )

    region_results = []

    # Step 4: Compare model predictions
    for i, box in enumerate(boxes):
        m_idx = int(np.argmax(mobile_probs[i]))
        e_idx = int(np.argmax(efficient_probs[i]))

        mobile_class = CLASS_NAMES[m_idx]
        efficient_class = CLASS_NAMES[e_idx]

        if mobile_class == efficient_class:
            status = "Agreement"
            final_prediction = mobile_class
        else:
            status = "Uncertain - Review Required"
            final_prediction = "Uncertain"

        region_results.append({
            "region": i + 1,
            "bounding_box": box.astype(int).tolist(),
            "detection_confidence": round(
                float(confidences[i]), 4
            ),
            "MobileNetV2": {
                "prediction": mobile_class,
                "confidence": round(
                    float(mobile_probs[i, m_idx]), 4
                )
            },
            "EfficientNetB0": {
                "prediction": efficient_class,
                "confidence": round(
                    float(efficient_probs[i, e_idx]), 4
                )
            },
            "status": status,
            "final_prediction": final_prediction
        })

    return {
        "image": image_path.name,
        "total_regions": len(region_results),
        "regions": region_results
    }
