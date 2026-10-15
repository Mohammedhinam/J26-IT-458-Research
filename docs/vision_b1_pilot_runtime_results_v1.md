# B1 four-grade pilot — verified owner-run Colab CPU evidence v1

Recorded2026-10-15 · branch `vinuthan`. **PASS:71 passed,0 failed,0 errors,0 skipped.** This supersedes the local preparation's three backend skips; it is not a full repository run, GPU qualification, dental training or clinical performance.

## Actual evidence verified, no rerun

Original downloaded archive:
`/Users/vinuthanvinuthan/Downloads/vision_b1_pilot_runtime_evidence_v1.zip`

Retained byte-identical copy:
`/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/docs/vision_b1_pilot_runtime_evidence_v1.zip`

- ZIP bytes:**5136**.
- SHA256:`8627aff3e7dfd744924aaa855661bf016e35043d407bdee99066bbb55384d11e`, matches owner-provided digest.
- ZIP CRC/membership pass:summary.json,junit.xml,pytest.log,source_hashes_before.json,source_hashes_after.json,evidence_manifest.json.
- All **5 declared evidence payload hashes** match.
- **20/20 source hashes** agree before/after execution, with the code ZIP's manifest/payloads and current local source files.
- **71 unique JUnit cases** exactly match the previously selected local71-case suite; no failures/errors/skips. All three backend cases below are explicit passes.
- Pytest log:**71 passed in128.35s**; JUnit suite128.353s.
- Summary flags:local_diagnostic=False,source_unchanged=True,RUN_PILOT=False,dental_images_accessed=False,dental_training_performed=False,pretrained_weights=None,acceptance_passed=True.
- Synthetic optimizer checks executed; they used generated inputs only. No pretrained weights or actual dental training were used. No new tests were run locally during this evidence review.

| Previously skipped backend case | Actual Colab result |
|---|---|
|test_resnet50_four_output_optimization_and_frozen_batchnorm_weights_none|PASSED|
|test_four_class_gradcam_geometry_and_hook_cleanup_weights_none|PASSED|
|test_four_class_synthetic_checkpoint_loading_and_reproducibility|PASSED|

Runtime:Python3.13.16,Linux,NumPy2.1.3,Pillow11.3.0,pytest8.4.2,torch2.11.0+cpu,torchvision0.26.0+cpu. **CUDA unavailable;GPU=None.** CPU compatibility does not itself establish GPU memory/runtime or learned dental accuracy.

## What is now ready

- Verified local package remains733 provisional development sources:680Training+53Validation model arrays and3CAM arrays. [Local package record](vision_b1_local_packaging_results_v1.md).
- New four-output MGI1–4 runner's selected synthetic CPU/backend cases now verified. Original five-grade research model/proposal and independent questionnaire branch unchanged.
- Versioned notebook/code-only handoff remains unchanged; no regeneration or code modifications were needed.
- All181holds,NP015/duplicate/Test boundaries and provisional-label/final-research approval gates stay unchanged.
- Source dataset was not opened in this review. Original evidence ZIP and all implementation files preserved.

## Remaining approval/action

The completed owner scope allowed local engineering and one local package, explicitly excluding cloud upload, actual dental training and pretrained downloads. Current evidence supplies **software verification, not those permissions**.

Next owner decision must separately cover this exact bounded exploratory scope:
1. Upload only the verified733-source B1 development bundle plus3eligible CAM arrays to a fresh isolated Colab environment.
2. Obtain the official ResNet50 ImageNet1K_V2 checkpoint from its documented source, verify/record its actual SHA, no alternate weights.
3. Run the versioned four-output MGI1–4 head-only protocol on a GPU:seed42,batch16,lr0.001,max5epochs,patience2,frozen backbone/BatchNorm; evaluate only the53Validation cases, training-derived majority baseline and3fixed development Grad-CAMs.
4. Bind the future owner record to current bundle/manifest/code/protocol/weights hashes and a fresh run ID. Do not fabricate future weight hashes or permission records.

No Test use, final scientific training approval, class relabeling, MGI0/healthy-detection claim, clinical validation, paid-resource purchase or automatic retry is authorised by this evidence.

**Provisional labels; non-clinical; non-final; participant independence unverified.** MGI1 Validation support remains1; qualified labels/participant independence/final research model remain pending.

Viva: **71 tests pass என்றால் dental model trained ஆகிவிட்டதா?** இல்லை. Generated inputs-ல் code/runtime வேலை செய்வது verify ஆகியுள்ளது; actual dental training இன்னும் நடக்கவில்லை.
