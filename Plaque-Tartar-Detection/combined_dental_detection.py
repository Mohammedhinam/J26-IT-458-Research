
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# Project paths
BASE_DIR = Path(__file__).resolve().parent

PLAQUE_MODEL_PATH = (
    BASE_DIR / "runs" / "segment"
    / "plaque_yolov8n_baseline" / "weights" / "best.pt"
)

TARTAR_MODEL_PATH = (
    BASE_DIR / "runs" / "detect" / "runs" / "detect"
    / "tartar_yolov8n_baseline" / "weights" / "best.pt"
)

TEST_IMAGE_PATH = (
    BASE_DIR / "Tarter_Only" / "test" / "images"
    / "calculus-1014-_jpg.rf.6031159f16b40047dbad227b9ec78180.jpg"
)

OUTPUT_DIR = BASE_DIR / "combined_detection_results"
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    print("Loading trained AI models...")

    plaque_model = YOLO(str(PLAQUE_MODEL_PATH))
    tartar_model = YOLO(str(TARTAR_MODEL_PATH))

    image = cv2.imread(str(TEST_IMAGE_PATH))

    if image is None:
        raise FileNotFoundError(f"Image not found: {TEST_IMAGE_PATH}")

    height, width = image.shape[:2]
    annotated = image.copy()

    # 1. Plaque segmentation
    print("Running plaque segmentation...")

    plaque_result = plaque_model.predict(
        source=image,
        conf=0.10,
        device=0,
        verbose=False
    )[0]

    plaque_mask = np.zeros((height, width), dtype=np.uint8)

    if plaque_result.masks is not None:
        for polygon in plaque_result.masks.xy:
            points = np.asarray(polygon, dtype=np.int32)

            if len(points) >= 3:
                cv2.fillPoly(plaque_mask, [points], 255)

    # Highlight predicted plaque regions in green
    overlay = annotated.copy()
    overlay[plaque_mask > 0] = (0, 255, 0)

    annotated = cv2.addWeighted(
        overlay, 0.35, annotated, 0.65, 0
    )

    # 2. Tartar object detection
    print("Running tartar detection...")

    tartar_result = tartar_model.predict(
        source=image,
        conf=0.25,
        device=0,
        verbose=False
    )[0]

    tartar_count = 0

    if tartar_result.boxes is not None:
        for box in tartar_result.boxes:
            x1, y1, x2, y2 = map(
                int, box.xyxy[0].cpu().numpy()
            )

            confidence = float(box.conf[0])
            tartar_count += 1

            # Red rectangle around detected tartar
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

    # 3. Detection summary
    plaque_pixels = int(np.count_nonzero(plaque_mask))
    plaque_detected = plaque_pixels > 0
    tartar_detected = tartar_count > 0

    print("\n===== AI DETECTION RESULTS =====")
    print(f"Plaque detected: {plaque_detected}")
    print(f"Predicted plaque pixels: {plaque_pixels}")
    print(f"Tartar detected: {tartar_detected}")
    print(f"Tartar bounding boxes: {tartar_count}")

    # Important: plaque pixels are not plaque coverage percentage.
    # A tooth mask is needed for the correct denominator.

    output_path = OUTPUT_DIR / "combined_detection.jpg"

    if not cv2.imwrite(str(output_path), annotated):
        raise RuntimeError("Failed to save annotated image.")

    print(f"\nAnnotated image saved to: {output_path}")


if __name__ == "__main__":
    main()
