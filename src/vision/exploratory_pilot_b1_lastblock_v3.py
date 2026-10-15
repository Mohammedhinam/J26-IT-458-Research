"""One authorized last-bottleneck stage; v1/v2 and final research gates stay intact."""
from dataclasses import asdict, replace
from pathlib import Path
import hashlib
import json
import platform
import time

from PIL import Image
import numpy as np

from src.vision import exploratory_pilot_b1_balanced_v2 as weighted
from src.vision import exploratory_pilot_b1_v1 as base
from src.vision import exploratory_bundle as legacy
from src.vision import train_pipeline as trainer
from src.vision import model_pipeline as models


VERSION = "pp1-b1-last-bottleneck-v3"
SCOPE = "run_cloud_exploratory_b1_lastblock_v3"
INITIAL_SHA = "c84936ad7af7366e44e4ae2456c00ba748bae47b983ef9e0df204ce80c386dbf"
ORIGIN_RUN = "pp1_b1_balanced_v2_20261015T150352287886Z"
BLOCK_LR = .00001
HEAD_NAMES = ("fc.weight", "fc.bias")
BLOCK_NAMES = tuple("layer4.2.conv" + str(i) + ".weight" for i in (1, 2, 3))


def configuration(device="cuda"):
    return replace(weighted.configuration(device), freeze_backbone=False, unfreeze_prefixes=("layer4.2",))


def protocol():
    return {**weighted.protocol(), "version": VERSION, "training": asdict(configuration()),
            "single_change": None, "stage": "selected final bottleneck fine-tuning, not a single-factor causal test",
            "initial_checkpoint_sha256": INITIAL_SHA, "initial_checkpoint_origin": ORIGIN_RUN,
            "trainable_names": list(HEAD_NAMES + BLOCK_NAMES),
            "optimizer_groups": {"head": .001, "last_bottleneck": BLOCK_LR},
            "batchnorm_affine_and_statistics": "all_frozen", "optimizer_state": "fresh_Adam",
            "reference": "verified unweighted v1 and weighted head-only v2; do not rerun"}


def code_hashes():
    return {**weighted.code_hashes(), "exploratory_pilot_b1_lastblock_v3.py": legacy.sha256(__file__),
            "verify_b1_lastblock_runtime_v3.py": legacy.sha256(Path(__file__).with_name("verify_b1_lastblock_runtime_v3.py"))}


def validate_initial_metadata(state):
    """Require the exact prior stage's schema/protocol/identity before using tensors."""
    context = state.get("context", {})
    if (state.get("version") != weighted.VERSION or state.get("schema") != list(base.GRADES)
            or state.get("epoch") != 1
            or trainer.digest(state.get("config")) != trainer.digest(weighted.protocol()["training"])
            or trainer.digest(context.get("protocol")) != trainer.digest(weighted.protocol())
            or context.get("manifest_sha256") != weighted.MANIFEST_SHA
            or context.get("weights", {}).get("sha256") != weighted.WEIGHTS_SHA
            or context.get("source_hashes") != weighted.code_hashes()
            or state.get("identity") != trainer.digest({"context": context, "config": state.get("config")})):
        raise ValueError("Pinned v2 best-epoch schema, protocol and provenance required")


def read_initial_checkpoint(path, trusted_sha):
    """Generic hash-bound reader also tested with generated checkpoints; no model execution."""
    path = Path(path)
    if path.is_symlink() or not path.is_file() or legacy.sha256(path) != trusted_sha:
        raise ValueError("Initial checkpoint SHA/path mismatch")
    torch = models._torch()
    state = torch.load(path, map_location="cpu", weights_only=True)
    validate_initial_metadata(state)
    if not state.get("model") or any(not torch.isfinite(value).all() for value in state["model"].values()):
        raise ValueError("Finite initial model tensors required")
    if state["model"]["fc.weight"].shape != (4, 2048) or state["model"]["fc.bias"].shape != (4,):
        raise ValueError("Exact four-output ResNet50 head required")
    if legacy.sha256(path) != trusted_sha:
        raise ValueError("Initial checkpoint changed while reading")
    return state


