"""Explicitly opt-in provisional PP1 pilot, separate from approved research training."""
from dataclasses import asdict
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

from src.vision import exploratory_bundle as eb
from src.vision import model_pipeline as vp
from src.vision import train_pipeline as tp

KIND = "pp1_exploratory_provisional"
WEIGHTS_NAME = "resnet50-11ad3fa6.pth"
WEIGHTS_URL = "https://download.pytorch.org/models/resnet50-11ad3fa6.pth"


def configuration(device="cuda"):
    return tp.TrainingConfig("resnet50", 16, 5, 0.001, 2, seed=42,
                            freeze_backbone=True, batchnorm="frozen", class_weight="none", device=device)


def pretrained_status(cache=None):
    """Inspect documented cache bytes only; never import/download/load a model."""
    if cache is None:
        home = Path(os.environ.get("TORCH_HOME", Path(os.environ.get("XDG_CACHE_HOME", Path.home()/".cache"))/"torch"))
        cache = home / "hub/checkpoints"
    checkpoint = Path(cache) / WEIGHTS_NAME
    digest = eb.sha256(checkpoint) if checkpoint.is_file() and not checkpoint.is_symlink() else None
    return {"notice": eb.NOTICE, "weight_enum": "ResNet50_Weights.IMAGENET1K_V2",
            "official_url": WEIGHTS_URL, "expected_path": str(checkpoint), "sha256": digest,
            "status": "documented_cache_present" if digest and digest.startswith("11ad3fa6") else "missing_or_invalid",
            "torch_installed": importlib.util.find_spec("torch") is not None,
            "torchvision_installed": importlib.util.find_spec("torchvision") is not None,
            "download_attempted": False}


def validate_fixed_bundle(bundle):
    records = eb.bundle_records(bundle)
    projected = [{"original_split": r["original_split"], "candidate_mgi_grade": r["provisional_mgi_grade"],
                  "source_record_id": r["source_record_id"]} for r in records]
    eb.fixed_cohort(projected)
    if bundle["source_draft_sha256"] != eb.DRAFT_SHA or bundle["cam_ids"] != list(eb.CAM_IDS):
        raise ValueError("Source DRAFT/fixed CAM identity mismatch")
    identity = [{k:r[k] for k in ["source_record_id", "original_image_path", "original_split",
                                 "content_group_id", "provisional_mgi_grade"]} for r in records]
    identity.sort(key=lambda r:r["source_record_id"])
    if eb.json_digest(identity) != eb.CANDIDATE_IDENTITY_SHA:
        raise ValueError("Frozen candidate identity/group/label mismatch")
    return records


def checked_labels(labels):
    values = np.asarray(labels)
    if (values.ndim != 1 or not values.size or values.dtype.kind not in "iu"
            or np.any((values < 0) | (values > 4))):
        raise ValueError("Nonempty integer labels in MGI 0..4 required")
    return values


def majority_baseline(training_labels, validation_labels):
    training_labels = checked_labels(training_labels)
    validation_labels = checked_labels(validation_labels)
    counts = np.bincount(training_labels, minlength=5)
    grade = int(counts.argmax())  # Lowest grade wins a tied largest count.
    probabilities = np.zeros((len(validation_labels), 5))
    probabilities[:, grade] = 1
    return {"notice": eb.NOTICE, "derived_from": "provisional_Training_only",
            "majority_grade": grade, "training_support": counts.tolist(),
            "validation": {"notice": eb.NOTICE, **tp.validation_metrics(validation_labels, probabilities)}}


def support_warnings(training_labels, validation_labels):
    train = np.bincount(checked_labels(training_labels), minlength=5).tolist()
    validation = np.bincount(checked_labels(validation_labels), minlength=5).tolist()
    return {"notice": eb.NOTICE, "training_support": train, "validation_support": validation,
            "unsupported_training_grades": [g for g,n in enumerate(train) if not n],
            "unsupported_validation_grades": [g for g,n in enumerate(validation) if not n],
            "scarce_validation_grades": [g for g,n in enumerate(validation) if 0 < n < 5],
            "five_class_validity_established": False,
            "interpretation": "Agreement with provisional labels; not clinical or participant-independent accuracy."}


