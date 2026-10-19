# Registered-photo live demo integration v1

17 October 2026 · `vinuthan` · local exploratory engineering only.

**Engineering verification PASS: 101 focused tests, zero failures/errors/skips; 24 unique browser checks passed.** A generated RGB JPEG passed through the real pinned v3 checkpoint, exact B1 preprocessing and predicted-class Grad-CAM. This does not measure dental accuracy or qualify arbitrary phone/internet photos.

## What is now connected

The existing React upload form → local FastAPI endpoint → immutable input registry → verified ResNet-50 v3 checkpoint → B1 extended-float input → four MGI 1–4 probabilities → aligned original-display/heatmap/overlay panels. No new training, model selection, inference threshold or colour conversion policy was introduced. The original research MGI 0–4 definitions and final approved-training gate remain unchanged.

The standard application still starts with the photo runtime **inactive**. Three explicit startup arguments are required together; an invalid binding stops startup rather than falling back. Only hash-registered RGB JPEGs, at most 8 MiB/40 million pixels, identity EXIF orientation and the qualified embedded ICC profile are accepted in real-photo mode. Missing/different ICC, PNG, rotated EXIF, unknown source, study/Test/held inputs are not approved by this integration. Merely converting an unknown PNG to JPEG cannot establish its provenance or colour interpretation.

The owner's supplied PNG has an explicitly uncertain internet/other source. It was **not registered, decoded by the runtime, or used for prediction**. No real non-study photo has yet passed this live pathway. Registry provenance records an owner declaration, not authenticated consent, qualified clinical review or proof that a copied/re-encoded photograph is independent of the study dataset.

## Reproduce the generated-only demonstration

Use the existing installed environment and checkpoint; no install or weight download is needed:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
.venv/bin/python -B -m src.tabular.api --port 8772 \
  --vision-checkpoint models/vision_live_demo_v1/v3_best.pt \
  --vision-registration data/pp1_live_photo_verification_v1_20261017T013402631604Z/generated_registration.json \
  --vision-registration-sha256 15d2e8584225660154dd5ce7291829b3993c33f7a7509dd411aea3482c7629e8
```

Open `http://127.0.0.1:8772/`, choose Vision, and upload only `data/pp1_live_photo_verification_v1_20261017T013402631604Z/generated_only.jpg`. The panel explicitly says generated verification. Its grade/probabilities have no clinical interpretation. The previous demo servers were preserved.

The ignored checkpoint is an exact copy of `best.pt` from the previously verified v3 result ZIP, not a retrained or altered model. Original archive SHA `c79f16cf59b268f86a5a4c4b6a3482636e374cb67629895f38e55dbb1eaf0d70`; checkpoint SHA `36dd33662e277d3770995bf406f714b71231e77846a4a6a01ef418864259b2ee`. Only the checkpoint member was copied; no dataset image or Test payload was read. All source results/checkpoints remain intact.

## Future source-confirmed photo activation

Before writing a real registry, establish the original photo's source, permission for this local use, non-study/non-Test/non-held provenance and supported RGB/ICC/orientation. No real registration was created in this task. Keep it in ignored local storage; do not put private photos/provenance in Git. The registration JSON has exactly:

- `version`: `pp1-live-photo-registration-v1`.
- `scope`: `local_nonstudy_demo`.
- `checkpoint_sha256`: the pinned v3 hash above.
- `profile_sha256`: qualified `2b8daf8cabe783b17f801e6687f57016b53c775a826269e21c51313083c9fefc`.
- `inputs`: exact JPEG SHA → `owner_supplied_nonstudy`.
- `provenance`: `kind=owner_supplied_nonstudy`, actual `reviewer`, ISO `date`, and an actual `evidence_reference` for the owner's source decision. Never fill these from guesses.

Compute the registry's SHA and start with the same three CLI options bound to that registry. A qualified profile alone is not source permission or clinical colour validation. Supporting ordinary sRGB/missing-profile phone files would require a separately tested, explicit input-colour contract; this task did not guess one.

## Actual verification and limits

Selected pytest files: `test_live_photo_demo.py` (51), `test_photo_explanation.py`, `test_component2_api.py`, `test_questionnaire_evidence.py`, `test_vision_evidence.py`; **101 passed in 4.94 seconds**. They use generated/configuration fixtures, including actual CPU/MPS ResNet/Grad-CAM checks with `weights=None`, and synthetic API adapters. They are not a full repository test run.

Initial tests found an immutable-registry reconstruction defect in generated scope. It was fixed by explicitly copying `allowed_inputs` when rebuilding the frozen dataclass; the regression remains. A later API mock was corrected to implement the actual runtime interface. Neither correction relaxed a production assertion or approval gate.

Actual browser checks use the pinned trained checkpoint and generated input only: upload readiness, exact checkpoint, generated status, four-class mapping, probability sum, same predicted/explained class, three 40×24 RGB views, reset, unregistered rejection, stale-error clearing, PNG rejection, mobile width, live fictional questionnaire and What-if/reset. Initial browser scenario fixture omitted setting cleaning days to 7; it correctly produced unchanged output. The corrected targeted check set 7, verified 21.41%→24.41%→21.41%; original failed harness evidence is preserved. No prediction logic changed to force a pass. Zero page errors.

Playwright MCP's upload filesystem roots point to a different project, so no file was copied into that project to bypass the restriction. The installed local Playwright/Chrome runtime performed the browser check instead. No dependency installation or external upload occurred.

Evidence: `docs/vision_registered_photo_live_verification_v1.json`; selected JUnit `docs/vision_registered_photo_live_tests_v1.xml`. Generated image/config/browser artifacts are only in ignored `data/pp1_live_photo_verification_v1_20261017T013402631604Z/`. The UI screenshot was visually checked; only generated colour blocks were passed to the model. Model, trainer, colour contracts, original datasets, 181 holds, NP015, split manifests and sealed Test stay unchanged. No commit/push.

Historical Vision accuracy remains 50.94% on the repeatedly reused 53 provisional Validation records, macro-F1 0.3259. This integration does not improve that performance. MGI 0 is unsupported; MGI 1/2 performance, qualified labels, participant independence and final Vision evaluation remain unresolved. Softmax scores are not calibrated clinical probabilities.

## Three blocks to explain

1. `load_registration`: registry SHA-வை முதலில் பார்க்கும். பதிவு செய்யாத photo அல்லது scope மாறிய file model-ஐ அடையாது. Source declaration மட்டும் clinical approval ஆகாது.
2. `load_v3_runtime(..., synthetic_only=...)`: saved checkpoint hash பொருந்தினால் மட்டுமே load செய்யும். புதிய weights download அல்லது training நடக்காது; generated mode தெளிவாகத் தெரியும்.
3. `PhotoRuntime.explain`: அதே B1 input-ல் prediction மற்றும் அதே predicted grade-க்கான Grad-CAM தரும். Model input-ல் extended values பாதுகாக்கப்படும்; display preview மட்டும் clipped sRGB.

Viva: **Does a working upload/heatmap prove higher accuracy?** இல்லை. Integration software வேலை செய்கிறது என்பதை மட்டும் காட்டுகிறது. Grades அனைத்திலும் accuracy, label correctness மற்றும் clinical validity-க்கு தனி evidence தேவை.

Next: obtain one genuinely source-confirmed, permitted, supported original non-study RGB JPEG and verify its header/registration before any real-photo inference. Human feedback/rehearsal and scientific approval tasks remain separate; do not release the 181 holds or rerun Test.
