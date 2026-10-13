"""Read-only archive/caption precheck. Never extracts images or trains models."""

import argparse
import csv
import io
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


EXPECTED = {"Training": 732, "Validation": 182, "Test": 182}
CAPTIONS = {"Training": "Train", "Validation": "Validation", "Test": "Test"}
NUMBER = r"([+-]?\d+(?:\.\d+)?)"
GRADE_PATTERNS = (
    re.compile(r"\bgingivitis\s+(?:(?:grade|level)\s+)?" + NUMBER, re.I),
    re.compile(r"\b(?:level|grade)\s+" + NUMBER + r"\s+gingivitis\b", re.I),
)


def safe_member(name):
    """Reject unsafe names before any future extraction is considered."""
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and "\\" not in name and ":" not in name


def caption_grades(text):
    """Read explicit grades, never tooth numbers or counts before 'level of'."""
    matches = []
    for pattern in GRADE_PATTERNS:
        matches.extend(match.group(1) for match in pattern.finditer(text or ""))
    if not matches:
        return set(), "no_explicit_grade"
    values = [float(value) for value in matches]
    if any(not value.is_integer() or not 0 <= value <= 4 for value in values):
        return set(), "invalid_grade"
    return {int(value) for value in values}, None


def audit_inventory(members, captions):
    """Cross-check archive names and all caption variants without image payloads."""
    anomalies = []

    def flag(kind, split, name):
        anomalies.append({"kind": kind, "split": split, "file": name})

    counts = Counter(members)
    for name, count in sorted(counts.items()):
        if not safe_member(name):
            flag("unsafe_archive_path", "archive", name)
        if count > 1:
            flag("duplicate_archive_path", "archive", name)
    images = {}
    basename_splits = defaultdict(set)
    basename_paths = defaultdict(set)
    for split in EXPECTED:
        prefix = f"Dataset/{split}/Images/"
        images[split] = [name for name in members if name.startswith(prefix)
                         and PurePosixPath(name).suffix.lower() in {".jpg", ".jpeg", ".png"}]
        for name in images[split]:
            basename_splits[PurePosixPath(name).name].add(split)
            basename_paths[(split, PurePosixPath(name).name)].add(name)
            if len(PurePosixPath(name).parts) != 4:
                flag("unexpected_image_path", split, name)
    for (split, name), paths in sorted(basename_paths.items()):
        if len(paths) > 1:
            flag("duplicate_filename_within_split", split, name)
    for name in members:
        path = PurePosixPath(name)
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"} and not any(
                name.startswith(f"Dataset/{split}/Images/") for split in EXPECTED):
            flag("unexpected_image_path", "archive", name)
    for name, splits in sorted(basename_splits.items()):
        if len(splits) > 1:
            flag("cross_split_filename", ",".join(sorted(splits)), name)
    # Case-only collisions matter on common macOS filesystems.
    folded = defaultdict(set)
    for name in members:
        folded[name.casefold()].add(name)
    for names in folded.values():
        if len(names) > 1:
            flag("case_insensitive_path_collision", "archive", "; ".join(sorted(names)))

    manifest = []
    summaries = []
    for split, expected in EXPECTED.items():
        image_names = {PurePosixPath(name).name for name in images[split]}
        groups = defaultdict(list)
        for row in captions[split]:
            name = row.get("FileName", "") or ""
            if not name or PurePosixPath(name).name != name or not safe_member(name):
                flag("invalid_caption_filename", split, name)
                continue
            groups[name].append(row)
            if name not in image_names:
                flag("caption_image_missing", split, name)
        distribution = Counter()
        mixed = 0
        maximum_conflicts = 0
        review = 0
        for name in sorted(image_names):
            rows = groups.get(name, [])
            issues = []
            if not rows:
                issues.append("image_caption_missing")
            elif len(rows) != 3 or Counter(row.get("#") for row in rows) != Counter(["1", "2", "3"]):
                issues.append("caption_variant_ids")
            grade_sets = []
            for row in rows:
                grades, issue = caption_grades(row.get("BS1"))
                if issue:
                    issues.append(issue)
                grade_sets.append(grades)
            if grade_sets and any(grades != grade_sets[0] for grades in grade_sets[1:]):
                issues.append("conflicting_caption_grades")
            if len({max(grades) for grades in grade_sets if grades}) > 1:
                maximum_conflicts += 1
            # A label remains provisional until mapping and leakage checks are done.
            label = None
            if issues:
                review += 1
                for issue in sorted(set(issues)):
                    flag(issue, split, name)
            else:
                label = max(grade_sets[0])
                distribution[label] += 1
            if any(len(grades) > 1 for grades in grade_sets):
                mixed += 1
            manifest.append({"split": split, "image_path": f"Dataset/{split}/Images/{name}",
                             "mgi_max": label, "status": "needs_review" if issues else "provisional",
                             "issues": sorted(set(issues))})
        summaries.append({"split": split, "expected": expected, "image_entries": len(images[split]),
                          "unique_image_names": len(image_names), "caption_rows": len(captions[split]),
                          "caption_names": len(groups), "needs_review": review,
                          "mixed_explicit_grades": mixed,
                          "conflicting_maxima": maximum_conflicts,
                          "grades": [distribution[grade] for grade in range(5)]})
    return {"summaries": summaries, "manifest": manifest, "anomalies": anomalies}


