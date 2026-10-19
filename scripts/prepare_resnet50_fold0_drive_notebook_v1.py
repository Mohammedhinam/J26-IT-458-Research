"""Create a separate Drive-input notebook; leave r2, its ZIP and training code intact."""
import ast
import copy
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ORIGINAL = REPO / "notebooks/resnet50_fold0_controlled_pilot_v1_r2.ipynb"
OUTPUT = REPO / "notebooks/resnet50_fold0_controlled_pilot_v1_r3_drive.ipynb"


def cell(kind, text):
    result = {"cell_type": kind, "id": hashlib.sha256(text.encode()).hexdigest()[:12],
              "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        result.update(outputs=[], execution_count=None)
    return result


def prepare():
    notebook = json.loads(ORIGINAL.read_text())
    old = copy.deepcopy(notebook["cells"])
    notebook["cells"][0] = cell("markdown", """# Controlled ResNet50 fold-0 pilot — Drive input, preparation only
Same r2 dataset ZIP, hashes, independent ImageNet initialization and fixed 1+5+5 budget.
544 fit /136 score from original Training only; labels provisional, participant independence
unverified. No Test, held records, personal photos or previous dental checkpoints.

After explicit cloud permission, manually place `resnet50_fold0_pilot_v1.zip` in
`My Drive/RP-J26-IT-458/roi_tooth_v1/` (the same folder as the older ROI files).
Use the355MB r2 ZIP with SHA starting `60f70f27`, not a previous failed preparation.
The mount cell asks you to authorize Drive access. The ZIP is hash-checked then copied to
the runtime; extraction and training remain on local VM storage. No automatic image uploader,
Drive result writer, extra training, changed inputs or demo integration is introduced.

Saved flags remain false: preparation does not grant training permission. Keep notebook and
outputs private. Same experimental/clinical limitations as r2. A Drive input does not repair
an already loaded mixed NumPy installation; restart the session when the setup cell requests it.
""")
    config = "".join(old[1]["source"])
    config = config.replace('ARCHIVE = Path("/content/resnet50_fold0_pilot_v1.zip")',
        'ARCHIVE = Path("/content/resnet50_fold0_drive_r3_input.zip")\n'
        'DRIVE_FOLDER = Path("/content/drive/MyDrive/RP-J26-IT-458/roi_tooth_v1")')
    config = config.replace('RUN_ROOT = Path("/content/resnet50_fold0_run_v1")',
                            'RUN_ROOT = Path("/content/resnet50_fold0_drive_r3_run_v1")')
    notebook["cells"][1] = cell("code", config)
    notebook["cells"][2] = cell("code", """# Install only mismatched packages; then STOP for a session restart.
if not CLOUD_UPLOAD_APPROVED:
    raise PermissionError("Cloud processing has not been approved. Training stays disabled.")
import importlib.metadata, subprocess
required = {"torch": "2.11.0", "torchvision": "0.26.0", "numpy": "2.5.3",
            "Pillow": "11.3.0", "scikit-learn": "1.9.1"}
missing = []
for name, version in required.items():
    try:
        current = importlib.metadata.version(name).split("+")[0]
    except importlib.metadata.PackageNotFoundError:
        current = None
    if current != version:
        missing.append(name + "==" + version)
if missing:
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    raise RuntimeError("Dependencies installed. Runtime > Restart session; then rerun from the configuration cell.")
loaded_numpy = sys.modules.get("numpy")
if loaded_numpy is not None and getattr(loaded_numpy, "__version__", None) != required["numpy"]:
    raise RuntimeError("Old NumPy is still loaded. Runtime > Restart session; rerun configuration/setup.")
print("Pinned package versions present. No package changes or training in this cell.")
""")
    drive_markdown = cell("markdown", """## Mount Drive and copy the already uploaded ZIP
Put the ZIP in the folder above once. Run this cell only after cloud processing permission;
approve the Google authorization dialog yourself. No Drive files are deleted or replaced.
If using a shared-folder shortcut, set DRIVE_FOLDER to its actual My Drive path.
""")
    drive_code = cell("code", """if not CLOUD_UPLOAD_APPROVED:
    raise PermissionError("Cloud processing has not been approved")
from google.colab import drive
import hashlib, shutil
drive.mount("/content/drive")
def input_sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            result.update(block)
    return result.hexdigest()
drive_zip = DRIVE_FOLDER / "resnet50_fold0_pilot_v1.zip"
if not drive_zip.is_file():
    raise FileNotFoundError("Manually upload the r2 ZIP to: " + str(DRIVE_FOLDER))
if input_sha(drive_zip) != ARCHIVE_SHA:
    raise ValueError("Drive ZIP hash mismatch: wait for upload completion and verify the r2 file. Do not change the hash.")
if ARCHIVE.exists():
    if input_sha(ARCHIVE) != ARCHIVE_SHA:
        raise ValueError("Existing local copy differs; preserve it and use a fresh ARCHIVE path.")
else:
    with drive_zip.open("rb") as source, ARCHIVE.open("xb") as target:
        shutil.copyfileobj(source, target, 1024*1024)
    if input_sha(ARCHIVE) != ARCHIVE_SHA:
        raise ValueError("Local copy integrity failed; preserve it and inspect before proceeding")
print("Verified local ZIP:", ARCHIVE)
""")
    notebook["cells"][3] = cell("markdown", """## Verify/extract the local copy and run data preflight
The following integrity, extraction and preflight code is unchanged from r2.
Drive remains the input archive source only. The training runner remains unchanged.
""")
    notebook["cells"][3:3] = [drive_markdown, drive_code]
    for item in notebook["cells"]:
        if item["cell_type"] == "code":
            ast.parse("".join(item["source"]))
    # Verify that transport/setup edits did not alter scientific execution or scoring cells.
    for index in (4,5,7,9):
        assert notebook["cells"][index+2] == old[index]
    with OUTPUT.open("x") as stream:
        json.dump(notebook, stream, indent=2)
        stream.write("\n")
    return OUTPUT


if __name__ == "__main__":
    print(prepare())
