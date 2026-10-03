from pathlib import Path
import hashlib

BASE = Path(__file__).resolve().parent

DATASETS = [
    BASE / "dental-plaque.v1i.coco-segmentation",
    BASE / "dental-plaque.v2i.coco-segmentation",
    BASE / "PLAK test.v2i.coco-segmentation",
]

SPLITS = ["train", "valid", "test"]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

hashes = {}
total_images = 0

for dataset in DATASETS:
    for split in SPLITS:
        folder = dataset / split

        if not folder.exists():
            continue

        for file in folder.iterdir():

            if file.suffix.lower() not in EXTENSIONS:
                continue

            total_images += 1

            with open(file, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            hashes.setdefault(file_hash, []).append(
                (dataset.name, split, file.name)
            )

duplicates = {
    h: files
    for h, files in hashes.items()
    if len(files) > 1
}

print("\n==============================")
print("PLAQUE DUPLICATE CHECK")
print("==============================")
print("Total image files:", total_images)
print("Unique images:", len(hashes))
print("Duplicate groups:", len(duplicates))

cross_split_groups = 0

for number, files in enumerate(duplicates.values(), start=1):

    splits = {item[1] for item in files}

    if len(splits) > 1:
        cross_split_groups += 1
        print(f"\nCross-split duplicate group {number}:")

        for dataset, split, filename in files:
            print(f"  {dataset} | {split} | {filename}")

print("\n==============================")
print("Cross-split duplicate groups:", cross_split_groups)
print("==============================")