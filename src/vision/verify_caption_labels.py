"""Read-only caption QA. Candidates are source summaries, never approved labels."""

import argparse
from copy import deepcopy
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.vision.audit_gingivitis import CAPTIONS, EXPECTED, GRADE_PATTERNS, safe_member
from src.vision.extract_audit_gingivitis import yolo_evidence


UPPER = frozenset({13, 12, 11, 21, 22, 23})
LOWER = frozenset({43, 42, 41, 31, 32, 33})
SITES = UPPER | LOWER
SITE_TEXT = r"((?:[\d,\s/&-]|\band\b)*)"
NORMAL = re.compile(r"\b(?:non[- ]inflamed|not\s+inflamed|normal\s+gingiva)\b", re.I)
MGI = re.compile(r"\bMGI\s+(?:grade\s+)?([+-]?\d+(?:\.\d+)?)\b", re.I)
POLICIES = ("strict", "check_upper_partial")


def parse_caption(text):
    """Keep explicit tooth evidence; missing sites never acquire grade zero."""
    text = re.sub(r"\s+", " ", (text or "").replace("，", ",")).strip()
    terms = []
    for pattern in (*GRADE_PATTERNS, MGI):
        for match in pattern.finditer(text):
            value = float(match.group(1))
            grade = int(value) if value.is_integer() and 0 <= value <= 4 else None
            terms.append((match, grade, "explicit_grade"))
    terms.extend((m, 0, "explicit_non_inflamed") for m in NORMAL.finditer(text))
    terms.sort(key=lambda term: term[0].start())
    assignments = defaultdict(set)
    mentions, issues = [], set()
    for term_index, (match, grade, kind) in enumerate(terms):
        before, after = text[:match.start()], text[match.end():]
        # Support both "teeth 13 level of gingivitis 2" and "grade ... at position 13".
        left = re.search(r"\bteeth\s*" + SITE_TEXT + r"\s*(?:level(?:s)?\s+of|is|are)\s*$", before, re.I)
        right = re.match(r"\s*(?:tooth\s+)?(?:at\s+(?:positions?|teeth)|teeth)\s*" + SITE_TEXT, after, re.I)
        raw_sites = left.group(1) if left else right.group(1) if right else ""
        if left and right:
            left_sites = set(re.findall(r"\d+", left.group(1)))
            right_sites = set(re.findall(r"\d+", right.group(1)))
            if right_sites and left_sites != right_sites:
                issues.add("contradictory_position_clause")
        listed = [int(n) for n in re.findall(r"\d+", raw_sites)]
        supported = set(listed) & SITES
        if set(listed) - SITES:
            issues.add("unsupported_tooth_position")
        if len(listed) != len(set(listed)):
            issues.add("repeated_tooth_position")
        if re.search(r"\d\s*-\s*\d", raw_sites):
            issues.add("ambiguous_tooth_range")
        count = re.search(r"\b(\d+)\s+(?:level\s+of\s+)?$", before)
        if count and not left and int(count.group(1)) != len(listed):
            issues.add("declared_tooth_count_mismatch")
        # An explicit second jaw list can share the same source phrase, not a guessed grade.
        next_start = terms[term_index + 1][0].start() if term_index + 1 < len(terms) else len(text)
        clause_tail = text[match.end():next_start]
        second_jaw = re.search(r"\bin\s+(?:upper|lower)\s+jaw\s+and\s+teeth\s*" + SITE_TEXT
                               + r"\s+in\s+(?:upper|lower)\s+jaw", clause_tail, re.I)
        if second_jaw:
            extra = [int(n) for n in re.findall(r"\d+", second_jaw.group(1))]
            if not extra:
                issues.add("unsupported_grade_clause")
            if set(extra) - SITES:
                issues.add("unsupported_tooth_position")
            if set(extra) & set(listed) or len(extra) != len(set(extra)):
                issues.add("repeated_tooth_position")
            supported.update(set(extra) & SITES)
        if grade is None:
            issues.add("invalid_grade")
        elif supported:
            for site in supported:
                assignments[site].add(grade)
        mentions.append({"grade": grade, "kind": kind, "sites": sorted(supported),
                         "phrase": match.group(0), "end": match.end(), "start": match.start()})

    for index, mention in enumerate(mentions):
        if mention["sites"] or mention["grade"] is None:
            continue
        # Caption 3 sometimes repeats a grade before a fully specified nested clause.
        following = mentions[index + 1] if index + 1 < len(mentions) else None
        bridge = text[mention["end"]:following["start"]] if following else ""
        wrapper = bool(following and following["sites"] and following["grade"] == mention["grade"]
                       and re.fullmatch(r"\s*teeth\s+has\s+\d+\s+level\s+of\s*", bridge, re.I))
        mention["supported_repeated_wrapper"] = wrapper
        if not wrapper:
            issues.add("unsupported_grade_clause")
    if not terms:
        issues.add("no_supported_grade")
    if any(len(grades) > 1 for grades in assignments.values()):
        issues.add("within_caption_position_conflict")
    # Bare severity wording is not interpreted as a numerical or normal grade.
    for match in re.finditer(r"\bgingivitis\b", text, re.I):
        if not any(m.start() <= match.start() < m.end() for m, _, _ in terms):
            issues.add("unparsed_severity_phrase")
    if not assignments:
        issues.add("no_supported_positions")
    return {"site_grades": {str(site): sorted(grades) for site, grades in sorted(assignments.items())},
            "missing_sites": sorted(SITES - assignments.keys()), "issues": sorted(issues),
            "mentions": [{k: v for k, v in m.items() if k not in {"start", "end"}} for m in mentions]}


