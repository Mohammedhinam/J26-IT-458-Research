"""Synthetic source-evidence tests; no clinical ground truth or image fitting."""

from copy import deepcopy
import csv
import json
import sys

import pytest

from src.vision.verify_caption_labels import (
    LOWER, SITES, UPPER, compare_captions, compare_txt, parse_caption, verify_record,
)
from src.vision import verify_caption_labels as qa


def variants(texts):
    return [{"#": str(i), "BS1": text} for i, text in enumerate(texts, 1)]


def full_caption(grade=2):
    return f"gingivitis {grade} at position " + ", ".join(str(s) for s in sorted(SITES))


@pytest.mark.parametrize("text", [
    "gingivitis 2 at position 13, 12",
    "Level 2 gingivitis teeth 13, ,12",
    "The upper jaw has teeth 13, 12 level of gingivitis 2",
    "MGI grade 2 at positions 13 / 12",
    "gingivitis grade 2 at position 13，12",
    "GINGIVITIS 2 at positions 13 and 12",
])
def test_supported_grade_formats(text):
    evidence = parse_caption(text)
    assert evidence["site_grades"] == {"12": [2], "13": [2]}
    assert evidence["issues"] == []


@pytest.mark.parametrize("text", [
    "non-inflamed tooth at position 13",
    "The tooth is not inflamed at teeth 13 in upper jaw",
    "The upper jaw has teeth 13 is non-inflamed at position",
    "normal gingiva at position 13",
])
def test_normal_is_explicit_source_wording_only(text):
    assert parse_caption(text)["site_grades"] == {"13": [0]}
    assert 12 in parse_caption(text)["missing_sites"]


@pytest.mark.parametrize("text,flag", [
    ("Level 4 gingivitis teeth in upper jaw", "unsupported_grade_clause"),
    ("gingivitis 9 at position 13", "invalid_grade"),
    ("gingivitis -1 at position 13", "invalid_grade"),
    ("gingivitis 2.5 at position 13", "invalid_grade"),
    ("gingivitis 2 at position 14", "unsupported_tooth_position"),
    ("gingivitis 2 at position 13, 13", "repeated_tooth_position"),
    ("gingivitis 2 at position 13-12", "ambiguous_tooth_range"),
    ("has 3 level of gingivitis 2 at position 13, 12", "declared_tooth_count_mismatch"),
    ("severe gingivitis at position 13", "unparsed_severity_phrase"),
])
def test_ambiguous_or_unsupported_is_review_evidence(text, flag):
    assert flag in parse_caption(text)["issues"]


def test_missing_never_becomes_zero():
    assert parse_caption("")["site_grades"] == {}
    assert compare_captions(variants(["", "", ""]))["caption_candidate_maximum"] is None


def test_explicit_two_jaw_normal_lists_and_empty_secondary_list():
    parsed = parse_caption("The tooth is not inflamed at teeth 13 in upper jaw and teeth 43 in lower jaw")
    assert parsed["site_grades"] == {"13": [0], "43": [0]}
    assert not parsed["issues"]
    parsed = parse_caption("The tooth is not inflamed at teeth 13 in upper jaw and teeth in lower jaw")
    assert "unsupported_grade_clause" in parsed["issues"]


def test_empty_high_grade_not_used_even_if_another_clause_supported():
    text = full_caption(2) + "; Level 4 gingivitis teeth in upper jaw"
    result = compare_captions(variants([text] * 3))
    assert "unsupported_grade_clause" in result["issues"]
    assert result["caption_candidate_maximum"] is None


def test_same_grade_nested_wrapper_is_recorded_without_phantom_sites():
    text = "Level 2 gingivitis teeth has 2 level of gingivitis 2 at position 43, 42 in lower jaw"
    parsed = parse_caption(text)
    assert not parsed["issues"]
    assert parsed["mentions"][0]["supported_repeated_wrapper"]
    assert parsed["site_grades"] == {"42": [2], "43": [2]}


def test_different_grade_wrapper_stays_unsupported():
    parsed = parse_caption("Level 4 gingivitis teeth has 2 level of gingivitis 2 at position 43, 42")
    assert "unsupported_grade_clause" in parsed["issues"]


def test_within_and_between_caption_position_conflicts():
    parsed = parse_caption("gingivitis 1 at position 13; gingivitis 2 at position 13")
    assert "within_caption_position_conflict" in parsed["issues"]
    result = compare_captions(variants([full_caption(1), full_caption(2), full_caption(2)]))
    assert "between_caption_position_conflict" in result["issues"]
    assert result["caption_candidate_maximum"] is None


def test_conflicting_position_lists_in_one_phrase_are_not_silently_selected():
    parsed = parse_caption("teeth 13 level of gingivitis 2 at position 12")
    assert "contradictory_position_clause" in parsed["issues"]


def test_lower_jaw_omission_remains_policy_pending():
    full = full_caption(2)
    upper = "gingivitis 2 at position " + ", ".join(str(s) for s in sorted(UPPER))
    result = compare_captions(variants([full, full, upper]))
    assert result["lower_jaw_omission_pattern"]
    assert "lower_jaw_omission_policy_pending" in result["issues"]
    assert result["caption_candidate_maximum"] is None
    assert set(result["captions"][2]["missing_sites"]) == LOWER


def test_omission_detected_even_when_numeric_grade_sets_and_maxima_match():
    full = full_caption(4)
    upper = "gingivitis 4 at position " + ", ".join(str(s) for s in sorted(UPPER))
    result = compare_captions(variants([full, full, upper]))
    assert result["lower_jaw_omission_pattern"]
    assert result["caption_candidate_maximum"] is None


