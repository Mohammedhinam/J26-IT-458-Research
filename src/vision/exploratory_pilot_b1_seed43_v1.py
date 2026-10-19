"""One local seed-stability run for the isolated four-grade B1 pilot.

This wrapper reuses the verified v2 checkpoint and v3 training functions. It
does not alter the five-grade research model, labels, bundle, or final gates.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import platform
from pathlib import Path
import resource
import time
import zipfile

from src.vision import b1_development_bundle_v1 as bundle
from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_pilot_b1_v1 as pilot
from src.vision import exploratory_pilot_b1_balanced_v2 as weighted
from src.vision import exploratory_pilot_b1_lastblock_v3 as stage
from src.vision import model_pipeline as models
from src.vision import train_pipeline as trainer


VERSION = "pp1-b1-lastblock-seed43-v1"
SCOPE = "run_local_exploratory_b1_lastblock_seed43_v1"
MANIFEST_SHA = "8e7ff195009a5e781c216795fd2a943db17a0b3ec8fd1c84760f3bf9878a4c9f"
DATA_ARCHIVE_SHA = "a8a4f7f339c589f81335d7afb663f4cf62d30e217f65bc480683d0a770afed70"
V2_ARCHIVE_SHA = "ab9d61f3d59c807b9181e6937f1099364f3cc06dda6607745bdf5fc11cae8a82"
INITIAL_SHA = stage.INITIAL_SHA
OWNER_REQUEST_SHA = "db8da8723c010ea6c0ee5a32b5dfb68603b31b634dee42036353dbd14042bbc4"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data/vision/pp1_b1_dev_v1_20261015T085436527238Z"
DATA_ARCHIVE = PROJECT_ROOT / "data/vision/pp1_b1_dev_v1_20261015T085436527238Z.zip"
V2_ARCHIVE = Path("/Users/vinuthanvinuthan/Downloads/pp1_b1_balanced_v2_20261015T150352287886Z_results.zip")
CAM_IDS = tuple(legacy.CAM_IDS)


@dataclass(frozen=True)
class LocalTrainingConfig(trainer.TrainingConfig):
    """The common trainer rules, plus a local MPS device option."""

    def validate(self):
        values = asdict(self)
        device = values["device"]
        if device not in {"cpu", "mps"}:
            raise ValueError("This local experiment permits only CPU or MPS")
        values["device"] = "cpu"
        trainer.TrainingConfig(**values).validate()
        torch = models._torch()
        if device == "mps" and not torch.backends.mps.is_available():
            raise ValueError("MPS is unavailable; use the explicit CPU fallback")


def configuration(device="mps"):
    """Keep the v3 recipe fixed and prospectively change only seed 42 to 43."""
    values = asdict(stage.configuration(device="cpu"))
    values["seed"] = 43
    values["device"] = device
    return LocalTrainingConfig(**values)


def protocol(device="mps"):
    config = configuration(device)
    config.validate()
    return {
        "version": VERSION,
        "parent_recipe": stage.VERSION,
        "change_from_seed42_reference": "random seed 42 -> 43 only; no seed search",
        "training": asdict(config),
        "starting_checkpoint_sha256": INITIAL_SHA,
        "starting_checkpoint_origin": stage.ORIGIN_RUN,
        "image_ids": "same frozen 680 Training / 53 Validation B1 bundle",
        "selection": "Validation four-grade macro-F1; development-only and selection-optimistic",
        "mgi_outputs": [1, 2, 3, 4],
        "research_mgi_schema_unchanged": [0, 1, 2, 3, 4],
        "held_count_excluded": 181,
        "np015_excluded": list(legacy.NP015_IDS),
        "protected_test_access": False,
        "pretrained_download": False,
        "gradcam_rerun": False,
        "notice": legacy.NOTICE,
    }


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def code_hashes():
    directory = Path(__file__).parent
    names = [
        "exploratory_pilot_b1_seed43_v1.py",
        "exploratory_pilot_b1_lastblock_v3.py",
        "exploratory_pilot_b1_balanced_v2.py",
        "exploratory_pilot_b1_v1.py",
        "b1_development_bundle_v1.py",
        "exploratory_bundle.py",
        "model_pipeline.py",
        "train_pipeline.py",
        "colour_b1_prototype.py",
        "colour_b1_streaming.py",
    ]
    return {name: sha256_file(directory / name) for name in names}


def bindings(output_id, device="mps"):
    return {
        "bundle_manifest_sha256": MANIFEST_SHA,
        "development_archive_sha256": DATA_ARCHIVE_SHA,
        "v2_results_archive_sha256": V2_ARCHIVE_SHA,
        "initial_checkpoint_sha256": INITIAL_SHA,
        "owner_request_sha256": OWNER_REQUEST_SHA,
        "protocol_sha256": trainer.digest(protocol(device)),
        "code_sha256": trainer.digest(code_hashes()),
        "output_run_id": output_id,
    }


def validate_records(records):
    """Fail closed unless the exact development membership remains frozen."""
    # Reject split names before checking any label field.
    for row in records:
        if row.get("original_split") not in legacy.EXPECTED_COUNTS:
            raise ValueError("Test or nondevelopment record rejected before label access")
    if len(records) != 733:
        raise ValueError("Exactly 733 development records are required")
    counts = {split: 0 for split in legacy.EXPECTED_COUNTS}
    groups = set()
    identifiers = set()
    grades = {split: [0, 0, 0, 0, 0] for split in counts}
    for row in records:
        split = row.get("original_split")
        identifier = row.get("source_record_id")
        if split not in counts:
            raise ValueError("Test or nondevelopment record rejected before label access")
        if (not isinstance(identifier, str) or not identifier.startswith(split + "/")
                or identifier in identifiers or identifier in legacy.NP015_IDS):
            raise ValueError("Duplicate, malformed, or NP015 record is forbidden")
        if (row.get("label_status") != "provisional"
                or row.get("qualified_label_approved") is not False
                or type(row.get("provisional_mgi_grade")) is not int
                or row["provisional_mgi_grade"] not in pilot.GRADES):
            raise ValueError("Only unchanged provisional MGI 1-4 records are permitted")
        group = row.get("content_group_id")
        if not isinstance(group, str) or not group or group in groups:
            raise ValueError("Missing, repeated, or cross-split content group")
        groups.add(group)
        identifiers.add(identifier)
        counts[split] += 1
        grades[split][row["provisional_mgi_grade"]] += 1
    if counts != legacy.EXPECTED_COUNTS:
        raise ValueError("Frozen 680/53 split counts changed")
    if grades != legacy.EXPECTED_GRADES:
        raise ValueError("Frozen provisional grade support changed")
    if not set(CAM_IDS) <= identifiers:
        raise ValueError("The fixed Validation CAM records are absent from the bundle")
    return {"records": len(records), "counts": counts, "grade_counts": grades,
            "unique_content_groups": len(groups), "test_records": 0,
            "held_records_included": 0, "np015_included": 0}


def extract_v2_best(archive, destination):
    """Extract only the trusted best.pt member; do not unpack prior CAM/results."""
    archive = Path(archive)
    if archive.is_symlink() or sha256_file(archive) != V2_ARCHIVE_SHA:
        raise ValueError("Verified v2 result ZIP hash required")
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Fresh checkpoint output path required")
    with zipfile.ZipFile(archive) as zipped:
        info = zipped.getinfo("best.pt")
        if info.is_dir() or info.file_size > 500 * 1024 * 1024:
            raise ValueError("Unexpected checkpoint member")
        digest = hashlib.sha256()
        with zipped.open(info) as source, destination.open("xb") as target:
            while True:
                block = source.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
                target.write(block)
    if digest.hexdigest() != INITIAL_SHA:
        raise ValueError("v2 best checkpoint SHA mismatch")
    return {"archive_sha256": V2_ARCHIVE_SHA, "checkpoint_sha256": digest.hexdigest(),
            "checkpoint_bytes": destination.stat().st_size}


def authorize_record(record, output_id, device="mps"):
    legacy.authorise(record, SCOPE, bindings(output_id, device), opt_in=True)
    if (record.get("local_training_authorized") is not True
            or record.get("cloud_upload_authorized") is not False
            or record.get("test_access_authorized") is not False):
        raise ValueError("Local-only training scope and explicit Test/cloud exclusions are required")


def run_local(root, v2_archive, output_parent, record, *, opt_in=False, device="mps"):
    """Run one seed-43 stage only after hash, manifest, and owner-scope checks."""
    if not opt_in:
        raise ValueError("Explicit owner opt-in required before any real data access")
    config = configuration(device)
    output_parent = Path(output_parent)
    output_id = output_parent.name
    authorize_record(record, output_id, device)
    if (output_parent.exists() or output_parent.is_symlink()
            or output_parent.parent.resolve() != (PROJECT_ROOT / "data/vision").resolve()
            or not (PROJECT_ROOT / "data/vision").resolve().is_relative_to(PROJECT_ROOT.resolve())):
        raise ValueError("Fresh ignored local data/vision output path required")
    if sha256_file(DATA_ARCHIVE) != DATA_ARCHIVE_SHA:
        raise ValueError("Pinned development ZIP SHA mismatch")
    if sha256_file(v2_archive) != V2_ARCHIVE_SHA:
        raise ValueError("Pinned v2 result ZIP SHA mismatch")
    verified = bundle.verify(root, MANIFEST_SHA)
    manifest_path = legacy.safe_file(root, "bundle_manifest.json")
    manifest = bundle.load_json(manifest_path)
    records = manifest["records"]
    selection = validate_records(records)
    if (manifest["held_count"] != 181 or manifest["np015_excluded"] != list(legacy.NP015_IDS)
            or manifest["qualified_labels_approved"] is not False
            or manifest["participant_independence_verified"] is not False
            or manifest["final_research_approved"] is not False):
        raise ValueError("Holds, uncertainty, or approval status changed")

    output_parent.mkdir(mode=0o700, parents=False, exist_ok=False)
    attempt = output_parent / "attempt.json"
    attempt.write_text(json.dumps({"status": "consumed_before_training", "authorization": record},
                                  indent=2) + "\n")
    checkpoint_path = output_parent / "initial_v2_best.pt"
    checkpoint = extract_v2_best(v2_archive, checkpoint_path)
    initial = stage.read_initial_checkpoint(checkpoint_path, INITIAL_SHA)

    torch = models._torch()
    torch.set_num_threads(2)
    torch.manual_seed(43)
    network = pilot.make_model(pretrained=False)
    network["model"].load_state_dict(initial["model"], strict=True)
    del initial
    by_split = {split: [row for row in records if row["original_split"] == split]
                for split in legacy.EXPECTED_COUNTS}
    datasets = {split: pilot.Dataset(root, rows, split) for split, rows in by_split.items()}
    context = {
        "version": VERSION,
        "notice": legacy.NOTICE,
        "protocol": protocol(device),
        "bindings": bindings(output_id, device),
        "source_hashes": code_hashes(),
        "dataset_verification": verified,
        "selection_summary": selection,
        "starting_checkpoint": checkpoint,
        "runtime": {"python": platform.python_version(), "torch": str(torch.__version__),
                    "torchvision": __import__("torchvision").__version__,
                    "numpy": __import__("numpy").__version__, "device": device,
                    "mps_available": bool(torch.backends.mps.is_available()),
                    "cpu_threads": torch.get_num_threads()},
        "qualified_labels_approved": False,
        "participant_independence_verified": False,
        "final_research_approved": False,
        "test_used": False,
    }
    (output_parent / "authorization.json").write_text(json.dumps(record, indent=2) + "\n")
    (output_parent / "protocol.json").write_text(json.dumps(context, indent=2) + "\n")

    start = time.perf_counter()
    result = stage.fit(network["model"], datasets["Training"], datasets["Validation"],
                       config, output_parent / "training", context)
    if device == "mps":
        torch.mps.synchronize()
    elapsed = time.perf_counter() - start
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() == "Darwin":
        rss_mib = rss / (1024 * 1024)
    else:
        rss_mib = rss / 1024
    result.update({
        "experiment_version": VERSION,
        "protocol": protocol(device),
        "runtime": context["runtime"],
        "training_seconds": elapsed,
        "process_peak_rss_mib": rss_mib,
        "mps_current_allocated_bytes": int(torch.mps.current_allocated_memory()) if device == "mps" else None,
        "validation_record_count": len(datasets["Validation"]),
        "validation_predictions_path": "training/validation_predictions_best.json",
        "checkpoint_path": "training/best.pt",
        "test_used": False,
        "clinical_validation": False,
        "healthy_mgi0_supported": False,
        "notice": legacy.NOTICE,
    })
    if code_hashes() != context["source_hashes"]:
        raise ValueError("Source code changed during the run")
    (output_parent / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    attempt.write_text(json.dumps({"status": "completed", "results_sha256": sha256_file(output_parent / "results.json"),
                                  "authorization": record}, indent=2) + "\n")
    return result
