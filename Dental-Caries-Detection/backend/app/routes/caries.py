from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import tempfile
import shutil

from app.services.caries_prediction import predict_dental_caries
from app.services.gradcam import generate_region_gradcams

router = APIRouter(prefix="/api/caries", tags=["Dental Caries"])


@router.post("/predict")
def predict_caries(file: UploadFile = File(...)):
    """Upload a dental image and return AI predictions."""

    allowed_types = ["image/jpeg", "image/png"]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG and PNG images are supported."
        )

    suffix = ".png" if file.content_type == "image/png" else ".jpg"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:
            shutil.copyfileobj(file.file, temp)
            temp_path = Path(temp.name)

        # Verify uploaded image
        try:
            with Image.open(temp_path) as img:
                if img.format not in ("JPEG", "PNG"):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid image format. Upload JPG or PNG."
                    )

                img.verify()

        except (UnidentifiedImageError, OSError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid or corrupted image."
            )

        # Run existing AI prediction pipeline
        results = predict_dental_caries(temp_path)

        # Return original uploaded filename
        results["image"] = file.filename

        return results

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Image prediction failed."
        )

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

        file.file.close()



@router.post("/gradcam")
def predict_gradcam(
    file: UploadFile = File(...),
    region: int = Form(...)
):
    """Generate Grad-CAM for a selected dental region."""

    if region < 1:
        raise HTTPException(
            status_code=400,
            detail="Region number must be 1 or greater."
        )

    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=400,
            detail="Only JPG and PNG images are supported."
        )

    suffix = ".png" if file.content_type == "image/png" else ".jpg"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:
            shutil.copyfileobj(file.file, temp)
            temp_path = Path(temp.name)

        # Validate the actual image content
        try:
            with Image.open(temp_path) as img:
                if img.format not in ("JPEG", "PNG"):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid image format."
                    )
                img.verify()

        except (UnidentifiedImageError, OSError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Invalid or corrupted image."
            )

        # Generate both Grad-CAM heatmaps
        results = generate_region_gradcams(
            temp_path,
            region
        )

        # Temporary response: test the Grad-CAM output
        
        return {
            "region": results["region"],
            "MobileNetV2": {
                "predicted_class": results["mobile_class"],
                "heatmap_shape": list(
                    results["mobile_heatmap"].shape
                ),
                "overlay": results["mobile_overlay"]
            },
            "EfficientNetB0": {
                "predicted_class": results["efficient_class"],
                "heatmap_shape": list(
                    results["efficient_heatmap"].shape
                ),
                "overlay": results["efficient_overlay"]
            }
        }


    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

   
    except Exception:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="Grad-CAM generation failed."
        )


    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

        file.file.close()

