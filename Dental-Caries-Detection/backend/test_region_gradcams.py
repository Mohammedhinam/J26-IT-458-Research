
from pathlib import Path
import numpy as np

from app.services.gradcam import generate_region_gradcams

# Existing dental test image
image_path = Path("test_image.jpg")

if not image_path.is_file():
    raise FileNotFoundError("Test image not found.")

# Generate Grad-CAM for Region R1
results = generate_region_gradcams(
    image_path,
    region_number=1
)

print("Selected Region:", results["region"])

print(
    "MobileNetV2 Predicted Class:",
    results["mobile_class"]
)

print(
    "MobileNetV2 Heatmap Shape:",
    results["mobile_heatmap"].shape
)

print(
    "EfficientNet-B0 Predicted Class:",
    results["efficient_class"]
)

print(
    "EfficientNet-B0 Heatmap Shape:",
    results["efficient_heatmap"].shape
)

# Verify results
assert results["mobile_heatmap"].shape == (7, 7)
assert results["efficient_heatmap"].shape == (7, 7)

assert np.isfinite(results["mobile_heatmap"]).all()
assert np.isfinite(results["efficient_heatmap"]).all()

assert 0 <= results["mobile_class"] <= 2
assert 0 <= results["efficient_class"] <= 2

print("Both Grad-CAM models passed!")
