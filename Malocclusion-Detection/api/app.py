from pathlib import Path

import numpy as np
import tensorflow as tf
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
from api.severity import attach_severity_to_prediction
from api.gradcam_service import generate_explanation

ROOT = Path(__file__).resolve().parents[1]

IMAGE_SIZE = (224, 224)


MODEL_CONFIG = {
    "crossbite": {
        "path": ROOT / "models" / "crossbite_binary" / "best_model.keras",
        "threshold": 0.5,
    },

    "open_bite": {
        "path": ROOT / "models" / "openbite_binary" / "best_model.keras",
        "threshold": 0.5,
    },

    "crowding": {
        "path": ROOT / "models" / "crowding_binary_stratified" / "best_model.keras",
        "threshold": 0.5,
    },

    "spacing": {
        "path": ROOT / "models" / "spacing_binary_stratified" / "best_model.keras",
        "threshold": 0.5,
        "experimental": True,
    },
}


app = FastAPI(
    title="Malocclusion Screening API",
    description=(
        "Preliminary research API for image-based malocclusion screening. "
        "This system is not a clinical diagnostic tool."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


models = {}


def load_models():
    print("=" * 60)
    print("LOADING MODELS")
    print("=" * 60)

    for condition, config in MODEL_CONFIG.items():
        model_path = config["path"]

        if not model_path.is_file():
            print(f"[WARNING] Model missing: {condition}")
            print(model_path)
            continue

        try:
            model = tf.keras.models.load_model(
                model_path,
                compile=False
            )

            models[condition] = model

            print(
                f"[LOADED] {condition}: {model_path}"
            )

        except Exception as error:
            print(
                f"[ERROR] Could not load {condition}: {error}"
            )

    print("=" * 60)
    print(
        f"Loaded models: {list(models.keys())}"
    )
    print("=" * 60)


def preprocess_image(image_bytes):
    try:
        image = Image.open(
            io.BytesIO(image_bytes)
        )

        image = image.convert("RGB")

        image = image.resize(
            IMAGE_SIZE
        )

        array = np.asarray(
            image,
            dtype=np.float32
        )

        array = np.expand_dims(
            array,
            axis=0
        )

        return array

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file: {error}"
        )


def predict_condition(
    model,
    image_array,
    threshold
):
    probability = float(
        model.predict(
            image_array,
            verbose=0
        )
        .reshape(-1)[0]
    )

    detected = (
        probability >= threshold
    )

    return {
        "probability": round(
            probability,
            4
        ),

        "threshold": threshold,

        "detected": detected,
    }


@app.on_event("startup")
def startup_event():
    load_models()


@app.get("/")
def root():
    return {
        "message":
            "Malocclusion Screening API is running",

        "status":
            "ok",

        "loaded_models":
            list(models.keys()),

        "warning":
            (
                "Research prototype only. "
                "Not for clinical diagnosis."
            ),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",

        "loaded_model_count":
            len(models),

        "loaded_models":
            list(models.keys()),
    }


@app.post("/predict")
async def predict(
    file: UploadFile = File(...)
):
    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="Missing content type."
        )

    if not file.content_type.startswith(
        "image/"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed."
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    image_array = preprocess_image(
        image_bytes
    )

    results = {}

    for condition, config in MODEL_CONFIG.items():

        if condition not in models:
            results[condition] = {
                "status": "model_unavailable"
            }
            continue

        prediction = predict_condition(
            model=models[condition],
            image_array=image_array,
            threshold=config["threshold"],
        )

        prediction["status"] = "available"

        if config.get(
            "experimental",
            False
        ):
            prediction[
                "reliability"
            ] = "experimental_low_data"

        else:
            prediction[
                "reliability"
            ] = "preliminary"

        prediction = attach_severity_to_prediction(
            condition,
            prediction
        )

        results[
            condition
        ] = prediction

    return {
        "filename":
            file.filename,

        "results":
            results,

        "interpretation":
            (
                "An above-threshold result means the model "
                "probability exceeded the configured research "
                "screening threshold. This does not represent "
                "a clinical diagnosis."
            ),

        "disclaimer":
            (
                "This output is for preliminary "
                "research screening only and must "
                "not be interpreted as a dental diagnosis."
            ),
    }



@app.post("/explain")
async def explain(
    condition: str = Form(...),
    file: UploadFile = File(...)
):
    allowed_conditions = {
        "crossbite",
        "open_bite",
        "crowding",
    }

    if condition not in allowed_conditions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported condition for Grad-CAM. "
                "Choose crossbite, open_bite or crowding."
            )
        )

    if condition not in models:
        raise HTTPException(
            status_code=503,
            detail="Requested model is not loaded."
        )

    if file.content_type not in {
        "image/jpeg",
        "image/png",
    }:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG and PNG images are supported."
        )

    max_size = 5 * 1024 * 1024

    image_bytes = await file.read(max_size + 1)

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    if len(image_bytes) > max_size:
        raise HTTPException(
            status_code=413,
            detail="Maximum image size is 5 MB."
        )

    try:
        explanation = generate_explanation(
            model=models[condition],
            condition=condition,
            image_bytes=image_bytes
        )

        return explanation

    except (ValueError, OSError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print(
            f"[GRADCAM ERROR] {condition}: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Grad-CAM generation failed. "
                "Check the backend logs."
            )
        )
