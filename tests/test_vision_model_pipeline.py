"""Synthetic-only tests; backend checks skip honestly if torch is unavailable."""

from copy import deepcopy
import numpy as np
from PIL import Image
import pytest

from src.vision import model_pipeline as vp


@pytest.mark.parametrize("shape,box", [((400, 200), (0, 56, 224, 112)),
                                       ((200, 400), (56, 0, 112, 224)),
                                       ((224, 224), (0, 0, 224, 224))])
def test_preprocessing_shape_colour_geometry_and_source_preservation(shape, box):
    image = Image.new("RGB", shape, (255, 80, 20))
    before = image.tobytes()
    prepared = vp.preprocess_rgb(image)
    assert prepared.normalized_chw.shape == (3, 224, 224)
    assert prepared.normalized_chw.dtype == np.float32
    assert prepared.valid_box == box
    np.testing.assert_array_equal(prepared.original_rgb, np.asarray(image))
    x, y, w, h = box
    expected = (np.array([255, 80, 20]) / 255 - vp.MEAN) / vp.STD
    np.testing.assert_allclose(prepared.normalized_chw[:, y, x], expected, atol=1e-6)
    if y:
        assert np.all(prepared.normalized_chw[:, :y] == 0)
    if x:
        assert np.all(prepared.normalized_chw[:, :, :x] == 0)
    assert image.tobytes() == before


@pytest.mark.parametrize("size", [0, -1, True, 2.5])
def test_invalid_preprocessing_size(size):
    with pytest.raises(ValueError):
        vp.preprocess_rgb(Image.new("RGB", (4, 4)), size)


@pytest.mark.parametrize("mode", ["L", "RGBA"])
def test_non_rgb_is_not_silently_accepted(mode):
    with pytest.raises(ValueError, match="RGB"):
        vp.preprocess_rgb(Image.new(mode, (4, 4)))


@pytest.mark.parametrize("index", range(5))
def test_output_mapping_preserves_all_five_mgi_definitions(index):
    logits = np.zeros(5)
    logits[index] = 1000
    result = vp.map_model_output(logits)
    assert result["mgi_schema_grade"] == index
    assert tuple(result["uncalibrated_softmax_scores"]) == (0, 1, 2, 3, 4)
    assert sum(result["uncalibrated_softmax_scores"].values()) == pytest.approx(1)


@pytest.mark.parametrize("logits", [[1, 2, 3, 4], [0, 0, 0, 0, np.nan], [[0]*5]])
def test_invalid_model_output(logits):
    with pytest.raises(ValueError, match="five finite"):
        vp.map_model_output(logits)


def test_factory_spec_sources_and_schema_without_model_download():
    assert vp.model_spec("resnet50")["weights"] == "ResNet50_Weights.IMAGENET1K_V2"
    assert vp.model_spec("efficientnet_b0")["weights"] == "EfficientNet_B0_Weights.IMAGENET1K_V1"
    assert vp.model_spec("resnet50")["mgi_grades"] == (0, 1, 2, 3, 4)
    with pytest.raises(ValueError):
        vp.model_spec("four_class_model")


def test_gradcam_algebra_is_class_specific():
    activation = np.zeros((2, 4, 4), dtype=np.float32)
    activation[0, 0, 0], activation[1, 3, 3] = 2, 3
    gradients = np.zeros_like(activation)
    gradients[0] = 1
    first, status = vp.aggregate_gradcam(activation, gradients)
    gradients[0], gradients[1] = 0, 1
    second, second_status = vp.aggregate_gradcam(activation, gradients)
    assert status == second_status == "ok"
    assert first[0, 0] == second[3, 3] == 1
    assert first[3, 3] == second[0, 0] == 0


@pytest.mark.parametrize("activation,gradient,status", [
    (np.zeros((1, 2, 2)), np.ones((1, 2, 2)), "no_positive_signal"),
    (np.ones((1, 2, 2)), -np.ones((1, 2, 2)), "no_positive_signal"),
    (np.ones((1, 2, 2)), np.ones((1, 2, 2)), "no_spatial_contrast"),
])
def test_zero_or_uniform_explanations_are_explicit(activation, gradient, status):
    cam, actual = vp.aggregate_gradcam(activation, gradient)
    assert actual == status and np.all(cam == 0)


