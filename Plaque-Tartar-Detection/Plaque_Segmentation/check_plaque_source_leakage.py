import json
import hashlib
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent

DATASETS = [
    BASE / "dental-plaque.v1i.coco-segmentation",
    BASE / "dental-plaque.v2i.coco-segmentation",
    BASE / "PLAK test.v2i.coco-segmentation",
]

SPLITS = ["train", "valid", "test"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

by_hash = defaultdict(list)
by_source = defaultdict(list)
total_images = 0


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_source_name(name):
    name = Path(name).name.lower()

    # Remove common Roboflow export suffix
    name = re.sub(
        r"\.rf\.[a-z0-9_-]+(?=\.[^.]+$)",
        "",
        name
    )

    return Path(name).stem


for dataset_number, dataset in enumerate(DATASETS, start=1):

    for split in SPLITS:

        folder = dataset / split
        json_file = folder / "_annotations.coco.json"

        if not folder.exists():
            continue

        source_by_filename = {}

        if json_file.exists():

            with open(json_file, "r", encoding="utf-8") as f:
                coco = json.load(f)

            for image in coco.get("images", []):

                filename = image.get("file_name")

                if not filename:
                    continue

                extra = image.get("extra", {})

                source_name = (
                    extra.get("name")
                    if isinstance(extra, dict)
                    else None
                )

                if not source_name:
                    source_name = filename

                source_by_filename[filename] = normalize_source_name(
                    source_name
                )

        for image_path in folder.iterdir():

            if (
                not image_path.is_file()
                or image_path.suffix.lower() not in IMAGE_EXTENSIONS
            ):
                continue

            total_images += 1

            tag = (
                f"Dataset {dataset_number} / "
                f"{split} / {image_path.name}"
            )

            file_hash = sha256(image_path)
            by_hash[file_hash].append(tag)

            source_name = source_by_filename.get(
                image_path.name,
                normalize_source_name(image_path.name)
            )

            by_source[source_name].append(tag)


exact_duplicate_groups = [
    group for group in by_hash.values()
    if len(group) > 1
]

same_source_groups = [
    group for group in by_source.values()
    if len(group) > 1
]


def get_split(tag):
    return tag.split(" / ")[1]


exact_cross_split = [
    group for group in exact_duplicate_groups
    if len({get_split(item) for item in group}) > 1
]

source_cross_split = [
    group for group in same_source_groups
    if len({get_split(item) for item in group}) > 1
]


print("\n========================================")
print("PLAQUE SAME-SOURCE / LEAKAGE CHECK")
print("========================================")

print("Total image files:", total_images)
print("Exact duplicate groups:", len(exact_duplicate_groups))
print("Exact cross-split leakage:", len(exact_cross_split))
print("Same-source groups:", len(same_source_groups))
print("Same-source cross-split leakage:", len(source_cross_split))

print("\n========================================")
print("SAME-SOURCE CROSS-SPLIT EXAMPLES")
print("========================================")

if not source_cross_split:
    print("No same-source cross-split leakage detected.")
else:
    for number, group in enumerate(source_cross_split[:20], start=1):
        print(f"\nGroup {number}")

        for item in group:
            print(" ", item)

print("\n========================================")
print("CHECK COMPLETE")
print("========================================")