def compare_captions(rows):
    """Require three complete agreeing variants; omissions remain policy-pending."""
    issues = set()
    if len(rows) != 3 or Counter(str(r.get("#", "")) for r in rows) != Counter(["1", "2", "3"]):
        issues.add("caption_variant_structure")
    ordered = sorted(rows, key=lambda r: str(r.get("#", "")))
    parsed = [parse_caption(r.get("BS1", "")) for r in ordered]
    maps = [p["site_grades"] for p in parsed]
    for p in parsed:
        issues.update(p["issues"])
    conflicts = []
    for site in sorted(SITES):
        values = {g for m in maps for g in m.get(str(site), [])}
        if len(values) > 1:
            conflicts.append(site)
    if conflicts:
        issues.add("between_caption_position_conflict")
    if any(p["missing_sites"] for p in parsed):
        issues.add("incomplete_caption_positions")
    omission = (not issues - {"incomplete_caption_positions"} and len(maps) == 3
                and set(maps[0]) == set(maps[1]) == {str(s) for s in SITES}
                and maps[0] == maps[1] and set(maps[2]) == {str(s) for s in UPPER}
                and all(maps[2][s] == maps[0][s] for s in maps[2]))
    if omission:
        issues.add("lower_jaw_omission_policy_pending")
    candidate = None
    if not issues and len(maps) == 3 and maps[0] == maps[1] == maps[2]:
        candidate = max(grades[0] for grades in maps[0].values())
    return {"captions": parsed, "issues": sorted(issues), "conflicting_positions": conflicts,
            "lower_jaw_omission_pattern": bool(omission), "caption_candidate_maximum": candidate}


def compare_txt(caption_result, annotation_path):
    """Compare grade histograms only: TXT contains no explicit FDI tooth IDs."""
    codes, annotation_issues = yolo_evidence(annotation_path)
    observed = Counter({code - 2: count for code, count in codes.items() if 2 <= code <= 6})
    checks = []
    issues = set(annotation_issues)
    for index, parsed in enumerate(caption_result["captions"], 1):
        grades = parsed["site_grades"]
        complete = set(grades) == {str(s) for s in SITES} and all(len(v) == 1 for v in grades.values())
        if complete and not annotation_issues:
            expected = Counter(v[0] for v in grades.values())
            agrees = expected == observed
            if not agrees:
                issues.add("caption_txt_grade_histogram_disagreement")
            checks.append({"variant": index, "histogram_agrees": agrees,
                           "caption_histogram": [expected[g] for g in range(5)]})
    return {"issues": sorted(issues), "txt_histogram": [observed[g] for g in range(5)],
            "complete_caption_checks": checks,
            "tooth_identity_verified": False,
            "limitation": "Histogram agreement cannot verify per-tooth correspondence or clinical correctness."}


