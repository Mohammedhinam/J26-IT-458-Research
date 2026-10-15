"""Aggregate-only pilot diagnosis and optional read-only checkpoint inspection.

No dataset loader, model construction, inference, training or downloads.
Historical runner and its hash bindings stay unchanged.
"""
import json
import math
from pathlib import Path

import numpy as np

from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_pilot_b1_v1 as pilot
from src.vision import train_pipeline as trainer


# These are the already verified, owner-supplied first pilot's exact bindings.
RUN_ID = "pp1_b1_mgi1to4_20261015T135216375748Z"
RESULT_INDEX_SHA = "f35c0d67d336b8123426e4bafc8ea33d009cece7eb8c62353c34d31f6dd6ffb2"
OFFICIAL_WEIGHTS_SHA = "11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca"


def training_reference(training_support, validation_support):
    """Fit priors/weights on Training counts only; Validation only scores priors."""
    counts = np.asarray(training_support)
    validation = np.asarray(validation_support)
    for values in (counts, validation):
        if (values.shape != (4,) or values.dtype.kind not in "iu"
                or np.any(values < 0) or values.sum() == 0):
            raise ValueError("Four nonnegative integer grade counts required")
    if np.any(counts == 0):
        raise ValueError("Do not invent support for an absent Training grade")
    labels = np.repeat(pilot.GRADES, counts)
    validation_labels = np.repeat(pilot.GRADES, validation)
    probabilities = counts / counts.sum()
    # Reuse the existing Training-only weighting formula; this does not train.
    weights = trainer.class_weights(labels, "balanced")[1:]
    measured = pilot.metrics(validation_labels,
                             np.tile(probabilities, (len(validation_labels), 1)))
    return {"grades": list(pilot.GRADES), "training_priors": probabilities.tolist(),
            "proposed_training_only_balanced_weights": weights.tolist(),
            "proposal_activated": False, "training_prior_baseline": measured}


def analyse_results(result):
    """Summarise existing measured evidence; never infer clinical root causes."""
    if (result.get("test_used") is not False
            or trainer.digest(result.get("protocol")) != trainer.digest(pilot.protocol())):
        raise ValueError("Expected unchanged, Test-free first pilot protocol")
    history = result.get("history", [])
    if not history or len(history) > 5:
        raise ValueError("Expected the bounded pilot's recorded epochs")
    first = history[0]
    training_support = first["training"]["support"]
    validation_support = first["validation"]["support"]
    if training_support != [12, 84, 223, 361] or validation_support != [1, 13, 22, 17]:
        raise ValueError("Frozen development cohort/support mismatch")
    rows = []
    for index, epoch in enumerate(history, start=1):
        if epoch.get("epoch") != index:
            raise ValueError("Epoch order is not consecutive")
        row = {"epoch": index}
        for split, expected in (("training", training_support), ("validation", validation_support)):
            metrics = epoch[split]
            matrix = np.asarray(metrics["confusion_matrix"])
            if (matrix.shape != (4, 4) or matrix.dtype.kind not in "iu"
                    or np.any(matrix < 0) or matrix.sum(axis=1).tolist() != expected
                    or metrics["support"] != expected or metrics["n"] != sum(expected)):
                raise ValueError("Confusion matrix/support mismatch")
            loss = metrics["loss"]
            if isinstance(loss, bool) or not math.isfinite(loss) or loss < 0:
                raise ValueError("Nonnegative finite recorded loss required")
            row[split] = {"loss": loss, "predicted_counts": matrix.sum(axis=0).tolist(),
                          "macro_f1": metrics["macro_f1_four_grades"]}
        rows.append(row)
    best = result.get("best_epoch")
    if type(best) is not int or not 1 <= best <= len(rows):
        raise ValueError("Best epoch must refer to recorded history")
    return {"notice": legacy.NOTICE, "epochs": rows, "best_epoch": best,
            "references": training_reference(training_support, validation_support),
            "validation_all_grade4_each_epoch": all(
                row["validation"]["predicted_counts"] == [0, 0, 0, 53] for row in rows),
            "training_metrics_are_online": True,
            "root_cause_established": False,
            "limitations": [
                "Training metrics accumulate changing weights within each epoch, not one frozen checkpoint.",
                "No per-image logits/features or initial-head snapshot exist in these aggregate results.",
                "Imbalance and pretrained-input domain shift are hypotheses, not proven causes.",
                "The four-output pilot currently ignores class_weight in its loss; recorded mode was none."]}


