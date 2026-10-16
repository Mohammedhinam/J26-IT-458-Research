"""Generated saved-view ZIPs only; no real dental image or model inference."""

import hashlib
import json
import struct
import zipfile
import zlib

import pytest

from src.vision.saved_pilot_demo import CASE_IDS, VIEWS, check_preview_png, prepare_saved_examples


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)


def generated_png(metadata=False):
    header = chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
    extra = chunk(b"tEXt", b"secret\x00generated") if metadata else b""
    return b"\x89PNG\r\n\x1a\n" + header + extra + chunk(b"IDAT", zlib.compress(b"\x00" + b"\x20\x30\x40" * 2 + b"\x00" + b"\x50\x60\x70" * 2)) + chunk(b"IEND", b"")


def generated_archive(tmp_path, bad_hash=False, split="Validation", metadata=False):
    files = {f"gradcam/Validation_{case}/{view}.png": generated_png(metadata) for case in CASE_IDS for view in VIEWS}
    predictions = {"grades": [1, 2, 3, 4], "records": [
        {"source_record_id": "Validation/" + case, "original_split": split,
         "provisional_mgi_grade": 3, "predicted_mgi_grade": 3,
         "probabilities_mgi1_to4": [0.1, 0.1, 0.7, 0.1]} for case in CASE_IDS]}
    files["validation_predictions_best.json"] = json.dumps(predictions).encode()
    hashes = {name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()}
    if bad_hash:
        hashes["gradcam/Validation_00733/original.png"] = "0" * 64
    archive = tmp_path / "generated.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for name, payload in files.items():
            output.writestr(name, payload)
        output.writestr("results_file_hashes.json", json.dumps(hashes))
        output.writestr("best.pt", b"must-never-be-opened")
    return archive, hashlib.sha256(archive.read_bytes()).hexdigest()


def test_png_structure_and_metadata_rejection():
    assert check_preview_png(generated_png()) == [2, 2]
    for payload in (generated_png(True), generated_png()[:-1], generated_png() + b"extra", b"wrong"):
        with pytest.raises(ValueError):
            check_preview_png(payload)


def test_only_nine_saved_views_are_copied_without_checkpoints(tmp_path, monkeypatch):
    archive, digest = generated_archive(tmp_path)
    original = archive.read_bytes()
    real_read = zipfile.ZipFile.read
    allowed = {"results_file_hashes.json", "validation_predictions_best.json"} | {
        f"gradcam/Validation_{case}/{view}.png" for case in CASE_IDS for view in VIEWS}

    def guarded(self, name, *args, **kwargs):
        assert name in allowed
        return real_read(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "read", guarded)
    out = tmp_path / "views"
    manifest = prepare_saved_examples(archive, out, digest)
    assert len(manifest["files"]) == 9 and len(list(out.iterdir())) == 10
    assert archive.read_bytes() == original
    assert all((out / name).read_bytes() == generated_png() for name in manifest["files"])
    with pytest.raises(FileExistsError):
        prepare_saved_examples(archive, out, digest)


@pytest.mark.parametrize("issue", ["archive_hash", "payload_hash", "Test", "metadata"])
def test_unsafe_archive_stops_before_output(tmp_path, issue):
    archive, digest = generated_archive(tmp_path, bad_hash=issue == "payload_hash",
                                        split="Test" if issue == "Test" else "Validation", metadata=issue == "metadata")
    with pytest.raises(ValueError):
        prepare_saved_examples(archive, tmp_path / "output", "0" * 64 if issue == "archive_hash" else digest)
    assert not (tmp_path / "output").exists()
