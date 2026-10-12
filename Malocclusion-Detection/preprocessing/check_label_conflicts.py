
import json
import csv
from pathlib import Path
from collections import defaultdict

base = Path("data/raw")
groups_file = Path("data/processed/duplicate_groups.json")
output = Path("data/processed/duplicate_label_review.csv")

data = json.loads(groups_file.read_text(encoding="utf-8"))

label_map = defaultdict(set)

# Read COCO labels for object detection datasets
for dataset in ["crowded_teeth", "smile_spacing"]:
    for split in ["train", "valid", "test"]:
        folder = base / dataset / split
        annotation_file = folder / "_annotations.coco.json"

        if not annotation_file.exists():
            continue

        coco = json.loads(annotation_file.read_text(encoding="utf-8"))

        categories = {
            c["id"]: c["name"]
            for c in coco["categories"]
        }

        filenames = {
            img["id"]: img["file_name"]
            for img in coco["images"]
        }

        for ann in coco["annotations"]:
            image_path = folder / filenames[ann["image_id"]]
            category = categories[ann["category_id"]]

            label_map[str(image_path)].add(category)

# Read multi-label CSV classification dataset
for split in ["train", "valid", "test"]:
    folder = base / "crooked_detection" / split
    csv_file = folder / "_classes.csv"

    if not csv_file.exists():
        continue

    with csv_file.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            image_path = folder / row["filename"]

            for label, value in row.items():
                if label == "filename":
                    continue

                if value == "1":
                    label_map[str(image_path)].add(label)

output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "group_id",
        "image_path",
        "labels",
        "review_required"
    ])

    for index, group in enumerate(data["duplicate_groups"], 1):
        group_labels = [
            label_map.get(path, set())
            for path in group
        ]

        needs_review = len({
            frozenset(labels)
            for labels in group_labels
        }) > 1

        for path, labels in zip(group, group_labels):
            writer.writerow([
                f"group_{index:02d}",
                path,
                "; ".join(sorted(labels)),
                "yes" if needs_review else "no"
            ])

print("Duplicate groups checked:", len(data["duplicate_groups"]))
print("Label review report:", output)
print("Original images unchanged.")
