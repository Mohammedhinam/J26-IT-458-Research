"""Approval-gated Vision scaffold. CLI runs generated-image smoke tests only."""

from dataclasses import asdict, dataclass
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import tempfile

import numpy as np
from PIL import Image

from src.vision import model_pipeline as vp


@dataclass(frozen=True)
class TrainingConfig:
    architecture: str
    batch_size: int
    epochs: int
    learning_rate: float
    patience: int
    seed: int = 42
    min_delta: float = 0.0
    freeze_backbone: bool = True
    unfreeze_prefixes: tuple = ()
    batchnorm: str = "frozen"
    class_weight: str = "none"
    weight_decay: float = 0.0
    device: str = "cpu"

    def validate(self):
        vp.model_spec(self.architecture)
        for value in (self.batch_size, self.epochs, self.patience):
            if type(value) is not int or value < 1:
                raise ValueError("Batch size, epochs and patience must be positive integers")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("Seed must be an integer in [0, 2**32)")
        for value in (self.learning_rate, self.min_delta, self.weight_decay):
            if isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError("Learning rate/delta/decay must be finite and nonnegative")
        if self.learning_rate == 0 or type(self.freeze_backbone) is not bool:
            raise ValueError("Positive learning rate and explicit backbone-freezing flag required")
        if self.batchnorm not in {"frozen", "train_selected"}:
            raise ValueError("BatchNorm must be frozen or train_selected")
        if self.freeze_backbone and (self.unfreeze_prefixes or self.batchnorm != "frozen"):
            raise ValueError("Frozen backbone requires frozen BatchNorm and no unfreeze prefixes")
        if not isinstance(self.unfreeze_prefixes, tuple) or any(not isinstance(p, str) for p in self.unfreeze_prefixes):
            raise ValueError("Unfreeze prefixes must be an explicit tuple of module names")
        if not self.freeze_backbone and not self.unfreeze_prefixes:
            raise ValueError("Fine-tuning requires explicit approved backbone module prefixes")
        if self.class_weight not in {"none", "balanced"} or self.device not in {"cpu", "cuda"}:
            raise ValueError("Unsupported weighting or device")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def approved_partitions(manifest, approval_verifier):
    """Validate externally authenticated evidence before any image is opened.

    Test entries are sealed identifiers/group metadata only; their labels are not read.
    The verifier is supplied by the owner integration, never implemented as auto-approval.
    """
    if not callable(approval_verifier) or approval_verifier(deepcopy(manifest)) is not True:
        raise ValueError("External manifest approval verification required")
    approval = manifest.get("approval", {})
    required = ("labels_approved", "split_approved", "duplicate_review_complete",
                "participant_independence_verified")
    if (manifest.get("status") != "approved" or not approval.get("qualified_reviewer")
            or not approval.get("date") or not approval.get("evidence_reference")
            or any(approval.get(key) is not True for key in required)):
        raise ValueError("Qualified label, duplicate and participant/split approval evidence missing")
    partitions = {"Training": [], "Validation": []}
    paths, content_splits, participant_splits = set(), {}, {}
    records = manifest.get("records", [])
    if not records:
        raise ValueError("Manifest is empty")
    for row in records:
        path = row.get("image_path")
        split = row.get("analysis_split")
        original = row.get("original_split")
        if (not isinstance(path, str) or not path or Path(path).is_absolute()
                or ".." in Path(path).parts or path in paths
                or split not in {"Training", "Validation", "Test"}
                or original not in {"Training", "Validation", "Test"}):
            raise ValueError("Invalid/duplicate image path or split metadata")
        paths.add(path)
        # Original final-Test images may never enter either development partition.
        if original == "Test" and split != "Test":
            raise ValueError("Original Test content cannot enter development")
        for field, seen in (("content_group_id", content_splits),
                            ("participant_id", participant_splits)):
            identity = row.get(field)
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError("Verified content/participant identity required; unknown is not independent")
            if identity in seen and seen[identity] != split:
                raise ValueError("Content/participant group crosses splits")
            if field == "content_group_id" and identity in seen:
                raise ValueError("Repeated content requires an externally approved single-record eligibility list")
            seen[identity] = split
        if split == "Test":
            continue  # Do not inspect a Test grade, label provenance or image payload.
        provenance = row.get("label_provenance", {})
        grade = row.get("mgi_grade")
        if (row.get("label_status") != "verified" or type(grade) is not int
                or grade not in vp.MGI_GRADES or not provenance.get("source_reference")
                or not provenance.get("qualified_reviewer") or not provenance.get("date")
                or provenance.get("target_definition") != "maximum_visible_mgi"
                or provenance.get("source_kind") not in {"caption_csv", "qualified_caption_adjudication"}):
            raise ValueError("Verified image-level caption label provenance required")
        partitions[split].append(deepcopy(row))
    if not all(partitions.values()):
        raise ValueError("Approved Training and Validation partitions are both required")
    return partitions


