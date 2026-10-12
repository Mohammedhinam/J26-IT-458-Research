
from pathlib import Path
from collections import defaultdict
from PIL import Image
import imagehash

base = Path("data/raw")
datasets = ["crooked_detection", "crowded_teeth", "smile_spacing"]
splits = ["train", "valid", "test"]

images = []
groups = defaultdict(list)

for dataset in datasets:
    for split in splits:
        folder = base / dataset / split

        if not folder.exists():
            continue

        for path in folder.rglob("*"):
            if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue

            try:
                with Image.open(path) as img:
                    h = imagehash.phash(img.convert("RGB"))

                images.append((dataset, split, path, h))
                groups[str(h)].append((dataset, split, path))

            except Exception as error:
                print("Skipped:", path, error)

print("Images checked:", len(images))

# Exact perceptual-hash matches, not exact file matches.
matches = [
    paths for paths in groups.values()
    if len(paths) > 1
]

print("Identical perceptual-hash groups:", len(matches))

# Check visually similar images across split boundaries.
near_matches = []

for i in range(len(images)):
    for j in range(i + 1, len(images)):
        a = images[i]
        b = images[j]

        if (a[0], a[1]) == (b[0], b[1]):
            continue

        distance = a[3] - b[3]

        if distance <= 5:
            near_matches.append((distance, a, b))

near_matches.sort(key=lambda item: item[0])

print("Potential cross-source/split near-duplicate pairs:",
      len(near_matches))

for distance, a, b in near_matches[:20]:
    print(f"\nDistance: {distance}")
    print("A:", a[2])
    print("B:", b[2])
