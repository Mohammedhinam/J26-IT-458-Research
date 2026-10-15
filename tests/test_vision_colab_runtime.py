"""Synthetic, weights=None architecture smoke checks for the Colab workflow."""

import numpy as np
from PIL import Image
import pytest

from src.vision import model_pipeline as vp


@pytest.mark.parametrize("architecture", ["resnet50", "efficientnet_b0"])
def test_each_architecture_gradcam_alignment_and_frozen_state(architecture):
    torch = pytest.importorskip("torch", reason="Requires the approved Colab runtime")
    pytest.importorskip("torchvision", reason="Requires compatible torchvision")
    torch.manual_seed(42)
    bundle = vp.make_model(architecture, pretrained=False, allow_download=False, freeze_backbone=True)
    model, target = bundle["model"], bundle["cam_layer"]
    expected_target = model.layer4[-1] if architecture == "resnet50" else model.features[-1]
    assert target is expected_target and bundle["loaded_weights"] is None
    assert not bundle["mgi_head_trained"] and not bundle["five_class_validity_established"]
    head = model.fc if architecture == "resnet50" else model.classifier
    head_parameters = {id(p) for p in head.parameters()}
    assert all(p.requires_grad == (id(p) in head_parameters) for p in model.parameters())

    # Procedural colour pattern only; no image files, clinical labels or manifests.
    pixels = np.zeros((72, 120, 3), dtype=np.uint8)
    pixels[..., 0] = np.arange(120, dtype=np.uint8)[None, :] * 2
    pixels[..., 1] = np.arange(72, dtype=np.uint8)[:, None] * 3
    pixels[..., 2] = 150
    prepared = vp.preprocess_rgb(Image.fromarray(pixels))
    with torch.no_grad():
        logits = model(torch.from_numpy(prepared.normalized_chw[None]))
    assert tuple(logits.shape) == (1, 5) and torch.isfinite(logits).all()

    # Nonuniform flags expose accidental state resets; Grad-CAM must restore them all.
    model.train()
    target.eval()
    states = [m.training for m in model.modules()]
    original_weights_buffers = {name: value.detach().clone() for name, value in model.state_dict().items()}
    original_hook_count = len(target._forward_hooks)
    feature_gradients = []
    def capture_gradient(module, inputs, output):
        output.register_hook(lambda gradient: feature_gradients.append(gradient.detach().clone()))
    inspection_hook = target.register_forward_hook(capture_gradient)
    try:
        result = vp.class_gradcam(model, target, prepared, class_index=2)
        assert len(target._forward_hooks) == original_hook_count + 1  # Only our inspection hook remains.
    finally:
        inspection_hook.remove()
    assert len(target._forward_hooks) == original_hook_count
    assert states == [m.training for m in model.modules()]
    assert len(feature_gradients) == 1 and torch.isfinite(feature_gradients[0]).all()
    assert feature_gradients[0].abs().sum() > 0
    assert all(parameter.grad is None for parameter in model.parameters())
    assert all(torch.equal(value, model.state_dict()[name]) for name, value in original_weights_buffers.items())
    assert result["explained_mgi_schema_grade"] == 2
    assert result["cam"].shape == (72, 120) and np.isfinite(result["cam"]).all()
    assert 0 <= result["cam"].min() <= result["cam"].max() <= 1
    assert all(result[key].shape == (72, 120, 3) for key in ["original", "heatmap", "overlay"])
    np.testing.assert_array_equal(result["original"], pixels)
    assert result["explanation_status"] in {"ok", "no_positive_signal", "no_spatial_contrast", "padding_only_signal"}