def read_archive(archive):
    """Use installed bsdtar; CSVs stream to memory and no file is extracted."""
    def read(arguments):
        return subprocess.run(["/usr/bin/bsdtar", *arguments, str(archive)],
                              check=True, capture_output=True, timeout=60).stdout

    members = read(["-tf"]).decode("utf-8").splitlines()
    # Reject unsafe or duplicated member paths rather than reading ambiguous entries.
    if any(not safe_member(name) for name in members) or len(set(members)) != len(members):
        raise ValueError("Unsafe or duplicated archive paths; stop before reading captions.")
    captions = {}
    for split, stem in CAPTIONS.items():
        member = f"Dataset/{split}/{stem}_captions.csv"
        raw = subprocess.run(["/usr/bin/bsdtar", "-xOf", str(archive), member],
                             check=True, capture_output=True, timeout=60).stdout
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not {"FileName", "#", "BS1"}.issubset(reader.fieldnames or []):
            raise ValueError(f"Required caption columns missing in {member}")
        captions[split] = list(reader)
    return members, captions


def render_report(result, archive):
    """Keep entry-count evidence separate from unperformed content checks."""
    lines = ["# Gingivitis archive and caption precheck", "", "Date: 2026-10-13", "",
             f"Source archive: `{archive}`", "",
             "**Not training-ready.** No image extraction, decoding, hashing or model training performed.", "",
             "Counts below are archive entries, not verified unique/decodable image content.", "",
             "| Split | Expected | Image entries | Check | Unique names | Caption rows | Caption names |",
             "|---|---:|---:|---|---:|---:|---:|"]
    total = 0
    for row in result["summaries"]:
        total += row["image_entries"]
        check = "MATCH" if row["image_entries"] == row["expected"] else "MISMATCH"
        lines.append(f"| {row['split']} | {row['expected']} | {row['image_entries']} | {check} | "
                     f"{row['unique_image_names']} | {row['caption_rows']} | {row['caption_names']} |")
    lines += [f"| Total | 1096 | {total} | {'MATCH' if total == 1096 else 'MISMATCH'} | — | — | — |", "",
              "## Provisional caption-derived maximum grades", "",
              "Only explicit numeric grades are recognised. All three variant IDs must be present and explicit grade sets agree. "
              "Missing/invalid/conflicting captions stay needs_review. Non-inflamed-only text is not automatically grade 0. "
              "No caption-derived label is frozen before manual/mapping review.", "",
              "| Split | MGI 0 | MGI 1 | MGI 2 | MGI 3 | MGI 4 | Needs review | Conflicting maxima | Mixed explicit grades |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in result["summaries"]:
        values = " | ".join(str(value) for value in row["grades"])
        lines.append(f"| {row['split']} | {values} | {row['needs_review']} | {row['conflicting_maxima']} | {row['mixed_explicit_grades']} |")
    kinds = Counter(item["kind"] for item in result["anomalies"])
    lines += ["", "## Archive-name / caption anomalies", "", "| Check | Findings |", "|---|---:|"]
    for kind in ["unsafe_archive_path", "duplicate_archive_path", "duplicate_filename_within_split",
                 "unexpected_image_path", "cross_split_filename",
                 "case_insensitive_path_collision", "invalid_caption_filename", "caption_image_missing",
                 "image_caption_missing", "caption_variant_ids", "no_explicit_grade", "invalid_grade",
                 "conflicting_caption_grades"]:
        lines.append(f"| {kind} | {kinds[kind]} |")
    if result["anomalies"]:
        lines += ["", "### Records needing review", "", "| Split | File | Issue |", "|---|---|---|"]
        for item in result["anomalies"]:
            lines.append(f"| {item['split']} | {item['file']} | {item['kind']} |")
    lines += ["", "## Remaining checks / blockers", "",
              "- Exact duplicate image content (SHA-256): NOT CHECKED.",
              "- Re-encoded/augmented near duplicates: NOT CHECKED; hashes alone cannot rule these out.",
              "- Image decoding, dimensions and visual quality: NOT CHECKED.",
              "- Participant overlap: UNKNOWN; filename uniqueness does not establish independence.",
              "- YOLO classes 0/1 ROI and 2–6 → MGI 0–4: published mapping, NOT locally verified.",
              "- Zero/non-inflamed wording and caption/image consistency: manual review pending.",
              "- Archive backup identity, unpacked space, links and safe staging: pending extraction preparation.",
              "", "Keep published splits provisional. Any leakage or label-policy change requires owner review; "
              "do not drop/reassign records silently. This audit does not access NHANES payloads.", ""]
    if sum(row["grades"][0] for row in result["summaries"]) == 0:
        lines += ["No provisional image-level MGI 0 labels were found in this run; five-class training feasibility is unresolved.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("docs/vision_dataset_audit.md"))
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(f"Preserve existing report: {args.report}")
    members, captions = read_archive(args.archive)
    result = audit_inventory(members, captions)
    report = render_report(result, args.archive)
    # Exclusive creation prevents overwriting someone else's evidence.
    with args.report.open("x", encoding="utf-8") as handle:
        handle.write(report)
    print(report)


if __name__ == "__main__":
    main()
