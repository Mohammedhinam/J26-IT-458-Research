# PROJECT_STATUS.md — Technical Handover

**Project:** RP Project J26-IT-458 — *AI-Integrated Dental Health Assessment and Preventive Analytics Framework*  
**Individual component:** *AI-Based Dental Caries Detection and Severity Assessment* (IT23135598)  
**Owner's Git branch:** `hinam`  
**Status as of:** 2026-10-17 (Asia/Colombo); sections 1–15 retain historical 2026-10-16 detail unless superseded by Section 16  
**Basis of this handover:** Outcomes, commands, file listings, and outputs explicitly reported in this conversation. This document is a handover, **not a fresh audit of the live repository, Drive, Colab session, or Teams Planner**. Where a path or implementation is known only from the user's report, that is indicated. Do not confuse technical execution with independent clinical validation.

---

## 0. TL;DR — current stopping point (updated 2026-10-17)

**Working demonstration (user-tested):** React/Vite (`http://localhost:5173`) and FastAPI (`http://127.0.0.1:8000`) execute the unchanged two-stage pipeline: YOLOv8n detections, 30%-padded crops, MobileNetV2 and EfficientNet-B0 severity dataset-label predictions. Interactive R1/R2 selection highlights matching boxes and prediction cards. Valid JPG upload returned HTTP 200; invalid JPG contents returned HTTP 400 and a frontend error without a crash. The user successfully displayed both Grad-CAM overlay images for a selected detection region via a separate `POST /api/caries/gradcam` endpoint, including a region-switching test. This is a technical research prototype, **not clinically validated**.

**Verified Git state:** October 17 commit **`8ecabf9`** (`Add Grad-CAM integration, interactive region selection, and image validation`) includes eight source/test files. User's terminal shows `8ecabf9 (HEAD -> hinam, origin/hinam)` and `## hinam...origin/hinam`, so this commit is pushed and tracked on `origin/hinam`. No merge into `main` was reported. Temporary local heatmap PNGs and one WhatsApp JPEG remain untracked intentionally.

**Next exact unfinished implementation step:** **Step 76.25 — bounding-box consistency test**. `backend/test_region_consistency.py` was created and committed, but **no execution output was provided**. Run it and inspect R1–Rn matches before relying on repeat YOLO inference for Grad-CAM region identity. Follow-up robustness work includes eliminating re-detection ambiguity, regression tests, resource limits and PP1 demonstration evidence.

**Important distinction:** Grad-CAM overlays are visually produced and served, but no dental expert evaluation, clinical validation, or ground-truth-confirmed localization of explanation patterns has been completed. Prior sections 1–15 are an archived 2026-10-16 history; **Section 16 contains the authoritative October 17 update**.

---

## 1. Repository, branch, development locations

| Property | Exact value / status |
|---|---|
| GitHub repo | `https://github.com/Mohammedhinam/J26-IT-458-Research` |
| Git remote | `https://github.com/Mohammedhinam/J26-IT-458-Research.git` |
| Individual branch | `hinam` |
| Other member branches (previously reported) | `vinuthan`, `faslur`, `vishnavi` |
| Local Windows repo root | `C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research` |
| Component root | `C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research\Dental-Caries-Detection` |
| Backend working directory | `...\Dental-Caries-Detection\backend` |
| Frontend working directory | `...\Dental-Caries-Detection\frontend` |
| **Active Python virtualenv** | `C:\caries-venv` (outside OneDrive to avoid Windows long-path issues) |
| Superseded virtualenv | `backend\.venv` (installation into it failed; it was **not** confirmed deleted) |
| Frontend dev server | Vite `http://localhost:5173/` |
| Backend dev server | `http://127.0.0.1:8000/` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| Working branch linked to remote | `hinam` tracking `origin/hinam` after successful push |

### Folder structure — **known files**, not an exhaustive listing

```text
J26-IT-458-Research/
├── .gitignore                         # modified and committed
└── Dental-Caries-Detection/
    ├── backend/
    │   ├── .venv/                     # earlier env; ignored, not the active env
    │   ├── app/
    │   │   ├── main.py               # FastAPI, CORS, health + caries routers
    │   │   ├── routes/
    │   │   │   ├── health.py          # preexisting health route (inferred from import)
    │   │   │   └── caries.py          # POST /api/caries/predict
    │   │   ├── schemas/              # exists; contents not established
    │   │   ├── services/
    │   │   │   ├── __init__.py
    │   │   │   ├── .gitkeep
    │   │   │   └── caries_prediction.py
    │   │   └── utils/                # exists; contents not established
    │   ├── test_prediction.py         # local integration test script; committed
    │   └── test_image.jpg            # local temporary test image; ignored
    ├── frontend/
    │   ├── public/
    │   ├── src/
    │   │   ├── assets/
    │   │   ├── components/
    │   │   ├── pages/
    │   │   │   └── Home.jsx
    │   │   ├── services/
    │   │   │   └── api.js
    │   │   ├── App.jsx
    │   │   ├── main.jsx
    │   │   └── index.css
    │   ├── .env.example
    │   ├── package.json
    │   └── vite.config.js
    ├── training/                       # prior scaffold, exact contents unknown
    ├── models/
    │   ├── best.pt                     # YOLOv8, ignored by *.pt
    │   ├── mobilenetv2.keras           # ignored by *.keras
    │   └── efficientnetb0.keras        # ignored by *.keras
    ├── notebooks/
    │   └── Dental_Caries_YOLOv8_Training.ipynb  # earlier committed notebook
    ├── docs/
    │   └── PROJECT_PROGRESS.md        # updated and committed
    └── tests/                          # earlier scaffold; content not established
```

**Do not assume** that `Dental_Caries_Severity_Classification.ipynb` was committed: it was created/used in Colab, but this conversation does not establish a local repository copy or a separate notebook commit. Other initial directories and files may exist beyond this known subset. The trained weights reside **locally and in Drive**, **not in GitHub**.

---

## 2. Design, data provenance, and research decisions

### Architecture

```text
Intraoral dental photo (JPG/PNG)
          |
          v
       YOLOv8n                  [local model: models/best.pt]
          |
     Detection boxes, scores
          |
          v
 Expand each detection by 30% per side (clamped to image bounds)
          |
      Resize RGB to 224×224; float32 values 0..255
          |
     +----+-----------------------------+
     |                                  |
     v                                  v
 MobileNetV2                       EfficientNet-B0
 (saved .keras)                    (saved .keras)
     |                                  |
     +-------------+--------------------+
                   |
          Compare argmax classes
                   |
          agreement -> preliminary class
          disagreement -> "Uncertain - Review Required"
                   |
             FastAPI JSON
                   |
          React results + boxes
```

- YOLO detection classes originate from `data.yaml`: **`0: D`, `1: d`**. **No clinically justified meaning for uppercase/lowercase labels has been established**; do not call them severity labels.
- Classifier class indices (alphabetical TensorFlow directory order) **must remain unchanged**:
  - `0: AdvanceEnamel_Caries`
  - `1: EarlyStageEnamel_Caries`
  - `2: NoEnamel_Caries`
