from pathlib import Path
import shutil

# Current datasets folder
BASE = Path(__file__).resolve().parent

# New calculus-only dataset
OUTPUT = BASE / "Tarter_Only"

SPLITS = ["train", "valid", "test"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

for split in SPLITS:

    source_images = BASE / split / "images"
    source_labels = BASE / split / "labels"

    output_images = OUTPUT / split / "images"
    output_labels = OUTPUT / split / "labels"

    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    images_copied = 0
    calculus_boxes = 0
    skipped = 0

    print(f"\nProcessing {split}...")

    for label_file in source_labels.glob("*.txt"):

        try:
            lines = label_file.read_text(
                encoding="utf-8"
            ).splitlines()
        except Exception as e:
            print(f"Could not read {label_file.name}: {e}")
            continue

        # Keep ONLY class 0 = calculus
        calculus_lines = []

        for line in lines:
            parts = line.strip().split()

            if len(parts) == 5 and parts[0] == "0":
                calculus_lines.append(line.strip())

        # Skip images without calculus
        if not calculus_lines:
            skipped += 1
            continue

        # Find matching image
        image_file = None

        for extension in IMAGE_EXTENSIONS:
            candidate = source_images / f"{label_file.stem}{extension}"

            if candidate.exists():
                image_file = candidate
                break

        if image_file is None:
            print(f"WARNING: No matching image for {label_file.name}")
            continue

        # Copy image
        shutil.copy2(
            image_file,
            output_images / image_file.name
        )

        # Write new calculus-only label
        new_label = output_labels / label_file.name

        new_label.write_text(
            "\n".join(calculus_lines) + "\n",
            encoding="utf-8"
        )

        images_copied += 1
        calculus_boxes += len(calculus_lines)

    print(f"Images copied: {images_copied}")
    print(f"Calculus boxes: {calculus_boxes}")
    print(f"Non-calculus labels skipped: {skipped}")

# Create new YAML
yaml_content = """path: .
train: train/images
val: valid/images
test: test/images

nc: 1
names:
  0: calculus
"""

(OUTPUT / "data.yaml").write_text(
    yaml_content,
    encoding="utf-8"
)

print("\n======================================")
print("CALCULUS-ONLY DATASET CREATED")
print("======================================")
print(f"Saved to: {OUTPUT}")