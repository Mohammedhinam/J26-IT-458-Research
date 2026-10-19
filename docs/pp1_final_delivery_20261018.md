# PP1 local demo completion and handoff

**Later update, same day:** the owner requested adding the proposal candidate.
The current four-model version includes EfficientNet-B0 + Grad-CAM first, with
ResNet as baseline and ROIv1/v2 as additional comparisons. Use **8773** and
`scripts/run_pp1_proposal_demo.sh`. See
[current integration/report](vision_efficientnet_live_integration_v1.md).
Updated deck: `pp1_final_20261018/PP1_Proposal_Doctor_Demo_v3.pptx`.
The earlier 8771 process and the three-model evidence below remain preserved.

18 October 2026. The existing three-model **engineering demo is verified and
ready for rehearsal**. Clinical validation and reliable Grade 1/2 performance
remain unfinished research. No new model has replaced the original demo.

## Open and run

Open **http://127.0.0.1:8771/** on this Mac. A new local server was started after
checking that the port was free. Other processes were not stopped or restarted.

If it has stopped, run from Terminal:

```sh
cd /Users/vinuthanvinuthan/Desktop/RP-J26-IT-458
zsh scripts/run_pp1_doctor_demo.sh
```

Leave that Terminal open. The launcher uses the three existing trusted model
artifacts, runs on loopback and MPS, and leaves any existing port-8771 listener
untouched. Colab, external uploads and training are unnecessary for this demo.

Desktop convenience folder: `/Users/vinuthanvinuthan/Desktop/PP1_Final_Demo_20261018/`.
It contains a copy of the verified presentation, a launcher and short instructions.

Presentation: `docs/pp1_final_20261018/PP1_Doctor_Demo.pptx`, 10 slides with editable
text and four native tables, actual UI screenshots and source notes. All final
slides were rendered and inspected. Structure/font/layout/import checks passed.
Native PowerPoint and Google Slides execution were not tested. The owner should
rehearse in the application used for PP1. This is a demo support deck, not a
replacement for an institution-required full presentation template or the owner's
manually drawn architecture diagram.

## What the doctor sees

1. **One photo upload:** new intraoral JPG/PNG up to 8 MiB, original preview,
   explicit consent and Run All Three Models.
2. **Doctor Review Mode:** record independent MGI assessment before predictions.
   Alternatively, Developer Demo Mode clearly says not clinically reviewed.
3. **Three separate cards:** ResNet50 v3, YOLO ROI v1 + ResNet18, YOLO ROI v2 CORAL.
   Each shows its own success/error status and actual available outputs. One
   failed request preserves the other successes. Reset/file changes prevent late
   responses from appearing as results for a new case.
4. **Model-specific feedback:** Agree / Disagree / Uncertain, optional reviewer
   grade, reason and notes. Explicit JSON/CSV export. Feedback never changes a
   prediction, dataset label or trained model automatically.
5. **Separate Questionnaire:** input answers, predict self-reported previous gum
   treatment, inspect SHAP, change only permitted what-if inputs and reset.
   Its probability never merges with the photo grade.

| Card | Genuine current output | Limit |
|---|---|---|
| A, ResNet50 v3 | Image MGI 1–4, four class scores, predicted-class original/Grad-CAM/overlay | Uncalibrated scores, no supported image Grade 0, heatmap can highlight irrelevant tissue |
| B, ROI v1, fold 00 | Predicted tooth boxes, detector scores, crop grades, maximum crop grade | No crop probability output in this adapter and no image probability distribution |
| C, CORAL v2, fold 00 | Same detector boxes, ordinal crop grades, actual five-grade crop probabilities, maximum crop grade | Crop probabilities are uncalibrated and are not an image-level probability distribution |

The two ROI classifiers share the same frozen fold-00 detector. Their output
cards are independent workflows, not statistically independent models. There is
no ensemble vote or fused diagnosis. Boxes are predictions for tooth/perigingival
regions, not TXT ground truth or validated gingival boundaries.

## Fresh actual verification

The previously permitted non-study example JPG was run through all three actual
checkpoints. It returned **ResNet MGI 3, ROI v1 maximum 3 with 12 boxes, CORAL
maximum 2 with 12 boxes**. Every response bound to the same input SHA and said
`photo_saved: false`. The model disagreement is real; it does not determine the
correct clinical grade. The ResNet top score was 35.1%, not accuracy/confidence
validated on this patient. The UI displays the original honest heatmap, including
its upper-lip attention. These are example predictions, not clinical ground truth.

The fictional Questionnaire example returned 21.41% for previous gum treatment.
SHAP, what-if and exact reset worked. This is a software example, not a patient's
current disease risk. Cached final questionnaire evaluation evidence remains
unchanged. No new held-out tabular evaluation was run.

| Verification | Actual result |
|---|---:|
| Focused API and image-decoding pytest suite | 31 passed, 0 failed |
| Browser checks including real inference, error fixtures, export, mobile and privacy | 37 passed, 0 failed |
| Generated ROI crop geometry checks | 12 assertions passed |
| Independent ROI metrics/membership/preservation verification | 76 assertions passed |
| Exact original training-crop JPEG reproduction | 48 / 48 |
| Existing protected model/research/UI artifact hashes | 29 / 29 unchanged |

