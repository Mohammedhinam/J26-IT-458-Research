import json
import shutil
from pathlib import Path

# Folder containing this script
BASE = Path(__file__).resolve().parent

# Your three downloaded datasets
DATASETS = [
    BASE / "dental-plaque.v1i.coco-segmentation",
    BASE / "dental-plaque.v2i.coco-segmentation",
    BASE / "PLAK test.v2i.coco-segmentation",
]

# New output folder
OUTPUT = BASE / "Plaque_YOLO"

SPLITS = ["train", "valid", "test"]

image_count = 0
label_count = 0
polygon_count = 0

for split in SPLITS:

    image_output = OUTPUT / split / "images"
    label_output = OUTPUT / split / "labels"

    image_output.mkdir(parents=True, exist_ok=True)
    label_output.mkdir(parents=True, exist_ok=True)

    for dataset_number, dataset in enumerate(DATASETS, start=1):

        split_folder = dataset / split
        json_file = split_folder / "_annotations.coco.json"

        if not json_file.exists():
            print(f"Skipping: {json_file}")
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            coco = json.load(f)

        # Find dental-plaque category automatically
        plaque_ids = {
            category["id"]
            for category in coco.get("categories", [])
            if category.get("name", "").strip().lower()
            in {"dental-plaque", "dental plaque", "plaque"}
        }

        print(f"\nDataset {dataset_number} - {split}")
        print("Plaque category IDs:", plaque_ids)

        if not plaque_ids:
            print("No plaque category found. Skipping.")
            continue

        images = {
            image["id"]: image
            for image in coco.get("images", [])
        }

        annotations_by_image = {}

        for annotation in coco.get("annotations", []):

            if annotation.get("category_id") not in plaque_ids:
                continue

            segmentation = annotation.get("segmentation", [])

            # We need polygon segmentation, not bounding boxes
            if not isinstance(segmentation, list):
                continue

            for polygon in segmentation:

                if not isinstance(polygon, list) or len(polygon) < 6:
                    continue

                annotations_by_image.setdefault(
                    annotation["image_id"], []
                ).append(polygon)

        for image_id, polygons in annotations_by_image.items():

            if image_id not in images:
                continue

            info = images[image_id]

            filename = info["file_name"]
            width = info["width"]
            height = info["height"]

            source_image = split_folder / filename

            if not source_image.exists():
                print("Missing image:", source_image)
                continue

            # Prefix prevents duplicate filenames between datasets
            new_stem = f"d{dataset_number}_{Path(filename).stem}"
            new_image_name = new_stem + Path(filename).suffix

            shutil.copy2(
                source_image,
                image_output / new_image_name
            )

            label_file = label_output / f"{new_stem}.txt"

            with open(label_file, "w", encoding="utf-8") as f:

                for polygon in polygons:

                    normalized = []

                    for i in range(0, len(polygon), 2):

                        x = polygon[i] / width
                        y = polygon[i + 1] / height

                        # Keep coordinates inside 0-1
                        x = min(max(x, 0.0), 1.0)
                        y = min(max(y, 0.0), 1.0)

                        normalized.extend([x, y])

                    # YOLO segmentation:
                    # class_id x1 y1 x2 y2 ...
                    line = "0 " + " ".join(
                        f"{value:.6f}" for value in normalized
                    )

                    f.write(line + "\n")
                    polygon_count += 1

            image_count += 1
            label_count += 1


# Create data.yaml
yaml_file = OUTPUT / "data.yaml"

with open(yaml_file, "w", encoding="utf-8") as f:
    f.write(
        "path: .\n"
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n\n"
        "nc: 1\n"
        "names:\n"
        "  0: plaque\n"
    )


print("\n================================")
print("CONVERSION COMPLETE")
print("================================")
print("Images copied:", image_count)
print("Label files:", label_count)
print("Plaque polygons:", polygon_count)
print("Output:", OUTPUT)