def jaw_histograms(annotation_path):
    """Assign only unambiguous jaw membership, never a tooth identity."""
    _, issues = yolo_evidence(annotation_path)
    issues = set(issues)
    if issues:
        return {"issues": sorted(issues), "histograms": {}, "tooth_identity_verified": False}
    boxes = [tuple(map(float, line.split())) for line in annotation_path.read_text(encoding="utf-8-sig").splitlines()
             if line.strip()]
    rois = {int(box[0]): box for box in boxes if box[0] in (0, 1)}
    if rois[0][2] >= rois[1][2]:
        issues.add("jaw_roi_order_ambiguous")
    histograms = {"upper": Counter(), "lower": Counter()}
    for code, x, y, _, _ in boxes:
        if code < 2:
            continue
        memberships = []
        for roi_code, (_, cx, cy, width, height) in rois.items():
            if cx - width / 2 <= x <= cx + width / 2 and cy - height / 2 <= y <= cy + height / 2:
                memberships.append(roi_code)
        if len(memberships) != 1:
            issues.add("tooth_jaw_membership_ambiguous")
            continue
        jaw = "upper" if memberships[0] == 0 else "lower"
        histograms[jaw][int(code) - 2] += 1
    if any(sum(hist.values()) != 6 for hist in histograms.values()):
        issues.add("jaw_tooth_count_review")
    return {"issues": sorted(issues),
            "histograms": {jaw: [hist[g] for g in range(5)] for jaw, hist in histograms.items()},
            "tooth_identity_verified": False}


def check_incomplete_policy(record, annotation_path):
    """Opt-in evidence check only. All historical labels/review fields are preserved."""
    reasons = set(record["qa_issues"]) - {"incomplete_caption_positions", "lower_jaw_omission_policy_pending"}
    reasons.update(set(record["original_issues"]) - {"conflicting_caption_grades"})
    parsed = record["csv"]["captions"]
    maps = [c["site_grades"] for c in parsed]
    if (len(maps) != 3 or any(c["issues"] for c in parsed)
            or any(set(m) != {str(s) for s in SITES} or any(len(v) != 1 for v in m.values()) for m in maps[:2])
            or maps[0] != maps[1]):
        reasons.add("complete_caption_pair_required")
    if (len(maps) != 3 or set(maps[2]) != {str(s) for s in UPPER}
            or any(maps[2][s] != maps[0].get(s) for s in maps[2])):
        reasons.add("matching_upper_partial_required")
    jaw_result = jaw_histograms(annotation_path)
    reasons.update(jaw_result["issues"])
    if not reasons:
        # Verify both complete variants against separate jaw histograms.
        for m in maps[:2]:
            for jaw, sites in [("upper", UPPER), ("lower", LOWER)]:
                expected = Counter(m[str(site)][0] for site in sites)
                if [expected[g] for g in range(5)] != jaw_result["histograms"][jaw]:
                    reasons.add("caption_txt_jaw_histogram_disagreement")
    eligible = not reasons
    result = deepcopy(record)
    result["incomplete_policy_check"] = {
        "mode": "check_upper_partial", "policy_eligible_candidate": eligible,
        "reasons": sorted(reasons), "jaw_evidence": jaw_result,
        "supported_source_maximum": max(v[0] for v in maps[0].values()) if eligible else None,
        "requires_qualified_approval": True, "approved_label_eligibility": False,
        "clears_review_status": False,
    }
    return result


