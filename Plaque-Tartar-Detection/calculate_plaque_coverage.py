
import csv
import json
from pathlib import Path

import cv2
import numpy as np

DATASET = Path("Plaque_Segmentation/dental-plaque.v1i.coco-segmentation")
SPLIT = "train"
ANNOTATIONS = DATASET / SPLIT / "_annotations.coco.json"

PLAQUE_CLASSES = {0, 1}
TOOTH_CLASS = 2

OUTPUT = Path("plaque_coverage_results.csv")


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

            points = np.rint(points.reshape(-1, 2)).astype(np.int32)
            cv2.fillPoly(mask, [points], 1)

    return mask


def main():
    with open(ANNOTATIONS, "r", encoding="utf-8") as file:
        coco = json.load(file)

    annotations_by_image = {}

    for annotation in coco["annotations"]:
        annotations_by_image.setdefault(
            annotation["image_id"], []
        ).append(annotation)

    results = []

    for image in coco["images"]:
        image_id = image["id"]
        height = image["height"]
        width = image["width"]

        annotations = annotations_by_image.get(image_id, [])

        tooth_annotations = [
            ann for ann in annotations
            if ann["category_id"] == TOOTH_CLASS
        ]

        plaque_annotations = [
            ann for ann in annotations
            if ann["category_id"] in PLAQUE_CLASSES
        ]

        if not tooth_annotations:
            continue

        tooth_mask = create_mask(tooth_annotations, height, width)
        plaque_mask = create_mask(plaque_annotations, height, width)

        tooth_pixels = int(np.count_nonzero(tooth_mask))

        if tooth_pixels == 0:
            continue

        plaque_on_teeth = cv2.bitwise_and(plaque_mask, tooth_mask)
        plaque_pixels = int(np.count_nonzero(plaque_on_teeth))

        coverage = (plaque_pixels / tooth_pixels) * 100

        results.append({
            "image": image["file_name"],
            "tooth_pixels": tooth_pixels,
            "plaque_pixels": plaque_pixels,
            "plaque_coverage_percent": round(coverage, 2)
        })

        print(f"{image['file_name']} : {coverage:.2f}%")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "image",
                "tooth_pixels",
                "plaque_pixels",
                "plaque_coverage_percent"
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    print("\n--------------------------------")
    print(f"Images processed: {len(results)}")
    print(f"Results saved to: {OUTPUT}")
    print("--------------------------------")


if __name__ == "__main__":
    main()