def test_complete_source_maximum_and_explicit_all_normal():
    result = compare_captions(variants([full_caption(3)] * 3))
    assert result["caption_candidate_maximum"] == 3
    normal = "non-inflamed tooth at position " + ", ".join(str(s) for s in sorted(SITES))
    assert compare_captions(variants([normal] * 3))["caption_candidate_maximum"] == 0


def test_variant_ids_not_selected_or_overwritten():
    rows = variants([full_caption()] * 3)
    rows[2]["#"] = "2"
    assert "caption_variant_structure" in compare_captions(rows)["issues"]


def write_txt(path, tooth_codes):
    rows = ["0 0.5 0.3 0.8 0.3", "1 0.5 0.7 0.8 0.3"]
    rows += [f"{code} 0.5 0.5 0.1 0.1" for code in tooth_codes]
    path.write_text("\n".join(rows) + "\n")


def test_txt_histogram_mapping_excludes_roi_and_does_not_invent_tooth_ids(tmp_path):
    path = tmp_path / "labels.txt"
    write_txt(path, [4] * 12)
    result = compare_txt(compare_captions(variants([full_caption(2)] * 3)), path)
    assert result["txt_histogram"] == [0, 0, 12, 0, 0]
    assert not result["issues"]
    assert not result["tooth_identity_verified"]


def test_00025_like_equal_maximum_can_have_histogram_conflict(tmp_path):
    path = tmp_path / "labels.txt"
    write_txt(path, [2] + [6] * 11)
    result = compare_txt(compare_captions(variants([full_caption(4)] * 3)), path)
    assert "caption_txt_grade_histogram_disagreement" in result["issues"]


def test_histogram_equality_cannot_certify_per_tooth_correspondence(tmp_path):
    path = tmp_path / "labels.txt"
    write_txt(path, [3] * 6 + [6] * 6)
    text = "gingivitis 1 at position " + ", ".join(map(str, sorted(UPPER)))
    text += "; gingivitis 4 at position " + ", ".join(map(str, sorted(LOWER)))
    result = compare_txt(compare_captions(variants([text] * 3)), path)
    assert not result["issues"]
    assert result["tooth_identity_verified"] is False


def test_preservation_reproducibility_and_historical_review_never_cleared(tmp_path):
    path = tmp_path / "labels.txt"
    write_txt(path, [4] * 12)
    before = path.read_bytes()
    source = {"split": "Test", "image_path": "Dataset/Test/Images/example.jpg",
              "status": "needs_review", "mgi_max": 2, "issues": ["duplicate_content"]}
    original = deepcopy(source)
    rows = variants([full_caption(2)] * 3)
    first = verify_record(source, rows, path)
    second = verify_record(source, list(reversed(rows)), path)
    assert first == second
    assert source == original and path.read_bytes() == before
    assert first["original_split"] == "Test" and first["original_status"] == "needs_review"
    assert first["candidate_image_maximum"] is None and first["approved_mgi_grade"] is None
    assert json.loads(json.dumps(first)) == first


def synthetic_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(qa, "EXPECTED", {"Training": 1, "Validation": 1, "Test": 1})
    rows = []
    for split, stem in qa.CAPTIONS.items():
        folder = tmp_path / "Dataset" / split
        (folder / "Images").mkdir(parents=True)
        (folder / "Labels").mkdir()
        (folder / "Images/example.jpg").write_bytes(b"Not decoded by annotation-only QA")
        write_txt(folder / "Labels/example.txt", [4] * 12)
        with (folder / f"{stem}_captions.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["FileName", "#", "BS1"])
            writer.writeheader()
            for variant in variants([full_caption(2)] * 3):
                writer.writerow({"FileName": "example.jpg", **variant})
        rows.append({"split": split, "image_path": f"Dataset/{split}/Images/example.jpg",
                     "status": "provisional", "mgi_max": 2, "issues": []})
    (tmp_path / "audit_verified").mkdir()
    cache = tmp_path / "audit_verified/integrity_results.json"
    cache.write_text(json.dumps({"result": {"manifest": rows}}))
    return cache


def test_dataset_bom_csv_uniform_rules_no_image_decode_or_manifest_edit(tmp_path, monkeypatch):
    cache = synthetic_dataset(tmp_path, monkeypatch)
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    first = qa.verify_dataset(tmp_path)
    assert len(first) == 3
    assert {r["original_split"] for r in first} == {"Training", "Validation", "Test"}
    assert all(r["candidate_image_maximum"] == 2 and r["approved_mgi_grade"] is None for r in first)
    assert first == qa.verify_dataset(tmp_path)
    assert {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


def test_filename_mismatch_stops_without_changing_sources(tmp_path, monkeypatch):
    synthetic_dataset(tmp_path, monkeypatch)
    path = tmp_path / "Dataset/Training/Train_captions.csv"
    path.write_text(path.read_text(encoding="utf-8-sig").replace("example.jpg", "other.jpg"))
    with pytest.raises(ValueError, match="filenames"):
        qa.verify_dataset(tmp_path)


def test_cli_never_overwrites_existing_report(tmp_path, monkeypatch):
    report = tmp_path / "report.md"
    report.write_text("preserve")
    details = tmp_path / "details.json"
    monkeypatch.setattr(sys, "argv", ["qa", "--staging", str(tmp_path), "--report", str(report), "--details", str(details)])
    with pytest.raises(FileExistsError):
        qa.main()
    assert report.read_text() == "preserve" and not details.exists()


def test_cli_rejects_output_inside_source_dataset(tmp_path, monkeypatch):
    source = tmp_path / "Dataset"
    source.mkdir()
    monkeypatch.setattr(sys, "argv", ["qa", "--staging", str(tmp_path), "--report", str(source / "report.md"), "--details", str(tmp_path / "details.json")])
    with pytest.raises(ValueError, match="source Dataset"):
        qa.main()
    assert not (source / "report.md").exists()