def class_weights(labels, mode):
    labels = np.asarray(labels)
    if labels.ndim != 1 or not labels.size or labels.dtype.kind not in "iu" or np.any((labels < 0) | (labels > 4)):
        raise ValueError("Training labels must be integers in MGI 0..4")
    support = np.bincount(labels, minlength=5)
    if mode == "none":
        return None
    if mode != "balanced":
        raise ValueError("Unsupported class weighting")
    # No invented support for an absent class; weighting uses Training only.
    weights = np.zeros(5, dtype=np.float32)
    present = support > 0
    weights[present] = len(labels) / (int(present.sum()) * support[present])
    return weights


def validation_metrics(labels, probabilities):
    """Five-schema metrics, explicit missing support, no unsupported AUROC imputation."""
    labels = np.asarray(labels)
    probabilities = np.asarray(probabilities, dtype=float)
    if (labels.ndim != 1 or not labels.size or labels.dtype.kind not in "iu"
            or np.any((labels < 0) | (labels > 4)) or probabilities.shape != (len(labels), 5)
            or not np.isfinite(probabilities).all() or np.any(probabilities < 0)
            or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-6)):
        raise ValueError("Expected valid labels and five finite probability columns summing to one")
    prediction = probabilities.argmax(axis=1)
    confusion = np.zeros((5, 5), dtype=int)
    np.add.at(confusion, (labels, prediction), 1)
    support = confusion.sum(axis=1)
    predicted_support = confusion.sum(axis=0)
    tp = confusion.diagonal()
    denominators = support + predicted_support
    f1 = np.divide(2 * tp, denominators, out=np.zeros(5), where=denominators > 0)
    recall = [float(tp[i] / support[i]) if support[i] else None for i in range(5)]
    auc = []
    for grade in vp.MGI_GRADES:
        truth = labels == grade
        if truth.all() or not truth.any():
            auc.append(None)
            continue
        # Rank-sum AUROC with tied scores assigned their mean rank.
        score = probabilities[:, grade]
        order = np.argsort(score, kind="stable")
        ranks = np.empty(len(score), dtype=float)
        start = 0
        while start < len(score):
            end = start + 1
            while end < len(score) and score[order[end]] == score[order[start]]:
                end += 1
            ranks[order[start:end]] = (start + 1 + end) / 2
            start = end
        positives = int(truth.sum())
        auc.append(float((ranks[truth].sum() - positives * (positives + 1) / 2)
                         / (positives * (len(score) - positives))))
    distance = (np.arange(5)[:, None] - np.arange(5)[None, :])**2 / 16
    expected = np.outer(support, predicted_support) / len(labels)
    expected_disagreement = float((distance * expected).sum())
    return {"n": len(labels), "support": support.tolist(), "confusion_matrix": confusion.tolist(),
            "accuracy": float(tp.sum() / len(labels)), "per_grade_recall": recall,
            "per_grade_f1": [float(f1[i]) if support[i] else None for i in range(5)],
            "macro_f1_five_schema": float(f1.mean()),
            "macro_f1_supported_grades": float(f1[support > 0].mean()),
            "missing_grades": np.flatnonzero(support == 0).tolist(),
            "ordinal_mae": float(np.abs(labels - prediction).mean()),
            "quadratic_weighted_kappa": (float(1 - (distance * confusion).sum() / expected_disagreement)
                                          if expected_disagreement else None),
            "per_grade_auroc": auc, "macro_auroc_five_schema": (float(np.mean(auc)) if None not in auc else None),
            "multiclass_brier": float(((probabilities - np.eye(5)[labels])**2).sum(axis=1).mean())}


