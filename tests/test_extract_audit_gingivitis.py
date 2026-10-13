"""Focused safety/content tests with synthetic files; published data is untouched."""

import subprocess
import tarfile
from pathlib import Path

import pytest

from src.vision.extract_audit_gingivitis import (
    DISK_RESERVE, MAX_FILE_BYTES, MAX_TOTAL_BYTES, duplicate_groups, extract_new,
    image_evidence, integrity_read, validate_entries, verify_extraction, yolo_evidence,
    identity_metadata_review,
    flag_duplicate_caption_conflicts,
)
from src.vision.audit_gingivitis import EXPECTED


def synthetic_entries():
    return [{"name": f"Dataset/{split}/Images/{i:05}.jpg", "type": "-", "size": 1}
            for split, count in EXPECTED.items() for i in range(count)]


def test_size_and_count_limits():
    entries = synthetic_entries()
    assert validate_entries(entries, MAX_TOTAL_BYTES + DISK_RESERVE) == 1096
    with pytest.raises(ValueError, match="free-space"):
        validate_entries(entries, DISK_RESERVE)
    with pytest.raises(ValueError, match="entry counts"):
        validate_entries(entries[:-1], MAX_TOTAL_BYTES + DISK_RESERVE)
    entries[0]["size"] = MAX_FILE_BYTES + 1
    with pytest.raises(ValueError, match="Member size"):
        validate_entries(entries, MAX_TOTAL_BYTES + DISK_RESERVE)


@pytest.mark.parametrize("name,kind", [
    ("/outside.jpg", "-"), ("Dataset/../outside.jpg", "-"),
    ("Dataset/Test/Images/link.jpg", "l"), ("Dataset/Test/Images/pipe.jpg", "p"),
    ("Dataset/Test/Images/C:\\outside.jpg", "-"),
    ("Dataset/Test/Images/foo.jpg link to /outside", "-"),
])
def test_reject_paths_links_and_special_files(name, kind):
    entries = synthetic_entries() + [{"name": name, "type": kind, "size": 1}]
    with pytest.raises(ValueError):
        validate_entries(entries, MAX_TOTAL_BYTES + DISK_RESERVE)


def test_duplicate_paths_case_collision_and_total_limit():
    entries = synthetic_entries()
    with pytest.raises(ValueError, match="duplicate"):
        validate_entries(entries + [entries[0]], MAX_TOTAL_BYTES + DISK_RESERVE)
    collision = {**entries[0], "name": entries[0]["name"].upper()}
    with pytest.raises(ValueError, match="duplicate"):
        validate_entries(entries + [collision], MAX_TOTAL_BYTES + DISK_RESERVE)
    for entry in entries:
        entry["size"] = MAX_FILE_BYTES
    with pytest.raises(ValueError, match="size or"):
        validate_entries(entries, 1000 * MAX_TOTAL_BYTES)


def test_existing_staging_is_never_overwritten(tmp_path):
    staging = tmp_path / "existing"
    staging.mkdir()
    original = staging / "keep.txt"
    original.write_text("preserve")
    with pytest.raises(FileExistsError):
        extract_new(tmp_path / "unused.rar", staging, [])
    assert original.read_text() == "preserve"


def test_verify_extracted_paths_sizes_and_links(tmp_path):
    path = tmp_path / "Dataset/Test/Images/test.jpg"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"test")
    entries = [{"name": "Dataset/Test/Images/test.jpg", "type": "-", "size": 4}]
    assert verify_extraction(tmp_path, entries) == {entries[0]["name"]: 4}
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="differ"):
        verify_extraction(tmp_path, entries)
    path.unlink()
    path.symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError, match="symlink"):
        verify_extraction(tmp_path, entries)


def test_full_integrity_stream_and_overflow(tmp_path):
    payload = tmp_path / "payload.txt"
    payload.write_bytes(b"synthetic")
    archive = tmp_path / "synthetic.tar"
    with tarfile.open(archive, "w") as handle:
        handle.add(payload, arcname="payload.txt")
    assert integrity_read(archive, 9, ["payload.txt"]) == 9
    with pytest.raises(ValueError, match="exceeded"):
        integrity_read(archive, 8, ["payload.txt"])


def test_image_decode_fingerprints_and_corruption(tmp_path):
    from PIL import Image

    first, second = tmp_path / "first.png", tmp_path / "second.png"
    image = Image.new("RGB", (16, 12), (100, 50, 20))
    image.save(first, compress_level=0)
    image.save(second, compress_level=9)
    a, b = image_evidence(first), image_evidence(second)
    assert a["decode_ok"] and (a["width"], a["height"], a["mode"]) == (16, 12, "RGB")
    assert a["sha256"] != b["sha256"]
    assert a["pixel_sha256"] == b["pixel_sha256"]
    assert image_evidence(first) == a
    first.write_bytes(b"not an image")
    with pytest.raises(Exception):
        image_evidence(first)


