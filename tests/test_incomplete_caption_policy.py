"""Opt-in QA policy tests; evidence eligibility never clears a clinical review."""

from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

from src.vision import verify_caption_labels as qa


def caption_rows():
    upper = "gingivitis 2 at position " + ", ".join(map(str, sorted(qa.UPPER)))
    lower = "gingivitis 4 at position " + ", ".join(map(str, sorted(qa.LOWER)))
    return [{"#": str(i), "BS1": text} for i, text in enumerate([upper + "; " + lower] * 2 + [upper], 1)]


def annotations(path, upper_code=4, lower_code=6, lower_count=6):
    lines = ["0 0.5 0.25 0.9 0.3", "1 0.5 0.75 0.9 0.3"]
    lines += [f"{upper_code} {0.2+i*0.1} 0.25 0.05 0.1" for i in range(6)]
    lines += [f"{lower_code} {0.2+i*0.1} 0.75 0.05 0.1" for i in range(lower_count)]
    path.write_text("\n".join(lines) + "\n")


def source():
    return {"split": "Validation", "image_path": "Dataset/Validation/Images/example.jpg",
            "status": "needs_review", "mgi_max": None, "issues": ["conflicting_caption_grades"]}


def test_strict_default_and_optional_are_non_destructive(tmp_path):
    txt = tmp_path / "example.txt"
    annotations(txt)
    original_source = source()
    before = deepcopy(original_source)
    original_txt = txt.read_bytes()
    strict = qa.verify_record(original_source, caption_rows(), txt)
    explicit = qa.verify_record(original_source, caption_rows(), txt, policy="strict")
    checked = qa.verify_record(original_source, caption_rows(), txt, policy="check_upper_partial")
    assert strict == explicit and "incomplete_policy_check" not in strict
    assert checked["incomplete_policy_check"]["policy_eligible_candidate"]
    assert checked["incomplete_policy_check"]["supported_source_maximum"] == 4
    assert checked["incomplete_policy_check"]["requires_qualified_approval"]
    assert not checked["incomplete_policy_check"]["approved_label_eligibility"]
    assert not checked["incomplete_policy_check"]["clears_review_status"]
    assert {k: v for k, v in checked.items() if k != "incomplete_policy_check"} == strict
    assert checked["candidate_image_maximum"] is None and checked["approved_mgi_grade"] is None
    assert original_source == before and txt.read_bytes() == original_txt


def test_jaw_swap_rejected_even_when_whole_image_counts_match(tmp_path):
    txt = tmp_path / "swapped.txt"
    annotations(txt, upper_code=6, lower_code=4)
    record = qa.verify_record(source(), caption_rows(), txt, policy="check_upper_partial")
    assert not record["txt"]["issues"]  # Whole-image histogram cannot see the swap.
    check = record["incomplete_policy_check"]
    assert not check["policy_eligible_candidate"]
    assert "caption_txt_jaw_histogram_disagreement" in check["reasons"]


@pytest.mark.parametrize("variant", [0, 1, 2])
def test_caption_disagreement_never_accepted(tmp_path, variant):
    txt = tmp_path / "labels.txt"
    annotations(txt)
    rows = caption_rows()
    rows[variant]["BS1"] = rows[variant]["BS1"].replace("gingivitis 2", "gingivitis 1")
    record = qa.verify_record(source(), rows, txt, policy="check_upper_partial")
    assert not record["incomplete_policy_check"]["policy_eligible_candidate"]


def test_01247_like_five_lower_boxes_remains_blocked(tmp_path):
    txt = tmp_path / "01247.txt"
    annotations(txt, lower_count=5)
    record = qa.verify_record(source(), caption_rows(), txt, policy="check_upper_partial")
    check = record["incomplete_policy_check"]
    assert not check["policy_eligible_candidate"]
    assert "annotation_tooth_count_review" in check["reasons"]
    assert record["qa_requires_review"] and record["candidate_image_maximum"] is None


def test_independent_duplicate_issue_blocks_otherwise_matching_evidence(tmp_path):
    txt = tmp_path / "labels.txt"
    annotations(txt)
    original = source()
    original["issues"].append("duplicate_content")
    record = qa.verify_record(original, caption_rows(), txt, policy="check_upper_partial")
    assert "duplicate_content" in record["incomplete_policy_check"]["reasons"]


