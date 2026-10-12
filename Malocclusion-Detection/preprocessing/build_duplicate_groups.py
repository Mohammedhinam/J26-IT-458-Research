
import csv
import json
from pathlib import Path
from collections import defaultdict

report = Path("data/processed/duplicate_review_detailed.csv")
output = Path("data/processed/duplicate_groups.json")

parent = {}

def find(x):
    parent.setdefault(x, x)
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra

confirmed = 0
uncertain = []

with report.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        status = row["review_status"].strip().lower()
        a = row["image_a"]
        b = row["image_b"]

        if status == "confirmed":
            union(a, b)
            confirmed += 1
        elif status == "uncertain":
            uncertain.append({
                "pair_id": row["pair_id"],
                "image_a": a,
                "image_b": b
            })

groups = defaultdict(list)

for image in parent:
    groups[find(image)].append(image)

result = {
    "confirmed_pairs": confirmed,
    "duplicate_groups": [
        sorted(images)
        for images in groups.values()
        if len(images) > 1
    ],
    "uncertain_pairs": uncertain
}

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    json.dumps(result, indent=2),
    encoding="utf-8"
)

print("Confirmed pairs:", confirmed)
print("Duplicate groups:", len(result["duplicate_groups"]))
print("Uncertain pairs:", len(uncertain))
print("Saved:", output)
print("Original dataset unchanged.")