def test_duplicate_groups_preserve_membership():
    rows = [{"split": "Training", "image_path": "a.jpg", "sha256": "same"},
            {"split": "Test", "image_path": "b.jpg", "sha256": "same"}]
    assert duplicate_groups(rows, "sha256") == [{"key": "sha256", "fingerprint": "same",
                                                "cross_split": True, "paths": ["a.jpg", "b.jpg"]}]
    assert [r["split"] for r in rows] == ["Training", "Test"]


def test_raw_yolo_codes_are_not_assigned_as_targets(tmp_path):
    path = tmp_path / "annotation.txt"
    path.write_text("0 0.5 0.5 0.9 0.9\n2 0.5 0.5 0.1 0.1\n6 0.5 0.5 0.1 0.1\n")
    counts, issues = yolo_evidence(path)
    assert dict(counts) == {0: 1, 2: 1, 6: 1}
    assert issues == ["annotation_roi_count_review", "annotation_tooth_count_review"]
    path.write_text("9 0.5 0.5 0.1 0.1\n2 nan 0.5 0.1 0.1\n")
    assert "invalid_annotation_row" in yolo_evidence(path)[1]


def test_regular_member_selection_and_real_new_extraction(tmp_path, monkeypatch):
    source = tmp_path / "source/Dataset/Test/Images/test.jpg"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic")
    archive = tmp_path / "synthetic.tar"
    with tarfile.open(archive, "w") as handle:
        handle.add(tmp_path / "source/Dataset", arcname="Dataset")
    member = "Dataset/Test/Images/test.jpg"
    observed = []
    original = subprocess.Popen

    def tracked_popen(arguments, **kwargs):
        observed.append(arguments)
        return original(arguments, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", tracked_popen)
    assert integrity_read(archive, 9, [member]) == 9
    entries = [{"name": "Dataset", "type": "d", "size": 0},
               {"name": member, "type": "-", "size": 9}]
    staging = tmp_path / "new"
    extract_new(archive, staging, entries)
    assert (staging / member).read_bytes() == b"synthetic"
    assert all(arguments[-1] == member for arguments in observed)


def test_hardlink_description_cannot_pass_as_regular_filename():
    entries = synthetic_entries()
    entries[0]["name"] = "Dataset/Training/Images/foo.jpg link to bar.jpg"
    with pytest.raises(ValueError, match="Unsafe"):
        validate_entries(entries, MAX_TOTAL_BYTES + DISK_RESERVE)


def test_metadata_is_not_automatically_a_participant_id(tmp_path):
    from PIL import Image

    image = Image.new("RGB", (16, 12))
    exif = Image.Exif()
    exif[270] = "synthetic description"
    image.save(tmp_path / "test.jpg", exif=exif)
    records = identity_metadata_review(tmp_path, [{"image_path": "test.jpg", "split": "Test"}])
    assert records[0]["ImageDescription_nonempty"]
    assert records[0]["participant_id"] == ""
    assert "synthetic description" not in str(records)


def test_blank_annotation_lines_do_not_create_invalid_labels(tmp_path):
    path = tmp_path / "annotation.txt"
    valid = "0 0.5 0.5 0.9 0.9\n1 0.5 0.5 0.9 0.9\n" + "3 0.5 0.5 0.1 0.1\n" * 12
    path.write_text(valid)
    first = yolo_evidence(path)
    path.write_text("\n" + valid + "   \n")
    assert yolo_evidence(path) == first
    assert first[1] == []


def test_duplicate_caption_disagreement_is_not_relabelled():
    rows = [{"image_path": "a.jpg", "split": "Training", "mgi_max": 3, "caption_maxima": [3, 3, 3],
             "status": "provisional", "issues": []},
            {"image_path": "b.jpg", "split": "Test", "mgi_max": 4, "caption_maxima": [4, 4, 4],
             "status": "provisional", "issues": []}]
    result = {"manifest": rows, "anomalies": [],
              "duplicate_groups": [{"key": "sha256", "paths": ["a.jpg", "b.jpg"]}]}
    flag_duplicate_caption_conflicts(result)
    assert [r["mgi_max"] for r in rows] == [3, 4]
    assert all(r["status"] == "needs_review" for r in rows)
    assert len(result["anomalies"]) == 2