- Classifier outputs are **dataset-label predictions**, not exact ICDAS codes or diagnoses.
- Pretrained architectures: YOLOv8n, Keras MobileNetV2 ImageNet backbone, Keras EfficientNetB0 ImageNet backbone. Both classifiers used a new softmax three-class head; feature extractors initially frozen.
- MobileNetV2 input: saved architecture includes horizontal flip, rotation 0.05, **`Rescaling(1./127.5, offset=-1)`** before backbone.
- EfficientNet-B0 input: **do not add MobileNetV2 rescaling**; EfficientNetB0 Keras backbone includes its own input scaling. Models accept RGB float32 input values 0–255.
- YOLO crop policy for prototype: **30% padding on each side** (`pad_x=0.30*(x2-x1)`, `pad_y=0.30*(y2-y1)`), clamped to image boundaries. No evidence that this pad amount is clinically optimal; domain shift remains.
- Ensemble policy: if both classifiers predict the same class, return that class with status `Agreement`; otherwise return `Uncertain` with status `Uncertain - Review Required`. Confidence values are **model scores, not calibrated clinical probabilities**, and agreement is **not clinical correctness**. No-detections response: `No suspected regions detected`, **not** `No Caries`.

### Original data sources

- **YOLO dataset:** Zenodo Benchmarking Dataset, `https://zenodo.org/records/14827784` (selected annotated intraoral image/YOLO-label subset).
- **Severity dataset:** Caries-Spectra v2, Mendeley, `https://data.mendeley.com/datasets/9jnf2jvghy/2`.
- Two datasets serve **different purposes**. Do not combine all images into one undifferentiated training set.

---

## 3. YOLOv8 dataset — paths, cleaning, training, evaluation

### Files and paths

| Resource | Exact location |
|---|---|
| Uploaded initial YOLO dataset ZIP | `/content/drive/MyDrive/YOLO_Caries_Training.zip` |
| Working extracted dataset | `/content/YOLO_Caries_Training` |
| Training/validation/test images | `/content/YOLO_Caries_Training/images/{train,valid,test}` |
| Bounding-box labels | `/content/YOLO_Caries_Training/labels/{train,valid,test}` |
| YAML | `/content/YOLO_Caries_Training/data.yaml` |
| Original label backup in earlier runtime | `/content/YOLO_Original_Labels_Backup` (**temporary**) |
| Excluded 16 pairs in earlier runtime | `/content/YOLO_Excluded_Images` (**temporary**) |
| **Durable cleaned dataset backup** | `/content/drive/MyDrive/YOLO_Caries_Cleaned.zip` |
| YOLO training directory | `/content/drive/MyDrive/Dental_Caries_Results/YOLOv8_First_Training/` |
| Trained YOLO best weight | `/content/drive/MyDrive/Dental_Caries_Results/YOLOv8_First_Training/weights/best.pt` |
| YOLO baseline summary | `/content/drive/MyDrive/Dental_Caries_Results/YOLOv8_Baseline_Summary.json` |
| Local exported best model | `Dental-Caries-Detection/models/best.pt` (~6.20 MB) |
| YOLO Colab notebook | `Dental_Caries_YOLOv8_Training.ipynb`; earlier added in repo `notebooks/` |

**`data.yaml` contents:**

```yaml
path: /content/YOLO_Caries_Training
train: images/train
val: images/valid
test: images/test
nc: 2
names:
  0: D
  1: d
```

Initially extracted YAML had an incorrect `.yaml.txt` filename and Windows paths; both were corrected. Image and label filenames were checked to match.

**Data cleaning verified:**

| Split | Before | After excluding bad label/image pairs |
|---|---:|---:|
| Train | 1,781 | 1,769 |
| Validation | 214 | 212 |
| Test | 232 | 230 |
| **Total** | **2,227** | **2,211** |

- Found **6,686 valid YOLO bounding boxes** plus **42 invalid boxes across 16 label files** (12 train, 2 valid, 2 test); 41 fully outside the image and 1 partly outside. All 16 affected label files contained only invalid boxes, so 16 image-label pairs were excluded rather than forcibly clamped.
- Rechecked cleaned dataset: **6,686 valid boxes, 0 invalid boxes**. Original ZIP kept; cleaned ZIP backed up to Drive.

**Actual initial training configuration:**

```python
from ultralytics import YOLO
import torch

model = YOLO("yolov8n.pt")
results = model.train(
    data="/content/YOLO_Caries_Training/data.yaml",
    epochs=20,
    imgsz=640,
    batch=8,
    device=0 if torch.cuda.is_available() else "cpu",
    project="/content/drive/MyDrive/Dental_Caries_Results",
    name="YOLOv8_First_Training",
    exist_ok=True,
)
```

**Saved first YOLOv8n test-set baseline:**

| Metric | Value |
|---|---:|
| Precision | `0.6989` = **69.89%** |
| Recall | `0.8396` = **83.96%** |
| mAP@0.50 | `0.7952` = **79.52%** |
| mAP@0.50:0.95 | `0.6340` = **63.40%** |
| Training epochs | **20** |
| Test images | **230** |
| Test instances in saved notebook report | **682** (from progress document; not independently rerun here) |

**Example image tested:**

`/content/YOLO_Caries_Training/images/test/anonymous-maxillaryView-1726818272842.jpg`

- Ground truth: **6** class `D` boxes.
- Predicted: **6** class `D` boxes with approximately 0.801, 0.783, 0.705, 0.691, 0.512, 0.412 confidence.
- One-to-one Hungarian assignment (`scipy.optimize.linear_sum_assignment(-iou_matrix)`) matched all six at IoU >= 0.5; per-match IoUs **0.883, 0.833, 0.825, 0.926, 0.836, 0.893**; mean **0.866**. **This is one image, not the full test-set accuracy.**

---

## 4. Caries-Spectra dataset, cleaning and splits

### Original data and backup paths

| Item | Location |
|---|---|
| User's ZIP uploaded to Drive | `/content/drive/MyDrive/Caries_Classification_Dataset.zip` |
| Extracted root | `/content/Caries_Classification/Caries_Dataset` |
| Working cleaned folder | `/content/Caries_Cleaned` |
| Working train/valid/test root | `/content/Caries_Split` |
| **Durable prepared split ZIP** | `/content/drive/MyDrive/Caries_Classification_Split.zip` |
| Classification notebook | `Dental_Caries_Severity_Classification.ipynb` in Google Colab; Git tracking **not confirmed** |

Raw main-folder image counts:

| Directory/class | Main-folder images |
|---|---:|
| `NoEnamel_Caries` | 400 |
| `EarlyStageEnamel_Caries` | 800 |
| `AdvanceEnamel_Caries` | 800 |
| **Total** | **2,000** |

