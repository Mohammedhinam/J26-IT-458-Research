"""Build a leakage-aware, conservatively labelled research data manifest.
Run from Malocclusion-Detection project root.
Never changes data/raw and does not train a model.
"""
import csv
import json
import hashlib
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.cwd()
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
OUT = PROCESSED / "clean_dataset"
GROUPS = PROCESSED / "duplicate_groups.json"
CONFLICT_GROUP = "group_12"
SPLITS = ("train", "valid", "test")
DATASETS = ("crooked_detection", "crowded_teeth", "smile_spacing")
TARGETS = ("crowding", "spacing", "open_bite", "crossbite")


def key(path):
    return str(path.resolve()).casefold()


def get_data():
    samples = {}
    errors = []
    for source in DATASETS:
        for split in SPLITS:
            folder = RAW / source / split
            if not folder.is_dir():
                errors.append(f"Missing folder: {folder}")
                continue
            if source == "crooked_detection":
                csv_path = folder / "_classes.csv"
                if not csv_path.is_file():
                    errors.append(f"Missing CSV: {csv_path}")
                    continue
                with csv_path.open(encoding="utf-8-sig", newline="") as f:
                    rows = list(csv.DictReader(f))
                for row in rows:
                    path = folder / row["filename"]
                    if not path.is_file():
                        errors.append(f"Missing image: {path}")
                        continue
                    k = key(path)
                    positive = set()
                    if row.get("crossbite") == "1":
                        positive.add("crossbite")
                    if row.get("openbite") == "1":
                        positive.add("open_bite")
                    samples[k] = {"path": path, "source": source, "original_split": split,
                                  "positives": positive,
                                  "source_labels": ";".join(c for c in row if c != "filename" and row[c] == "1")}
            else:
                annotation_file = folder / "_annotations.coco.json"
                if not annotation_file.is_file():
                    errors.append(f"Missing COCO JSON: {annotation_file}")
                    continue
                coco = json.loads(annotation_file.read_text(encoding="utf-8"))
                categories = {c["id"]: c["name"] for c in coco["categories"]}
                labels_by_id = defaultdict(set)
                for ann in coco["annotations"]:
                    labels_by_id[ann["image_id"]].add(categories[ann["category_id"]])
                for image in coco["images"]:
                    path = folder / image["file_name"]
                    if not path.is_file():
                        errors.append(f"Missing image: {path}")
                        continue
                    original_labels = labels_by_id[image["id"]]
                    positive = set()
                    if source == "crowded_teeth":
                        if any("crowded" in s.lower() for s in original_labels):
                            positive.add("crowding")
                    else:
                        if "crowding" in original_labels:
                            positive.add("crowding")
                        if "spacing" in original_labels:
                            positive.add("spacing")
                    samples[key(path)] = {"path": path, "source": source,
                                          "original_split": split, "positives": positive,
                                          "source_labels": ";".join(sorted(original_labels))}
    return samples, errors


