# PP1 Functional Test Cases
## Component 03 - Malocclusion Detection

Project: AI-Integrated Dental Health Assessment and Preventive Analytics Framework  
Project ID: J26-IT-458  
Component: AI-Based Malocclusion Detection, Severity Assessment and Explainable Preliminary Screening

| TC ID | Test Scenario | Test Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| TC-01 | API health check | Open `http://127.0.0.1:8000/health` | API returns healthy status and loaded models | API returned healthy status with 4 loaded models | PASS |
| TC-02 | Valid dental image upload | Upload a JPG/PNG dental image in the frontend | Image preview should appear | Image preview displayed correctly | PASS |
| TC-03 | Analyze valid dental image | Upload image and click Analyze Image | API should return screening probabilities | Four condition probabilities displayed | PASS |
| TC-04 | Crossbite result display | Analyze a known Crossbite test image | Crossbite result card should display probability and screening status | Crossbite probability and status displayed | PASS |
| TC-05 | Open Bite result display | Analyze a known Open Bite test image | Open Bite result card should display probability and screening status | Open Bite probability and status displayed | PASS |
| TC-06 | Four-condition output | Analyze a supported dental image | Crossbite, Open Bite, Crowding and Spacing cards should appear | All 4 result cards displayed | PASS |
| TC-07 | Severity framework integration | Analyze a dental image | Severity should not be inferred from AI confidence; status should indicate pending assessment | `not_assessed` / Pending clinical assessment displayed | PASS |
| TC-08 | Invalid file rejection | Attempt to upload/send a non-image file | System/API should reject unsupported file | API rejects non-image files | PASS |
| TC-09 | Experimental Spacing warning | Analyze a dental image | Spacing should show low-data/experimental reliability warning | Experimental / Low Data displayed | PASS |
| TC-10 | Upload another image | Complete analysis and click Upload Another Image | Previous image/results should reset and new image can be selected | Interface reset successfully | PASS |

## Observed Model Limitation

During testing, some known Open Bite images also produced Crossbite probabilities above the research threshold.

This indicates inter-condition false positives in the current preliminary models.

The prototype therefore reports probabilities and preliminary screening thresholds rather than clinical diagnoses.

## Severity Validation Note

Severity is not calculated from prediction confidence.

Current severity outputs remain:

- Mild - planned
- Moderate - planned
- Severe - planned

Final severity assignment requires literature-supported or clinically validated criteria.

## Overall PP1 Test Result

Frontend image upload: PASS  
FastAPI communication: PASS  
Four model inference: PASS  
Result visualization: PASS  
Severity framework integration: PASS  
Research disclaimer: PASS  

Overall Prototype Status: FUNCTIONALLY OPERATIONAL FOR PP1 RESEARCH DEMONSTRATION