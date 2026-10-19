"""Isolated fold-0 preparation/preflight and explicitly gated future CUDA pilot.

Never imports the live demo or its checkpoint. Labels remain provisional.
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn import metrics as sk

from src.vision import colour_b1_prototype as b1
from src.vision import model_pipeline as cam


VERSION = "resnet50-fold0-matched-adaptation-v1"
WEIGHTS_SHA = "11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca"
FOLDS_SHA = "e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4"
SOURCE_MANIFEST_SHA = "8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f"
GRADES = [1, 2, 3, 4]
CONFIG = {
    "version": VERSION, "fold": 0, "seed": 42, "batch_size": 16,
    "warmup_epochs": 1, "arm_epochs": 5, "head_lr": 0.001,
    "block_lr": 0.00001, "optimizer": "Adam", "weight_decay": 0,
    "batchnorm": "all_affine_and_running_statistics_frozen",
    "augmentation": False, "early_stopping": False, "score_epoch": 5,
    "resolution": 224, "grades": GRADES, "amp": False,
    "preprocessing": "unchanged_cached_B1_extended_float32_HWC_then_B1_normalize",
    "arm_A": "head_and_last_bottleneck", "arm_B": "head_and_full_layer4",
    "primary_metric": "macro_f1", "test_used": False,
}
APPROVAL_TEXT = "I approve this exact fold-0 Colab GPU pilot and cloud processing."
DEPENDENCIES = {"torch": "2.11.0", "torchvision": "0.26.0", "numpy": "2.5.3",
                "Pillow": "11.3.0", "scikit-learn": "1.9.1"}


def sha256_file(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def write_json(path, value):
    """Never overwrite prior receipts or results."""
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def safe_path(root, name):
    relative = Path(name)
    if relative.is_absolute() or not relative.parts or any(p in ("..", ".") for p in relative.parts):
        raise ValueError("Unsafe relative package path")
    root = Path(root).resolve()
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError("Missing, linked or unsafe package file")
    if not path.resolve().is_relative_to(root):
        raise ValueError("Path escaped package")
    return path


def validate_records(manifest):
    """Verify the frozen partition before opening any pixel array."""
    if (manifest["version"] != VERSION or manifest["config"] != CONFIG
            or manifest["source_manifest_sha256"] != SOURCE_MANIFEST_SHA
            or manifest["fold_assignment_sha256"] != FOLDS_SHA
            or manifest["qualified_labels_approved"] is not False
            or manifest["participant_independence_verified"] is not False):
        raise ValueError("Unexpected protocol or research-approval claims")
    rows = manifest["records"]
    ids = [r["id"] for r in rows]
    if len(rows) != 680 or ids != sorted(set(ids)):
        raise ValueError("Exactly 680 sorted unique Training records required")
    if any(not r["id"].startswith("Training/") or r["grade"] not in GRADES
           or r["role"] not in ("fit", "score") or not r["group"]
           or r["array"] != "arrays/" + r["id"].split("/")[1] + ".npy"
           for r in rows):
        raise ValueError("Missing labels, unsupported grade or non-Training membership")
    expected = {"fit": [9, 67, 179, 289], "score": [3, 17, 44, 72]}
    for role, support in expected.items():
        selected = [r for r in rows if r["role"] == role]
        if [sum(r["grade"] == g for r in selected) for g in GRADES] != support:
            raise ValueError("Fixed fold-0 class counts changed")
    fit_groups = {r["group"] for r in rows if r["role"] == "fit"}
    score_groups = {r["group"] for r in rows if r["role"] == "score"}
    fit_hashes = {r["source_sha256"] for r in rows if r["role"] == "fit"}
    score_hashes = {r["source_sha256"] for r in rows if r["role"] == "score"}
    if fit_groups & score_groups or fit_hashes & score_hashes:
        raise ValueError("Content group or exact source overlap")
    membership = {"ids": ids, "roles": [r["role"] for r in rows],
                  "grades": [r["grade"] for r in rows], "groups": [r["group"] for r in rows]}
    if digest(membership) != manifest["membership_sha256"]:
        raise ValueError("Membership binding changed")
    # The full frozen assignment binds every role, rather than relying on counts alone.
    snapshot = manifest["fold_snapshot"]
    if (snapshot["ids"] != ids or digest(snapshot["folds"]) != FOLDS_SHA
            or any(r["role"] != ("score" if f == 0 else "fit")
                   for r, f in zip(rows, snapshot["folds"], strict=True))):
        raise ValueError("Role differs from original frozen fold assignment")
    review = manifest["cam_ids"]
    score_ids = {r["id"] for r in rows if r["role"] == "score"}
    if len(review) != 8 or len(set(review)) != 8 or not set(review) <= score_ids:
        raise ValueError("Exactly eight predeclared scoring CAM cases required")
    return rows


def preflight(root, expected_manifest_sha=None):
    """Hash and numerically inspect only explicit package members; no model inference."""
    root = Path(root)
    manifest_path = safe_path(root, "manifest.json")
    if expected_manifest_sha and sha256_file(manifest_path) != expected_manifest_sha:
        raise ValueError("Manifest SHA mismatch")
    manifest = json.loads(manifest_path.read_text())
    rows = validate_records(manifest)
    expected = set(manifest["files"]) | {"manifest.json"}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("Missing or unexpected package files")
    for name, info in manifest["files"].items():
        member = safe_path(root, name)
        if member.stat().st_size != info["bytes"] or sha256_file(member) != info["sha256"]:
            raise ValueError("Package integrity failure: " + name)
    array_hashes = {r["role"]: set() for r in rows}
    for row in rows:
        path = safe_path(root, row["array"])
        if manifest["files"][row["array"]]["sha256"] != row["array_sha256"]:
            raise ValueError("Array provenance mismatch")
        values = np.load(path, allow_pickle=False)
        b1.normalize(values)  # Frozen B1 finite/range/shape checks; no resizing or clipping.
        array_hashes[row["role"]].add(row["array_sha256"])
        left, top, width, height = row["valid_box"]
        sw, sh = row["source_dimensions"]
        scale = min(224 / sw, 224 / sh)
        expected_w, expected_h = round(sw * scale), round(sh * scale)
        if (left, top, width, height) != ((224 - expected_w)//2, (224 - expected_h)//2,
                                         expected_w, expected_h):
            raise ValueError("Original aspect ratio or letterbox changed")
    if array_hashes["fit"] & array_hashes["score"]:
        raise ValueError("Identical B1 arrays cross fit/score")
    for record_id in manifest["cam_ids"]:
        row = next(r for r in rows if r["id"] == record_id)
        with Image.open(safe_path(root, row["preview"])) as image:
            sw, sh = row["source_dimensions"]
            if (image.mode != "RGB" or image.format != "PNG" or image.info
                    or abs(image.width / image.height - sw / sh) > .003):
                raise ValueError("Preview metadata, RGB or original geometry mismatch")
    weights = safe_path(root, "weights/resnet50-11ad3fa6.pth")
    if sha256_file(weights) != WEIGHTS_SHA:
        raise ValueError("Only pinned official ImageNet V2 initialization is allowed")
    return {"status": "passed", "fit_count": 544, "score_count": 136,
            "fit_support_1_to_4": [9, 67, 179, 289], "score_support_1_to_4": [3, 17, 44, 72],
            "cam_cases": 8, "verified_files": len(manifest["files"]),
            "manifest_sha256": sha256_file(manifest_path), "training_run": False,
            "validation_payloads_used": 0, "test_payloads_used": 0,
            "participant_independence_verified": False}


def model_factory(weights):
    """Official ImageNet only: never accepts the historical dental v3 checkpoint."""
    from torchvision.models import resnet50
    if sha256_file(weights) != WEIGHTS_SHA:
        raise ValueError("Non-ImageNet initialization rejected")
    torch.manual_seed(CONFIG["seed"])
    model = resnet50(weights=None)
    model.load_state_dict(torch.load(weights, map_location="cpu", weights_only=True))
    model.fc = torch.nn.Linear(model.fc.in_features, 4)
    return model


def state_hashes(model):
    return {name: hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
            for name, value in model.state_dict().items()}


def configure(model, stage):
    """Only the declared head/block trains; all BatchNorm state stays fixed."""
    if stage not in ("warmup", "A", "B") or model.fc.out_features != 4:
        raise ValueError("Unknown stage or incompatible head")
    model.requires_grad_(False)
    model.fc.requires_grad_(True)
    if stage != "warmup":
        block = model.layer4[-1] if stage == "A" else model.layer4
        block.requires_grad_(True)
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            module.requires_grad_(False)
    # ResNet50 has no dropout. eval freezes BN while autograd still trains declared weights.
    model.eval()
    head, block, names = [], [], []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            names.append(name)
            (head if name.startswith("fc.") else block).append(parameter)
    groups = [{"params": head, "lr": CONFIG["head_lr"]}]
    if block:
        groups.append({"params": block, "lr": CONFIG["block_lr"]})
    return groups, names


def class_weights(labels):
    values = np.asarray(labels)
    if values.dtype.kind not in "iu" or values.ndim != 1 or set(values.tolist()) != {1, 2, 3, 4}:
        raise ValueError("All four fitting grades required")
    return (len(values) / (4 * np.bincount(values, minlength=5)[1:])).astype(np.float32)


def epoch_order(count, stage, epoch):
    # Both arms use identical epoch-specific orders, including after a restart.
    seed = CONFIG["seed"] + (1000 if stage == "warmup" else 2000) + epoch
    return np.random.default_rng(seed).permutation(count)


def train_epoch(model, optimizer, arrays, labels, weights, order, device):
    """No scoring arrays/labels enter this function."""
    model.eval()
    total_loss, total_weight = 0., 0.
    for start in range(0, len(order), CONFIG["batch_size"]):
        index = order[start:start + CONFIG["batch_size"]]
        inputs = torch.from_numpy(arrays[index]).to(device)
        targets = torch.as_tensor(labels[index] - 1, dtype=torch.long, device=device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        losses = torch.nn.functional.cross_entropy(logits, targets, reduction="none")
        selected_weights = weights[targets]
        loss = (losses * selected_weights).sum() / selected_weights.sum()
        if not torch.isfinite(loss):
            raise ValueError("Nonfinite fitting loss")
        loss.backward()
        for parameter in model.parameters():
            if parameter.requires_grad and (parameter.grad is None or not torch.isfinite(parameter.grad).all()):
                raise ValueError("Missing or nonfinite gradient")
        optimizer.step()
        total_loss += float((losses.detach() * selected_weights).sum())
        total_weight += float(selected_weights.sum())
    return total_loss / total_weight


def train_stage(model, stage, arrays, labels, destination, binding, device):
    """Epoch checkpoints resume only with identical inputs, initialization and runtime."""
    destination = Path(destination)
    destination.mkdir(exist_ok=True)
    groups, allowed = configure(model, stage)
    optimizer = torch.optim.Adam(groups, weight_decay=0)
    initial = state_hashes(model)
    identity = digest({"binding": binding, "stage": stage, "initial": initial,
                       "config": CONFIG, "torch": str(torch.__version__), "device": device})
    weights = torch.tensor(class_weights(labels), device=device)
    epochs = 1 if stage == "warmup" else 5
    for epoch in range(1, epochs + 1):
        checkpoint = destination / f"epoch_{epoch:02}.pt"
        order = epoch_order(len(labels), stage, epoch)
        if checkpoint.exists():
            saved = torch.load(checkpoint, map_location=device, weights_only=True)
            if (saved["identity"] != identity or saved["epoch"] != epoch
                    or saved["order_sha256"] != digest(order.tolist())):
                raise ValueError("Checkpoint provenance/config/runtime mismatch")
            model.load_state_dict(saved["model"])
            optimizer.load_state_dict(saved["optimizer"])
            if state_hashes(model) != saved["tensor_hashes"]:
                raise ValueError("Checkpoint tensor hashes changed")
            if any(saved["tensor_hashes"][name] != value for name, value in initial.items() if name not in allowed):
                raise ValueError("Resumed checkpoint changed frozen tensors or BatchNorm")
            if any(not torch.isfinite(value).all() for value in model.state_dict().values()):
                raise ValueError("Nonfinite resumed checkpoint tensor")
            continue
        loss = train_epoch(model, optimizer, arrays, labels, weights, order, device)
        final = state_hashes(model)
        if any(final[name] != value for name, value in initial.items() if name not in allowed):
            raise ValueError("Frozen tensors or BatchNorm state changed")
        if any(not torch.isfinite(value).all() for value in model.state_dict().values()):
            raise ValueError("Nonfinite checkpoint tensor")
        saved = {"identity": identity, "binding": binding, "config": CONFIG, "stage": stage,
                 "epoch": epoch, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                 "initial_tensor_hashes": initial, "tensor_hashes": final,
                 "trainable_names": allowed, "class_weights": weights.cpu().tolist(),
                 "order_sha256": digest(order.tolist()), "fit_weighted_ce": loss}
        # Exclusive write preserves any previous or interrupted file instead of replacing it.
        with checkpoint.open("xb") as stream:
            torch.save(saved, stream)
        write_json(destination / f"epoch_{epoch:02}.json",
                   {key: saved[key] for key in ("identity", "stage", "epoch", "fit_weighted_ce",
                                                "order_sha256", "trainable_names", "class_weights")})
        print(json.dumps({"stage": stage, "epoch": epoch, "fit_weighted_ce": loss}), flush=True)
    return {"initial_sha256": digest(initial), "final_sha256": digest(state_hashes(model)),
            "final_checkpoint": str(destination / f"epoch_{epochs:02}.pt")}


def measure(labels, probabilities):
    labels, probabilities = np.asarray(labels), np.asarray(probabilities)
    if (labels.ndim != 1 or labels.dtype.kind not in "iu" or not set(labels.tolist()) <= set(GRADES)
            or probabilities.shape != (len(labels), 4) or not np.isfinite(probabilities).all()
            or (probabilities < 0).any() or not np.allclose(probabilities.sum(1), 1, atol=1e-6, rtol=0)):
        raise ValueError("Invalid scoring grades/probabilities")
    predicted = probabilities.argmax(1) + 1
    recalls = sk.recall_score(labels, predicted, labels=GRADES, average=None, zero_division=0)
    qwk = float(sk.cohen_kappa_score(labels, predicted, labels=GRADES, weights="quadratic"))
    return {"accuracy": float(sk.accuracy_score(labels, predicted)),
            "macro_f1": float(sk.f1_score(labels, predicted, labels=GRADES, average="macro", zero_division=0)),
            "balanced_accuracy": float(sk.balanced_accuracy_score(labels, predicted)),
            "per_grade_recall": dict(zip(map(str, GRADES), recalls.tolist())),
            "confusion_matrix": sk.confusion_matrix(labels, predicted, labels=GRADES).tolist(),
            "confusion_matrix_labels": GRADES, "ordinal_mae": float(sk.mean_absolute_error(labels, predicted)),
            "quadratic_weighted_kappa": qwk if np.isfinite(qwk) else None}


def predict(model, arrays, device):
    model.eval()
    scores = []
    with torch.no_grad():
        for start in range(0, len(arrays), CONFIG["batch_size"]):
            logits = model(torch.from_numpy(arrays[start:start + CONFIG["batch_size"]]).to(device))
            scores.extend(logits.softmax(1).cpu().tolist())
    return np.asarray(scores)


def gradcam(model, prepared, target_index=None):
    """Reuse unchanged CAM geometry; no gum masks, attention loss or cosmetic filtering."""
    captured = []
    hook = model.layer4[-1].register_forward_hook(lambda module, inputs, output: captured.append(output))
    try:
        model.eval()
        device = next(model.parameters()).device
        inputs = torch.tensor(prepared.normalized_chw[None], device=device, requires_grad=True)
        logits = model(inputs)
        selected = int(logits.argmax()) if target_index is None else target_index
        if selected not in range(4) or len(captured) != 1:
            raise ValueError("Invalid four-class CAM target")
        gradients = torch.autograd.grad(logits[0, selected], captured[0])[0]
        views = cam.gradcam_views(captured[0].detach().cpu().numpy()[0],
                                  gradients.detach().cpu().numpy()[0], prepared)
        return views, {"explained_grade": selected + 1, "predicted_grade": int(logits.argmax()) + 1,
                       "target_layer": "layer4[-1]", "native_feature_shape": list(captured[0].shape),
                       "explanation_status": views["explanation_status"],
                       "warning": "Model attention; not validated disease localization or gingival boundaries."}
    finally:
        hook.remove()


def run(root, output, *, execute=False, approval="", manifest_sha=None):
    """Real fitting is unavailable without a separate exact execution opt-in and CUDA."""
    if not execute or approval != APPROVAL_TEXT:
        raise PermissionError("Preparation only: explicit future cloud/GPU approval is required")
    if not isinstance(manifest_sha, str) or len(manifest_sha) != 64:
        raise ValueError("An explicitly pinned manifest SHA is required")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; never silently fall back to CPU training")
    versions = {name: importlib.metadata.version(name) for name in DEPENDENCIES}
    if any(versions[name].split("+")[0] != required for name, required in DEPENDENCIES.items()):
        raise RuntimeError("Runtime differs from pinned dependencies; stop before fitting")
    receipt = preflight(root, manifest_sha)
    root, output = Path(root), Path(output)
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError("Run outputs must be outside immutable package")
    torch.set_num_threads(2)
    torch.manual_seed(CONFIG["seed"])
    torch.cuda.manual_seed_all(CONFIG["seed"])
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    manifest = json.loads((root / "manifest.json").read_text())
    binding = {"manifest_sha256": receipt["manifest_sha256"], "config": CONFIG,
               "weights_sha256": WEIGHTS_SHA, "python": platform.python_version(),
               "torch": str(torch.__version__), "cuda": torch.version.cuda,
               "gpu": torch.cuda.get_device_name(), "dependencies": versions, "training_authorized": True}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "run_binding.json").exists():
        if json.loads((output / "run_binding.json").read_text()) != binding:
            raise ValueError("Existing run belongs to another protocol/runtime")
    else:
        if any(output.iterdir()):
            raise ValueError("Fresh output or matching resumable run required")
        write_json(output / "run_binding.json", binding)
    if (output / "complete.json").exists():
        raise FileExistsError("Completed run preserved; do not run again")
    rows = manifest["records"]
    fit_rows = [r for r in rows if r["role"] == "fit"]
    score_rows = [r for r in rows if r["role"] == "score"]
    fit_x = np.stack([b1.normalize(np.load(root / r["array"], allow_pickle=False)) for r in fit_rows])
    fit_y = np.array([r["grade"] for r in fit_rows])
    weights = root / "weights/resnet50-11ad3fa6.pth"
    model = model_factory(weights).cuda()
    warmup = train_stage(model, "warmup", fit_x, fit_y, output / "warmup", binding, "cuda")
    shared = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
    del model
    # Scoring is delayed until both arms finish; it never selects an epoch or setting.
    trained, arm_records = {}, {}
    for arm in ("A", "B"):
        model = model_factory(weights).cuda()
        model.load_state_dict(shared)
        arm_records[arm] = train_stage(model, arm, fit_x, fit_y, output / arm, binding, "cuda")
        trained[arm] = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
        del model
        torch.cuda.empty_cache()
    if arm_records["A"]["initial_sha256"] != arm_records["B"]["initial_sha256"]:
        raise ValueError("Arms did not start from identical warm-up tensors")
    score_x = np.stack([b1.normalize(np.load(root / r["array"], allow_pickle=False)) for r in score_rows])
    score_y = np.array([r["grade"] for r in score_rows])
    results, probabilities = {}, {}
    for arm in ("A", "B"):
        model = model_factory(weights).cuda()
        model.load_state_dict(trained[arm])
        probabilities[arm] = predict(model, score_x, "cuda")
        results[arm] = measure(score_y, probabilities[arm])
        for record_id in manifest["cam_ids"]:
            row = next(r for r in score_rows if r["id"] == record_id)
            index = score_rows.index(row)
            with Image.open(root / row["preview"]) as image:
                prepared = cam.RGBInput(np.asarray(image).copy(), score_x[index], tuple(row["valid_box"]))
            # Predicted-class view plus a common A-predicted target make class changes explicit.
            targets = {"predicted": None, "common_A_target": int(probabilities["A"][index].argmax())}
            for target_name, target in targets.items():
                directory = output / "cam" / row["id"].split("/")[1] / arm / target_name
                directory.mkdir(parents=True, exist_ok=True)
                views, detail = gradcam(model, prepared, target)
                for name in ("original", "heatmap", "overlay"):
                    path = directory / (name + ".png")
                    if path.exists():
                        raise FileExistsError("Preserve existing CAM output; inspect interrupted scoring")
                    Image.fromarray(views[name]).save(path)
                write_json(directory / "explanation.json", detail)
        del model
        torch.cuda.empty_cache()
    predictions = {arm: [{"id": row["id"], "provisional_grade": row["grade"],
                          "predicted_grade": int(probabilities[arm][i].argmax()) + 1,
                          "uncalibrated_probabilities_grades_1_to_4": probabilities[arm][i].tolist()}
                         for i, row in enumerate(score_rows)] for arm in ("A", "B")}
    write_json(output / "predictions.json", predictions)
    write_json(output / "metrics.json", {"arms": results, "n_score": 136,
               "interpretation": "Single development fold; not 680-image OOF or clinical validation.",
               "B_minus_A": {key: results["B"][key] - results["A"][key]
                             for key in ("accuracy", "macro_f1", "balanced_accuracy", "ordinal_mae")}})
    write_json(output / "complete.json", {"status": "fixed_fold0_completed", "warmup": warmup,
               "arms": arm_records, "test_used": False, "validation_used": False})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "run"])
    parser.add_argument("root", type=Path)
    parser.add_argument("--manifest-sha", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approval", default="")
    args = parser.parse_args()
    if args.action == "preflight":
        print(json.dumps(preflight(args.root, args.manifest_sha), indent=2))
    else:
        if args.output is None:
            parser.error("--output required for a future authorized run")
        print(json.dumps(run(args.root, args.output, execute=args.execute,
                             approval=args.approval, manifest_sha=args.manifest_sha), indent=2))
