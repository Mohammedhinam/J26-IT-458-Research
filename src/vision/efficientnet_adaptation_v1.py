"""One matched, Training-only EfficientNet experiment; never downloads data/weights.

The original classifier, colour contract, labels and final Test remain unchanged.
Generated callers can test the helpers without opening any dental payload.
"""
import hashlib
import io
import json
from pathlib import Path
import platform
import resource
import time

import numpy as np
import torch

from . import frozen_feature_probe as base
from . import efficientnet_feature_probe as encoder
from . import exploratory_pilot_b1_balanced_v2 as weighted


VERSION = "training680-matched-efficientnet-adaptation-v1"
SCOPE = "run_training680_matched_efficientnet_adaptation_v1"
ARMS = ("head_only", "last_block")
WEIGHTS_SHA = "7f5810bc96def8f7552d5b7e68d53c4786f81167d28291b21c0d90e1fca14934"
FOLD_SHA = "e202132b8b7ee38ec4041ea399bccb0b538ef75ce1861faec044292c11cf90d4"
CONFIG = {"version": VERSION, "arms": list(ARMS), "folds": 5, "fits": 10,
          "seed": 42, "epochs": 5, "batch_size": 16, "device": "mps",
          "head_lr": 0.001, "block_lr": 0.00001, "weight_decay": 0.0001,
          "unfreeze": "features.8_except_BatchNorm", "batchnorm": "frozen",
          "optimizer": "AdamW", "loss": "fitting_fold_balanced_cross_entropy",
          "score_epoch": 5, "resolution": 224, "grades": [1, 2, 3, 4],
          "early_stopping": False, "augmentation": False,
          "primary": "last_block_minus_head_only_OOF_macro_F1"}
REPO = Path(__file__).resolve().parents[2]
ATTEMPT = REPO / "data/efficientnet_adaptation_once_v1/attempt.json"


def code_hashes():
    """Bind reused array, loss, metric and fold implementations as well as this file."""
    return {**encoder.code_hashes(), **weighted.code_hashes(),
            "efficientnet_adaptation_v1.py": base.legacy.sha256(__file__)}


def state_hashes(model):
    # CPU byte hashes let us prove that frozen parameters and BN never changed.
    result = {}
    for name, value in model.state_dict().items():
        array = value.detach().cpu().contiguous().numpy()
        result[name] = hashlib.sha256(array.tobytes()).hexdigest()
    return result


def configure_model(model, arm):
    """Enable only the four-output head, and optionally non-BN final-block weights."""
    if arm not in ARMS or len(model.features) != 9 or model.classifier[-1].out_features != 4:
        raise ValueError("Expected a declared arm and nine-block, four-output model")
    model.requires_grad_(False)
    model.classifier.requires_grad_(True)
    if arm == "last_block":
        for module in model.features[8].modules():
            if not isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
                for parameter in module.parameters(recurse=False):
                    parameter.requires_grad_(True)
    # BatchNorm affine parameters and statistics remain frozen in both arms.
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            module.requires_grad_(False)
    groups = []
    for prefix, rate in (("classifier.", CONFIG["head_lr"]), ("features.8.", CONFIG["block_lr"])):
        named = [(name, value) for name, value in model.named_parameters()
                 if name.startswith(prefix) and value.requires_grad]
        if named:
            groups.append({"params": [value for _, value in named],
                           "names": [name for name, _ in named], "lr": rate})
    names = [name for group in groups for name in group["names"]]
    actual = [name for name, value in model.named_parameters() if value.requires_grad]
    if not names or set(names) != set(actual):
        raise ValueError("Unexpected trainable tensor outside declared head/final block")
    return {"parameter_groups": groups, "trainable_names": sorted(names),
            "trainable_parameters": sum(value.numel() for group in groups for value in group["params"])}


def training_mode(model):
    # Frozen backbone stochastic-depth and every BatchNorm stay in evaluation mode.
    model.eval()
    model.classifier.train()