def check_cached_omissions(staging, cached_records):
    """Reuse QA and reparse only the omission subset to detect stale CSV evidence."""
    selected = [r for r in cached_records if r["csv"]["lower_jaw_omission_pattern"]]
    keys = {r["image_path"] for r in selected}
    if len(keys) != len(selected):
        raise ValueError("Repeated cached omission path")
    lookup = defaultdict(list)
    for split, stem in CAPTIONS.items():
        with (staging / f"Dataset/{split}/{stem}_captions.csv").open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                filename = row["FileName"]
                if not safe_member(filename) or Path(filename).name != filename:
                    raise ValueError("Unsafe caption filename")
                key = f"Dataset/{split}/Images/{filename}"
                if key in keys:
                    lookup[key].append(row)
    results = []
    for record in selected:
        path = record["image_path"]
        split = record["original_split"]
        if split not in CAPTIONS or not safe_member(path) or not path.startswith(f"Dataset/{split}/Images/"):
            raise ValueError("Unsafe cached omission path")
        if compare_captions(lookup[path]) != record["csv"]:
            raise ValueError("Selected CSV evidence differs from cached QA; do not use stale evidence")
        annotation = staging / "Dataset" / split / "Labels" / (Path(path).stem + ".txt")
        # Reuse the whole-image validator, then add the stricter jaw-only evidence check.
        if compare_txt(record["csv"], annotation) != record["txt"]:
            raise ValueError("Selected TXT evidence differs from cached QA; stop")
        results.append(check_incomplete_policy(record, annotation))
    return results


def format_policy_report(results):
    """Separate evidence eligibility from qualification, approval and status clearance."""
    lines = ["# Optional incomplete-caption policy check", "", "Date: 2026-10-14. Branch: vinuthan.",
             "Check-only mode, not policy activation. Strict remains the default. No approved labels or review statuses changed.", "",
             "Requirements: matching complete Caption 1/2; all six stated upper positions in Caption 3 match; no additional independent anomaly; valid upper/lower TXT grade histograms. Each tooth centre must belong to exactly one documented jaw ROI, with six tooth boxes per jaw. Ambiguous geometry is rejected, not assigned by left-to-right rank or nearest jaw. Jaw metadata does not prove FDI tooth identity.", "",
             "| Original split | Omission records checked | Policy-eligible candidates | Blocked by independent evidence |",
             "|---|---:|---:|---:|"]
    for split in [*EXPECTED, "Total"]:
        rows = [r for r in results if split == "Total" or r["original_split"] == split]
        eligible = sum(r["incomplete_policy_check"]["policy_eligible_candidate"] for r in rows)
        lines.append(f"| {split} | {len(rows)} | {eligible} | {len(rows)-eligible} |")
    lines += ["", "Every checked record still requires qualification/approval; eligible does not mean clinically validated or training-ready. Original candidate_image_maximum, qa_requires_review and historical fields are unchanged.", "",
              "## Blocked records", ""]
    for r in results:
        if not r["incomplete_policy_check"]["policy_eligible_candidate"]:
            lines.append(f"- {r['original_split']} {Path(r['image_path']).stem}: " + ", ".join(r['incomplete_policy_check']['reasons']))
    lines += ["", "## Approval and boundaries", "",
              "This optional configuration only tests an approval proposal. Activating an incomplete-caption label policy, accepting individual clinical labels and freezing final eligibility/splits require qualified reviewer/supervisor approval with provenance and date. MGI 0–4, RGB → maximum visible MGI → Grad-CAM and the independent questionnaire architecture are unchanged. Missing information is never zero.",
              "No full dataset/image re-audit, model fitting, selection, inference or test evaluation. Final-test annotations are examined exclusively for this authorized QA check. Criteria and geometry rules are fixed independently of performance outcomes. Historical QA flags and original statuses are not cleared; evidence candidates never automatically reduce the unresolved queue."]
    return "\n".join(lines) + "\n"


def verify_record(source, captions, annotation_path, policy="strict"):
    """Preserve historical status and target; new flags belong to separate QA fields."""
    if policy not in POLICIES:
        raise ValueError("Unknown caption policy")
    csv_result = compare_captions(captions)
    txt_result = compare_txt(csv_result, annotation_path)
    issues = sorted(set(csv_result["issues"]) | set(txt_result["issues"]))
    requires_review = source["status"] == "needs_review" or bool(issues)
    result = {"image_path": source["image_path"], "original_split": source["split"],
            "original_status": source["status"], "original_mgi_max": source["mgi_max"],
            "original_issues": source["issues"], "qa_issues": issues,
            "qa_requires_review": requires_review,
            "candidate_image_maximum": None if requires_review else csv_result["caption_candidate_maximum"],
            "approved_mgi_grade": None, "csv": csv_result, "txt": txt_result}
    return result if policy == "strict" else check_incomplete_policy(result, annotation_path)


