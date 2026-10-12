
from pathlib import Path
from collections import defaultdict
import hashlib

base = Path("data/raw")
datasets = ["crooked_detection", "crowded_teeth", "smile_spacing"]
splits = ["train", "valid", "test"]

hashes = defaultdict(list)
total = 0

for dataset in datasets:
    for split in splits:
        folder = base / dataset / split

        if not folder.exists():
            continue

        for file in folder.rglob("*"):
            if not file.is_file():
                continue

            if file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            hashes[digest].append((dataset, split, str(file)))
            total += 1

duplicates = [paths for paths in hashes.values() if len(paths) > 1]

leakage = [
    paths for paths in duplicates
    if len({(dataset, split) for dataset, split, _ in paths}) > 1
]

print("Total images checked:", total)
print("Unique image hashes:", len(hashes))
print("Duplicate groups:", len(duplicates))
print("Cross-dataset/split duplicate groups:", len(leakage))

for group in leakage[:10]:
    print("\nDuplicate found:")
    for dataset, split, path in group:
        print(f"  [{dataset}/{split}] {path}")