def test_invalid_gradcam_evidence():
    with pytest.raises(ValueError):
        vp.aggregate_gradcam(np.zeros((2, 2)), np.zeros((2, 2)))
    with pytest.raises(ValueError):
        vp.aggregate_gradcam(np.full((1, 2, 2), np.nan), np.ones((1, 2, 2)))


def test_padding_is_removed_before_heatmap_returns_to_original_coordinates():
    prepared = vp.preprocess_rgb(Image.new("RGB", (16, 8)), 16)
    cam = np.ones((16, 16), dtype=np.float32)
    cam[4:12] = 0
    aligned = vp.align_cam(cam, prepared)
    assert aligned.shape == (8, 16) and np.all(aligned == 0)


def test_padding_only_signal_is_not_silently_reported_as_valid_explanation():
    prepared = vp.preprocess_rgb(Image.new("RGB", (16, 8), (80, 100, 120)), 16)
    activation = np.ones((1, 16, 16), dtype=np.float32)
    activation[:, 4:12] = 0
    result = vp.gradcam_views(activation, np.ones_like(activation), prepared)
    assert result["explanation_status"] == "padding_only_signal"
    np.testing.assert_array_equal(result["overlay"], prepared.original_rgb)


def test_alignment_preserves_spatial_location_and_render_preserves_original():
    prepared = vp.preprocess_rgb(Image.new("RGB", (8, 8), (20, 100, 180)), 8)
    cam = np.zeros((8, 8), dtype=np.float32)
    cam[1, 6] = 1
    aligned = vp.align_cam(cam, prepared)
    assert np.unravel_index(aligned.argmax(), aligned.shape) == (1, 6)
    before = prepared.original_rgb.copy()
    views = vp.render_gradcam(prepared.original_rgb, aligned)
    assert all(value.shape == (8, 8, 3) and value.dtype == np.uint8 for value in views.values())
    np.testing.assert_array_equal(views["original"], before)
    np.testing.assert_array_equal(views["overlay"][0, 0], before[0, 0])
    np.testing.assert_array_equal(prepared.original_rgb, before)


def test_zero_map_never_tints_original():
    original = np.full((3, 5, 3), 100, dtype=np.uint8)
    views = vp.render_gradcam(original, np.zeros((3, 5)))
    np.testing.assert_array_equal(views["overlay"], original)
    with pytest.raises(ValueError):
        vp.render_gradcam(original, np.zeros((5, 3)))
    with pytest.raises(ValueError):
        vp.render_gradcam(original, np.zeros((3, 5)), alpha=2)


def manifest():
    return {"status": "approved", "approval": {"qualified_reviewer": "SYNTHETIC TEST ONLY", "date": "test",
                                                "labels_approved": True, "split_approved": True},
            "records": [{"image_path": "synthetic/train", "analysis_split": "Training", "content_group_id": "a",
                         "label_status": "verified", "mgi_grade": 2},
                        {"image_path": "synthetic/test", "analysis_split": "Test", "content_group_id": "b",
                         "label_status": "verified", "mgi_grade": 4}]}


def test_gate_returns_training_metadata_only_and_cannot_create_approval():
    value = manifest()
    before = deepcopy(value)
    assert [r["image_path"] for r in vp.approved_training_records(value)] == ["synthetic/train"]
    assert value == before
    with pytest.raises(ValueError, match="qualified-approved"):
        vp.approved_training_records({"status": "PROPOSED", "training_ready_manifest": False})


@pytest.mark.parametrize("problem", ["same_group", "unverified", "invalid_grade", "missing_signoff"])
def test_manifest_gate_rejects_unapproved_or_leaky_evidence(problem):
    value = manifest()
    if problem == "same_group":value["records"][1]["content_group_id"] = "a"
    elif problem == "unverified":value["records"][0]["label_status"] = "needs_review"
    elif problem == "invalid_grade":value["records"][0]["mgi_grade"] = 5
    else:value["approval"]["split_approved"] = False
    with pytest.raises(ValueError):
        vp.approved_training_records(value)


