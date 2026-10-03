from pathlib import Path

root = Path("Tarter_Only")

total_images = 0
total_labels = 0
total_boxes = 0
wrong_classes = []
empty_labels = []
missing_labels = []

for split in ["train", "valid", "test"]:

    image_dir = root / split / "images"
    label_dir = root / split / "labels"

    images = list(image_dir.glob("*.*"))
    labels = list(label_dir.glob("*.txt"))

    print(f"\nChecking {split}...")
    print("Images:", len(images))
    print("Labels:", len(labels))

    total_images += len(images)
    total_labels += len(labels)

    # Check labels
    for label in labels:
        lines = [
            line.strip()
            for line in label.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        if not lines:
            empty_labels.append(str(label))
            continue

        for line in lines:
            parts = line.split()

            if parts[0] != "0":
                wrong_classes.append((str(label), line))
            else:
                total_boxes += 1

    # Check every image has a matching label
    for image in images:
        label = label_dir / (image.stem + ".txt")

        if not label.exists():
            missing_labels.append(str(image))


print("\n==============================")
print("VERIFICATION COMPLETE")
print("==============================")

print("Total images:", total_images)
print("Total labels:", total_labels)
print("Total calculus boxes:", total_boxes)

print("Wrong class labels:", len(wrong_classes))
print("Empty labels:", len(empty_labels))
print("Images without labels:", len(missing_labels))

if (
    len(wrong_classes) == 0
    and len(empty_labels) == 0
    and len(missing_labels) == 0
):
    print("\nDATASET OK - ONLY CALCULUS CLASS EXISTS")
else:
    print("\nDATASET HAS PROBLEMS")