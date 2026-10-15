"""One owner-authorized Training-balanced comparison; historical v1 unchanged.

Uses the same B1 Dataset, model factory, metrics, Grad-CAM and checkpoint writer.
Only the Training objective changes. No implicit data/weights downloads.
"""
from dataclasses import asdict, replace
from pathlib import Path
import json
import platform

import numpy as np
from PIL import Image

from src.vision import exploratory_pilot_b1_v1 as base
from src.vision import exploratory_bundle as legacy
from src.vision import train_pipeline as trainer
from src.vision import model_pipeline as models


VERSION = "pp1-b1-balanced-mgi1to4-v2"
SCOPE = "run_cloud_exploratory_b1_balanced_v2"
MANIFEST_SHA = "8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f"
WEIGHTS_SHA = "11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca"


def configuration(device="cuda"):
    return replace(base.configuration(device), class_weight="balanced")


def protocol():
    return {**base.protocol(), "version": VERSION, "training": asdict(configuration()),
            "single_change": "Training-only balanced cross-entropy",
            "weight_formula": "N_Training/(4*n_Training_grade)",
            "batch_objective": "sum(w_target*CE)/sum(w_target)",
            "loss_reported": "unweighted_cross_entropy_per_sample",
            "probabilities_saved": "best_checkpoint_Validation_only",
            "reference": "verified unweighted pilot v1; do not retrain reference"}


def code_hashes():
    directory = Path(__file__).parent
    return {**base.code_hashes(), "exploratory_pilot_b1_balanced_v2.py": legacy.sha256(__file__),
            "verify_b1_balanced_runtime_v2.py": legacy.sha256(directory / "verify_b1_balanced_runtime_v2.py")}


def training_weights(labels):
    labels = base.checked_grades(labels)
    if set(labels.tolist()) != set(base.GRADES):
        raise ValueError("All four observed Training grades need real support")
    return trainer.class_weights(labels, "balanced")[1:]


def weighted_objective(losses, targets, weights):
    """Match torch weighted-mean CE; never divide weighted sums by batch size."""
    torch = models._torch()
    if (losses.ndim != 1 or not losses.numel() or targets.shape != losses.shape
            or targets.dtype != torch.long or weights.shape != (4,)
            or not torch.isfinite(losses).all() or torch.any(losses < 0)
            or not torch.isfinite(weights).all() or torch.any(weights <= 0)
            or torch.any((targets < 0) | (targets > 3))):
        raise ValueError("Finite per-case CE, valid four-grade indices and positive weights required")
    sample_weights = weights[targets]
    return (losses * sample_weights).sum() / sample_weights.sum()


def run_epoch(model, loader, config, weights, optimizer=None):
    torch = models._torch()
    trainer.training_mode(model, config) if optimizer is not None else model.eval()
    weights = torch.as_tensor(weights, dtype=torch.float32, device=config.device)
    labels, probabilities = [], []
    raw_sum, weighted_sum, weight_sum = 0., 0., 0.
    with torch.set_grad_enabled(optimizer is not None):
        for values, target in loader:
            values = values.to(config.device, dtype=torch.float32)
            target = target.to(config.device, dtype=torch.long)
            if not torch.isfinite(values).all():
                raise ValueError("Non-finite model inputs")
            if optimizer is not None:
                optimizer.zero_grad(set_to_none=True)
            logits = model(values)
            if logits.shape != (len(target), 4) or not torch.isfinite(logits).all():
                raise ValueError("Four finite logits required")
            losses = torch.nn.functional.cross_entropy(logits, target, reduction="none")
            objective = weighted_objective(losses, target, weights)
            if not torch.isfinite(objective):
                raise ValueError("Non-finite objective")
            if optimizer is not None:
                objective.backward()
                optimizer.step()
            raw_sum += float(losses.detach().sum())
            weighted_sum += float((losses.detach() * weights[target]).sum())
            weight_sum += float(weights[target].sum())
            labels.extend((target.detach().cpu() + 1).tolist())
            probabilities.extend(logits.detach().softmax(1).cpu().tolist())
    if not labels:
        raise ValueError("Nonempty development epoch required")
    return {"loss": raw_sum / len(labels), "weighted_ce_diagnostic": weighted_sum / weight_sum,
            **base.metrics(labels, probabilities)}, {"labels": labels, "probabilities": probabilities}


