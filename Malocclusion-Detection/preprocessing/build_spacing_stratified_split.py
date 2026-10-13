import csv
import json
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "raw" / "smile_spacing"

OUTPUT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "spacing_stratified"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "spacing_split_manifest.csv"
)

OUTPUT_JSON = (
    OUTPUT_DIR
    / "spacing_split_summary.json"
)

SEED = 42

TRAIN_RATIO = 0.70
VALID_RATIO = 0.15
TEST_RATIO = 0.15


def find_coco_json(folder):
    json_files = list(
        folder.glob("*.json")
    )

    if not json_files:
        raise FileNotFoundError(
            f"No COCO JSON found in {folder}"
        )

    for file in json_files:
        if "coco" in file.name.lower():
            return file

    return json_files[0]


def collect_images():
    records = []

    for split in [
        "train",
        "valid",
        "test"
    ]:
        folder = DATA_DIR / split

        annotation_file = (
            find_coco_json(folder)
        )

        coco = json.loads(
            annotation_file.read_text(
                encoding="utf-8"
            )
        )

        category_names = {
            category["id"]:
                category["name"]
                .strip()
                .lower()

            for category
            in coco["categories"]
        }

        image_info = {
            image["id"]: image
            for image in coco["images"]
        }

        image_labels = defaultdict(set)

        for annotation in coco[
            "annotations"
        ]:
            image_id = annotation[
                "image_id"
            ]

            category_id = annotation[
                "category_id"
            ]

            category_name = (
                category_names[
                    category_id
                ]
            )

            image_labels[
                image_id
            ].add(category_name)

        for image_id, info in (
            image_info.items()
        ):
            labels = image_labels[
                image_id
            ]

            has_spacing = (
                "spacing" in labels
            )

            has_normal = (
                "normal" in labels
            )

            has_crowding = (
                "crowding" in labels
            )

            has_overbite = (
                "overbite" in labels
            )

            # Keep only pure Spacing.
            if (
                has_spacing
                and not has_normal
                and not has_crowding
                and not has_overbite
            ):
                class_name = "spacing"

            # Keep only pure Normal.
            elif (
                has_normal
                and not has_spacing
                and not has_crowding
                and not has_overbite
            ):
                class_name = "normal"

            else:
                continue

            image_path = (
                folder
                / info["file_name"]
            )

            if not image_path.is_file():
                continue

            records.append({
                "image": str(
                    image_path.resolve()
                ),
                "filename":
                    info["file_name"],
                "label":
                    class_name,
                "original_split":
                    split,
            })

    return records


def split_class(records):
    items = records.copy()

    random.Random(
        SEED
    ).shuffle(items)

    total = len(items)

    train_count = int(
        total * TRAIN_RATIO
    )

    valid_count = int(
        total * VALID_RATIO
    )

    test_count = (
        total
        - train_count
        - valid_count
    )

    train = items[
        :train_count
    ]

    valid = items[
        train_count:
        train_count
        + valid_count
    ]

    test = items[
        train_count
        + valid_count:
    ]

    if (
        len(train) == 0
        or len(valid) == 0
        or len(test) == 0
    ):
        raise RuntimeError(
            "A split became empty. "
            "Spacing dataset is too small."
        )

    return {
        "train": train,
        "valid": valid,
        "test": test,
    }


records = collect_images()

by_class = {
    "spacing": [],
    "normal": [],
}

for record in records:
    by_class[
        record["label"]
    ].append(record)


print("=" * 60)
print(
    "SPACING STRATIFIED SPLIT"
)
print("=" * 60)

print(
    "Total usable images:",
    len(records)
)

print(
    "Spacing:",
    len(
        by_class["spacing"]
    )
)

print(
    "Normal:",
    len(
        by_class["normal"]
    )
)


if len(
    by_class["spacing"]
) < 10:
    print(
        "\nWARNING: Very few Spacing-positive images."
    )

if len(
    by_class["spacing"]
) < 5:
    raise RuntimeError(
        "Too few Spacing images for a meaningful split."
    )


split_records = {
    "train": [],
    "valid": [],
    "test": [],
}

for class_name in [
    "spacing",
    "normal"
]:
    class_split = split_class(
        by_class[class_name]
    )

    for split_name in [
        "train",
        "valid",
        "test"
    ]:
        split_records[
            split_name
        ].extend(
            class_split[
                split_name
            ]
        )


for split_name in split_records:
    random.Random(
        SEED
    ).shuffle(
        split_records[
            split_name
        ]
    )


summary = {
    "seed": SEED,
    "ratios": {
        "train": TRAIN_RATIO,
        "valid": VALID_RATIO,
        "test": TEST_RATIO,
    },
    "total_usable": len(records),
    "class_totals": {
        "spacing":
            len(
                by_class[
                    "spacing"
                ]
            ),
        "normal":
            len(
                by_class[
                    "normal"
                ]
            ),
    },
    "splits": {},
}


print("\n===== NEW SPLITS =====")

for split_name in [
    "train",
    "valid",
    "test"
]:
    subset = split_records[
        split_name
    ]

    spacing_count = sum(
        1
        for item in subset
        if item["label"]
        == "spacing"
    )

    normal_count = sum(
        1
        for item in subset
        if item["label"]
        == "normal"
    )

    print(
        f"\n{split_name.upper()}"
    )

    print(
        "Images:",
        len(subset)
    )

    print(
        "Spacing:",
        spacing_count
    )

    print(
        "Normal:",
        normal_count
    )

    summary["splits"][
        split_name
    ] = {
        "images": len(subset),
        "spacing":
            spacing_count,
        "normal":
            normal_count,
    }


with OUTPUT_CSV.open(
    "w",
    encoding="utf-8",
    newline=""
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "image",
            "filename",
            "label",
            "split",
            "original_split",
        ]
    )

    writer.writeheader()

    for split_name in [
        "train",
        "valid",
        "test"
    ]:
        for item in (
            split_records[
                split_name
            ]
        ):
            writer.writerow({
                "image":
                    item["image"],
                "filename":
                    item["filename"],
                "label":
                    item["label"],
                "split":
                    split_name,
                "original_split":
                    item[
                        "original_split"
                    ],
            })


OUTPUT_JSON.write_text(
    json.dumps(
        summary,
        indent=2
    ),
    encoding="utf-8"
)


print("\n===== OUTPUT =====")

print(
    "Manifest:",
    OUTPUT_CSV
)

print(
    "Summary:",
    OUTPUT_JSON
)

print(
    "Original dataset unchanged."
)