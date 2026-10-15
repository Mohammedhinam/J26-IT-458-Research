"""PROPOSED content grouping and cached dHash screening; never changes splits."""

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path
import re

from src.vision.audit_gingivitis import EXPECTED, safe_member
from src.vision.extract_audit_gingivitis import duplicate_groups


VERSION = "proposed-content-v1"
DEFAULT_MAX_HAMMING = 4  # Fixed screen: at most 4 of 64 gradient bits differ.
SPLIT_PRIORITY = {"Training": 0, "Validation": 1, "Test": 2}


def connected_components(keys, edges):
    """Deterministic graph components; caller decides what edges mean."""
    parents = {key: key for key in keys}

    def root(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    for a, b in sorted(edges):
        ra, rb = root(a), root(b)
        parents[max(ra, rb)] = min(ra, rb)
    groups = defaultdict(list)
    for key in sorted(parents):
        groups[root(key)].append(key)
    return sorted(groups.values())


def proposed_placement(records):
    """Protect original test/validation groups; never consult labels or scores."""
    destination = max((r["split"] for r in records), key=SPLIT_PRIORITY.get)
    representative = min(r["image_path"] for r in records if r["split"] == destination)
    return {"proposed_reserved_split": destination,
            "proposed_representative": representative, "activated": False}


def build_content_groups(records):
    """Merge cached byte/pixel equality only; retain every source row unchanged."""
    lookup = {r["image_path"]: r for r in records}
    if len(lookup) != len(records):
        raise ValueError("Repeated source image path")
    for row in records:
        if row["split"] not in SPLIT_PRIORITY or not safe_member(row["image_path"]):
            raise ValueError("Invalid source split/path")
        for field, size in [("sha256", 64), ("pixel_sha256", 64), ("dhash", 16)]:
            if not re.fullmatch(r"[0-9a-f]{" + str(size) + r"}", row.get(field, "")):
                raise ValueError(f"Missing/invalid cached {field}; do not invent fingerprints")
    edges = []
    for field in ["sha256", "pixel_sha256"]:
        for group in duplicate_groups(records, field):
            members = sorted(group["paths"])
            edges.extend((members[0], path) for path in members[1:])
    groups = []
    for paths in connected_components(lookup, edges):
        rows = [lookup[p] for p in paths]
        if len({r["pixel_sha256"] for r in rows}) != 1 or len({r["dhash"] for r in rows}) != 1:
            raise ValueError("Inconsistent cached fingerprints inside an exact content group")
        group_id = "content-" + rows[0]["pixel_sha256"]
        groups.append({"group_id": group_id, "members": paths,
                       "source_records": deepcopy(rows), "dhash": rows[0]["dhash"],
                       "original_splits": sorted({r["split"] for r in rows}),
                       "cross_split": len({r["split"] for r in rows}) > 1,
                       **proposed_placement(rows)})
    return sorted(groups, key=lambda g: g["group_id"])


def screen_near_duplicates(groups, max_hamming=DEFAULT_MAX_HAMMING):
    """dHash is a candidate screen, not clinical similarity or duplicate proof."""
    if type(max_hamming) is not int or not 0 <= max_hamming <= 64:
        raise ValueError("Hamming threshold must be an integer in 0..64")
    ordered = sorted(groups, key=lambda g: g["group_id"])
    candidates = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            distance = (int(left["dhash"], 16) ^ int(right["dhash"], 16)).bit_count()
            if distance <= max_hamming:
                candidates.append({"left_group": left["group_id"], "right_group": right["group_id"],
                                   "hamming_distance": distance,
                                   "cross_split_candidate": any(a != b for a in left["original_splits"]
                                                                for b in right["original_splits"]),
                                   "requires_visual_verification": True, "confirmed_duplicate": False})
    return candidates


def grouping_analysis(cache, max_hamming=DEFAULT_MAX_HAMMING):
    """Compute shadow counts; never combine tentative edges with confirmed evidence."""
    rows = cache["result"]["manifest"]
    groups = build_content_groups(rows)
    known = [g for g in cache["result"]["duplicate_groups"] if g["key"] == "sha256"]
    cached_pairs = {tuple(sorted(g["paths"])) for g in known}
    found_pairs = {tuple(sorted(g["paths"])) for g in duplicate_groups(rows, "sha256")}
    if cached_pairs != found_pairs:
        raise ValueError("Cached exact-group ledger disagrees with cached byte hashes; stop")
    near = screen_near_duplicates(groups, max_hamming)
    components = connected_components([g["group_id"] for g in groups],
                                      [(p["left_group"], p["right_group"]) for p in near])
    by_id = {g["group_id"]: g for g in groups}
    hypothetical = Counter()
    candidate_components = []
    for component in components:
        members = [r for key in component for r in by_id[key]["source_records"]]
        placement = proposed_placement(members)
        hypothetical[placement["proposed_reserved_split"]] += 1
        if len(component) > 1:
            candidate_components.append({"content_groups": component,
                                         "source_paths": sorted(r["image_path"] for r in members),
                                         **placement, "verified": False})
    return {"version": VERSION, "status": "PROPOSED — no split/label activation",
            "method": {"fingerprint": "cached 64-bit horizontal dHash", "max_hamming": max_hamming,
                       "threshold_selected_using_labels_or_model_outputs": False},
            "source_records": len(rows), "original_split_counts": dict(Counter(r["split"] for r in rows)),
            "known_exact_groups": deepcopy(known), "exact_content_groups": groups,
            "exact_proposed_counts": dict(Counter(g["proposed_reserved_split"] for g in groups)),
            "near_candidate_pairs": near, "candidate_review_components": candidate_components,
            "if_all_near_edges_verified_proposed_counts": dict(hypothetical),
            "if_all_near_edges_verified_group_count": len(components),
            "training_ready_manifest": False, "participant_identity_verified": False}


def format_grouping_report(result, review_groups):
    groups = result["exact_content_groups"]
    near = result["near_candidate_pairs"]
    keys = {pair[key] for pair in near for key in ("left_group", "right_group")}
    involved = [g for g in groups if g["group_id"] in keys]
    near_paths = {path for g in involved for path in g["members"]}
    exact_paths = {path for g in result["known_exact_groups"] for path in g["paths"]}
    pair_types = Counter(" / ".join(sorted(Path(p).parts[1] for p in g["paths"]))
                         for g in result["known_exact_groups"])
    lines = ["# Vision content grouping and near-duplicate screen — v1", "",
             "Date: 2026-10-14. Branch: vinuthan. **PROPOSED / PENDING qualified approval.**", "",
             "## Prespecified method and source evidence", "",
             "Reused audit_verified/integrity_results.json cached byte/pixel SHA-256 and dHash fingerprints; no image read/decode/hash recomputation, caption audit or extraction. Exact equality uses byte or RGB pixel hashes (pixel cache includes dimensions). Every original filename, split and source row is preserved in a separate ignored proposal artifact.",
             "dHash is the existing 9×8 luminance/Lanczos thumbnail: horizontal adjacent-pixel comparisons produce 64 bits. Luminance is used only for this fingerprint, not classifier RGB inputs. The prespecified default candidate radius is 4 bits of 64 (6.25%). No threshold tuning, label/grade filtering, model outputs, selected-pair visual judgment or outcome-based choice occurred. The threshold is configurable for a separately documented future screen, not a learned clinical criterion.",
             "Screen unique exact-content groups first, so aliases do not multiply candidate pairs. Candidate edges and transitive review components stay separate from confirmed groups. Connected does not mean every pair is near-identical. A dHash match may be a collision or different mouth; cropped/rotated/re-encoded duplicates may be missed. Candidates require qualified visual verification.", "",
             "## Actual cached overlaps and new candidates", "",
             f"- Source records: {result['source_records']}; exact content groups: {len(groups)}.",
             f"- Known byte-duplicate groups: {len(result['known_exact_groups'])}; original cross-split groups: {sum(g['cross_split'] for g in result['known_exact_groups'])}."]
    for kind, count in sorted(pair_types.items()):
        lines.append(f"- {kind}: {count} known pairs.")
    lines += ["", "| Known exact pair | Original member filenames/splits |", "|---|---|"]
    for number, group in enumerate(sorted(result["known_exact_groups"], key=lambda g: sorted(g["paths"])), 1):
        members = "; ".join(f"{Path(p).parts[1]} {Path(p).stem}" for p in sorted(group["paths"]))
        lines.append(f"| {number} | {members} |")
    lines.append("")
    lines += [f"- Newly screened near-candidate group pairs (exact aliases excluded): {len(near)}; cross-split candidate pairs: {sum(p['cross_split_candidate'] for p in near)}.",
              f"- Involved unique exact-content groups: {len(keys)}; distinct source entries: {sum(len(g['members']) for g in involved)}; non-singleton review components: {len(result['candidate_review_components'])}.",
              f"- Exact/near affected source-entry overlap: {len(exact_paths & near_paths)}; union of affected source entries: {len(exact_paths | near_paths)}. Overlapping aliases are not counted twice.",
              "", "## Hypothetical label-blind counts — no split changes", "",
              "Rule fixed before screening: Test > Validation > Training reservation. Pick the lexicographically first original filename within the reserved destination, without labels or scores. Preserve all aliases; representative is only proposed, not a selected training sample.", "",
              "| Scenario | Training groups | Validation groups | Test groups | Total groups |", "|---|---:|---:|---:|---:|"]
    for label, counts in [("Exact content only", result["exact_proposed_counts"]),
                          ("IF every near edge is verified (not confirmed)", result["if_all_near_edges_verified_proposed_counts"])]:
        values = [counts.get(s, 0) for s in EXPECTED]
        lines.append(f"| {label} | " + " | ".join(map(str, [*values, sum(values)])) + " |")
    lines += ["", "Pair counts are not exclusions: shared edges are combined once per hypothetical component. Do not subtract the candidate-pair count from the image total. These counts include unresolved annotations and are not final eligibility or participants.", "",
              "## Deterministic near-candidate examples (not visually verified)", "",
              "| Left group source members | Right group source members | Hamming distance |", "|---|---|---:|"]
    by_id = {g["group_id"]: g for g in groups}
    for pair in near[:10]:
        descriptions = []
        for key in ["left_group", "right_group"]:
            descriptions.append(", ".join(f"{Path(p).parts[1]} {Path(p).stem}" for p in by_id[pair[key]]["members"]))
        lines.append(f"| {descriptions[0]} | {descriptions[1]} | {pair['hamming_distance']} |")
    lines += ["", "All candidate edges, member filenames/original splits, cached source evidence and proposed placements are in the separate ignored content_grouping_proposed_v1.json artifact. This report does not export a training-ready manifest.", "",
              "## Annotation conflicts and independence blockers", "",
              f"Cached qualified-referral ledger: {len(review_groups)} known exact pairs; {sum(g['complete_position_maps_differ'] for g in review_groups)} with differing complete tooth maps; {sum(g['ambiguous_box_rank_or_count'] for g in review_groups)} with ambiguous/incomplete box coverage. All require joint review. Historical three maximum-disagreement pairs are a subset, not three extra groups. No labels were compared to choose grouping settings or representatives.",
              "Near-candidate member annotations remain as cached unresolved/provisional evidence; no consensus grade or new clinical judgment is assigned. All 274 incomplete-caption candidates remain unapproved. Earlier 339 QA flags are not cleared.",
              "Participant IDs are not documented; content grouping cannot prove participant independence or exclude repeated people with visually different photos. No participant IDs are invented from filenames, metadata or fingerprints.",
              "Signed proposal §§3.2/3.5 (pp.17–18/22) requires preventing split overlap and a frozen participant-grouped split if overlap exists. Supervisor must approve whether reserved content grouping is an acceptable documented implementation or specify a participant-grouped partition/identity procedure. This utility does not activate a final split or create a training-ready manifest.", "",
              "## Approval gates", "",
              "Qualified visual verification of candidates; joint annotation adjudication; participant/group-basis limitations; label-blind placement/representative policy; final reviewed labels and frozen split/eligibility approval. Training requires separate authorization. No MGI 0–4 definitions, RGB → image maximum → Grad-CAM or independent questionnaire architecture changed."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--review-groups", type=Path, required=True)
    parser.add_argument("--max-hamming", type=int, default=DEFAULT_MAX_HAMMING)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--details", type=Path, required=True)
    args = parser.parse_args()
    for output in (args.report, args.details):
        if output.exists():
            raise FileExistsError("Preserve existing output")
        if "Dataset" in output.resolve().parts or not output.parent.is_dir():
            raise ValueError("Output must have an existing parent outside original Dataset")
    if args.report.resolve() == args.details.resolve():
        raise ValueError("Report and details must differ")
    result = grouping_analysis(json.loads(args.cache.read_text()), args.max_hamming)
    report = format_grouping_report(result, json.loads(args.review_groups.read_text()))
    with args.details.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    with args.report.open("x", encoding="utf-8") as f:
        f.write(report)
    print(report)


if __name__ == "__main__":
    main()