def verify_dataset(staging):
    """Read cached inventory and current annotations; never decode images or train."""
    staging = Path(staging)
    source = json.loads((staging / "audit_verified/integrity_results.json").read_text())["result"]
    rows = source["manifest"]
    if Counter(r["split"] for r in rows) != Counter(EXPECTED):
        raise ValueError("Cached split counts do not match the expected source inventory")
    lookup = defaultdict(list)
    for split, stem in CAPTIONS.items():
        with (staging / f"Dataset/{split}/{stem}_captions.csv").open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not {"FileName", "#", "BS1"} <= set(reader.fieldnames or []):
                raise ValueError("Missing CSV columns")
            for row in reader:
                filename = row["FileName"]
                if not safe_member(filename) or Path(filename).name != filename:
                    raise ValueError("Unsafe caption filename")
                lookup[(split, filename)].append(row)
    expected_keys = {(r["split"], Path(r["image_path"]).name) for r in rows}
    if set(lookup) != expected_keys or len({r["image_path"] for r in rows}) != len(rows):
        raise ValueError("CSV filenames and cached image inventory differ")
    results = []
    for row in rows:
        relative = row["image_path"]
        if not safe_member(relative) or not relative.startswith(f"Dataset/{row['split']}/Images/"):
            raise ValueError("Unsafe cached image path")
        if not (staging / relative).is_file():
            raise FileNotFoundError(relative)
        name = Path(relative).name
        annotation = staging / "Dataset" / row["split"] / "Labels" / (Path(name).stem + ".txt")
        results.append(verify_record(row, lookup[(row["split"], name)], annotation))
    return results