`NoEnamel_Caries/[Originals]` additionally had **234 images**, **excluded from main-folder counts and classifier splits**. Other two class folders did not have `[Originals]`. Some images in `[Originals]` and main folder share stems and may represent related/original/processed views; this relationship was not clinically or provenance-verified.

**Quality checks:**

- SHA-256 byte-exact duplicate groups: **0** across 2,000 main-folder images.
- Perceptual hashing (`ImageHash` / `imagehash.phash`) returned **218 groups with identical pHash**, comprising **563 images** and **345 extra copies within those groups**.
- **Four pHash groups spanned conflicting early/advanced labels**, totaling **14 images** flagged and excluded from the working dataset, without deleting originals:

```text
AdvanceEnamel_Caries/AdvanceEnamel_Caries_128.jpg
AdvanceEnamel_Caries/AdvanceEnamel_Caries_192.jpg
AdvanceEnamel_Caries/AdvanceEnamel_Caries_270.jpg
AdvanceEnamel_Caries/AdvanceEnamel_Caries_415.jpg
AdvanceEnamel_Caries/AdvanceEnamel_Caries_438.jpg
AdvanceEnamel_Caries/AdvanceEnamel_Caries_541.jpg
AdvanceEnamel_Caries/AdvanceEnamel_Caries_687.jpg
EarlyStageEnamel_Caries/EarlyStageEnamel_Caries_066.jpg
EarlyStageEnamel_Caries/EarlyStageEnamel_Caries_437.jpg
EarlyStageEnamel_Caries/EarlyStageEnamel_Caries_439.jpg
EarlyStageEnamel_Caries/EarlyStageEnamel_Caries_440.jpg
EarlyStageEnamel_Caries/EarlyStageEnamel_Caries_441.jpg
EarlyStageEnamel_Caries/EarlyStageEnamel_Caries_442.jpg
EarlyStageEnamel_Caries/EarlyStageEnamel_Caries_443.jpg
```

- Cross-category image pair `EarlyStageEnamel_Caries_066.jpg` and `AdvanceEnamel_Caries_541.jpg` was displayed and appeared to show the same tooth despite different labels; **not independently clinically adjudicated**. Exclusion was precautionary.
- Remaining cleaned **1,986 images**: `NoEnamel_Caries=400`, `EarlyStageEnamel_Caries=793`, `AdvanceEnamel_Caries=793`.
- Used **70% / 15% / 15% group-aware-ish per-class random split with seed 42**, grouping identical **pHash** images within each class. This prevents identical pHashes crossing splits, **not** all near-duplicates/patient-level leakage. No formal patient IDs available/verified.

**Final verified split counts:**

| Split | No enamel | Early stage | Advanced | Total |
|---|---:|---:|---:|---:|
| Train | 280 | 556 | 559 | **1,395** |
| Valid | 60 | 121 | 119 | **300** |
| Test | 60 | 116 | 115 | **291** |
| **Total** | **400** | **793** | **793** | **1,986** |

Verification printed `OVERALL TOTAL: 1986`, `Identical perceptual hashes across splits: 0`, `Initial split verification PASSED!`. Prepared split ZIP saved to Drive. **Do not reshuffle before comparing saved model results.**

---

## 5. MobileNetV2 classifier — trained and evaluated

**Training:** TensorFlow/Keras **2.21.0** in Google Colab; GPU available. `tf.keras.utils.image_dataset_from_directory`, 224×224, batch 16, `label_mode='categorical'`, training seed 42, validation/test `shuffle=False`.

**Model structure:** ImageNet-pretrained `MobileNetV2(input_shape=(224,224,3), include_top=False, weights='imagenet')`, backbone `trainable=False`; `Input → RandomFlip('horizontal') → RandomRotation(0.05) → Rescaling(1/127.5, offset=-1) → MobileNetV2(training=False) → GlobalAveragePooling2D → Dropout(0.3) → Dense(3, softmax)`.

**Training config:** Adam `learning_rate=0.001`; categorical cross-entropy; accuracy; up to **15 epochs**, `ModelCheckpoint(save_best_only=True, monitor='val_loss')`, `EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True)`, `ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-5)`. **Actual number of completed epochs was not supplied**; do not claim all 15 ran.

| Resource | Path |
|---|---|
| Best Keras checkpoint in Drive | `/content/drive/MyDrive/Dental_Caries_Results/MobileNetV2/best_model.keras` |
| Exported local weight | `Dental-Caries-Detection/models/mobilenetv2.keras` (~9.23 MB) |
| Saved confusion matrix | `/content/drive/MyDrive/Dental_Caries_Results/MobileNetV2/confusion_matrix.png` |
| Saved Grad-CAM sample | `/content/drive/MyDrive/Dental_Caries_Results/MobileNetV2/gradcam_sample.png` |
| Saved metrics JSON | `/content/drive/MyDrive/Dental_Caries_Results/MobileNetV2/evaluation_results.json` |

**291-image held-out image-split test metrics:**

| Metric | MobileNetV2 |
|---|---:|
| Test accuracy | **87.63%** (`0.8763`), 255/291 correct |
| Test loss | **0.3050** |
| Macro precision | `0.9032` |
| Macro recall | `0.8746` |
| Macro F1 | `0.8858` |
| Weighted F1 | `0.8776` |

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `AdvanceEnamel_Caries` | 0.9065 | 0.8435 | 0.8739 | 115 |
| `EarlyStageEnamel_Caries` | 0.8030 | 0.9138 | 0.8548 | 116 |
| `NoEnamel_Caries` | 1.0000 | 0.8667 | 0.9286 | 60 |

**Confusion matrix** (class order `Advance`, `Early`, `No`; rows = actual, columns = predicted), inferred from explicitly reported counts and shown matrix:

```text
[[ 97, 18,  0],
 [ 10,106,  0],
 [  0,  8, 52]]
```

---

## 6. EfficientNet-B0 classifier — trained and evaluated

**Training settings:** Same **1,395 train / 300 validation / 291 test**, 224×224, batch 16, seed 42. ImageNet-pretrained `EfficientNetB0(input_shape=(224,224,3), include_top=False, weights='imagenet')`; backbone frozen, `Input → RandomFlip('horizontal') → RandomRotation(0.05) → EfficientNetB0(training=False) → GlobalAveragePooling2D → Dropout(0.3) → Dense(3, softmax)`. **No extra external MobileNet-style rescaling**. Adam 0.001, categorical cross-entropy, up to 15 epochs with same checkpoint, early stopping and LR reduction. Actual completed epoch count not reported.

| Resource | Path |
|---|---|
| Best checkpoint in Drive | `/content/drive/MyDrive/Dental_Caries_Results/EfficientNetB0/best_model.keras` |
| Exported local weight | `Dental-Caries-Detection/models/efficientnetb0.keras` (~16.30 MB) |
| Confusion matrix | `/content/drive/MyDrive/Dental_Caries_Results/EfficientNetB0/confusion_matrix.png` |
| Grad-CAM sample | `/content/drive/MyDrive/Dental_Caries_Results/EfficientNetB0/gradcam_sample.png` |
| Metrics JSON | `/content/drive/MyDrive/Dental_Caries_Results/EfficientNetB0/evaluation_results.json` |