def class_weights(targets):
    """Balanced weights use fitting-fold zero-based targets, never scoring labels."""
    values = np.asarray(targets)
    if values.ndim != 1 or not len(values) or values.dtype.kind not in "iu" or set(values.tolist()) != {0, 1, 2, 3}:
        raise ValueError("All four fitting classes, encoded0to3, are required")
    return (len(values) / (4 * np.bincount(values, minlength=4))).astype(np.float32)


def validate_folds(ids, labels, groups, folds, strict=False):
    """One scoring fold per unique record; known content groups cannot leak."""
    labels = base.pilot.checked_grades(labels)
    folds = np.asarray(folds)
    if (list(ids) != sorted(ids) or len(set(ids)) != len(ids)
            or any(not isinstance(name, str) or name.startswith(("Test/", "Validation/")) for name in ids)
            or len(ids) != len(labels) or len(groups) != len(ids) or folds.shape != labels.shape
            or folds.dtype.kind not in "iu" or set(folds.tolist()) != set(range(5))
            or any(not isinstance(group, str) or not group for group in groups)):
        raise ValueError("Invalid unique membership or five-fold coverage")
    groups = np.asarray(groups)
    for fold in range(5):
        fit, score = folds != fold, folds == fold
        if (set(groups[fit]) & set(groups[score]) or set(labels[fit]) != {1, 2, 3, 4}
                or set(labels[score]) != {1, 2, 3, 4}):
            raise ValueError("Fold group leakage or missing class support")
    if strict and (len(ids) != 680 or any(not name.startswith("Training/") for name in ids)
                   or np.bincount(labels, minlength=5).tolist() != [0, 12, 84, 223, 361]
                   or base.b1.digest_json(folds.tolist()) != FOLD_SHA
                   or any(np.sum(folds == fold) != 136 for fold in range(5))):
        raise ValueError("Pinned680Training membership/folds required")
    return folds