@pytest.mark.parametrize("architecture", ["resnet50", "efficientnet_b0"])
def test_actual_backend_model_shapes_and_targets_no_download(architecture):
    torch = pytest.importorskip("torch", reason="torch unavailable; no installation authorized")
    pytest.importorskip("torchvision", reason="torchvision unavailable")
    bundle = vp.make_model(architecture, pretrained=False)
    with torch.no_grad():
        logits = bundle["model"](torch.zeros(1, 3, 224, 224))
    assert tuple(logits.shape) == (1, 5)
    assert bundle["cam_layer"] in list(bundle["model"].modules())
    assert not bundle["mgi_head_trained"] and not bundle["five_class_validity_established"]


@pytest.mark.parametrize("architecture", ["resnet50", "efficientnet_b0"])
def test_uncached_pretrained_weights_never_download_implicitly(architecture, tmp_path, monkeypatch):
    torch = pytest.importorskip("torch", reason="torch unavailable")
    torchvision = pytest.importorskip("torchvision", reason="torchvision unavailable")
    monkeypatch.setattr(torch.hub, "get_dir", lambda: str(tmp_path))
    def forbidden(**kwargs):pytest.fail("Uncached weights must be blocked before model construction")
    monkeypatch.setattr(torchvision.models, architecture, forbidden)
    with pytest.raises(FileNotFoundError, match="download is blocked"):
        vp.make_model(architecture)


def toy_model(torch):
    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = torch.nn.Conv2d(3, 2, 1, bias=False)
            with torch.no_grad():
                self.conv.weight.zero_()
                self.conv.weight[0, 0, 0, 0] = 1
                self.conv.weight[1, 1, 0, 0] = 1
        def forward(self, inputs):
            pooled = self.conv(inputs).relu().mean(dim=(2, 3))
            a, b = pooled[:, :1], pooled[:, 1:2]
            return torch.cat([a, b, -a, a+b, b*0], dim=1)
    return Toy()


def test_actual_autograd_class_consistency_frozen_backbone_and_hook_cleanup():
    torch = pytest.importorskip("torch", reason="torch unavailable; autograd not verified here")
    model = toy_model(torch)
    for p in model.parameters():p.requires_grad_(False)
    model.train()
    model.conv.eval()
    before = {key: value.clone() for key, value in model.state_dict().items()}
    states = [m.training for m in model.modules()]
    image = Image.new("RGB", (8, 8), (120, 110, 100))
    image.putpixel((1, 1), (255, 0, 0));image.putpixel((6, 6), (0, 255, 0))
    prepared = vp.preprocess_rgb(image, 8)
    with torch.no_grad():first = vp.class_gradcam(model, model.conv, prepared, 0)
    second = vp.class_gradcam(model, model.conv, prepared, 1)
    assert first["explained_mgi_schema_grade"] == 0 and second["explained_mgi_schema_grade"] == 1
    assert np.unravel_index(first["cam"].argmax(), (8, 8)) == (1, 1)
    assert np.unravel_index(second["cam"].argmax(), (8, 8)) == (6, 6)
    assert not model.conv._forward_hooks and states == [m.training for m in model.modules()]
    assert all(torch.equal(value, model.state_dict()[key]) for key, value in before.items())
    assert all(p.grad is None for p in model.parameters())


def test_actual_autograd_no_positive_signal_and_inference_guard():
    torch = pytest.importorskip("torch", reason="torch unavailable")
    model = toy_model(torch)
    prepared = vp.preprocess_rgb(Image.new("RGB", (8, 8), (255, 255, 255)), 8)
    result = vp.class_gradcam(model, model.conv, prepared, 4)
    assert result["explanation_status"] == "no_positive_signal"
    with torch.inference_mode(), pytest.raises(RuntimeError, match="outside"):
        vp.class_gradcam(model, model.conv, prepared)