def inspect_saved_checkpoints(directory, official_weights_path, code_root):
    """Optional Colab check: load hash-pinned tensors safely; no image/model IO.

    Only call with the existing owner's completed run and cached official file.
    Missing runtime/cache is a STOP, not permission to install or download.
    """
    directory = Path(directory)
    if directory.name != RUN_ID:
        raise ValueError("Only the verified completed run is supported")
    index_path = legacy.safe_file(directory, "results_file_hashes.json")
    if legacy.sha256(index_path) != RESULT_INDEX_SHA:
        raise ValueError("Result hash index changed")
    index = json.loads(index_path.read_text())
    for name in ("best.pt", "last.pt", "pilot_results.json", "source_hashes_after.json"):
        if legacy.sha256(legacy.safe_file(directory, name)) != index[name]:
            raise ValueError("Completed result payload changed: " + name)
    source_hashes = json.loads((directory / "source_hashes_after.json").read_text())
    for name, digest in source_hashes.items():
        if legacy.sha256(legacy.safe_file(code_root, name)) != digest:
            raise ValueError("Verified runtime source changed")
    official_weights_path = Path(official_weights_path)
    if (official_weights_path.is_symlink() or not official_weights_path.is_file()
            or legacy.sha256(official_weights_path) != OFFICIAL_WEIGHTS_SHA):
        raise ValueError("Original verified official cache required; no downloads")
    import torch
    # weights_only prevents ordinary arbitrary Python pickle reconstruction.
    official = torch.load(official_weights_path, map_location="cpu", weights_only=True)
    observed = []
    for filename, expected_epoch in (("best.pt", 1), ("last.pt", 3)):
        state = torch.load(directory / filename, map_location="cpu", weights_only=True)
        if (state.get("version") != pilot.VERSION or state.get("schema") != list(pilot.GRADES)
                or state.get("epoch") != expected_epoch
                or trainer.digest(state.get("config")) != trainer.digest(pilot.protocol()["training"])
                or state.get("identity") != trainer.digest({"context": state["context"], "config": state["config"]})
                or trainer.digest(state["context"].get("protocol")) != trainer.digest(pilot.protocol())):
            raise ValueError("Checkpoint provenance/schema/configuration mismatch")
        model = state["model"]
        keys = {name for name in model if not name.startswith("fc.")}
        official_keys = {name for name in official if not name.startswith("fc.")}
        if keys != official_keys:
            raise ValueError("Backbone key coverage mismatch")
        changed = [name for name in sorted(keys) if not torch.equal(model[name], official[name])]
        head = model["fc.weight"]
        bias = model["fc.bias"]
        if head.shape != (4, 2048) or bias.shape != (4,) or not torch.isfinite(head).all() or not torch.isfinite(bias).all():
            raise ValueError("Four finite head rows and biases required")
        states = state["optimizer"]["state"]
        steps = sorted(int(item["step"].item()) for item in states.values())
        expected_steps = expected_epoch * math.ceil(680 / 16)
        if len(states) != 2 or steps != [expected_steps, expected_steps]:
            raise ValueError("Unexpected head-only optimizer step coverage")
        observed.append({"checkpoint": filename, "epoch": expected_epoch,
                         "backbone_tensors_compared": len(keys), "changed_backbone_keys": changed,
                         "backbone_unchanged": not changed, "optimizer_steps": steps,
                         "head_row_l2_norms": head.norm(dim=1).tolist(), "head_biases": bias.tolist()})
        del state, model, head, bias, states
    if any(legacy.sha256(directory / name) != index[name] for name in ("best.pt", "last.pt")):
        raise ValueError("Checkpoint bytes changed during inspection")
    if legacy.sha256(official_weights_path) != OFFICIAL_WEIGHTS_SHA:
        raise ValueError("Official cached bytes changed during inspection")
    return {"notice": legacy.NOTICE, "scope": "read-only completed checkpoint diagnosis",
            "checkpoint_checks": observed, "images_accessed": False, "inference_performed": False,
            "training_performed": False, "downloads_performed": False,
            "initial_head_snapshot_available": False}
