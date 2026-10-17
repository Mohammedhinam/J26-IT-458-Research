
from pathlib import Path
import os
import base64

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = Path(os.environ.get("DENTAL_MODEL_DIR", str(BASE_DIR)))

PLAQUE_MODEL_PATH = (
    MODEL_DIR / "runs" / "segment"
    / "plaque_yolov8n_baseline" / "weights" / "best.pt"
)

TARTAR_MODEL_PATH = (
    MODEL_DIR / "runs" / "detect" / "runs" / "detect"
    / "tartar_yolov8n_baseline" / "weights" / "best.pt"
)

TOOTH_MODEL_PATH = (
    MODEL_DIR / "Tooth_Segmentation" / "runs"
    / "tooth_yolov8n_baseline" / "weights" / "best.pt"
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(
    title="Dental Plaque, Tartar and Tooth Analysis API",
    version="1.1.0",
    description="Research prototype for AI-based dental image analysis."
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

# Load models once at startup.
plaque_model = YOLO(str(PLAQUE_MODEL_PATH))
tartar_model = YOLO(str(TARTAR_MODEL_PATH))
tooth_model = YOLO(str(TOOTH_MODEL_PATH))


def create_union_mask(result, height, width):
    """Combine all predicted segmentation polygons into one binary mask."""
    mask = np.zeros((height, width), dtype=np.uint8)

    if result.masks is not None:
        for polygon in result.masks.xy:
            points = np.asarray(polygon, dtype=np.int32)

            if len(points) >= 3:
                cv2.fillPoly(mask, [points], 255)

    return mask


@app.get("/")
def home():
    return {
        "message": "Dental AI Analysis API is running",
        "status": "ready"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "plaque_model_loaded": True,
        "tartar_model_loaded": True,
        "tooth_model_loaded": True
    }


@app.post("/analyze")
async def analyze_dental_image(file: UploadFile = File(...)):
    if file.content_type not in {
        "image/jpeg", "image/png", "image/webp"
    }:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WEBP image."
        )

    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds the 10 MB upload limit."
        )

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=400,
            detail="The file is not a valid image."
        )

    height, width = image.shape[:2]

    if height * width > 20_000_000:
        raise HTTPException(
            status_code=413,
            detail="Image dimensions are too large."
        )

    # 1. PLAQUE SEGMENTATION
    plaque_result = plaque_model.predict(
        source=image,
        conf=0.10,
        device=0,
        verbose=False
    )[0]

    plaque_mask = create_union_mask(
        plaque_result, height, width
    )

    plaque_pixels = int(np.count_nonzero(plaque_mask))
    plaque_detected = plaque_pixels > 0

    # 2. TOOTH SEGMENTATION
    tooth_result = tooth_model.predict(
        source=image,
        conf=0.25,
        device=0,
        verbose=False
    )[0]

    tooth_mask = create_union_mask(
        tooth_result, height, width
    )

    tooth_pixels = int(np.count_nonzero(tooth_mask))
    tooth_detected = tooth_pixels > 0

    # 3. AUTOMATIC PLAQUE COVERAGE
    plaque_on_teeth_mask = cv2.bitwise_and(
        plaque_mask, tooth_mask
    )

    plaque_pixels_on_teeth = int(
        np.count_nonzero(plaque_on_teeth_mask)
    )

    if tooth_pixels > 0:
        plaque_coverage_percent = round(
            (plaque_pixels_on_teeth / tooth_pixels) * 100,
            2
        )
    else:
        plaque_coverage_percent = None

    # 4. ANNOTATED IMAGE
    annotated = image.copy()
    overlay = annotated.copy()

    # Light blue = predicted tooth regions
    overlay[tooth_mask > 0] = (255, 200, 0)

    # Green = predicted plaque regions
    overlay[plaque_mask > 0] = (0, 255, 0)

    annotated = cv2.addWeighted(
        overlay, 0.35, annotated, 0.65, 0
    )

    # 5. TARTAR OBJECT DETECTION
    tartar_result = tartar_model.predict(
        source=image,
        conf=0.25,
        device=0,
        verbose=False
    )[0]

    tartar_boxes = []

    if tartar_result.boxes is not None:
        for box in tartar_result.boxes:
            x1, y1, x2, y2 = map(
                int, box.xyxy[0].cpu().numpy()
            )

            confidence = float(box.conf[0])

            tartar_boxes.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": round(confidence, 4)
            })

            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                2
            )

            cv2.putText(
                annotated,
                f"Tartar {confidence:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )

    tartar_detected = len(tartar_boxes) > 0

    # 6. EDUCATIONAL FEEDBACK
    if plaque_detected and tartar_detected:
        feedback = (
            "Possible plaque and tartar were detected. "
            "Maintain regular brushing and interdental cleaning. "
            "A dental professional can assess and remove tartar."
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
            "No plaque or tartar was detected by these models. "
            "This does not confirm that the teeth are disease-free."
        )

    # 7. ENCODE ANNOTATED IMAGE
    success, encoded_image = cv2.imencode(
        ".jpg", annotated
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Could not encode the annotated image."
        )

    image_base64 = base64.b64encode(
        encoded_image.tobytes()
    ).decode("utf-8")

    # 8. API RESPONSE
    return {
        "plaque_detected": plaque_detected,
        "tartar_detected": tartar_detected,
        "tooth_detected": tooth_detected,
        "predicted_plaque_pixels": plaque_pixels,
        "predicted_tooth_pixels": tooth_pixels,
        "plaque_pixels_on_teeth": plaque_pixels_on_teeth,
        "plaque_coverage_percent": plaque_coverage_percent,
        "tartar_coverage_percent": None,
        "tartar_box_count": len(tartar_boxes),
        "tartar_boxes": tartar_boxes,
        "hygiene_score": None,
        "feedback": feedback,
        "quantification_status": (
            "Automatic tooth-normalized plaque coverage "
            "is available when teeth are detected. "
            "Tartar pixel coverage requires segmentation. "
            "A validated hygiene scoring method is still "
            "under development."
        ),
        "annotated_image": (
            "data:image/jpeg;base64," + image_base64
        ),
        "disclaimer": (
            "Experimental research prototype only. "
            "Predicted plaque coverage is not a clinically "
            "validated oral hygiene score or diagnosis."
        )
    }
