# Explainable AI-Based Malocclusion Detection

This component focuses on preliminary dental malocclusion screening using dental and smile images.

## Core Objective

The primary task is to distinguish:

- Normal
- Possible Malocclusion

using a fine-tuned MobileNetV2 model.

## Explainability

Grad-CAM will be investigated to provide visual explanations of model predictions.

## Proposed Extension

The component will investigate malocclusion type classification:

- Crowding
- Spacing
- Open Bite
- Crossbite

The proposed extension requires appropriately labelled data and separate validation.

## Evaluation

The model will be evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion Matrix
- Unseen-image testing
- Robustness testing
- Inference time

## Scope Boundary

This system is intended for preliminary screening and does not provide a clinical diagnosis or replace professional dental assessment.