**291-image held-out image-split test:**

| Metric | EfficientNet-B0 |
|---|---:|
| Test accuracy | **87.97%** (`0.8797`), 256/291 correct |
| Test loss | **0.3145** |
| Macro precision | **89.61%** (`0.8961`) — as reported in discussion |
| Macro recall | **88.29%** (`0.8829`) — as reported in discussion |
| Macro F1 | **88.86%** (`0.8886`) — as reported in discussion |
| Weighted F1 | **88.05%** (`0.8805`) — as reported in discussion |

**Per-class recall**: Advanced **86.09%** (99/115); Early **88.79%** (103/116); No enamel **90.00%** (54/60). Detailed EfficientNet confusion-matrix cell values are in the saved PNG/JSON; **do not invent them based on recall alone**.

**Comparison conclusion:** EfficientNet overall test accuracy **+0.34 percentage points** (one additional correct image), slightly higher weighted F1; MobileNet lower test loss and higher early-stage recall (91.38% vs 88.79%). These are small differences; no statistical superiority or clinical validity established.

**Comparison JSON:** `/content/drive/MyDrive/Dental_Caries_Results/Classification_Model_Comparison.json`.

---

## 7. Grad-CAM — implemented for both models

In the saved functional models, the Keras pretrained backbones are **nested Functional layers**. The full top-level layers were inspected; Grad-CAM was computed using **nested backbone final feature outputs** and the trained head (not by assuming the output of the softmax Dense is a convolutional layer).

| Model | Nested backbone name | Last feature layer | Feature map |
|---|---|---|---|
| MobileNetV2 | `mobilenetv2_1.00_224` | `out_relu` | `(None, 7, 7, 1280)` |
| EfficientNet-B0 | `efficientnetb0` | `top_activation` | `(None, 7, 7, 1280)` |

**Implementation logic:** open image as RGB → resize to 224×224 → float32 0–255 → call augmentation layers with `training=False` → MobileNet-only rescaling → nested backbone with `training=False` → global average pool + dropout (inference) + Dense softmax → with `tf.GradientTape`, gradient of **predicted class score** w.r.t. feature maps → channel-weighted average of gradients over spatial axes → weighted sum of feature channels → ReLU, normalize → resize heatmap to 224×224 → overlay `jet` color map on original → save plot PNG to Drive. No retraining.

**Shared example:** `EarlyStageEnamel_Caries_002.jpg` from `/content/Caries_Split/test/EarlyStageEnamel_Caries/`.

- MobileNetV2 predicted **Early-Stage**, **93.67%** score. Hot activation upper-middle part of tooth with some overlap near dark fissure.
- EfficientNet-B0 predicted **Early-Stage**, **80.69%** score. Strongest activation toward upper-right/image edge.
- Both matched this sample's dataset label, but **Grad-CAM does not diagnose cavities nor prove the highlighted pixels are medically correct**. EfficientNet boundary activation was flagged for further investigation.

**Saved samples:** `.../MobileNetV2/gradcam_sample.png` and `.../EfficientNetB0/gradcam_sample.png`.

---

## 8. End-to-end model integration experiments (Colab)

**First image:** `anonymous-maxillaryView-1726818272842.jpg`, 6 YOLO detections. Tight crops were visualized, then **expanded by 30% per side**; expanded crops were visualized and showed more tooth context. Both classifiers processed these 6 RGB/224×224 float32 crops and **both labeled all 6 Advanced**.

Per-region scores from the Colab/local/Swagger workflow:

| Region | YOLO detection score | MobileNetV2 Advanced | EfficientNet-B0 Advanced |
|---|---:|---:|---:|
| 1 | 0.8006 | 98.57% | 86.86% |
| 2 | 0.7833 | 91.07% | 84.21% |
| 3 | 0.7051 | 99.90% | 94.06% |
| 4 | 0.6913 | 99.73% | 94.42% |
| 5 | 0.5122 | 97.48% | 64.47% |
| 6 | 0.4121 | 99.93% | 94.49% |

**Second experiment:** five selected YOLO test photographs (`np.random.default_rng(42)`, `replace=False`), detecting **3 + 4 + 5 + 1 + 4 = 17** regions. Each classifier predicted **15 Advanced, 2 Early, 0 No enamel**. A follow-up **per-region** comparison confirmed **15/17 matching labels = 88.24% agreement**, **2 disagreements** (identical overall class counts did not imply perfect per-region agreement). Across both tests each classifier labeled 21/23 regions Advanced.

**Disagreement examples visually inspected:**

- Maxillary region: MobileNetV2 **Early 74.74%** vs EfficientNet-B0 **Advanced 54.29%**.
- Mandibular region: MobileNetV2 **Advanced 95.96%** vs EfficientNet-B0 **Early 47.93%**.

**Disagreement log:** `/content/drive/MyDrive/Dental_Caries_Results/Integration_Disagreements.json` (two review-required examples).

**Reusable Colab `predict_dental_caries(image_path)` and matching local Python function** implemented to return:

```json
{
  "image": "test_image.jpg",
  "total_regions": 6,
  "regions": [
    {
      "region": 1,
      "bounding_box": [1391, 710, 1636, 865],
      "detection_confidence": 0.8006,
      "MobileNetV2": {
        "prediction": "AdvanceEnamel_Caries",
        "confidence": 0.9857
      },
      "EfficientNetB0": {
        "prediction": "AdvanceEnamel_Caries",
        "confidence": 0.8686
      },
      "status": "Agreement",
      "final_prediction": "AdvanceEnamel_Caries"
    }
  ]
}
```

The example JSON above abbreviates the six-element `regions` array; the actual Swagger test returned all **six** results. For no detection, the function returns `regions: []`, `total_regions: 0`, and message `No suspected regions detected`.

**Integration result artifact:** `/content/drive/MyDrive/Dental_Caries_Results/Integration/combined_prediction_results.json`.

**Annotated image artifacts:**
- `/content/drive/MyDrive/Dental_Caries_Results/Integration/annotated_prediction.jpg`
- `/content/drive/MyDrive/Dental_Caries_Results/Integration/annotated_prediction_improved.jpg`

The PIL annotation code initially failed to open the hard-coded DejaVuSans font path. Fallback font loading was provided (see troubleshooting). User replied `ok` after applying the fix, but a second improved-image screenshot/output was **not independently shown**.

**Do not claim:** a clinically validated three-class severity label for YOLO crops; confirmed generalization between datasets; calibrated uncertainty; or 88.24% actual severity accuracy. Domain shift remains the major integration research limitation.

---

## 9. Backend — verified FastAPI integration

### Local trained models

Verified on Windows after download/export from Google Drive:

