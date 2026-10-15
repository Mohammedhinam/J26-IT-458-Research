"""Cached grouping tests: no photos, labels for model fitting, or split activation."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

import pytest

from src.vision.content_groups import (
    build_content_groups, connected_components, grouping_analysis,
    proposed_placement, screen_near_duplicates,
)
from src.vision.extract_audit_gingivitis import duplicate_groups


def row(name, split="Training", content=None, fingerprint=0):
    content = name if content is None else content
    return {"image_path": f"Dataset/{split}/Images/{name}.jpg", "split": split,
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "pixel_sha256": hashlib.sha256(("pixel:" + content).encode()).hexdigest(),
            "dhash": f"{fingerprint:016x}", "mgi_max": 4, "status": "needs_review", "issues": []}


def cache(rows):
    return {"result": {"manifest": rows, "duplicate_groups": duplicate_groups(rows, "sha256")}}


def projection(groups):
    return [{k: v for k, v in g.items() if k != "source_records"} for g in groups]


def test_grouping_is_deterministic_and_preserves_all_source_rows():
    rows = [row("a", content="same"), row("b", "Test", content="same"), row("c", fingerprint=65535)]
    original = deepcopy(rows)
    groups = build_content_groups(rows)
    assert groups == build_content_groups(list(reversed(rows)))
    assert len(groups) == 2 and sum(len(g["source_records"]) for g in groups) == 3
    assert rows == original
    aliases = next(g for g in groups if len(g["members"]) == 2)
    assert aliases["proposed_reserved_split"] == "Test"
    assert aliases["proposed_representative"] == "Dataset/Test/Images/b.jpg"
    assert aliases["activated"] is False


def test_grouping_representatives_thresholds_and_edges_are_label_blind():
    rows = [row("a", content="same"), row("b", "Test", content="same"), row("c", fingerprint=15)]
    changed = deepcopy(rows)
    for i, item in enumerate(changed):
        item["mgi_max"] = i
        item["status"] = "provisional"
        item["issues"] = ["different_annotation"]
    first, second = build_content_groups(rows), build_content_groups(changed)
    assert projection(first) == projection(second)
    assert screen_near_duplicates(first) == screen_near_duplicates(second)


def test_equal_pixels_can_group_differently_encoded_files():
    rows = [row("a", content="same"), row("b", content="same")]
    rows[1]["sha256"] = hashlib.sha256(b"re-encoded").hexdigest()
    assert len(build_content_groups(rows)) == 1


def test_inconsistent_or_missing_cached_fingerprints_stop():
    rows = [row("a", content="same"), row("b", content="same")]
    rows[1]["dhash"] = "f" * 16
    with pytest.raises(ValueError, match="Inconsistent"):
        build_content_groups(rows)
    rows = [row("a")]
    rows[0]["dhash"] = ""
    with pytest.raises(ValueError, match="cached dhash"):
        build_content_groups(rows)


def test_duplicate_path_and_unknown_split_stop():
    with pytest.raises(ValueError, match="Repeated"):
        build_content_groups([row("a"), row("a")])
    with pytest.raises(ValueError, match="split/path"):
        build_content_groups([row("a", "unknown")])


def test_hamming_default_boundary_and_candidates_not_confirmation():
    groups = build_content_groups([row("a", fingerprint=0), row("b", fingerprint=15)])
    pairs = screen_near_duplicates(groups)
    assert len(pairs) == 1 and pairs[0]["hamming_distance"] == 4
    assert pairs[0]["requires_visual_verification"] and not pairs[0]["confirmed_duplicate"]
    groups = build_content_groups([row("a", fingerprint=0), row("b", fingerprint=31)])
    assert screen_near_duplicates(groups) == []


def test_dhash_collision_is_not_an_exact_group():
    groups = build_content_groups([row("a", fingerprint=1), row("b", fingerprint=1)])
    assert len(groups) == 2
    assert screen_near_duplicates(groups)[0]["hamming_distance"] == 0


@pytest.mark.parametrize("threshold", [-1, 65, 2.5, True])
def test_invalid_hamming_threshold_rejected(threshold):
    with pytest.raises(ValueError, match="threshold"):
        screen_near_duplicates([], threshold)


def test_aliases_do_not_multiply_near_pairs_or_hypothetical_exclusions():
    rows = [row("a", content="same", fingerprint=0), row("b", "Test", content="same", fingerprint=0),
            row("c", "Validation", fingerprint=15)]
    result = grouping_analysis(cache(rows))
    assert len(result["exact_content_groups"]) == 2
    assert len(result["near_candidate_pairs"]) == 1
    assert result["if_all_near_edges_verified_group_count"] == 1
    assert result["if_all_near_edges_verified_proposed_counts"] == {"Test": 1}
    assert not result["training_ready_manifest"]


def test_transitive_review_component_not_all_pair_similarity():
    rows = [row("a", fingerprint=0), row("b", fingerprint=15), row("c", fingerprint=255)]
    result = grouping_analysis(cache(rows))
    assert len(result["near_candidate_pairs"]) == 2
    assert len(result["candidate_review_components"]) == 1
    assert result["if_all_near_edges_verified_group_count"] == 1
    assert not result["candidate_review_components"][0]["verified"]
    assert connected_components(["c", "a", "b"], [("b", "c"), ("a", "b")]) == [["a", "b", "c"]]


def test_validation_reservation_and_label_blind_filename_order():
    rows = [row("z", "Training"), row("b", "Validation"), row("a", "Validation")]
    result = proposed_placement(rows)
    assert result["proposed_reserved_split"] == "Validation"
    assert result["proposed_representative"] == "Dataset/Validation/Images/a.jpg"


def test_inconsistent_cached_exact_group_ledger_stops():
    value = cache([row("a", content="same"), row("b", content="same")])
    value["result"]["duplicate_groups"] = []
    with pytest.raises(ValueError, match="ledger"):
        grouping_analysis(value)


def test_cached_dataset_regression_no_source_image_read_or_label_change():
    location = os.environ.get("VISION_QA_STAGING")
    if not location:
        pytest.skip("Optional local cached-evidence regression")
    path = Path(location) / "audit_verified/integrity_results.json"
    before = path.read_bytes()
    data = json.loads(before)
    original = deepcopy(data)
    result = grouping_analysis(data)
    assert len(result["known_exact_groups"]) == 14
    assert sum(g["cross_split"] for g in result["known_exact_groups"]) == 8
    assert len(result["exact_content_groups"]) == 1082
    assert result["exact_proposed_counts"] == {"Training": 718, "Validation": 182, "Test": 182}
    assert len(result["near_candidate_pairs"]) == 54
    assert sum(p["cross_split_candidate"] for p in result["near_candidate_pairs"]) == 11
    assert len(result["candidate_review_components"]) == 40
    assert result["if_all_near_edges_verified_group_count"] == 1028
    assert result["if_all_near_edges_verified_proposed_counts"] == {"Training": 678, "Validation": 177, "Test": 173}
    preserved = {r["image_path"]: r for g in result["exact_content_groups"] for r in g["source_records"]}
    assert preserved == {r["image_path"]: r for r in data["result"]["manifest"]}
    assert data == original and path.read_bytes() == before
    assert all(not g["activated"] for g in result["exact_content_groups"])
