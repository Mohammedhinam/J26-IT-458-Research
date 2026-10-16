
import csv
import json
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# Paths relative to your datasets folder
DATASET = Path("Plaque_Segmentation/dental-plaque.v1i.coco-segmentation")
TEST_DIR = DATASET / "test"
ANNOTATIONS = TEST_DIR / "_annotations.coco.json"
MODEL_PATH = Path("runs/segment/plaque_yolov8n_baseline/weights/best.pt")
OUTPUT = Path("ai_plaque_coverage_results.csv")

# Original COCO category IDs
TOOTH_CLASS = 2
PLAQUE_CLASSES = {0, 1}

# Confidence selected during previous validation tuning
CONFIDENCE = 0.10


def create_mask(annotations, height, width):
    mask = np.zeros((height, width), dtype=np.uint8)

    for annotation in annotations:
        segmentation = annotation.get("segmentation", [])

        if not isinstance(segmentation, list):
            continue

        for polygon in segmentation:
            points = np.asarray(polygon, dtype=np.float32)

            if points.size < 6 or points.size % 2 != 0:
                continue

            points = np.rint(
                points.reshape(-1, 2)
            ).astype(np.int32)

            cv2.fillPoly(mask, [points], 1)

    return mask


def main():
    model = YOLO(str(MODEL_PATH))

    with open(ANNOTATIONS, "r", encoding="utf-8") as file:
        coco = json.load(file)

    annotations_by_image = {}

    for annotation in coco["annotations"]:
        annotations_by_image.setdefault(
            annotation["image_id"], []
        ).append(annotation)

    results = []

    for image_info in coco["images"]:
        image_path = TEST_DIR / image_info["file_name"]

        if not image_path.exists():
            print(f"Missing image: {image_path}")
            continue

        image = cv2.imread(str(image_path))

        if image is None:
            print(f"Could not read image: {image_path}")
            continue

        height, width = image.shape[:2]

        annotations = annotations_by_image.get(
            image_info["id"], []
        )

        tooth_annotations = [
            annotation
            for annotation in annotations
            if annotation["category_id"] == TOOTH_CLASS
        ]

        plaque_annotations = [
            annotation
            for annotation in annotations
            if annotation["category_id"] in PLAQUE_CLASSES
        ]

        if not tooth_annotations:
            print(f"No tooth annotation: {image_path.name}")
            continue

        tooth_mask = create_mask(
            tooth_annotations, height, width
        )

        tooth_pixels = int(np.count_nonzero(tooth_mask))

        if tooth_pixels == 0:
            print(f"Empty tooth mask: {image_path.name}")
            continue

        # Predict plaque segmentation using trained YOLO
        prediction = model.predict(
            source=str(image_path),
            conf=CONFIDENCE,
            imgsz=640,
            verbose=False
        )[0]

        predicted_plaque_mask = np.zeros(
            (height, width), dtype=np.uint8
        )

        if prediction.masks is not None:
            # Convert predicted polygons to original image coordinates
            for polygon in prediction.masks.xy:
                points = np.asarray(
                    polygon, dtype=np.float32
                )

                if len(points) < 3:
                    continue

                points = np.rint(points).astype(np.int32)

                cv2.fillPoly(
                    predicted_plaque_mask,
                    [points],
                    1
                )

        # Keep only predicted plaque pixels inside tooth mask
        predicted_plaque_on_teeth = cv2.bitwise_and(
            predicted_plaque_mask,
            tooth_mask
        )

        predicted_plaque_pixels = int(
            np.count_nonzero(predicted_plaque_on_teeth)
        )

        ai_coverage = (
            predicted_plaque_pixels / tooth_pixels
        ) * 100

        # Annotation-based reference for comparison
        reference_plaque_mask = create_mask(
            plaque_annotations, height, width
        )

        reference_plaque_on_teeth = cv2.bitwise_and(
            reference_plaque_mask,
            tooth_mask
        )

        reference_plaque_pixels = int(
            np.count_nonzero(reference_plaque_on_teeth)
        )

        reference_coverage = (
            reference_plaque_pixels / tooth_pixels
        ) * 100

        results.append({
            "image": image_path.name,
            "tooth_pixels": tooth_pixels,
            "ai_plaque_pixels": predicted_plaque_pixels,
            "ai_plaque_coverage_percent": round(ai_coverage, 2),
            "annotation_plaque_coverage_percent": round(
                reference_coverage, 2
            ),
            "absolute_difference_percent_points": round(
                abs(ai_coverage - reference_coverage), 2
            )
        })

        print(
            f"{image_path.name}: "
            f"AI={ai_coverage:.2f}% | "
            f"Annotation={reference_coverage:.2f}%"
        )

    fieldnames = [
        "image",
        "tooth_pixels",
        "ai_plaque_pixels",
        "ai_plaque_coverage_percent",
        "annotation_plaque_coverage_percent",
        "absolute_difference_percent_points"
    ]

    with open(
        OUTPUT, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(results)

    print("\n--------------------------------")
    print(f"Images processed: {len(results)}")
    print(f"Results saved to: {OUTPUT}")
    print("--------------------------------")


if __name__ == "__main__":
    main()