| Filename | Size (reported) | Usage |
|---|---:|---|
| `Dental-Caries-Detection/models/best.pt` | 6.20 MB | YOLOv8n detector |
| `Dental-Caries-Detection/models/mobilenetv2.keras` | 9.23 MB | Three-class MobileNetV2 |
| `Dental-Caries-Detection/models/efficientnetb0.keras` | 16.30 MB | Three-class EfficientNetB0 |

### `backend/app/services/caries_prediction.py`

- `BASE_DIR = Path(__file__).resolve().parents[3]` resolves to `Dental-Caries-Detection` from `backend/app/services/caries_prediction.py`.
- `MODEL_DIR = BASE_DIR / 'models'`.
- Defines `YOLO_PATH = models/best.pt`, `MOBILENET_PATH = models/mobilenetv2.keras`, `EFFICIENTNET_PATH = models/efficientnetb0.keras`.
- `@lru_cache(maxsize=1)` on `load_models()` so weights aren't loaded on each inference call.
- `YOLO(str(YOLO_PATH))`; `tf.keras.models.load_model(..., compile=False)` for each classifier.
- `CLASS_NAMES = ['AdvanceEnamel_Caries','EarlyStageEnamel_Caries','NoEnamel_Caries']`.
- `predict_dental_caries(image_path)` opens an RGB image, calls YOLO at `conf=0.25`, obtains `xyxy` and detection confidence, expands each box by 30% per side, resizes crops to 224×224 float32, predicts on both classifiers, compares class IDs, returns JSON-serializable dict with boxes, per-model predictions/scores and agreement status.

**Exact local model-load smoke test** (executed successfully from backend directory with `caries-venv` active):

```powershell
python -c "from app.services.caries_prediction import load_models; yolo, mobile, efficient = load_models(); print('SUCCESS: All three AI models loaded!')"
```

### `backend/app/routes/caries.py`

Implemented:

```python
router = APIRouter(prefix="/api/caries", tags=["Dental Caries"])

@router.post("/predict")
def predict_caries(file: UploadFile = File(...)):
    ...
```

- Accepts declared MIME types `image/jpeg` and `image/png`.
- Copies upload to temporary JPG/PNG file using `tempfile.NamedTemporaryFile(delete=False, suffix=...)` and `shutil.copyfileobj`.
- Calls `predict_dental_caries(temp_path)` and substitutes `results['image'] = file.filename`.
- Deletes temp file with `Path.unlink(missing_ok=True)` in `finally`; closes uploaded file.
- **Current limitations:** no upload-size cap, decoded-image validation, malicious/corrupt image handling distinction, concurrency/performance hardening, or safe handling of all invalid inputs; broad `except Exception` -> HTTP 500 `Image prediction failed.`. Suitable for local prototype only.

### `backend/app/main.py` — reported final form

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.caries import router as caries_router
from app.routes.health import router as health_router

app = FastAPI(title="Dental Caries Detection API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(caries_router)
```

**Run backend:**

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research\Dental-Caries-Detection\backend
C:\caries-venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`.
- Confirmed `POST /api/caries/predict` visible, `test_image.jpg` uploaded, JSON response with six correctly structured regions and all classes `AdvanceEnamel_Caries`, matching Colab/local CLI results. Successful application behavior reported; exact printed HTTP status code was not supplied, though a complete JSON response appeared.
- Health endpoint: existing frontend calls `GET /health` through `getHealth()`; React displayed `Backend: Connected`.

### Local smoke test `backend/test_prediction.py`

Created, executed successfully, committed. It loads `backend/test_image.jpg`, calls `predict_dental_caries`, prints image, six region scores and classes. Relevant command:

```powershell
python -u test_prediction.py
Write-Host "Python exit code: $LASTEXITCODE"
```

Confirmed output: `Running dental caries detection...`, `Detected regions: 6`, six model agreement results, `Local prediction test completed!`, **`Python exit code: 0`**. `-u` fixed initially invisible/buffered output; first normal run showed only TensorFlow logs and returned to prompt.

---

## 10. Frontend — verified React/Vite integration

### `frontend/src/services/api.js`

```javascript
const API_BASE_URL = 'http://127.0.0.1:8000';

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
  return response.json();
}

export async function predictCaries(file) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE_URL}/api/caries/predict`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    let message = `Prediction failed: ${response.status}`;
    try {
      const errorData = await response.json();
      message = errorData.detail || message;
    } catch { /* fall back to generic HTTP status */ }
    throw new Error(message);
  }
  return response.json();
}
```

Do not manually set multipart `Content-Type`; `fetch` handles it with `FormData`.

### `frontend/src/pages/Home.jsx`

Features actually created and tested:

- Initial backend health-check via `useEffect`, `getHealth()`, and `status` state.
- Upload JPG/PNG, preview via `URL.createObjectURL(file)`, revoke preview URL in effect cleanup.
- Upload image using `predictCaries(file)` and display analyzing/error states.
- `imageDimensions` state with original `naturalWidth` and `naturalHeight`, populated by `new Image().onload` in `handleFileChange`. (Needed for box alignment.)
- Bounding boxes rendered with absolutely positioned overlays in a `relative inline-block` container around an `<img className='block max-h-96 max-w-full ...'>`; percentages use `x1/width`, `y1/height`, `(x2-x1)/width`, `(y2-y1)/height`.
- Region labels R1–R6; red for agreed model predictions, purple for `Uncertain`.
- Individual result cards show detection confidence, each classifier's class/score, final preliminary class, and review-required warning on disagreement.
- Dynamic analysis summary counts: Detected Regions, Model Agreement, Advanced Predictions, Review Required.
- Research-prototype disclaimer; no-detection message avoids claiming no disease.
- Tailwind classes are used for styling; existing React/Vite scaffold preserved.

**Verified screenshot:** six correctly aligned red bounding boxes over posterior teeth and labels R1–R6 for the uploaded test photograph. User independently confirmed **all six prediction cards display correctly** (YOLO scores: 80.06%, 78.33%, 70.51%, 69.13%, 51.22%, 41.21%, and both classifiers Advanced in each).

**Run frontend:**

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research\Dental-Caries-Detection\frontend
npm run dev
```

If dependencies are missing: `npm install` and retry. Vite URL `http://localhost:5173/`. Keep backend running in another terminal.

**Last precise planned/not implemented frontend change:** **Step 73** would add `const [selectedRegion, setSelectedRegion] = useState(null);` plus `setSelectedRegion(null)` when a new file is chosen, followed by making R1–R6 clickable and highlighting matching cards. **User explicitly did not do Step 73**, so neither state change nor click handling should be represented as completed. Start here when returning to implementation.

---

## 11. Development environment and solved errors

### Windows Python environment

- OS: Windows 11, VS Code, PowerShell, Python **3.11.9**.
- Original backend `.venv` contained FastAPI and Uvicorn but not AI libraries. Installing TensorFlow inside `...OneDrive\Desktop\J26-IT-458-Research\Dental-Caries-Detection\backend\.venv` failed on a deeply nested TensorFlow C header:

