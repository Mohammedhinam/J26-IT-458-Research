from pathlib import Path

import numpy as np

from app.services.caries_prediction import load_models, predict_dental_caries


image_path = Path("test_image.jpg")
if not image_path.is_file():
    raise FileNotFoundError("Test image not found.")

# Run the existing prediction pipeline.
prediction = predict_dental_caries(image_path)

# Run YOLO again with the same settings as the Grad-CAM endpoint.
yolo_model, _, _ = load_models()
detection = yolo_model.predict(
    source=str(image_path),
    conf=0.25,
    verbose=False,
)[0]
second_boxes = detection.boxes.xyxy.cpu().numpy()

print("Prediction regions:", prediction["total_regions"])
print("Second detection regions:", len(second_boxes))
assert prediction["total_regions"] == len(second_boxes), "Region count mismatch!"
assert len(second_boxes) > 0, "No regions detected; cannot verify bounding boxes."

for region_number, (region, box) in enumerate(
    zip(prediction["regions"], second_boxes), start=1
):
    # The prediction response serializes YOLO coordinates as integers.
    prediction_box = np.asarray(region["bounding_box"])
    second_box = box.astype(int)
    matches = region["region"] == region_number and np.array_equal(
        prediction_box, second_box
    )
    print(
        f"R{region_number}: {'MATCH' if matches else 'MISMATCH'} "
        f"prediction={prediction_box.tolist()} "
        f"second_detection={second_box.tolist()}"
    )
    assert matches, f"Region R{region_number} bounding box mismatch!"

print("All region bounding boxes match!")
