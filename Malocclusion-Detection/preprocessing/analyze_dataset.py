import json
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parents[1]
ANNOTATION_DIR = BASE_DIR / "data" / "raw" / "omni_coco" / "annotations"


def analyze_split(split_name):
    annotation_file = ANNOTATION_DIR / f"instances_{split_name}.json"

    with open(annotation_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    categories = {
        category["id"]: category["name"]
        for category in data["categories"]
    }

    image_labels = {}

    for image in data["images"]:
        image_labels[image["id"]] = set()

    for annotation in data["annotations"]:
        image_id = annotation["image_id"]
        category_id = annotation["category_id"]

        if image_id in image_labels:
            image_labels[image_id].add(categories[category_id])

    label_counts = Counter()

    for labels in image_labels.values():
        for label in labels:
            label_counts[label] += 1

    print(f"\n===== {split_name.upper()} =====")
    print(f"Images: {len(data['images'])}")
    print(f"Annotations: {len(data['annotations'])}")

    print("\nImage count by category:")

    for category_id, category_name in categories.items():
        print(
            f"{category_name}: "
            f"{label_counts.get(category_name, 0)}"
        )


if __name__ == "__main__":
    for split in ["train", "val", "test"]:
        analyze_split(split)