def fit_arm(model, fit_x, fit_y, score_x, arm, device="cpu", epochs=5,
            batch_size=16, progress=None):
    """Train on fit_x/fit_y only; scoring labels are deliberately not an argument."""
    if device not in {"cpu", "mps"} or not 1 <= epochs <= 5 or not 1 <= batch_size <= 16:
        raise ValueError("Bounded CPU/MPS fit configuration required")
    fit_x, score_x = torch.as_tensor(fit_x), torch.as_tensor(score_x)
    fit_y = torch.as_tensor(fit_y)
    if (fit_x.ndim != 4 or score_x.ndim != 4 or fit_x.shape[1:] != score_x.shape[1:]
            or fit_x.shape[1] != 3 or len(fit_y) != len(fit_x) or not len(score_x)
            or fit_y.dtype != torch.long or not torch.isfinite(fit_x).all()
            or not torch.isfinite(score_x).all()):
        raise ValueError("Finite aligned fitting/scoring tensors required")
    torch.manual_seed(CONFIG["seed"])
    model.to(device)
    configuration = configure_model(model, arm)
    initial = state_hashes(model)
    initial_sha = base.b1.digest_json(initial)
    trainable = configuration["trainable_names"]
    optimizer = torch.optim.AdamW(
        [{"params": group["params"], "lr": group["lr"]} for group in configuration["parameter_groups"]],
        weight_decay=CONFIG["weight_decay"])
    weights = class_weights(fit_y.cpu().numpy())
    device_weights = torch.as_tensor(weights, device=device)
    rng = np.random.default_rng(CONFIG["seed"])
    orders, history = [], []
    for epoch in range(epochs):
        training_mode(model)
        order = rng.permutation(len(fit_y))
        orders.append(order.tolist())
        raw_sum, weighted_sum, weight_sum = 0., 0., 0.
        for start in range(0, len(order), batch_size):
            index = torch.as_tensor(order[start:start + batch_size])
            values = fit_x[index].to(device, dtype=torch.float32)
            target = fit_y[index].to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(values)
            if logits.shape != (len(target), 4) or not torch.isfinite(logits).all():
                raise ValueError("Four finite training logits required")
            losses = torch.nn.functional.cross_entropy(logits, target, reduction="none")
            objective = weighted.weighted_objective(losses, target, device_weights)
            if not torch.isfinite(objective):
                raise ValueError("Non-finite training objective")
            objective.backward()
            if any(value.grad is None or not torch.isfinite(value.grad).all()
                   for value in model.parameters() if value.requires_grad):
                raise ValueError("Missing/non-finite trainable gradient")
            optimizer.step()
            if any(not torch.isfinite(value).all() for value in model.parameters() if value.requires_grad):
                raise ValueError("Non-finite fitted parameter")
            raw_sum += float(losses.detach().sum())
            weighted_sum += float((losses.detach() * device_weights[target]).sum())
            weight_sum += float(device_weights[target].sum())
        item = {"epoch": epoch + 1, "fitting_unweighted_ce": raw_sum / len(fit_y),
                "fitting_weighted_ce": weighted_sum / weight_sum}
        history.append(item)
        if progress is not None:
            progress(item)
    # Score the outer fold only once, after the prospectively fixed final epoch.
    model.eval()
    probabilities = []
    with torch.no_grad():
        for start in range(0, len(score_x), batch_size):
            logits = model(score_x[start:start + batch_size].to(device, dtype=torch.float32))
            if logits.shape != (len(score_x[start:start + batch_size]), 4) or not torch.isfinite(logits).all():
                raise ValueError("Invalid final scoring logits")
            probabilities.append(logits.softmax(1).cpu().numpy())
    probabilities = np.concatenate(probabilities)
    if not np.isfinite(probabilities).all() or not np.allclose(probabilities.sum(1), 1, atol=1e-6, rtol=0):
        raise ValueError("Invalid final scoring probabilities")
    after = state_hashes(model)
    if any(after[name] != value for name, value in initial.items() if name not in trainable):
        raise ValueError("Frozen parameter or BatchNorm state changed")
    diagnostics = [{"names": group["names"], "lr": group["lr"],
                    "parameters": sum(value.numel() for value in group["params"])}
                   for group in configuration["parameter_groups"]]
    return {"probabilities": probabilities, "history": history, "initial_sha": initial_sha,
            "order_sha": base.b1.digest_json(orders), "frozen_check": True,
            "trainable_names": trainable, "parameter_diagnostics": diagnostics,
            "class_weights": weights.tolist(), "initial_tensor_hashes": initial,
            "final_tensor_hashes": after}


def execute_comparison(arrays, labels, ids, groups, folds, model_factory, device="cpu",
                       epochs=5, batch_size=16, on_fit_complete=None, progress=None):
    """Two fresh matched models per fold; never select an epoch from outer scores."""
    folds = validate_folds(ids, labels, groups, folds)
    arrays = torch.as_tensor(arrays)
    labels = np.asarray(labels)
    if len(arrays) != len(ids):
        raise ValueError("Array/membership length mismatch")
    predictions = {arm: np.full((len(ids), 4), np.nan) for arm in ARMS}
    records = []
    for fold in range(5):
        fit, score = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        fit_x, score_x = arrays[fit], arrays[score]
        pair = []
        for arm in ARMS:
            if len(records) >= 10:
                raise ValueError("Ten-fit budget exhausted")
            torch.manual_seed(CONFIG["seed"])
            model = model_factory()
            def report(item):
                if progress is not None:
                    progress({"fold": fold, "arm": arm, **item})
            result = fit_arm(model, fit_x, torch.as_tensor(labels[fit] - 1), score_x,
                             arm, device, epochs, batch_size, report)
            if not np.isnan(predictions[arm][score]).all():
                raise ValueError("Duplicate OOF assignment")
            predictions[arm][score] = result["probabilities"]
            record = {"fold": fold, "arm": arm, "fit_count": len(fit), "score_count": len(score),
                      "fit_support": np.bincount(labels[fit], minlength=5)[1:].tolist(),
                      **{key: value for key, value in result.items() if key != "probabilities"}}
            records.append(record)
            pair.append((result["initial_sha"], result["order_sha"]))
            if on_fit_complete is not None:
                on_fit_complete(fold, arm, model, result)
            model.to("cpu")
            del model
        if pair[0] != pair[1]:
            raise ValueError("Paired initial state or fitting order changed")
    if len(records) != 10 or any(not np.isfinite(values).all() for values in predictions.values()):
        raise ValueError("Incomplete ten-fit OOF comparison")
    return {"probabilities": predictions, "fit_records": records, "fit_count": len(records),
            "metrics": {arm: base.measure(labels, values) for arm, values in predictions.items()}}


