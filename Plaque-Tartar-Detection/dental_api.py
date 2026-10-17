
from pathlib import Path
import os
import base64

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO


# ==========================================
# 1. MODEL CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = Path(
    os.environ.get("DENTAL_MODEL_DIR", str(BASE_DIR))
)

PLAQUE_MODEL_PATH = (
    MODEL_DIR / "runs" / "segment"
    / "plaque_yolov8n_baseline"
    / "weights" / "best.pt"
)

TARTAR_MODEL_PATH = (
    MODEL_DIR / "runs" / "detect"
    / "runs" / "detect"
    / "tartar_yolov8n_baseline"
    / "weights" / "best.pt"
)

TOOTH_MODEL_PATH = (
    MODEL_DIR / "Tooth_Segmentation"
    / "runs" / "tooth_yolov8n_baseline"
    / "weights" / "best.pt"
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


# ==========================================
# 2. FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Dental Plaque, Tartar and Tooth Analysis API",
    version="1.2.0",
    description=(
        "Experimental AI-based dental image analysis "
        "with plaque segmentation, tooth segmentation, "
        "tartar detection and research quantification."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ==========================================
# 3. LOAD TRAINED AI MODELS
# ==========================================

plaque_model = YOLO(str(PLAQUE_MODEL_PATH))
tartar_model = YOLO(str(TARTAR_MODEL_PATH))
tooth_model = YOLO(str(TOOTH_MODEL_PATH))


# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================

def create_union_mask(result, height, width):
    """
    Combine predicted segmentation polygons
    into a single binary mask.
    """
    mask = np.zeros(
        (height, width),
        dtype=np.uint8,
    )

    if result.masks is not None:
        for polygon in result.masks.xy:
            points = np.asarray(
                polygon,
                dtype=np.int32,
            )

            if len(points) >= 3:
                cv2.fillPoly(
                    mask,
                    [points],
                    255,
                )

    return mask


def calculate_percentage(numerator, denominator):
    """
    Calculate a percentage when the
    denominator is greater than zero.
    """
    if denominator <= 0:
        return None

    return round(
        (numerator / denominator) * 100,
        2,
    )


# ==========================================
# 5. API ROUTES
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Dental AI Analysis API is running",
        "status": "ready",
        "version": "1.2.0",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "plaque_model_loaded": plaque_model is not None,
        "tartar_model_loaded": tartar_model is not None,
        "tooth_model_loaded": tooth_model is not None,
    }


# ==========================================
# 6. ANALYZE DENTAL IMAGE
# ==========================================

@app.post("/analyze")
async def analyze_dental_image(
    file: UploadFile = File(...)
):

    # --------------------------------------
    # Validate uploaded image
    # --------------------------------------

    if file.content_type not in {
        "image/jpeg",
        "image/png",
        "image/webp",
    }:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WEBP image.",
        )

    image_bytes = await file.read(
        MAX_UPLOAD_BYTES + 1
    )

    await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty.",
        )

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds the 10 MB upload limit.",
        )

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="The file is not a valid image.",
        )

    height, width = image.shape[:2]

    if height * width > MAX_IMAGE_PIXELS:
        raise HTTPException(
            status_code=413,
            detail="Image dimensions are too large.",
        )

    # --------------------------------------
    # 1. Plaque segmentation
    # --------------------------------------

    plaque_result = plaque_model.predict(
        source=image,
        conf=0.10,
        device=0,
        verbose=False,
    )[0]

    plaque_mask = create_union_mask(
        plaque_result,
        height,
        width,
    )

    plaque_pixels = int(
        np.count_nonzero(plaque_mask)
    )

    plaque_detected = plaque_pixels > 0

    # --------------------------------------
    # 2. Tooth segmentation
    # --------------------------------------

    tooth_result = tooth_model.predict(
        source=image,
        conf=0.25,
        device=0,
        verbose=False,
    )[0]

    tooth_mask = create_union_mask(
        tooth_result,
        height,
        width,
    )

    tooth_pixels = int(
        np.count_nonzero(tooth_mask)
    )

    tooth_detected = tooth_pixels > 0

    # --------------------------------------
    # 3. Plaque coverage
    # --------------------------------------

    plaque_on_teeth_mask = cv2.bitwise_and(
        plaque_mask,
        tooth_mask,
    )

    plaque_pixels_on_teeth = int(
        np.count_nonzero(
            plaque_on_teeth_mask
        )
    )

    plaque_coverage_percent = (
        calculate_percentage(
            plaque_pixels_on_teeth,
            tooth_pixels,
        )
    )

    # --------------------------------------
    # 4. Tartar object detection
    # --------------------------------------

    tartar_result = tartar_model.predict(
        source=image,
        conf=0.25,
        device=0,
        verbose=False,
    )[0]

    tartar_boxes = []

    # Union of all tartar detection rectangles.
    # This is NOT a tartar segmentation mask.
    tartar_box_mask = np.zeros(
        (height, width),
        dtype=np.uint8,
    )

    if tartar_result.boxes is not None:
        for box in tartar_result.boxes:

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].cpu().numpy(),
            )

            confidence = float(
                box.conf[0]
            )

            # Keep coordinates within image bounds.
            x1 = max(0, min(x1, width))
            x2 = max(0, min(x2, width))
            y1 = max(0, min(y1, height))
            y2 = max(0, min(y2, height))

            if x2 <= x1 or y2 <= y1:
                continue

            tartar_boxes.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": round(
                    confidence,
                    4,
                ),
            })

            # NumPy slicing uses exclusive end
            # coordinates and avoids double counting.
            tartar_box_mask[
                y1:y2,
                x1:x2
            ] = 255

    tartar_detected = (
        len(tartar_boxes) > 0
    )

    # --------------------------------------
    # 5. Experimental tartar-box measurement
    # --------------------------------------

    tartar_boxes_on_teeth_mask = (
        cv2.bitwise_and(
            tartar_box_mask,
            tooth_mask,
        )
    )

    tartar_box_pixels = int(
        np.count_nonzero(
            tartar_box_mask
        )
    )

    tartar_box_pixels_on_teeth = int(
        np.count_nonzero(
            tartar_boxes_on_teeth_mask
        )
    )

    tartar_box_tooth_area_percent = (
        calculate_percentage(
            tartar_box_pixels_on_teeth,
            tooth_pixels,
        )
    )

    # IMPORTANT:
    # Bounding boxes include background and
    # potentially healthy tooth pixels.
    # Therefore this measurement must not
    # be called actual tartar coverage.

    tartar_coverage_percent = None

    # --------------------------------------
    # 6. Annotated dental image
    # --------------------------------------

    annotated = image.copy()
    overlay = annotated.copy()

    # Light blue: predicted teeth.
    overlay[tooth_mask > 0] = (
        255, 200, 0
    )

    # Green: predicted plaque.
    overlay[plaque_mask > 0] = (
        0, 255, 0
    )

    annotated = cv2.addWeighted(
        overlay,
        0.35,
        annotated,
        0.65,
        0,
    )

    # Red: tartar detection bounding boxes.
    for box in tartar_boxes:

        x1 = box["x1"]
        y1 = box["y1"]
        x2 = box["x2"]
        y2 = box["y2"]

        confidence = box["confidence"]

        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            2,
        )

        cv2.putText(
            annotated,
            f"Tartar {confidence:.2f}",
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2,
        )

    # --------------------------------------
    # 7. Educational feedback
    # --------------------------------------

    if plaque_detected and tartar_detected:
        feedback = (
            "Possible plaque and tartar were detected. "
            "Maintain regular brushing and interdental "
            "cleaning. A dental professional can assess "
            "and remove tartar."
        )

    elif plaque_detected:
        feedback = (
            "Possible plaque was detected. "
            "Brush thoroughly with fluoride toothpaste "
            "and clean between your teeth daily."
        )

    elif tartar_detected:
        feedback = (
            "Possible tartar was detected. "
            "Consider a professional dental examination "
            "and cleaning."
        )

    else:
        feedback = (
            "No plaque or tartar was detected by these "
            "models. This does not confirm that the "
            "teeth are disease-free."
        )

    # --------------------------------------
    # 8. Encode annotated image
    # --------------------------------------

    success, encoded_image = cv2.imencode(
        ".jpg",
        annotated,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Could not encode the annotated image.",
        )

    image_base64 = base64.b64encode(
        encoded_image.tobytes()
    ).decode("utf-8")

    # --------------------------------------
    # 9. Research quantification status
    # --------------------------------------

    if tooth_pixels == 0:
        quantification_status = (
            "No tooth region was detected. "
            "Tooth-normalized plaque and tartar-box "
            "measurements cannot be calculated. "
            "Try a clearer front-facing dental image."
        )
    else:
        quantification_status = (
            "Automatic plaque pixel coverage is "
            "available. Experimental tartar bounding-box "
            "area relative to predicted teeth is also "
            "available. Bounding-box area is not actual "
            "tartar coverage. A clinically validated "
            "oral hygiene score remains under development."
        )

    # --------------------------------------
    # 10. API response
    # --------------------------------------

    return {
        "plaque_detected": plaque_detected,
        "tartar_detected": tartar_detected,
        "tooth_detected": tooth_detected,

        "predicted_plaque_pixels": plaque_pixels,
        "predicted_tooth_pixels": tooth_pixels,
        "plaque_pixels_on_teeth": (
            plaque_pixels_on_teeth
        ),
        "plaque_coverage_percent": (
            plaque_coverage_percent
        ),

        # Experimental box-area proxy.
        "tartar_box_count": len(tartar_boxes),
        "tartar_boxes": tartar_boxes,
        "tartar_box_pixels": tartar_box_pixels,
        "tartar_box_pixels_on_teeth": (
            tartar_box_pixels_on_teeth
        ),
        "tartar_box_tooth_area_percent": (
            tartar_box_tooth_area_percent
        ),

        # Not available from a detection-only model.
        "tartar_coverage_percent": (
            tartar_coverage_percent
        ),

        # Do not invent a clinical score.
        "hygiene_score": None,

        "feedback": feedback,
        "quantification_status": (
            quantification_status
        ),

        "annotated_image": (
            "data:image/jpeg;base64,"
            + image_base64
        ),

        "disclaimer": (
            "Experimental research prototype only. "
            "Plaque coverage and tartar-box area are "
            "image-based AI measurements, not clinically "
            "validated dental indices or diagnoses. "
            "Tartar-box area must not be interpreted "
            "as true tartar surface coverage."
        ),
    }