class ProvisionalDevelopmentDataset:
    """A distinct adapter: integer tensor targets do not grant qualified approval."""
    def __init__(self, root, records, split):
        if split not in eb.EXPECTED_COUNTS or not records or any(r["original_split"] != split for r in records):
            raise ValueError("Only nonempty single-split development records")
        self.root = Path(root)
        self.records = []
        for r in records:
            if (r.get("label_status") != "provisional" or r.get("qualified_label_approved") is not False
                    or type(r.get("provisional_mgi_grade")) is not int
                    or r["provisional_mgi_grade"] not in vp.MGI_GRADES):
                raise ValueError("Provisional provenance required")
            eb.relative_path(r["image_path"])
            # This in-memory target is for the numerical loop only, not an approved manifest.
            self.records.append({**r, "mgi_grade": r["provisional_mgi_grade"]})

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        row = self.records[index]
        path = eb.safe_file(self.root, row["image_path"])
        with Image.open(path) as source:
            if source.mode != "RGB":
                raise ValueError("Explicit RGB input required")
            prepared = vp.preprocess_rgb(source)
        return prepared.normalized_chw, row["mgi_grade"]


def verify_checkpoint(path, expected_hash, context, config):
    """Hash before safe deserialisation; never accept a final/foreign checkpoint."""
    if eb.sha256(path) != expected_hash:
        raise ValueError("Checkpoint byte integrity mismatch")
    state = vp._torch().load(path, map_location="cpu", weights_only=True)
    identity = tp.digest({"config": asdict(config), "context": context})
    if (state.get("schema") != list(vp.MGI_GRADES) or state.get("context") != context
            or state.get("identity") != identity or state.get("config") != asdict(config)
            or context.get("experiment_kind") != KIND or context.get("notice") != eb.NOTICE
            or context.get("qualified_labels_approved") is not False
            or context.get("participant_independence_verified") is not False):
        raise ValueError("Exploratory checkpoint provenance/configuration mismatch")
    return state