def seed_everything(seed):
    torch = vp._torch()
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def configure_trainable_layers(model, config):
    """Explicit head-only stage or approved module-prefix fine-tuning; no automatic stage switch."""
    config.validate()
    head_name = "fc" if config.architecture == "resnet50" else "classifier"
    modules = dict(model.named_modules())
    for prefix in config.unfreeze_prefixes:
        if not prefix or prefix not in modules or prefix == head_name or prefix.startswith(head_name + "."):
            raise ValueError("Fine-tuning prefixes must name existing backbone modules")
    for name, parameter in model.named_parameters():
        is_head = name == head_name or name.startswith(head_name + ".")
        selected = any(name.startswith(prefix + ".") for prefix in config.unfreeze_prefixes)
        parameter.requires_grad_(is_head or selected)
    if not any(p.requires_grad for p in model.parameters()):
        raise ValueError("No trainable classification parameters")


def training_mode(model, config):
    torch = vp._torch()
    model.train()
    if config.freeze_backbone:
        model.eval()  # Frozen features: no BatchNorm drift or stochastic backbone dropout.
        (model.fc if config.architecture == "resnet50" else model.classifier).train()
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            if not module.track_running_stats:
                raise ValueError("BatchNorm without tracked statistics is unsupported")
            selected = any(p.requires_grad for p in module.parameters())
            if config.batchnorm == "frozen" or not selected:
                module.eval()


class RGBDataset:
    """Only approved development records; no Test dataset object can be constructed."""
    def __init__(self, records, image_root, split, image_reader=None):
        if split not in {"Training", "Validation"} or not records:
            raise ValueError("Only nonempty Training/Validation loaders are allowed")
        if any(r["analysis_split"] != split or r["original_split"] == "Test" for r in records):
            raise ValueError("Loader contains forbidden split")
        self.records = deepcopy(records)
        self.root = Path(image_root).resolve()
        self.image_reader = image_reader or self._read

    @staticmethod
    def _read(path):
        with Image.open(path) as source:
            if source.mode != "RGB":
                raise ValueError("Source must already be RGB")
            return source.copy()

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        row = self.records[index]
        path = (self.root / row["image_path"]).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Image path escapes approved root")
        prepared = vp.preprocess_rgb(self.image_reader(path))
        return prepared.normalized_chw, row["mgi_grade"]


def run_epoch(model, loader, criterion, config, optimizer=None):
    torch = vp._torch()
    if getattr(criterion, "reduction", None) != "sum":
        raise ValueError("Epoch loss aggregation requires reduction=sum")
    if optimizer is None:
        model.eval()
    else:
        training_mode(model, config)
    labels, probabilities = [], []
    total_loss, count = 0.0, 0
    with torch.set_grad_enabled(optimizer is not None):
        for inputs, target in loader:
            inputs = inputs.to(config.device, dtype=torch.float32)
            target = target.to(config.device, dtype=torch.long)
            if optimizer is not None:
                optimizer.zero_grad(set_to_none=True)
            logits = model(inputs)
            if tuple(logits.shape) != (len(target), 5) or not torch.isfinite(logits).all():
                raise ValueError("Non-finite or non-five-logit model output")
            loss = criterion(logits, target)
            if not torch.isfinite(loss):
                raise ValueError("Non-finite loss")
            if optimizer is not None:
                (loss / len(target)).backward()
                optimizer.step()
            total_loss += float(loss.detach())
            count += len(target)
            labels.extend(target.detach().cpu().tolist())
            probabilities.extend(logits.detach().softmax(dim=1).cpu().tolist())
    if not count:
        raise ValueError("Empty epoch")
    # Criterion uses reduction=sum, making epoch loss independent of batch boundaries.
    return {"loss": total_loss / count, **validation_metrics(labels, probabilities)}


