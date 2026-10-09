
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import tempfile
import shutil

from app.services.caries_prediction import predict_dental_caries

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

        results = predict_dental_caries(temp_path)

        # Return the original uploaded filename
        results["image"] = file.filename

        return results

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Image prediction failed."
        )

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        file.file.close()