def configure_stage(model, config):
    """Allow exactly three final-bottleneck convolution weights and the existing head."""
    torch = models._torch()
    config.validate()
    if (config.architecture != "resnet50" or config.freeze_backbone
            or config.unfreeze_prefixes != ("layer4.2",) or config.batchnorm != "frozen"
            or config.class_weight != "balanced" or config.learning_rate != .001 or config.weight_decay != 0):
        raise ValueError("Only the approved last-bottleneck recipe is supported")
    parameters = dict(model.named_parameters())
    allowed = set(HEAD_NAMES + BLOCK_NAMES)
    if not allowed <= parameters.keys() or not isinstance(model.fc, torch.nn.Linear) or model.fc.out_features != 4:
        raise ValueError("Missing or incompatible approved layer names/head")
    modules = dict(model.named_modules())
    for name in BLOCK_NAMES:
        if not isinstance(modules[name.removesuffix(".weight")], torch.nn.Conv2d):
            raise ValueError("Only the selected convolution weights may be unfrozen")
    for name, parameter in parameters.items():
        parameter.requires_grad_(name in allowed)
    # eval() freezes running statistics; requires_grad_(False) also freezes BN affine weights.
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            module.eval()
            for parameter in module.parameters():
                parameter.requires_grad_(False)
    actual = {name for name, parameter in parameters.items() if parameter.requires_grad}
    if actual != allowed or len({id(parameters[name]) for name in actual}) != 5:
        raise ValueError("Exact unique trainable-parameter allowlist required")
    groups = [{"name": "head", "params": [parameters[n] for n in HEAD_NAMES], "lr": config.learning_rate},
              {"name": "last_bottleneck", "params": [parameters[n] for n in BLOCK_NAMES], "lr": BLOCK_LR}]
    return groups


def tensor_hashes(model):
    """Small per-tensor CPU copies; save hashes, never activation or patient-pixel dumps."""
    return {name: hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
            for name, value in model.state_dict().items()}


def check_frozen(before, after):
    if set(before) != set(after):
        raise ValueError("Model tensor coverage changed")
    changed = [name for name in sorted(before) if before[name] != after[name]]
    unexpected = set(changed) - set(HEAD_NAMES + BLOCK_NAMES)
    if unexpected:
        raise ValueError("Frozen/BatchNorm tensors changed: " + ", ".join(sorted(unexpected)))
    return {"frozen_tensors_compared": len(before) - 5, "unexpected_changes": [],
            "changed_trainable_names": changed, "all_frozen_tensors_unchanged": True}


def load_stage_checkpoint(path, expected_sha, context, config):
    if legacy.sha256(path) != expected_sha:
        raise ValueError("Stage checkpoint SHA mismatch")
    state = models._torch().load(path, map_location="cpu", weights_only=True)
    if (state.get("version") != VERSION or state.get("schema") != list(base.GRADES)
            or state.get("context") != context
            or trainer.digest(state.get("config")) != trainer.digest(asdict(config))
            or state.get("identity") != trainer.digest({"context": context, "config": asdict(config)})):
        raise ValueError("Stage checkpoint provenance mismatch")
    return state


