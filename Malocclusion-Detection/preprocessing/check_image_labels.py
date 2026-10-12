
import json
from pathlib import Path
from collections import defaultdict

base = Path("data/raw")
datasets = ["crowded_teeth", "smile_spacing"]
splits = ["train", "valid", "test"]

for dataset in datasets:
    print(f"\n===== DATASET: {dataset} =====")

    for split in splits:
        path = base / dataset / split / "_annotations.coco.json"

        if not path.exists():
            print(f"{split}: Annotation file not found")
            continue

        with open(path, encoding="utf-8") as file:
            data = json.load(file)

        categories = {
            category["id"]: category["name"]
            for category in data["categories"]
        }

        image_labels = defaultdict(set)

        for annotation in data["annotations"]:
            category_name = categories[annotation["category_id"]]
            image_labels[category_name].add(annotation["image_id"])

        counts = {
            name: len(image_ids)
            for name, image_ids in image_labels.items()
        }

        print(f"\nSplit: {split}")
        print(f"Images: {len(data['images'])}")
        print(f"Annotations: {len(data['annotations'])}")
        print(f"Image counts by label: {counts}")
