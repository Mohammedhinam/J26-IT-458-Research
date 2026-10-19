"""Generated-only tests for registered-photo ROI v2 runtime integration."""

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.vision import photo_explanation, roi_ordinal_v2_live as live
from test_photo_explanation import generated_jpeg


def make_photo_runtime(raw: bytes, profile_sha: str, *, ready=True):
    runtime = SimpleNamespace(
        allowed_inputs={sha256(raw).hexdigest(): "generated"},
        profile_sha256=profile_sha,
        synthetic_only=True,
    )
    runtime.status = lambda: {"ready": ready}
    return runtime


def make_roi_runtime(raw: bytes, profile_sha: str, *, allowed=None):
    source_runtime = SimpleNamespace(
        allowed_inputs=allowed if allowed is not None else {sha256(raw).hexdigest(): "generated"},
        profile_sha256=profile_sha,
        synthetic_only=True,
    )
    return live.ROIV2PhotoRuntime(
        detector=object(), classifier=object(), device="cpu", fold=0,
        receipt={"zip_sha256": "a" * 64}, detector_sha256="b" * 64,
        classifier_sha256="c" * 64, photo_runtime=source_runtime,
        checkpoint_temp=None,
    )


def test_build_requires_the_existing_registered_photo_runtime(tmp_path, monkeypatch):
    return_zip = tmp_path / "returned.zip"
    return_zip.write_bytes(b"verified placeholder")
    monkeypatch.setattr(live, "_verified_checkpoint_pair",
                        lambda *_args: pytest.fail("Unregistered startup reached checkpoint extraction"))

    with pytest.raises(ValueError, match="photo runtime"):
        live.build_runtime(return_zip, make_photo_runtime(b"x", "1" * 64, ready=False))


def test_build_loads_only_verified_fold_zero_and_keeps_weights_available(tmp_path, monkeypatch):
    return_zip = tmp_path / "returned.zip"
    return_zip.write_bytes(b"verified placeholder")
    detector_path = tmp_path / "detector.pt"
    classifier_path = tmp_path / "classifier.pt"
    detector_path.write_bytes(b"detector")
    classifier_path.write_bytes(b"classifier")
    calls = []

    def verified_pair(path, fold, temporary_root):
        calls.append((path, fold, temporary_root))
        return detector_path, classifier_path, {"zip_sha256": "a" * 64}, "b" * 64, "c" * 64

    def load_models(detector, classifier, *, fold, device):
        return "detector-model", "crop-model", device or "cpu"

    monkeypatch.setattr(live, "_verified_checkpoint_pair", verified_pair)
    monkeypatch.setattr(live, "load_coral_roi_models", load_models)
    photo_runtime = SimpleNamespace(
        allowed_inputs={"d" * 64: "owner_supplied_nonstudy"},
        profile_sha256="e" * 64,
        synthetic_only=False,
        status=lambda: {"ready": True},
    )

    runtime = live.build_runtime(return_zip, photo_runtime, device="cpu")

    assert calls[0][0:2] == (return_zip, 0)
    assert Path(calls[0][2]).is_dir()
    assert runtime.status()["ready"] and runtime.status()["fold"] == 0
    assert runtime.status()["registered_count"] == 1
    assert detector_path.is_file() and classifier_path.is_file()


def test_registered_photo_returns_bounded_overlay_and_maximum_grade(monkeypatch):
    raw, profile_sha = generated_jpeg()
    runtime = make_roi_runtime(raw, profile_sha)
    checked = []

    def validate(payload, profile):
        checked.append((payload, profile))
        return object()

    def predict(detector, classifier, photo_path, *, device):
        assert Path(photo_path).read_bytes() == raw
        assert device == "cpu"
        return {
            "model_family": "roi_tooth_v2_coral",
            "image_mgi_grade": 3,
            "no_detection": False,
            "detections": [{"grade": 2, "detector_confidence": 0.91,
                            "xyxy": [1, 2, 20, 22],
                            "grade_probabilities": {"0": 0.05, "1": 0.15,
                                                     "2": 0.55, "3": 0.20, "4": 0.05}}],
        }

    monkeypatch.setattr(photo_explanation, "prepare_jpeg", validate)
    monkeypatch.setattr(live, "predict_coral_tooth_rois", predict)
    monkeypatch.setattr(live, "_render_preview", lambda *_args: "cG5n")

    result = runtime.predict(raw)

    assert checked == [(raw, profile_sha)]
    assert result["image_mgi_grade"] == 3
    assert result["detections"][0]["grade"] == 2
    assert result["overlay_png_base64"] == "cG5n"
    assert result["all_development_refit"] is False
    assert result["fold"] == 0 and result["device"] == "cpu"
    assert "input_photo" not in result


def test_unregistered_photo_is_rejected_before_image_decoder(monkeypatch):
    raw, profile_sha = generated_jpeg()
    runtime = make_roi_runtime(raw, profile_sha)
    monkeypatch.setattr(photo_explanation, "prepare_jpeg",
                        lambda *_args: pytest.fail("Unregistered photo was decoded"))

    with pytest.raises(ValueError, match="not in the source-confirmed"):
        runtime.predict(raw + b"changed")


def test_preview_is_bounded_and_has_research_watermark(tmp_path):
    from PIL import Image
    import base64
    import io

    photo_path = tmp_path / "large.jpg"
    Image.new("RGB", (2400, 1600), (90, 120, 150)).save(photo_path)
    rendered = live._render_preview(photo_path, {
        "detections": [{"grade": 2, "detector_confidence": 0.9,
                        "xyxy": [100, 100, 500, 500]}],
    })

    with Image.open(io.BytesIO(base64.b64decode(rendered))) as overlay:
        assert max(overlay.size) == live.MAX_OVERLAY_SIDE
        assert overlay.mode == "RGB"
        assert not overlay.info
