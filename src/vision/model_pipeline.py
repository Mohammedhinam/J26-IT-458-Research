"""Vision building blocks only: RGB, five MGI outputs and class-specific Grad-CAM.

No training loop, dataset loader, automatic downloads or clinical validity claim.
"""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
from PIL import Image


MGI_GRADES = (0, 1, 2, 3, 4)
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
MODEL_SPECS = {
    "resnet50": {"weights": "ResNet50_Weights.IMAGENET1K_V2", "cam_layer": "layer4[-1]"},
    "efficientnet_b0": {"weights": "EfficientNet_B0_Weights.IMAGENET1K_V1", "cam_layer": "features[-1]"},
}


@dataclass(frozen=True)
class RGBInput:
    original_rgb: np.ndarray
    normalized_chw: np.ndarray
    valid_box: tuple  # left, top, resized width, resized height in the square input.


def preprocess_rgb(image, size=224):
    """Resize without cropping; save letterbox geometry for inverse CAM alignment."""
    if not isinstance(image, Image.Image) or image.mode != "RGB":
        raise ValueError("An explicit RGB PIL image is required; no implicit grayscale conversion")
    if type(size) is not int or size <= 0:
        raise ValueError("Input size must be a positive integer")
    original = np.asarray(image, dtype=np.uint8).copy()
    width, height = image.size
    scale = min(size / width, size / height)
    resized_width = max(1, min(size, round(width * scale)))
    resized_height = max(1, min(size, round(height * scale)))
    left, top = (size - resized_width) // 2, (size - resized_height) // 2
    resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
    # Mean-colour padding becomes zero after normalisation, not fabricated tissue.
    canvas = np.broadcast_to(MEAN, (size, size, 3)).copy()
    canvas[top:top + resized_height, left:left + resized_width] = np.asarray(resized, dtype=np.float32) / 255
    normalized = ((canvas - MEAN) / STD).transpose(2, 0, 1).copy()
    return RGBInput(original, normalized, (left, top, resized_width, resized_height))


def model_spec(architecture):
    if architecture not in MODEL_SPECS:
        raise ValueError("Supported architectures: resnet50, efficientnet_b0")
    return {**MODEL_SPECS[architecture], "mgi_grades": MGI_GRADES, "input_size": 224,
            "preprocessing": "RGB aspect-preserving letterbox, ImageNet mean/std"}


def _torch():
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("torch is unavailable; use an approved Vision runtime. No automatic installation.") from error
    return torch


def make_model(architecture, pretrained=True, allow_download=False, freeze_backbone=True):
    """Replace the ImageNet head with five fresh outputs; never call this trained MGI."""
    spec = model_spec(architecture)
    torch = _torch()
    try:
        from torchvision import models
    except ImportError as error:
        raise RuntimeError("Compatible torchvision is required in the approved Vision runtime") from error
    weight_type, weight_name = spec["weights"].split(".")
    weights = getattr(getattr(models, weight_type), weight_name) if pretrained else None
    if weights is not None and not allow_download:
        filename = Path(urlparse(weights.url).path).name
        checkpoint = Path(torch.hub.get_dir()) / "checkpoints" / filename
        if not checkpoint.is_file():
            raise FileNotFoundError("Pretrained checkpoint is not cached; implicit download is blocked")
    model = getattr(models, architecture)(weights=weights, progress=False)
    if architecture == "resnet50":
        model.fc = torch.nn.Linear(model.fc.in_features, len(MGI_GRADES))
        head, target = model.fc, model.layer4[-1]
    else:
        model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, len(MGI_GRADES))
        head, target = model.classifier, model.features[-1]
    if freeze_backbone:
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        for parameter in head.parameters():
            parameter.requires_grad_(True)
    model.eval()
    return {"model": model, "cam_layer": target, "spec": spec,
            "loaded_weights": spec["weights"] if pretrained else None,
            "mgi_head_trained": False, "five_class_validity_established": False}


def map_model_output(logits):
    """Keep five schema outputs even though current dataset has no supported MGI 0."""
    values = np.asarray(logits, dtype=np.float64)
    if values.shape != (5,) or not np.isfinite(values).all():
        raise ValueError("Expected five finite logits in MGI order 0,1,2,3,4")
    exp = np.exp(values - values.max())
    scores = exp / exp.sum()
    index = int(values.argmax())
    return {"model_class_index": index, "mgi_schema_grade": MGI_GRADES[index],
            "uncalibrated_softmax_scores": {grade: float(scores[i]) for i, grade in enumerate(MGI_GRADES)}}


def aggregate_gradcam(activations, gradients):
    """Spatially average class gradients, weight channels, then keep positive evidence."""
    activation = np.asarray(activations, dtype=np.float32)
    gradient = np.asarray(gradients, dtype=np.float32)
    if activation.ndim != 3 or activation.shape != gradient.shape or not activation.size:
        raise ValueError("Activation and gradient arrays must share nonempty C,H,W shape")
    if not np.isfinite(activation).all() or not np.isfinite(gradient).all():
        raise ValueError("Non-finite Grad-CAM evidence")
    channel_weights = gradient.mean(axis=(1, 2))
    cam = np.maximum((channel_weights[:, None, None] * activation).sum(axis=0), 0)
    positive_signal = bool(cam.max() > 0)
    cam = cam - cam.min()
    scale = float(cam.max())
    if scale <= np.finfo(np.float32).eps:
        return np.zeros_like(cam), "no_spatial_contrast" if positive_signal else "no_positive_signal"
    return cam / scale, "ok"


