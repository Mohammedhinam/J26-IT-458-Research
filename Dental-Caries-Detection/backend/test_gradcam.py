
from pathlib import Path
import numpy as np
from PIL import Image
import time

from app.services.caries_prediction import load_models
from app.services.gradcam import generate_gradcam, resize_heatmap

# Existing test image in the backend folder
image_path = Path("test_image.jpg")

if not image_path.is_file():
    raise FileNotFoundError(
        "test_image.jpg was not found in the backend folder."
    )

# Load saved models
_, _, efficient_model = load_models()
# Prepare RGB image
# Prepare a YOLO-detected crop with the agreed 30% padding
yolo_model, _, _ = load_models()

with Image.open(image_path) as img:
    original = img.convert("RGB")
    width, height = original.size

detection = yolo_model.predict(
    source=str(image_path),
    conf=0.25,
    verbose=False
)[0]

boxes = detection.boxes.xyxy.cpu().numpy()

if len(boxes) == 0:
    raise RuntimeError("No suspected caries regions detected.")

# Use the first detected region (R1)
x1, y1, x2, y2 = boxes[0]

pad_x = (x2 - x1) * 0.30
pad_y = (y2 - y1) * 0.30

crop = original.crop((
    max(0, int(x1 - pad_x)),
    max(0, int(y1 - pad_y)),
    min(width, int(x2 + pad_x)),
    min(height, int(y2 + pad_y))
))

image_array = np.asarray(
    crop.resize((224, 224)),
    dtype=np.float32
)

crop.save("gradcam_region1_crop.png")
print("YOLO Region 1 crop saved.")

# Generate Grad-CAM
start_time = time.perf_counter()

heatmap, predicted_class = generate_gradcam(
    efficient_model,
    image_array,
    "efficientnet"
)

elapsed_time = time.perf_counter() - start_time

print(f"EfficientNet-B0 Grad-CAM time: {elapsed_time:.2f} seconds")

# Resize and save grayscale heatmap
resized = resize_heatmap(heatmap)

output_path = Path("gradcam_efficientnet_test.png")

Image.fromarray(
    np.uint8(np.clip(resized, 0, 1) * 255)
).save(output_path)

# Create a colored Grad-CAM overlay
import matplotlib.pyplot as plt

original_image = np.uint8(
    np.clip(image_array, 0, 255)
)

plt.figure(figsize=(6, 6))
plt.imshow(original_image)
plt.imshow(resized, cmap="jet", alpha=0.4, vmin=0, vmax=1)
plt.axis("off")
plt.tight_layout(pad=0)

plt.savefig(
    "gradcam_overlay_efficientnet.png",
    bbox_inches="tight",
    pad_inches=0
)

plt.close()

print("Grad-CAM overlay saved successfully.")

print("Predicted class index:", predicted_class)
print("Heatmap shape:", heatmap.shape)
print("Heatmap minimum:", float(heatmap.min()))
print("Heatmap maximum:", float(heatmap.max()))
print("Saved heatmap:", output_path.resolve())