def main():
    if not GROUPS.is_file():
        raise SystemExit(f"Missing review groups: {GROUPS}")
    info = json.loads(GROUPS.read_text(encoding="utf-8"))
    if info.get("confirmed_pairs") != 15 or len(info.get("uncertain_pairs", [])) != 1:
        raise SystemExit("Review counts changed. Recheck duplicate_groups.json before continuing.")
    samples, errors = get_data()
    if errors:
        raise SystemExit("Input errors; no output written:\n" + "\n".join(errors[:20]))
    if len(samples) != 1501:
        raise SystemExit(f"Expected 1,501 source images; found {len(samples)}. Check inputs before running.")

    # Build components for manually confirmed duplicates only.
    parent = {k: k for k in samples}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        x, y = find(a), find(b)
        if x != y:
            parent[y] = x

    reviewed = info["duplicate_groups"]
    for group in reviewed:
        ids = [key(ROOT / p) for p in group]
        if any(i not in samples for i in ids):
            raise SystemExit(f"Duplicate group path does not match input files: {group}")
        for item in ids[1:]:
            union(ids[0], item)

    clusters = defaultdict(list)
    for item in samples:
        clusters[find(item)].append(item)

    # Quarantine both ends of uncertain pair; never split a potentially same-patient pair.
    uncertain_keys = set()
    for row in info["uncertain_pairs"]:
        for field in ("image_a", "image_b"):
            k = key(ROOT / row[field])
            if k not in samples:
                raise SystemExit(f"Uncertain pair path not found: {row[field]}")
            uncertain_keys.add(k)
    blocked_roots = {find(k) for k in uncertain_keys}

    # The image-path pair in Group 12 has conflicting partial annotations.
    # Group IDs correspond to order in duplicate_groups.json, not Excel CSV sort order.
    conflict_index = 12
    if len(reviewed) < conflict_index:
        raise SystemExit("Conflict group_12 not found")
    conflict_keys = {key(ROOT / p) for p in reviewed[conflict_index - 1]}
    conflict_roots = {find(k) for k in conflict_keys}
    blocked_roots |= conflict_roots

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "dataset_manifest.csv"
    exclusions = OUT / "excluded_review.csv"
    rows, excluded = [], []
    split_rank = {"train": 0, "valid": 1, "test": 2}
    moved_groups = 0

    for group in clusters.values():
        group = sorted(group)
        root = find(group[0])
        if root in blocked_roots:
            reason = "label_conflict_group_12" if root in conflict_roots else "uncertain_same_patient_or_view"
            for k in group:
                s = samples[k]
                excluded.append({"source_path": str(s["path"].relative_to(ROOT)),
                                 "dataset": s["source"], "original_split": s["original_split"],
                                 "reason": reason, "source_labels": s["source_labels"]})
            continue

        members = [samples[k] for k in group]
        # Prefer training for groups crossing boundaries, rather than contaminate validation/test.
        split = min((s["original_split"] for s in members), key=lambda x: split_rank[x])
        if any(s["original_split"] != split for s in members):
            moved_groups += 1
        positives = set().union(*(s["positives"] for s in members))
        # Every absent/unannotated target is UNKNOWN, never a verified negative.
        # Preserve one representative and a list of all original sources.
        representative = next((s for s in members if s["original_split"] == split), members[0])
        rel = str(representative["path"].relative_to(ROOT))
        unique_id = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16]
        name = f"{unique_id}{representative['path'].suffix.lower()}"
        dest = OUT / "images" / split / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(representative["path"], dest)
        record = {"image": str(dest.relative_to(ROOT)), "split": split,
                  "source": representative["source"], "original_path": rel,
                  "group_member_count": len(group),
                  "original_sources": " | ".join(str(s["path"].relative_to(ROOT)) for s in members),
                  "raw_source_labels": " | ".join(s["source_labels"] for s in members)}
        for target in TARGETS:
            record[target] = "1" if target in positives else "unknown"
        rows.append(record)

    with manifest.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "split", "source", "original_path", "group_member_count", "original_sources", "raw_source_labels", *TARGETS])
        writer.writeheader()
        writer.writerows(rows)
    with exclusions.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["source_path", "dataset", "original_split", "reason", "source_labels"])
        writer.writeheader()
        writer.writerows(excluded)

    counts = Counter(r["split"] for r in rows)
    positive_counts = Counter(t for r in rows for t in TARGETS if r[t] == "1")
    print("Source images:", len(samples))
    print("Curated images:", len(rows))
    print("Excluded source images for review:", len(excluded))
    print("Cross-split duplicate groups assigned together:", moved_groups)
    print("Curated split counts:", dict(counts))
    print("Known positive counts:", dict(positive_counts))
    print("Manifest:", manifest)
    print("Review exclusions:", exclusions)
    print("IMPORTANT: Unknown labels are NOT negative labels. NOT YET READY for four-class supervised training.")
    print("Original data/raw/ untouched.")


if __name__ == "__main__":
    main()
