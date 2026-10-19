# Grade 1/2 data and clinical review preparation

18 October 2026. A preparation checklist, not completed clinical validation.

Current safe Training support is 12/84/223/361 for image grades 1/2/3/4.
Fold-0 fit support is 9/67/179/289. The 76-case fit-only queue is under
`data/vision/pp1_final_local_20261018_v1/roi_context/grade12_fit_review_queue.json`.
All qualified-grade, reviewer and permission fields remain empty. No new photos
or clinical labels were obtained by this task.

## Qualified review

1. A qualified dental reviewer records an independent assessment before seeing
   model outputs, with an uncertain/unassessable option.
2. Record reviewer qualification, review date, rubric/source and whether the
   available photograph supports image-level MGI assessment.
3. Review each tooth ROI's visible gum margin and whether cropping excludes
   relevant tissue. Existing boxes do not define gingival segmentation masks.
4. Keep the original caption-derived grade unchanged. Record any proposed grade
   separately, with reasons and genuine reviewer provenance. Resolve disagreements
   through a predefined adjudication process before training eligibility changes.
5. Doctor-demo feedback is exploratory feedback. It does not automatically become
   an approved dataset label or authorize retraining.

## Additional photo intake

Before including a photo, document permitted research use and applicable consent,
capture source and acquisition conditions, a non-identifying participant/group
key, grading provenance, and duplicate/near-duplicate checks. Store any identifying
linkage separately under the owner's approved local process. Avoid identifiers
in filenames and free-text exports. Do not assume a public image is clinically
graded or that a missing caption means healthy/Grade 0.

Use qualified grading of the actual MGI target. Do not translate generic
Healthy/Gingivitis/Periodontitis class labels into MGI 0–4 automatically. Preserve
original annotations and distinguish human review from AI suggestions. Check
metadata/colour/orientation compatibility before creating versioned derivatives.
Cloud upload requires its own appropriate permission. Nothing is uploaded here.

Additional participant groups need a prospective split policy. Do not quietly
insert them into frozen OOF scoring folds, clear existing holds, or mix protected
Test aliases into development data. The owner must approve any revised manifest.

## Smallest defensible next training comparison

This is a proposed future protocol, **not execution approval**. Obtain genuine
review first. If additional context is justified, compare 15% versus a single
predeclared 30% crop-training context, using identical eligible records/groups,
frozen original fold assignments, the same fold-local YOLO detectors, matched
ImageNet initializations, classifier budget, class weights and random seeds.
The frozen detector must not have trained on that fold's scoring groups.
Train separate classifiers for each context. Do not initialize from a checkpoint
that has seen scoring images. Preserve original v1/v2 checkpoints and demo.

Use image-level Macro-F1 and Grade 1/2 recall as decision criteria alongside
accuracy, balanced accuracy, confusion matrix, ordinal MAE, QWK and abstention.
Evaluate both methods on exactly the same scoring IDs. Report conditional paired
intervals and acknowledge small Grade 1 support and participant uncertainty.
Detector mAP remains a separate localization metric. A small fold pilot cannot
be presented as a replacement 680-image OOF result.

For explanation review, use the same photos and target class, preserve image
geometry and display the unaltered model attention. Let the reviewer record
irrelevant attention and uncertainty. Never tune heatmap colours, masks or crops
to hide inconvenient regions. No verified gingival masks currently support a
gingiva-supervised loss in this dataset.

An appropriate Colab GPU would support a separately approved matched training
run. The current PP1 demo and this completed frozen-weight diagnostic require
no Colab run. New data, clinical review, protocol approval and any cloud upload
remain separate next steps.