```text
OSError: [Errno 2] No such file or directory:
...\.venv\Lib\site-packages\tensorflow\include\external\envoy_api\envoy\extensions\load_balancing_policies\client_side_weighted_round_robin\v3\client_side_weighted_round_robin.upb.h
```

- Worked around probable **Windows long-path** issue by creating **short external venv** without moving repo:

```powershell
deactivate
py -3.11 -m venv C:\caries-venv
C:\caries-venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install tensorflow==2.21.0 ultralytics pillow numpy python-multipart
python -m pip install fastapi "uvicorn[standard]" python-multipart
```

- Verified installed/running:

| Package | Verified version |
|---|---|
| Python | 3.11.9 |
| TensorFlow | 2.21.0 |
| Keras | 3.15.1 (from pip output) |
| Ultralytics | 8.4.178 |
| NumPy | 2.4.6 |
| FastAPI | 0.143.2 |
| Uvicorn | 0.54.0 |
| Pillow | 12.3.0 (from pip output) |
| Python-multipart | 0.0.32 (from pip output) |

**Verification commands:**

```powershell
python -c "import tensorflow as tf; from ultralytics import YOLO; import numpy; from PIL import Image; print('TensorFlow:', tf.__version__); print('Ultralytics: OK'); print('NumPy:', numpy.__version__); print('Pillow: OK')"
python -c "import fastapi, uvicorn; print('FastAPI:', fastapi.__version__); print('Uvicorn:', uvicorn.__version__)"
```

- TensorFlow emitted CPU optimization info and `TensorFlow GPU support is not available on native Windows for TensorFlow >= 2.11`. **Expected:** local inference on CPU; Colab GPU used for training. Do not suggest downgrading TF merely to silence message.

### Google Colab runtime recovery

- Google Drive mount via `from google.colab import drive; drive.mount('/content/drive')`.
- `/content/` is **ephemeral**; model ZIPs, checkpoints, summaries live under MyDrive. On restart remount Drive and extract `Caries_Classification_Split.zip` to `/content/Caries_Split`, or `YOLO_Caries_Cleaned.zip` to `/content` (verify extracted folder layout). Keep input root consistent.
- Ultralytics missing in a new classification notebook raised `ModuleNotFoundError: No module named 'ultralytics'`; fixed with `%pip install -q ultralytics` and `from ultralytics import YOLO`.
- `NameError: yolo_model_path is not defined` after a Colab runtime reset; fixed by redeclaring the saved Drive path and loading `YOLO(...)`. Not a corrupt model.
- PIL `OSError: cannot open resource` at `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` during improved annotation; remedied by font fallback:

```python
from PIL import ImageFont
font_size = max(20, image.width // 45)
try:
    font = ImageFont.truetype('DejaVuSans.ttf', font_size)
except OSError:
    try:
        font = ImageFont.truetype(
            '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
            font_size,
        )
    except OSError:
        font = ImageFont.load_default(size=font_size)
```

### Git push troubleshooting (solved)

First `git push -u origin hinam` compressed/wrote 42 objects but ended `error: failed to push some refs`. `git fetch origin` and `git ls-remote origin HEAD` temporarily failed with `fatal: Could not read from remote repository`, though the GitHub website was accessible. `git status -sb` indicated **`## hinam...origin/hinam [ahead 7]`**, and local commit log showed seven local-only commits.

Diagnostics and commands **actually run**:

```powershell
git branch --show-current
git status --short
git remote -v
git config --show-origin --get-all credential.helper
git config --show-origin --get-regexp "url\..*\.insteadof"
git -c credential.interactive=always -c core.askPass= ls-remote https://github.com/Mohammedhinam/J26-IT-458-Research.git HEAD
git ls-remote https://github.com/git/git.git HEAD
Test-NetConnection github.com -Port 443
git config --show-origin --get-regexp "http\..*proxy"
$env:GIT_TRACE = "1"
$env:GIT_CURL_VERBOSE = "1"
git ls-remote https://github.com/git/git.git HEAD
Remove-Item Env:GIT_TRACE
Remove-Item Env:GIT_CURL_VERBOSE
git ls-remote origin HEAD
git push -u origin hinam
```

Outcomes:
- Remote URL correct `https://github.com/Mohammedhinam/J26-IT-458-Research.git`.
- Credential helper `manager` set in `C:/Program Files/Git/etc/gitconfig`.
- No `insteadOf` rewrite and no Git `http.*proxy` setting reported.
- `Test-NetConnection github.com -Port 443`: **`TcpTestSucceeded: True`**.
- Verbose public repo request finally succeeded (`f57c9a73884400380bddd172acc88b569834f909 HEAD`); subsequent `git ls-remote origin HEAD` succeeded (`49ce34257777b15960d93da11ae412456f378411 HEAD`).
- Retried non-forced `git push -u origin hinam`; confirmed **SUCCESS**, remote `hinam -> hinam`, upstream configured. **Root cause of intermittent failure was not definitively established**. Do not claim a credential reset or proxy removal happened; neither did.

---

## 12. Git commits and push status — verified outputs

### Pre-existing commits (from earlier progress document; not created in this segment)

| ID | Original log message |
|---|---|
| `3bfae42` | Initial setup for dental caries detection component |
| `17538b6` | Connect React frontend with FastAPI backend |
| `e50bb44` | Add initial YOLOv8 caries detection training notebook |

### Seven commits created on `hinam` and pushed this session

| Order | Commit ID | **Actual** Git log message | Purpose |
|---|---|---|---|
| 1 | `a351031` | `feat(caries): integrate detection and severity classification models` | `backend/app/services/caries_prediction.py` |
| 2 | `ec0a2f4` | `feat(api): add dental caries prediction endpoint` | `backend/app/routes/caries.py`, `backend/app/main.py` |
| 3 | `64758d9` | `feat(frontend): connect React to dental caries prediction API` | `frontend/src/services/api.js` |
| 4 | `f87863e` | `add dental image analysis and detection visualization` | `frontend/src/pages/Home.jsx` |
| 5 | `2a789d6` | `add local AI prediction integration test` | `backend/test_prediction.py` |
| 6 | `a2a584c` | `update AI training results and implementation progress` | `docs/PROJECT_PROGRESS.md` |
| 7 | `0d69de7` | `exclude trained models and temporary test images` | root `.gitignore` |

The commit messages above reflect the **actual** `git log --oneline` output. Some do **not** use the earlier suggested conventional-commit wording, which is fine. Last local HEAD hash before push: **`0d69de7`**.

**Ignore rules applied** (existing rules preserved):

```gitignore
# Already present:
*.pt
.venv/

# Added:
*.keras
Dental-Caries-Detection/backend/test_image.jpg
```

The user's `git status --short` became **empty** (clean working tree) after commits. Final push reported:

```text
To https://github.com/Mohammedhinam/J26-IT-458-Research.git
   <old-hash>..<new-hash>  hinam -> hinam
branch 'hinam' set up to track 'origin/hinam'.
```