def consume_attempt(marker, record):
    """Exclusive creation prevents replay even after a failed or interrupted fit."""
    marker = Path(marker)
    if any(path.is_symlink() for path in (marker, *marker.parents)):
        raise ValueError("Symlink attempt path")
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x") as handle:
        json.dump({"status": "consumed_before_fitting", "authorization": record}, handle, indent=2)


def metric_differences(metrics):
    """Use the actual shared metric names; this block never fits a model."""
    keys = ("accuracy", "macro_f1_four_grades", "balanced_accuracy",
            "quadratic_weighted_kappa", "multiclass_brier")
    return {key: metrics["last_block"][key] - metrics["head_only"][key]
            for key in keys}


def metadata(root, output):
    """Validate manifest/folds before any array payload is opened."""
    path = base.legacy.safe_file(root, "bundle_manifest.json")
    if base.legacy.sha256(path) != base.MANIFEST_SHA:
        raise ValueError("Pinned manifest SHA mismatch")
    rows = base.training_rows(base.bundle.load_json(path))
    ids = [row["source_record_id"] for row in rows]
    labels = np.array([row["provisional_mgi_grade"] for row in rows])
    groups = [row["content_group_id"] for row in rows]
    folds = validate_folds(ids, labels, groups, base.make_folds(ids, labels, groups), strict=True)
    bindings = {"manifest_sha256": base.MANIFEST_SHA, "weights_sha256": WEIGHTS_SHA,
                "config_sha256": base.b1.digest_json(CONFIG),
                "code_sha256": base.b1.digest_json(code_hashes()),
                "selection_sha256": base.b1.digest_json(rows), "fold_sha256": FOLD_SHA,
                "output_path_sha256": hashlib.sha256(str(Path(output).resolve()).encode()).hexdigest()}
    return rows, ids, labels, groups, folds, bindings