def fit(model, training, validation, config, output, context):
    """New stage loop; v2 requires a wholly frozen backbone and must remain unchanged."""
    torch = models._torch()
    trainer.seed_everything(config.seed)
    groups = configure_stage(model, config)
    measured_groups = [{"name": group["name"], "lr": group["lr"],
                        "parameters": sum(p.numel() for p in group["params"])} for group in groups]
    before = tensor_hashes(model)
    weights = weighted.training_weights([r["provisional_mgi_grade"] for r in training.records])
    model.to(config.device)
    optimizer = torch.optim.Adam(groups, weight_decay=0.)  # Fresh optimizer; never restore v2 moments.
    output = Path(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    base.bundle.write_json(output / "initial_tensor_hashes.json", before)
    loaders = {
        "Training": torch.utils.data.DataLoader(training, batch_size=config.batch_size, shuffle=True,
                                               num_workers=0, generator=torch.Generator().manual_seed(config.seed)),
        "Validation": torch.utils.data.DataLoader(validation, batch_size=config.batch_size, shuffle=False, num_workers=0)}
    history, best, bad = [], -float("inf"), 0
    identity = trainer.digest({"context": context, "config": asdict(config)})
    for epoch in range(config.epochs):
        train, _ = weighted.run_epoch(model, loaders["Training"], config, weights, optimizer)
        val, predictions = weighted.run_epoch(model, loaders["Validation"], config, weights)
        best, bad, improved = trainer.stopping_update(val["macro_f1_four_grades"], best, bad,
                                                    config.patience, config.min_delta)
        history.append({"epoch": epoch + 1, "training": train, "validation": val, "notice": legacy.NOTICE})
        check_frozen(before, tensor_hashes(model))
        state = {"version": VERSION, "schema": list(base.GRADES), "identity": identity, "context": context,
                 "config": asdict(config), "epoch": epoch + 1, "history": history, "model": model.state_dict(),
                 "optimizer": optimizer.state_dict(), "best": best, "bad_epochs": bad,
                 "class_weights": weights.tolist(), "optimizer_groups": measured_groups}
        trainer._save_checkpoint(output / "last.pt", state)
        if improved:
            trainer._save_checkpoint(output / "best.pt", state)
            best_predictions = weighted.validation_predictions(validation.records, predictions)
        print(json.dumps({"stage_epoch": epoch + 1, "training_loss": train["loss"], "validation_loss": val["loss"],
                          "validation_macro_f1": val["macro_f1_four_grades"], "improved": improved}), flush=True)
        if bad >= config.patience:
            break
    state = load_stage_checkpoint(output / "best.pt", legacy.sha256(output / "best.pt"), context, config)
    model.load_state_dict(state["model"])
    model.eval()
    after = tensor_hashes(model)
    frozen = check_frozen(before, after)
    base.bundle.write_json(output / "selected_tensor_hashes.json", after)
    base.bundle.write_json(output / "validation_predictions_best.json", best_predictions)
    return {"notice": legacy.NOTICE, "history": history, "best_epoch": state["epoch"],
            "best_validation": state["history"][-1]["validation"], "class_weights_training_only": weights.tolist(),
            "optimizer_groups": measured_groups, "frozen_tensor_checks": frozen, "test_used": False}


def validate_execution(record, output, verification):
    bound = {"bundle_manifest_sha256": weighted.MANIFEST_SHA, "protocol_sha256": trainer.digest(protocol()),
             "code_sha256": trainer.digest(code_hashes()), "initial_checkpoint_sha256": INITIAL_SHA,
             "weights_sha256": weighted.WEIGHTS_SHA, "verification_sha256": verification,
             "output_run_id": Path(output).name}
    legacy.authorise(record, SCOPE, bound, opt_in=True)
    if record.get("training_authorized") is not True or record.get("cloud_upload_authorized") is not True:
        raise ValueError("Explicit existing-development-cloud and stage-training permission required")


def run_pilot(root, initial_path, record, output, verification_directory, *, opt_in=False):
    if not opt_in:
        raise ValueError("Explicit last-bottleneck opt-in required")
    from src.vision import verify_b1_lastblock_runtime_v3 as verification
    proof = verification.require_pass(verification_directory)
    validate_execution(record, output, proof)
    root, initial_path, output = Path(root), Path(initial_path), Path(output)
    if (root.resolve() != Path("/content/b1_pp1_pilot/development")
            or output.parent.resolve() != Path("/content/b1_pp1_pilot/results")
            or initial_path.parent.name != ORIGIN_RUN or initial_path.name != "best.pt"
            or initial_path.parent.parent.resolve() != output.parent.resolve()
            or any(p.is_symlink() for p in (initial_path, *initial_path.parents, output, *output.parents))
            or Path("/content/drive").exists() or output.exists()):
        raise ValueError("Exact existing development/checkpoint paths and fresh output required")
    torch = models._torch()
    if not torch.cuda.is_available():
        raise RuntimeError("Existing CUDA GPU required; no fallback or installs")
    if legacy.sha256(initial_path) != INITIAL_SHA:
        raise ValueError("Exact v2 best checkpoint required; no replacement")
    base.bundle.verify(root, weighted.MANIFEST_SHA)
    manifest = base.bundle.load_json(legacy.safe_file(root, "bundle_manifest.json"))
    rows = {split: [r for r in manifest["records"] if r["original_split"] == split] for split in legacy.EXPECTED_COUNTS}
    datasets = {split: base.Dataset(root, records, split) for split, records in rows.items()}
    base.bundle.write_json(output.parent / ".owner_b1_lastblock_v3_attempt.json",
                           {"status": "consumed", "authorization": record})
    initial = read_initial_checkpoint(initial_path, INITIAL_SHA)
    config = configuration()
    trainer.seed_everything(config.seed)
    network = base.make_model(pretrained=False)  # Load trusted prior tensors; no pretrained downloads.
    network["model"].load_state_dict(initial["model"], strict=True)
    del initial
    context = {"version": VERSION, "notice": legacy.NOTICE, "manifest_sha256": weighted.MANIFEST_SHA,
               "initial_checkpoint_sha256": INITIAL_SHA, "protocol": protocol(), "source_hashes": code_hashes(),
               "runtime": {"python": platform.python_version(), "torch": str(torch.__version__),
                           "numpy": np.__version__, "gpu": torch.cuda.get_device_name()},
               "synthetic_verification_sha256": proof, "qualified_labels_approved": False,
               "participant_independence_verified": False, "final_research_approved": False, "test_used": False}
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    result = fit(network["model"], datasets["Training"], datasets["Validation"], config, output, context)
    result.update(protocol=protocol(), initial_checkpoint_sha256=INITIAL_SHA, runtime=context["runtime"], cam=[],
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
    selected_hashes = base.bundle.load_json(output / "selected_tensor_hashes.json")
    if tensor_hashes(network["model"]) != selected_hashes:
        raise ValueError("Grad-CAM must not change selected model tensors")
    torch.cuda.synchronize()
    result["measured_runtime"] = {"fit_and_cam_seconds": time.perf_counter() - started,
                                  "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated()}
    if code_hashes() != context["source_hashes"] or legacy.sha256(initial_path) != INITIAL_SHA:
        raise ValueError("Source code or original starting checkpoint changed")
    base.bundle.write_json(output / "pilot_results.json", result)
    base.bundle.write_json(output / "training_authorization.json", record)
    return result
