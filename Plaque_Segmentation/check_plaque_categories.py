import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

DATASETS = [
    BASE / "dental-plaque.v1i.coco-segmentation",
    BASE / "dental-plaque.v2i.coco-segmentation",
    BASE / "PLAK test.v2i.coco-segmentation",
]

for number, dataset in enumerate(DATASETS, start=1):

    print("\n" + "=" * 50)
    print(f"DATASET {number}: {dataset.name}")
    print("=" * 50)

    for split in ["train", "valid", "test"]:

        json_file = dataset / split / "_annotations.coco.json"

        if not json_file.exists():
            print(f"{split}: annotation file NOT FOUND")
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            coco = json.load(f)

        print(f"\n{split.upper()} categories:")

        for category in coco.get("categories", []):
            print(f"ID {category['id']} = {category['name']}")