def validation_predictions(rows, evidence):
    """Keep actual probabilities and original Validation IDs in local results only."""
    labels = base.checked_grades(evidence["labels"])
    probabilities = np.asarray(evidence["probabilities"], dtype=float)
    base.metrics(labels, probabilities)
    if len(rows) != len(labels):
        raise ValueError("Prediction coverage mismatch")
    records, seen = [], set()
    for row, label, values in zip(rows, labels.tolist(), probabilities.tolist()):
        identifier = row["source_record_id"]
        if (row["original_split"] != "Validation" or not identifier.startswith("Validation/")
                or identifier in legacy.NP015_IDS or identifier in seen
                or row["provisional_mgi_grade"] != label):
            raise ValueError("Validation-only unique original label coverage required")
        seen.add(identifier)
        records.append({"source_record_id": identifier, "original_split": "Validation",
                        "provisional_mgi_grade": label, "probabilities_mgi1_to4": values,
                        "predicted_mgi_grade": base.GRADES[int(np.argmax(values))]})
    return {"notice": legacy.NOTICE, "grades": list(base.GRADES), "records": records}


def load_checkpoint(path, expected_sha, context, config):
    if legacy.sha256(path) != expected_sha:
        raise ValueError("Checkpoint SHA mismatch")
    state = models._torch().load(path, map_location="cpu", weights_only=True)
    if (state.get("version") != VERSION or state.get("schema") != list(base.GRADES)
            or state.get("context") != context
            or state.get("identity") != trainer.digest({"context": context, "config": asdict(config)})):
        raise ValueError("Balanced checkpoint provenance mismatch")
    return state


def fit(model, training, validation, config, output, context):
    """Separate small loop: v1 hardcodes unweighted CE and cannot accept a loss callback."""
    torch = models._torch()
    config.validate()
    if config.class_weight != "balanced" or not config.freeze_backbone or config.batchnorm != "frozen":
        raise ValueError("This comparison requires balanced loss and a frozen backbone/BN")
    weights = training_weights([row["provisional_mgi_grade"] for row in training.records])
    trainer.seed_everything(config.seed)
    trainer.configure_trainable_layers(model, config)
    model.to(config.device)
    output = Path(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=config.learning_rate)
    loaders = {
        "Training": torch.utils.data.DataLoader(training, batch_size=config.batch_size, shuffle=True,
                                               num_workers=0, generator=torch.Generator().manual_seed(config.seed)),
        "Validation": torch.utils.data.DataLoader(validation, batch_size=config.batch_size, shuffle=False, num_workers=0)}
    history, best, bad = [], -float("inf"), 0
    identity = trainer.digest({"context": context, "config": asdict(config)})
    trainer._save_checkpoint(output / "initial_head.pt", {
        "version": VERSION, "schema": list(base.GRADES), "identity": identity,
        "head": {name: value.detach().cpu().clone() for name, value in model.fc.state_dict().items()}})
    for epoch in range(config.epochs):
        train, _ = run_epoch(model, loaders["Training"], config, weights, optimizer)
        val, predictions = run_epoch(model, loaders["Validation"], config, weights)
        best, bad, improved = trainer.stopping_update(val["macro_f1_four_grades"], best, bad,
                                                    config.patience, config.min_delta)
        history.append({"epoch": epoch + 1, "training": train, "validation": val, "notice": legacy.NOTICE})
        state = {"version": VERSION, "schema": list(base.GRADES), "identity": identity, "context": context,
                 "config": asdict(config), "epoch": epoch + 1, "history": history, "model": model.state_dict(),
                 "optimizer": optimizer.state_dict(), "best": best, "bad_epochs": bad, "class_weights": weights.tolist()}
        trainer._save_checkpoint(output / "last.pt", state)
        if improved:
            trainer._save_checkpoint(output / "best.pt", state)
            best_predictions = validation_predictions(validation.records, predictions)
        print(json.dumps({"epoch": epoch + 1, "training_loss": train["loss"], "validation_loss": val["loss"],
                          "validation_macro_f1": val["macro_f1_four_grades"], "improved": improved}), flush=True)
        if bad >= config.patience:
            break
    state = load_checkpoint(output / "best.pt", legacy.sha256(output / "best.pt"), context, config)
    model.load_state_dict(state["model"])
    model.eval()
    base.bundle.write_json(output / "validation_predictions_best.json", best_predictions)
    return {"notice": legacy.NOTICE, "history": history, "best_epoch": state["epoch"],
            "best_validation": state["history"][-1]["validation"], "class_weights_training_only": weights.tolist(),
            "best_validation_macro_f1_four_grades": state["best"], "test_used": False}


