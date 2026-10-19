"""Generated-only checks for the isolated YOLO ROI v1 upload runtime."""

import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from src.vision import roi_tooth_v1_live as live
from test_photo_explanation import generated_jpeg


def make_return_bundle(tmp_path):
    archive_path = tmp_path / "roi_tooth_v1_colab_return.zip"
    payloads = {
        "experiment_complete.json": json.dumps({
            "status": "all_requested_folds_completed", "test_split_used": False,
        }).encode(),
        "fold_00/detector_last.pt": b"generated-detector",
        "fold_00/crop_classifier_last.pt": b"generated-classifier",
    }
    lines = ["path,bytes,sha256"]
    for name in ("fold_00/detector_last.pt", "fold_00/crop_classifier_last.pt"):
        content = payloads[name]
        lines.append(f"{name},{len(content)},{hashlib.sha256(content).hexdigest()}")
    payloads["return_integrity_manifest.csv"] = ("\n".join(lines) + "\n").encode()
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in payloads.items():
            archive.writestr(name, content)
    digest = live._sha256_file(archive_path)
    receipt = {
        "status": "verified_complete",
        "return_zip": {"sha256": digest},
    }
    (tmp_path / "colab_verification_summary_v1.json").write_text(json.dumps(receipt))
    return archive_path


def test_verified_pair_checks_receipt_and_manifest_before_extraction(tmp_path):
    archive = make_return_bundle(tmp_path)
    root = tmp_path / "extracted"
    detector, classifier, receipt, detector_sha, classifier_sha = live._verified_checkpoint_pair(archive, root)
    assert detector.read_bytes() == b"generated-detector"
    assert classifier.read_bytes() == b"generated-classifier"
    assert receipt["status"] == "verified_complete"
    assert detector_sha == hashlib.sha256(detector.read_bytes()).hexdigest()
    assert classifier_sha == hashlib.sha256(classifier.read_bytes()).hexdigest()


def test_changed_archive_is_rejected_before_checkpoint_extraction(tmp_path):
    archive = make_return_bundle(tmp_path)
    with archive.open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="does not match"):
        live._verified_checkpoint_pair(archive, tmp_path / "extracted")


def test_build_loads_only_verified_fold_zero(tmp_path, monkeypatch):
    archive = make_return_bundle(tmp_path)
    calls = []

    def load_models(detector, classifier, device=None):
        calls.append((Path(detector).name, Path(classifier).name, device))
        return object(), object(), device or "cpu"

    monkeypatch.setattr(live, "load_roi_checkpoint_models", load_models)
    runtime = live.build_runtime(archive, device="cpu")
    assert runtime.status()["ready"]
    assert runtime.status()["fold"] == 0
    assert runtime.status()["image_level_oof_accuracy"] == pytest.approx(0.6073529411764705)
    assert calls == [("detector_last.pt", "crop_classifier_last.pt", "cpu")]


def test_upload_uses_normalized_srgb_temporary_image_and_marks_score_types(monkeypatch):
    raw, _ = generated_jpeg()
    runtime = live.ROIV1PhotoRuntime(
        detector=object(), classifier=object(), device="cpu",
        receipt={"return_zip": {"sha256": "a" * 64}},
        detector_sha="b" * 64, classifier_sha="c" * 64, temp=object(),
    )
    seen = []

    def predict(detector, photo_path, *, crop_classifier, device):
        photo_path = Path(photo_path)
        with Image.open(photo_path) as image:
            seen.append((photo_path.suffix, image.mode, image.size, image.info.get("icc_profile")))
        return {
            "model_family": "roi_tooth_v1", "image_mgi_grade": 2,
            "no_detection": False,
            "detections": [{"grade": 1, "confidence": 0.88, "xyxy": [2, 3, 20, 22]}],
        }

    monkeypatch.setattr(live, "predict_tooth_rois", predict)
    monkeypatch.setattr(live, "_render_overlay", lambda *_args: "cG5n")
    result = runtime.predict_upload(raw, "image/jpeg")

    assert seen and seen[0][0:2] == (".png", "RGB")
    assert seen[0][3] is None
    assert result["image_mgi_grade"] == 2
    assert result["detections"][0]["detector_confidence"] == 0.88
    assert result["input_format"] == "JPEG"
    assert result["photo_saved"] is False
    assert result["all_development_refit"] is False
    assert result["overlay_png_base64"] == "cG5n"

