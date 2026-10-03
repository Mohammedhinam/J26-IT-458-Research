import json
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent

DATASETS = [
    BASE / "dental-plaque.v1i.coco-segmentation",
    BASE / "dental-plaque.v2i.coco-segmentation",
    BASE / "PLAK test.v2i.coco-segmentation",
]

OUTPUT = BASE / "Plaque_YOLO_Clean"

SOURCE_SPLITS = ["train", "valid", "test"]
PLAQUE_NAMES = {"plaque", "dental-plaque", "dental plaque"}

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def normalize_source_name(name):
    name = Path(name).name.lower()

    # Remove Roboflow-generated .rf.HASH portion
    name = re.sub(
        r"\.rf\.[a-z0-9_-]+(?=\.[^.]+$)",
        "",
        name
    )

    return Path(name).stem


# Store every usable image together with its plaque polygons
records = []

for dataset_number, dataset in enumerate(DATASETS, start=1):

    for old_split in SOURCE_SPLITS:

        folder = dataset / old_split
        json_file = folder / "_annotations.coco.json"

        if not json_file.exists():
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            coco = json.load(f)

        plaque_ids = {
            c["id"]
            for c in coco.get("categories", [])
            if c.get("name", "").strip().lower() in PLAQUE_NAMES
        }

        images = {
            image["id"]: image
            for image in coco.get("images", [])
        }

        polygons_by_image = defaultdict(list)

        for annotation in coco.get("annotations", []):

            if annotation.get("category_id") not in plaque_ids:
                continue

            segmentation = annotation.get("segmentation", [])

            if not isinstance(segmentation, list):
                continue

            for polygon in segmentation:

                if isinstance(polygon, list) and len(polygon) >= 6:
                    polygons_by_image[annotation["image_id"]].append(
                        polygon
                    )

        for image_id, polygons in polygons_by_image.items():

            if image_id not in images:
                continue

            info = images[image_id]

            filename = info["file_name"]
            image_path = folder / filename

            if not image_path.exists():
                continue

            extra = info.get("extra", {})

            source_name = (
                extra.get("name")
                if isinstance(extra, dict)
                else None
            )

            if not source_name:
                source_name = filename

            source_group = normalize_source_name(source_name)

            records.append({
                "dataset": dataset_number,
                "old_split": old_split,
                "image_path": image_path,
                "filename": filename,
                "width": info["width"],
                "height": info["height"],
                "polygons": polygons,
                "source_group": source_group,
            })


# Group all versions of the same source together
groups = defaultdict(list)

for record in records:
    groups[record["source_group"]].append(record)

group_names = list(groups.keys())
random.shuffle(group_names)

total_groups = len(group_names)

train_end = int(total_groups * 0.70)
valid_end = train_end + int(total_groups * 0.20)

train_groups = set(group_names[:train_end])
valid_groups = set(group_names[train_end:valid_end])
test_groups = set(group_names[valid_end:])


def final_split(group_name):

    if group_name in train_groups:
        return "train"

    if group_name in valid_groups:
        return "valid"

    return "test"


# Remove old generated clean folder if it exists
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)


for split in ["train", "valid", "test"]:
    (OUTPUT / split / "images").mkdir(parents=True, exist_ok=True)
    (OUTPUT / split / "labels").mkdir(parents=True, exist_ok=True)


image_counts = defaultdict(int)
polygon_counts = defaultdict(int)


for index, record in enumerate(records, start=1):

    split = final_split(record["source_group"])

    source_image = record["image_path"]

    # Unique filename prevents collisions across datasets/exports
    new_stem = (
        f"d{record['dataset']}_"
        f"{index:04d}_"
        f"{Path(record['filename']).stem}"
    )

    new_image = new_stem + source_image.suffix.lower()

    shutil.copy2(
        source_image,
        OUTPUT / split / "images" / new_image
    )

    label_path = OUTPUT / split / "labels" / f"{new_stem}.txt"

    with open(label_path, "w", encoding="utf-8") as f:

        for polygon in record["polygons"]:

            normalized = []

            for i in range(0, len(polygon), 2):

                x = polygon[i] / record["width"]
                y = polygon[i + 1] / record["height"]

                x = min(max(x, 0.0), 1.0)
                y = min(max(y, 0.0), 1.0)

                normalized.extend([x, y])

            f.write(
                "0 "
                + " ".join(f"{value:.6f}" for value in normalized)
                + "\n"
            )

            polygon_counts[split] += 1

    image_counts[split] += 1


# Create YOLO data.yaml
yaml_path = OUTPUT / "data.yaml"

with open(yaml_path, "w", encoding="utf-8") as f:

    f.write(
        f"path: {OUTPUT.as_posix()}\n"
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n\n"
        "nc: 1\n"
        "names:\n"
        "  0: plaque\n"
    )


print("\n========================================")
print("CLEAN PLAQUE DATASET CREATED")
print("========================================")

print("Source groups:", total_groups)
print()

for split in ["train", "valid", "test"]:

    print(
        f"{split.upper():5} | "
        f"Images: {image_counts[split]:3} | "
        f"Polygons: {polygon_counts[split]}"
    )

print()
print("Output:", OUTPUT)
print("Random seed:", RANDOM_SEED)

print("\nIMPORTANT:")
print("The split was performed by source group.")
print("Variants of the same source were kept in one split.")
print("========================================")