def validate_execution(authorization, output, trusted_manifest_sha256, weights, verification):
    bindings = {"bundle_manifest_sha256": MANIFEST_SHA, "protocol_sha256": trainer.digest(protocol()),
                "code_sha256": trainer.digest(code_hashes()), "weights_sha256": WEIGHTS_SHA,
                "verification_sha256": verification, "output_run_id": Path(output).name}
    legacy.authorise(authorization, SCOPE, bindings, opt_in=True)
    if (trusted_manifest_sha256 != MANIFEST_SHA or weights.get("sha256") != WEIGHTS_SHA
            or weights.get("status") != "documented_cache_present"
            or authorization.get("cloud_upload_authorized") is not True
            or authorization.get("training_authorized") is not True):
        raise ValueError("Pinned cohort, existing authentic weights and explicit owner scope required")


def run_pilot(root, authorization, output, verification_directory, *, opt_in=False):
    if not opt_in:
        raise ValueError("Explicit balanced comparison opt-in required")
    from src.vision import verify_b1_balanced_runtime_v2 as verification
    proof = verification.require_pass(verification_directory)
    root, output = Path(root), Path(output)
    weights = base.original_pilot.pretrained_status()
    validate_execution(authorization, output, MANIFEST_SHA, weights, proof)
    if (root.resolve() != Path("/content/b1_pp1_pilot/development")
            or output.parent.resolve() != Path("/content/b1_pp1_pilot/results")
            or any(path.is_symlink() for path in (output, *output.parents))
            or Path("/content/drive").exists() or output.exists()):
        raise ValueError("Existing isolated development root and fresh results required")
    torch = models._torch()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; no CPU fallback")
    base.bundle.verify(root, MANIFEST_SHA)
    manifest = base.bundle.load_json(legacy.safe_file(root, "bundle_manifest.json"))
    rows = {split: [r for r in manifest["records"] if r["original_split"] == split]
            for split in legacy.EXPECTED_COUNTS}
    datasets = {split: base.Dataset(root, records, split) for split, records in rows.items()}
    # One exclusive marker for the entire approved experiment, not just a new run ID.
    marker = output.parent / ".owner_b1_balanced_v2_attempt.json"
    base.bundle.write_json(marker, {"status": "consumed", "authorization": authorization})
    config = configuration()
    trainer.seed_everything(config.seed)
    network = base.make_model(pretrained=True)  # Fresh original initialization; never resume v1.
    context = {"version": VERSION, "notice": legacy.NOTICE, "manifest_sha256": MANIFEST_SHA,
               "protocol": protocol(), "source_hashes": code_hashes(), "weights": weights,
               "runtime": {"python": platform.python_version(), "torch": str(torch.__version__),
                           "gpu": torch.cuda.get_device_name(), "numpy": np.__version__},
               "qualified_labels_approved": False, "participant_independence_verified": False,
               "final_research_approved": False, "test_used": False, "synthetic_verification_sha256": proof}
    result = fit(network["model"], datasets["Training"], datasets["Validation"], config, output, context)
    result.update(protocol=protocol(), weights=weights, cam=[],
                  majority_baseline=base.majority_baseline(
                      [r["provisional_mgi_grade"] for r in rows["Training"]],
                      [r["provisional_mgi_grade"] for r in rows["Validation"]]))
    for identifier in legacy.CAM_IDS:
        row = next(r for r in rows["Validation"] if r["source_record_id"] == identifier)
        views = base.gradcam(network["model"], network["cam_layer"], base.cam_input(root, row))
        directory = output / "gradcam" / identifier.replace("/", "_")
        directory.mkdir(parents=True)
        for name in ("original", "heatmap", "overlay"):
            Image.fromarray(views[name]).save(directory / (name + ".png"))
        result["cam"].append({"source_record_id": identifier,
                              **{k: v for k, v in views.items() if k not in ("original", "heatmap", "overlay", "cam")}})
    if code_hashes() != context["source_hashes"] or legacy.sha256(weights["expected_path"]) != WEIGHTS_SHA:
        raise ValueError("Code or official cached weights changed during the run")
    base.bundle.write_json(output / "pilot_results.json", result)
    base.bundle.write_json(output / "training_authorization.json", authorization)
    return result
