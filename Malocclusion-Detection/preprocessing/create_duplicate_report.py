
import csv
from pathlib import Path
from PIL import Image
import imagehash

base = Path("data/raw")
datasets = ["crooked_detection", "crowded_teeth", "smile_spacing"]
splits = ["train", "valid", "test"]

images = []

for dataset in datasets:
    for split in splits:
        folder = base / dataset / split

        if not folder.exists():
            continue

        for path in sorted(folder.rglob("*")):
            if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue

            with Image.open(path) as img:
                phash = imagehash.phash(img.convert("RGB"))

            images.append((dataset, split, path, phash))

matches = []

for i in range(len(images)):
    for j in range(i + 1, len(images)):
        a, b = images[i], images[j]

        if (a[0], a[1]) == (b[0], b[1]):
            continue

        distance = a[3] - b[3]

        if distance <= 5:
            matches.append((distance, a, b))

matches.sort(key=lambda x: (x[0], str(x[1][2]), str(x[2][2])))

output = Path("data/processed/duplicate_review_detailed.csv")
output.parent.mkdir(parents=True, exist_ok=True)

with open(output, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "pair_id",
        "image_a",
        "image_b",
        "dataset_a",
        "split_a",
        "dataset_b",
        "split_b",
        "phash_distance",
        "review_status"
    ])

    for index, (distance, a, b) in enumerate(matches, start=1):
        writer.writerow([
            f"pair_{index:02d}",
            str(a[2]),
            str(b[2]),
            a[0],
            a[1],
            b[0],
            b[1],
            distance,
            "pending"
        ])

print("Images checked:", len(images))
print("Potential duplicate pairs:", len(matches))
print("Detailed report:", output)
print("Original images were not modified.")