(`<old-hash>..<new-hash>` was shown in chat as placeholders, not actual hashes; **do not treat those as verified commit IDs**.)

**Useful Git commands for new chat:**

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research
git branch --show-current
git status -sb
git log -10 --oneline
git fetch origin
git status -sb
git push origin hinam
```

**No `git push --force`, `git reset`, or merge was done.** If changing `main` or integrating team branches, follow team approval and a separate PR workflow.

---

## 13. Verified completed vs planned / unverified

### VERIFIED AS COMPLETED (through user-reported outputs/screenshots/commands)

1. Prepared and cleaned YOLO bounding-box dataset; excluded 16 unusable pairs; trained YOLOv8n 20 epochs; reported four test metrics.
2. Inferred six boxes on a held-out YOLO sample; verified unique IoU assignments for that sample.
3. Extracted Caries-Spectra and counted 2,000 main images, detected no SHA duplicates, pHash groups and 14 possible label conflicts, created cleaned 1,986-image working set.
4. Created and checked 1,395 / 300 / 291 splits with no identical pHashes across splits, saved split ZIP to Drive.
5. Trained and evaluated pretrained MobileNetV2 and EfficientNet-B0 three-class heads, saved best `.keras` weights, confusion matrices, evaluation JSONs, comparative JSON.
6. Generated example Grad-CAM for both classifiers and examined the results.
7. Combined YOLOv8 with padded crops and both classifiers in Colab; tested five extra photos and investigated two disagreements.
8. Created combined prediction function; saved JSON prediction output and preliminary annotated dental image.
9. Downloaded all three model files into local `models/` folder, successfully loaded all three with TensorFlow/Ultralytics in Windows Python 3.11 short venv.
10. Executed CLI local inference successfully, exit code 0, same six-region predictions as Colab.
11. Created and successfully exercised FastAPI prediction endpoint in Swagger.
12. Updated React API service and Home page, successfully uploaded image, displayed six prediction cards, bounding boxes aligned over original image, summary counts.
13. Created and **pushed seven commits** to remote `origin/hinam` after resolving connectivity issues.

### PLANNED / NOT VERIFIED COMPLETE

1. **Step 73 interactive bounding-box selection/highlight**: user deferred. Don't mark complete.
2. Proper backend request validation: enforce max file size, verified image format/decode, safe dimensions, clearer errors, resource limits, security/privacy controls, tests.
3. Automated regression/integration tests, frontend test suite, CI, API schema tightening; only a local one-image script is known.
4. Larger independent evaluation of the **full YOLO-crop-to-severity** pipeline; labels for YOLO detections lack expert-confirmed severity ground truth.
5. More rigorous duplicate analysis, patient-level train/validation/test separation, external dataset validation, evaluation of calibration and out-of-distribution crops.
6. More diverse manual image testing (different sizes, no detections, rotated/corrupted/non-JPG images, edge cases and error states), speed benchmarking on native Windows CPU.
7. Grad-CAM integrated into FastAPI and React **not done**. Only Colab sample visualizations exist.
8. Review and adjudicate 14 pHash-conflict images with qualified annotator/dentist if possible; no re-labeling done.
9. ICDAS-guided clinical evaluation was discussed as a future possibility; user explicitly said **not now**. No ICDAS integration implemented.
10. Full integration with other team members' components into overall project **not done in this chat**.
11. Teams Planner updates for the completed work **not verified**; user wants them in the separate dedicated chat.
12. Severity training notebook checked into Git: **not established**. Save/export notebook and suitably lightweight reproducibility config/source code before representing it as repository-tracked.
13. Production deployment, multi-user handling and clinical claims: **not done**.

---

## 14. Suggested next-session workflow (one step at a time)

1. **Begin at Step 73**: ask to inspect current `Home.jsx` (or use the known working version) and add `selectedRegion` state, clear selection when file changes, bind click handlers to box overlays, and highlight corresponding cards. Maintain image coordinate scaling and accessibility (use actual buttons/keyboard focus for boxes).
2. Verify R1–R6 selection visually in browser **before committing** new changes.
3. Add stronger upload image validation and response errors, and at least a few integration tests. Be careful not to block valid large intraoral photos.
4. Confirm `Dental_Caries_Severity_Classification.ipynb` is exported/backed up and create reproducible training/evaluation code or notebook commit if desired (omit heavy data and weights).
5. For a full scientific comparison, collect/annotate **independent severity ground truth** for YOLO crops, review pHash/patient leakage and dataset label definitions; explicitly report domain shift. Do not interpret the pipeline's technical 6/6 agreement as clinical accuracy.
6. Update the separate **Plan Teams Planner Tasks** conversation bucket `02 – Dental Caries Detection – Hinamul` using verified milestones and Git hashes. Don't assert this is already done.
7. Keep changes on `hinam`, stage exact feature files, make work-specific commits, push normally, and merge into `main` only through team coordination.

### Immediate restart commands

**Backend (PowerShell terminal 1):**

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research\Dental-Caries-Detection\backend
C:\caries-venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

**Frontend (PowerShell terminal 2):**

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research\Dental-Caries-Detection\frontend
npm run dev
```

**Check frontend/backend:** `http://localhost:5173/`, `http://127.0.0.1:8000/docs`, `GET http://127.0.0.1:8000/health`.

**Git:**

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research
git branch --show-current
git status -sb
git log -7 --oneline
```

### Colab restart snippets

```python
from google.colab import drive
drive.mount('/content/drive')

from pathlib import Path
from zipfile import ZipFile

classification_zip = Path('/content/drive/MyDrive/Caries_Classification_Split.zip')
classification_dir = Path('/content/Caries_Split')
if not classification_dir.exists():
    with ZipFile(classification_zip) as zf:
        zf.extractall(classification_dir)

# Confirm folder structure before inference/training:
for split in ('train', 'valid', 'test'):
    print(split, (classification_dir / split).exists())
```

```python
# If restoring YOLO in a fresh Colab runtime:
from pathlib import Path
from zipfile import ZipFile

yolo_zip = Path('/content/drive/MyDrive/YOLO_Caries_Cleaned.zip')
yolo_root = Path('/content/YOLO_Caries_Training')
if not yolo_root.exists():
    with ZipFile(yolo_zip) as zf:
        zf.extractall('/content')
