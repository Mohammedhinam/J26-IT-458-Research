
from pathlib import Path
from PIL import Image

from app.services.gradcam import prepare_region_crop

# Use the existing dental test image
image_path = Path("test_image.jpg")

if not image_path.is_file():
    raise FileNotFoundError(
        "test_image.jpg was not found."
    )

# Prepare the first detected region
region_number = 1

image_array = prepare_region_crop(
    image_path,
    region_number
)

# Save the crop to inspect it
output_path = Path("region1_crop_test.png")

Image.fromarray(
    image_array.astype("uint8")
).save(output_path)

print("Selected region:", region_number)
print("Crop shape:", image_array.shape)
print("Crop saved:", output_path.resolve())