def stopping_update(score, best, bad_epochs, patience, min_delta):
    if not math.isfinite(score):
        raise ValueError("Early-stopping score must be finite")
    improved = score > best + min_delta
    return (score if improved else best), (0 if improved else bad_epochs + 1), improved


def _save_checkpoint(path, state):
    torch = vp._torch()
    # Atomic replacement is limited to scaffold-owned checkpoint files.
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".pt", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        torch.save(state, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _fit(model, training, validation, config, output_dir, context, resume=None, stop_after=None):
    """Internal loop shared by approved integration and generated-only tests."""
    torch = vp._torch()
    config.validate()
    seed_everything(config.seed)
    configure_trainable_layers(model, config)
    model.to(config.device)
    optimizer = torch.optim.Adam((p for p in model.parameters() if p.requires_grad),
                                 lr=config.learning_rate, weight_decay=config.weight_decay)
    weights = class_weights([r["mgi_grade"] for r in training.records], config.class_weight)
    training_loss = torch.nn.CrossEntropyLoss(weight=None if weights is None else
                                              torch.tensor(weights, device=config.device), reduction="sum")
    validation_loss = torch.nn.CrossEntropyLoss(reduction="sum")
    generator = torch.Generator().manual_seed(config.seed)
    train_loader = torch.utils.data.DataLoader(training, batch_size=config.batch_size, shuffle=True,
                                               num_workers=0, generator=generator)
    validation_loader = torch.utils.data.DataLoader(validation, batch_size=config.batch_size, shuffle=False,
                                                    num_workers=0, generator=torch.Generator().manual_seed(config.seed + 1))
    output = Path(output_dir)
    identity = digest({"config": asdict(config), "context": context})
    start, best, bad_epochs, history = 0, -math.inf, 0, []
    if resume is None:
        output.mkdir(parents=True, exist_ok=False)
    else:
        if Path(resume).resolve() != (output / "last.pt").resolve() or not (output / "best.pt").is_file():
            raise ValueError("Resume requires this run's last.pt and best.pt")
        state = torch.load(resume, map_location="cpu", weights_only=True)
        if state["identity"] != identity or state["schema"] != list(vp.MGI_GRADES):
            raise ValueError("Checkpoint configuration/manifest/source identity mismatch")
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        start, best, bad_epochs, history = state["epoch"], state["best"], state["bad_epochs"], state["history"]
        generator.set_state(state["loader_rng"])
        torch.set_rng_state(state["torch_rng"])
        if state["cuda_rng"]:
            torch.cuda.set_rng_state_all(state["cuda_rng"])
        random.setstate(state["python_rng"])
        ns = state["numpy_rng"]
        np.random.set_state((ns[0], np.array(ns[1], dtype=np.uint32), ns[2], ns[3], ns[4]))
    for epoch in range(start, config.epochs):
        if bad_epochs >= config.patience:
            break
        measured_training = run_epoch(model, train_loader, training_loss, config, optimizer)
        measured_validation = run_epoch(model, validation_loader, validation_loss, config)
        score = measured_validation["macro_f1_five_schema"]
        best, bad_epochs, improved = stopping_update(score, best, bad_epochs, config.patience, config.min_delta)
        history.append({"epoch": epoch + 1, "training": measured_training, "validation": measured_validation})
        ns = np.random.get_state()
        state = {"identity": identity, "config": asdict(config), "context": context,
                 "schema": list(vp.MGI_GRADES), "epoch": epoch + 1, "best": best,
                 "bad_epochs": bad_epochs, "history": history, "model": model.state_dict(),
                 "optimizer": optimizer.state_dict(), "loader_rng": generator.get_state(),
                 "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
                 "python_rng": random.getstate(), "numpy_rng": (ns[0], ns[1].tolist(), ns[2], ns[3], ns[4])}
        if improved:
            _save_checkpoint(output / "best.pt", state)
        _save_checkpoint(output / "last.pt", state)
        if stop_after is not None and epoch + 1 >= stop_after:
            break
    # Leave caller with best validation checkpoint, not the last optimisation step.
    best_state = torch.load(output / "best.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(best_state["model"])
    model.eval()
    result = {"history": history, "best_epoch": best_state["epoch"], "best_validation_macro_f1": best_state["best"],
              "early_stopped": bad_epochs >= config.patience, "five_class_validity_established": False,
              "test_used": False, "identity": identity}
    (output / "history.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def fit_approved(manifest, image_root, config, output_dir, approval_verifier, protocol_verifier, resume=None):
    """Future integration API; cannot run with current proposed/pending artifacts."""
    config.validate()
    partitions = approved_partitions(manifest, approval_verifier)
    configuration = asdict(config)
    if not callable(protocol_verifier) or protocol_verifier(deepcopy(manifest), configuration) is not True:
        raise ValueError("Separate external approval of exact experiment configuration required")
    protocol = manifest.get("protocol", {})
    if (protocol.get("status") != "approved" or protocol.get("configuration_sha256") != digest(configuration)
            or protocol.get("missing_grade_support_acknowledged") is not True):
        raise ValueError("Frozen approved configuration and explicit missing-grade acknowledgement required")
    repo = Path(__file__).resolve().parents[2]
    output = Path(output_dir).resolve()
    if not output.is_relative_to(repo / "models") or output == repo / "models":
        raise ValueError("Production checkpoints require a new ignored models/ run directory")
    seed_everything(config.seed)
    bundle = vp.make_model(config.architecture, pretrained=True, allow_download=False, freeze_backbone=True)
    training = RGBDataset(partitions["Training"], image_root, "Training")
    validation = RGBDataset(partitions["Validation"], image_root, "Validation")
    context = {"manifest_sha256": digest(manifest), "pretrained_source": bundle["loaded_weights"],
               "trainer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "model_source_sha256": hashlib.sha256(Path(vp.__file__).read_bytes()).hexdigest(),
               "runtime": {"torch": str(vp._torch().__version__), "numpy": np.__version__,
                           "device": config.device, "cpu_threads": vp._torch().get_num_threads()},
               "purpose": "externally approved development only"}
    return _fit(bundle["model"], training, validation, config, output, context, resume)


def synthetic_data(split, count=10):
    """Generated RGB arrays only; synthetic grades exercise code, not clinical evidence."""
    records = [{"image_path": f"synthetic/{split}/{i}.png", "analysis_split": split,
                "original_split": split, "mgi_grade": i % 5} for i in range(count)]
    def reader(path):
        index = int(path.stem)
        return Image.new("RGB", (32, 24), (index * 23 % 256, 80, 160))
    return RGBDataset(records, "/synthetic", split, reader)


def synthetic_smoke(output_dir):
    """Tiny generated-image optimisation, checkpoint and resume; never opens dataset files."""
    torch = vp._torch()
    config = TrainingConfig("resnet50", 5, 2, 0.001, 2)
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.features = torch.nn.Sequential(torch.nn.Conv2d(3, 2, 1), torch.nn.BatchNorm2d(2),
                                                torch.nn.AdaptiveAvgPool2d(1), torch.nn.Flatten())
            self.fc = torch.nn.Linear(2, 5)
        def forward(self, inputs):
            return self.fc(self.features(inputs))
    seed_everything(config.seed)
    initial = Tiny()
    training, validation = synthetic_data("Training"), synthetic_data("Validation")
    context = {"purpose": "generated RGB only"}
    _fit(initial, training, validation, config, output_dir, context, stop_after=1)
    result = _fit(Tiny(), training, validation, config, output_dir, context, resume=Path(output_dir) / "last.pt")
    return {"mode": "synthetic_smoke", "checkpoint_reload_and_resume": True, **result}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generated-image smoke only; no dataset training CLI")
    parser.add_argument("--smoke", action="store_true", required=True)
    arguments = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    base = repo / "models"
    base.mkdir(exist_ok=True)
    # Reserve a unique name without overwriting any existing run.
    output = base / ("synthetic-" + os.urandom(8).hex())
    print(json.dumps(synthetic_smoke(output), indent=2, allow_nan=False))