print('YOLO root exists:', yolo_root.exists())
print('YOLO model exists:', Path('/content/drive/MyDrive/Dental_Caries_Results/YOLOv8_First_Training/weights/best.pt').exists())
```

**Colab packages if new runtime:** `%pip install -q ultralytics ImageHash` (TensorFlow in Colab availability/version should be checked before loading `.keras`).

---

## 15. Research reporting safeguards

- Object detection **mAP@50 79.52%** is **not** caries severity classification accuracy. Classification accuracies **87.63% / 87.97%** are from the **separate image-level Caries-Spectra test set**, not the combined YOLO crop pipeline.
- The combined pipeline **functions technically**, but on a different image distribution and without external clinical ground truth for severity. 6/6 agreement in one photo and 15/17 agreement in other photos are **inter-model agreement** only.
- Models mostly output `AdvanceEnamel_Caries` on YOLO-produced crops; **possible domain shift or prediction bias**, not proof of advanced dental disease in these photos.
- The three dataset severity categories are **not verified as ICDAS codes**; do not present them as clinically mapped ICDAS 0–6 scores.
- The two pHash-conflict groups' labels cannot be resolved by looking at a screenshot alone; 14 images were excluded rather than relabeled.
- **No clinical diagnostic claims**, no replacements for dentist examination, and do not upload identifiable patient photos publicly without authorization.

---

**Handover closing state:** Finished local React + FastAPI + 3-model technical integration and uploaded **7 Git commits to `origin/hinam`**. Pause before **Step 73 interactive box selection**, and do Planner updates in the user's separate Planner chat. Everything marked planned/unverified above remains open.


---

## 16. Development update — 2026-10-17 (authoritative continuation)

### 16.1 Completed development and user-observed tests

1. **Step 73, interactive bounding-box selection — done and user-tested.** `frontend/src/pages/Home.jsx`: selected-region state; click/keyboard selection for bounding boxes; corresponding prediction card highlight; resets on image change/reanalysis.
2. **Steps 74–75, image validity and end-to-end verification — partially complete.** `backend/app/routes/caries.py` retains `POST /api/caries/predict`, validates MIME and actual JPEG/PNG content via Pillow `Image.verify()`, retains HTTP 400 errors instead of hiding them as HTTP 500, and removes temporary uploads. The user reported HTTP **200** for an actual dental JPEG, HTTP **400** for a text file named `invalid_test.jpg`, and the React error message `Invalid or corrupted image`. The user rechecked frontend detection, prediction cards, and selection. **Max file size, pixel limits, decoded-image protections, privacy controls and automated negative tests are not finished.**
3. **Steps 76.3–76.13, Grad-CAM local verification — done for functionality.** The saved Keras models' nested backbone outputs were inspected locally: MobileNetV2 `mobilenetv2_1.00_224` → `out_relu` and EfficientNet-B0 `efficientnetb0` → `top_activation`, both feature maps `(None, 7, 7, 1280)`. `backend/app/services/gradcam.py` computes gradient-weighted heatmaps using each model's existing preprocessing, including MobileNet-only rescaling. Separate full-photo and YOLO-R1 30%-padded-crop visual experiments produced PNG heatmaps/overlays. On one R1 crop both classifiers predicted class index **0** (`AdvanceEnamel_Caries`). Heatmaps are visual interpretations, not verified lesion masks or clinical evidence. Recorded single-region heatmap timings: MobileNetV2 **0.39 s**; EfficientNet-B0 **0.68 s** (one run each; exclude initial loading, YOLO, network, rendering).
4. **Steps 76.15–76.23, backend Grad-CAM API — done and user-tested.** `POST /api/caries/gradcam` accepts multipart `file` and integer `region`, validates actual JPEG/PNG, reruns YOLOv8n at `conf=0.25`, selects `boxes[region-1]`, applies existing 30% crop padding, computes both classifier Grad-CAM maps and creates colored PNG overlays encoded as `data:image/png;base64,...`. Swagger finally returned HTTP **200**, with both overlay fields. Corrected initial indentation errors and a Matplotlib API compatibility failure by using `matplotlib.colormaps["jet"]` rather than removed `cm.get_cmap`.
5. **Steps 76.24.1–76.24.8, React Grad-CAM visualization — done and user-tested.** `frontend/src/services/api.js` adds `getGradcam(file, region)`. `Home.jsx` adds Grad-CAM results/loading/error state, an explicit **Generate Grad-CAM** button for selected region, two displayed overlays, selection resets, and `useRef` request-ID checks to ignore stale responses. User reported both overlays displayed and a successful R1-to-R2 switching test.
6. **Step 76.25, bounding-box identity consistency — NOT DONE.** Test file `backend/test_region_consistency.py` exists and was committed; user answered `ok` to the instruction but provided **no actual run output**, so `All region bounding boxes match!` is not verified. The API currently reruns YOLO for Grad-CAM. Number matching is only a hypothesis until tested; even a passing one-photo test cannot guarantee stable ordering for every input.

### 16.2 Files changed and Git verification

Commit: **`8ecabf9`**, message: `Add Grad-CAM integration, interactive region selection, and image validation`; eight files, **808 insertions, 17 deletions** reported by local git.

Committed files:

- `Dental-Caries-Detection/backend/app/routes/caries.py`
- `Dental-Caries-Detection/backend/app/services/gradcam.py`
- `Dental-Caries-Detection/backend/test_gradcam.py`
- `Dental-Caries-Detection/backend/test_region_consistency.py`
- `Dental-Caries-Detection/backend/test_region_crop.py`
- `Dental-Caries-Detection/backend/test_region_gradcams.py`
- `Dental-Caries-Detection/frontend/src/pages/Home.jsx`
- `Dental-Caries-Detection/frontend/src/services/api.js`

Git state user pasted:

```text
## hinam...origin/hinam
8ecabf9 (HEAD -> hinam, origin/hinam) Add Grad-CAM integration, interactive region selection, and image validation
```

Untracked artifacts intentionally excluded from Git: `backend/WhatsApp Image 2026-10-17 at 9.31.01 PM.jpeg`, `backend/gradcam_efficientnet_test.png`, `backend/gradcam_mobilenet_test.png`, `backend/gradcam_overlay_efficientnet.png`, `backend/gradcam_overlay_mobilenet.png`, `backend/gradcam_region1_crop.png`, `backend/gradcam_test.png`, `backend/region1_crop_test.png`. Model weights remain local/Drive, not in Git.

### 16.3 Immediate next session — resume one step at a time

**First and only next technical step: Step 76.25 — run committed bounding-box consistency test.** From a VS Code PowerShell terminal:

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\J26-IT-458-Research\Dental-Caries-Detection\backend
C:\caries-venv\Scripts\python.exe test_region_consistency.py
```

User should send the **full terminal output** (detected-region count; each Rn MATCH/MISMATCH; final assertion result). Do **not** claim this test passed until actual output appears. If it fails, prioritize a stable region identifier / same detection geometry across API requests rather than modifying trained model architecture.

**PP1 target: 2026-10-22.** After bounding-box verification: preserve functional demo and record representative screenshots, predictable startup instructions, empirical timing, successful/invalid/no-detection cases, and explicit distinction between separate dataset test metrics vs end-to-end clinical performance. No retraining required merely to demonstrate Grad-CAM. Keep all implementation on branch `hinam`; other members' branches and overall system integration unaffected.

**Teams Planner:** bucket `02 – Dental Caries Detection – Hinamul` still **not verified updated**; user prefers handling it separately.

**Status file publication:** This version was created from the user's uploaded handover. It must still be copied into the local repository and committed/pushed separately; the `8ecabf9` commit did **not** include this October 17 status update.
