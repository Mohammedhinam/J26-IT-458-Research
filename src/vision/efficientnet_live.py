"""Pinned EfficientNet-B0 fold-0 photo inference, using the existing B1 decoder.

The proposal's main candidate is a research demonstration, not a final model.
No training, weight download, dataset access or automatic photo storage occurs.
"""
from hashlib import sha256
from io import BytesIO
from pathlib import Path

from .local_photo_upload_demo import LocalUploadPhotoRuntime

VERSION = "efficientnet-b0-local-photo-v1"
CHECKPOINT_SHA = "b557f52e358ca88329391e01e3f2c6f77123d14bbbe1027dd38391a27ea96353"
DEFAULT_CHECKPOINT = Path(__file__).resolve().parents[2] / (
    "data/efficientnet_adaptation_v1_20261017_1792202682936988000/"
    "fold0_last_block/final.pt"
)
EXPECTED_BINDINGS = {
    "manifest_sha256": "8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f",
    "weights_sha256": "7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934",
    "config_sha256": "b73a4df70082d8664e34c373e06fd5ebd89eba392f66e197d2c39028a4c73286",
    "fold_sha256": "e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4",
}


class EfficientNetPhotoRuntime(LocalUploadPhotoRuntime):
    """Share decoding, predicted-class CAM alignment and response validation."""

    def identity(self):
        return {
            "version": VERSION,
            "model_family": "efficientnet_b0",
            "model_name": "EfficientNet-B0",
            "proposal_role": "main_candidate",
            "fold": 0,
            "training_arm": "last_block",
            "cam_target_layer": "features.8",
            "checkpoint_sha256": self.checkpoint_sha256,
            "device": "cpu",
            "all_development_refit": False,
            "evaluation": {
                "protocol": "five_fold_680_training_oof_last_block_arm",
                "accuracy": 0.4676470588235294,
                "macro_f1": 0.34157925156206276,
                "scope": "Pooled five-fold evidence, not the accuracy of a new photo or this fold alone",
            },
        }

    def status(self):
        return {**super().status(), **self.identity()}

    def explain_upload(self, payload, content_type):
        # The shared runtime preserves B1 preprocessing and the original geometry.
        return {**super().explain_upload(payload, content_type), **self.identity()}


def load_runtime(checkpoint=DEFAULT_CHECKPOINT):
    """Hash-check before deserialization and use only the declared fold/arm."""
    import torch
    from torchvision.models import efficientnet_b0

    path = Path(checkpoint)
    if path.is_symlink() or not path.is_file():
        raise ValueError("A regular pinned EfficientNet checkpoint is required")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != CHECKPOINT_SHA:
        raise ValueError("EfficientNet checkpoint SHA mismatch before loading")
    state = torch.load(BytesIO(raw), map_location="cpu", weights_only=True)
    if (state.get("version") != "training680-matched-efficientnet-adaptation-v1"
            or state.get("grades") != [1, 2, 3, 4]
            or state.get("fold") != 0 or state.get("arm") != "last_block"):
        raise ValueError("Unexpected EfficientNet checkpoint schema, fold or arm")
    if any(state.get("bindings", {}).get(key) != value for key, value in EXPECTED_BINDINGS.items()):
        raise ValueError("EfficientNet training provenance changed")
    model = efficientnet_b0(weights=None)
    model.classifier[-1] = torch.nn.Linear(1280, 4)
    model.load_state_dict(state["model"], strict=True)
    model.requires_grad_(False)
    model.eval()
    # features.8 is the final convolution/BN/activation block before pooling.
    return EfficientNetPhotoRuntime(model, model.features[8], CHECKPOINT_SHA)