def save_cam(model, layer, root, row, output, checkpoint_hash):
    """Metadata-safe full-resolution development copies only; never a Test image."""
    if (row.get("original_split") != "Validation" or row.get("source_record_id") not in eb.CAM_IDS
            or row.get("cam_original_path") != "cam/" + row["source_record_id"] + ".png"):
        raise ValueError("Only fixed eligible Validation Grad-CAM originals")
    path = eb.safe_file(root, row["cam_original_path"])
    eb.verify_rgb_export(path, {"sha256": row["cam_payload_sha256"],
                               "rgb_sha256": row["cam_rgb_sha256"], "dimensions": row["cam_dimensions"]})
    with Image.open(path) as source:
        prepared = vp.preprocess_rgb(source)
    result = vp.class_gradcam(model, layer, prepared)
    directory = output / "gradcam" / row["source_record_id"].replace("/", "_")
    directory.mkdir(parents=True, exist_ok=False)
    metadata = PngImagePlugin.PngInfo()
    metadata.add(b"sRGB", b"\x01")
    metadata.add_text("notice", eb.NOTICE)
    for name in ["original", "heatmap", "overlay"]:
        Image.fromarray(result[name]).save(directory / (name + ".png"), pnginfo=metadata)
    panel = Image.new("RGB", (1800, 520), "white")
    draw = ImageDraw.Draw(panel)
    draw.text((12, 10), eb.NOTICE, fill="black", font=ImageFont.load_default(size=20))
    for index,name in enumerate(["original", "heatmap", "overlay"]):
        image = Image.fromarray(result[name]); image.thumbnail((590, 450))
        panel.paste(image, (600*index+(600-image.width)//2, 60+(450-image.height)//2))
        draw.text((600*index+12, 37), name, fill="black")
    panel.save(directory / "three_panel.png", pnginfo=metadata)
    summary = {k:v for k,v in result.items() if k not in {"original", "heatmap", "overlay", "cam"}}
    summary.update(notice=eb.NOTICE, source_record_id=row["source_record_id"], checkpoint_sha256=checkpoint_hash,
                   unsupported_prediction=result["mgi_schema_grade"] == 0, clinical_validation=False)
    (directory / "explanation.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return summary


def run_pilot(bundle_root, authorization, output_dir, opt_in=False):
    print(eb.NOTICE)
    if not opt_in:
        raise ValueError("Explicit owner opt-in required before data access")
    config = configuration()
    config.validate()
    manifest = eb.safe_file(bundle_root, "bundle_manifest.json")
    weights = pretrained_status()
    eb.authorise(authorization, "run_exploratory", {
        "source_draft_sha256": eb.DRAFT_SHA, "bundle_manifest_sha256": eb.sha256(manifest),
        "config_sha256": tp.digest(asdict(config)), "weights_sha256": weights["sha256"],
        "weights_source_url": WEIGHTS_URL, "code_sha256": eb.json_digest(eb.source_code_hashes()),
        "output_run_id": Path(output_dir).name}, opt_in)
    if weights["status"] != "documented_cache_present":
        raise FileNotFoundError("Documented ResNet-50 V2 checkpoint missing/invalid; no automatic download")
    root = Path(bundle_root).resolve()
    if not root.is_relative_to(Path("/content/pp1_exploratory_v1/data")) or Path("/content/drive").exists():
        raise ValueError("Use a fresh isolated Colab data root without Drive mount")
    torch = vp._torch()
    if not torch.cuda.is_available():
        raise RuntimeError("Authorised pilot requires a GPU; no silent CPU fallback")
    bundle, records = eb.validate_bundle(root)
    validate_fixed_bundle(bundle)
    output = eb.new_ignored_output(output_dir, "models/exploratory_pp1")
    selected = {s:[r for r in records if r["original_split"]==s] for s in eb.EXPECTED_COUNTS}
    datasets = {s:ProvisionalDevelopmentDataset(root,selected[s],s) for s in selected}
    labels = {s:[r["provisional_mgi_grade"] for r in selected[s]] for s in selected}
    context = {"experiment_kind": KIND, "notice": eb.NOTICE, "qualified_labels_approved": False,
               "participant_independence_verified": False, "source_draft_sha256": eb.DRAFT_SHA,
               "bundle_manifest_sha256": eb.sha256(manifest), "weights_sha256": weights["sha256"],
               "authorization": authorization,
               "source_hashes": {Path(p).name:eb.sha256(p) for p in [__file__,eb.__file__,tp.__file__,vp.__file__]},
               "runtime": {"python":sys.version, "torch":str(torch.__version__), "numpy":np.__version__,
                           "torchvision":version("torchvision"), "Pillow":version("Pillow"),
                           "gpu":torch.cuda.get_device_name(), "cpu_threads":torch.get_num_threads()},
               "purpose": "exploratory_provisional_only"}
    tp.seed_everything(config.seed)
    model = vp.make_model("resnet50", pretrained=True, allow_download=False, freeze_backbone=True)
    # Reuse the numerical engine; do not touch or impersonate its approved API.
    result = tp._fit(model["model"], datasets["Training"], datasets["Validation"], config, output, context)
    result.update(notice=eb.NOTICE, experiment_kind=KIND, participant_independence_verified=False)
    for epoch in result["history"]:
        epoch["notice"] = eb.NOTICE
        for split in ["training", "validation"]:
            epoch[split]["notice"] = eb.NOTICE
    # Only files in this new scaffold-owned output are updated.
    (output / "history.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    hashes = {name:eb.sha256(output/name) for name in ["best.pt", "last.pt"]}
    best = verify_checkpoint(output/"best.pt", hashes["best.pt"], context, config)
    model["model"].load_state_dict(best["model"])
    majority = majority_baseline(labels["Training"], labels["Validation"])
    summary = {"notice": eb.NOTICE, "experiment_kind": KIND, "pilot": result,
               "majority_baseline": majority, "support_warnings":support_warnings(*labels.values()),
               "checkpoint_sha256": hashes, "final_research_approved":False,
               "test_used":False, "gradcam":[]}
    for identifier in eb.CAM_IDS:
        row = next(r for r in selected["Validation"] if r["source_record_id"]==identifier)
        summary["gradcam"].append(save_cam(model["model"],model["cam_layer"],root,row,output,hashes["best.pt"]))
    (output/"pilot_results.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n")
    return summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description=eb.NOTICE)
    parser.add_argument("--check-weights", action="store_true")
    parser.add_argument("--bundle-root")
    parser.add_argument("--authorization")
    parser.add_argument("--output")
    parser.add_argument("--exploratory-provisional", action="store_true")
    args = parser.parse_args()
    if args.check_weights:
        print(json.dumps(pretrained_status(), indent=2))
        return
    if not all([args.bundle_root,args.authorization,args.output]):
        parser.error("Explicit bundle, authorization and new output required")
    result = run_pilot(args.bundle_root,json.loads(Path(args.authorization).read_text()),args.output,args.exploratory_provisional)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
