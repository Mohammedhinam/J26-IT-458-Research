# Project Progress

## 1. Project Overview

**Project:** AI-Based Dental Caries Detection and Severity Assessment

This research component aims to detect suspected dental caries from intraoral photographs and estimate enamel caries severity using AI models.

The system uses:
- **YOLOv8** for suspected caries detection and localization.
- **MobileNetV2 and EfficientNet-B0** for three-class severity classification.
- **Grad-CAM** for model explainability.
- **FastAPI** for backend prediction services.
- **React/Vite** for the web application frontend.

## 2. Completed Tasks

### 2.1 Project Setup
- Created the project folder structure, frontend, backend, notebooks, models, documentation, and tests directories.
- Configured the React/Vite frontend and FastAPI backend.
- Implemented the backend health-check endpoint and React connectivity checking.

### 2.2 YOLOv8 Caries Detection
- Prepared and cleaned the annotated dental image dataset.
- Retained 2,211 image-label pairs after excluding 16 pairs containing invalid annotations.
- Trained YOLOv8n for 20 epochs.
- Evaluated the trained model using 230 test images.
- Tested bounding-box predictions and verified IoU matching on a sample image.

**YOLOv8 Test Results**

| Metric | Result |
|---|---|
| Precision | 69.89% |
| Recall | 83.96% |
| mAP@50 | 79.52% |
| mAP@50–95 | 63.40% |

### 2.3 Dental Caries Severity Classification
- Prepared the Caries-Spectra dataset containing three enamel caries categories.
- Checked exact duplicates and identical perceptual hashes.
- Flagged and excluded 14 images with potentially conflicting category labels.
- Prepared 1,986 images for classification.
- Created training, validation, and testing splits while keeping identical perceptual-hash groups together.
- Trained MobileNetV2 and EfficientNet-B0 using ImageNet transfer learning.
- Evaluated both models on the same 291-image test set.

**Classification Model Comparison**

| Metric | MobileNetV2 | EfficientNet-B0 |
|---|---|---|
| Test Accuracy | 87.63% | 87.97% |
| Test Loss | 0.3050 | 0.3145 |
| Weighted F1-score | 87.76% | 88.05% |

Both models demonstrated similar performance. EfficientNet-B0 achieved slightly higher test accuracy, while MobileNetV2 achieved slightly lower test loss.

### 2.4 Grad-CAM Explainability
- Generated Grad-CAM heatmaps for MobileNetV2.
- Generated Grad-CAM heatmaps for EfficientNet-B0.
- Compared activation regions for the same dental test image.
- Saved visualization results in Google Drive.

### 2.5 AI Model Integration
- Combined YOLOv8 with MobileNetV2 and EfficientNet-B0.
- Implemented 30% bounding-box expansion to provide additional tooth context.
- Tested severity classification on YOLOv8-detected regions.
- Implemented model agreement checking.
- Flagged conflicting predictions as `Uncertain - Review Required`.
- Created a reusable combined prediction function.
- Tested the integrated pipeline in Google Colab and locally in VS Code.

In one integration test using 17 detected regions, the two severity classification models agreed on 15 predictions (88.24%).

### 2.6 FastAPI Backend
- Created the combined AI prediction service.
- Implemented `POST /api/caries/predict` for dental image uploads and predictions.
- Registered the prediction route in FastAPI.
- Successfully tested the endpoint using Swagger UI.
- Verified that YOLOv8, MobileNetV2, and EfficientNet-B0 load and run in the local Python environment.

### 2.7 React Frontend
- Connected React to the FastAPI prediction endpoint.
- Implemented dental image upload and preview.
- Added image analysis functionality.
- Displayed YOLOv8 bounding boxes and region labels.
- Displayed MobileNetV2 and EfficientNet-B0 predictions.
- Added model agreement and uncertainty messages.
- Added an overall analysis summary showing detected regions, advanced predictions, agreements, and review-required cases.
- Successfully tested the end-to-end image analysis workflow.

## 3. Current Implementation Status

The research prototype currently supports:

**Dental image upload → YOLOv8 detection → Expanded image crops → Severity classification → Model agreement checking → React results display**

The trained models and the web application have been integrated and tested locally.

The integrated severity predictions are preliminary AI assessments and are not clinically validated diagnoses.

## 4. Git Development Progress

The project is developed in the `hinam` branch of the existing team repository.

Recent development commits include:

| Commit | Description |
|---|---|
| `a351031` | Detection and severity classification integration |
| `ec0a2f4` | FastAPI prediction endpoint |
| `64758d9` | React prediction API integration |
| `f87863e` | Dental image analysis and detection visualization |

The repository also contains the earlier project setup, frontend/backend integration, and YOLOv8 training notebook commits.

Trained model files and temporary test images are kept outside normal Git tracking.

## 5. Pending Tasks

- Implement interactive bounding-box selection and corresponding prediction highlighting.
- Improve frontend design, usability, and error handling.
- Add automated backend and frontend tests.
- Strengthen uploaded-image validation and privacy protections.
- Conduct broader end-to-end testing.
- Investigate domain shift between the detection and classification datasets.
- Perform additional independent and clinically guided validation where feasible.
- Complete research documentation and final project integration.

## 6. Research Limitations

- Classification performance is based on the current image-level test split, not a confirmed patient-independent evaluation.
- Perceptual-hash grouping reduces some duplicate-related leakage but does not eliminate all possible related-image leakage.
- The severity classifiers were trained on a different image dataset from YOLOv8.
- Model agreement does not prove that the predicted severity is correct.
- The system is intended as a research prototype, not a replacement for professional dental assessment.

## 7. Next Step

Improve interactive frontend visualization, extend application testing, and prepare the component for integration into the team's overall dental health assessment framework.