The pytest run reports three existing SHAP matplotlib deprecation warnings.
Assertions and crop matches are not extra pytest test cases. Browser failure,
flat-CAM and no-detection checks use explicitly synthetic fixtures. They are not
model results or real clinician feedback. Real screenshots use actual inference.

Evidence root: `data/vision/pp1_final_local_20261018_v1/`.
`focused_tests.xml`, `browser_verification.json`, `desktop_real_outputs.png`,
`doctor_demo_clean.png`, `three_models_clean.png`, `questionnaire_live.png` and
`mobile_real_outputs.png` contain the bounded verification evidence. Export
files named smoke/synthetic contain software test feedback only.

## ROI check and next-data work

Four Grade 1/2 fit photos and 48 training crops were inspected. Gum margins
already appear in multiple current crops. Clinical sufficiency is unverified.
The single fixed padding ablation used shared detector boxes and frozen weights
on the same 136 score images. Increasing context from 15% to 30% changed accuracy
61.76% to 62.50%, Macro-F1 .3347 to .2980 and Grade 2 recall 1/17 to 0/17.
**The experiment did not solve the minority-grade problem, so it was not adopted.**

This is inference sensitivity, not a retrained model or a new 680-image result.
The local baseline agreed with 128/136 historical Colab predictions. Backend/run
differences remain unisolated. Detailed counts, both confusion matrices, ordinal
MAE/QWK and limitations are in `docs/vision_roi_context_diagnostic_20261018.md`.

A fit-only review queue covers 9 Grade 1 + 67 Grade 2 cases. It is preparation
for a qualified reviewer, not 76 new/verified labels. Additional verified photos
were not obtained. `docs/grade12_data_review_next_steps_20261018.md` contains the
intake and qualified-review checklist and a proposed future matched training
comparison. Clinical review, permission for new source data, grading provenance,
participant isolation and any future training approval remain necessary inputs.

The earlier controlled ResNet A/B pilot is already complete and preserved.
Its 136-image results and eight matched Grad-CAM cases do not establish a gum
attention fix. See `docs/vision_resnet50_fold0_colab_results_v1.md`. Do not rerun
blind fine-tuning or describe model attention as clinically validated localization.

## Files added by this completion task

- `scripts/pp1_roi_context_diagnostic_v1.py`: isolated fit coverage and fixed
  score-inference diagnostic. Does not import a training entry point or change
  existing adapters. New versioned outputs only.
- `scripts/run_pp1_doctor_demo.sh`: minimal local launcher using existing models.
- `docs/vision_roi_context_diagnostic_20261018.md`: actual diagnostic results.
- `docs/grade12_data_review_next_steps_20261018.md`: review/data preparation.
- `docs/pp1_final_delivery_20261018.md`: this runbook and verified scope.
- `docs/pp1_final_20261018/PP1_Doctor_Demo.pptx`: editable presentation.
- Private evidence root, Desktop convenience copies, and AI/diary/handoff entries.

Existing React/API, questionnaire scientific code, ROI adapters, model weights,
datasets, original splits and research results were not edited. The dirty working
tree was preserved. No commit, push, reset, deletion, cloud upload, external
patient-image transmission, Test payload access or new training occurred.

## Privacy and operating limits

Normal uploads use temporary local storage and return results in memory. No
automatic permanent photo storage or browser local/session-storage persistence
was observed. Explicit feedback export excludes image bytes, filenames, input
image hashes and patient-ID fields. Free text could still contain information a
user types, so omit identifiers. Developer mode is not clinician review. Doctor
role is self-declared, not authenticated. A local prototype is not a certified
clinical deployment. The separate saved screenshots use the example photo the
owner already permitted for this bounded verification.

The MGI labels remain provisional, Grade 1 performance remains weak, image-level
MGI 0 lacks support, and participant independence is not established. All 181
held records and sealed Test boundaries remain unchanged. No final Vision Test
claim is made. Existing training/testing metrics with different populations must
not be ranked as though they measured the same protocol.

## Tamil rehearsal and viva

“ஒரு புதிய mouth photo upload செய்தால், அதே photo-வை மூன்று existing trained
workflows predict செய்கின்றன. Grade என்பது model estimate. Heatmap model எங்கு
கவனம் வைத்தது என்பதை காட்டுகிறது. Box என்பது detector கண்ட tooth region.
இவை diagnosis அல்லது clinically verified gum boundaries அல்ல.”

“Questionnaire branch தனியாக previous gum treatment probability கொடுக்கிறது.
SHAP model output-ஐ விளக்குகிறது. What-if model sensitivity மட்டும்; future
health அல்லது treatment benefit என்று சொல்லவில்லை.”

“ROI padding அதிகரித்தால் நல்ல result வரும் என்று assume செய்யவில்லை. ஒரே
136 photos, அதே detector boxes மற்றும் weights வைத்து பார்த்தோம். Accuracy
ஒரு image உயர்ந்தாலும் Macro-F1, Grade 2 recall குறைந்ததால் மாற்றவில்லை.”

Three lines to understand: the manifest fixes membership, shared boxes keep the
comparison matched, and exclusive output creation preserves earlier work. Likely
viva question: **Does 60.74% prove the model works for a doctor?** No. It is a
provisional development OOF accuracy, with Grade 1 recall 0/12 and weaker Grade 2
recall. The working demo enables honest comparison and clinical review.

Engineering completion does not complete the qualified clinical review. Owner
should rehearse the deck and explain these limits before presenting the work.
