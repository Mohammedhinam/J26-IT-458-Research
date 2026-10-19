"""Local package builder only. No uploads, optimizer steps or model inference."""
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.vision import resnet50_fold0_pilot_v1 as pilot
from src.vision import b1_jpeg_source_v1 as source
from src.vision.roi_dataset_v1 import DEFAULT_SOURCE

BUNDLE = REPO / "data/vision/pp1_b1_dev_v1_20261015T085436527238Z"
FOLDS = REPO / "data/vision/roi_tooth_v1_20261017/dataset_v4"
OUTPUT = REPO / "data/vision/resnet50_fold0_pilot_v1_20261018_r2"
NOTEBOOK = REPO / "notebooks/resnet50_fold0_controlled_pilot_v1_r2.ipynb"


def display_preview(row):
    """B1 colour-converted full-frame display only; preserve original aspect ratio.

    The float32 224 input is independently checked against its existing cache.
    Display samples are clipped to RGB8, like existing CAM previews, never used to train.
    """
    path = DEFAULT_SOURCE.parent / row["original_image_path"]
    with source.decoded(path, row["source_sha256"], row["source_dimensions"], row["profile_sha256"]) as image:
        converter = source.Converter(image.info["icc_profile"])
        actual = source.model_view(image, converter)
        cached = np.load(BUNDLE / row["model_path"], allow_pickle=False)
        if not np.array_equal(actual, cached):
            raise ValueError("B1 source-to-cache parity failed")
        width, height = image.size
        scale = min(1, 1200 / max(width, height))
        pw, ph = round(width * scale), round(height * scale)
        xs = np.minimum(((np.arange(pw) + .5) * width / pw).astype(int), width - 1)
        ys = np.minimum(((np.arange(ph) + .5) * height / ph).astype(int), height - 1)
        preview = np.empty((ph, pw, 3), dtype=np.uint8)
        for y, original_y in enumerate(ys):
            with image.crop((0, int(original_y), width, int(original_y) + 1)) as strip:
                values = converter.convert(np.asarray(strip)[:, xs, :])[0][0]
            preview[y] = np.rint(np.clip(values, 0, 1) * 255).astype(np.uint8)
        return preview