def format_report(results):
    """Summarise QA counts without publishing participant-level manifests."""
    lines = ["# Vision caption-label verification QA", "", "Date: 2026-10-14. Branch: vinuthan.",
             "Read-only annotation QA across all 1,096 cached records. No labels/splits approved or changed; no training.", "",
             "## Fixed QA rules and limits", "",
             "Explicit grades 0–4 and source non-inflamed wording must be grounded to explicit supported tooth positions. Empty clauses, invalid grades, conflicting positions and declared-count errors require review. Three complete agreeing variants are required for a candidate; the 113-pattern omission never automatically clears a record. Historical needs_review always stays pending.",
             "TXT 0/1 are ROI; 2–6 correspond to MGI 0–4. Only grade-count histograms are compared, never asserted tooth identity. Histogram agreement is necessary evidence here, not clinical validation; equal histograms can conceal per-tooth permutations.",
             "Rules are annotation QA only, uniformly applied to original splits. Test annotations/statistics are not used for model design, selection or final-test inference. RGB originals are not decoded, resized or modified in this task.", "",
             "## Actual record counts", "",
             "| Split | Source records | Original needs_review | New QA flags outside historical queue | QA-consistent and historically provisional | Pending union |",
             "|---|---:|---:|---:|---:|---:|"]
    for split in [*EXPECTED, "Total"]:
        rows = [r for r in results if split == "Total" or r["original_split"] == split]
        historical = sum(r["original_status"] == "needs_review" for r in rows)
        new = sum(r["original_status"] != "needs_review" and bool(r["qa_issues"]) for r in rows)
        pending = sum(r["qa_requires_review"] for r in rows)
        lines.append(f"| {split} | {len(rows)} | {historical} | {new} | {len(rows)-pending} | {pending} |")
    lines += ["", "These are source-evidence categories, not cleared training eligibility or approved clinical grades.", "",
              "## QA issue flags (overlap; do not sum)", "",
              "| Flag | Training | Validation | Test | Total |", "|---|---:|---:|---:|---:|"]
    flags = sorted({flag for r in results for flag in r["qa_issues"]})
    for flag in flags:
        counts = [sum(flag in r["qa_issues"] for r in results if r["original_split"] == s) for s in EXPECTED]
        lines.append(f"| {flag} | " + " | ".join(map(str, [*counts, sum(counts)])) + " |")
    lines += ["", "## Candidate source maxima, not assigned labels", "",
              "| Split | MGI 0 | MGI 1 | MGI 2 | MGI 3 | MGI 4 | Candidate withheld |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for split in [*EXPECTED, "Total"]:
        rows = [r for r in results if split == "Total" or r["original_split"] == split]
        counts = Counter(r["candidate_image_maximum"] for r in rows)
        lines.append(f"| {split} | " + " | ".join(str(counts[g]) for g in [0, 1, 2, 3, 4, None]) + " |")
    lines += ["", "## Regression evidence and new examples", ""]
    for split, name in [("Training", "00025"), ("Training", "00029"), ("Validation", "01106"), ("Test", "01223")]:
        row = next(r for r in results if r["original_split"] == split and Path(r["image_path"]).stem == name)
        lines.append(f"- {split} {name}: original status {row['original_status']}; QA flags {', '.join(row['qa_issues']) or 'none'}; candidate {row['candidate_image_maximum']}; approved grade remains unset.")
    omission = [r for r in results if r["csv"]["lower_jaw_omission_pattern"]]
    lines.append(f"- Lower-jaw-omission pattern found: {len(omission)} records; all remain policy-pending.")
    old_omission = sum(r["original_status"] == "needs_review" for r in omission)
    lines.append(f"- Omission overlap: {old_omission} already in the historical review queue; {len(omission)-old_omission} outside it. The previously documented 113-case subset is included, not replaced or newly resolved.")
    new = [r for r in results if r["original_status"] != "needs_review" and r["qa_issues"]]
    lines.append("- Newly flagged means outside the cached 161-record queue, not necessarily first discovery: 00025 was already documented as a sampled concern. The former 934-record hypothetical screen is not a verified clean cohort after this broader QA.")
    lines.append("- First newly flagged examples: " + "; ".join(f"{r['original_split']} {Path(r['image_path']).stem}" for r in new[:10]) + ".")
    lines += ["", "## Remaining blockers", "",
              "Qualified annotation/clinical review, incomplete-caption policy approval, unresolved duplicate groups and participant independence, absent image-level MGI 0 support, and final reviewed target/split manifest. Five-class MGI definitions and RGB → maximum MGI → Grad-CAM architecture remain unchanged. No four-class mapping, model choice, relabel or split policy is implemented.",
              "", "Historical manifests/reports are preserved. New QA flags supplement, never overwrite, the 161-case history. Detailed QA output is a separate ignored local artifact, not a final label manifest."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--details", type=Path, required=True)
    parser.add_argument("--policy", choices=POLICIES, default="strict")
    parser.add_argument("--cached-qa", type=Path,
                        help="Required for optional check; selects only cached omission records")
    args = parser.parse_args()
    # Exclusive outputs prevent replacing any historical report or manifest.
    if args.report.exists() or args.details.exists():
        raise FileExistsError("Output already exists; preserve it")
    dataset = args.staging / "Dataset"
    for output in (args.report, args.details):
        if dataset.resolve() == output.resolve() or dataset.resolve() in output.resolve().parents:
            raise ValueError("Do not write into source Dataset")
        if not output.parent.is_dir():
            raise FileNotFoundError(output.parent)
    if args.policy == "check_upper_partial":
        if args.cached_qa is None:
            parser.error("--cached-qa is required for the focused optional check")
        results = check_cached_omissions(args.staging, json.loads(args.cached_qa.read_text()))
        report = format_policy_report(results)
    else:
        if args.cached_qa is not None:
            parser.error("--cached-qa is supported only with --policy check_upper_partial")
        results = verify_dataset(args.staging)
        report = format_report(results)
    with args.details.open("x", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with args.report.open("x", encoding="utf-8") as f:
        f.write(report)
    print(report)


if __name__ == "__main__":
    main()