def run_authorized(root, weights, output, authorization, *, opt_in=False, qualification=None):
    """One explicitly approved MPS experiment; no cloud, Test or automatic retry."""
    if not opt_in:
        raise ValueError("Explicit owner opt-in required before data access")
    if (not isinstance(qualification, dict) or qualification.get("status") != "PASS"
            or qualification.get("code_sha256") != base.b1.digest_json(code_hashes())
            or qualification.get("mps_generated_step") is not True):
        raise ValueError("Current generated qualification and MPS step required")
    root, weights, output = Path(root), Path(weights), Path(output)
    rows, ids, labels, groups, folds, bindings = metadata(root, output)
    bindings["qualification_sha256"] = base.b1.digest_json(qualification)
    base.legacy.authorise(authorization, SCOPE, bindings, opt_in=True)
    if (weights.is_symlink() or not weights.is_file() or base.legacy.sha256(weights) != WEIGHTS_SHA
            or not torch.backends.mps.is_available()):
        raise ValueError("Existing trusted ImageNet weights and MPS required")
    if output.exists() or output.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(output.resolve()):
        raise ValueError("Fresh output separate from bundle required")
    base.legacy.new_ignored_output(output, "data")
    if ATTEMPT.exists():
        raise FileExistsError("One-run authorization already consumed")
    output.mkdir(parents=True, exist_ok=False)
    protocol = {"config": CONFIG, "bindings": bindings, "ids": ids, "groups": groups,
                "folds": folds.tolist(), "authorization": authorization, "qualification": qualification}
    base.bundle.write_json(output / "protocol.json", protocol)
    consume_attempt(ATTEMPT, authorization)
    started = time.perf_counter()
    try:
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        raw = weights.read_bytes()
        if hashlib.sha256(raw).hexdigest() != WEIGHTS_SHA:
            raise ValueError("Weights changed before tensor decoding")
        initial_weights = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
        def factory():
            from torchvision.models import efficientnet_b0
            model = efficientnet_b0(weights=None)
            model.load_state_dict(initial_weights, strict=True)
            model.classifier[-1] = torch.nn.Linear(1280, 4)
            return model
        # Read and normalize exactly680Training views once; no Validation/CAM iterator.
        arrays = np.empty((680, 3, 224, 224), dtype=np.float32)
        for index, row in enumerate(rows):
            values = base.bundle.model_array(base.legacy.safe_file(root, row["model_path"]), row["model_sha256"])
            arrays[index] = base.b1.normalize(values)
        base.bundle.write_json(output / "payload_access.json", {
            "Training_model_arrays": len(rows), "Validation_arrays": 0, "CAM_arrays": 0,
            "Test_arrays": 0, "held_arrays": 0, "ids": ids})
        def save_fit(fold, arm, model, result):
            path = output / f"fold{fold}_{arm}"
            path.mkdir()
            torch.save({"version": VERSION, "grades": [1, 2, 3, 4], "fold": fold, "arm": arm,
                        "bindings": bindings,
                        "model": {name: value.detach().cpu() for name, value in model.state_dict().items()}},
                       path / "final.pt")
            base.bundle.write_json(path / "fit.json", {key: value for key, value in result.items() if key != "probabilities"})
        def progress(item):
            print(json.dumps(item), flush=True)
        result = execute_comparison(arrays, labels, ids, groups, folds, factory, "mps", 5, 16, save_fit, progress)
        torch.mps.synchronize()
        np.savez(output / "oof.npz", ids=np.array(ids), labels=labels, groups=np.array(groups),
                 folds=folds, **result["probabilities"])
        delta = metric_differences(result["metrics"])
        if base.b1.digest_json(code_hashes()) != bindings["code_sha256"]:
            raise ValueError("Bound source changed during experiment")
        if base.legacy.sha256(weights) != WEIGHTS_SHA:
            raise ValueError("Original ImageNet weights changed")
        summary = {"version": VERSION, "status": "completed", "notice": base.legacy.NOTICE,
                   "config": CONFIG, "bindings": bindings, "metrics": result["metrics"],
                   "last_block_minus_head_only": delta, "fit_count": result["fit_count"],
                   "fit_records": result["fit_records"], "oof_sha256": base.legacy.sha256(output / "oof.npz"),
                   "runtime": {"python": platform.python_version(), "torch": str(torch.__version__),
                               "numpy": np.__version__, "device": "mps",
                               "seconds": time.perf_counter() - started,
                               "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2},
                   "test_used": False, "validation53_used": False,
                   "qualified_labels_approved": False, "participant_independence_verified": False}
        base.bundle.write_json(output / "results.json", summary)
        base.bundle.write_json(output / "COMPLETE.json", {"results_sha256": base.legacy.sha256(output / "results.json")})
        return summary
    except Exception as error:
        base.bundle.write_json(output / "FAILED.json", {"error_type": type(error).__name__, "message": str(error),
                                                       "attempt_consumed": True})
        raise
