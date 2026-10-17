
# AI-Based Plaque, Tartar and Oral Hygiene Scoring Methodology

## 1. Research Objective

Develop an experimental AI-based approach for assessing
dental plaque and tartar from intraoral photographs.

The proposed system uses:
- YOLOv8 plaque segmentation
- YOLOv8 tartar object detection
- YOLOv8 tooth segmentation

The long-term objective is to develop separate plaque
and tartar scores and a combined oral hygiene score.

The current system is a research prototype and is not
a clinically validated diagnostic or scoring tool.

## 2. Scientific Background

### 2.1 Silness and Loe Plaque Index (1964)

The Silness-Loe Plaque Index evaluates plaque accumulation
on tooth surfaces using a clinical scale from 0 to 3.

Score 0: No plaque.
Score 1: Thin plaque film, generally detected clinically
         using a probe or disclosing agent.
Score 2: Moderate plaque accumulation visible clinically.
Score 3: Abundant plaque accumulation.

This clinical index cannot be reproduced directly from
whole-image pixel percentages without further validation.

### 2.2 Simplified Oral Hygiene Index (OHI-S)

Greene and Vermillion (1964) introduced OHI-S.

OHI-S consists of:
- Simplified Debris Index (DI-S), range 0 to 3.
- Simplified Calculus Index (CI-S), range 0 to 3.

OHI-S = DI-S + CI-S

The combined clinical index ranges from 0 to 6.

Clinical OHI-S scoring uses selected tooth surfaces,
surface-coverage criteria and calculus observations.

Our current AI system does not reproduce those clinical
examination procedures.

## 3. Current AI Measurements

### 3.1 Plaque Pixel Coverage

Plaque coverage (%) =
    (Predicted plaque pixels overlapping predicted teeth
     / Total predicted tooth pixels) * 100

The calculation is performed only when tooth pixels
are detected.

This is an experimental image-based plaque measurement,
not a validated Silness-Loe Plaque Index or DI-S score.

### 3.2 Tartar Bounding-Box Area Proxy

Tartar-box tooth area (%) =
    (Predicted tooth pixels inside the union of tartar
     detection bounding boxes
     / Total predicted tooth pixels) * 100

Overlapping tartar boxes are counted only once.

Bounding boxes contain pixels that may not be tartar.
Therefore, this is NOT actual tartar surface coverage.

### 3.3 Example Experimental Output

For one tested dental photograph:

Plaque coverage: 10.16%
Tartar-box tooth area proxy: 5.57%
Tartar detection boxes: 1

These measurements are image-specific model predictions.
They are not clinical examination results.

## 4. Proposed Scoring Development

### 4.1 Plaque Score

Investigate whether plaque segmentation measurements
can be calibrated against dentist-assigned clinical
plaque scores.

Required research:
- Identify a suitable clinical plaque index.
- Define the tooth surfaces to be assessed.
- Collect expert-scored reference images.
- Compare AI predictions with clinical observations.
- Derive score boundaries from reference data rather
  than selecting arbitrary percentage thresholds.

Current implementation status:
NOT IMPLEMENTED.

### 4.2 Tartar Score

Investigate a calculus scoring method based on
established clinical criteria.

The current tartar model predicts bounding boxes,
not exact tartar segmentation masks.

Potential future approaches:
- Train a tartar segmentation model using
  polygon or pixel-level annotations.
- Develop tooth-surface-specific calculus measurements.
- Compare AI predictions against dentist-assigned
  calculus scores.

A tartar-box percentage must not be treated as
a validated clinical calculus score.

Current implementation status:
NOT IMPLEMENTED.

### 4.3 Combined Oral Hygiene Score

The established clinical OHI-S formula is:

OHI-S = DI-S + CI-S

However, this formula can only represent clinical
OHI-S when its required scoring procedure is followed.

An AI-derived combined score will require:
- A justified plaque/debris component.
- A justified tartar/calculus component.
- Defined measurement conditions.
- Clinically supported thresholds.
- Validation against expert reference scores.

Current implementation status:
NOT IMPLEMENTED.

## 5. Validation Plan

Evaluate the proposed scoring method using:
- Expert dental assessments.
- Agreement between AI and clinical scores.
- Separate plaque and calculus evaluations.
- Error analysis for missed tooth regions.
- Evaluation across different image angles
  and lighting conditions.
- Independent test images where available.

Do not claim clinical validation until these
evaluations have been completed.

## 6. Current Research Limitations

1. Plaque coverage depends on segmentation accuracy.
2. Tooth segmentation may miss teeth in angled images.
3. Tartar bounding boxes do not provide exact
   tartar pixel boundaries.
4. Whole-image percentages do not directly correspond
   to clinical index measurements.
5. Current confidence thresholds are model inference
   settings, not clinically validated hygiene thresholds.
6. The existing datasets do not establish clinical
   score cutoffs.

## 7. Scientific References

Silness, J., and Loe, H. (1964).
Periodontal Disease in Pregnancy II:
Correlation Between Oral Hygiene and Periodontal Condition.
Acta Odontologica Scandinavica, 22, 121-135.

Greene, J. C., and Vermillion, J. R. (1964).
The Simplified Oral Hygiene Index.
Journal of the American Dental Association,
68, 7-13.

Note:
Verify complete bibliographic details and review
the original clinical scoring criteria before using
these references in the final research report.

## 8. PP1 Research Position

Completed:
- Plaque segmentation model
- Tartar detection model
- Tooth segmentation model
- Automatic plaque coverage calculation
- Experimental tartar-box area calculation
- Integrated FastAPI and React prototype

Under development:
- Clinically supported plaque scoring method
- Clinically supported calculus scoring method
- Combined AI-derived oral hygiene scoring method
- Independent clinical validation

The proposed scoring framework is research in progress.
It must not be presented as a completed or validated
clinical hygiene index.
