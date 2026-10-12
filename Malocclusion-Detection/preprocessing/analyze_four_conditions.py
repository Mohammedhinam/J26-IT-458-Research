
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT / "data" / "processed" / "clean_dataset"
    / "dataset_manifest.csv"
)

OUTPUT_DIR = ROOT / "evaluation" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONDITIONS = [
    "crowding",
    "spacing",
    "open_bite",
    "crossbite",
]

SPLITS = ["train", "valid", "test"]

with MANIFEST.open(
    "r", encoding="utf-8-sig", newline=""
) as file:
    reader = csv.DictReader(file)

    required = {"source", "split", "image", *CONDITIONS}
    missing = required - set(reader.fieldnames or [])

    if missing:
        raise ValueError(f"Missing CSV columns: {missing}")

    rows = list(reader)

print("=" * 60)
print("FOUR-CONDITION DATASET READINESS ANALYSIS")
print("=" * 60)
print("Total curated images:", len(rows))

if len(rows) != len({r["image"] for r in rows}):
    raise ValueError("Duplicate image paths found in manifest")

for row in rows:
    if row["split"] not in SPLITS:
        raise ValueError(f"Unexpected split: {row['split']}")

    for condition in CONDITIONS:
        if row[condition] not in ("0", "1", "unknown"):
            raise ValueError(
                f"Invalid label {condition}={row[condition]}"
            )

sources = sorted(set(row["source"] for row in rows))

report = {
    "total_images": len(rows),
    "conditions": CONDITIONS,
    "sources": {},
    "overall": {},
    "splits": {},
    "warnings": [],
}

print("\n===== DATASET SOURCE DISTRIBUTION =====")

for source in sources:
    subset = [r for r in rows if r["source"] == source]

    report["sources"][source] = {
        "images": len(subset),
        "condition_counts": {},
    }

    print(f"\nSource: {source}")
    print("Images:", len(subset))

    for condition in CONDITIONS:
        counts = Counter(r[condition] for r in subset)

        values = {
            "positive": counts["1"],
            "negative": counts["0"],
            "unknown": counts["unknown"],
        }

        report["sources"][source][
            "condition_counts"
        ][condition] = values

        print(f"  {condition}: {values}")

print("\n===== OVERALL LABEL DISTRIBUTION =====")

for condition in CONDITIONS:
    counts = Counter(r[condition] for r in rows)

    values = {
        "positive": counts["1"],
        "negative": counts["0"],
        "unknown": counts["unknown"],
    }

    report["overall"][condition] = values

    print(f"{condition}: {values}")

    if values["negative"] == 0:
        report["warnings"].append(
            f"{condition}: no confirmed negative examples"
        )

    if values["positive"] < 50:
        report["warnings"].append(
            f"{condition}: fewer than 50 positive examples"
        )

print("\n===== TRAIN / VALID / TEST =====")

for split in SPLITS:
    subset = [r for r in rows if r["split"] == split]

    split_report = {
        "images": len(subset),
        "conditions": {},
    }

    print(f"\n{split.upper()}: {len(subset)} images")

    for condition in CONDITIONS:
        counts = Counter(r[condition] for r in subset)

        values = {
            "positive": counts["1"],
            "negative": counts["0"],
            "unknown": counts["unknown"],
        }

        split_report["conditions"][condition] = values
        print(f"  {condition}: {values}")

    report["splits"][split] = split_report

print("\n===== KNOWN LABEL CO-OCCURRENCE =====")

co_occurrence = defaultdict(int)

for row in rows:
    positives = [
        condition for condition in CONDITIONS
        if row[condition] == "1"
    ]

    for i in range(len(positives)):
        for j in range(i + 1, len(positives)):
            pair = tuple(sorted(
                [positives[i], positives[j]]
            ))
            co_occurrence[pair] += 1

for pair, count in sorted(co_occurrence.items()):
    print(f"{pair[0]} + {pair[1]}: {count}")

if not co_occurrence:
    print("No co-occurring known positives found.")

report["known_positive_co_occurrences"] = {
    " + ".join(pair): count
    for pair, count in co_occurrence.items()
}

print("\n===== RESEARCH READINESS =====")

for condition in CONDITIONS:
    values = report["overall"][condition]

    ready = (
        values["positive"] > 0
        and values["negative"] > 0
        and report["splits"]["test"]["conditions"][
            condition
        ]["positive"] >= 5
        and report["splits"]["test"]["conditions"][
            condition
        ]["negative"] >= 5
    )

    print(
        f"{condition}: "
        f"{'BASIC LABEL CHECK PASSED' if ready else 'NOT READY'}"
    )

    # Passing this check would not prove clinical
    # validity or an adequate sample size.
    report.setdefault("basic_label_readiness", {})[
        condition
    ] = ready

output = OUTPUT_DIR / "four_condition_analysis.json"

output.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n===== FINAL RESULT =====")
print("Report saved:", output)
print("Original dataset unchanged.")
print("Unknown labels were not converted to negatives.")
