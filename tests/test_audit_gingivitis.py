"""Synthetic archive/caption checks; no real image data or training required."""

import pytest

from src.vision.audit_gingivitis import EXPECTED, audit_inventory, caption_grades, safe_member


def fixture_inputs():
    members = []
    captions = {}
    for split in EXPECTED:
        name = f"{split}.jpg"
        members.append(f"Dataset/{split}/Images/{name}")
        captions[split] = [{"FileName": name, "#": str(i),
                            "BS1": "4 level of gingivitis 1 at position 13; Level 3 gingivitis teeth 42"}
                           for i in range(1, 4)]
    return members, captions


@pytest.mark.parametrize("text,expected,error", [
    ("4 level of gingivitis 1 at position 13; Level 3 gingivitis teeth 42", {1, 3}, None),
    ("gingivitis 0; gingivitis grade 4", {0, 4}, None),
    ("non-inflamed tooth 13", set(), "no_explicit_grade"),
    ("gingivitis 5", set(), "invalid_grade"),
    ("Level -1 gingivitis", set(), "invalid_grade"),
    ("gingivitis 2.5", set(), "invalid_grade"),
    ("", set(), "no_explicit_grade"),
])
def test_caption_parser(text, expected, error):
    assert caption_grades(text) == (expected, error)


def test_provisional_maximum_and_distribution():
    members, captions = fixture_inputs()
    result = audit_inventory(members, captions)
    assert result["anomalies"] == []
    assert [row["mgi_max"] for row in result["manifest"]] == [3, 3, 3]
    assert all(row["grades"] == [0, 0, 0, 1, 0] for row in result["summaries"])
    assert all(row["mixed_explicit_grades"] == 1 for row in result["summaries"])


def test_conflicting_variants_and_missing_ids_require_review():
    members, captions = fixture_inputs()
    captions["Training"][0]["BS1"] = "gingivitis 2"
    captions["Validation"][1]["#"] = "1"
    result = audit_inventory(members, captions)
    assert {row["kind"] for row in result["anomalies"]} == {"conflicting_caption_grades", "caption_variant_ids"}
    assert [row["mgi_max"] for row in result["manifest"]] == [None, None, 3]


def test_missing_images_captions_and_duplicate_names():
    members, captions = fixture_inputs()
    members += [members[0], "Dataset/Test/Images/Training.jpg", "Dataset/Test/Images/test.jpg"]
    captions["Validation"][0]["FileName"] = "absent.jpg"
    result = audit_inventory(members, captions)
    kinds = {row["kind"] for row in result["anomalies"]}
    assert {"duplicate_archive_path", "cross_split_filename", "case_insensitive_path_collision",
            "caption_image_missing", "image_caption_missing", "caption_variant_ids"} <= kinds


@pytest.mark.parametrize("name", ["/etc/passwd", "Dataset/../escape.jpg", "C:\\escape.jpg"])
def test_unsafe_names(name):
    assert not safe_member(name)
    members, captions = fixture_inputs()
    members.append(name)
    assert any(row["kind"] == "unsafe_archive_path" for row in audit_inventory(members, captions)["anomalies"])


def test_counts_and_labels_are_deterministic():
    members, captions = fixture_inputs()
    first = audit_inventory(members, captions)
    assert first == audit_inventory(members, captions)
    assert sum(row["image_entries"] for row in first["summaries"]) == 3
    assert all(sum(row["grades"]) + row["needs_review"] == row["unique_image_names"]
               for row in first["summaries"])


def test_same_maximum_but_conflicting_grade_sets_remain_review():
    members, captions = fixture_inputs()
    captions["Training"][0]["BS1"] = "gingivitis 3"
    result = audit_inventory(members, captions)
    assert result["manifest"][0]["mgi_max"] is None
    assert result["summaries"][0]["conflicting_maxima"] == 0


def test_duplicate_basename_in_nested_path_is_flagged():
    members, captions = fixture_inputs()
    members.append("Dataset/Training/Images/nested/Training.jpg")
    kinds = {row["kind"] for row in audit_inventory(members, captions)["anomalies"]}
    assert {"duplicate_filename_within_split", "unexpected_image_path"} <= kinds