@pytest.mark.parametrize("geometry", ["overlap", "outside", "reversed", "unbalanced"])
def test_ambiguous_or_invalid_jaw_geometry_rejected(tmp_path, geometry):
    txt = tmp_path / "labels.txt"
    annotations(txt)
    text = txt.read_text()
    if geometry == "overlap":
        text = text.replace("0.25 0.9 0.3", "0.25 0.9 1").replace("0.75 0.9 0.3", "0.75 0.9 1")
    elif geometry == "outside":
        text = text.replace("4 0.2 0.25", "4 0.2 0.5")
    elif geometry == "reversed":
        text = text.replace("0 0.5 0.25", "0 0.5 0.75").replace("1 0.5 0.75", "1 0.5 0.25")
    else:
        text = text.replace("4 0.2 0.25", "4 0.2 0.75")
    txt.write_text(text)
    check = qa.verify_record(source(), caption_rows(), txt, policy="check_upper_partial")["incomplete_policy_check"]
    assert not check["policy_eligible_candidate"]
    assert check["jaw_evidence"]["tooth_identity_verified"] is False


def test_unsupported_clause_never_accepted(tmp_path):
    txt = tmp_path / "labels.txt"
    annotations(txt)
    rows = caption_rows()
    rows[2]["BS1"] += "; Level 4 gingivitis teeth in lower jaw"
    result = qa.verify_record(source(), rows, txt, policy="check_upper_partial")
    assert not result["incomplete_policy_check"]["policy_eligible_candidate"]


def test_policy_name_validation(tmp_path):
    with pytest.raises(ValueError, match="Unknown"):
        qa.verify_record(source(), caption_rows(), tmp_path / "unused", policy="auto_accept")


def test_check_is_deterministic_and_does_not_mutate_cached_record(tmp_path):
    txt = tmp_path / "labels.txt"
    annotations(txt)
    strict = qa.verify_record(source(), caption_rows(), txt)
    original = deepcopy(strict)
    first = qa.check_incomplete_policy(strict, txt)
    assert first == qa.check_incomplete_policy(strict, txt) and strict == original


def test_optional_cli_dispatch_never_runs_full_dataset_qa(tmp_path, monkeypatch):
    txt = tmp_path / "labels.txt"
    annotations(txt)
    strict = qa.verify_record(source(), caption_rows(), txt)
    checked = qa.check_incomplete_policy(strict, txt)
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps([strict]))
    before = cache.read_bytes()
    report, details = tmp_path / "report.md", tmp_path / "details.json"
    monkeypatch.setattr(sys, "argv", ["qa", "--staging", str(tmp_path), "--cached-qa", str(cache),
                                     "--policy", "check_upper_partial", "--report", str(report), "--details", str(details)])
    def full_qa_forbidden(*args):
        pytest.fail("Focused optional check must never dispatch full dataset QA")
    def focused(staging, records):
        assert staging == tmp_path and records == [strict]
        return [checked]
    monkeypatch.setattr(qa, "verify_dataset", full_qa_forbidden)
    monkeypatch.setattr(qa, "check_cached_omissions", focused)
    qa.main()
    assert json.loads(details.read_text()) == [checked]
    assert cache.read_bytes() == before and "Strict remains the default" in report.read_text()


def test_optional_cli_requires_existing_cached_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["qa", "--staging", str(tmp_path), "--policy", "check_upper_partial",
                                     "--report", str(tmp_path / "report.md"), "--details", str(tmp_path / "details.json")])
    with pytest.raises(SystemExit) as error:
        qa.main()
    assert error.value.code == 2
    assert not (tmp_path / "report.md").exists() and not (tmp_path / "details.json").exists()


def test_focused_live_regression_274_candidates_and_01247_exclusion():
    location = os.environ.get("VISION_QA_STAGING")
    if not location:
        pytest.skip("Optional local annotation regression; set VISION_QA_STAGING")
    staging = Path(location)
    cached_path = staging / "caption_qa_2026-10-14.json"
    before = cached_path.read_bytes()
    records = json.loads(before)
    results = qa.check_cached_omissions(staging, records)
    assert len(results) == 275
    eligible = [r for r in results if r["incomplete_policy_check"]["policy_eligible_candidate"]]
    assert len(eligible) == 274
    assert Counter(r["original_split"] for r in eligible) == {"Training": 2, "Validation": 119, "Test": 153}
    blocked = [r for r in results if not r["incomplete_policy_check"]["policy_eligible_candidate"]]
    assert [r["image_path"] for r in blocked] == ["Dataset/Test/Images/01247.jpg"]
    original = {r["image_path"]: r for r in records}
    for r in results:
        assert {k: v for k, v in r.items() if k != "incomplete_policy_check"} == original[r["image_path"]]
        assert r["candidate_image_maximum"] is None and r["approved_mgi_grade"] is None
        assert r["qa_requires_review"]
    assert cached_path.read_bytes() == before