def align_cam(cam, prepared):
    """Remove padding in input coordinates before restoring original image dimensions."""
    values = np.asarray(cam, dtype=np.float32)
    if values.ndim != 2 or not values.size or not np.isfinite(values).all():
        raise ValueError("CAM must be a nonempty finite 2D map")
    if values.min() < 0 or values.max() > 1:
        raise ValueError("CAM must be normalised to [0,1]")
    _, height, width = prepared.normalized_chw.shape
    left, top, valid_width, valid_height = prepared.valid_box
    if not (0 <= left < width and 0 <= top < height and valid_width > 0 and valid_height > 0
            and left + valid_width <= width and top + valid_height <= height):
        raise ValueError("Invalid letterbox geometry")
    view = Image.fromarray(values).resize((width, height), Image.Resampling.BILINEAR)
    view = view.crop((left, top, left + valid_width, top + valid_height))
    original_height, original_width = prepared.original_rgb.shape[:2]
    return np.clip(np.asarray(view.resize((original_width, original_height), Image.Resampling.BILINEAR)), 0, 1).copy()


def render_gradcam(original_rgb, aligned_cam, alpha=0.45):
    """Display pseudocolour separately; leave original pixels unchanged."""
    original = np.asarray(original_rgb)
    cam = np.asarray(aligned_cam, dtype=np.float32)
    if original.dtype != np.uint8 or original.ndim != 3 or original.shape[2] != 3:
        raise ValueError("Original view must be uint8 RGB")
    if cam.shape != original.shape[:2] or not np.isfinite(cam).all() or cam.min() < 0 or cam.max() > 1:
        raise ValueError("Aligned CAM must match the original H,W and lie in [0,1]")
    if not np.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("Overlay alpha must lie in [0,1]")
    colours = np.stack([np.clip(1.5 - np.abs(4 * cam - centre), 0, 1) for centre in (3, 2, 1)], axis=-1)
    heatmap = np.rint(colours * 255).astype(np.uint8)
    # Zero CAM contributes no overlay, rather than tinting irrelevant/unsupported pixels.
    opacity = (alpha * cam)[..., None]
    overlay = np.rint(original * (1 - opacity) + heatmap * opacity).astype(np.uint8)
    return {"original": original.copy(), "heatmap": heatmap, "overlay": overlay}


def gradcam_views(activations, gradients, prepared, alpha=0.45):
    """Numerically tested image views; report attention lost entirely to padding."""
    cam, status = aggregate_gradcam(activations, gradients)
    aligned = align_cam(cam, prepared)
    if status == "ok" and aligned.max() <= np.finfo(np.float32).eps:
        status = "padding_only_signal"
    return {"cam": aligned, "explanation_status": status,
            **render_gradcam(prepared.original_rgb, aligned, alpha)}


def class_gradcam(model, target_layer, prepared, class_index=None, alpha=0.45):
    """One synthetic/uploaded image and one class; gradients do not update weights."""
    torch = _torch()
    if torch.is_inference_mode_enabled():
        raise RuntimeError("Grad-CAM requires autograd; call outside torch.inference_mode")
    if class_index is not None and (type(class_index) is not int or class_index not in MGI_GRADES):
        raise ValueError("Class index must be an integer in 0..4")
    states = [(module, module.training) for module in model.modules()]
    captured = []
    handle = target_layer.register_forward_hook(lambda module, inputs, output: captured.append(output))
    try:
        model.eval()
        parameter = next(model.parameters(), None)
        device = parameter.device if parameter is not None else "cpu"
        with torch.enable_grad():
            # Input gradients allow explanations even when the pretrained backbone is frozen.
            inputs = torch.tensor(prepared.normalized_chw[None], dtype=torch.float32, device=device,
                                  requires_grad=True)
            logits = model(inputs)
            if tuple(logits.shape) != (1, 5):
                raise ValueError("Model must return one row with five MGI logits")
            mapped = map_model_output(logits.detach().cpu().numpy()[0])
            selected = mapped["model_class_index"] if class_index is None else class_index
            if len(captured) != 1 or captured[0].ndim != 4 or captured[0].shape[0] != 1:
                raise ValueError("Target layer must yield one N,C,H,W feature tensor")
            gradients = torch.autograd.grad(logits[0, selected], captured[0])[0]
            views = gradcam_views(captured[0].detach().cpu().numpy()[0],
                                  gradients.detach().cpu().numpy()[0], prepared, alpha)
        return {**mapped, "explained_mgi_schema_grade": MGI_GRADES[selected], **views,
                "meaning": "Class-specific model attention, not clinical inflammation boundaries"}
    finally:
        handle.remove()
        for module, training in states:
            module.training = training


def approved_training_records(manifest):
    """Interface gate only; cannot authenticate a reviewer or grant approval itself."""
    approval = manifest.get("approval", {})
    if (manifest.get("status") != "approved" or approval.get("labels_approved") is not True
            or approval.get("split_approved") is not True or not approval.get("qualified_reviewer")
            or not approval.get("date")):
        raise ValueError("Separately qualified-approved labels and duplicate-safe split manifest required")
    records = manifest.get("records", [])
    if not records or len({r["image_path"] for r in records}) != len(records):
        raise ValueError("Manifest must preserve distinct source records")
    group_splits = {}
    for row in records:
        group = row.get("content_group_id")
        split = row.get("analysis_split")
        grade = row.get("mgi_grade")
        if (not group or split not in {"Training", "Validation", "Test"}
                or type(grade) is not int or grade not in MGI_GRADES or row.get("label_status") != "verified"):
            raise ValueError("Unverified label/group/split evidence in manifest")
        if group in group_splits and group_splits[group] != split:
            raise ValueError("Content group crosses analysis splits")
        group_splits[group] = split
    training = [dict(r) for r in records if r["analysis_split"] == "Training"]
    if not training:
        raise ValueError("No approved training records")
    return training