def cell(kind, text):
    result = {"cell_type": kind, "id": "cell-" + pilot.digest([kind, text])[:12],
              "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def build_notebook(archive_sha, manifest_sha):
    cells = [cell("markdown", """# Controlled ResNet50 fold-0 pilot — PREPARATION ONLY
Do not upload or train until the owner separately approves cloud processing and this run.
544 fit / 136 score, all original Training. No Validation, Test, held records or personal photos.
Provisional grades 1–4; no whole-image grade-0 support. Content groups are isolated;
participant independence and clinical labels are unverified. This is not gingiva-supervised training.

After approval: choose a CUDA GPU (T4 is sufficient), set permission flags below, install
dependencies, manually upload the named ZIP using the Files sidebar, then verify/extract.
No Drive mount or automatic image uploader is used. Keep the notebook private; omit outputs
when saving/sharing because later CAM views contain dental images.
"""), cell("code", f'''# Keep both False during preparation. Run All cannot start training by default.
import os, sys
from pathlib import Path
sys.dont_write_bytecode = True
os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
CLOUD_UPLOAD_APPROVED = False
RUN_TRAINING = False
OWNER_APPROVAL = ""
ARCHIVE = Path("/content/resnet50_fold0_pilot_v1.zip")
ROOT = Path("/content/resnet50_fold0_package_v1")
RUN_ROOT = Path("/content/resnet50_fold0_run_v1")
ARCHIVE_SHA = "{archive_sha}"
MANIFEST_SHA = "{manifest_sha}"
'''), cell("code", '''# Install only after separate approval, before importing Torch/NumPy.
if not CLOUD_UPLOAD_APPROVED:
    raise PermissionError("STOP: no external upload or GPU run is authorized yet.")
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install",
    "torch==2.11.0", "torchvision==0.26.0", "numpy==2.5.3",
    "Pillow==11.3.0", "scikit-learn==1.9.1"])
# Restart the session if Colab reports that imported packages must be restarted.
'''), cell("markdown", """## Verify the manually uploaded ZIP before importing its code
Expected filename: `resnet50_fold0_pilot_v1.zip`. The ZIP includes the pinned public
ImageNet initialization and local dataset derivatives; no old dental model checkpoint.
Extraction refuses an existing destination. To resume a training session, reuse the already
verified package and matching run directory; do not re-extract into it.
"""), cell("code", '''if not CLOUD_UPLOAD_APPROVED:
    raise PermissionError("Cloud processing has not been approved")
import hashlib, json, stat, zipfile
def file_sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            result.update(block)
    return result.hexdigest()
assert file_sha(ARCHIVE) == ARCHIVE_SHA, "Wrong or damaged ZIP"
if not ROOT.exists():
    with zipfile.ZipFile(ARCHIVE) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        assert len(names) == len(set(names)) < 750
        assert sum(entry.file_size for entry in entries) < 1024**3
        for entry in entries:
            name = Path(entry.filename)
            assert not name.is_absolute() and ".." not in name.parts
            assert not entry.is_dir() and not stat.S_ISLNK(entry.external_attr >> 16)
            assert entry.file_size < 110*1024**2
        assert hashlib.sha256(archive.read("manifest.json")).hexdigest() == MANIFEST_SHA
        manifest = json.loads(archive.read("manifest.json"))
        assert set(names) == set(manifest["files"]) | {"manifest.json"}
        ROOT.mkdir()
        for name in names:
            member = ROOT / name
            member.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, member.open("xb") as destination:
                import shutil
                shutil.copyfileobj(source, destination)
assert file_sha(ROOT / "manifest.json") == MANIFEST_SHA
# Check vendored source hashes before the first import, even on a resumed session.
manifest = json.loads((ROOT / "manifest.json").read_text())
for name, info in manifest["files"].items():
    path = ROOT / name
    assert not path.is_symlink() and file_sha(path) == info["sha256"], name
sys.path.insert(0, str(ROOT))
from src.vision import resnet50_fold0_pilot_v1 as pilot
PREFLIGHT = pilot.preflight(ROOT, MANIFEST_SHA)
print(json.dumps(PREFLIGHT, indent=2))
'''), cell("code", '''# GPU/runtime check: no fitting occurs in this cell.
import torch, torchvision, numpy, sklearn, PIL
print({"torch": torch.__version__, "torchvision": torchvision.__version__,
       "numpy": numpy.__version__, "sklearn": sklearn.__version__, "Pillow": PIL.__version__})
assert torch.cuda.is_available(), "CUDA GPU required; stop instead of CPU training"
print(torch.cuda.get_device_name(), "CUDA", torch.version.cuda)
'''), cell("markdown", """## Explicit future execution gate
After a separate owner approval, set RUN_TRAINING=True and OWNER_APPROVAL to:
`I approve this exact fold-0 Colab GPU pilot and cloud processing.`

Budget: shared warm-up 1 epoch, arm A 5 epochs, arm B 5 epochs; no early stopping,
score-driven selection or automatic extra epochs. Fresh Adam per stage; same arm batch orders.
Checkpoints are saved every epoch. Identical-runtime interrupted fits can resume with the
same RUN_ROOT. An incomplete checkpoint is preserved and fails closed. A completed run refuses
execution. Scoring/CAM export interruptions require inspection; they are not silently overwritten.
"""), cell("code", '''if not CLOUD_UPLOAD_APPROVED or not RUN_TRAINING:
    raise PermissionError("Preparation complete. STOP and obtain explicit training approval.")
RESULT = pilot.run(ROOT, RUN_ROOT, execute=RUN_TRAINING,
                   approval=OWNER_APPROVAL, manifest_sha=MANIFEST_SHA)
print(json.dumps(RESULT, indent=2))
'''), cell("markdown", """## Review and return results — only after a completed approved run
Review `metrics.json`, `predictions.json`, `warmup/`, `A/`, `B/` and `cam/`.
CAM contains predicted-class and common-A-target original/heatmap/overlay views for the same
eight predeclared photos. Attention is not validated disease localization or gum boundaries.
Doctor review should be blinded to model identity; record relevant/irrelevant/uncertain and
notes separately. No attention-mask score is claimed without qualified clinical annotation.

The optional return ZIP contains experimental CAM images as well as weights/results.
It stays on the Colab VM until you explicitly download it. It never installs into the PP1 demo.
Colab local storage is ephemeral: manually download checkpoints/results before ending the session.
"""), cell("code", '''# Explicit optional packaging; never upload or install into the Mac demo automatically.
assert (RUN_ROOT / "complete.json").is_file(), "No completed experiment yet"
import shutil
RETURN_BASE = Path("/content/resnet50_fold0_return_v1")
assert not RETURN_BASE.with_suffix(".zip").exists(), "Preserve existing return ZIP"
files = {path.relative_to(RUN_ROOT).as_posix(): file_sha(path)
         for path in RUN_ROOT.rglob("*") if path.is_file()}
integrity = RUN_ROOT / "return_integrity.json"
assert not integrity.exists(), "Preserve existing integrity receipt"
integrity.write_text(json.dumps(files, indent=2))
shutil.make_archive(str(RETURN_BASE), "zip", RUN_ROOT)
print("Download manually:", RETURN_BASE.with_suffix(".zip"))
print("SHA-256:", file_sha(RETURN_BASE.with_suffix(".zip")))
''')]
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"}, "colab": {"provenance": []}}, "nbformat": 4, "nbformat_minor": 5}


def main():
    if OUTPUT.exists() or NOTEBOOK.exists():
        raise FileExistsError("Versioned preparation already exists; preserve it")
    OUTPUT.mkdir(parents=True)
    protected = json.loads((REPO / "data/vision/doctor_demo_ui_v2_20261018/preservation_before.json").read_text())
    # Include every current demo source plus all model files, not only historical receipt paths.
    paths = set(protected)
    for folder in ("models", "src/tabular/ui"):
        paths.update(p.relative_to(REPO).as_posix() for p in (REPO / folder).rglob("*") if p.is_file())
    paths.update(["src/vision/local_photo_upload_demo.py", "src/vision/roi_inference_v1.py",
                  "src/vision/roi_ordinal_v2_inference.py", "src/vision/roi_ordinal_v2_live.py"])
    before = {name: pilot.sha256_file(REPO / name) for name in sorted(paths)}
    pilot.write_json(OUTPUT / "preservation_before.json", before)
    if pilot.sha256_file(BUNDLE / "bundle_manifest.json") != pilot.SOURCE_MANIFEST_SHA:
        raise ValueError("Original B1 manifest changed")
    original = json.loads((BUNDLE / "bundle_manifest.json").read_text())
    snapshot = json.loads((FOLDS / "folds_protocol_snapshot.json").read_text())
    frozen = json.loads((FOLDS / "folds.json").read_text())["folds"][0]
    rows = sorted([r for r in original["records"] if r["original_split"] == "Training"],
                  key=lambda r: r["source_record_id"])
    if [r["source_record_id"] for r in rows] != snapshot["ids"]:
        raise ValueError("B1/fold membership mismatch")
    protected_groups = set(original["protected_groups"]) | set(original["uncertain_groups"])
    if any(r["content_group_id"] in protected_groups or r["source_record_id"] in original["np015_excluded"] for r in rows):
        raise ValueError("Protected content entered preparation")
    score = set(frozen["score_ids"])
    if set(frozen["fit_ids"]) & score or set(frozen["fit_ids"]) | score != set(snapshot["ids"]):
        raise ValueError("Frozen fold membership is inconsistent")
    # Selection happens before any inference: first two scoring IDs for each provisional grade.
    cam_ids = sorted([r["source_record_id"] for grade in pilot.GRADES
                      for r in [r for r in rows if r["source_record_id"] in score
                                and r["provisional_mgi_grade"] == grade][:2]])
    package = OUTPUT / "package"
    (package / "arrays").mkdir(parents=True)
    (package / "previews").mkdir()
    (package / "weights").mkdir()
    (package / "src/vision").mkdir(parents=True)
    for name in ("src/__init__.py", "src/vision/__init__.py"):
        (package / name).write_text("")
    for filename in ("resnet50_fold0_pilot_v1.py", "model_pipeline.py", "colour_b1_prototype.py"):
        shutil.copyfile(REPO / "src/vision" / filename, package / "src/vision" / filename)
    records = []
    for row in rows:
        record_id = row["source_record_id"]
        name = record_id.split("/")[1]
        source_array = BUNDLE / row["model_path"]
        if pilot.sha256_file(source_array) != row["model_sha256"]:
            raise ValueError("Source cached B1 array changed")
        array = "arrays/" + name + ".npy"
        shutil.copyfile(source_array, package / array)
        record = {"id": record_id, "role": "score" if record_id in score else "fit",
                  "grade": row["provisional_mgi_grade"], "group": row["content_group_id"],
                  "source_sha256": row["source_sha256"], "array": array,
                  "array_sha256": row["model_sha256"], "valid_box": row["valid_box"],
                  "source_dimensions": row["source_dimensions"]}
        if record_id in cam_ids:
            record["preview"] = "previews/" + name + ".png"
            Image.fromarray(display_preview(row)).save(package / record["preview"])
            print("Full-frame preview / exact B1 cache parity:", record_id, flush=True)
        records.append(record)
    weights = Path.home() / ".cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth"
    if pilot.sha256_file(weights) != pilot.WEIGHTS_SHA:
        raise ValueError("Official cached ImageNet initialization unavailable")
    shutil.copyfile(weights, package / "weights/resnet50-11ad3fa6.pth")
    pilot.write_json(package / "WEIGHTS_PROVENANCE.json", {
        "identity": "torchvision ResNet50_Weights.IMAGENET1K_V2",
        "source_url": "https://download.pytorch.org/models/resnet50-11ad3fa6.pth",
        "sha256": pilot.WEIGHTS_SHA, "dental_training_seen": False,
        "note": "Existing official cached weights; never the dental v3 checkpoint."
    })
    attribution = original["dataset_attribution"]
    attribution["transformation_notice"] = (
        "680 unchanged B1 extended-sRGB float32 224 letterboxed arrays; original metadata absent. "
        "Eight full-frame B1 colour-converted clipped RGB8 display previews, max side1200; "
        "original sources unchanged. Existing provisional caption-maximum grades and fold0 reused. "
        "No clinical validation, licensor endorsement, cloud-upload or execution approval.")
    pilot.write_json(package / "ATTRIBUTION.json", attribution)
    (package / "requirements.txt").write_text(
        "torch==2.11.0\ntorchvision==0.26.0\nnumpy==2.5.3\nPillow==11.3.0\nscikit-learn==1.9.1\n")
    (package / "README.txt").write_text(
        "LOCAL PREPARATION ONLY. Do not upload/run until separately authorized.\n"
        "CC BY 4.0 source attribution: see ATTRIBUTION.json. No guarantee of privacy clearance.\n"
        "Only original Training680: 544fit/136score; Validation/Test/held records excluded.\n"
        "No whole-image MGI0; provisional labels and unknown participant independence.\n"
        "Use the separately supplied Colab notebook and SHA receipt. No previous dental checkpoint.\n"
        "Never use the 53 repeatedly selected Validation examples as new independent validation.\n")
    manifest = {"version": pilot.VERSION, "config": pilot.CONFIG, "records": records,
                "source_manifest_sha256": pilot.SOURCE_MANIFEST_SHA, "fold_assignment_sha256": pilot.FOLDS_SHA,
                "fold_snapshot": {"ids": snapshot["ids"], "folds": snapshot["folds"]},
                "qualified_labels_approved": False, "participant_independence_verified": False,
                "cloud_upload_authorized": False, "gpu_training_authorized": False,
                "cam_ids": cam_ids, "cam_selection": "first two score IDs per provisional grade; before inference",
                "source_to_B1_exact_parity_cases": cam_ids, "files": {}}
    manifest["membership_sha256"] = pilot.digest({"ids": [r["id"] for r in records],
        "roles": [r["role"] for r in records], "grades": [r["grade"] for r in records],
        "groups": [r["group"] for r in records]})
    manifest["files"] = {p.relative_to(package).as_posix(): {"sha256": pilot.sha256_file(p), "bytes": p.stat().st_size}
                         for p in sorted(package.rglob("*")) if p.is_file()}
    pilot.write_json(package / "manifest.json", manifest)
    receipt = pilot.preflight(package)
    pilot.write_json(OUTPUT / "preflight.json", receipt)
    archive = OUTPUT / "resnet50_fold0_pilot_v1.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as target:
        for name in sorted(set(manifest["files"]) | {"manifest.json"}):
            target.write(package / name, name)
    with zipfile.ZipFile(archive) as target:
        if target.testzip() is not None:
            raise ValueError("Archive CRC failure")
    archive_sha = pilot.sha256_file(archive)
    pilot.write_json(NOTEBOOK, build_notebook(archive_sha, receipt["manifest_sha256"]))
    after = {name: pilot.sha256_file(REPO / name) for name in before}
    if after != before:
        raise ValueError("An existing protected artifact changed")
    pilot.write_json(OUTPUT / "preservation_after.json", after)
    pilot.write_json(OUTPUT / "preparation.json", {"status": "prepared_not_executed", "notebook": str(NOTEBOOK),
        "archive": str(archive), "archive_sha256": archive_sha, "archive_bytes": archive.stat().st_size,
        "manifest_sha256": receipt["manifest_sha256"], "protected_files_unchanged": len(before),
        "cloud_upload_authorized": False, "gpu_training_authorized": False, "preflight": receipt})
    print(json.dumps(json.loads((OUTPUT / "preparation.json").read_text()), indent=2))


if __name__ == "__main__":
    main()
