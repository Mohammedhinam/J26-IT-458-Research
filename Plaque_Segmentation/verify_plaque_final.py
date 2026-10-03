from pathlib import Path

BASE = Path(__file__).resolve().parent
DATASET = BASE / "Plaque_YOLO_Clean"

SPLITS = ["train", "valid", "test"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

total_images = 0
total_labels = 0
total_polygons = 0

missing_labels = 0
missing_images = 0
empty_labels = 0
wrong_classes = 0
invalid_coordinates = 0
malformed_polygons = 0

print("\n========================================")
print("FINAL PLAQUE DATASET VERIFICATION")
print("========================================")

for split in SPLITS:

    image_dir = DATASET / split / "images"
    label_dir = DATASET / split / "labels"

    images = {
        p.stem: p
        for p in image_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    }

    labels = {
        p.stem: p
        for p in label_dir.glob("*.txt")
    }

    split_polygons = 0

    for stem in images:
        if stem not in labels:
            missing_labels += 1

    for stem in labels:
        if stem not in images:
            missing_images += 1

    for label_path in labels.values():

        text = label_path.read_text(
            encoding="utf-8"
        ).strip()

        if not text:
            empty_labels += 1
            continue

        for line in text.splitlines():

            parts = line.split()

            # class + minimum 3 (x,y) points
            if len(parts) < 7:
                malformed_polygons += 1
                continue

            # After class ID, coordinate count must be even
            if (len(parts) - 1) % 2 != 0:
                malformed_polygons += 1
                continue

            try:
                class_id = int(parts[0])
                coordinates = [
                    float(value)
                    for value in parts[1:]
                ]
            except ValueError:
                malformed_polygons += 1
                continue

            if class_id != 0:
                wrong_classes += 1

            if any(
                value < 0.0 or value > 1.0
                for value in coordinates
            ):
                invalid_coordinates += 1

            split_polygons += 1

    print(
        f"{split.upper():5} | "
        f"Images: {len(images):3} | "
        f"Labels: {len(labels):3} | "
        f"Polygons: {split_polygons}"
    )

    total_images += len(images)
    total_labels += len(labels)
    total_polygons += split_polygons


print("\n========================================")
print("TOTALS")
print("========================================")

print("Total images:", total_images)
print("Total labels:", total_labels)
print("Total polygons:", total_polygons)

print("\n========================================")
print("ERROR CHECK")
print("========================================")

print("Missing labels:", missing_labels)
print("Labels without images:", missing_images)
print("Empty labels:", empty_labels)
print("Wrong class IDs:", wrong_classes)
print("Invalid coordinates:", invalid_coordinates)
print("Malformed polygons:", malformed_polygons)

errors = (
    missing_labels
    + missing_images
    + empty_labels
    + wrong_classes
    + invalid_coordinates
    + malformed_polygons
)

print("\n========================================")

if errors == 0:
    print("DATASET PASSED - READY FOR YOLO SEGMENTATION")
else:
    print("DATASET HAS ERRORS - DO NOT TRAIN YET")

print("========================================")